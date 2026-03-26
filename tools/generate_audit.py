"""Generate visual SEO & GEO audit reports from JSON configs.

Usage:
    python3 tools/generate_audit.py generate <config.json> [--output <path>] [--publish]
    python3 tools/generate_audit.py scaffold --client <slug> --company <name> --url <website>

Generates a standalone HTML audit report using the audit-report template.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    from jinja2 import Environment, BaseLoader
except ImportError:
    print("ERROR: jinja2 required. Run: pip3 install --user jinja2")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "business", "sales", "templates")
CONFIG_DIR = os.path.join(BASE_DIR, "business", "sales", "configs")
OUTPUT_DIR = os.path.join(BASE_DIR, "business", "sales")
TEMPLATE_FILE = "audit-report.html.j2"


def generate(config_path, output_path=None, publish=False):
    config_path = Path(config_path)
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        return None

    with open(config_path) as f:
        config = json.load(f)

    template_path = os.path.join(TEMPLATE_DIR, TEMPLATE_FILE)
    with open(template_path) as f:
        template_str = f.read()

    env = Environment(loader=BaseLoader(), autoescape=False)
    template = env.from_string(template_str)
    html = template.render(**config)

    if not output_path:
        slug = config["client"]["slug"]
        output_path = os.path.join(OUTPUT_DIR, f"{slug}-site-audit.html")

    with open(output_path, "w") as f:
        f.write(html)

    size = os.path.getsize(output_path) / 1024
    print(f"Generated: {output_path} ({size:.1f} KB)")

    if publish:
        slug = config["client"]["slug"]
        publish_cmd = [
            sys.executable, os.path.join(BASE_DIR, "tools", "publish_proposal.py"),
            "upload", output_path,
            "--client", slug,
            "--name", "site-audit.html"
        ]
        subprocess.run(publish_cmd)

    return output_path


def scaffold(client_slug, company_name, website_url):
    config = {
        "client": {"company": company_name, "slug": client_slug},
        "audit_date": "March 2026",
        "cover": {
            "headline_html": f"{company_name}<br><em>Site &amp; SEO Audit</em>",
            "image_url": "TODO: Cover image CDN URL",
            "image_position": "center 30%"
        },
        "images": {"breaks": [
            {"url": "TODO", "alt": "TODO", "caption": "TODO"}
        ]},
        "overall_scores": [
            {"value": 0, "label": "Overall SEO", "grade": "TODO", "color": "bad"},
            {"value": 0, "label": "Local / GEO", "grade": "TODO", "color": "bad"},
            {"value": 0, "label": "Content", "grade": "TODO", "color": "bad"},
            {"value": 0, "label": "Visual Assets", "grade": "TODO", "color": "bad"}
        ],
        "sections": [
            {
                "type": "seo",
                "eyebrow": "SEO Audit",
                "headline_html": "Search visibility.<br><em>Where you rank today.</em>",
                "lead": f"TODO: SEO summary for {website_url}",
                "categories": [
                    {"name": "Technical SEO", "findings": [
                        {"status": "fail", "title": "TODO", "detail": "TODO"}
                    ]},
                    {"name": "On-Page SEO", "findings": [
                        {"status": "fail", "title": "TODO", "detail": "TODO"}
                    ]},
                    {"name": "Content & Keywords", "findings": [
                        {"status": "fail", "title": "TODO", "detail": "TODO"}
                    ]}
                ]
            },
            {
                "type": "geo",
                "eyebrow": "Local SEO &amp; GEO Audit",
                "headline_html": "Local visibility.<br><em>Can they find you?</em>",
                "lead": "TODO",
                "categories": [
                    {"name": "Google Business Profile", "findings": [
                        {"status": "fail", "title": "TODO", "detail": "TODO"}
                    ]}
                ]
            },
            {
                "type": "competitors",
                "eyebrow": "Competitive Landscape",
                "headline_html": "How you compare.<br><em>Side by side.</em>",
                "lead": "TODO",
                "columns": ["Builder", "Website", "SEO", "Social", "Awards"],
                "rows": [
                    {"highlight": True, "cells": [company_name, "TODO", "TODO", "TODO", "TODO"]},
                    {"highlight": False, "cells": ["Competitor 1", "TODO", "TODO", "TODO", "TODO"]}
                ]
            },
            {
                "type": "content",
                "eyebrow": "Content &amp; Visual Assets",
                "headline_html": "What you have.<br><em>What you\u2019re missing.</em>",
                "lead": "TODO",
                "categories": [
                    {"name": "Photography", "findings": [
                        {"status": "fail", "title": "TODO", "detail": "TODO"}
                    ]}
                ]
            },
            {
                "type": "recommendations",
                "eyebrow": "What I\u2019d Fix First",
                "headline_html": "The action plan.<br><em>Priority order.</em>",
                "lead": "TODO",
                "stats": [
                    {"value": "TODO", "label": "TODO"},
                    {"value": "TODO", "label": "TODO"},
                    {"value": "TODO", "label": "TODO"}
                ],
                "steps": [
                    {"number": "1", "title": "TODO", "description": "TODO"},
                    {"number": "2", "title": "TODO", "description": "TODO"},
                    {"number": "3", "title": "TODO", "description": "TODO"}
                ],
                "insight": {
                    "title": "This Is Where a Creative Partner Comes In",
                    "content_html": "<p>TODO: Connect audit findings to proposal.</p>"
                }
            }
        ]
    }

    out_path = os.path.join(CONFIG_DIR, f"{client_slug}-audit.json")
    with open(out_path, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"Scaffolded: {out_path}")
    print(f"Fill in findings, then run:")
    print(f"  python3 tools/generate_audit.py generate {out_path} --publish")


def main():
    parser = argparse.ArgumentParser(description="Generate visual SEO/GEO audit reports")
    sub = parser.add_subparsers(dest="command")

    p_gen = sub.add_parser("generate", help="Generate audit HTML")
    p_gen.add_argument("config", help="Path to audit config JSON")
    p_gen.add_argument("--output", help="Output HTML path")
    p_gen.add_argument("--publish", action="store_true", help="Publish to GitHub Pages")

    p_scaffold = sub.add_parser("scaffold", help="Create starter audit config")
    p_scaffold.add_argument("--client", required=True, help="Client slug")
    p_scaffold.add_argument("--company", required=True, help="Company name")
    p_scaffold.add_argument("--url", required=True, help="Website URL")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == "generate":
        generate(args.config, args.output, args.publish)
    elif args.command == "scaffold":
        scaffold(args.client, args.company, args.url)


if __name__ == "__main__":
    main()
