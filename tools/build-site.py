#!/usr/bin/env python3
"""
Static site builder for mattanthonyphoto.com
Converts Squarespace code injection blocks into standalone HTML pages.

Usage:
    python tools/build-site.py                    # Build to dist/
    python tools/build-site.py --image-base URL   # Rewrite image URLs
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parent.parent
WEBSITE_DIR = ROOT / "business" / "website"
CODE_BLOCKS = WEBSITE_DIR / "code-blocks"
CONFIG_FILE = WEBSITE_DIR / "site-config.json"
TEMPLATE_FILE = WEBSITE_DIR / "template.html"
DIST_DIR = ROOT / "dist"


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def load_template():
    with open(TEMPLATE_FILE, "r") as f:
        return f.read()


def read_code_block(relative_path):
    full_path = CODE_BLOCKS / relative_path
    if not full_path.exists():
        print(f"  WARNING: Missing code block: {full_path}")
        return None
    with open(full_path, "r") as f:
        return f.read()


def rewrite_squarespace_images(html, image_base):
    """Replace Squarespace CDN URLs with new image base URL."""
    if not image_base:
        return html

    def replace_url(match):
        full_url = match.group(0)
        # Extract filename from Squarespace URL
        # Pattern: .../content/.../HASH/filename.jpg?format=...
        # We want just the filename
        parts = full_url.split("/")
        filename_with_params = parts[-1]
        filename = filename_with_params.split("?")[0]
        return f"{image_base.rstrip('/')}/{filename}"

    # Match Squarespace CDN image URLs
    pattern = r'https://images\.squarespace-cdn\.com/content/[^"\'>\s)]+'
    return re.sub(pattern, replace_url, html)


def build_page(template, page_config, header_html, image_base=None):
    """Build a single page from template + code block."""
    code_block = read_code_block(page_config["file"])
    if code_block is None:
        return None

    # Rewrite image URLs if needed
    if image_base:
        code_block = rewrite_squarespace_images(code_block, image_base)
        header_html_final = rewrite_squarespace_images(header_html, image_base)
    else:
        header_html_final = header_html

    meta = page_config.get("meta", {})
    title = meta.get("title", "Matt Anthony Photography")
    description = meta.get("description", "")
    og_description = meta.get("og_description", description)
    url = page_config.get("url", "/")
    canonical = f"https://mattanthonyphoto.com{url}"

    # Build the page
    html = template
    html = html.replace("{{title}}", title)
    html = html.replace("{{description}}", description)
    html = html.replace("{{og_description}}", og_description)
    html = html.replace("{{canonical}}", canonical)
    html = html.replace("{{url}}", url)
    html = html.replace("{{header}}", header_html_final)
    html = html.replace("{{content}}", code_block)

    return html


def build_site(image_base=None):
    config = load_config()
    template = load_template()
    header_html = read_code_block("sitewide/sitewide-header.html")

    if header_html is None:
        print("ERROR: Could not load sitewide header")
        sys.exit(1)

    if image_base:
        print(f"Rewriting images to: {image_base}")

    # Clean dist (preserve images directory)
    if DIST_DIR.exists():
        import shutil
        for item in DIST_DIR.iterdir():
            if item.name == "images" or item.name == ".git":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    pages_built = 0
    pages_failed = 0

    for page in config["pages"]:
        url = page["url"]
        slug = page.get("slug", url.strip("/"))

        # Determine output path
        if url == "/":
            out_path = DIST_DIR / "index.html"
        else:
            out_path = DIST_DIR / slug / "index.html"

        html = build_page(template, page, header_html, image_base)
        if html is None:
            pages_failed += 1
            continue

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            f.write(html)

        pages_built += 1
        print(f"  Built: {url}")

    # Copy CNAME for GitHub Pages custom domain
    cname_path = DIST_DIR / "CNAME"
    with open(cname_path, "w") as f:
        f.write("mattanthonyphoto.com\n")

    # Create .nojekyll to skip Jekyll processing
    (DIST_DIR / ".nojekyll").touch()

    # Create 404 page
    create_404(template, header_html, image_base)

    print(f"\nDone! {pages_built} pages built, {pages_failed} failed.")
    print(f"Output: {DIST_DIR}")


def create_404(template, header_html, image_base=None):
    """Create a simple 404 page."""
    content = """<style>
.err-wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;background:#1a1a18;padding:2rem}
.err-wrap h1{font-family:'Cormorant Garamond',Georgia,serif;font-size:clamp(3rem,8vw,6rem);font-weight:300;color:#f6f4f0;margin:0}
.err-wrap p{font-family:'DM Sans',sans-serif;font-size:.85rem;color:#8a8579;letter-spacing:.1em;margin:1rem 0 2rem}
.err-wrap a{font-family:'DM Sans',sans-serif;font-size:.65rem;letter-spacing:.2em;text-transform:uppercase;padding:.8rem 2rem;border:1px solid #c9a96e;color:#c9a96e;text-decoration:none;transition:all .3s ease}
.err-wrap a:hover{background:#c9a96e;color:#1a1a18}
</style>
<div class="err-wrap">
  <h1>404</h1>
  <p>This page doesn't exist</p>
  <a href="/">Back to Home</a>
</div>"""

    if image_base:
        header_html = rewrite_squarespace_images(header_html, image_base)

    html = template if isinstance(template, str) else ""
    html = html.replace("{{title}}", "Page Not Found | Matt Anthony Photography")
    html = html.replace("{{description}}", "")
    html = html.replace("{{og_description}}", "")
    html = html.replace("{{canonical}}", "https://mattanthonyphoto.com/404")
    html = html.replace("{{url}}", "/404")
    html = html.replace("{{header}}", header_html)
    html = html.replace("{{content}}", content)

    out_path = DIST_DIR / "404.html"
    with open(out_path, "w") as f:
        f.write(html)
    print("  Built: /404")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build mattanthonyphoto.com static site")
    parser.add_argument("--image-base", help="Base URL for images (e.g., https://images.mattanthonyphoto.com)")
    args = parser.parse_args()

    build_site(image_base=args.image_base)
