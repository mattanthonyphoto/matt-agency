#!/usr/bin/env python3
"""Sync ALL content from mattanthonyphoto.com into structured JSON files for AI use.

Pulls:
- All project pages (architect, builder, designer, materials, brief)
- All journal/blog posts (title, summary, key points)
- Case studies and partner pages

Outputs:
- tools/playbooks/matt-anthony.json — projects updated with full briefs
- tools/data/journal_library.json — all journal posts indexed
- tools/data/partner_briefs.json — partner/client pages

Run anytime the website is updated.

Usage:
  python3 tools/sync_website_content.py              # sync everything
  python3 tools/sync_website_content.py --projects   # only projects
  python3 tools/sync_website_content.py --journals   # only journal
  python3 tools/sync_website_content.py --partners   # only partner pages
"""
import os
import sys
import json
import argparse
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

PLAYBOOK = PROJECT_ROOT / "tools" / "playbooks" / "matt-anthony.json"
DATA_DIR = PROJECT_ROOT / "tools" / "data"
JOURNAL_FILE = DATA_DIR / "journal_library.json"
PARTNER_FILE = DATA_DIR / "partner_briefs.json"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# All URLs from the sitemap
PROJECT_URLS = {
    "the-perch": "https://www.mattanthonyphoto.com/the-perch-sunshine-coast",
    "warbler": "https://www.mattanthonyphoto.com/warbler-whistler",
    "fitzsimmons": "https://www.mattanthonyphoto.com/fitzsimmons-whistler",
    "fraser-valley-vista": "https://www.mattanthonyphoto.com/fraser-valley-vista",
    "sda-bc-headquarters": "https://www.mattanthonyphoto.com/seventh-day-adventist-bc-headquarters",
    "osprey": "https://www.mattanthonyphoto.com/osprey",
    "tranquil-retreat": "https://www.mattanthonyphoto.com/tranquil-retreat",
    "browns-residence": "https://www.mattanthonyphoto.com/browns-residence",
    "net-zero-whistler": "https://www.mattanthonyphoto.com/net-zero-build-whistler",
    "silverstar": "https://www.mattanthonyphoto.com/silver-star-residence",
    "sugarloaf": "https://www.mattanthonyphoto.com/sugarloaf-residence",
    "eagle": "https://www.mattanthonyphoto.com/eagle-residence",
    "wakefield-rooftop": "https://www.mattanthonyphoto.com/wakefield-rooftop-oasis",
    "gambier": "https://www.mattanthonyphoto.com/gambier-island-residence",
    "art-deco-reno": "https://www.mattanthonyphoto.com/art-deco-reno",
    "sunridge": "https://www.mattanthonyphoto.com/sunridge-whistler",
    "west-10th": "https://www.mattanthonyphoto.com/west-10th-vancouver",
    "balsam-way": "https://www.mattanthonyphoto.com/balsam-way",
    "sunset-beach": "https://www.mattanthonyphoto.com/sunset-beach",
}

JOURNAL_URLS = [
    "https://www.mattanthonyphoto.com/journal/how-to-photograph-your-project-for-award-submissions",
    "https://www.mattanthonyphoto.com/journal/what-architects-should-look-for-hiring-photographer",
    "https://www.mattanthonyphoto.com/journal/architectural-photography-whistler-mountain-projects",
    "https://www.mattanthonyphoto.com/journal/summerhill-fine-homes-visual-brand-ongoing-photography",
    "https://www.mattanthonyphoto.com/journal/roi-professional-architectural-photography-builders",
    "https://www.mattanthonyphoto.com/journal/why-your-award-submission-photos-arent-working",
    "https://www.mattanthonyphoto.com/journal/documenting-design-intent-photography-before-build-finished",
    "https://www.mattanthonyphoto.com/journal/how-to-prepare-project-architectural-photo-shoot",
    "https://www.mattanthonyphoto.com/journal/project-photography-vs-real-estate-photography",
    "https://www.mattanthonyphoto.com/journal/seasonal-considerations-architectural-photography-bc",
    "https://www.mattanthonyphoto.com/journal/behind-the-shoot-the-perch-sunshine-coast",
    "https://www.mattanthonyphoto.com/journal/5-details-make-or-break-architectural-interior-photography",
    "https://www.mattanthonyphoto.com/journal/construction-lifestyle-photography-best-social-media-investment-builders",
    "https://www.mattanthonyphoto.com/journal/what-georgie-award-judges-look-for-submission-photography",
    "https://www.mattanthonyphoto.com/journal/how-to-build-visual-library-website-proposals-awards",
    "https://www.mattanthonyphoto.com/journal/georgie-awards-guide",
    "https://www.mattanthonyphoto.com/journal/architectural-photography-for-publications",
    "https://www.mattanthonyphoto.com/journal/aibc-awards-guide",
    "https://www.mattanthonyphoto.com/journal/chba-national-awards-guide",
    "https://www.mattanthonyphoto.com/journal/dezeen-submissions-guide",
    "https://www.mattanthonyphoto.com/journal/dwell-submissions-guide",
    "https://www.mattanthonyphoto.com/journal/havan-awards-guide",
    "https://www.mattanthonyphoto.com/journal/raic-awards-guide",
    "https://www.mattanthonyphoto.com/journal/western-living-submissions",
    "https://www.mattanthonyphoto.com/journal/how-cost-sharing-works-architectural-photography",
]

PARTNER_URLS = {
    "summerhill-fine-homes": "https://www.mattanthonyphoto.com/summerhill-fine-homes",
    "balmoral-construction": "https://www.mattanthonyphoto.com/balmoral-construction",
    "sitelines-architecture": "https://www.mattanthonyphoto.com/sitelines-architecture",
    "the-window-merchant": "https://www.mattanthonyphoto.com/the-window-merchant",
    "lrd-studio": "https://www.mattanthonyphoto.com/lrd-studio-interior-design",
}


def fetch_page(url: str) -> str:
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  ✗ {e}")
        return ""


def claude_extract(html: str, schema_prompt: str) -> dict:
    if not ANTHROPIC_API_KEY:
        return {}
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        text = html[:30000] if len(html) > 30000 else html
        msg = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{"role": "user", "content": schema_prompt + "\n\nPage content:\n" + text}]
        )
        response = msg.content[0].text.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
            response = response.strip()
        return json.loads(response)
    except Exception as e:
        print(f"  ✗ Claude extract: {e}")
        return {}


def sync_projects():
    print("\n=== SYNCING PROJECT BRIEFS ===\n")
    with open(PLAYBOOK) as f:
        playbook = json.load(f)

    existing_slugs = {p.get("slug"): i for i, p in enumerate(playbook["projects"])}

    schema_prompt = """Extract project data from this architectural photographer's project page. Return ONLY a valid JSON object (no markdown):

{
  "name": "project name",
  "architect": "architect name or null",
  "builder": "builder name or null",
  "interior_designer": "designer name or null",
  "location": "city, region",
  "design_intent": "1-2 sentences describing the design philosophy",
  "materials": ["material 1", "material 2", "..."],
  "brief": "2-3 paragraph editorial description from the page"
}

Use null for missing fields. materials should be 3-8 specific items. brief should be the actual editorial copy, not a summary."""

    updated = 0
    added = 0
    for slug, url in PROJECT_URLS.items():
        print(f"→ {slug}: {url}")
        html = fetch_page(url)
        if not html:
            continue
        data = claude_extract(html, schema_prompt)
        if not data:
            continue
        # Drop nulls
        data = {k: v for k, v in data.items() if v not in (None, "", [], "null")}
        data["pinterest_url"] = url

        if slug in existing_slugs:
            playbook["projects"][existing_slugs[slug]].update(data)
            updated += 1
            print(f"  ✓ updated existing")
        else:
            data["slug"] = slug
            data["path"] = ""  # Photo path - needs manual setup
            data["photo_count"] = 0
            data["client"] = data.get("builder") or data.get("architect") or ""
            playbook["projects"].append(data)
            added += 1
            print(f"  ✓ added new")
        time.sleep(0.5)  # Be polite

    with open(PLAYBOOK, "w") as f:
        json.dump(playbook, f, indent=2)
    print(f"\n✓ Projects: {updated} updated, {added} added")


def sync_journals():
    print("\n=== SYNCING JOURNAL POSTS ===\n")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    schema_prompt = """Extract journal/blog post data from this architectural photographer's article. Return ONLY a valid JSON object:

{
  "title": "post title",
  "category": "Awards | Process | Education | Case Study | Industry",
  "summary": "2-3 sentence summary",
  "key_points": ["point 1", "point 2", "..."],
  "target_audience": "architects | builders | designers | general",
  "primary_topic": "what is this article really about",
  "useful_for": "what AI use case this content supports (e.g., 'caption inspiration', 'sales pitch material', 'client education')"
}"""

    journals = []
    for url in JOURNAL_URLS:
        slug = url.split("/")[-1]
        print(f"→ {slug}")
        html = fetch_page(url)
        if not html:
            continue
        data = claude_extract(html, schema_prompt)
        if data:
            data["url"] = url
            data["slug"] = slug
            journals.append(data)
            print(f"  ✓ {data.get('title', slug)[:50]}")
        time.sleep(0.5)

    output = {
        "journals": journals,
        "count": len(journals),
        "last_synced": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(JOURNAL_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n✓ Journals: {len(journals)} posts saved to {JOURNAL_FILE.name}")


def sync_partners():
    print("\n=== SYNCING PARTNER PAGES ===\n")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    schema_prompt = """Extract partner/client information from this case study page on an architectural photographer's website. Return ONLY a valid JSON object:

{
  "name": "company name",
  "type": "builder | architect | interior designer | trade",
  "location": "city, region",
  "summary": "1-2 sentence intro to who they are",
  "relationship": "1-2 sentences about working with Matt",
  "projects_together": ["project 1", "project 2"],
  "key_quotes": ["any direct quotes from them"]
}"""

    partners = {}
    for slug, url in PARTNER_URLS.items():
        print(f"→ {slug}")
        html = fetch_page(url)
        if not html:
            continue
        data = claude_extract(html, schema_prompt)
        if data:
            data["url"] = url
            partners[slug] = data
            print(f"  ✓ {data.get('name', slug)}")
        time.sleep(0.5)

    output = {
        "partners": partners,
        "count": len(partners),
        "last_synced": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(PARTNER_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n✓ Partners: {len(partners)} saved to {PARTNER_FILE.name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--projects", action="store_true", help="Sync only projects")
    parser.add_argument("--journals", action="store_true", help="Sync only journal posts")
    parser.add_argument("--partners", action="store_true", help="Sync only partner pages")
    args = parser.parse_args()

    if not (args.projects or args.journals or args.partners):
        # Default: sync everything
        sync_projects()
        sync_journals()
        sync_partners()
    else:
        if args.projects:
            sync_projects()
        if args.journals:
            sync_journals()
        if args.partners:
            sync_partners()


if __name__ == "__main__":
    main()
