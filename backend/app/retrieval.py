import os

import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

from app.schemas import Source

# 沒設定環境變數時，預設連 docker-compose 起的開發資料庫（帳密只用於本機開發）
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://whiskey:whiskey@localhost:5434/whiskey")

model = SentenceTransformer("BAAI/bge-m3")


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
