"""
Ontology-driven entity linking.

app/graph/hybrid.py links entities by asking whether the canonical label appears
verbatim in the question. That works for brand names and for nothing else: the
canonical labels are lifted from source documents and read like
"Chronic obstructive pulmonary disease (COPD)", while an HCP types "COPD".

This linker matches against skos:prefLabel *and* every skos:altLabel, then walks
the inferred graph to the products. Two rules keep it from over-firing:

  - word boundaries, always ("PE" must not match "prevention");
  - short all-caps acronyms (<= 4 chars) match case-sensitively, everything else
    case-insensitively. Otherwise "AF" fires on "affects" and "NP" on "input".

Every match reports which label matched, prefLabel or altLabel. That trace is
what makes a wrong retrieval debuggable instead of mysterious.
"""
from __future__ import annotations
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from rdflib import Graph, Namespace, RDF  # noqa: E402
from rdflib.namespace import SKOS  # noqa: E402
from app.onto.reason import closure  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
KG_TTL = os.path.join(_HERE, "kg.ttl")
INS = Namespace("https://insight-rag.local/onto#")

_g: Graph | None = None


def graph() -> Graph:
    """Inferred graph, built once per process."""
    global _g
    if _g is None:
        _g = closure(Graph().parse(KG_TTL, format="turtle"))
    return _g


def _pattern(text: str) -> re.Pattern:
    esc = re.escape(text)
    if len(text) <= 4 and text.isupper():
        return re.compile(rf"(?<![A-Za-z0-9]){esc}(?![A-Za-z0-9])")
    return re.compile(rf"(?<![A-Za-z0-9]){esc}(?![A-Za-z0-9])", re.I)


def link(question: str) -> list[dict]:
    """Entities mentioned in the question, longest match wins per URI."""
    g = graph()
    found: dict[str, dict] = {}
    for prop, kind in ((SKOS.prefLabel, "prefLabel"), (SKOS.altLabel, "altLabel")):
        for uri, _, lit in g.triples((None, prop, None)):
            text = str(lit)
            if not _pattern(text).search(question):
                continue
            prev = found.get(str(uri))
            if prev and len(prev["matched"]) >= len(text):
                continue
            found[str(uri)] = {
                "uri": uri,
                "label": str(g.value(uri, SKOS.prefLabel) or text),
                "matched": text,
                "via": kind,
                "type": _type_of(g, uri),
            }
    return sorted(found.values(), key=lambda e: -len(e["matched"]))


def _type_of(g: Graph, uri) -> str:
    for cls in (INS.Product, INS.Substance, INS.DrugClass, INS.Indication,
                INS.ReversalAgent, INS.Alliance, INS.LegalEntity):
        if (uri, RDF.type, cls) in g:
            return str(cls).split("#")[-1]
    return "Thing"


def _products_of(uri, kind: str) -> set[str]:
    """Products reachable from one entity, 1 hop on the inferred graph."""
    g = graph()
    if kind == "Product":
        return {str(g.value(uri, SKOS.prefLabel))}
    out = set()
    for inverse in (INS.substanceOf, INS.drugClassOf, INS.indicationOf,
                    INS.reverses, INS.manufactures):
        for prod in g.objects(uri, inverse):
            if (prod, RDF.type, INS.Product) in g:
                out.add(str(g.value(prod, SKOS.prefLabel)))
    return out


def products_for(entities: list[dict]) -> list[str]:
    """
    Products the question is about.

    Multiple linked entities are *constraints*, not alternatives: "what does
    Norwick offer for T2D" means the products that satisfy both, not the union
    of everything BI makes with everything treating T2D. Intersect, and fall back
    to the union only when the intersection is empty — an over-constrained
    question should still retrieve something rather than nothing.
    """
    sets = [s for s in (_products_of(e["uri"], e["type"]) for e in entities) if s]
    if not sets:
        return []
    narrowed = set.intersection(*sets)
    return sorted(narrowed or set.union(*sets))


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Which product can I use in COPD?"
    ents = link(q)
    print("Q:", q)
    for e in ents:
        print(f"  linked {e['label']!r} [{e['type']}] via {e['via']} {e['matched']!r}")
    print("  products:", ", ".join(products_for(ents)) or "(none)")
