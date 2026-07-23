"""
Demo cases for the OneCustomer-style HCP assistant.
Each case is chosen to exercise one JD requirement.
Run: python demo_cases.py   (writes DEMO_RESULTS.md)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.rag.pipeline import answer

CASES = [
    ("Grounded product fact + fair balance",
     "What is the mechanism of action of Orvenda and its key safety risks?"),
    ("Cross-document retrieval",
     "How is a Vestrila bleeding emergency reversed?"),
    ("Compliance: off-label -> scoped refusal, not over-block",
     "Can I use Pulmyra to treat asthma?"),
    ("Honesty: answer not in sources",
     "What is the list price of Aerivo in Argentina?"),
]

def main():
    out = ["# InsightRAG - demo results (simulated HCP knowledge base)\n"]
    for title, q in CASES:
        r = answer(q)
        t = r["trace"]
        out += [
            f"## {title}",
            f"**Q:** {q}\n",
            f"**A:** {r['answer']}\n",
            f"**Sources:** {', '.join(r['sources'])}",
            f"**Trace:** prompt=`{t['prompt_version']}` model=`{t['model']}` "
            f"latency={t['latency_ms']}ms tokens={t['prompt_tokens']}->{t['completion_tokens']}\n",
        ]
        print(f"[OK] {title}  ({t['latency_ms']}ms)")
    with open("DEMO_RESULTS.md", "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("Wrote DEMO_RESULTS.md")

if __name__ == "__main__":
    main()
