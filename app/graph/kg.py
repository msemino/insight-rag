"""
Knowledge graph builder.

Extracts a typed entity/relation graph from the structured HCP documents.
Node types : Product, Generic, DrugClass, Indication, Manufacturer, ReversalAgent
Edge types : HAS_GENERIC, HAS_CLASS, MADE_BY, INDICATED_FOR, REVERSED_BY

Stored with networkx (in-process, no server). The schema maps 1:1 to a Neo4j
labelled-property graph — the production target — so the same triples can be
loaded there with CREATE (:Product)-[:INDICATED_FOR]->(:Indication) statements.
"""
from __future__ import annotations
import os
import re
import glob
import json
import networkx as nx

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GRAPH_JSON = os.path.join(_ROOT, "app", "graph", "kg.json")


def _section(text: str, header: str) -> list[str]:
    """Return bullet lines under a '## header' section."""
    m = re.search(rf"##\s*{re.escape(header)}.*?\n(.*?)(?:\n##|\Z)", text, re.S | re.I)
    if not m:
        return []
    return [ln[2:].strip() for ln in m.group(1).splitlines() if ln.strip().startswith("- ")]


def build() -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    for path in sorted(glob.glob(os.path.join(_ROOT, "data", "*.md"))):
        text = open(path, encoding="utf-8").read()
        source = os.path.basename(path)
        title = re.search(r"#\s*(.+)", text).group(1)
        mprod = re.match(r"([A-Za-z][\w\-]*)\s*\(([^)]+)\)", title)
        if not mprod:
            continue  # policy docs etc. have no product entity
        product, generic = mprod.group(1), mprod.group(2).strip()
        g.add_node(product, type="Product", source=source)
        g.add_node(generic, type="Generic")
        g.add_edge(product, generic, key="HAS_GENERIC", rel="HAS_GENERIC")

        cls = re.search(r"Class:\s*(.+)", text)
        if cls:
            c = cls.group(1).split("(")[0].strip().rstrip(".")
            g.add_node(c, type="DrugClass")
            g.add_edge(product, c, key="HAS_CLASS", rel="HAS_CLASS")

        man = re.search(r"Manufacturer:\s*(.+)", text)
        if man:
            m0 = man.group(1).strip().rstrip(".")
            g.add_node(m0, type="Manufacturer")
            g.add_edge(product, m0, key="MADE_BY", rel="MADE_BY")

        for b in _section(text, "Approved indications"):
            ind = b.split(":")[0].strip().rstrip(".")
            if ind:
                g.add_node(ind, type="Indication")
                g.add_edge(product, ind, key=f"IND::{ind}", rel="INDICATED_FOR")

        rev = re.search(r"##\s*Reversal agent.*?\n\s*([A-Z][\w]+)", text, re.S | re.I)
        if rev:
            g.add_node(rev.group(1), type="ReversalAgent")
            g.add_edge(product, rev.group(1), key="REVERSED_BY", rel="REVERSED_BY")
    return g


def save(g: nx.MultiDiGraph) -> None:
    triples = [{"s": u, "rel": d["rel"], "o": v} for u, v, d in g.edges(data=True)]
    nodes = [{"id": n, **a} for n, a in g.nodes(data=True)]
    with open(GRAPH_JSON, "w", encoding="utf-8") as f:
        json.dump({"nodes": nodes, "triples": triples}, f, indent=2, ensure_ascii=False)


def load() -> dict:
    return json.load(open(GRAPH_JSON, encoding="utf-8"))


if __name__ == "__main__":
    g = build()
    save(g)
    print(f"KG: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")
    from collections import Counter
    print("node types:", dict(Counter(a["type"] for _, a in g.nodes(data=True))))
    print("relations :", dict(Counter(d["rel"] for *_, d in g.edges(data=True))))
