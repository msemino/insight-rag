"""
Vector store + embeddings, local-first.

Embeddings: nomic-embed-text via Ollama (RTX 3090). No cloud calls.
Vector DB: Qdrant in local/embedded mode (persists to ./qdrant_data, no server).
"""
from __future__ import annotations
import os
import json
import glob
import urllib.request

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
EMBED_MODEL = os.getenv("INSIGHT_EMBED", "nomic-embed-text")
COLLECTION = "hcp_kb"
_DIM = 768  # nomic-embed-text output dimension

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_QDRANT_PATH = os.path.join(_ROOT, "qdrant_data")


def embed(text: str) -> list[float]:
    payload = {"model": EMBED_MODEL, "prompt": text}
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))["embedding"]


def client() -> QdrantClient:
    return QdrantClient(path=_QDRANT_PATH)


def _chunk(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    """Simple char-window chunker with overlap. Splits on blank lines first."""
    blocks, cur = [], ""
    for para in text.split("\n\n"):
        if len(cur) + len(para) < size:
            cur += para + "\n\n"
        else:
            if cur.strip():
                blocks.append(cur.strip())
            cur = para + "\n\n"
    if cur.strip():
        blocks.append(cur.strip())
    return blocks


def ingest(data_glob: str) -> int:
    c = client()
    if c.collection_exists(COLLECTION):
        c.delete_collection(COLLECTION)
    c.create_collection(
        COLLECTION,
        vectors_config=VectorParams(size=_DIM, distance=Distance.COSINE),
    )
    points, pid = [], 0
    for path in sorted(glob.glob(data_glob)):
        source = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for chunk in _chunk(text):
            vec = embed(chunk)
            points.append(PointStruct(
                id=pid, vector=vec,
                payload={"source": source, "text": chunk},
            ))
            pid += 1
    c.upsert(COLLECTION, points)
    return len(points)


def search(query: str, k: int = 4) -> list[dict]:
    c = client()
    hits = c.query_points(COLLECTION, query=embed(query), limit=k).points
    return [{"source": h.payload["source"],
             "text": h.payload["text"],
             "score": round(h.score, 3)} for h in hits]


if __name__ == "__main__":
    import sys
    n = ingest(os.path.join(_ROOT, "data", "*.md"))
    print(f"Ingested {n} chunks into '{COLLECTION}' at {_QDRANT_PATH}")
