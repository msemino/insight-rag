# InsightRAG

Self-hosted, local-first **AI customer-insight assistant** for regulated domains.
A compact reference implementation of a production RAG stack: hybrid retrieval
(vector + knowledge graph), compliance-aligned prompting, full observability,
domain fine-tuning, and a versioned deployment path.

Built to run entirely on a single RTX 3090 (24 GB), scaling to frontier
endpoints on demand.

---

## Why this exists

Most RAG demos stop at "embed a PDF, ask a question." Real deployments in
regulated industries (pharma, finance, health) need the parts that are hard:
traceability, compliance guardrails, low false-positive prompting, model/prompt
versioning, and an observability layer that a compliance officer can audit.

InsightRAG implements those parts end-to-end over a simulated
Healthcare-Professional (HCP) knowledge base built from public regulatory and
clinical documents — no sensitive data.

## Architecture

```
             ┌──────────────┐
   query ──▶ │  FastAPI API │ ──▶ trace ──▶ Langfuse (obs)
             └──────┬───────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
  Vector retrieval        Graph retrieval
  (Qdrant + embeddings)   (Neo4j / GraphRAG)
        └───────────┬───────────┘
                    ▼
        Compliance-aligned prompt layer
        (versioned system prompts + guardrails)
                    ▼
        Local LLM (Qwen3.6 / Ollama, RTX 3090)
        + on-demand frontier fallback
        + optional domain LoRA adapter
```

## Capabilities

| Area | What it does | Status |
|---|---|---|
| **RAG** | Vector store (Qdrant), chunking, hybrid retrieval | wk1 |
| **Observability** | Per-query traces, latency/cost/error dashboards, eval harness | wk2 |
| **Knowledge graph** | Neo4j entity/relation store, GraphRAG hybrid answers | wk3 |
| **Fine-tuning** | Domain LoRA/QLoRA adapter (unsloth) with a custom dataset | wk4 |
| **MLOps** | Versioned model+prompt endpoints, CI/CD (GitHub Actions) | wk4 |
| **Compliance** | Versioned system prompts + guardrails to cut false positives | ongoing |

## Design principles

- **Local-first, frontier on-demand.** Resolve locally when local capacity
  clears the task threshold; escalate on evidence of insufficiency, not reflex.
- **Backend-agnostic.** The same call path targets local Ollama or a frontier
  endpoint via env var.
- **Everything traced.** No black-box calls: latency, tokens, retrieval hits and
  prompt version are logged for every request.

## Quickstart

```bash
python app/llm.py          # smoke-test the local LLM loop
# wk1+ : ingest, serve, query  (see docs per module)
```

## Stack

Python · Ollama (Qwen3.6, RTX 3090) · Qdrant · Neo4j · Langfuse · FastAPI ·
unsloth (LoRA) · GitHub Actions
