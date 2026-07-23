"""
SPARQL over the inferred graph — the class of question dense retrieval answers badly.

Vector search is good at "what does the label say about X". It is unreliable at
negation ("which products have NO reversal agent"), at aggregation ("how many
indications each"), and at multi-hop joins that no single passage states. Those
are set operations, and a set operation over an index of nearest neighbours is a
guess. Here they are exact, and the answer is derivable rather than generated.

Run:  python app/onto/sparql.py            (all named queries)
      python app/onto/sparql.py negation   (one)
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.onto.link import graph  # noqa: E402

PREFIX = """
PREFIX ins:  <https://insight-rag.local/onto#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
"""

QUERIES: dict[str, tuple[str, str]] = {
    "identity": (
        "Products by marketing-authorisation holder (needs the alliance chain)",
        """
        SELECT ?company ?product WHERE {
          ?org a ins:LegalEntity ; skos:prefLabel ?company .
          ?org ins:manufactures ?p .
          ?p skos:prefLabel ?product .
        } ORDER BY ?company ?product
        """),

    "taxonomy": (
        "Every product in the anticoagulant class, however narrowly it is typed",
        """
        SELECT ?product ?class WHERE {
          ?p ins:hasDrugClass ins:anticoagulant ; skos:prefLabel ?product .
          ?p ins:hasDrugClass ?c . ?c skos:prefLabel ?class .
        } ORDER BY ?product ?class
        """),

    "negation": (
        "Products with NO reversal agent (a question dense retrieval cannot answer)",
        """
        SELECT ?product WHERE {
          ?p a ins:Product ; skos:prefLabel ?product .
          FILTER NOT EXISTS { ?p ins:reversedBy ?any }
        } ORDER BY ?product
        """),

    "aggregate": (
        "Approved indications per product",
        """
        SELECT ?product (COUNT(?i) AS ?indications) WHERE {
          ?p a ins:Product ; skos:prefLabel ?product ; ins:indicatedFor ?i .
        } GROUP BY ?product ORDER BY DESC(?indications)
        """),

    "profile": (
        "Full multi-hop profile of one product, with its source document",
        """
        SELECT ?product ?substance ?class ?indication ?source WHERE {
          ?p skos:prefLabel "Pradaxa"@en ; skos:prefLabel ?product ;
             ins:sourceDocument ?source ;
             ins:hasSubstance/skos:prefLabel ?substance ;
             ins:indicatedFor/skos:prefLabel ?indication ;
             ins:hasDrugClass/skos:prefLabel ?class .
        } ORDER BY ?indication ?class
        """),
}


def run(name: str) -> None:
    title, q = QUERIES[name]
    print(f"\n=== {name} — {title}")
    rows = list(graph().query(PREFIX + q))
    if not rows:
        print("   (no rows)")
        return
    for row in rows:
        print("   " + " | ".join(str(v) for v in row))
    print(f"   ({len(rows)} rows)")


if __name__ == "__main__":
    names = sys.argv[1:] or list(QUERIES)
    for n in names:
        run(n)
