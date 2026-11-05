# Whiskey Assistant

描述你想要的風味，從一萬四千多篇真實品飲筆記中挑出三支威士忌，寫成貼近真實品飲的中文介紹。

![示範：輸入問題後，推薦紀錄依序出現](docs/images/demo.gif)

## 特色

- **用中文描述想喝的酒**：簡單的風味（「有沒有喝起來像巧克力、橘子皮的？」）或較專業的條件（「想找雪莉桶熟成、帶一點泥煤煙燻，有黑巧克力和皮革調性的」）都可以
- **查指定酒款**：輸入酒名（「Macallan 18 喝起來如何？」），找出該酒款與相近版本的品飲筆記並整理成風味介紹
- **點選風味標籤**：不知道怎麼描述時，點選蜂蜜、果乾、泥煤、皮革等標籤，自動組成問句
- **介紹來自真實品飲筆記**：每支酒附上一句話印象，以及香氣、口感、尾韻三段描述。內容只根據品飲者的筆記改寫，不由 LLM 憑空編造
- **只回答找酒的問題**：無關的問題不會硬推薦，而是引導使用者描述想要的風味

## 運作方式

```mermaid
flowchart LR
    Q[使用者問題] --> A[意圖判斷＋查詢改寫<br/>LLM]
    A -->|不是找酒| N[回傳引導提示]
    A -->|找酒| R[向量檢索 30 筆<br/>bge-m3 ＋ pgvector]
    R --> K[Re-rank 取前 3 支<br/>bge-reranker-v2-m3]
    K --> G[撰寫中文推薦卡<br/>LLM]
```

1. **意圖判斷與查詢改寫**：一次 LLM 呼叫同時判斷是否在找酒，並把中文問題改寫成英文品飲筆記的口吻，讓查詢和英文筆記的寫法一致
2. **向量檢索**：用 `bge-m3` 把查詢轉成向量，從 pgvector 取出最相近的 30 筆候選
3. **Re-rank**：cross-encoder 把查詢和每篇筆記成對讀入、逐篇評分，挑出最符合的 3 支
4. **撰寫推薦卡**：LLM 依筆記內容寫成中文介紹，以 Structured Outputs 取得固定格式；酒名一律由資料庫對回，避免被改寫或寫錯

## 技術亮點

- **不使用 LangChain 等框架**：RAG 各步驟自行實作，資料存取用 psycopg 撰寫原生 SQL
- **以實驗數據決定設計**：同一組 20 題中，推薦酒款符合需求的比例從 48% 提升到 83%。過程中也驗證了向量距離門檻無法判斷無關問題、改寫會讓推薦集中到少數酒款等現象，詳見[檢索品質改善紀錄](docs/retrieval-experiments.md)
- **兩階段檢索**：向量檢索負責「不漏掉」，cross-encoder re-rank 負責「排得準」
- **降低 prompt injection 影響**：使用者輸入以標記包起來並視為資料；LLM 只能輸出固定欄位

## 技術棧

| 項目 | 選擇 |
|---|---|
| 後端 | Python 3.12、FastAPI |
| 資料庫 | PostgreSQL 17 ＋ pgvector（HNSW 索引） |
| Embedding | `BAAI/bge-m3`（本機執行） |
| Re-rank | `BAAI/bge-reranker-v2-m3`（本機執行） |
| LLM | OpenAI Responses API（Structured Outputs） |
| 前端 | Vue 3、Vite、TypeScript |

## 本機執行

```bash
# 1. 資料庫（PostgreSQL ＋ pgvector，port 5434）
docker compose up -d

# 2. 後端（port 8010）
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
cp .env.example .env   # 填入 OPENAI_API_KEY
.venv/Scripts/uvicorn app.main:app --port 8010 --env-file .env

# 3. 前端（http://localhost:5290，/api 經 proxy 轉到後端）
cd frontend
npm install
npm run dev
```

## 已知限制與後續規劃

- 一次回答約需 15 到 18 秒（兩次 LLM 呼叫），之後考慮以串流逐張顯示
- 單純否定的需求（「完全沒有煙燻味」）仍可能推薦出煙燻酒
- 查詢改寫會把描述轉成常見的風味詞，不同問題容易推薦到少數相同酒款
- 後續規劃：建立評估集量化檢索品質、加入多輪對話、部署

完整規格與待決定事項見 [SPEC.md](SPEC.md)。
