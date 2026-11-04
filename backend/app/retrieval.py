import os

import numpy as np
import psycopg
import torch
from pgvector.psycopg import register_vector
from sentence_transformers import CrossEncoder, SentenceTransformer

from app.schemas import Source

# 沒設定環境變數時，預設連 docker-compose 起的開發資料庫（帳密只用於本機開發）
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://whiskey:whiskey@localhost:5434/whiskey")

model = SentenceTransformer("BAAI/bge-m3")
# fp16 讓 VRAM 用量減半（約 1 GB），實驗確認排序結果不受影響
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", model_kwargs={"torch_dtype": torch.float16})


def embed_query(question: str) -> np.ndarray:
    return model.encode(question, normalize_embeddings=True)


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
