"""
Fast, offline unit tests — no LLM / GPU required, so they run in CI.
Cover the deterministic parts: chunking, KG extraction, metrics math.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_chunker_splits_and_overlaps():
    from app.rag.store import _chunk
    text = ("A" * 400 + "\n\n" + "B" * 400 + "\n\n" + "C" * 400)
    chunks = _chunk(text, size=500, overlap=100)
    assert len(chunks) >= 2
    assert all(c.strip() for c in chunks)


def test_kg_builds_expected_types():
    from app.graph.kg import build
    g = build()
    types = {a["type"] for _, a in g.nodes(data=True)}
    assert {"Product", "DrugClass", "Indication"} <= types
    rels = {d["rel"] for *_, d in g.edges(data=True)}
    assert "INDICATED_FOR" in rels and "REVERSED_BY" in rels


def test_kg_links_vestrila_to_reversal_agent():
    from app.graph.kg import build
    g = build()
    revs = [(u, v) for u, v, d in g.edges(data=True) if d["rel"] == "REVERSED_BY"]
    assert any(u == "Vestrila" for u, _ in revs)


def test_metrics_percentile_math():
    from app.obs.metrics import _pct
    vals = [10, 20, 30, 40, 50]
    assert _pct(vals, 50) == 30
    assert _pct(vals, 95) == 50
    assert _pct([], 50) is None


def test_entity_linking_matches_query():
    from app.graph.kg import build, save
    from app.graph.hybrid import _link_entities, _graph_facts
    save(build())
    from app.graph.kg import load
    kg = load()
    ents = _link_entities("what is the class of orvenda?", kg)
    assert "Orvenda" in ents
    facts, boost = _graph_facts(ents, kg)
    assert any("SGLT2" in f for f in facts)
    assert "orvenda.md" in boost


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"[PASS] {fn.__name__}")
        except Exception:
            failed += 1
            print(f"[FAIL] {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
