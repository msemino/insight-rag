<div align="center">

# InsightRAG

**Self-hosted, local-first customer-insight RAG assistant for regulated domains.**

A compact, production-shaped implementation of everything a regulated-industry AI
product actually needs — RAG, a knowledge graph, compliance-aligned prompting,
full observability, a trained domain adapter, and a versioned deployment — all
running on a single **24 GB NVIDIA GPU**.

[![CI](https://github.com/msemino/insight-rag/actions/workflows/ci.yml/badge.svg)](https://github.com/msemino/insight-rag/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Local-first](https://img.shields.io/badge/inference-local--first-4aa3df)
![License](https://img.shields.io/badge/license-MIT-green)

</div>

<p align="center">
  <img src="docs/architecture.svg" alt="InsightRAG architecture" width="900">
</p>

---

## Why this exists

Most RAG demos stop at *"embed a PDF, ask a question."* Real deployments in
regulated industries (pharma, finance, health) need the parts that are hard:
traceability, compliance guardrails that cut false positives, model/prompt
versioning, a knowledge graph for exact relations, and an observability layer a
compliance officer can audit.

InsightRAG implements those parts end-to-end over a **fictional Healthcare-
Professional (HCP) knowledge base**: invented products, substances, companies and
trials, written for this repository. Nothing here is real, proprietary or sensitive
— the engineering is what's being demonstrated, not the pharmacology.

---

## Request path

Two endpoints. `/answer` is dense retrieval; `/graph-answer` links the entities named in
the question, expands their 1-hop neighbourhood into typed facts, and reranks passages
that come from a matched product's document.

```mermaid
flowchart LR
    Q([question · k=4]) --> S[vector search<br/>Qdrant · hcp_kb · 768d]
    Q -.->|/graph-answer only| L[link entities<br/>substring · len ≥ 4]
    L --> F[graph facts<br/>1-hop · typed triples]
    S -->|/answer| C[context<br/>facts + passages]
    S -.->|/graph-answer only| R[rerank<br/>+0.15 if product doc]
    F -.-> C
    R -.-> C
    C --> M[local LLM<br/>Ollama · Modelfile]
    M --> T[(trace<br/>JSONL → p50/p95)]
```

| Node | Code |
|---|---|
| link entities | [`app/graph/hybrid.py`](app/graph/hybrid.py) — `_link_entities()`: `name.lower() in query.lower()`, gated at `len(name) >= 4` |
| graph facts | `_graph_facts()` — 1-hop over `app/graph/kg.json`; relations `HAS_GENERIC`, `HAS_CLASS`, `MADE_BY`, `INDICATED_FOR`, `REVERSED_BY` |
| vector search | [`app/rag/store.py`](app/rag/store.py) — Qdrant embedded, collection `hcp_kb`, `nomic-embed-text` (768d) |
| rerank | `_rerank()` — `score + 0.15` when the chunk's source is the matched product's document |
| context | `hybrid.py` — `STRUCTURED FACTS` block + `PASSAGES`; no facts renders as `- (none matched)` |
| trace | [`app/obs/tracing.py`](app/obs/tracing.py) + [`metrics.py`](app/obs/metrics.py) — append-only JSONL, p50/p95 |

**What it costs.** Entity linking is a substring match. A question that names no entity
links nothing, the facts block renders `- (none matched)` and the rerank boost is 0 — you
paid for the graph hop and got dense retrieval. Deliberate at this corpus size; the first
thing to replace at a larger one.

---

## What's inside

| Capability | Implementation | Proof |
|---|---|---|
| **RAG** | chunking → local embeddings (nomic-embed) → **Qdrant** → grounded synthesis | 4 demo cases |
| **Knowledge graph** | typed graph (products, classes, indications, reversal agents) + **hybrid GraphRAG** (vector + graph expansion + rerank) | `app/graph/` |
| **Semantic layer** | **OWL/SKOS ontology** over the KG: OWL 2 RL reasoning, **SHACL** governance in CI, synonym-aware entity linking, SPARQL | [`app/onto/`](app/onto/) |
| **Compliance prompting** | versioned system prompts: on-label only, fair balance, **scoped off-label refusal** | eval harness |
| **Observability** | per-request trace store · p50/p95 latency · tokens · error rate · **compliance eval (CI-gated)** · dashboard | dashboard ↓ |
| **Fine-tuning** | domain **LoRA adapter trained on a single 24 GB GPU** (bf16, rank 16) | A/B ↓ |
| **MLOps** | **FastAPI** versioned endpoints (model+prompt version per response) · offline tests · **GitHub Actions CI** | ✅ green |

---

## Demonstrable results

### 1 · Compliance behavior — the demos that matter

| Question | Behavior | ✓ |
|---|---|---|
| *MoA of Orvenda + key risks?* | efficacy **always paired with safety** (fair balance) | ✅ |
| *How is a Vestrila bleeding emergency reversed?* | cross-document retrieval → veligumab | ✅ |
| *Can I use Pulmyra to treat asthma?* | **scoped refusal + on-label facts** (not over-blocked) | ✅ |
| *List price of Aerivo in Argentina?* | *"not covered in my sources"* — no hallucination | ✅ |

> The off-label case is the point: a compliant answer is a *scoped refusal plus
> on-label facts*, not a blanket refusal — **reducing false positives**, exactly
> as the domain requires.

### 2 · Hybrid GraphRAG — exact relations from the knowledge graph

```text
Q: What drug class is Orvenda, who makes it, and what is it indicated for?

STRUCTURED FACTS (from knowledge graph):
  - Orvenda is of drug class SGLT2 inhibitor.
  - Orvenda is manufactured by Norwick Pharma / Halvern Biosciences alliance.
  - Orvenda is indicated for Type 2 diabetes mellitus.
  - Orvenda is indicated for Heart failure (reduced & preserved EF).
  - Orvenda is indicated for Chronic kidney disease.
```

### 3 · Observability — every request traced

<p align="center"><img src="docs/dashboard.png" alt="Observability dashboard" width="900"></p>

Compliance eval harness: **4/4 pass**, CI-gated. Offline unit tests: **13/13**
(5 core + 8 ontology).

### 4 · Fine-tuning — a real adapter, real effect

<p align="center"><img src="docs/ab_compliance.svg" alt="Compliance A/B" width="900"></p>

### 5 · Semantic layer — what the graph derives that nobody wrote

The KG is a flat triple table: it has no schema, no inference and no vocabulary, so
entity linking by substring misses any question that uses an acronym or a clinical
synonym. `app/onto/` lifts it into OWL/SKOS and closes that gap — measured, not claimed:

| Check | Result |
|---|---|
| OWL 2 RL closure | 230 asserted triples → **688** (**+468 derived**) |
| SHACL governance | asserted graph: **11 violations** → inferred graph: **conforms** |
| Synonym-aware linking vs substring | **6 of 7** realistic HCP questions recovered |

Two property chains do most of the work — declarative rules in a versioned `.ttl`,
not code:

```turtle
ins:madeBy       owl:propertyChainAxiom ( ins:madeBy ins:hasMember ) .
ins:hasDrugClass owl:propertyChainAxiom ( ins:hasDrugClass skos:broaderTransitive ) .
```

No source document says Orvenda is made by Norwick Pharma — only that the
alliance makes it. The reasoner derives the rest. Details, including the two defects
the layer found in its own data, in [`app/onto/README.md`](app/onto/README.md).

---

## Quickstart

```bash
pip install -r requirements.txt          # + Ollama with a chat model & nomic-embed-text
python -m app.rag.store                  # ingest corpus -> Qdrant
python demo_cases.py                     # 4 compliance demo cases
python -m app.graph.kg                   # build the knowledge graph
python -m app.graph.hybrid "What class is Orvenda and what is it indicated for?"
python -m app.obs.evaluate               # compliance eval harness (CI-style)
python -m app.obs.dashboard              # render the observability dashboard
python tests/test_core.py                # offline unit tests (what CI runs)
uvicorn app.api:app --port 8100          # versioned inference API

python app/onto/build.py                 # lift the KG into the OWL/SKOS ontology
python app/onto/reason.py                # OWL 2 RL closure + diff of what was derived
python app/onto/validate.py              # SHACL, asserted vs inferred
python app/onto/compare_linking.py       # substring vs ontology-aware entity linking
python tests/test_onto.py                # ontology tests (also in CI)
```

Fine-tuning (single 24 GB GPU): see [`finetune/`](finetune/) — dataset generator, native
Windows LoRA trainer, and the [A/B result](finetune/AB_RESULT.md).

---

## Repository layout

```
app/
  llm.py            local-first LLM client (Ollama), backend-agnostic + traced
  rag/              chunking, Qdrant vector store, dense pipeline
  graph/            knowledge graph + hybrid GraphRAG (vector + graph + rerank)
  onto/             OWL/SKOS ontology, OWL 2 RL reasoning, SHACL, SPARQL, linking
  obs/              trace store, metrics, compliance eval, HTML dashboard
  api.py            FastAPI versioned inference service
prompts/            versioned compliance system prompts
data/               simulated HCP knowledge base (public info)
finetune/           dataset + LoRA trainer (Win & unsloth) + A/B result
tests/              offline unit tests (CI)
docs/               architecture + showcase visuals
```

## Design principles

- **Local-first, frontier on-demand** — resolve locally when local capacity clears
  the task threshold; escalate on evidence of insufficiency, not reflex.
- **Backend-agnostic** — the same call path targets local Ollama or a frontier
  endpoint via env var.
- **Everything traced** — latency, tokens, retrieval hits and prompt version logged
  for every request; schema is Langfuse/Phoenix-exportable.

## Scope & honesty

This is a **reference implementation**, not a shipped product. The corpus is
simulated (public info), and the LoRA adapter is a **proof-of-pipeline** trained
on a small dataset — it demonstrates the effect, and hardens by extending the
dataset. The knowledge graph runs on networkx with a Neo4j-ready schema, and the
semantic layer runs in rdflib — neither has been exercised on a graph database.

**Everything in the corpus is fictional, and not affiliated with or endorsed by any
company.** Orvenda, Vestrila, Pulmyra, Aerivo and Bindavex are invented brands;
orvagliflozin, veligatran, selranib, calmatropium and veligumab are invented
substances — they follow real INN stem conventions (`-gliflozin`, `-gatran`,
`-nib`, `-tropium`, `-umab`) so the domain reads correctly, but no such products,
companies or trials exist. Every document under `data/` was written for this
repository and is marked *fictional*; none of it is, or derives from, any
company's internal, regulatory or promotional material. Any resemblance to a real
product is coincidental. **Nothing here is medical advice.**

## Stack

Python · Ollama (Qwen3.6, local 24 GB GPU) · Qdrant · networkx · FastAPI · transformers /
peft / trl (LoRA) · GitHub Actions

<div align="center"><sub>Built by <a href="https://github.com/msemino">@msemino</a> · Remote · UTC-3</sub></div>
