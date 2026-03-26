"""Carousel builder — curates and sequences project photos into engagement-optimized
carousel sets with slide-by-slide narratives.

Uses Claude Vision to analyze images, group them into logical carousel sets,
sequence for maximum engagement (hook → progression → closer), and write
slide-by-slide captions that create open-loop narratives.

Subcommands:
  curate       Analyze images and create carousel sets from a project manifest
  caption      Generate slide-by-slide captions for a carousel set
  full         Full pipeline: curate + caption all sets

Usage:
  # Full pipeline from a processed project
  python tools/carousel_builder.py full \
    --project-dir "Photo Assets/Client/Project" \
    --project "The Perch" \
    --client "Summerhill Fine Homes" \
    --location "Sunshine Coast, BC" \
    --architect "Michel Laflamme Architect"

  # Just curate (group + sequence images, no captions)
  python tools/carousel_builder.py curate \
    --project-dir "Photo Assets/Client/Project"

  # Generate captions for an existing carousel plan
  python tools/carousel_builder.py caption \
    --carousel-plan carousel-plan.json \
    --project "The Perch" \
    --client "Summerhill Fine Homes"
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
load_dotenv(PROJECT_ROOT / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ── Carousel types and their rules ──────────────────────────

CAROUSEL_TYPES = {
    "project_reveal": {
        "name": "Project Reveal",
        "platform": "instagram",
        "slides": "8-12",
        "description": "The hero carousel. Full project walkthrough.",
        "sequence_rule": "Open with strongest exterior or hero interior. Progress outside-in or through the home naturally. End with twilight/drone or strongest overall shot. The first slide must stop the scroll.",
        "caption_style": "Hook first line (curiosity gap or bold observation). 2-3 sentences about the design. Swipe CTA. Tag collaborators.",
    },
    "detail_breakdown": {
        "name": "Detail Breakdown",
        "platform": "instagram",
        "slides": "6-8",
        "description": "Focus on materials, craftsmanship, design decisions.",
        "sequence_rule": "Open with the most striking detail shot. Group by material or trade (all millwork together, all stone together). End with a wide shot showing how the details compose into the whole.",
        "caption_style": "Hook about a specific material or design decision. Educational angle — what makes this detail exceptional. Tag relevant trades.",
    },
    "educational": {
        "name": "Educational",
        "platform": "instagram",
        "slides": "8-12",
        "description": "Teaching content using this project as the example.",
        "sequence_rule": "Slide 1: Bold statement or question as text overlay concept. Slides 2-8: Each image illustrates one point. Final slide: summary or question to drive comments.",
        "caption_style": "Hook is a compelling question. 3-5 concise points. End with a question to drive comments.",
    },
    "linkedin_story": {
        "name": "LinkedIn Project Story",
        "platform": "linkedin",
        "slides": "7-10",
        "description": "B2B document carousel (PDF). Tells the business story.",
        "sequence_rule": "Slide 1: Hero shot with project title overlay concept. Slide 2-3: The challenge/brief. Slides 4-7: The solution (key images). Slide 8-9: The result/impact. Final slide: CTA or contact.",
        "caption_style": "B2B angle. What was the builder's goal? How does documentation help their business? No links in body. 3-5 hashtags.",
    },
    "before_after": {
        "name": "Before/After",
        "platform": "instagram",
        "slides": "4-8",
        "description": "Construction phase vs completed. Transformation story.",
        "sequence_rule": "Alternate before/after pairs of the same angle. Start with most dramatic transformation. End with the overall before vs overall after.",
        "caption_style": "Hook about transformation or time invested. Brief context about the build. Tag builder prominently.",
    },
}


def extract_json(text):
    """Extract JSON from a response that might have markdown fences."""
    import re
    # Try raw first
    text = text.strip()
    if text.startswith("[") or text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    # Try extracting from markdown fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    # Last resort: find first [ or { and parse from there
    for i, c in enumerate(text):
        if c in ("[", "{"):
            try:
                return json.loads(text[i:])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Could not extract JSON from response: {text[:200]}")


def encode_image_b64(path, max_dim=800):
    """Encode image to base64 for Claude Vision."""
    img = Image.open(path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def get_client():
    """Create Anthropic client."""
    import anthropic
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def load_manifest(project_dir):
    """Load the image analysis manifest from a processed project."""
    manifest_path = Path(project_dir) / "social" / "manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: No manifest found at {manifest_path}")
        print("Run resize_images.py batch first to analyze and process images.")
        sys.exit(1)
    with open(manifest_path) as f:
        return json.load(f)


def curate_carousels(manifest, originals_dir):
    """Use Claude Vision to analyze all images and create carousel groupings."""
    client = get_client()

    # Build image grid for Claude to see all images at once
    content = []
    content.append({
        "type": "text",
        "text": "I'm going to show you all images from an architectural photography project. Each image has metadata from a previous analysis. Your job is to curate these into carousel sets.\n\n"
    })

    # Send images in batches with their metadata
    for i, item in enumerate(manifest):
        source_path = Path(item.get("source_path", ""))
        if not source_path.exists():
            # Try relative to originals_dir
            source_path = Path(originals_dir) / item.get("filename", "")
        if not source_path.exists():
            continue

        meta_text = (
            f"IMAGE {i+1}: {item.get('filename', 'unknown')}\n"
            f"  Subject: {item.get('subject', 'unknown')}\n"
            f"  Category: {item.get('category', 'unknown')}\n"
            f"  Composition: {item.get('composition', 'unknown')}\n"
            f"  Hero score: {item.get('hero_score', 0)}/10\n"
            f"  IG format: {item.get('ig_best_format', 'unknown')}"
        )
        content.append({"type": "text", "text": meta_text})
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": encode_image_b64(source_path, max_dim=512),
            }
        })

    carousel_type_descriptions = "\n".join([
        f"- **{k}**: {v['description']} ({v['slides']} slides). Sequencing: {v['sequence_rule']}"
        for k, v in CAROUSEL_TYPES.items()
    ])

    content.append({
        "type": "text",
        "text": f"""Now create carousel sets from these images. Available carousel types:

{carousel_type_descriptions}

Rules:
- Create 2-4 carousel sets from the available images
- Every project MUST have a project_reveal carousel (the main hero set)
- Images can appear in multiple carousels if they serve different narrative purposes
- Sequence images within each carousel for maximum engagement (the first image must be the absolute strongest scroll-stopper)
- Consider visual flow: vary between wide and tight, light and dark, interior and exterior
- The project_reveal carousel should tell the complete story of the home
- A detail_breakdown should group by material/trade/design element
- An educational carousel should teach something using these images as examples
- Reference images by their IMAGE number

Return a JSON array of carousel objects:
[
  {{
    "type": "project_reveal",
    "name": "The Perch — Full Project Reveal",
    "image_indices": [13, 7, 20, 3, 18, 15, 23, 25, 1, 14],
    "sequence_rationale": "Opens with the iconic twilight fire pit shot (10/10 hero). Progresses from exterior approach through living spaces to private rooms. Closes with the aerial establishing shot for scale and context.",
    "suggested_hook_style": "curiosity_gap",
    "notes": "The twilight shots are the strongest openers. The suspended fireplace interior shots create the mid-carousel 'wow' moment."
  }}
]

Return ONLY the JSON array."""
    })

    print("  Analyzing images and creating carousel sets...")
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": content}]
    )

    return extract_json(response.content[0].text)


def generate_carousel_captions(carousel_set, manifest, originals_dir, project_meta):
    """Generate slide-by-slide captions for a carousel set using Vision."""
    client = get_client()
    carousel_type = CAROUSEL_TYPES.get(carousel_set["type"], CAROUSEL_TYPES["project_reveal"])

    # Build content with the actual carousel images in sequence
    content = []
    content.append({
        "type": "text",
        "text": f"You are writing captions for a {carousel_type['name']} carousel for Matt Anthony Photography.\n\n"
               f"Brand voice: Professional but warm. Calm, structured, intentional. No hype, no superlatives, no exclamation marks. Let the work speak.\n\n"
               f"Project: {project_meta.get('project', '')}\n"
               f"Client/Builder: {project_meta.get('client', '')}\n"
               f"Location: {project_meta.get('location', '')}\n"
               f"Architect: {project_meta.get('architect', '')}\n"
               f"Features: {project_meta.get('features', '')}\n"
               f"Trades: {project_meta.get('trades', '')}\n\n"
               f"Carousel: {carousel_set.get('name', '')}\n"
               f"Sequence rationale: {carousel_set.get('sequence_rationale', '')}\n\n"
               f"I'm showing you each slide in order. Generate captions for the FULL POST.\n"
    })

    # Add each image in carousel order
    image_indices = carousel_set.get("image_indices", [])
    for slide_num, idx in enumerate(image_indices, 1):
        # Indices are 1-based from the curation step
        manifest_idx = idx - 1
        if manifest_idx < 0 or manifest_idx >= len(manifest):
            continue

        item = manifest[manifest_idx]
        source_path = Path(item.get("source_path", ""))
        if not source_path.exists():
            source_path = Path(originals_dir) / item.get("filename", "")
        if not source_path.exists():
            continue

        content.append({
            "type": "text",
            "text": f"SLIDE {slide_num}/{len(image_indices)}: {item.get('subject', 'unknown')} ({item.get('category', '')})"
        })
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": encode_image_b64(source_path, max_dim=600),
            }
        })

    platform = carousel_type["platform"]
    caption_style = carousel_type["caption_style"]

    if platform == "instagram":
        content.append({
            "type": "text",
            "text": f"""Now write the Instagram carousel caption and slide-by-slide alt text.

Caption style: {caption_style}

The caption should:
- Reference specific visual details you can SEE in the images (light quality, material textures, spatial relationships, views)
- NOT be generic — mention things only someone who has seen these exact images would know
- Create an "open loop" — the first line should make someone want to swipe
- Under 300 words
- No hashtags (added separately)

Return a JSON object:
{{
  "main_caption": "The full Instagram caption text",
  "hook_line": "Just the first line (for preview/testing)",
  "slide_alt_texts": ["Alt text for slide 1", "Alt text for slide 2", ...],
  "suggested_hashtag_set": "reveal_a" or "reveal_b" or "educational_a" etc (from pre-built rotation groups),
  "engagement_prompt": "A question or CTA designed to drive comments (not just 'what do you think?')"
}}

Return ONLY the JSON."""
        })
    elif platform == "linkedin":
        content.append({
            "type": "text",
            "text": f"""Now write the LinkedIn document carousel text.

Caption style: {caption_style}

The LinkedIn post needs:
1. A post caption (what appears above the carousel) — B2B angle, first 2 lines are the hook
2. Slide-by-slide text overlays (short phrases that would appear on each slide if this were a designed PDF)
3. The post should position the builder/architect's work, not just showcase pretty photos

Return a JSON object:
{{
  "post_caption": "The full LinkedIn post text (no links in body, [Link in first comment] at end)",
  "hook_lines": "First 2 lines (what shows before 'see more')",
  "slide_texts": ["Text overlay for slide 1 (title slide)", "Text for slide 2", ...],
  "hashtags": ["#hashtag1", "#hashtag2", ...],
  "engagement_prompt": "A question designed to drive meaningful B2B conversation"
}}

Return ONLY the JSON."""
        })

    print(f"  Generating captions for: {carousel_set.get('name', 'carousel')}...")
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": content}]
    )

    return extract_json(response.content[0].text)


# ── CLI Commands ────────────────────────────────────────────


def cmd_curate(args):
    """Analyze images and create carousel groupings."""
    project_dir = Path(args.project_dir)
    manifest = load_manifest(project_dir)
    originals_dir = project_dir / "originals"

    print(f"Curating carousels from {len(manifest)} images...")
    carousel_sets = curate_carousels(manifest, originals_dir)

    # Save carousel plan
    output_path = project_dir / "social" / "carousel-plan.json"
    with open(output_path, "w") as f:
        json.dump(carousel_sets, f, indent=2)

    print(f"\nCarousel plan saved to {output_path}")
    print(f"\n{'='*60}")
    print("CAROUSEL SETS")
    print(f"{'='*60}")

    for i, cs in enumerate(carousel_sets, 1):
        ctype = CAROUSEL_TYPES.get(cs["type"], {})
        print(f"\n{i}. {cs.get('name', 'Untitled')} [{cs['type']}]")
        print(f"   Platform: {ctype.get('platform', 'instagram')}")
        print(f"   Slides: {len(cs.get('image_indices', []))}")
        print(f"   Hook style: {cs.get('suggested_hook_style', 'n/a')}")
        print(f"   Rationale: {cs.get('sequence_rationale', '')[:120]}...")

        # Show image sequence
        indices = cs.get("image_indices", [])
        for j, idx in enumerate(indices, 1):
            midx = idx - 1
            if 0 <= midx < len(manifest):
                item = manifest[midx]
                hero = item.get("hero_score", 0)
                star = " ***" if hero >= 9 else ""
                print(f"     Slide {j:2d}: [{hero}/10] {item.get('subject', 'unknown')[:60]}{star}")

    return 0


def cmd_caption(args):
    """Generate captions for carousel sets."""
    if args.carousel_plan:
        plan_path = Path(args.carousel_plan)
    else:
        plan_path = Path(args.project_dir) / "social" / "carousel-plan.json"

    if not plan_path.exists():
        print(f"ERROR: No carousel plan found at {plan_path}")
        print("Run 'curate' first.")
        return 1

    with open(plan_path) as f:
        carousel_sets = json.load(f)

    project_dir = Path(args.project_dir)
    manifest = load_manifest(project_dir)
    originals_dir = project_dir / "originals"

    project_meta = {
        "project": args.project or "",
        "client": args.client or "",
        "location": args.location or "",
        "architect": args.architect or "",
        "features": args.features or "",
        "trades": args.trades or "",
    }

    results = []
    for cs in carousel_sets:
        captions = generate_carousel_captions(cs, manifest, originals_dir, project_meta)
        cs["captions"] = captions
        results.append(cs)

        # Print results
        ctype = CAROUSEL_TYPES.get(cs["type"], {})
        platform = ctype.get("platform", "instagram")
        print(f"\n{'─'*60}")
        print(f"## {cs.get('name', 'Carousel')} [{platform}]")
        print(f"{'─'*60}")

        if platform == "instagram":
            print(f"\nHOOK: {captions.get('hook_line', '')}")
            print(f"\nCAPTION:\n{captions.get('main_caption', '')}")
            print(f"\nENGAGEMENT PROMPT: {captions.get('engagement_prompt', '')}")
            print(f"HASHTAG SET: {captions.get('suggested_hashtag_set', '')}")
        elif platform == "linkedin":
            print(f"\nHOOK: {captions.get('hook_lines', '')}")
            print(f"\nPOST:\n{captions.get('post_caption', '')}")
            print(f"\nSLIDE TEXTS:")
            for j, st in enumerate(captions.get("slide_texts", []), 1):
                print(f"  Slide {j}: {st}")
            print(f"\nENGAGEMENT: {captions.get('engagement_prompt', '')}")

    # Save complete plan with captions
    output_path = project_dir / "social" / "carousel-plan.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n\nFull carousel plan with captions saved to {output_path}")
    return 0


def cmd_full(args):
    """Full pipeline: curate + caption."""
    project_dir = Path(args.project_dir)
    manifest = load_manifest(project_dir)
    originals_dir = project_dir / "originals"

    print(f"Found {len(manifest)} images in manifest")
    print(f"\nStep 1: Curating carousel sets...\n")

    carousel_sets = curate_carousels(manifest, originals_dir)

    print(f"\nCreated {len(carousel_sets)} carousel sets")
    print(f"\nStep 2: Generating vision-enhanced captions...\n")

    project_meta = {
        "project": args.project or "",
        "client": args.client or "",
        "location": args.location or "",
        "architect": args.architect or "",
        "features": args.features or "",
        "trades": args.trades or "",
    }

    results = []
    for cs in carousel_sets:
        captions = generate_carousel_captions(cs, manifest, originals_dir, project_meta)
        cs["captions"] = captions
        results.append(cs)

    # Save
    output_path = project_dir / "social" / "carousel-plan.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print("CAROUSEL PLAN COMPLETE")
    print(f"{'='*60}")

    for i, cs in enumerate(results, 1):
        ctype = CAROUSEL_TYPES.get(cs["type"], {})
        platform = ctype.get("platform", "instagram")
        captions = cs.get("captions", {})

        print(f"\n{'─'*60}")
        print(f"{i}. {cs.get('name', 'Untitled')} [{platform}] — {len(cs.get('image_indices', []))} slides")
        print(f"{'─'*60}")

        if platform == "instagram":
            print(f"\nHOOK: {captions.get('hook_line', '')}")
            print(f"\nCAPTION:\n{captions.get('main_caption', '')}")
            print(f"\nENGAGEMENT: {captions.get('engagement_prompt', '')}")
            print(f"HASHTAG SET: {captions.get('suggested_hashtag_set', '')}")

            alt_texts = captions.get("slide_alt_texts", [])
            if alt_texts:
                print(f"\nALT TEXTS:")
                for j, alt in enumerate(alt_texts, 1):
                    print(f"  Slide {j}: {alt}")

        elif platform == "linkedin":
            print(f"\nHOOK: {captions.get('hook_lines', '')}")
            print(f"\nPOST:\n{captions.get('post_caption', '')}")
            slide_texts = captions.get("slide_texts", [])
            if slide_texts:
                print(f"\nSLIDE OVERLAY TEXTS:")
                for j, st in enumerate(slide_texts, 1):
                    print(f"  Slide {j}: {st}")
            print(f"\nENGAGEMENT: {captions.get('engagement_prompt', '')}")

    # Image usage summary
    all_used = set()
    for cs in results:
        all_used.update(cs.get("image_indices", []))
    unused = [i+1 for i in range(len(manifest)) if (i+1) not in all_used]

    print(f"\n{'='*60}")
    print("IMAGE USAGE")
    print(f"{'='*60}")
    print(f"  Used in carousels: {len(all_used)}/{len(manifest)}")
    if unused:
        print(f"  Not in any carousel: {len(unused)} images")
        print(f"  These are best used as: standalone singles, Pinterest pins, or Stories")
        for idx in unused:
            item = manifest[idx-1]
            print(f"    [{item.get('hero_score', 0)}/10] {item.get('subject', 'unknown')[:60]}")

    print(f"\nFull plan saved to: {output_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Build engagement-optimized carousel sets from project photos"
    )
    sub = parser.add_subparsers(dest="command")

    # Shared args
    def add_project_args(p):
        p.add_argument("--project-dir", required=True, help="Project directory (with social/manifest.json)")
        p.add_argument("--project", default="", help="Project name")
        p.add_argument("--client", default="", help="Client/builder name")
        p.add_argument("--location", default="", help="Project location")
        p.add_argument("--architect", default="", help="Architect/designer")
        p.add_argument("--features", default="", help="Standout features")
        p.add_argument("--trades", default="", help="Trades to tag")

    # --- curate ---
    cur = sub.add_parser("curate", help="Analyze images and create carousel groupings")
    cur.add_argument("--project-dir", required=True, help="Project directory")

    # --- caption ---
    cap = sub.add_parser("caption", help="Generate captions for carousel sets")
    add_project_args(cap)
    cap.add_argument("--carousel-plan", help="Path to carousel plan JSON (default: project-dir/social/carousel-plan.json)")

    # --- full ---
    full = sub.add_parser("full", help="Full pipeline: curate + caption")
    add_project_args(full)

    args = parser.parse_args()

    if args.command == "curate":
        return cmd_curate(args)
    elif args.command == "caption":
        return cmd_caption(args)
    elif args.command == "full":
        return cmd_full(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
