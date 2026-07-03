"""Screenshot the observability dashboard to docs/dashboard.png (repo showcase)."""
import os
from playwright.sync_api import sync_playwright

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(_ROOT, "app", "obs", "dashboard.html")
OUT = os.path.join(_ROOT, "docs", "dashboard.png")

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1100, "height": 720}, device_scale_factor=2)
    pg.goto("file:///" + HTML.replace("\\", "/"))
    pg.wait_for_timeout(400)
    pg.screenshot(path=OUT, full_page=True)
    b.close()
print("wrote", OUT)
