#!/usr/bin/env python3
"""Sync project briefs from mattanthonyphoto.com into the playbook.

For each project in tools/playbooks/matt-anthony.json that has a pinterest_url
(which is the actual project page URL on the website), fetch the page and use
Claude to extract architect, builder, designer, materials, design intent, and
the editorial brief.

Run this whenever you update a project page on the website to keep the AI's
context fresh.

Usage:
  python3 tools/sync_project_briefs.py                # sync all projects
  python3 tools/sync_project_briefs.py --slug warbler # sync one project
  python3 tools/sync_project_briefs.py --dry-run      # show what would change
"""
import os
import sys
import json
import argparse
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

PLAYBOOK = PROJECT_ROOT / "tools" / "playbooks" / "matt-anthony.json"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


def fetch_page_text(url: str) -> str:
    """Fetch a webpage and return raw HTML/text."""
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  ✗ Failed to fetch {url}: {e}")
        return ""


def extract_brief_with_claude(page_html: str, project_name: str) -> dict:
    """Send page HTML to Claude and extract structured brief data."""
    if not ANTHROPIC_API_KEY:
        print("  ✗ ANTHROPIC_API_KEY not set")
        return {}

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=ANTHROPIC_API_KEY)

        # Trim HTML to a reasonable size (Claude can handle a lot but no point sending nav/footer)
        # Try to extract just the main content
        text = page_html
        if len(text) > 30000:
            text = text[:30000]

        prompt = f"""You are extracting structured data from a project page on an architectural photographer's website.

Project: {project_name}

Page HTML/text:
{text}

Extract the following and return ONLY a valid JSON object (no markdown fences, no commentary):

{{
  "architect": "name or null",
  "builder": "name or null",
  "interior_designer": "name or null",
  "location": "city, region",
  "design_intent": "1-2 sentence design philosophy as quoted or paraphrased from the page",
  "materials": ["material 1", "material 2", "..."],
  "brief": "2-3 paragraph editorial description of the project pulled from the page. Should read like the architect/photographer would describe it."
}}

Rules:
- If a field isn't on the page, use null (NOT empty string)
- materials should be an array of 3-8 specific materials/finishes mentioned
- brief should be the actual editorial text from the page, not a summary
- Return ONLY the JSON, no preamble"""

        msg = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = msg.content[0].text.strip()

        # Strip any markdown fences
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        data = json.loads(response_text)
        # Drop null fields
        return {k: v for k, v in data.items() if v not in (None, "", [], "null")}
    except Exception as e:
        print(f"  ✗ Claude extraction failed: {e}")
        return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", help="Sync only one project by slug")
    parser.add_argument("--dry-run", action="store_true", help="Don't save changes")
    args = parser.parse_args()

    with open(PLAYBOOK) as f:
        playbook = json.load(f)

    updated_count = 0
    for proj in playbook["projects"]:
        slug = proj.get("slug", "")
        if args.slug and slug != args.slug:
            continue

        url = proj.get("pinterest_url", "")
        if not url or "mattanthonyphoto.com" not in url:
            print(f"⊘ {slug}: no website URL, skipping")
            continue

        if url.endswith("/projects"):
            print(f"⊘ {slug}: generic projects page, skipping")
            continue

        print(f"→ {slug}: fetching {url}")
        html = fetch_page_text(url)
        if not html:
            continue

        brief_data = extract_brief_with_claude(html, proj.get("name", slug))
        if not brief_data:
            print(f"  ✗ No data extracted")
            continue

        if args.dry_run:
            print(f"  Would update with: {list(brief_data.keys())}")
            print(f"  Brief preview: {brief_data.get('brief', '')[:100]}...")
        else:
            proj.update(brief_data)
            updated_count += 1
            print(f"  ✓ Updated ({len(brief_data)} fields)")

    if not args.dry_run and updated_count > 0:
        with open(PLAYBOOK, "w") as f:
            json.dump(playbook, f, indent=2)
        print(f"\n✓ Saved {updated_count} updates to {PLAYBOOK.name}")
    elif args.dry_run:
        print("\n(dry run — no changes saved)")
    else:
        print("\nNo updates to save")


if __name__ == "__main__":
    main()
