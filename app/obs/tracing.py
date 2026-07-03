"""
Trace store. Every RAG request appends one JSON line here.

Local-first observability: no external service required, but the schema is a
superset of what Langfuse/Phoenix expect, so traces can be shipped to either
by a thin exporter without touching the pipeline.
"""
from __future__ import annotations
import os
import json
import time
import hashlib

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRACE_LOG = os.path.join(_ROOT, "app", "obs", "traces.jsonl")


def log_trace(question: str, answer: str, trace: dict, *, error: str | None = None) -> None:
    record = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "question": question,
        "question_id": hashlib.sha1(question.encode("utf-8")).hexdigest()[:10],
        "answer_chars": len(answer or ""),
        "error": error,
        **trace,
    }
    os.makedirs(os.path.dirname(TRACE_LOG), exist_ok=True)
    with open(TRACE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_traces() -> list[dict]:
    if not os.path.exists(TRACE_LOG):
        return []
    out = []
    with open(TRACE_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
