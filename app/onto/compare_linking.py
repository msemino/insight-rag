"""
A/B: substring entity linking (current pipeline) vs ontology linking.

Both linkers get the same questions. The questions are phrased the way an HCP
actually phrases them — acronyms, generic names, class-level asks — not the way
the source documents are titled.

Run:  python app/onto/compare_linking.py
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.graph.kg import load as load_flat        # noqa: E402
from app.graph.hybrid import _link_entities       # noqa: E402  (the incumbent)
from app.onto.link import link, products_for      # noqa: E402

QUESTIONS = [
    "Which of your products can I use in COPD?",
    "Do you market any anticoagulant?",
    "Is there an antidote for veligatran?",
    "What does Norwick offer for T2D?",
    "Which drug is indicated for IPF?",
    "Any option for a patient with NVAF?",
    "What is Orvenda indicated for?",           # control: substring already works
]


def main() -> int:
    flat = load_flat()
    wins = 0
    for q in QUESTIONS:
        naive = _link_entities(q, flat)
        onto = link(q)
        prods = products_for(onto)
        print(f"\nQ: {q}")
        print(f"  substring : {naive or '(nothing linked)'}")
        print(f"  ontology  : " + (", ".join(
            f"{e['label']} [{e['type']}] via {e['via']}:{e['matched']!r}" for e in onto)
            or "(nothing linked)"))
        print(f"  -> products: {', '.join(prods) or '(none)'}")
        if not naive and prods:
            wins += 1
            print("  ** recovered: substring linked nothing, ontology reached a product")
    print(f"\n{wins}/{len(QUESTIONS)} questions recovered by the ontology layer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
