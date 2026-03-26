"""Generate HTML proposals from JSON configs and Jinja2 templates.

Usage:
    python3 tools/generate_proposal.py generate <config.json> [--output <path>] [--publish]
    python3 tools/generate_proposal.py scaffold <type> --client <slug> --owner <name> --company <name>
    python3 tools/generate_proposal.py list-configs

Proposal types for scaffold: creative-partner, project-photography, awards-pitch
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, BaseLoader
except ImportError:
    print("ERROR: jinja2 required. Run: pip3 install --user jinja2")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "business", "sales", "templates")
CONFIG_DIR = os.path.join(BASE_DIR, "business", "sales", "configs")
OUTPUT_DIR = os.path.join(BASE_DIR, "business", "sales")
TEMPLATE_FILE = "proposal.html.j2"


def generate(config_path, output_path=None, publish=False):
    """Generate an HTML proposal from a config file."""
    config_path = Path(config_path)
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        return None

    # Load config
    with open(config_path) as f:
        config = json.load(f)

    # Validate required fields
    required = ["client", "proposal", "cover", "images", "sections"]
    missing = [r for r in required if r not in config]
    if missing:
        print(f"ERROR: Config missing required fields: {', '.join(missing)}")
        return None

    # Load and render template
    template_path = os.path.join(TEMPLATE_DIR, TEMPLATE_FILE)
    if not os.path.exists(template_path):
        print(f"ERROR: Template not found: {template_path}")
        return None

    with open(template_path) as f:
        template_str = f.read()

    env = Environment(loader=BaseLoader(), autoescape=False)
    template = env.from_string(template_str)
    html = template.render(**config)

    # Determine output path
    if not output_path:
        slug = config["client"]["slug"]
        ptype = config["proposal"]["type"]
        filename = config["proposal"].get("filename", f"{slug}-{ptype}.html")
        output_path = os.path.join(OUTPUT_DIR, filename)

    # Write output
    with open(output_path, "w") as f:
        f.write(html)

    size = os.path.getsize(output_path) / 1024
    print(f"Generated: {output_path} ({size:.1f} KB)")

    # Publish if requested
    if publish:
        slug = config["client"]["slug"]
        filename = config["proposal"].get("filename", f"{slug}-{config['proposal']['type']}.html")
        publish_cmd = [
            sys.executable, os.path.join(BASE_DIR, "tools", "publish_proposal.py"),
            "upload", output_path,
            "--client", slug,
            "--name", filename
        ]
        subprocess.run(publish_cmd)

    return output_path


def scaffold(ptype, client_slug, owner_name, company_name):
    """Create a starter config for a given proposal type."""
    # Base config every proposal needs
    config = {
        "client": {
            "company": company_name,
            "slug": client_slug,
            "owner": owner_name,
            "owner_title": "Owner",
            "confidentiality_name": company_name
        },
        "proposal": {
            "type": ptype,
            "title": "",
            "date": "",
            "valid_through": "",
            "filename": f"{client_slug}-{ptype}.html"
        },
        "cover": {
            "eyebrow": company_name,
            "headline_html": "Your creative<br>department.<br><em>Without the overhead.</em>",
            "subtitle": "TODO: One-line description of what this proposal covers.",
            "cta_text": "View Options",
            "cta_target": "#tiers",
            "image_url": "TODO: Squarespace CDN URL for cover image",
            "image_position": "center 25%"
        },
        "images": {
            "breaks": [
                {"url": "TODO: CDN URL", "alt": "TODO: Description", "caption": "TODO: Project &middot; Location &middot; Matt Anthony Photography"}
            ]
        },
        "sections": [],
    }

    if ptype == "creative-partner":
        config["proposal"]["title"] = "Creative Partner"
        config["sections"] = ["story", "services", "pricing", "roadmap", "vision", "numbers", "awards", "next_steps"]
        config["story"] = {
            "eyebrow": "The Story So Far",
            "headline_html": "You build exceptional homes.<br><em>People should know about it.</em>",
            "lead": f"TODO: Relationship context with {owner_name} and {company_name}.",
            "paragraphs": ["TODO: The gap/opportunity.", "TODO: How this proposal closes the gap."],
            "stats": [
                {"value": "TODO", "label": "TODO"},
                {"value": "TODO", "label": "TODO"},
                {"value": "TODO", "label": "TODO"},
                {"value": "TODO", "label": "TODO"}
            ]
        }
        config["services"] = {
            "eyebrow": "What's Included",
            "headline_html": f"Everything {company_name} needs.<br><em>Nothing it doesn't.</em>",
            "intro": "TODO: Context on existing relationship and what this adds.",
            "cards": [
                {"title": "Project Photography", "is_new": True, "entries": [
                    "1 full-day shoot per month", "20 to 25 edited images per session",
                    "Drone and aerial coverage included", "Multi-format delivery: web, print, social, award-ready",
                    "Full licensing for all channels", "Priority scheduling, weather flexibility"
                ]},
                {"title": "Build and Team Content", "is_new": True, "entries": [
                    "Crew action shots and candid documentation", "Material close-ups: timber, steel, craft details",
                    "Construction progress from framing to finish", "Content built for proposals, presentations, and social"
                ]},
                {"title": "Video and Social", "is_new": True, "entries": [
                    "Monthly social media reel from shoot footage", "Year-end project film (Growth and Full tiers)",
                    "Content repurposed for Instagram and LinkedIn", "Monthly strategy call and content calendar"
                ]}
            ]
        }
        config["pricing"] = {
            "eyebrow": "Choose Your Tier",
            "headline_html": "Three tiers. Same partner.<br><em>Your call.</em>",
            "intro": "TODO: Framing for how to choose.",
            "tiers": [
                {
                    "name": "Foundation", "slug": "foundation", "price": "$2,500", "unit": "/ mo",
                    "term": "3-month pilot &middot; $7,500 total", "recommended": False,
                    "entries": [
                        {"text": "1 full-day shoot / month", "included": True},
                        {"text": "20 to 25 edited images", "included": True},
                        {"text": "Drone and aerial coverage", "included": True},
                        {"text": "Multi-format delivery (web, print, social, award)", "included": True},
                        {"text": "Full image licensing", "included": True},
                        {"text": "Project page per shoot", "included": True},
                        {"text": "Build and team content", "included": False},
                        {"text": "Year-end project film", "included": False},
                        {"text": "Social media reel", "included": False},
                        {"text": "Monthly strategy call", "included": False},
                        {"text": "Full social media management", "included": False}
                    ],
                    "bottom_label": "Annual investment", "bottom_value": "$30,000"
                },
                {
                    "name": "Growth", "slug": "growth", "price": "$3,000", "unit": "/ mo",
                    "term": "3-month pilot &middot; $9,000 total", "recommended": True,
                    "entries": [
                        {"text": "1 full-day shoot / month", "included": True},
                        {"text": "20 to 25 edited images", "included": True},
                        {"text": "Drone and aerial coverage", "included": True},
                        {"text": "Build and team content (crew, materials, progress)", "included": True},
                        {"text": "Multi-format delivery (web, print, social, award)", "included": True},
                        {"text": "Full image licensing", "included": True},
                        {"text": "Project page per shoot", "included": True},
                        {"text": "Monthly social media reel", "included": True},
                        {"text": "Monthly strategy call", "included": True},
                        {"text": "Year-end project film (60 to 90 seconds)", "included": True},
                        {"text": "Full social media management", "included": False}
                    ],
                    "bottom_label": "Annual investment", "bottom_value": "$36,000"
                },
                {
                    "name": "Full Creative Partner", "slug": "full", "price": "$3,500", "unit": "/ mo",
                    "term": "3-month pilot &middot; $10,500 total", "recommended": False,
                    "entries": [
                        {"text": "1 full-day shoot / month", "included": True},
                        {"text": "25 to 30 edited images", "included": True},
                        {"text": "Drone and aerial coverage", "included": True},
                        {"text": "Build and team content (crew, materials, progress)", "included": True},
                        {"text": "Multi-format delivery (web, print, social, award)", "included": True},
                        {"text": "Full image licensing", "included": True},
                        {"text": "Project page per shoot", "included": True},
                        {"text": "Monthly social media reel", "included": True},
                        {"text": "Monthly strategy call", "included": True},
                        {"text": "Year-end documentary film (2 to 3 minutes)", "included": True},
                        {"text": "Full social media management (3x/week)", "included": True}
                    ],
                    "bottom_label": "Annual investment", "bottom_value": "$42,000"
                }
            ],
            "insight": {
                "title": "How to Think About This",
                "content_html": "<p>TODO: Comparison framing.</p>",
                "breakdowns": [
                    {"label": "Foundation", "desc": "TODO"},
                    {"label": "Growth", "desc": "TODO"},
                    {"label": "Creative Partner", "desc": "TODO"}
                ]
            }
        }
        config["roadmap"] = {
            "eyebrow": "3-Month Pilot Roadmap",
            "headline_html": "What gets done.<br><em>Month by month.</em>",
            "intro": "TODO: Pilot overview.",
            "months": [
                {"month": "TODO Month 1", "label_html": "TODO:<br>First Shoot", "entries": ["TODO"]},
                {"month": "TODO Month 2", "label_html": "TODO:<br>Second Shoot", "entries": ["TODO"]},
                {"month": "TODO Month 3", "label_html": "TODO:<br>Prove It", "entries": ["TODO"]}
            ],
            "stats": [
                {"value": "3", "label": "Full-Day Shoots"},
                {"value": "75", "label": "Professional Images"},
                {"value": "3", "label": "Social Reels"},
                {"value": "90", "label": "Days to Prove It"}
            ]
        }
        config["vision"] = {
            "eyebrow": "The 12-Month Vision",
            "headline_html": "What a full year<br><em>looks like.</em>",
            "intro": "TODO: Vision framing.",
            "quarters": [
                {"period": "Q2 2026", "title": "Prove the Model", "description": "TODO"},
                {"period": "Q3 2026", "title": "Scale the Library", "description": "TODO"},
                {"period": "Q4 2026", "title": "Leverage the Work", "description": "TODO"},
                {"period": "Q1 2027", "title": "The Advantage Compounds", "description": "TODO"}
            ]
        }
        config["numbers"] = {
            "stats": [
                {"value": "300", "label": "Professional Images"},
                {"value": "12", "label": "Drone Flights"},
                {"value": "12", "label": "Blog Posts"}
            ]
        }
        config["awards"] = {
            "eyebrow": "Awards &amp; Publications",
            "headline_html": "The credentials your<br><em>competitors already have.</em>",
            "lead": f"TODO: Awards gap for {company_name}.",
            "paragraphs": ["TODO: Why this matters."],
            "competitor_numbers": [
                {"value": "0", "label": f"{company_name} Awards to Date"},
                {"value": "TODO", "label": "Competitor Awards"},
                {"value": "TODO", "label": "Years of Builds"}
            ],
            "services": [
                {"title": "Award Submissions", "entries": ["Georgie Awards (CHBA BC)", "CHBA National Awards", "HAVAN Awards", "Gold Nugget Awards", "Dezeen &amp; AZ Awards"]},
                {"title": "Publication Pitches", "entries": ["Western Living", "Dwell", "Mountain Life", "ArchDaily &amp; Dezeen", "NUVO Magazine"]}
            ],
            "insight": {
                "title": "One Project, Multiple Credentials",
                "content_html": "<p>A single project photographed to spec can generate <strong>3 to 5 credentials</strong>.</p>"
            }
        }
        config["next_steps"] = {
            "eyebrow": "Next Steps",
            "headline_html": f"Let's start with<br><em>TODO: First project.</em>",
            "paragraphs": [f"TODO: Personal closing message to {owner_name}."],
            "steps": [
                {"number": "1", "title": "Pick Your Tier", "description": "Foundation, Growth, or Full Creative Partner."},
                {"number": "2", "title": "Deposit", "description": "50% of the pilot total to lock in scheduling."},
                {"number": "3", "title": "Plan", "description": "Quick 20-minute call to plan the first shoot."}
            ],
            "valid_note": "This proposal is valid through <strong style=\"color:var(--ink);\">TODO: Date</strong>."
        }

    elif ptype == "project-photography":
        config["proposal"]["title"] = "Project Photography"
        config["sections"] = ["story", "services", "pricing", "next_steps"]
        config["story"] = {
            "eyebrow": "The Project",
            "headline_html": f"TODO: Project headline<br><em>for {company_name}.</em>",
            "lead": "TODO: Project context.",
            "paragraphs": ["TODO"],
            "stats": []
        }
        config["services"] = {
            "eyebrow": "What's Included",
            "headline_html": "Professional documentation.<br><em>Start to finish.</em>",
            "intro": "TODO",
            "cards": [
                {"title": "Photography", "is_new": False, "entries": ["Full-day shoot", "20-25 edited images", "Drone coverage", "Multi-format delivery"]},
                {"title": "Video", "is_new": False, "entries": ["60-90 second highlight film", "Social media reel", "Full licensing"]}
            ]
        }
        config["pricing"] = {
            "eyebrow": "Investment",
            "headline_html": "Simple pricing.<br><em>No surprises.</em>",
            "intro": "TODO",
            "tiers": [
                {"name": "Project Package", "slug": "project", "price": "$3,500", "unit": "", "term": "One-time investment", "recommended": True,
                 "entries": [{"text": "TODO", "included": True}],
                 "bottom_label": "", "bottom_value": ""}
            ]
        }
        config["next_steps"] = {
            "eyebrow": "Next Steps",
            "headline_html": "Let's get<br><em>started.</em>",
            "paragraphs": ["TODO"],
            "steps": [
                {"number": "1", "title": "Confirm", "description": "TODO"},
                {"number": "2", "title": "Schedule", "description": "TODO"},
                {"number": "3", "title": "Shoot", "description": "TODO"}
            ]
        }

    # Write config
    out_path = os.path.join(CONFIG_DIR, f"{client_slug}-{ptype}.json")
    with open(out_path, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"Scaffolded: {out_path}")
    print(f"Fill in the TODO fields, then run:")
    print(f"  python3 tools/generate_proposal.py generate {out_path}")
    print(f"  python3 tools/generate_proposal.py generate {out_path} --publish")
    return out_path


def list_configs():
    """List available config files."""
    if not os.path.exists(CONFIG_DIR):
        print("No configs found")
        return
    configs = sorted(Path(CONFIG_DIR).glob("*.json"))
    if not configs:
        print("No configs found")
        return
    print("Available configs:")
    for c in configs:
        with open(c) as f:
            data = json.load(f)
        client = data.get("client", {}).get("company", "?")
        ptype = data.get("proposal", {}).get("type", "?")
        print(f"  {c.name:<45} {client} — {ptype}")


def main():
    parser = argparse.ArgumentParser(description="Generate HTML proposals from configs")
    sub = parser.add_subparsers(dest="command")

    p_gen = sub.add_parser("generate", help="Generate proposal HTML")
    p_gen.add_argument("config", help="Path to config JSON")
    p_gen.add_argument("--output", help="Output HTML path")
    p_gen.add_argument("--publish", action="store_true", help="Publish to GitHub Pages after generating")

    p_scaffold = sub.add_parser("scaffold", help="Create starter config")
    p_scaffold.add_argument("type", choices=["creative-partner", "project-photography", "awards-pitch"])
    p_scaffold.add_argument("--client", required=True, help="Client slug")
    p_scaffold.add_argument("--owner", required=True, help="Owner/contact name")
    p_scaffold.add_argument("--company", required=True, help="Company name")

    sub.add_parser("list-configs", help="List available configs")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "generate":
        generate(args.config, args.output, args.publish)
    elif args.command == "scaffold":
        scaffold(args.type, args.client, args.owner, args.company)
    elif args.command == "list-configs":
        list_configs()


if __name__ == "__main__":
    main()
