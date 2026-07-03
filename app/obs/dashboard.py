"""Render a static HTML observability dashboard from the trace log + metrics."""
from __future__ import annotations
import os
import html
from app.obs.tracing import read_traces
from app.obs.metrics import compute

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "app", "obs", "dashboard.html")


def _card(label, value):
    return (f'<div class="card"><div class="v">{html.escape(str(value))}</div>'
            f'<div class="l">{html.escape(label)}</div></div>')


def render() -> str:
    m = compute()
    tr = read_traces()[-25:][::-1]
    cards = "".join([
        _card("requests", m["requests"]),
        _card("error rate", m["error_rate"]),
        _card("latency p50 (ms)", m["latency_ms"]["p50"]),
        _card("latency p95 (ms)", m["latency_ms"]["p95"]),
        _card("avg prompt tok", m["tokens"]["avg_prompt"]),
        _card("avg out tok", m["tokens"]["avg_completion"]),
        _card("avg top score", m["retrieval"]["avg_top_score"]),
    ])
    rows = ""
    for t in tr:
        srcs = ", ".join(r["source"] for r in t.get("retrieval", []))
        rows += (
            f"<tr><td>{html.escape(t.get('iso',''))}</td>"
            f"<td>{html.escape(t.get('question','')[:70])}</td>"
            f"<td>{t.get('latency_ms','')}</td>"
            f"<td>{t.get('prompt_tokens','')}&rarr;{t.get('completion_tokens','')}</td>"
            f"<td>{t.get('top_score','')}</td>"
            f"<td>{html.escape(t.get('prompt_version',''))}</td>"
            f"<td>{html.escape(srcs)}</td></tr>"
        )
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>InsightRAG — observability</title><style>
body{{font-family:Segoe UI,Arial,sans-serif;margin:24px;background:#0f1720;color:#e6edf3}}
h1{{font-size:20px}} .grid{{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0}}
.card{{background:#18212b;border:1px solid #2a3a47;border-radius:10px;padding:14px 18px;min-width:120px}}
.card .v{{font-size:22px;font-weight:700;color:#4aa3df}} .card .l{{font-size:11px;color:#8b98a5;text-transform:uppercase}}
table{{border-collapse:collapse;width:100%;font-size:12px}}
th,td{{border-bottom:1px solid #23303c;padding:6px 8px;text-align:left}}
th{{color:#8b98a5;text-transform:uppercase;font-size:10px}}
</style></head><body>
<h1>InsightRAG &mdash; observability dashboard</h1>
<div class="grid">{cards}</div>
<h3>Recent requests (traced)</h3>
<table><tr><th>time</th><th>question</th><th>ms</th><th>tokens</th><th>top score</th><th>prompt ver</th><th>sources</th></tr>
{rows}</table>
<p style="color:#8b98a5;font-size:11px">Local-first trace store &middot; schema is Langfuse/Phoenix-exportable.</p>
</body></html>"""


if __name__ == "__main__":
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render())
    print("wrote", OUT)
