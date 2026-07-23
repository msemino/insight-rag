"""
Offline tests for the ontology layer — no LLM / GPU, so they run in CI.

These are the guardrails on the semantic layer itself: if a rule stops firing or
the graph stops conforming, CI fails instead of the RAG quietly getting worse.
The label-duplication test exists because that defect actually shipped and was
only noticed as duplicated SPARQL rows.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _inferred():
    from rdflib import Graph
    from app.onto.build import build, KG_TTL
    from app.onto.reason import closure
    build().serialize(destination=KG_TTL, format="turtle")
    return closure(Graph().parse(KG_TTL, format="turtle"))


def test_abox_lifts_every_kg_node():
    from rdflib.namespace import SKOS
    from app.graph.kg import load
    from app.onto.build import build
    g = build()
    labelled = {str(o) for o in g.objects(None, SKOS.prefLabel)}
    for node in load()["nodes"]:
        assert node["id"] in labelled, f"{node['id']} lost in the lift"


def test_alliance_chain_resolves_authorisation_holder():
    """Orvenda's document names only the alliance; the chain must reach BI."""
    from rdflib import Namespace
    from rdflib.namespace import SKOS
    INS = Namespace("https://insight-rag.local/onto#")
    g = _inferred()
    holders = {str(g.value(o, SKOS.prefLabel)) for o in g.objects(INS["orvenda"], INS.madeBy)}
    assert "Norwick Pharma" in holders
    assert "Halvern Biosciences and Company" in holders


def test_class_taxonomy_is_transitive():
    """Vestrila is only typed as a DOAC; it must reach Antithrombotic agent, two hops up."""
    from rdflib import Namespace
    from rdflib.namespace import SKOS
    INS = Namespace("https://insight-rag.local/onto#")
    g = _inferred()
    classes = {str(g.value(o, SKOS.prefLabel)) for o in g.objects(INS["vestrila"], INS.hasDrugClass)}
    assert {"Anticoagulant", "Antithrombotic agent"} <= classes


def test_inferred_graph_conforms_to_shacl():
    from rdflib import Graph
    from app.onto.validate import run, SHAPES_TTL
    conforms, msgs = run(_inferred(), Graph().parse(SHAPES_TTL, format="turtle"))
    assert conforms, "SHACL violations on the inferred graph:\n" + "\n".join(msgs)


def test_no_duplicate_or_untagged_preferred_labels():
    """The defect that shipped: TBox wrote plain literals, ABox wrote @en ones."""
    from collections import Counter
    from rdflib.namespace import SKOS
    from app.onto.build import build
    g = build()
    counts = Counter(s for s, _, _ in g.triples((None, SKOS.prefLabel, None)))
    dupes = [str(s) for s, n in counts.items() if n > 1]
    assert not dupes, f"entities with more than one prefLabel: {dupes}"
    untagged = [str(o) for o in g.objects(None, SKOS.prefLabel) if not o.language]
    assert not untagged, f"untagged prefLabels: {untagged}"


def test_ontology_linking_beats_substring_on_acronyms():
    from app.graph.kg import build as build_flat, save, load
    from app.graph.hybrid import _link_entities
    from app.onto.link import link, products_for
    save(build_flat())
    flat = load()
    for question, expected in [("Which product can I use in COPD?", "Aerivo"),
                               ("Which drug is indicated for IPF?", "Pulmyra"),
                               ("Do you market any anticoagulant?", "Vestrila")]:
        assert not _link_entities(question, flat), "substring baseline unexpectedly linked"
        assert products_for(link(question)) == [expected]


def test_multiple_entities_intersect_not_union():
    """'What does Norwick offer for T2D' is one product, not the whole catalogue."""
    from app.onto.link import link, products_for
    assert products_for(link("What does Norwick offer for T2D?")) == ["Orvenda"]


def test_short_acronyms_do_not_fire_inside_words():
    """'PE' must not match 'prevention'; 'AF' must not match 'affects'."""
    from app.onto.link import link
    matched = {e["matched"] for e in link("This prevention program affects combined outcomes.")}
    assert not {"PE", "AF", "NP", "HF"} & matched, f"false positives: {matched}"


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
