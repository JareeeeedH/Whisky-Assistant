"""把清理過的品飲筆記組成 chunk、產生 embedding，寫入 PostgreSQL。

先跑 clean_data.py 產生 data/whisky_clean.json。流程與設計見 SPEC.md 第 6 節。

用法（在 backend/ 執行）：
    .venv/Scripts/python scripts/ingest.py --limit 100   # 隨機抽 100 筆試跑
    .venv/Scripts/python scripts/ingest.py               # 全部
"""

import argparse
import json
import os
import random
import time
from pathlib import Path

import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb
from sentence_transformers import SentenceTransformer

CLEAN_PATH = Path(__file__).resolve().parents[2] / "data" / "whisky_clean.json"

# 沒設定環境變數時，預設連 docker-compose 起的開發資料庫（帳密只用於本機開發）
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://whiskey:whiskey@localhost:5434/whiskey")


def build_chunk(record: dict) -> str:
    return f"{record['name']}\n\n{record['note']}"


def embed(texts: list[str]) -> np.ndarray:
    model = SentenceTransformer("BAAI/bge-m3")
    return model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
    )


def write_to_db(records: list[dict], chunks: list[str], vectors: np.ndarray) -> None:
    with psycopg.connect(DATABASE_URL) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            # 每次都整批重建：資料只有一萬多筆，比判斷哪些已存在、哪些要更新簡單得多
            cur.execute("TRUNCATE documents, chunks RESTART IDENTITY")
            for record, chunk, vector in zip(records, chunks, vectors, strict=True):
                cur.execute(
                    "INSERT INTO documents (title, source, metadata) "
                    "VALUES (%s, %s, %s) RETURNING id",
                    (
                        record["name"],
                        f"whiskyDataset.json#{record['id']}",
                        Jsonb(
                            {
                                "original_id": record["id"],
                                "points": record["points"],
                                "sgp": record["sgp"],
                                "image": record["image"],
                            }
                        ),
                    ),
                )
                document_id = cur.fetchone()[0]
                # 目前一筆資料只有一個 chunk，所以 chunk_index 固定為 0
                cur.execute(
                    "INSERT INTO chunks (document_id, chunk_index, content, embedding) "
                    "VALUES (%s, 0, %s, %s)",
                    (document_id, chunk, vector),
                )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, help="隨機抽樣的筆數，試跑用；不給就處理全部")
    parser.add_argument("--seed", type=int, default=42, help="抽樣用的亂數種子，固定才能重現")
    parser.add_argument("--dump", type=Path, help="另外把 chunk 與向量存成 JSON，供人工檢查")
    args = parser.parse_args()

    records = json.loads(CLEAN_PATH.read_text(encoding="utf-8"))
    if args.limit is not None:
        # 原始資料依酒廠排序，取前 N 筆會全是同一家酒廠，所以要隨機抽
        records = random.Random(args.seed).sample(records, args.limit)
    print(f"處理 {len(records)} 筆")

    chunks = [build_chunk(record) for record in records]

    started = time.perf_counter()
    vectors = embed(chunks)
    print(f"embedding 完成：{vectors.shape}，耗時 {time.perf_counter() - started:.1f} 秒")

    if args.dump is not None:
        dump = [
            {
                "id": record["id"],
                "name": record["name"],
                "chunk": chunk,
                "embedding": [round(float(x), 6) for x in vector],
            }
            for record, chunk, vector in zip(records, chunks, vectors, strict=True)
        ]
        args.dump.write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已存檔：{args.dump}")

    write_to_db(records, chunks, vectors)
    print("已寫入資料庫")


if __name__ == "__main__":
    main()
