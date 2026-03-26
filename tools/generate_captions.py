"""Social media caption generator — uses Claude API to produce platform-specific
captions from project metadata.

Subcommands:
  generate     Generate captions for a project (all platforms)
  single       Generate a single caption for one platform/type
  batch        Generate captions for multiple projects from a Google Sheet

Usage:
  python tools/generate_captions.py generate \
    --project "The Perch" \
    --client "Balmoral Construction" \
    --location "Sunshine Coast" \
    --architect "Sitelines Architecture" \
    --features "cantilevered living space, floor-to-ceiling glazing, ocean views" \
    --trades "@westcoast_millwork"

  python tools/generate_captions.py single \
    --project "The Perch" \
    --client "Balmoral Construction" \
    --location "Sunshine Coast" \
    --platform instagram \
    --type carousel

  python tools/generate_captions.py batch \
    --sheet-id "YOUR_SHEET_ID" \
    --tab "Content Queue"
"""

import argparse
import base64
import io
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

BRAND_VOICE = """
You are writing social media captions for Matt Anthony Photography, an
architectural and interiors photographer based in Squamish, BC.

Brand voice: Professional but warm. Calm, structured, intentional. No hype,
no superlatives, no exclamation marks. Let the work speak. Documentary
aesthetic — clarity and intention over spectacle.

Target audience: Architects, custom home builders, interior designers, and
construction firms in British Columbia.

Service areas: Sea-to-Sky Corridor, Sunshine Coast, Vancouver, Fraser Valley,
Okanagan.

Instagram handle: @mattanthonyphoto
Website: mattanthonyphoto.com
"""

PLATFORM_RULES = {
    "instagram": {
        "carousel": {
            "instructions": """Write an Instagram carousel caption.
- Hook must be the FIRST line — no preamble, no "New work:" style announcements
- Use curiosity gaps, story entries, or specific observations as hooks
- 2-3 sentences about the design (not the photography) after the hook
- End with a CTA (link in bio, swipe, or tag acknowledgment)
- Tag collaborators at the end: @builder @architect @designer
- Keep under 300 words
- Do NOT include hashtags (those are added separately)""",
        },
        "reel": {
            "instructions": """Write an Instagram Reel caption.
- 1-2 sentences max — the video does the talking
- Hook in the first line
- Brief context about what's shown
- Do NOT include hashtags (those are added separately)""",
        },
        "single": {
            "instructions": """Write an Instagram single image caption.
- Focus on one specific detail or material
- 1-2 sentences, tight and specific
- Tag relevant trades
- Do NOT include hashtags (those are added separately)""",
        },
        "educational": {
            "instructions": """Write an Instagram educational carousel caption.
- Hook must be a compelling question or bold statement
- 3-5 concise points, each 1-2 sentences
- End with a question to drive comments
- Do NOT include hashtags (those are added separately)""",
        },
        "testimonial": {
            "instructions": """Write an Instagram testimonial post caption.
- Lead with the strongest line from the testimonial in quotes
- Full quote attributed to the client
- 1 honest sentence about the working relationship
- Soft CTA at the end
- Do NOT include hashtags (those are added separately)""",
        },
        "behindthescenes": {
            "instructions": """Write an Instagram behind-the-scenes caption.
- Hook about the challenge, surprise, or process
- 1-2 sentences expanding on what made this shoot interesting
- "More from this project coming soon."
- Do NOT include hashtags (those are added separately)""",
        },
    },
    "linkedin": {
        "project": {
            "instructions": """Write a LinkedIn project story post.
- First 2 lines are the hook — all that shows before "see more"
- B2B angle: what was the builder's/architect's goal? How does this project
  position them in their market?
- 3-5 short paragraphs, one thought per line, liberal line breaks
- Connect to a broader industry insight
- NO links in the body — write "[Link in first comment]" at the end
- Tag collaborators with @ mentions
- End with 3-5 hashtags: #architecturephotography #constructionmarketing #bcbuilder etc.
- Do NOT use exclamation marks""",
        },
        "insight": {
            "instructions": """Write a LinkedIn industry insight/educational text post.
- First 2 lines are the hook — provocative statement or contrarian take
- State the problem clearly with a specific example
- 2-3 supporting points, each a short paragraph
- Closing: perspective shift, not a hard sell
- NO links in the body
- End with 3-5 hashtags
- Do NOT use exclamation marks""",
        },
        "client": {
            "instructions": """Write a LinkedIn client spotlight post.
- Hook about the value of documentation or the client relationship
- Tell the client's story — how professional photography impacted their business
- Broader lesson for the industry
- No hard CTA — let the story sell
- Tag the client company
- End with 3-5 hashtags
- Do NOT use exclamation marks""",
        },
    },
    "pinterest": {
        "pin": {
            "instructions": """Write a Pinterest pin title and description.

PIN TITLE (60-80 characters, keyword-first):
Format: "[Style] [Type] in [Location], BC — [Standout Feature]"

PIN DESCRIPTION (100-200 words):
- Open with project type, location, and 2-3 key design elements
- Name the architect/designer and builder
- One sentence about what makes this space special
- One sentence connecting to a broader design trend
- End with "Architectural photography by Matt Anthony Photography, Squamish BC.
  See the full project gallery at mattanthonyphoto.com."
- Add 8-10 hashtags: #WestCoastModern #CustomHome #ArchitecturalPhotography etc.

PIN ALT TEXT (1 sentence):
Format: "[Adjective] [room/space] with [key features] in a [style] [building type] in [Location], BC."

Output all three clearly labeled.""",
        },
    },
}


def get_client():
    """Create Anthropic client."""
    import anthropic

    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def encode_image_b64(path, max_dim=800):
    """Encode image to base64 for Claude Vision."""
    img = Image.open(path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def load_hero_images(project_dir, count=3):
    """Load top hero images from a project manifest for vision-enhanced captions."""
    manifest_path = Path(project_dir) / "social" / "manifest.json"
    if not manifest_path.exists():
        return []

    with open(manifest_path) as f:
        manifest = json.load(f)

    # Sort by hero score, take top N
    scored = sorted(manifest, key=lambda x: x.get("hero_score", 0), reverse=True)
    heroes = []
    for item in scored[:count]:
        source = Path(item.get("source_path", ""))
        if not source.exists():
            source = Path(project_dir) / "originals" / item.get("filename", "")
        if source.exists():
            heroes.append({
                "path": source,
                "subject": item.get("subject", ""),
                "category": item.get("category", ""),
                "hero_score": item.get("hero_score", 0),
            })
    return heroes


def build_project_context(args):
    """Build project context string from CLI args."""
    parts = [f"Project: {args.project}"]
    if args.client:
        parts.append(f"Client/Builder: {args.client}")
    if args.location:
        parts.append(f"Location: {args.location}")
    if args.architect:
        parts.append(f"Architect/Designer: {args.architect}")
    if args.features:
        parts.append(f"Standout features: {args.features}")
    if args.trades:
        parts.append(f"Notable trades to tag: {args.trades}")
    if args.testimonial:
        parts.append(f"Client testimonial: \"{args.testimonial}\"")
    if args.notes:
        parts.append(f"Additional notes: {args.notes}")
    return "\n".join(parts)


def generate_caption(client, project_context, platform, content_type, hero_images=None):
    """Generate a single caption using Claude API, optionally with Vision."""
    rules = PLATFORM_RULES.get(platform, {}).get(content_type)
    if not rules:
        print(f"ERROR: Unknown platform/type: {platform}/{content_type}")
        return None

    prompt_text = f"""Generate a social media caption using these details:

{project_context}

Platform: {platform}
Content type: {content_type}

Rules:
{rules['instructions']}

"""

    if hero_images:
        prompt_text += """I'm showing you the actual project photos. Reference SPECIFIC visual details
you can see — light quality, material textures, spatial relationships, views,
colors, architectural forms. Write as someone who has SEEN this space, not
just read about it. Avoid generic descriptions.

"""

    prompt_text += "Write ONLY the caption — no preamble, no labels, no explanation. Just the ready-to-post text."

    # Build message content (text-only or multimodal)
    if hero_images:
        content = []
        for img in hero_images:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": encode_image_b64(img["path"]),
                }
            })
        content.append({"type": "text", "text": prompt_text})
        messages = [{"role": "user", "content": content}]
    else:
        messages = [{"role": "user", "content": prompt_text}]

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=BRAND_VOICE,
        messages=messages,
    )
    return message.content[0].text


# ── generate (all platforms) ─────────────────────────────────


def cmd_generate(args):
    """Generate captions for all platforms/types."""
    client = get_client()
    project_context = build_project_context(args)

    # Load hero images for vision-enhanced captions if project dir is available
    hero_images = None
    if args.project_dir:
        hero_images = load_hero_images(args.project_dir, count=3)
        if hero_images:
            print(f"Vision mode: Using {len(hero_images)} hero images for context")
            for img in hero_images:
                print(f"  [{img['hero_score']}/10] {img['subject'][:60]}")
            print()
        else:
            print("No manifest found — generating captions from metadata only\n")

    # Define what to generate
    outputs = [
        ("instagram", "carousel", "Instagram Carousel"),
        ("instagram", "reel", "Instagram Reel"),
        ("instagram", "single", "Instagram Detail/Single"),
        ("instagram", "behindthescenes", "Instagram BTS"),
        ("linkedin", "project", "LinkedIn Project Story"),
        ("linkedin", "insight", "LinkedIn Industry Insight"),
        ("pinterest", "pin", "Pinterest Pin"),
    ]

    # Add testimonial if provided
    if args.testimonial:
        outputs.append(("instagram", "testimonial", "Instagram Testimonial"))
        outputs.append(("linkedin", "client", "LinkedIn Client Spotlight"))

    results = {}
    for platform, content_type, label in outputs:
        print(f"Generating: {label}...")
        caption = generate_caption(client, project_context, platform, content_type, hero_images)
        if caption:
            results[label] = caption

    # Output
    print("\n" + "=" * 70)
    print(f"CAPTIONS FOR: {args.project}")
    print("=" * 70)

    for label, caption in results.items():
        print(f"\n{'─' * 50}")
        print(f"## {label}")
        print(f"{'─' * 50}")
        print(caption)

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_data = {
            "project": args.project,
            "client": args.client,
            "location": args.location,
            "captions": results,
        }
        output_path.write_text(json.dumps(output_data, indent=2))
        print(f"\nSaved to {output_path}")

    return 0


# ── single caption ───────────────────────────────────────────


def cmd_single(args):
    """Generate a single caption for one platform/type."""
    client = get_client()
    project_context = build_project_context(args)

    print(f"Generating {args.platform}/{args.type}...")
    caption = generate_caption(client, project_context, args.platform, args.type)

    if caption:
        print(f"\n{'─' * 50}")
        print(caption)

    if args.output:
        Path(args.output).write_text(caption)
        print(f"\nSaved to {args.output}")

    return 0


# ── batch from Google Sheet ──────────────────────────────────


def cmd_batch(args):
    """Generate captions for multiple projects from a Google Sheet.

    Expected sheet columns:
    A: Project Name
    B: Client/Builder
    C: Location
    D: Architect/Designer
    E: Standout Features
    F: Notable Trades
    G: Testimonial (optional)
    H: Notes (optional)
    I+: Output columns (filled by this script)
    """
    from tools.google_sheets_auth import get_sheets_service

    sheets = get_sheets_service()
    client = get_client()

    # Read input
    result = sheets.spreadsheets().values().get(
        spreadsheetId=args.sheet_id,
        range=f"'{args.tab}'!A:H",
    ).execute()
    rows = result.get("values", [])

    if len(rows) < 2:
        print("No data rows found.")
        return 0

    headers = [h.strip().lower() for h in rows[0]]

    # Map columns
    col_map = {}
    for i, h in enumerate(headers):
        if "project" in h:
            col_map["project"] = i
        elif "client" in h or "builder" in h:
            col_map["client"] = i
        elif "location" in h:
            col_map["location"] = i
        elif "architect" in h or "designer" in h:
            col_map["architect"] = i
        elif "feature" in h:
            col_map["features"] = i
        elif "trade" in h:
            col_map["trades"] = i
        elif "testimonial" in h:
            col_map["testimonial"] = i
        elif "note" in h:
            col_map["notes"] = i

    if "project" not in col_map:
        print("ERROR: No 'Project' column found in sheet headers.")
        return 1

    def get_val(row, key):
        idx = col_map.get(key)
        if idx is not None and idx < len(row):
            return row[idx].strip()
        return ""

    # Process each row
    output_rows = [
        [
            "Project",
            "IG Carousel",
            "IG Reel",
            "IG Detail",
            "IG BTS",
            "LinkedIn Project",
            "LinkedIn Insight",
            "Pinterest Pin",
        ]
    ]

    for i, row in enumerate(rows[1:], start=2):
        project = get_val(row, "project")
        if not project:
            continue

        print(f"\nRow {i}: {project}")

        # Build a namespace that looks like argparse output
        class ProjectArgs:
            pass

        pa = ProjectArgs()
        pa.project = project
        pa.client = get_val(row, "client")
        pa.location = get_val(row, "location")
        pa.architect = get_val(row, "architect")
        pa.features = get_val(row, "features")
        pa.trades = get_val(row, "trades")
        pa.testimonial = get_val(row, "testimonial")
        pa.notes = get_val(row, "notes")

        project_context = build_project_context(pa)

        captions = []
        for platform, content_type, label in [
            ("instagram", "carousel", "IG Carousel"),
            ("instagram", "reel", "IG Reel"),
            ("instagram", "single", "IG Detail"),
            ("instagram", "behindthescenes", "IG BTS"),
            ("linkedin", "project", "LinkedIn Project"),
            ("linkedin", "insight", "LinkedIn Insight"),
            ("pinterest", "pin", "Pinterest Pin"),
        ]:
            print(f"  → {label}...")
            caption = generate_caption(client, project_context, platform, content_type)
            captions.append(caption or "")

        output_rows.append([project] + captions)

    # Write results to a new tab
    output_tab = args.output_tab or "Generated Captions"
    sheets.spreadsheets().values().update(
        spreadsheetId=args.sheet_id,
        range=f"'{output_tab}'!A1",
        valueInputOption="RAW",
        body={"values": output_rows},
    ).execute()

    print(f"\nDone. {len(output_rows) - 1} projects written to '{output_tab}' tab.")
    return 0


# ── CLI ──────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Generate social media captions using Claude API"
    )
    sub = parser.add_subparsers(dest="command")

    # --- generate ---
    gen = sub.add_parser("generate", help="Generate captions for all platforms")
    gen.add_argument("--project", required=True, help="Project name")
    gen.add_argument("--client", default="", help="Client/builder name")
    gen.add_argument("--location", default="", help="Project location")
    gen.add_argument("--architect", default="", help="Architect or designer")
    gen.add_argument("--features", default="", help="Standout design features")
    gen.add_argument("--trades", default="", help="Notable trades to tag")
    gen.add_argument("--testimonial", default="", help="Client testimonial quote")
    gen.add_argument("--notes", default="", help="Additional context")
    gen.add_argument("--project-dir", default="", help="Project directory with social/manifest.json for vision-enhanced captions")
    gen.add_argument("--output", help="Save JSON output to file path")

    # --- single ---
    single = sub.add_parser("single", help="Generate one caption")
    single.add_argument("--project", required=True, help="Project name")
    single.add_argument("--client", default="", help="Client/builder name")
    single.add_argument("--location", default="", help="Project location")
    single.add_argument("--architect", default="", help="Architect or designer")
    single.add_argument("--features", default="", help="Standout design features")
    single.add_argument("--trades", default="", help="Notable trades to tag")
    single.add_argument("--testimonial", default="", help="Client testimonial quote")
    single.add_argument("--notes", default="", help="Additional context")
    single.add_argument(
        "--platform",
        required=True,
        choices=["instagram", "linkedin", "pinterest"],
    )
    single.add_argument(
        "--type",
        required=True,
        choices=[
            "carousel",
            "reel",
            "single",
            "educational",
            "testimonial",
            "behindthescenes",
            "project",
            "insight",
            "client",
            "pin",
        ],
    )
    single.add_argument("--output", help="Save caption to file path")

    # --- batch ---
    batch = sub.add_parser("batch", help="Batch generate from Google Sheet")
    batch.add_argument("--sheet-id", required=True, help="Google Sheet ID")
    batch.add_argument("--tab", default="Content Queue", help="Input tab name")
    batch.add_argument("--output-tab", default="Generated Captions", help="Output tab")

    args = parser.parse_args()

    if args.command == "generate":
        return cmd_generate(args)
    elif args.command == "single":
        return cmd_single(args)
    elif args.command == "batch":
        return cmd_batch(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
