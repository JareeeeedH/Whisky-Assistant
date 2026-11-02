# Whiskey Assistant 規格書

## 1. 專案目標

Whiskey Assistant 是一個威士忌問答助手：使用者以自然語言提問，系統從威士忌知識庫檢索相關資料，交由 LLM 產生回答，並附上資料來源。

技術重點：

- **Python 後端**：FastAPI、PostgreSQL、API 設計
- **RAG**：資料切塊、embedding、向量檢索、prompt 組裝，**核心流程自行實作，不依賴 LangChain 等框架**，以完整掌握每個環節的行為與取捨

## 2. MVP 範圍

### 要做

- 資料匯入流程：讀取原始資料 → 切塊 → embedding → 寫入資料庫
- `POST /api/chat`：單輪問答，以 SSE 串流回傳答案和來源
- 前端聊天介面：具備專業質感的輸入互動視窗

### 不做（之後的規劃見第 12 節）

- 多輪對話（追問）
- 使用者登入
- 混合檢索、rerank、metadata 過濾
- 正式部署
- 測試（見 `CLAUDE.md`）

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
│   └── requirements.txt
├── frontend/             # Vue 3 專案
├── data/                 # 原始資料（待提供）
├── docker-compose.yml    # 開發用，只跑 PostgreSQL + pgvector
├── .env.example
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

### 資料匯入（離線執行的腳本）

1. 讀取 `data/` 裡的原始資料
2. 切塊：切法和大小**等資料到位後再決定**
3. 用 `bge-m3` 產生每個切塊的 embedding
4. 寫入 `documents` 和 `chunks`

### 問答（`/api/chat`）

1. 用 `bge-m3` 產生問題的 embedding
2. 用 cosine 距離從 `chunks` 取出最相近的前 k 筆（k 預設為 5，寫在設定檔）
3. 把切塊加上編號 `[1]`、`[2]`… 組進 prompt，要求 Claude 根據這些資料回答，並以編號標註引用
4. 以串流方式回傳 Claude 的回答，最後回傳來源清單

> **待定**：知識庫找不到相關資料時要怎麼回應，留到後續 polish 階段再決定。

## 7. API

### `POST /api/chat`

**Request**

```json
{ "question": "有沒有泥煤味不重、帶果香的艾雷島威士忌？" }
```

`question` 不可為空，長度上限 1000 字。

**Response**：`text/event-stream`（SSE），依序送出以下事件：

| 事件 | data | 說明 |
|---|---|---|
| `token` | `{"text": "..."}` | 回答的文字片段，會送出多次 |
| `sources` | `[{"id": 1, "title": "...", "source": "...", "content": "..."}]` | 本次引用的來源，`id` 對應回答中的 `[n]` |
| `done` | `{}` | 結束 |
| `error` | `{"message": "..."}` | 發生錯誤，之後不再送出其他事件 |

## 8. 前端需求

- 介面和回答都使用繁體中文
- 視覺風格依 frontend-design skill 從威士忌的元素發想，實作前先提出設計方案給使用者確認
- 輸入框會隨內容自動長高；Enter 送出、Shift+Enter 換行
- 回答以串流方式逐字顯示
- 回答使用 Markdown 渲染
- 回答下方顯示來源，點開可以看到原文片段
- 載入中、錯誤都要有明確的狀態提示
- 等待回答時不能重複送出

## 9. 設定（`.env`）

| 變數 | 說明 |
|---|---|
| `DATABASE_URL` | PostgreSQL 連線字串 |
| `ANTHROPIC_API_KEY` | Claude API 金鑰 |
| `CLAUDE_MODEL` | Claude 模型 ID |
| `RETRIEVAL_TOP_K` | 檢索筆數，預設 5 |

## 10. 開發順序

1. 用 `docker-compose.yml` 跑起 PostgreSQL + pgvector，建立資料表
2. 後端：用假資料串通 `/api/chat` 的 SSE 串流
3. 前端：完成聊天介面，接上串流
4. 拿到資料後：完成資料匯入腳本
5. 把真正的檢索和 Claude 接進 `/api/chat`

## 11. 待決定事項

- 資料來源（由使用者提供）
- 切塊策略
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
