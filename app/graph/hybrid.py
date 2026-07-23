"""
Hybrid GraphRAG retrieval = vector search + knowledge-graph expansion + rerank.

1. Vector search returns candidate chunks (dense retrieval).
2. Entity linking: match query terms to KG entities (product/generic/class/indication).
3. Graph expansion: pull the 1-hop neighbourhood of matched entities as structured
   facts (triples) — precise, non-hallucinated relations.
4. Rerank: boost vector chunks whose source document belongs to a matched product.
5. Compose context = structured facts + reranked passages, then answer.

The structured-fact block is what makes graph retrieval pay off: exact relations
(REVERSED_BY, INDICATED_FOR, HAS_CLASS) that dense retrieval alone can miss or dilute.
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.rag.store import search        # noqa: E402
from app.graph.kg import load           # noqa: E402
from app.llm import chat                 # noqa: E402
from app.obs.tracing import log_trace    # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROMPT_VERSION = "compliance_system_v1"

_REL_PHRASE = {
    "HAS_GENERIC": "has generic name",
    "HAS_CLASS": "is of drug class",
    "MADE_BY": "is manufactured by",
    "INDICATED_FOR": "is indicated for",
    "REVERSED_BY": "is reversed by",
}


def _link_entities(query: str, kg: dict) -> list[str]:
    ql = query.lower()
    hits = []
    for node in kg["nodes"]:
        name = node["id"]
        if len(name) >= 4 and name.lower() in ql:
            hits.append(name)
    return hits


def _graph_facts(entities: list[str], kg: dict) -> tuple[list[str], set[str]]:
    ents = set(entities)
    facts, products = [], set()
    for t in kg["triples"]:
        if t["s"] in ents or t["o"] in ents:
            facts.append(f"{t['s']} {_REL_PHRASE.get(t['rel'], t['rel'])} {t['o']}.")
            products.add(t["s"])
    # map matched products to their source docs for reranking
    src = {n["id"]: n.get("source") for n in kg["nodes"] if n.get("source")}
    prod_sources = {src[p] for p in products if p in src}
    return sorted(set(facts)), prod_sources


def _rerank(hits: list[dict], boost_sources: set[str]) -> list[dict]:
    for h in hits:
        h["rerank"] = round(h["score"] + (0.15 if h["source"] in boost_sources else 0.0), 3)
    return sorted(hits, key=lambda x: x["rerank"], reverse=True)


def _load_prompt() -> str:
    with open(os.path.join(_ROOT, "prompts", f"{PROMPT_VERSION}.md"), encoding="utf-8") as f:
        return f.read()


def answer(question: str, k: int = 4) -> dict:
    kg = load()
    entities = _link_entities(question, kg)
    facts, boost = _graph_facts(entities, kg)
    hits = _rerank(search(question, k=k), boost)

    facts_block = "STRUCTURED FACTS (from knowledge graph):\n" + \
                  ("\n".join(f"- {f}" for f in facts) if facts else "- (none matched)")
    passages = "\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)
    context = f"{facts_block}\n\nPASSAGES:\n{passages}"

    system = _load_prompt().replace("{context}", context)
    result = chat(system=system, user=question)
    trace = {
        "prompt_version": PROMPT_VERSION,
        "mode": "graphrag",
        "linked_entities": entities,
        "graph_facts": len(facts),
        "retrieval": [{"source": h["source"], "score": h["score"], "rerank": h["rerank"]} for h in hits],
        "top_score": hits[0]["rerank"] if hits else None,
        "model": result["model"],
        "latency_ms": result["latency_ms"],
        "prompt_tokens": result["prompt_tokens"],
        "completion_tokens": result["completion_tokens"],
    }
    log_trace(question, result["text"], trace)
    return {"question": question, "answer": result["text"],
            "sources": [h["source"] for h in hits],
            "entities": entities, "facts": facts, "trace": trace}


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What class is Orvenda and what is it indicated for?"
    r = answer(q)
    print("Q:", r["question"])
    print("ENTITIES:", r["entities"])
    print("GRAPH FACTS:")
    for f in r["facts"]:
        print("  -", f)
    print("\nA:", r["answer"])
    print("\nTRACE:", {k: r["trace"][k] for k in ("mode", "linked_entities", "graph_facts", "latency_ms")})
