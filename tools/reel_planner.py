"""Reel planner — generates Reel scripts, shot lists, and audio suggestions
from project photos and metadata.

Reels drive 2.5x more reach than any other format. This tool creates
ready-to-execute Reel plans from your project assets.

Subcommands:
  plan         Generate Reel plans for a project (multiple Reel concepts)
  script       Generate a detailed script for a single Reel concept

Usage:
  python tools/reel_planner.py plan \
    --project-dir "Photo Assets/Summerhill Fine Homes/The Perch" \
    --project "The Perch" \
    --client "Summerhill Fine Homes" \
    --location "Sunshine Coast, BC"

  python tools/reel_planner.py script \
    --project-dir "Photo Assets/Summerhill Fine Homes/The Perch" \
    --concept "walkthrough_reveal" \
    --project "The Perch"
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

# ── Reel formats that perform for architecture ──────────────

REEL_FORMATS = {
    "walkthrough_reveal": {
        "name": "Walkthrough Reveal",
        "duration": "15-30 sec",
        "description": "Smooth walkthrough from entry to hero space. The money shot is the payoff.",
        "structure": "Approach exterior → enter front door → move through hallway → reveal hero space (living room, view, etc.)",
        "audio": "Trending audio or ambient with bass drop at reveal moment",
        "shoot_notes": "Gimbal required. One continuous motion or 3-4 stitched clips. Slow, deliberate movement.",
        "best_for": "First Reel from a new project. Maximum wow factor.",
    },
    "before_after": {
        "name": "Before/After Transformation",
        "duration": "8-15 sec",
        "description": "Construction phase snaps to finished. Dramatic transformation.",
        "structure": "Construction shot (hold 2 sec) → transition effect → finished shot from same angle (hold 3 sec)",
        "audio": "Sound effect transition (snap, whoosh) + trending audio",
        "shoot_notes": "Need construction phase photos from same angle. Phone photos work. Match the framing as closely as possible.",
        "best_for": "Builder audience. Shows the transformation they deliver.",
    },
    "detail_slowmo": {
        "name": "Detail Slow-Mo",
        "duration": "10-20 sec",
        "description": "Slow pans across standout details. Materials, textures, craftsmanship.",
        "structure": "3-4 slow pan clips (3-5 sec each): material texture → hardware → millwork → wide context shot",
        "audio": "Minimal ambient or soft instrumental. Let the visuals breathe.",
        "shoot_notes": "Tripod or gimbal. Slow horizontal pan. Close enough to see grain/texture. Golden hour light preferred.",
        "best_for": "Detail-oriented audience. Designers, millwork shops, trades.",
    },
    "timelapse_retouch": {
        "name": "Retouching Timelapse",
        "duration": "15-30 sec",
        "description": "Screen recording of your editing process sped up. Shows the craft behind the final image.",
        "structure": "Start with raw file → color correction → perspective correction → final export. Speed up 20-40x.",
        "audio": "Lo-fi or ambient electronic. Nothing distracting.",
        "shoot_notes": "Screen record in Lightroom/Capture One. Record 5-10 min of real editing, speed up in editor.",
        "best_for": "Process content. Other photographers and curious clients.",
    },
    "drone_reveal": {
        "name": "Drone Reveal",
        "duration": "10-20 sec",
        "description": "Aerial perspective reveals the full site context. Rising or orbiting shot.",
        "structure": "Start tight on a detail (roof, deck, landscape) → pull back/rise to reveal full property and surroundings",
        "audio": "Cinematic ambient or trending audio with build-up",
        "shoot_notes": "Need drone footage. Single continuous clip works best. Dawn/dusk for dramatic light.",
        "best_for": "Properties with strong site context — waterfront, mountain, forest.",
    },
    "photo_slideshow": {
        "name": "Photo Slideshow with Motion",
        "duration": "15-30 sec",
        "description": "Ken Burns effect on still photos. No video needed — works with existing portfolio.",
        "structure": "8-12 photos with subtle zoom/pan (Ken Burns). 2-3 sec per image. Build from exterior to interior to hero shot.",
        "audio": "Trending audio that matches the mood. Sync transitions to beat drops.",
        "shoot_notes": "No video required. Use existing project photos. Add subtle motion in CapCut or InShot.",
        "best_for": "When you have no video footage. Every project can have this Reel.",
    },
    "educational_talking": {
        "name": "Educational Quick Tip",
        "duration": "15-30 sec",
        "description": "Text overlay on project photos teaching something. No talking head needed.",
        "structure": "Hook text (2 sec) → Point 1 with photo (4 sec) → Point 2 with photo (4 sec) → Point 3 with photo (4 sec) → CTA text (2 sec)",
        "audio": "Trending audio (low volume) under text. Or voiceover if comfortable.",
        "shoot_notes": "Use existing photos. Add text overlays in CapCut, InShot, or Instagram editor. Bold, readable font.",
        "best_for": "Educational pillar. Positions you as an expert, not just a photographer.",
    },
    "day_to_night": {
        "name": "Day to Twilight Transition",
        "duration": "8-15 sec",
        "description": "Same angle captured at different times. Shows how light transforms architecture.",
        "structure": "Daylight shot (hold 3 sec) → smooth transition → twilight shot from same angle (hold 5 sec)",
        "audio": "Ambient transition sound + moody music for twilight portion",
        "shoot_notes": "Shoot same composition at golden hour and blue hour. Tripod essential. Match framing exactly.",
        "best_for": "Showing the value of twilight photography. Convinces builders to book evening sessions.",
    },
}


def encode_image_b64(path, max_dim=600):
    """Encode image to base64."""
    img = Image.open(path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def extract_json(text):
    """Extract JSON from response that might have markdown fences."""
    import re
    text = text.strip()
    if text.startswith("[") or text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    for i, c in enumerate(text):
        if c in ("[", "{"):
            try:
                return json.loads(text[i:])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Could not extract JSON from response: {text[:200]}")


def get_client():
    """Create Anthropic client."""
    import anthropic
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def load_manifest(project_dir):
    """Load image manifest."""
    manifest_path = Path(project_dir) / "social" / "manifest.json"
    if not manifest_path.exists():
        return []
    with open(manifest_path) as f:
        return json.load(f)


def cmd_plan(args):
    """Generate Reel plans for a project."""
    client = get_client()
    project_dir = Path(args.project_dir)
    manifest = load_manifest(project_dir)
    originals_dir = project_dir / "originals"

    # Build vision content with top images
    content = []
    content.append({
        "type": "text",
        "text": f"I'm planning Instagram Reels for an architectural photography project.\n\n"
               f"Project: {args.project}\n"
               f"Client: {args.client}\n"
               f"Location: {args.location}\n"
               f"Architect: {getattr(args, 'architect', '')}\n\n"
               f"Here are the project photos:\n"
    })

    # Show top images
    heroes = sorted(manifest, key=lambda x: x.get("hero_score", 0), reverse=True)[:8]
    for i, item in enumerate(heroes):
        source = Path(item.get("source_path", ""))
        if not source.exists():
            source = originals_dir / item.get("filename", "")
        if not source.exists():
            continue

        content.append({
            "type": "text",
            "text": f"Image {i+1}: {item.get('subject', '')} ({item.get('category', '')})"
        })
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": encode_image_b64(source),
            }
        })

    # Available Reel formats
    formats_desc = "\n".join([
        f"- **{k}**: {v['name']} — {v['description']} ({v['duration']}). Best for: {v['best_for']}"
        for k, v in REEL_FORMATS.items()
    ])

    content.append({
        "type": "text",
        "text": f"""Based on these project photos, create 4-6 Reel concepts. Available formats:

{formats_desc}

For each Reel, return a JSON array of objects:
[
  {{
    "format": "walkthrough_reveal",
    "title": "The Perch — First Look",
    "hook_text": "Text that appears in the first 1-2 seconds (the scroll-stopper)",
    "concept": "2-3 sentence description of the Reel concept and why it works for this project",
    "sequence": ["Shot 1 description", "Shot 2 description", ...],
    "duration_estimate": "20 sec",
    "audio_suggestion": "Specific audio recommendation",
    "caption": "The Instagram caption for this Reel (1-2 sentences, hook first)",
    "difficulty": "easy" | "medium" | "hard",
    "requires_video": true/false,
    "image_refs": [1, 3, 5] (which images from above to use, if photo-based),
    "priority": 1-6 (1 = make this first)
  }}
]

Rules:
- At least 1 Reel must be "easy" (photo_slideshow or educational — no video needed)
- At least 1 should leverage the strongest visual from this project
- Consider what would make someone send this Reel to a colleague
- Hook text must work in 0.5 seconds — bold, specific, visual
- Captions: brand voice is professional but warm, no hype, no exclamation marks

Return ONLY the JSON array."""
    })

    print(f"Analyzing project and generating Reel plans...")
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": content}]
    )

    reel_plans = extract_json(response.content[0].text)

    # Save
    output_path = project_dir / "social" / "reel-plans.json"
    with open(output_path, "w") as f:
        json.dump(reel_plans, f, indent=2)

    # Print
    print(f"\n{'='*60}")
    print(f"REEL PLANS: {args.project}")
    print(f"{'='*60}")

    for reel in sorted(reel_plans, key=lambda x: x.get("priority", 99)):
        fmt = REEL_FORMATS.get(reel.get("format", ""), {})
        difficulty = reel.get("difficulty", "medium")
        video_req = "Video needed" if reel.get("requires_video") else "Photos only"
        priority = reel.get("priority", "?")

        print(f"\n{'─'*60}")
        print(f"[Priority {priority}] {reel.get('title', 'Untitled')}")
        print(f"  Format: {fmt.get('name', reel.get('format', '?'))} | {reel.get('duration_estimate', '?')} | {difficulty} | {video_req}")
        print(f"{'─'*60}")
        print(f"\n  HOOK TEXT: \"{reel.get('hook_text', '')}\"")
        print(f"\n  CONCEPT: {reel.get('concept', '')}")
        print(f"\n  SHOT LIST:")
        for j, shot in enumerate(reel.get("sequence", []), 1):
            print(f"    {j}. {shot}")
        print(f"\n  AUDIO: {reel.get('audio_suggestion', '')}")
        print(f"  CAPTION: {reel.get('caption', '')}")

        if reel.get("image_refs"):
            print(f"  IMAGES: {', '.join(str(r) for r in reel['image_refs'])}")

        if fmt.get("shoot_notes"):
            print(f"\n  SHOOT NOTES: {fmt['shoot_notes']}")

    # Summary
    easy = [r for r in reel_plans if r.get("difficulty") == "easy"]
    no_video = [r for r in reel_plans if not r.get("requires_video")]

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  Total Reel concepts: {len(reel_plans)}")
    print(f"  Easy (no video editing): {len(easy)}")
    print(f"  Photos-only (no footage needed): {len(no_video)}")
    print(f"\n  Start with Priority 1 — the easiest win.")
    print(f"\n  Saved to: {output_path}")

    return 0


def cmd_script(args):
    """Generate a detailed production script for a single Reel."""
    client = get_client()
    project_dir = Path(args.project_dir)

    # Load existing reel plans
    plans_path = project_dir / "social" / "reel-plans.json"
    if plans_path.exists():
        with open(plans_path) as f:
            plans = json.load(f)
    else:
        print("No reel plans found. Run 'plan' first.")
        return 1

    # Find the requested concept
    target = None
    for plan in plans:
        if plan.get("format") == args.concept or args.concept.lower() in plan.get("title", "").lower():
            target = plan
            break

    if not target:
        print(f"Concept '{args.concept}' not found. Available:")
        for p in plans:
            print(f"  - {p.get('format', '?')}: {p.get('title', '?')}")
        return 1

    fmt = REEL_FORMATS.get(target.get("format", ""), {})

    print(f"\n{'='*60}")
    print(f"PRODUCTION SCRIPT: {target.get('title', '')}")
    print(f"{'='*60}")
    print(f"\n  Format: {fmt.get('name', '?')}")
    print(f"  Duration: {target.get('duration_estimate', fmt.get('duration', '?'))}")
    print(f"  Audio: {target.get('audio_suggestion', '')}")

    print(f"\n{'─'*60}")
    print("PRE-PRODUCTION CHECKLIST")
    print(f"{'─'*60}")

    if target.get("requires_video"):
        print("  [ ] Charge gimbal / ensure stabilization")
        print("  [ ] Scout the walkthrough path")
        print("  [ ] Check lighting conditions (golden hour preferred)")
        print("  [ ] Clear the path of obstacles")
        print("  [ ] Do 2-3 practice walks before recording")
    else:
        print("  [ ] Select images (see image_refs below)")
        print("  [ ] Open CapCut or InShot")
        print("  [ ] Find audio (search trending sounds in IG)")
        print("  [ ] Prep text overlays if needed")

    print(f"\n{'─'*60}")
    print("SHOT-BY-SHOT BREAKDOWN")
    print(f"{'─'*60}")

    for j, shot in enumerate(target.get("sequence", []), 1):
        print(f"\n  Shot {j}:")
        print(f"    {shot}")

    print(f"\n{'─'*60}")
    print("POST-PRODUCTION")
    print(f"{'─'*60}")
    print(f"  1. Import clips/photos to editor (CapCut recommended for Reels)")
    print(f"  2. Trim to {target.get('duration_estimate', '15-30 sec')}")
    print(f"  3. Add audio: {target.get('audio_suggestion', 'trending sound')}")
    print(f"  4. Add hook text overlay: \"{target.get('hook_text', '')}\"")
    print(f"  5. Export at 1080x1920 (9:16)")
    print(f"  6. Upload to Instagram with caption below")

    print(f"\n{'─'*60}")
    print("CAPTION")
    print(f"{'─'*60}")
    print(f"  {target.get('caption', '')}")

    if fmt.get("shoot_notes"):
        print(f"\n{'─'*60}")
        print("TIPS")
        print(f"{'─'*60}")
        print(f"  {fmt['shoot_notes']}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Generate Reel plans and scripts from project photos"
    )
    sub = parser.add_subparsers(dest="command")

    # --- plan ---
    pln = sub.add_parser("plan", help="Generate Reel plans for a project")
    pln.add_argument("--project-dir", required=True, help="Project directory")
    pln.add_argument("--project", required=True, help="Project name")
    pln.add_argument("--client", default="", help="Client/builder")
    pln.add_argument("--location", default="", help="Location")
    pln.add_argument("--architect", default="", help="Architect")

    # --- script ---
    scr = sub.add_parser("script", help="Detailed script for one Reel concept")
    scr.add_argument("--project-dir", required=True, help="Project directory")
    scr.add_argument("--concept", required=True, help="Reel format name or title keyword")
    scr.add_argument("--project", default="", help="Project name")

    args = parser.parse_args()

    if args.command == "plan":
        return cmd_plan(args)
    elif args.command == "script":
        return cmd_script(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
