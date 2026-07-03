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
| **RAG** | Vector store (Qdrant), chunking, dense retrieval | ✅ done |
| **Observability** | Per-query trace store, latency/token/error metrics, compliance eval harness (4/4), HTML dashboard | ✅ done |
| **Knowledge graph** | networkx entity/relation graph + hybrid GraphRAG (vector + graph expansion + rerank); Neo4j-ready schema | ✅ done |
| **MLOps** | Versioned FastAPI endpoints (model+prompt version per response), offline unit tests, GitHub Actions CI | ✅ done |
| **Fine-tuning** | Domain compliance **LoRA adapter trained on the RTX 3090** (bf16, rank 16, native Windows); A/B shows scoped off-label refusal held with a one-line prompt | ✅ done |
| **Compliance** | Versioned system prompts + guardrails; scoped off-label refusal to cut false positives | ✅ ongoing |

## Run it

```bash
pip install -r requirements.txt          # + Ollama with a chat model & nomic-embed-text
python -m app.rag.store                  # ingest corpus -> Qdrant
python demo_cases.py                     # 4 compliance demo cases
python -m app.graph.kg                   # build knowledge graph
python -m app.graph.hybrid "What class is Jardiance and what is it indicated for?"
python -m app.obs.evaluate               # compliance eval harness (CI-style)
python -m app.obs.dashboard              # render observability dashboard
python tests/test_core.py                # offline unit tests (what CI runs)
uvicorn app.api:app --port 8100          # versioned inference API
```

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
