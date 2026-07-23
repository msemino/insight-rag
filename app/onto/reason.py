"""
OWL 2 RL reasoning over the lifted graph.

This is the step a property graph cannot do for you: the closure *derives* facts
nobody wrote down. Two chains matter here (declared in ontology.ttl):

  madeBy o hasMember          -> Orvenda is madeBy Norwick Pharma, even
                                 though the document only names the BI/Halvern alliance.
  hasDrugClass o broaderTrans -> Vestrila hasDrugClass Anticoagulant, even though
                                 the document only says "Direct oral anticoagulant".

Plus every owl:inverseOf, so the graph is traversable in both directions.

Run:  python app/onto/reason.py   ->  app/onto/kg-inferred.ttl  +  a diff report
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from rdflib import Graph, Namespace  # noqa: E402
from rdflib.namespace import SKOS  # noqa: E402
from owlrl import DeductiveClosure, OWLRL_Semantics  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
KG_TTL = os.path.join(_HERE, "kg.ttl")
INFERRED_TTL = os.path.join(_HERE, "kg-inferred.ttl")

INS = Namespace("https://insight-rag.local/onto#")

# Object properties whose new triples we report (the closure also derives a lot of
# schema housekeeping — rdf:type owl:Thing and friends — which is noise here).
_REPORTED = ["madeBy", "manufactures", "hasDrugClass", "drugClassOf",
             "indicatedFor", "indicationOf", "hasSubstance", "substanceOf",
             "reversedBy", "reverses"]


def closure(g: Graph) -> Graph:
    DeductiveClosure(OWLRL_Semantics, axiomatic_triples=False,
                     datatype_axioms=False).expand(g)
    return g


def label(g: Graph, node) -> str:
    lab = g.value(node, SKOS.prefLabel)
    return str(lab) if lab else str(node).split("#")[-1]


if __name__ == "__main__":
    asserted = Graph()
    asserted.parse(KG_TTL, format="turtle")
    before = set(asserted)

    inferred = Graph()
    inferred.parse(KG_TTL, format="turtle")
    closure(inferred)
    inferred.bind("ins", INS)
    inferred.serialize(destination=INFERRED_TTL, format="turtle")

    new = set(inferred) - before
    print(f"asserted: {len(before)} triples  ->  after closure: {len(inferred)} "
          f"(+{len(new)} derived)")
    print(f"wrote {INFERRED_TTL}\n")

    for prop in _REPORTED:
        rows = sorted((label(inferred, s), label(inferred, o))
                      for s, p, o in new if p == INS[prop])
        if rows:
            print(f"  derived {prop} ({len(rows)}):")
            for s, o in rows:
                print(f"    {s}  ->  {o}")
