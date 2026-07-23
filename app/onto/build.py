"""
ABox builder: lifts the flat networkx KG into RDF conforming to ontology.ttl.

The existing graph (app/graph/kg.json) stores entities as bare strings. Here each
one becomes a URI with a deterministic slug, a typed class, a skos:prefLabel and
— for products — the source document it came from, so citations survive the lift.

Run:  python app/onto/build.py      ->  app/onto/kg.ttl   (TBox + ABox, asserted only)
"""
from __future__ import annotations
import os
import re
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from rdflib import Graph, Literal, Namespace, RDF, URIRef  # noqa: E402
from rdflib.namespace import SKOS  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
ONTOLOGY_TTL = os.path.join(_HERE, "ontology.ttl")
KG_TTL = os.path.join(_HERE, "kg.ttl")
KG_JSON = os.path.join(_ROOT, "app", "graph", "kg.json")

INS = Namespace("https://insight-rag.local/onto#")

# kg.json node type -> ontology class
_CLASS = {
    "Product": INS.Product,
    "Generic": INS.Substance,
    "DrugClass": INS.DrugClass,
    "Indication": INS.Indication,
    "Manufacturer": INS.Organization,
    "ReversalAgent": INS.ReversalAgent,
}

# kg.json relation -> ontology object property
_PROP = {
    "HAS_GENERIC": INS.hasSubstance,
    "HAS_CLASS": INS.hasDrugClass,
    "MADE_BY": INS.madeBy,
    "INDICATED_FOR": INS.indicatedFor,
    "REVERSED_BY": INS.reversedBy,
}


def slug(label: str) -> str:
    """Deterministic URI fragment. Must stay in sync with the slugs in ontology.ttl."""
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", label.lower())).strip("-")


def uri(label: str) -> URIRef:
    return INS[slug(label)]


def build() -> Graph:
    kg = json.load(open(KG_JSON, encoding="utf-8"))
    g = Graph()
    g.parse(ONTOLOGY_TTL, format="turtle")   # TBox first: schema + synonyms + taxonomy
    g.bind("ins", INS)
    g.bind("skos", SKOS)

    for node in kg["nodes"]:
        u = uri(node["id"])
        g.add((u, RDF.type, _CLASS[node["type"]]))
        g.add((u, SKOS.prefLabel, Literal(node["id"], lang="en")))
        if node.get("source"):
            g.add((u, INS.sourceDocument, Literal(node["source"])))

    for t in kg["triples"]:
        g.add((uri(t["s"]), _PROP[t["rel"]], uri(t["o"])))

    return g


if __name__ == "__main__":
    g = build()
    g.serialize(destination=KG_TTL, format="turtle")
    n_ind = len(set(g.subjects(SKOS.prefLabel, None)))
    n_alt = len(list(g.triples((None, SKOS.altLabel, None))))
    print(f"wrote {KG_TTL}")
    print(f"  {len(g)} asserted triples · {n_ind} labelled individuals · {n_alt} synonyms")
