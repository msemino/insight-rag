"""
FastAPI inference service — the deployable surface of InsightRAG.

Versioned endpoints expose model + prompt version on every response, so a
consumer (and an auditor) always knows which configuration produced an answer.
This is the MLOps contract: config is observable and pinned per request.

Run: uvicorn app.api:app --host 0.0.0.0 --port 8100
"""
from __future__ import annotations
import os
from fastapi import FastAPI
from pydantic import BaseModel

from app.rag.pipeline import answer as rag_answer, PROMPT_VERSION
from app.graph.hybrid import answer as graph_answer
from app.obs.metrics import compute
from app.llm import MODEL

SERVICE_VERSION = "0.4.0"

app = FastAPI(title="InsightRAG", version=SERVICE_VERSION)


class Query(BaseModel):
    question: str
    k: int = 4


@app.get("/health")
def health():
    return {"status": "ok", "service_version": SERVICE_VERSION,
            "model": MODEL, "prompt_version": PROMPT_VERSION}


@app.get("/metrics")
def metrics():
    return compute()


@app.post("/answer")
def answer(q: Query):
    """Dense RAG answer."""
    return rag_answer(q.question, k=q.k)


@app.post("/graph-answer")
def graph_answer_ep(q: Query):
    """Hybrid GraphRAG answer (vector + knowledge graph)."""
    return graph_answer(q.question, k=q.k)
