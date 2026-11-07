# Whiskey Assistant 規格書

## 1. 專案目標

Whiskey Assistant 是一個威士忌推薦助手：使用者以自然語言描述想要的威士忌，系統從品飲筆記知識庫檢索最相近的酒款，交由 LLM 整理成中文推薦介紹。

技術重點：

- **Python 後端**：FastAPI、PostgreSQL、API 設計
- **RAG**：資料切塊、embedding、向量檢索、prompt 組裝

## 2. MVP 範圍

### 

- 資料匯入流程：讀取原始資料 → 切塊 → embedding → 寫入資料庫
- `POST /api/chat`：單輪問答，以 JSON 一次回傳推薦酒款
- 前端聊天介面：具備專業質感的輸入互動視窗



## 3. 技術選型

| 項目 | 選擇 |
|---|---|
| 後端框架 | FastAPI |
| 資料庫 | PostgreSQL + pgvector（開發時用 Docker 執行） |
| Embedding | OpenAI `text-embedding-3-small`（1536 維） |
| Re-rank | 本機 `cross-encoder/ms-marco-MiniLM-L-6-v2`（cross-encoder，約 90 MB，只支援英文） |

模型選擇的考量：原本使用本機的 `bge-m3` 與 `bge-reranker-v2-m3`，兩者常駐記憶體合計約 4 到 6 GB，部署平台依記憶體計費，費用約每月 $45 到 70。改用 embedding API 與小型 reranker 後，後端記憶體預估降到 1 GB 以下。查詢改寫後是英文、筆記也是英文，所以只支援英文的 reranker 就夠用。
| LLM | OpenAI API（模型 ID 寫在設定檔） |
| Python 套件管理 | pip + venv（`requirements.txt`） |
| 程式碼檢查 | ruff（設定在 `ruff.toml`） |
| 前端 | Vue 3 + Vite + TypeScript，UI 自己刻，不套元件庫 |

## 4. 專案結構

```
Whiskey-Assistant/
├── backend/
│   ├── app/
│   │   ├── main.py       # FastAPI 進入點與路由
│   │   ├── schemas.py    # API 的 request / response 格式
│   │   ├── retrieval.py  # 查詢 embedding、向量檢索與 re-rank
│   │   └── chat.py       # 分析問題、prompt 組裝、呼叫 LLM、串起問答流程
│   ├── db/schema.sql     # 資料表定義，資料庫第一次啟動時自動執行
│   ├── scripts/          # 資料清理與匯入腳本
│   ├── .env.example      # 設定範本；實際設定放 .env（不進 git）
│   └── requirements.txt
├── frontend/             # Vue 3 專案
├── data/                 # 原始資料與清理結果（不進 git）
├── docker-compose.yml    # 開發用，只跑 PostgreSQL + pgvector
├── ruff.toml
├── CLAUDE.md
└── SPEC.md
```

## 5. 資料庫結構

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id          BIGSERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    source      TEXT,                          -- 資料來源（網址或檔名）
    metadata    JSONB NOT NULL DEFAULT '{}',   -- 原始資料 id、分數（points、sgp）、圖片檔名（image）
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE chunks (
    id           BIGSERIAL PRIMARY KEY,
    document_id  BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index  INT NOT NULL,                 -- 在原文件中的順序
    content      TEXT NOT NULL,
    embedding    VECTOR(1536) NOT NULL,          -- text-embedding-3-small 的輸出維度
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
- `IMAGE_PATH`：酒瓶照片的路徑，如 `Material29/Macallan-18-OB.jpg`。圖片檔不在資料內，另存於公開 repo `JareeeeedH/fundata`，見第 8 節「酒瓶照片」

### 資料匯入（離線執行的腳本）

分成兩支腳本，中間產生 `data/whisky_clean.json`：清理只要幾秒、embedding 要很久，拆開後調整清理規則時不必重跑 embedding，也能直接打開檔案檢查清理結果。

**腳本 1：`backend/scripts/clean_data.py`**

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
   - `image`：取 `IMAGE_PATH` 的檔名，不保留 `MaterialNN` 資料夾
5. 輸出 `data/whisky_clean.json`，共 14,555 筆，格式：

```json
{ "id": 4, "name": "Ben Nevis 15 yo 1998/2014 (57.7%, ...)", "note": "...\nColour: white wine.\nNose: ...", "points": 89, "sgp": "551", "image": "Ben-Nevis-15-yo-1998-Acorn.jpg" }
```

6. 被排除的 2,791 筆另存 `data/whisky_excluded.json`，供人工檢查篩選規則有沒有誤刪。`reason` 是排除原因，`matched` 是觸發排除的詞（同品牌推斷時為品牌名）：

```json
{ "id": 29, "name": "La Mauny 5 ans d'âge (45%, OB, Martinique, agricole, +/-1990)", "reason": "非威士忌烈酒", "matched": "martinique", "note": "..." }
```

**腳本 2：`backend/scripts/ingest.py`**（組 chunk、embedding、寫入資料庫）

1. 讀取 `data/whisky_clean.json`
2. 組 chunk：一筆資料一個 chunk，內容為 `name` + 空行 + `note`
   - 不再切細：最長約 3,100 字元（約 770 token），遠低於 embedding 模型的 8,191 token 上限；切開會讓口感段落和酒名分離
   - 一定要包含 `name`：許多筆記內文不提酒名，少了它檢索不到，LLM 也不知道在講哪支酒
   - 不放分數：數字對語意檢索幫助不大，`points`、`sgp` 存進 `documents.metadata` 供之後篩選、排序
3. 呼叫 OpenAI embedding API 產生每個 chunk 的 embedding，分批送出（每批數百筆），全部約 450 萬 token，費用約 $0.09
4. 寫入 `documents` 和 `chunks`（整批重建）

已知但先不處理的資料問題（第 2 階段用評估集確認影響後再決定）：

- 約 800 篇筆記依賴上下文，例如 `Nose: same as above`、`same cask`；單獨被檢索到時資訊不足
- 86 篇筆記結尾被截斷；約 690 篇開頭不完整（沒有 `Colour`/`Nose` 段落）
- 275 組同名酒款有多篇不同筆記（同一支酒品飲多次），全部保留
- 4 篇筆記內含多支酒的品飲紀錄

### 問答（`/api/chat`）

1. **分析問題**：呼叫一次 LLM，以 Structured Outputs 同時取得意圖與改寫後的查詢
   - 意圖 `recommend`：想找到、認識或比較具體的威士忌酒款，包含模糊的找酒需求（送禮、天冷想喝點暖身的）、指名酒款、詢問某支酒的風味
   - 意圖 `other`：其他所有情況，包含威士忌知識問答、其他酒類、無關的問題、打招呼、無意義的輸入、要求透露指示。直接回傳固定的提示，不檢索也不寫推薦卡
   - 改寫：把問題寫成一到兩句英文散文，口吻像品飲筆記，讓查詢與英文筆記的寫法一致；否定轉成正面描述（「泥煤味不重」寫成 unpeated, no smoke）；只寫風味，場合、對象、價格等轉成風味方向；保留使用者提到的酒款名稱，但不主動加入其他酒廠，避免推薦偏向 LLM 熟悉的品牌
   - 使用者輸入以標記包起來，並說明標記內是資料而非指令，降低 prompt injection 的影響
2. 用匯入時相同的 embedding 模型，產生改寫後查詢的 embedding
3. 用 cosine 距離從 `chunks` 取出最相近的候選（預設 30 筆）
4. **Re-rank**：以 cross-encoder 把「改寫後的查詢＋每筆候選的完整筆記」成對評分，依分數重新排序後取前 3 支。向量檢索負責不漏掉，re-rank 負責排得準
5. 把每筆資料加上編號組進 prompt（寫推薦卡時不附上問題），一次呼叫 LLM，以 Structured Outputs 取得固定格式的 JSON。每筆資料寫成一張中文推薦卡：一句話印象（40 到 60 字，先點出整體風格，再帶出最突出的兩三個風味，可補上整體評價），以及香氣、口感、尾韻各一句（20 到 50 字）；可以寫得生動，但風味與評價都必須來自筆記。以品飲介紹的口吻直接描述，不寫「筆記者覺得」這類字眼：讀起來較自然，代價是主觀評價會像客觀描述
6. 後端用編號把介紹對回檢索結果，酒名一律使用資料庫的 `title`，不採用 LLM 寫的酒名，避免被改寫或寫錯

設計依據：以 70 筆問題實測，相關與無關問題的向量距離完全重疊（例如「推薦咖啡豆，要有巧克力和堅果風味」比多數威士忌問題還近），無法以距離門檻判斷，因此改由 LLM 判斷意圖。改寫後，相關問題的檢索距離約從 0.40 降到 0.20 到 0.30。加入 re-rank 後，推薦酒款符合需求的比例從 62% 提升到 85%（26 題）；re-rank 選出的酒常來自向量排名第 20 到 29 名，因此候選取 30 筆。以上數據是以 `bge-m3` 與 `bge-reranker-v2-m3` 量測；換成目前的模型後，以 20 題重新驗證，準確度為 87%（原本 83%）。實驗細節見 `docs/retrieval-experiments.md`。

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
  "recommendations": [
    { "title": "Bunnahabhain 12 yo (46.3%, OB, 2022)", "tagline": "一句話印象……", "nose": "香氣……", "palate": "口感……", "finish": "尾韻……", "image": "Bunnahabhain-12-OB.jpg" }
  ],
  "notice": null
}
```

意圖不是找酒時，同樣回傳 200：

```json
{ "recommendations": [], "notice": "目前只能幫你挑選威士忌。描述你想要的風味，例如「帶果香、不太煙燻的」。" }
```

- `recommendations`：推薦酒款，依檢索的相似度排序
  - `title`：酒名，來自資料庫
  - `tagline`：一句話印象，由 LLM 撰寫
  - `nose`、`palate`、`finish`：香氣、口感、尾韻各一句，由 LLM 撰寫；全部為純文字
  - `image`：酒瓶照片的檔名，網址由前端組出；沒有時為 `null`
- `notice`：問題不是要找酒時的提示文字，由後端固定提供；正常推薦時為 `null`。以獨立欄位表示，不讓前端從「推薦是空的」推測原因
- `question` 驗證失敗時回傳 422

## 8. 前端需求

- 介面和回答都使用繁體中文
- 視覺設計見下方「視覺設計」小節
- 輸入框會隨內容自動長高；Enter 換行，只有點「提問」按鈕才會送出
- 回答列出推薦酒款：酒瓶照片、酒名、一句話印象，以及香氣／口感／尾韻三行，不顯示評分與英文原文
- 酒名：由前端以第一個 `(` 切開，括號前為主標題；括號內只取前兩項（濃度、裝瓶商）以 ` / ` 連接成較小的第二行，`OB` 顯示為「原廠裝瓶」。桶號、瓶數等收藏家資訊不顯示
- 酒瓶照片：由前端以 `image` 組出網址，瀏覽器直接向 GitHub 載入；原圖自帶黃色外框，顯示時裁掉四邊；載入失敗時只留空白底與桶號
  - 網址：`https://raw.githubusercontent.com/JareeeeedH/fundata/master/whiskyfun/{資料夾}/{檔名}`
  - 資料夾是檔名中第一個英文字母的大寫（路徑區分大小寫），例如 `_balcones….jpg` 在 `B/`、`3-ships.jpg` 在 `S/`
  - 已知限制：少數照片與酒款不符（原始資料的問題，例如 Okayama 那筆指向 Akashi 的照片）；照片著作權屬 WhiskyFun
- 介紹以純文字顯示，不渲染 HTML
- 載入中、錯誤都要有明確的狀態提示
- 有 `notice` 時，在問題下方以一般內文顯示；它是引導而不是錯誤，不使用錯誤提示的樣式
- 等待回答時不能重複送出

### 視覺設計：酒窖帳冊

概念取自蘇格蘭傳統酒窖：管理員手寫的帳冊，加上酒桶端面用模板噴漆標記的桶號。回答呈現為帳冊條目，每支推薦酒款是一筆入庫紀錄，以桶號編號。整個介面唯一的大膽設計放在桶號標記上，其餘保持克制。

**配色**（僅淺色模式）

| 名稱 | 色碼 | 用途 |
|---|---|---|
| Limewash | `#E9EAE6` | 背景 |
| Paper | `#F7F7F4` | 只用於輸入框底色，比背景亮一階，讓書寫區浮出來 |
| Char | `#2B2420` | 主要文字、輸入框外框 |
| Oak | `#9C8268` | 只用於分隔線；對背景僅 2.99:1，不可用於文字 |
| Sherry | `#7A2E22` | 只用於桶號標記 |
| Spirit | `#C8892E` | 只以 30% 淡色作為「香氣／口感／尾韻」標籤與已選風味 tag 的底色，為頁面帶一點酒色；不可用於文字或外框 |
| Spirit Deep | `#A8681A` | 鍵盤 focus 外框；輸入框取得焦點時的外框與光暈（3.73:1，符合非文字元素 3:1 的對比要求） |

次要文字一律使用 Char。

**字體**（Google Fonts）

- LXGW WenKai TC：所有中文文字（少數字採舊字形，例如「為」顯示為「爲」，已確認接受）
- Big Shoulders Stencil：只用於桶號標記與 Logo

**版面**

- 靠左對齊，每行最多約 34 個中文字；窄螢幕為單欄（頁面最寬 40rem）
- 寬螢幕（64rem 以上）首頁放寬到 72rem，分成兩欄：左側為標題、輸入框、範例與風味 tag，右側為「酒瓶牆」；有回答後放寬到 78rem，三款推薦並排成三欄，方便一眼比較
- 酒瓶牆：3×3 張資料庫中的原廠裝瓶照片（從 24 張精選照片中每次隨機挑 9 張），白邊、各自略微歪斜，像釘在酒窖牆上的酒標；載入時依序貼上。純裝飾，對螢幕閱讀器隱藏，窄螢幕不顯示
- 有回答後整個畫面固定為一個視窗高：頁首與輸入框不動，只有中間有外框的對話框捲動；輸入框下方留約 10vh 的空白，不貼齊視窗底緣
- 不使用聊天泡泡；每組問答是一筆條目：問題為標題，下方是推薦酒款的紀錄
- 每筆推薦紀錄：左側為酒瓶照片（3:4），桶號（01、02、03）蓋在照片左上角；右側依序為酒名、裝瓶細節、一句話印象（字級比內文大）、香氣／口感／尾韻三行；紀錄之間以虛線分隔（單欄為橫線、三欄為直線），不做成卡片外框。三欄時照片放大到 8rem 寬（接近原圖寬度，再大會糊），酒名排在照片旁，內文跨滿整欄
- 輸入框是有外框的書寫欄位（Paper 底色、Char 外框），「提問」按鈕放在框內右下角
  - 空白狀態：位於標題與範例問題之間，預設約三行高、字級略大；整組內容緊接在頁首下方，不垂直置中（置中在高螢幕上會讓標題離頁首太遠）
  - 開始對話後：位於對話框下方，外框與對話框同寬
- 空白狀態的標題：「想找哪款威士忌呢？」，不放副標
- 空白狀態顯示五個範例問題，每題前面有靜態的桶號 01 到 05（不蓋章，動態只留給回答出現時）；點擊後填入輸入框（不直接送出），讓使用者可以先修改。範例用口語寫法，每題示範一種問法，並避開單純否定與價格（檢索仍會出錯、資料沒有價格）：
  - 想找雪莉桶、果乾味濃、香甜一點的（桶型）
  - 有沒有喝起來像巧克力、橘子皮的？（多重風味）
  - 想找雪莉桶熟成、帶一點泥煤煙燻，有黑巧克力和皮革調性的（專業條件）
  - Macallan 18 喝起來如何？（指定酒款）
  - Lagavulin 16 是什麼風味？（指定酒款）
- 範例下方為「或用風味挑選」：10 個風味 tag（蜂蜜、果乾、堅果、巧克力、辛香料、海風、泥煤、熱帶水果、皮革、蠟質），可多選，依點選順序組成「想找有○○、○○風味的」填入輸入框（不直接送出）；再點一次取消，改點範例問題時清除選取。不放果香、花香、橡木這類幾乎每篇筆記都有、沒有區分度的詞

**動態效果**

- 首頁：酒瓶牆的照片依序貼上
- 等待回答：顯示三個步驟（理解你想要的風味 → 從品飲筆記中找出候選 → 依筆記撰寫香氣、口感與尾韻），進行中的步驟以琥珀色方塊明暗起伏。後端沒有回報進度，依實測耗時推進，最後一步停留到回答出現
- 回答出現時：推薦紀錄的桶號依序以蓋章方式出現
- 不加入 hover 效果；系統設定減少動態效果時直接顯示

**文案**

- 送出按鈕寫「提問」
- 錯誤訊息須說明原因與處理方式，例如：「無法連線到伺服器。請確認後端已啟動，再重新提問。」

## 9. 設定（`backend/.env`）

| 變數 | 說明 |
|---|---|
| `DATABASE_URL` | PostgreSQL 連線字串 |
| `OPENAI_API_KEY` | OpenAI API 金鑰 |
| `LLM_MODEL` | OpenAI 模型 ID，預設 `gpt-6-luna` |
| `EMBEDDING_MODEL` | OpenAI embedding 模型 ID，預設 `text-embedding-3-small`；匯入與查詢必須相同，更換時要一併修改資料表維度並重新匯入 |
| `RERANK_MODEL` | cross-encoder 模型 ID，預設 `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| `CORS_ORIGINS` | 允許呼叫 API 的前端網址，多個以逗號分隔；只在部署時設定，本機開發走 Vite proxy 不需要 |

前端（建置時讀取，設定在部署平台上）：

| 變數 | 說明 |
|---|---|
| `VITE_API_BASE_URL` | 後端網址，例如 `https://xxx.up.railway.app`；本機開發不設定，以相對路徑 `/api` 經 Vite proxy 轉給後端 |
| `RETRIEVAL_CANDIDATES` | 向量檢索取出、交給 re-rank 的候選筆數，預設 30 |
| `RETRIEVAL_TOP_K` | re-rank 後推薦的酒款數，預設 3 |

## 10. 待決定事項

- 威士忌知識問答：例如「雪莉桶是什麼」，目前歸為 `other` 回傳提示，之後再決定是否支援
- 比較多支酒：例如「Ardbeg 跟 Laphroaig 差在哪」只產生一個查詢，結果可能只涵蓋其中一支；可考慮讓 LLM 產生多個查詢
- 個別酒款與問題不符時是否隱藏：例如資料庫中混有少數非威士忌的紀錄（蘭姆酒、干邑），可能被推薦出來
- 推薦集中到少數常客：LLM 改寫的用詞相近，不同問題常推薦出同樣的酒（30 題中前 5 名常客占 90 支的 22 支）；可測試合併「改寫查詢」與「原句」的候選再 re-rank，或調整改寫規則
- 單純否定仍會出錯：例如「完全沒有煙燻味」，改寫後的 unpeated、smoke-free 仍含有 peat、smoke；可要求改寫時完全不寫出被否定的風味
- 偏向老酒：約四分之一的推薦是 1990 年以前蒸餾或 30 年以上的酒，現實中多半難以取得
- 重複酒款：同一款酒的不同版本可能同時被推薦（例如三支不同年份的 Macallan 18），括號前名稱也不同，無法用簡單的同名判斷去除
- re-rank 分數門檻：目前一律推薦前 3 支，分數很低的酒也會顯示；需要更多數據才能決定門檻
- 部署方式

## 11. 後續路線圖

> 以下是 MVP 之後的方向，**目前不做**。每個階段開始前，再把細節寫進這份規格書。

### 第 2 階段：評估與優化

- 建立評估集：30 到 50 個問題，每題標註應該取回的資料
- 量化指標：檢索命中率（recall@k）、回答是否忠於資料（用 LLM 當評審）
- 細分意圖：把 `recommend` 拆成推薦、查酒款、比較、知識問答，各走適合的流程。例如查酒款改用酒名精確查詢，目前走語意檢索，「Macallan 18」會混入 Macallan 10、30
- 加入混合檢索（關鍵字 + 向量）、metadata 過濾，並用評估集比較改善前後的數字。酒名這類專有名詞，關鍵字比向量準；PostgreSQL 內建全文檢索，不必新增服務

### 第 3 階段：Agent 與工具使用

- 自己寫 tool use 迴圈，不使用 agent 框架
- 第一個情境：比較多支酒（「Ardbeg 跟 Laphroaig 差在哪」），由 LLM 決定查哪些酒、查幾次，並限制最多 3 到 4 輪
- 工具：語意檢索、依酒名查詢、依酒精度/酒齡/裝瓶商篩選（SQL，需先從酒名解析出欄位）、找風味相近的酒。資料沒有價格，產區需另建對照表
- 支援多輪對話
- 有餘力的話，把知識庫包成 MCP server

### 第 4 階段：工程化

- 部署到雲端，提供可以直接使用的網址
- 記錄每次請求的 token 用量、成本、延遲
- 補上核心邏輯的測試
- README：架構圖、技術決策的理由、評估結果
