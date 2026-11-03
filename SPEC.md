# Whiskey Assistant 規格書

## 1. 專案目標

Whiskey Assistant 是一個威士忌問答助手：使用者以自然語言提問，系統從威士忌知識庫檢索相關資料，交由 LLM 產生回答，並附上資料來源。

技術重點：

- **Python 後端**：FastAPI、PostgreSQL、API 設計
- **RAG**：資料切塊、embedding、向量檢索、prompt 組裝，**核心流程自行實作，不依賴 LangChain 等框架**，以完整掌握每個環節的行為與取捨

## 2. MVP 範圍

### 要做

- 資料匯入流程：讀取原始資料 → 切塊 → embedding → 寫入資料庫
- `POST /api/chat`：單輪問答，以 JSON 一次回傳答案和來源
- 前端聊天介面：具備專業質感的輸入互動視窗

### 不做（之後的規劃見第 12 節）

- 多輪對話（追問）
- 使用者登入
- 混合檢索、rerank、metadata 過濾
- 正式部署
- 測試（見 `CLAUDE.md`）
- 串流輸出（SSE）：等 Claude 回答完整串接後再加回

## 3. 技術選型

| 項目 | 選擇 |
|---|---|
| 後端框架 | FastAPI |
| 資料庫 | PostgreSQL + pgvector（開發時用 Docker 執行） |
| Embedding | 本機 `bge-m3`（1024 維，支援中英文） |
| LLM | Claude API（模型 ID 寫在設定檔） |
| Python 套件管理 | pip + venv（`requirements.txt`） |
| 程式碼檢查 | ruff（設定在 `ruff.toml`） |
| 前端 | Vue 3 + Vite + TypeScript，UI 自己刻，不套元件庫 |

## 4. 專案結構

```
Whiskey-Assistant/
├── backend/
│   ├── app/              # FastAPI 應用程式
│   ├── scripts/          # 資料匯入等一次性腳本
│   ├── .env.example      # 設定範本；實際設定放 .env（不進 git）
│   └── requirements.txt
├── frontend/             # Vue 3 專案
├── data/                 # 原始資料（待提供）
├── docker-compose.yml    # 開發用，只跑 PostgreSQL + pgvector
├── ruff.toml
├── CLAUDE.md
└── SPEC.md
```

## 5. 資料庫結構

資料內容還沒確定，先用通用結構，不確定的欄位放進 JSONB。等資料到位後再決定要不要拆成正式欄位。

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id          BIGSERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    source      TEXT,                          -- 資料來源（網址或檔名）
    metadata    JSONB NOT NULL DEFAULT '{}',   -- 產區、酒廠、年份等
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE chunks (
    id           BIGSERIAL PRIMARY KEY,
    document_id  BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index  INT NOT NULL,                 -- 在原文件中的順序
    content      TEXT NOT NULL,
    embedding    VECTOR(1024) NOT NULL,
    UNIQUE (document_id, chunk_index)
);

CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
```

## 6. RAG 流程

### 原始資料

`data/whiskyDataset.json`（不進 git）：17,346 筆英文品飲筆記，每筆有 `id`、`NAME`、`NOTE`、`SCORE`、`IMAGE_PATH`。

- `NAME`：酒名，括號內含酒齡、年份、酒精濃度、裝瓶商、桶型等資訊
- `NOTE`：品飲筆記，長度中位數約 976 字元，最長 3,002 字元
- `SCORE`：例如 `SGP:551 - 89 points`，格式不一致，有一筆無法解析
- `IMAGE_PATH`：圖片檔不在資料內，不使用

### 資料匯入（離線執行的腳本）

分成兩支腳本，中間產生 `data/whisky_clean.json`：清理只要幾秒、embedding 要很久，拆開後調整清理規則時不必重跑 embedding，也能直接打開檔案檢查清理結果。

**腳本 1：`backend/scripts/clean_data.py`**（已完成）

1. 讀取 `data/whiskyDataset.json`
2. 清理文字（`NAME`、`NOTE`）：
   - 用 `html.unescape` 還原 HTML 跳脫字元（411 個酒名、1,898 篇筆記，最多的是 `&mdash;`、`&egrave;`、`&euro;`）
   - 把連續空白、換行、tab 合併成一個空格，並去除前後空白（16,314 篇筆記、6,861 個酒名有前後空白；1,256 篇有連續空白）
   - 在筆記的段落標籤（`Colour`、`Nose`、`With water`、`Mouth`、`Finish`、`Comments` 等）前換行。99.3% 的筆記依 Colour → Nose → Mouth → Finish → Comments 的順序書寫，換行後 LLM 與前端都能看出段落。開頭的引言保留，常含裝瓶背景、價格、是否有泥煤等資訊
3. 排除資料：
   - 酒名不含括號的 16 筆：這些「酒名」其實是一句話（如 `Let's try another one...`），無法辨識是哪支酒。另有 2 筆威士忌因酒名少了左括號一併被排除，先接受
   - 非威士忌烈酒，符合任一條件即排除：
     - 酒名括號內以逗號分隔的項目中，有任一項（去掉開頭的 `la `）整項等於烈酒類別（`cognac`、`bas-armagnac`、`grande champagne`、`borderies`、`agricole`、`tequila`、`mezcal`、`cachaça` 等）或蘭姆酒、龍舌蘭產地（`jamaica`、`guyana`、`barbados`、`martinique` 等）；或含有 `rhum` 但不含 `whisky`（法國獨立裝瓶商 `Whisky & Rhum` 旗下是威士忌）。只比對整項，`rum cask finish` 這類過桶描述不會誤刪
     - 品牌名（酒名開頭到第一個數字、引號或括號之前）本身是上述類別或產地（如 `Jamaica 1990`），或含有 `rum`、`rhum`（如 `Jamaican Rum`）
     - 同品牌有 10% 以上被判定為非威士忌：許多蘭姆酒的酒名只寫酒廠名（如 `Hampden 8 yo (56.5%, Kintra)`）。實測非威士忌品牌至少 14%，威士忌酒廠因特例被誤判的最多約 6%
   - 波本、裸麥、調和、穀物威士忌都保留。目前已知 Kavalan 有 1 筆以 `rum` 標示桶型而被誤刪；仍有少數漏網的非威士忌（例如酒名寫成 `Frapin … Grande Champagne …` 而不在括號內），先接受
4. 解析 `SCORE`：
   - `points`：取緊貼 `points` 前的整數（多位評審如 `OH 92 DB 88 SV 91 points` 會取到 91）；解析不到則為 `null`（1 筆）
   - `sgp`：`SGP` 後的三位數字；不是三位數（如 `SGP:???`、`SGP: -`）則為 `null`（43 筆）
5. 輸出 `data/whisky_clean.json`，共 14,555 筆，格式：

```json
{ "id": 4, "name": "Ben Nevis 15 yo 1998/2014 (57.7%, ...)", "note": "...\nColour: white wine.\nNose: ...", "points": 89, "sgp": "551" }
```

6. 被排除的 2,791 筆另存 `data/whisky_excluded.json`，供人工檢查篩選規則有沒有誤刪。`reason` 是排除原因，`matched` 是觸發排除的詞（同品牌推斷時為品牌名）：

```json
{ "id": 29, "name": "La Mauny 5 ans d'âge (45%, OB, Martinique, agricole, +/-1990)", "reason": "非威士忌烈酒", "matched": "martinique", "note": "..." }
```

**腳本 2：組 chunk、embedding、寫入資料庫**（尚未實作）

1. 讀取 `data/whisky_clean.json`
2. 組 chunk：一筆資料一個 chunk，內容為 `name` + 空行 + `note`
   - 不再切細：最長約 3,100 字元（約 770 token），遠低於 `bge-m3` 的 8,192 token 上限；切開會讓口感段落和酒名分離
   - 一定要包含 `name`：許多筆記內文不提酒名，少了它檢索不到，LLM 也不知道在講哪支酒
   - 不放分數：數字對語意檢索幫助不大，`points`、`sgp` 存進 `documents.metadata` 供之後篩選、排序
3. 用 `bge-m3` 產生每個 chunk 的 embedding
4. 寫入 `documents` 和 `chunks`

已知但先不處理的資料問題（第 2 階段用評估集確認影響後再決定）：

- 約 800 篇筆記依賴上下文，例如 `Nose: same as above`、`same cask`；單獨被檢索到時資訊不足
- 86 篇筆記結尾被截斷；約 690 篇開頭不完整（沒有 `Colour`/`Nose` 段落）
- 275 組同名酒款有多篇不同筆記（同一支酒品飲多次），全部保留
- 4 篇筆記內含多支酒的品飲紀錄

### 問答（`/api/chat`）

1. 用 `bge-m3` 產生問題的 embedding
2. 用 cosine 距離從 `chunks` 取出最相近的前 k 筆（k 預設為 5，寫在設定檔）
3. 把切塊加上編號 `[1]`、`[2]`… 組進 prompt，要求 Claude 根據這些資料回答，並以編號標註引用
4. 回傳 Claude 的回答與來源清單

> **待定**：知識庫找不到相關資料時要怎麼回應，留到後續 polish 階段再決定。

## 7. API

### `POST /api/chat`

**Request**

```json
{ "question": "有沒有泥煤味不重、帶果香的艾雷島威士忌？" }
```

`question` 不可為空，長度上限 1000 字。

**Response**：`application/json`

```json
{
  "answer": "可以從 Bunnahabhain 12 開始…… [1]",
  "sources": [
    { "id": 1, "title": "...", "source": "...", "content": "..." }
  ]
}
```

- `answer`：Markdown 格式的回答，以 `[n]` 標註引用
- `sources`：本次引用的來源，`id` 對應回答中的 `[n]`；沒有引用時為空陣列
- `question` 驗證失敗時回傳 422

## 8. 前端需求

- 介面和回答都使用繁體中文
- 視覺設計見下方「視覺設計」小節
- 輸入框會隨內容自動長高；Enter 換行，只有點「提問」按鈕才會送出
- 回答使用 Markdown 渲染
- 回答下方顯示來源，點開可以看到原文片段；原文保留換行（`white-space: pre-line`），段落才看得出來
- 載入中、錯誤都要有明確的狀態提示
- 等待回答時不能重複送出

### 視覺設計：酒窖帳冊

概念取自蘇格蘭傳統酒窖：管理員手寫的帳冊，加上酒桶端面用模板噴漆標記的桶號。回答呈現為帳冊條目，引用編號呈現為桶號，點開可查看原文。整個介面唯一的大膽設計放在桶號標記上，其餘保持克制。

**配色**（僅淺色模式）

| 名稱 | 色碼 | 用途 |
|---|---|---|
| Limewash | `#E9EAE6` | 背景 |
| Char | `#2B2420` | 主要文字 |
| Oak | `#9C8268` | 只用於分隔線與輸入框底線；對背景僅 2.99:1，不可用於文字 |
| Sherry | `#7A2E22` | 只用於桶號標記 |
| Spirit | `#C8892E` | 串流加回後用於輸入游標；對背景僅 2.46:1，不可用於 focus 外框 |
| Spirit Deep | `#A8681A` | 鍵盤 focus 外框（3.73:1，符合非文字元素 3:1 的對比要求） |

次要文字一律使用 Char。

**字體**（Google Fonts）

- LXGW WenKai TC：所有中文文字（少數字採舊字形，例如「為」顯示為「爲」，已確認接受）
- Big Shoulders Stencil：只用於桶號標記與 Logo

**版面**

- 單欄、靠左對齊，每行最多約 34 個中文字
- 不使用聊天泡泡；每組問答是一筆條目：問題為標題、回答為內文、來源為條目下方的紀錄列
- 來源列顯示桶號與文件標題，點擊後就地展開原文片段
- 輸入區呈現為帳冊橫線：空白狀態時位於畫面中央（標題與範例問題之間），開始對話後固定在畫面底部
- 空白狀態顯示三個範例問題，點擊後填入輸入框（不直接送出），讓使用者可以先修改：
  - 泥煤味不重、帶果香的艾雷島威士忌有哪些？
  - Lagavulin 16 和 Laphroaig 10 差在哪？
  - 雪莉桶熟成會帶來什麼風味？

**動態效果**

- 只有一個：回答出現時，桶號標記依序以蓋章方式出現
- 不加入進場動畫與 hover 效果；系統設定減少動態效果時直接顯示

**文案**

- 送出按鈕寫「提問」
- 錯誤訊息須說明原因與處理方式，例如：「無法連線到伺服器。請確認後端已啟動，再重新提問。」
- 未引用來源時顯示：「這次回答沒有引用知識庫資料。」

## 9. 設定（`backend/.env`）

| 變數 | 說明 |
|---|---|
| `DATABASE_URL` | PostgreSQL 連線字串 |
| `ANTHROPIC_API_KEY` | Claude API 金鑰 |
| `CLAUDE_MODEL` | Claude 模型 ID |
| `RETRIEVAL_TOP_K` | 檢索筆數，預設 5 |

## 10. 開發順序

1. 用 `docker-compose.yml` 跑起 PostgreSQL + pgvector，建立資料表
2. 後端：用假資料串通 `/api/chat`
3. 前端：完成聊天介面，接上 `/api/chat`
4. 拿到資料後：完成資料匯入腳本
5. 把真正的檢索和 Claude 接進 `/api/chat`

## 11. 待決定事項

- 查無相關資料時的回應方式
- 部署方式

## 12. 後續路線圖

> 以下是 MVP 之後的方向，**目前不做**。每個階段開始前，再把細節寫進這份規格書。

### 第 2 階段：評估與優化

- 建立評估集：30 到 50 個問題，每題標註應該取回的資料
- 量化指標：檢索命中率（recall@k）、回答是否忠於資料（用 LLM 當評審）
- 加入混合檢索（關鍵字 + 向量）、rerank、metadata 過濾，並用評估集比較改善前後的數字

### 第 3 階段：Agent 與工具使用

- 自己寫 tool use 迴圈，不使用 agent 框架
- 工具：語意檢索、依產區/價格/年份查詢（SQL）、比較多支酒
- 支援多輪對話
- 有餘力的話，把知識庫包成 MCP server

### 第 4 階段：工程化

- 部署到雲端，提供可以直接使用的網址
- 記錄每次請求的 token 用量、成本、延遲
- 補上核心邏輯的測試
- README：架構圖、技術決策的理由、評估結果
