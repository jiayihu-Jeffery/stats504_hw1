"""Render report/report.md to a single self-contained HTML file (figures embedded)."""
import base64, re, sys
from pathlib import Path
from markdown_it import MarkdownIt
R = Path(__file__).resolve().parents[1]
md = (R / "report.md").read_text()
def embed(m):
    alt, src = m.group(1), m.group(2)
    data = base64.b64encode((R / src).resolve().read_bytes()).decode()
    return f"![{alt}](data:image/png;base64,{data})"
md = re.sub(r"!\[([^\]]*)\]\(([^)]+\.png)\)", embed, md)
body = MarkdownIt("commonmark").enable("table").render(md)
css = """body{font-family:Georgia,'Times New Roman',serif;max-width:900px;margin:40px auto;padding:0 16px;line-height:1.5;color:#222;background:#fff}
h1{font-size:1.8em;border-bottom:2px solid #333}h2{margin-top:1.8em;border-bottom:1px solid #ccc}h3{margin-top:1.4em}
table{border-collapse:collapse;margin:1em 0;font-size:.86em;width:100%}th,td{border:1px solid #bbb;padding:4px 6px;vertical-align:top}
th{background:#eef2f6}img{max-width:100%;display:block;margin:1em auto 0}em{color:#444}code{font-size:.9em}
@media print{body{margin:0;max-width:none}h2{page-break-before:auto}img,table{page-break-inside:avoid}}"""
html = f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Customer Personality Analysis</title><style>{css}</style></head><body>{body}</body></html>"
(R / "report.html").write_text(html); print("wrote", R / "report.html", f"{len(html)/1e6:.1f} MB")
