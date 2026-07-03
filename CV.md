# Marcelo Semino
**AI / LLM Engineer · RAG & LLM-Ops · Local-first Inference · MLOps**
Buenos Aires, Argentina (Remote · UTC-3) · msemino@gmail.com · linkedin.com/in/marcelosemino · github.com/msemino

---

## Professional Summary

AI/LLM Engineer who builds and operates production LLM systems end-to-end: RAG
pipelines, vector databases, compliance-aligned prompting, observability, and
MLOps deployment. I run self-hosted inference on an RTX 3090 (24GB) with Ollama —
tuning models, managing context windows, and integrating LLMs into real systems,
with on-demand escalation to frontier endpoints when the task requires it.

Background: 30+ years in systems engineering and enterprise infrastructure (IBM,
critical-infrastructure operations). I reached LLM work through production needs,
not research — so I treat LLMs as infrastructure components with latency, cost,
reliability, compliance and failure modes, not as magic.

I build LLM-powered systems that work in production and keep working — and I
document them so a non-technical stakeholder or a compliance officer can follow
what the system does and why.

---

## Core Skills

**LLM Application Engineering**
RAG pipelines (chunking, retrieval, synthesis) · Vector databases (Qdrant) ·
Embeddings (local, nomic-embed-text) · Knowledge-graph / GraphRAG (Neo4j) ·
Compliance-aligned & few-shot prompt engineering · Prompt versioning · Structured
/ JSON output · Guardrails to reduce false positives

**LLM-Ops & Observability**
Per-request tracing (latency / tokens / retrieval hits) · Langfuse · Eval
harnesses · Prompt & model version control · Latency and cost optimization ·
Failure-mode analysis

**Inference & Model Ops**
Ollama · CUDA (RTX 3090 24GB) · Flash attention · KV-cache tuning (q8\_0) ·
Context-window management · Quantization & VRAM trade-offs · Model selection
(quality vs. latency vs. VRAM) · LoRA/QLoRA fine-tuning (unsloth)

**Deployment & Infrastructure**
FastAPI inference endpoints · Docker · Linux · systemd · GitHub Actions (CI/CD) ·
Tailscale · Cloudflare Workers · Python · Playwright · Git

**Agents & Orchestration**
LangGraph · Multi-agent coordination · Tool-use / function calling · Progressive
tool disclosure · Agent state management · Hermes (custom orchestrator)

---

## Selected Projects

### InsightRAG — self-hosted customer-insight assistant for regulated domains *(2026)*
*A compact, production-shaped RAG platform · github.com/msemino/insight-rag*

Reference implementation of the exact stack a regulated-industry AI product needs
(RAG + compliance + observability + knowledge graph + fine-tuning + deployment),
running entirely on a single RTX 3090.

- **RAG in production shape**: document ingestion → chunking → local embeddings
  (nomic-embed-text) → **Qdrant** vector store → grounded synthesis with a local
  LLM. Fully offline, no cloud API dependency.
- **Compliance-aligned prompting**: versioned system prompts enforcing on-label-only
  answers, fair balance (efficacy always paired with safety), no superiority
  claims, and source-grounded responses. Tuned so off-label questions get a
  *scoped refusal plus on-label facts* — reducing false positives instead of
  over-blocking legitimate queries.
- **Observability by design**: every request emits a trace (prompt version,
  retrieval hits + scores, model, latency, token counts) — the audit trail a
  compliance/medical stakeholder can review.
- **Local-first, frontier on-demand**: backend-agnostic call path resolves locally
  and escalates only on evidence of insufficiency.
- **Hybrid GraphRAG**: a typed knowledge graph (products, classes, indications,
  reversal agents) is queried alongside vector search — structured triples plus
  reranked passages — for exact relations dense retrieval alone can miss.
- **MLOps**: versioned FastAPI endpoints exposing model + prompt version per
  response; offline unit tests; GitHub Actions CI (green).
- **Validated** on a simulated HCP knowledge base with reproducible demo cases and
  a compliance eval harness (grounding, fair balance, off-label refusal, honesty).
- **Fine-tuning pipeline ready**: instruction dataset built from the corpus + a
  LoRA/QLoRA training script (unsloth) sized for the RTX 3090.

### AI Platform Lab — LLM Engineer & Operator *(2024–Present)*
*Self-hosted production AI · github.com/msemino*

- **Latency optimization**: Hermes orchestrator (LangGraph) with a reasoning model.
  398s/call → 33s/call (**12×**, same hardware) via `reasoning_effort=low`, pruned
  tool lists, and progressive-disclosure skill loading.
- **VRAM management**: RTX 3090 (24GB), all-GPU loading via KV-cache `q8_0` + flash
  attention; 64K context in VRAM, no swap.
- **Model selection discipline**: documented quality/latency/VRAM trade-offs across
  models; chose per task type.
- **RAG local & Whisper pipeline**: offline document QA; WhatsApp voice →
  Whisper.cpp on GPU → structured text (<10s for 60s audio).
- **LLM-ops judgment**: on a price-audit agent, found the LLM sat on a critical
  path that didn't need it — removed it, cut latency 10× and improved accuracy.

---

## Experience

**ARSAT — Systems Engineer** *(2013–Present)* — Enterprise systems, change
management, IBM Maximo. Critical infrastructure, strict SLAs.

**IBM Global — Service Delivery Manager** *(2011–2013)* — Service delivery for
enterprise accounts. Cross-functional leadership, P&L, SLA accountability.

**AfterNet Improve Solutions — Founder & IT Architect** *(2005–2011)* — Complex
system integrations, full lifecycle from design to production handoff.

---

## Education & Certifications

Information Systems Engineering — UAI · MCT · MCSE/MCSA · MCITP · CCNA · CCNP ·
VMware VCP5 · **Lean Six Sigma Green Belt** · PM Orientation (IBM)

---

## Languages

Spanish (native) · **English (fluent)**

---

## Proof of Work

| Repo | What it shows |
|---|---|
| [`insight-rag`](https://github.com/msemino/insight-rag) | RAG + vector DB + compliance prompting + observability + HCP demo, local-first |
| [`local-agent-orchestrator`](https://github.com/msemino/local-agent-orchestrator) | LLM-ops: 398s→33s, VRAM tuning, model-selection log |
| [`self-hosted-ai-lab`](https://github.com/msemino/self-hosted-ai-lab) | Full platform: 2 nodes, inference, voice, agents |
| [`agente-book`](https://github.com/msemino/agente-book) | When to remove the LLM from the critical path |

*Remote · Async-first · Available immediately*
