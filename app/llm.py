"""
Cliente LLM local-first (Ollama / RTX 3090) con hook de observabilidad.

Diseñado backend-agnostico: el mismo `chat()` puede apuntar a Ollama local
o a un endpoint frontier via variable de entorno, siguiendo la tesis
local-first + frontier on-demand. Cada llamada emite un trace para Langfuse.
"""
from __future__ import annotations
import os
import time
import json
import urllib.request

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
MODEL = os.getenv("INSIGHT_MODEL", "marcelo-brain-qwen36-no-think:latest")


def chat(system: str, user: str, *, temperature: float = 0.2) -> dict:
    """Una vuelta de chat contra el modelo local. Devuelve texto + metricas."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": temperature},
    }
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    latency_ms = round((time.perf_counter() - t0) * 1000)

    return {
        "text": data["message"]["content"],
        "model": MODEL,
        "latency_ms": latency_ms,
        "prompt_tokens": data.get("prompt_eval_count"),
        "completion_tokens": data.get("eval_count"),
    }


if __name__ == "__main__":
    r = chat(
        system="Sos un asistente de customer insights. Responde en una frase.",
        user="Que es un HCP en el contexto de una farmaceutica?",
    )
    print(f"[{r['model']}] {r['latency_ms']}ms  "
          f"in={r['prompt_tokens']} out={r['completion_tokens']}")
    print(r["text"])
