"""
SHACL validation, run twice: on the asserted graph and on the inferred one.

The contrast is the point. Same shapes, same data — the only difference is
whether the reasoner ran. What fails before and passes after is exactly the
value the ontology adds over the flat KG.

Run:  python app/onto/validate.py        (exit code 1 if the inferred graph fails)
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from rdflib import Graph  # noqa: E402
from pyshacl import validate as shacl_validate  # noqa: E402
from app.onto.reason import closure  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
KG_TTL = os.path.join(_HERE, "kg.ttl")
SHAPES_TTL = os.path.join(_HERE, "shapes.ttl")


def run(graph: Graph, shapes: Graph) -> tuple[bool, list[str]]:
    conforms, _, text = shacl_validate(graph, shacl_graph=shapes, advanced=True)
    msgs = [ln.strip()[len("Message:"):].strip()
            for ln in text.splitlines() if ln.strip().startswith("Message:")]
    focus = [ln.strip().split("#")[-1]
             for ln in text.splitlines() if ln.strip().startswith("Focus Node:")]
    return conforms, [f"{f}: {m}" for f, m in zip(focus, msgs)] or msgs


if __name__ == "__main__":
    shapes = Graph().parse(SHAPES_TTL, format="turtle")

    asserted = Graph().parse(KG_TTL, format="turtle")
    ok_a, msgs_a = run(asserted, shapes)
    print(f"ASSERTED graph  : {'conforms' if ok_a else f'{len(msgs_a)} violation(s)'}")
    for m in msgs_a:
        print(f"   x {m}")

    inferred = closure(Graph().parse(KG_TTL, format="turtle"))
    ok_i, msgs_i = run(inferred, shapes)
    print(f"\nINFERRED graph  : {'conforms' if ok_i else f'{len(msgs_i)} violation(s)'}")
    for m in msgs_i:
        print(f"   x {m}")

    if ok_i and not ok_a:
        print("\n-> the reasoner is what closes the gap: identity resolved by "
              "propertyChainAxiom(madeBy, hasMember).")
    sys.exit(0 if ok_i else 1)
