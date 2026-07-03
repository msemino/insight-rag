"""
RAG pipeline: retrieve -> compliance-aligned prompt -> local LLM -> traced answer.

This is the core request path the FastAPI service (wk4) will expose. Every call
returns a trace dict (retrieval hits, prompt version, latency, tokens) so the
observability layer (wk2) can log it without changing this code.
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.llm import chat            # noqa: E402
from app.rag.store import search    # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROMPT_VERSION = "compliance_system_v1"


def _load_prompt() -> str:
    with open(os.path.join(_ROOT, "prompts", f"{PROMPT_VERSION}.md"), encoding="utf-8") as f:
        return f.read()


def answer(question: str, k: int = 4) -> dict:
    hits = search(question, k=k)
    context = "\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)
    system = _load_prompt().replace("{context}", context)
    result = chat(system=system, user=question)
    return {
        "question": question,
        "answer": result["text"],
        "sources": [h["source"] for h in hits],
        "trace": {
            "prompt_version": PROMPT_VERSION,
            "retrieval": [{"source": h["source"], "score": h["score"]} for h in hits],
            "model": result["model"],
            "latency_ms": result["latency_ms"],
            "prompt_tokens": result["prompt_tokens"],
            "completion_tokens": result["completion_tokens"],
        },
    }


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What is the mechanism of action of Jardiance?"
    r = answer(q)
    print("Q:", r["question"])
    print("A:", r["answer"])
    print("SOURCES:", r["sources"])
    print("TRACE:", r["trace"])
