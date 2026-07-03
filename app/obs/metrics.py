"""Aggregate metrics over the trace log: latency, tokens, error rate, retrieval."""
from __future__ import annotations
import os
import json
from app.obs.tracing import read_traces

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _pct(sorted_vals, p):
    if not sorted_vals:
        return None
    k = max(0, min(len(sorted_vals) - 1, round((p / 100) * (len(sorted_vals) - 1))))
    return sorted_vals[k]


def compute() -> dict:
    tr = read_traces()
    n = len(tr)
    lat = sorted(t["latency_ms"] for t in tr if t.get("latency_ms") is not None)
    pin = [t["prompt_tokens"] for t in tr if t.get("prompt_tokens")]
    pout = [t["completion_tokens"] for t in tr if t.get("completion_tokens")]
    errs = sum(1 for t in tr if t.get("error"))
    scores = [t["top_score"] for t in tr if t.get("top_score") is not None]
    return {
        "requests": n,
        "errors": errs,
        "error_rate": round(errs / n, 3) if n else 0.0,
        "latency_ms": {
            "p50": _pct(lat, 50), "p95": _pct(lat, 95),
            "avg": round(sum(lat) / len(lat)) if lat else None,
            "max": lat[-1] if lat else None,
        },
        "tokens": {
            "avg_prompt": round(sum(pin) / len(pin)) if pin else None,
            "avg_completion": round(sum(pout) / len(pout)) if pout else None,
        },
        "retrieval": {
            "avg_top_score": round(sum(scores) / len(scores), 3) if scores else None,
        },
    }


if __name__ == "__main__":
    m = compute()
    out = os.path.join(_ROOT, "app", "obs", "metrics.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)
    print(json.dumps(m, indent=2))
    print("wrote", out)
