"""Render report/two_page_summary.md to print-ready HTML (US Letter, two pages)."""
from pathlib import Path
from markdown_it import MarkdownIt
R = Path(__file__).resolve().parents[1]
import base64, re
md = (R / "two_page_summary.md").read_text()
md = re.sub(r"!\[([^\]]*)\]\(([^)]+\.png)\)",
            lambda m: f"![{m.group(1)}](data:image/png;base64,{base64.b64encode((R / m.group(2)).resolve().read_bytes()).decode()})", md)
body = MarkdownIt("commonmark").enable("table").render(md)
css = """@page{size:Letter;margin:0.5in 0.65in}
:root{--ink:#1a1a1a;--muted:#555;--rule:#c9c9c9;--head:#eef2f6}
body{font-family:'Times New Roman',Georgia,serif;font-size:10pt;line-height:1.26;color:var(--ink);background:#fff;max-width:7.2in;margin:0 auto;padding:0 16px}
h1{font-size:15pt;margin:0 0 2pt}h2{font-size:11.5pt;margin:8pt 0 2pt;border-bottom:1px solid var(--rule)}
p{margin:2pt 0 4pt;text-align:justify}ol,ul{margin:1pt 0 3pt 0;padding-left:16pt}li{margin:0 0 1pt}em{color:inherit}
h1+p em{color:var(--muted)}
table{border-collapse:collapse;width:100%;font-size:8.4pt;margin:3pt 0}th,td{border:1px solid var(--rule);padding:2pt 4pt;vertical-align:top}th{background:var(--head)}
img{width:100%;display:block;margin:3pt 0 0}
p:has(> img)+p{font-size:8.6pt;color:var(--muted);margin:0 0 4pt;text-align:left}
@media print{body{padding:0;max-width:none}img{break-inside:avoid}}"""
html = f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Project Summary</title><style>{css}</style></head><body>{body}</body></html>"
(R / "two_page_summary.html").write_text(html); print("wrote", R / "two_page_summary.html")
