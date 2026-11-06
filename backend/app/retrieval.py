import os

import numpy as np
import psycopg
from openai import OpenAI
from pgvector.psycopg import register_vector
from sentence_transformers import CrossEncoder

from app.schemas import Source

# 沒設定環境變數時，預設連 docker-compose 起的開發資料庫（帳密只用於本機開發）
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://whiskey:whiskey@localhost:5434/whiskey")
# 必須和 scripts/ingest.py 匯入時用的模型相同，向量才能互相比較
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
RERANK_MODEL = os.environ.get("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

client = OpenAI(timeout=30)
# 小模型常駐記憶體只要約 100 MB，CPU 上也夠快；只讀前 512 token，平均約 270 token 的筆記大多讀得完
reranker = CrossEncoder(RERANK_MODEL)


def embed_query(question: str) -> np.ndarray:
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=question)
    return np.array(response.data[0].embedding, dtype=np.float32)


def retrieve(question: str, top_k: int) -> list[Source]:
    query = embed_query(question)
    with psycopg.connect(DATABASE_URL) as conn:
        register_vector(conn)
        # ORDER BY 要直接用 <=> 由小到大排並搭配 LIMIT，HNSW 索引才會被使用
        rows = conn.execute(
            "SELECT d.title, d.source, c.content, d.metadata->>'image' "
            "FROM chunks c JOIN documents d ON d.id = c.document_id "
            "ORDER BY c.embedding <=> %s "
            "LIMIT %s",
            (query, top_k),
        ).fetchall()

    # id 用排名而非資料庫 id：prompt 裡的資料編號就是它，LLM 的介紹靠它對回酒款
    sources = []
    for rank, (title, source, content, image) in enumerate(rows, start=1):
        # chunk 開頭的酒名是為了讓 embedding 檢索得到；回傳時已有 title，去掉避免重複
        text = content.removeprefix(f"{title}\n\n")
        sources.append(
            Source(id=rank, title=title, source=source, content=text, image=image)
        )
    return sources


def rerank(query: str, sources: list[Source], top_k: int) -> list[Source]:
    # cross-encoder 同時讀查詢與整篇筆記再評分，能分辨向量看不出的細節（例如多重條件）；
    # 酒名一起送入，和實驗時的輸入一致
    pairs = []
    for source in sources:
        pairs.append((query, f"{source.title}\n\n{source.content}"))
    scores = reranker.predict(pairs)

    ranked = sorted(zip(scores, sources, strict=True), key=lambda pair: pair[0], reverse=True)
    # 重新編號：id 是 prompt 裡的資料編號，維持 1 到 top_k，和最後的推薦順序一致
    results = []
    for rank, (_, source) in enumerate(ranked[:top_k], start=1):
        results.append(source.model_copy(update={"id": rank}))
    return results
