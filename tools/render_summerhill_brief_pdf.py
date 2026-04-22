#!/usr/bin/env python3
"""Render the Summerhill creative brief as a branded PDF via Chrome headless."""

import subprocess
import tempfile
from pathlib import Path
import markdown

ROOT = Path("/Users/matthewfernandes/Documents/Claude")
SRC = ROOT / "business/sales/summerhill-creative-brief-may2026.md"
OUT = ROOT / "business/sales/summerhill-creative-brief-may2026.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

md_text = SRC.read_text()
html_body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "toc", "attr_list", "smarty"],
)

CSS_STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Josefin+Sans:wght@300;400;600&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,400;1,500&family=DM+Sans:wght@300;400;500&display=swap');

@page {
  size: Letter;
  margin: 22mm 22mm 25mm 22mm;
  @bottom-left {
    content: "Summerhill Fine Homes  \\2014  Creative brief  \\2014  May 2026";
    font-family: 'Josefin Sans', sans-serif;
    font-size: 8pt;
    font-weight: 300;
    letter-spacing: 0.25em;
    color: #8A8579;
    text-transform: uppercase;
  }
  @bottom-right {
    content: counter(page) " / " counter(pages);
    font-family: 'Josefin Sans', sans-serif;
    font-size: 8pt;
    font-weight: 300;
    letter-spacing: 0.2em;
    color: #8A8579;
  }
}

@page :first {
  margin: 0;
  @bottom-left { content: none; }
  @bottom-right { content: none; }
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  padding: 0;
  font-family: 'DM Sans', sans-serif;
  font-size: 10.5pt;
  line-height: 1.65;
  color: #1A1A18;
  background: #FAFAF8;
  font-weight: 300;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

.cover {
  page-break-after: always;
  width: 215.9mm;
  height: 279.4mm;
  background: #1A1A18;
  color: #F6F4F0;
  position: relative;
  padding: 38mm 28mm 28mm 28mm;
  overflow: hidden;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.cover::before {
  content: '';
  position: absolute;
  top: 30mm;
  right: 28mm;
  width: 30mm;
  height: 1px;
  background: #C9A96E;
  opacity: 0.6;
}

.cover .doc-id {
  font-family: 'Josefin Sans', sans-serif;
  font-size: 8.5pt;
  font-weight: 600;
  letter-spacing: 0.4em;
  color: #C9A96E;
  text-transform: uppercase;
  margin: 0 0 22mm 0;
}

.cover .pretitle {
  font-family: 'Josefin Sans', sans-serif;
  font-size: 10pt;
  font-weight: 600;
  letter-spacing: 0.45em;
  color: #C9A96E;
  text-transform: uppercase;
  margin-bottom: 12mm;
}

.cover .title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 64pt;
  font-weight: 300;
  line-height: 0.98;
  letter-spacing: -0.01em;
  color: #F6F4F0;
  margin: 0 0 6mm 0;
}

.cover .subtitle {
  font-family: 'Cormorant Garamond', serif;
  font-style: italic;
  font-size: 18pt;
  font-weight: 300;
  line-height: 1.3;
  color: #C9A96E;
  margin: 0 0 14mm 0;
  max-width: 145mm;
}

.cover .gold-line {
  display: block;
  width: 50mm;
  height: 1.5px;
  background: #C9A96E;
  margin: 0 0 12mm 0;
  border: none;
}

.cover .lede {
  font-family: 'DM Sans', sans-serif;
  font-size: 11pt;
  font-weight: 300;
  line-height: 1.6;
  color: #D9D5CD;
  max-width: 140mm;
  margin: 0;
}

.cover .meta {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  border-top: 1px solid rgba(201,169,110,0.3);
  padding-top: 8mm;
  gap: 6mm;
}

.cover .meta-block {
  font-family: 'DM Sans', sans-serif;
  font-size: 9pt;
  color: #D9D5CD;
  line-height: 1.4;
}

.cover .meta-block .label {
  font-family: 'Josefin Sans', sans-serif;
  font-size: 7.5pt;
  font-weight: 600;
  letter-spacing: 0.3em;
  color: #C9A96E;
  text-transform: uppercase;
  display: block;
  margin-bottom: 2mm;
}

.content {
  padding: 0;
  max-width: 165mm;
  margin: 0 auto;
}

h1 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 30pt;
  font-weight: 300;
  line-height: 1.12;
  color: #1A1A18;
  margin: 0 0 8mm 0;
  letter-spacing: -0.01em;
  border-bottom: 1px solid rgba(201,169,110,0.4);
  padding-bottom: 5mm;
  page-break-after: avoid;
  page-break-before: always;
}

h1:first-of-type { page-break-before: avoid; }

h2 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 20pt;
  font-weight: 400;
  line-height: 1.2;
  color: #1A1A18;
  margin: 14mm 0 5mm 0;
  letter-spacing: -0.005em;
  page-break-after: avoid;
}

h2::before {
  content: '';
  display: block;
  width: 18mm;
  height: 1.5px;
  background: #C9A96E;
  margin-bottom: 4mm;
}

h3 {
  font-family: 'Josefin Sans', sans-serif;
  font-size: 9pt;
  font-weight: 600;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: #B8975A;
  margin: 9mm 0 3mm 0;
  page-break-after: avoid;
}

h4 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 13pt;
  font-weight: 500;
  font-style: italic;
  color: #1A1A18;
  margin: 6mm 0 2mm 0;
  page-break-after: avoid;
}

p {
  margin: 0 0 4mm 0;
  font-size: 10.5pt;
  line-height: 1.7;
  color: #1A1A18;
  hyphens: auto;
  text-align: left;
}

strong { font-weight: 500; color: #1A1A18; }
em { font-style: italic; color: #1A1A18; }

a {
  color: #B8975A;
  text-decoration: none;
  border-bottom: 1px solid rgba(201,169,110,0.35);
}

ul, ol { margin: 0 0 5mm 0; padding-left: 6mm; }
li { margin: 0 0 2mm 0; font-size: 10.5pt; line-height: 1.6; }
li::marker { color: #C9A96E; }

blockquote {
  margin: 5mm 0;
  padding: 5mm 5mm 5mm 8mm;
  border-left: 2.5px solid #C9A96E;
  font-family: 'Cormorant Garamond', serif;
  font-style: italic;
  font-size: 12pt;
  font-weight: 400;
  line-height: 1.55;
  color: #1A1A18;
  background: rgba(201,169,110,0.05);
  page-break-inside: avoid;
}

hr {
  border: none;
  height: 1px;
  background: rgba(201,169,110,0.3);
  margin: 12mm 0;
}
"""

HTML_DOC = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Summerhill Fine Homes — Creative Brief</title>
<style>{CSS_STYLE}</style>
</head>
<body>

<section class="cover">
  <div class="doc-id">Creative Brief — Confidential</div>
  <div class="pretitle">Summerhill Fine Homes</div>
  <div class="title">Oles Cove &amp;<br>Johnstone Rd.</div>
  <div class="subtitle">Two waterfront residences, two shoot days, one coordinated visual strategy.</div>
  <div class="gold-line"></div>
  <div class="lede">
    A read of both projects before we step on site. Design reads, shot priorities, staging questions, logistics, and a proposed two-day schedule, built so we walk onto each property with a plan rather than a scavenger hunt.
  </div>
  <div class="meta">
    <div class="meta-block">
      <span class="label">Prepared for</span>
      Kyle Paisley<br>Summerhill Fine Homes
    </div>
    <div class="meta-block">
      <span class="label">Shoot window</span>
      May 14–15, 2026
    </div>
    <div class="meta-block">
      <span class="label">Prepared by</span>
      Matt Anthony<br>Photography
    </div>
    <div class="meta-block">
      <span class="label">Drafted</span>
      2026 · 04 · 22
    </div>
  </div>
</section>

<section class="content">
{html_body}
</section>

</body>
</html>
"""

tmp_dir = ROOT / ".tmp"
tmp_dir.mkdir(parents=True, exist_ok=True)
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, dir=str(tmp_dir)) as f:
    f.write(HTML_DOC)
    tmp_html = Path(f.name)

OUT.parent.mkdir(parents=True, exist_ok=True)

cmd = [
    CHROME,
    "--headless=new",
    "--disable-gpu",
    "--no-pdf-header-footer",
    "--virtual-time-budget=10000",
    f"--print-to-pdf={OUT}",
    "--no-margins",
    f"file://{tmp_html}",
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
tmp_html.unlink(missing_ok=True)

if not OUT.exists():
    print("FAILED")
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
else:
    size_kb = OUT.stat().st_size / 1024
    print(f"Rendered: {OUT}")
    print(f"Size: {size_kb:.1f} KB")
