"""Social media manager — central engine for Matt Anthony Photography's
content pipeline. Orchestrates image processing, carousel building, caption
generation, content planning, and scheduling.

Subcommands:
  ingest       Full pipeline: process a new project from photos to content plan
  plan         Generate a 4-week content calendar from a processed project
  brief        Daily briefing: what's scheduled, what needs attention
  report       Monthly performance report with strategy recommendations

Usage:
  # Process a new project end-to-end
  python tools/social_media_manager.py ingest \
    --project-dir "Photo Assets/Summerhill Fine Homes/The Perch" \
    --project "The Perch" \
    --client "Summerhill Fine Homes" \
    --location "Sunshine Coast, BC" \
    --architect "Michel Laflamme Architect" \
    --features "floor-to-ceiling glass, suspended fireplace, dark wood cladding" \
    --trades "@summerhillfinehomes @atelier_michel_laflamme" \
    --website "https://mattanthonyphoto.com/the-perch-sunshine-coast"

  # Generate a 4-week content calendar
  python tools/social_media_manager.py plan \
    --project-dir "Photo Assets/Summerhill Fine Homes/The Perch" \
    --start-date 2026-03-24

  # Daily briefing
  python tools/social_media_manager.py brief \
    --sheet-id "YOUR_CONTENT_CALENDAR_SHEET_ID"

  # Monthly report
  python tools/social_media_manager.py report \
    --sheet-id "YOUR_CONTENT_CALENDAR_SHEET_ID" \
    --month 2026-03
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ── Weekly posting schedule ─────────────────────────────────
# Based on research: 60-70% Reels, 20-30% Carousels, 10% Singles
# But for a photographer without video editing workflow yet,
# we weight toward carousels (highest engagement) and singles

WEEKLY_SLOTS = [
    {"day": "Monday",    "platform": "instagram", "type": "carousel",  "pillar": "showcase",    "time": "09:00", "priority": 1},
    {"day": "Monday",    "platform": "linkedin",  "type": "carousel",  "pillar": "showcase",    "time": "08:30", "priority": 1},
    {"day": "Monday",    "platform": "pinterest",  "type": "pins",     "pillar": "showcase",    "time": "12:00", "priority": 2, "count": 5},
    {"day": "Tuesday",   "platform": "instagram", "type": "reel",      "pillar": "bts",         "time": "12:00", "priority": 2},
    {"day": "Tuesday",   "platform": "linkedin",  "type": "text",      "pillar": "educational", "time": "08:30", "priority": 2},
    {"day": "Wednesday", "platform": "pinterest",  "type": "pins",     "pillar": "showcase",    "time": "12:00", "priority": 3, "count": 5},
    {"day": "Thursday",  "platform": "instagram", "type": "carousel",  "pillar": "educational", "time": "09:00", "priority": 1},
    {"day": "Thursday",  "platform": "linkedin",  "type": "carousel",  "pillar": "client",      "time": "08:30", "priority": 2},
    {"day": "Thursday",  "platform": "pinterest",  "type": "pins",     "pillar": "showcase",    "time": "12:00", "priority": 3, "count": 5},
    {"day": "Friday",    "platform": "instagram", "type": "reel",      "pillar": "showcase",    "time": "12:00", "priority": 2},
    {"day": "Friday",    "platform": "linkedin",  "type": "text",      "pillar": "personal",    "time": "08:30", "priority": 3},
    {"day": "Friday",    "platform": "pinterest",  "type": "pins",     "pillar": "showcase",    "time": "12:00", "priority": 3, "count": 5},
    {"day": "Saturday",  "platform": "instagram", "type": "single",    "pillar": "showcase",    "time": "10:00", "priority": 3},
    {"day": "Saturday",  "platform": "pinterest",  "type": "pins",     "pillar": "educational", "time": "12:00", "priority": 3, "count": 3},
]

DAY_ORDER = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}


def get_client():
    """Create Anthropic client."""
    import anthropic
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def run_tool(tool_name, args_list):
    """Run another tool as a subprocess."""
    cmd = [sys.executable, str(PROJECT_ROOT / "tools" / tool_name)] + args_list
    result = subprocess.run(cmd, capture_output=False, text=True, cwd=str(PROJECT_ROOT))
    return result.returncode


# ── INGEST ──────────────────────────────────────────────────


def cmd_ingest(args):
    """Full pipeline: photos → analyzed → cropped → carousels → captions → content plan."""
    project_dir = Path(args.project_dir)
    originals_dir = project_dir / "originals"

    # Check for originals
    if not originals_dir.exists():
        # Maybe images are directly in project_dir
        extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
        images_in_root = [f for f in project_dir.iterdir() if f.suffix.lower() in extensions]
        if images_in_root:
            print(f"Found {len(images_in_root)} images in project root. Moving to originals/...")
            originals_dir.mkdir(exist_ok=True)
            for img in images_in_root:
                img.rename(originals_dir / img.name)
        else:
            print(f"ERROR: No images found in {project_dir} or {originals_dir}")
            return 1

    # Count images
    extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
    image_count = len([f for f in originals_dir.iterdir() if f.suffix.lower() in extensions])
    print(f"{'='*60}")
    print(f"INGESTING: {args.project}")
    print(f"{'='*60}")
    print(f"  Client: {args.client}")
    print(f"  Location: {args.location}")
    print(f"  Architect: {args.architect}")
    print(f"  Images: {image_count}")
    print(f"  Output: {project_dir / 'social'}")

    seo_prefix = args.project.lower().replace(" ", "-").replace("'", "")
    if args.location:
        loc_slug = args.location.lower().split(",")[0].strip().replace(" ", "-")
        seo_prefix = f"{seo_prefix}-{loc_slug}"

    # ── Step 1: Analyze + resize images ──
    print(f"\n{'─'*60}")
    print("STEP 1: Analyzing and processing images")
    print(f"{'─'*60}\n")

    social_dir = project_dir / "social"
    manifest_path = social_dir / "manifest.json"

    if manifest_path.exists() and not args.force:
        print("  Manifest already exists. Skipping image processing (use --force to redo).")
    else:
        ret = run_tool("resize_images.py", [
            "batch",
            "--input-dir", str(originals_dir),
            "--output-dir", str(social_dir),
            "--seo-prefix", seo_prefix,
        ])
        if ret != 0:
            print("ERROR: Image processing failed.")
            return 1

    # ── Step 2: Build carousels ──
    print(f"\n{'─'*60}")
    print("STEP 2: Building carousel sets")
    print(f"{'─'*60}\n")

    carousel_plan_path = social_dir / "carousel-plan.json"
    if carousel_plan_path.exists() and not args.force:
        print("  Carousel plan already exists. Skipping (use --force to redo).")
    else:
        carousel_args = [
            "full",
            "--project-dir", str(project_dir),
            "--project", args.project,
            "--client", args.client,
            "--location", args.location,
        ]
        if args.architect:
            carousel_args.extend(["--architect", args.architect])
        if args.features:
            carousel_args.extend(["--features", args.features])
        if args.trades:
            carousel_args.extend(["--trades", args.trades])

        ret = run_tool("carousel_builder.py", carousel_args)
        if ret != 0:
            print("ERROR: Carousel building failed.")
            return 1

    # ── Step 3: Generate standalone captions ──
    print(f"\n{'─'*60}")
    print("STEP 3: Generating standalone captions (singles, Reels, Pinterest)")
    print(f"{'─'*60}\n")

    captions_dir = project_dir / "captions"
    captions_dir.mkdir(exist_ok=True)
    captions_path = captions_dir / "standalone-captions.json"

    if captions_path.exists() and not args.force:
        print("  Standalone captions already exist. Skipping (use --force to redo).")
    else:
        caption_args = [
            "generate",
            "--project", args.project,
            "--client", args.client,
            "--location", args.location,
        ]
        if args.architect:
            caption_args.extend(["--architect", args.architect])
        if args.features:
            caption_args.extend(["--features", args.features])
        if args.trades:
            caption_args.extend(["--trades", args.trades])
        caption_args.extend(["--output", str(captions_path)])

        ret = run_tool("generate_captions.py", caption_args)
        if ret != 0:
            print("WARNING: Caption generation had issues, but continuing.")

    # ── Step 4: Generate content plan ──
    print(f"\n{'─'*60}")
    print("STEP 4: Generating 4-week content plan")
    print(f"{'─'*60}\n")

    plan = generate_content_plan(project_dir, args)
    plan_path = social_dir / "content-plan.json"
    with open(plan_path, "w") as f:
        json.dump(plan, f, indent=2)

    # ── Summary ──
    print(f"\n{'='*60}")
    print("INGEST COMPLETE")
    print(f"{'='*60}")

    print(f"\nProject: {args.project}")
    print(f"\nOutputs:")
    print(f"  social/manifest.json          — Image analysis ({image_count} images)")
    print(f"  social/instagram/             — IG feed crops")
    print(f"  social/stories/               — Story/Reel crops")
    print(f"  social/linkedin/              — LinkedIn crops")
    print(f"  social/pinterest/             — Pinterest pins")
    print(f"  social/web/                   — Journal images")
    print(f"  social/carousel-plan.json     — Carousel sets with captions")
    print(f"  social/content-plan.json      — 4-week posting calendar")
    print(f"  captions/standalone-captions.json — Singles, Reels, Pinterest captions")

    # Print the content plan summary
    print(f"\n{'─'*60}")
    print("4-WEEK CONTENT PLAN")
    print(f"{'─'*60}")

    for week in plan.get("weeks", []):
        print(f"\n  Week {week['week_number']} ({week['start_date']} to {week['end_date']}):")
        for post in week.get("posts", []):
            status = post.get("status", "draft")
            manual = " [MANUAL]" if post.get("requires_manual", False) else ""
            print(f"    {post['day']:9s} {post['platform']:10s} {post['type']:10s} {post.get('description', '')[:45]}{manual}")

    print(f"\n  Total posts planned: {sum(len(w.get('posts', [])) for w in plan.get('weeks', []))}")

    # What needs manual work
    manual_items = []
    for week in plan.get("weeks", []):
        for post in week.get("posts", []):
            if post.get("requires_manual"):
                manual_items.append(post)

    if manual_items:
        print(f"\n{'─'*60}")
        print(f"REQUIRES YOUR ATTENTION ({len(manual_items)} items)")
        print(f"{'─'*60}")
        for item in manual_items:
            print(f"  - {item['day']} {item['platform']} {item['type']}: {item.get('manual_reason', '')}")

    if args.website:
        print(f"\n  Website link for Pinterest pins: {args.website}")

    print(f"\nNext steps:")
    print(f"  1. Review carousel-plan.json — edit captions to your voice")
    print(f"  2. Review content-plan.json — adjust dates if needed")
    print(f"  3. Check image crops in social/ folders — verify nothing critical is clipped")
    print(f"  4. Approve and schedule (manually or via Postiz)")

    return 0


def generate_content_plan(project_dir, args):
    """Generate a 4-week content plan from processed project data."""
    social_dir = project_dir / "social"

    # Load manifest
    manifest = []
    manifest_path = social_dir / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)

    # Load carousel plan
    carousels = []
    carousel_path = social_dir / "carousel-plan.json"
    if carousel_path.exists():
        with open(carousel_path) as f:
            carousels = json.load(f)

    # Load captions
    captions = {}
    captions_path = project_dir / "captions" / "standalone-captions.json"
    if captions_path.exists():
        with open(captions_path) as f:
            captions = json.load(f)

    # Determine start date
    if args.start_date:
        start = datetime.strptime(args.start_date, "%Y-%m-%d")
    else:
        # Start next Monday
        today = datetime.now()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        start = today + timedelta(days=days_until_monday)

    # Separate carousels by platform
    ig_carousels = [c for c in carousels if c.get("type") in ("project_reveal", "detail_breakdown", "educational", "before_after")]
    li_carousels = [c for c in carousels if c.get("type") == "linkedin_story"]

    # Get hero images for singles
    heroes = sorted(
        [m for m in manifest if m.get("hero_score", 0) >= 7],
        key=lambda x: x.get("hero_score", 0),
        reverse=True
    )

    # Get Pinterest-viable images
    pin_images = [m for m in manifest if m.get("pinterest_viable", False)]

    # Build the 4-week plan
    plan = {
        "project": args.project,
        "client": args.client,
        "location": args.location,
        "architect": getattr(args, "architect", ""),
        "generated_at": datetime.now().isoformat(),
        "website_link": getattr(args, "website", ""),
        "weeks": [],
    }

    ig_carousel_queue = list(ig_carousels)
    li_carousel_queue = list(li_carousels)
    hero_queue = list(heroes)
    pin_queue = list(pin_images)

    caption_data = captions.get("captions", {})

    for week_num in range(1, 5):
        week_start = start + timedelta(weeks=week_num - 1)
        week_end = week_start + timedelta(days=6)

        week = {
            "week_number": week_num,
            "start_date": week_start.strftime("%Y-%m-%d"),
            "end_date": week_end.strftime("%Y-%m-%d"),
            "posts": [],
        }

        for slot in WEEKLY_SLOTS:
            day_offset = DAY_ORDER.get(slot["day"], 0)
            post_date = week_start + timedelta(days=day_offset)

            post = {
                "day": slot["day"],
                "date": post_date.strftime("%Y-%m-%d"),
                "time": slot["time"],
                "platform": slot["platform"],
                "type": slot["type"],
                "pillar": slot["pillar"],
                "priority": slot["priority"],
                "status": "draft",
                "requires_manual": False,
            }

            # Assign content based on type and week
            if slot["type"] == "carousel" and slot["platform"] == "instagram":
                if ig_carousel_queue:
                    cs = ig_carousel_queue.pop(0)
                    post["description"] = cs.get("name", "Project carousel")
                    post["carousel_ref"] = cs.get("type", "")
                    post["image_indices"] = cs.get("image_indices", [])
                    post["caption_source"] = "carousel-plan.json"
                else:
                    post["description"] = f"{args.project} — additional carousel"
                    post["status"] = "needs_content"
                    post["notes"] = "No more carousel sets available. Create from remaining images or use educational angle."

            elif slot["type"] == "carousel" and slot["platform"] == "linkedin":
                if li_carousel_queue:
                    cs = li_carousel_queue.pop(0)
                    post["description"] = cs.get("name", "LinkedIn project story")
                    post["carousel_ref"] = cs.get("type", "")
                    post["caption_source"] = "carousel-plan.json"
                    post["requires_manual"] = True
                    post["manual_reason"] = "LinkedIn document carousels (PDFs) must be uploaded manually — API doesn't support PDF upload"
                elif week_num <= 2:
                    post["description"] = f"{args.project} — LinkedIn project story"
                    post["requires_manual"] = True
                    post["manual_reason"] = "Create PDF carousel in Canva using LinkedIn slides from carousel-plan.json"
                else:
                    post["description"] = "Client spotlight or industry insight"
                    post["pillar"] = "educational"
                    post["caption_source"] = "standalone-captions.json → LinkedIn Industry Insight"

            elif slot["type"] == "single" and slot["platform"] == "instagram":
                if hero_queue:
                    hero = hero_queue.pop(0)
                    post["description"] = f"Detail shot: {hero.get('subject', '')[:40]}"
                    post["image_ref"] = hero.get("seo_name", hero.get("filename", ""))
                    post["caption_source"] = "standalone-captions.json → Instagram Detail/Single"
                else:
                    post["description"] = f"{args.project} detail or throwback"
                    post["status"] = "needs_content"

            elif slot["type"] == "reel":
                post["description"] = f"{args.project} — Reel"
                post["requires_manual"] = True
                if week_num == 1:
                    post["manual_reason"] = "BTS Reel: compile phone footage from shoot day, 15-30 sec, raw over polished"
                    post["caption_source"] = "standalone-captions.json → Instagram Reel"
                elif week_num == 2:
                    post["manual_reason"] = "Process Reel: screen-record retouching timelapse or walkthrough reveal, 15-30 sec"
                elif week_num == 3:
                    post["manual_reason"] = "Before/After Reel: construction progress vs final (if footage available)"
                else:
                    post["manual_reason"] = "Detail Reel: slow pan across key design elements, 15-30 sec"

            elif slot["type"] == "text" and slot["platform"] == "linkedin":
                if slot["pillar"] == "educational":
                    post["description"] = "Industry insight / educational text post"
                    post["caption_source"] = "standalone-captions.json → LinkedIn Industry Insight"
                else:
                    post["description"] = "Personal/brand LinkedIn post"
                    post["requires_manual"] = True
                    post["manual_reason"] = "Personal posts need your authentic voice — use hooks-scripts-library.md Pillar 5"

            elif slot["type"] == "pins":
                count = slot.get("count", 5)
                if pin_queue:
                    batch = pin_queue[:count]
                    pin_queue = pin_queue[count:]
                    post["description"] = f"{len(batch)} Pinterest pins"
                    post["pin_images"] = [p.get("seo_name", p.get("filename", "")) for p in batch]
                    post["caption_source"] = "standalone-captions.json → Pinterest Pin"
                    post["pin_count"] = len(batch)
                else:
                    post["description"] = "Pinterest pins — repin or educational"
                    post["status"] = "needs_content"
                    post["notes"] = "All project pins used. Create educational pins or repin from boards."

            week["posts"].append(post)

        plan["weeks"].append(week)

    # Add summary stats
    total_posts = sum(len(w["posts"]) for w in plan["weeks"])
    manual_count = sum(1 for w in plan["weeks"] for p in w["posts"] if p.get("requires_manual"))
    auto_count = total_posts - manual_count
    needs_content = sum(1 for w in plan["weeks"] for p in w["posts"] if p.get("status") == "needs_content")

    plan["summary"] = {
        "total_posts": total_posts,
        "automated": auto_count,
        "requires_manual": manual_count,
        "needs_content": needs_content,
        "platforms": {
            "instagram": sum(1 for w in plan["weeks"] for p in w["posts"] if p["platform"] == "instagram"),
            "linkedin": sum(1 for w in plan["weeks"] for p in w["posts"] if p["platform"] == "linkedin"),
            "pinterest": sum(1 for w in plan["weeks"] for p in w["posts"] if p["platform"] == "pinterest"),
        }
    }

    return plan


# ── PLAN ────────────────────────────────────────────────────


def cmd_plan(args):
    """Generate a 4-week content calendar from a processed project."""
    project_dir = Path(args.project_dir)

    # Load project metadata from manifest or carousel plan
    social_dir = project_dir / "social"
    meta = {}

    carousel_path = social_dir / "carousel-plan.json"
    if carousel_path.exists():
        with open(carousel_path) as f:
            carousels = json.load(f)

    content_plan_path = social_dir / "content-plan.json"
    if content_plan_path.exists():
        with open(content_plan_path) as f:
            existing = json.load(f)
        meta = {
            "project": existing.get("project", ""),
            "client": existing.get("client", ""),
            "location": existing.get("location", ""),
        }

    # Override with CLI args
    args.project = args.project or meta.get("project", "Unknown")
    args.client = args.client or meta.get("client", "")
    args.location = args.location or meta.get("location", "")
    args.architect = getattr(args, "architect", "")
    args.website = getattr(args, "website", "")

    plan = generate_content_plan(project_dir, args)

    plan_path = social_dir / "content-plan.json"
    with open(plan_path, "w") as f:
        json.dump(plan, f, indent=2)

    print(f"Content plan saved to {plan_path}")
    print(f"\n4-WEEK CONTENT PLAN: {args.project}")
    print(f"{'='*60}")

    for week in plan["weeks"]:
        print(f"\n  Week {week['week_number']} ({week['start_date']} — {week['end_date']}):")
        for post in week["posts"]:
            manual = " [MANUAL]" if post.get("requires_manual") else ""
            flag = " [NEEDS CONTENT]" if post.get("status") == "needs_content" else ""
            print(f"    {post['day']:9s} {post['time']}  {post['platform']:10s} {post['type']:10s} {post.get('description', '')[:40]}{manual}{flag}")

    s = plan["summary"]
    print(f"\n  Summary: {s['total_posts']} posts ({s['automated']} automated, {s['requires_manual']} manual, {s['needs_content']} need content)")
    print(f"  IG: {s['platforms']['instagram']} | LI: {s['platforms']['linkedin']} | Pinterest: {s['platforms']['pinterest']}")

    return 0


# ── BRIEF ───────────────────────────────────────────────────


def cmd_brief(args):
    """Daily briefing: what's scheduled, what needs attention."""
    today = datetime.now().strftime("%Y-%m-%d")
    today_name = datetime.now().strftime("%A")

    print(f"\n{'='*60}")
    print(f"DAILY BRIEF — {today_name}, {today}")
    print(f"{'='*60}")

    # Check for content plans in Photo Assets
    photo_assets = PROJECT_ROOT / "Photo Assets"
    plans_found = []

    if photo_assets.exists():
        for plan_file in photo_assets.rglob("content-plan.json"):
            with open(plan_file) as f:
                plan = json.load(f)
            plans_found.append((plan_file, plan))

    if not plans_found:
        print("\n  No content plans found.")
        print("  Run 'ingest' on a project to generate a content plan.")
        return 0

    # Find today's posts across all plans
    todays_posts = []
    upcoming_posts = []
    overdue_posts = []

    for plan_file, plan in plans_found:
        project = plan.get("project", "Unknown")
        for week in plan.get("weeks", []):
            for post in week.get("posts", []):
                post_date = post.get("date", "")
                post["_project"] = project

                if post_date == today:
                    todays_posts.append(post)
                elif post_date > today and post_date <= (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"):
                    upcoming_posts.append(post)
                elif post_date < today and post.get("status") in ("draft", "needs_content"):
                    overdue_posts.append(post)

    # Today's posts
    print(f"\nTODAY ({len(todays_posts)} posts):")
    if todays_posts:
        for post in sorted(todays_posts, key=lambda x: x.get("time", "")):
            manual = " [MANUAL]" if post.get("requires_manual") else ""
            print(f"  {post['time']}  {post['platform']:10s} {post['type']:10s} {post.get('description', '')[:45]}{manual}")
            if post.get("manual_reason"):
                print(f"          → {post['manual_reason'][:70]}")
    else:
        print("  No posts scheduled for today.")

    # Overdue
    if overdue_posts:
        print(f"\nOVERDUE ({len(overdue_posts)} posts):")
        for post in overdue_posts[:5]:
            print(f"  {post['date']}  {post['platform']:10s} {post['type']:10s} {post.get('description', '')[:45]}")

    # Next 7 days
    print(f"\nNEXT 7 DAYS ({len(upcoming_posts)} posts):")
    by_date = {}
    for post in upcoming_posts:
        d = post.get("date", "")
        by_date.setdefault(d, []).append(post)

    for date_str in sorted(by_date.keys()):
        day_name = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
        posts = by_date[date_str]
        print(f"\n  {day_name} {date_str}:")
        for post in sorted(posts, key=lambda x: x.get("time", "")):
            manual = " [M]" if post.get("requires_manual") else ""
            print(f"    {post['time']}  {post['platform']:10s} {post['type']:10s} {post.get('description', '')[:40]}{manual}")

    # Engagement reminders
    print(f"\n{'─'*60}")
    print("DAILY ENGAGEMENT (10 min)")
    print(f"{'─'*60}")
    print("  [ ] Respond to all comments on recent posts (2 min)")
    print("  [ ] Comment on 3-5 LinkedIn posts from architects/builders (5 min)")
    print("  [ ] Post Instagram Story if you have casual content (2 min)")
    print("  [ ] Send 2-3 LinkedIn connection requests (1 min)")

    return 0


# ── REPORT ──────────────────────────────────────────────────


def cmd_report(args):
    """Monthly performance report with strategy recommendations."""
    client = get_client()

    # Gather all content plans
    photo_assets = PROJECT_ROOT / "Photo Assets"
    all_plans = []

    if photo_assets.exists():
        for plan_file in photo_assets.rglob("content-plan.json"):
            with open(plan_file) as f:
                plan = json.load(f)
            all_plans.append(plan)

    # Gather all carousel plans
    all_carousels = []
    if photo_assets.exists():
        for carousel_file in photo_assets.rglob("carousel-plan.json"):
            with open(carousel_file) as f:
                carousels = json.load(f)
            all_carousels.extend(carousels)

    month = args.month or datetime.now().strftime("%Y-%m")

    print(f"\n{'='*60}")
    print(f"MONTHLY REPORT — {month}")
    print(f"{'='*60}")

    # Content production summary
    total_planned = 0
    by_platform = {"instagram": 0, "linkedin": 0, "pinterest": 0}
    by_type = {}
    manual_items = 0

    for plan in all_plans:
        for week in plan.get("weeks", []):
            for post in week.get("posts", []):
                if post.get("date", "").startswith(month):
                    total_planned += 1
                    by_platform[post["platform"]] = by_platform.get(post["platform"], 0) + 1
                    by_type[post["type"]] = by_type.get(post["type"], 0) + 1
                    if post.get("requires_manual"):
                        manual_items += 1

    print(f"\nCONTENT PRODUCTION:")
    print(f"  Total posts planned: {total_planned}")
    print(f"  By platform: {', '.join(f'{k}: {v}' for k, v in by_platform.items())}")
    print(f"  By type: {', '.join(f'{k}: {v}' for k, v in by_type.items())}")
    print(f"  Manual items: {manual_items}")

    # Projects processed
    projects = set(p.get("project", "") for p in all_plans if p.get("project"))
    print(f"\n  Projects in pipeline: {', '.join(projects) if projects else 'None'}")

    # Carousel summary
    if all_carousels:
        print(f"\nCAROUSEL SETS CREATED: {len(all_carousels)}")
        for cs in all_carousels:
            print(f"  - {cs.get('name', 'Untitled')} ({len(cs.get('image_indices', []))} slides)")

    # Strategy recommendations (use Claude to analyze)
    print(f"\n{'─'*60}")
    print("STRATEGY RECOMMENDATIONS")
    print(f"{'─'*60}")

    prompt = f"""Based on this social media pipeline status for an architectural photographer:

- Month: {month}
- Posts planned: {total_planned}
- Platform breakdown: {json.dumps(by_platform)}
- Content type breakdown: {json.dumps(by_type)}
- Projects in pipeline: {', '.join(projects) if projects else 'None'}
- Carousel sets: {len(all_carousels)}
- Manual items pending: {manual_items}

Target cadence: Instagram 4-5/week, LinkedIn 3-4/week, Pinterest 20-30 pins/week.
Algorithm priority: Saves (25%), DM shares (20%), meaningful comments (15%).
Best performing formats: Carousels (3.1x engagement), Reels (2.5x reach).

Give 3-5 specific, actionable recommendations for this month. Focus on:
1. Content gaps or imbalances
2. Engagement optimization
3. What to double down on
4. What to add or change

Be concise. One paragraph per recommendation. No generic advice."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    print(f"\n{response.content[0].text}")

    return 0


# ── CLI ─────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Social media manager — central engine for content pipeline"
    )
    sub = parser.add_subparsers(dest="command")

    # --- ingest ---
    ing = sub.add_parser("ingest", help="Full pipeline: photos → content plan")
    ing.add_argument("--project-dir", required=True, help="Project directory with originals/")
    ing.add_argument("--project", required=True, help="Project name")
    ing.add_argument("--client", default="", help="Client/builder name")
    ing.add_argument("--location", default="", help="Project location")
    ing.add_argument("--architect", default="", help="Architect/designer")
    ing.add_argument("--features", default="", help="Standout design features")
    ing.add_argument("--trades", default="", help="Trades to tag (IG handles)")
    ing.add_argument("--website", default="", help="Project page URL on mattanthonyphoto.com")
    ing.add_argument("--start-date", help="Content plan start date (YYYY-MM-DD, default: next Monday)")
    ing.add_argument("--force", action="store_true", help="Reprocess even if outputs exist")

    # --- plan ---
    pln = sub.add_parser("plan", help="Generate 4-week content calendar")
    pln.add_argument("--project-dir", required=True, help="Project directory")
    pln.add_argument("--project", default="", help="Project name")
    pln.add_argument("--client", default="", help="Client/builder")
    pln.add_argument("--location", default="", help="Location")
    pln.add_argument("--start-date", help="Start date (YYYY-MM-DD)")

    # --- brief ---
    brf = sub.add_parser("brief", help="Daily briefing")
    brf.add_argument("--sheet-id", default="", help="Google Sheet ID (optional)")

    # --- report ---
    rpt = sub.add_parser("report", help="Monthly performance report")
    rpt.add_argument("--sheet-id", default="", help="Google Sheet ID (optional)")
    rpt.add_argument("--month", default="", help="Month to report (YYYY-MM, default: current)")

    args = parser.parse_args()

    if args.command == "ingest":
        return cmd_ingest(args)
    elif args.command == "plan":
        return cmd_plan(args)
    elif args.command == "brief":
        return cmd_brief(args)
    elif args.command == "report":
        return cmd_report(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
