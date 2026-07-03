"""
Build a domain instruction dataset for LoRA fine-tuning, derived from the corpus
and the knowledge graph. Output: finetune/dataset.jsonl (chat format).

The goal of the adapter is not new knowledge (RAG supplies that) but *behavior*:
consistent compliance style — fair balance, scoped off-label refusals, source
citation — so the base model needs fewer prompt tokens to stay in policy.
"""
from __future__ import annotations
import os
import re
import glob
import json

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(_ROOT, "finetune", "dataset.jsonl")

SYS = ("You are OneInsight, a compliant HCP customer-insight assistant. Answer "
       "on-label only, pair efficacy with safety, cite sources, and refuse "
       "off-label use with a scoped refusal plus on-label facts.")


def _section_prose(text: str, header: str) -> str:
    m = re.search(rf"##\s*{re.escape(header)}.*?\n(.*?)(?:\n##|\Z)", text, re.S | re.I)
    return m.group(1).strip() if m else ""


def _bullets(text: str, header: str) -> list[str]:
    body = _section_prose(text, header)
    return [ln[2:].strip() for ln in body.splitlines() if ln.strip().startswith("- ")]


def build() -> list[dict]:
    rows = []
    for path in sorted(glob.glob(os.path.join(_ROOT, "data", "*.md"))):
        text = open(path, encoding="utf-8").read()
        src = os.path.basename(path)
        title = re.search(r"#\s*(.+)", text).group(1)
        mp = re.match(r"([A-Za-z][\w\-]*)\s*\(([^)]+)\)", title)
        if not mp:
            continue
        prod = mp.group(1)

        moa = _section_prose(text, "Mechanism of action")
        inds = _bullets(text, "Approved indications")
        risks = _bullets(text, "Key safety notes for HCPs")

        if moa:
            rows.append(_pair(
                f"What is the mechanism of action of {prod}?",
                f"{moa}\n\n[{src}]"))
        if inds and risks:
            a = ("Approved indications:\n- " + "\n- ".join(inds) +
                 "\n\nKey safety information:\n- " + "\n- ".join(risks[:4]) +
                 f"\n\n[{src}]")
            rows.append(_pair(
                f"What is {prod} indicated for, and what should I keep in mind on safety?", a))
        # compliance behavior: off-label scoped refusal
        rows.append(_pair(
            f"Can I prescribe {prod} for an indication that is not on its label?",
            (f"That use is not part of the approved label for {prod}, so I can't "
             f"advise on it. On-label, {prod} is indicated for: "
             + "; ".join(i.split(':')[0] for i in inds) + f". [{src}]")))
    return rows


def _pair(q: str, a: str) -> dict:
    return {"messages": [
        {"role": "system", "content": SYS},
        {"role": "user", "content": q},
        {"role": "assistant", "content": a},
    ]}


if __name__ == "__main__":
    rows = build()
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(rows)} training examples to {OUT}")
