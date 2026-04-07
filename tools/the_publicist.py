#!/usr/bin/env python3
"""The Publicist — Social media agent that plans, approves, and publishes content
for Matt Anthony Photography and client accounts.

Modes:
  plan      Build next week's content calendar in Notion for all accounts
  publish   Read today's approved posts from Notion → upload images → schedule via Late/Postiz
  rotate    Update project rotation state
  notify    Send Telegram summary linking to Notion calendar for review
  report    Weekly analytics — sync Late.dev data to Notion + Telegram summary
  status    Quick queue status across all accounts

Usage:
  python3 tools/the_publicist.py plan
  python3 tools/the_publicist.py publish
  python3 tools/the_publicist.py status
"""
import sys, os, json, re, subprocess
from datetime import datetime, timedelta, date
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from agent_utils import send_telegram, get_google_creds, logger
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

# === CONFIG ===
TOOLS_DIR = Path(__file__).resolve().parent
ACCOUNTS_FILE = TOOLS_DIR / "social_accounts.json"
PLAYBOOKS_DIR = TOOLS_DIR / "playbooks"
ROTATION_FILE = TOOLS_DIR / ".social_rotation_state.json"

NOTION_CONTENT_DB_DATA_SOURCE = "collection://0603363c-f282-47a0-a416-430d3158acdf"
NOTION_CONTENT_DB_ID = "cdd1e6d67f5944ee8a935dfee9360dcb"

LATE_API_KEY = os.getenv("LATE_API_KEY")
LATE_API_BASE = "https://getlate.dev/api/v1"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Image hosting fallback
FREEIMAGE_API_KEY = "6d207e02198a847aa98d0a2a901485a5"

# Queue file for Notion posts (used when no Notion API key)
NOTION_QUEUE_FILE = TOOLS_DIR / ".publicist_notion_queue.json"

import requests


# ── Helpers ─────────────────────────────────────────────

def load_accounts():
    """Load social_accounts.json."""
    with open(ACCOUNTS_FILE) as f:
        return json.load(f)


def load_playbook(account_slug):
    """Load a playbook JSON for an account."""
    path = PLAYBOOKS_DIR / f"{account_slug}.json"
    if not path.exists():
        logger.warning(f"No playbook found for {account_slug}")
        return None
    with open(path) as f:
        return json.load(f)


def load_rotation_state():
    """Load or initialize project rotation state."""
    if ROTATION_FILE.exists():
        with open(ROTATION_FILE) as f:
            return json.load(f)
    return {}


def save_rotation_state(state):
    """Save project rotation state."""
    with open(ROTATION_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_today():
    """Get today's date string."""
    return date.today().isoformat()


def get_week_dates(start_offset_days=0):
    """Get Mon-Sat dates for next week (or offset)."""
    today = date.today()
    # Find next Monday
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    monday = today + timedelta(days=days_until_monday + start_offset_days)
    return [(monday + timedelta(days=i)) for i in range(6)]  # Mon-Sat


def upload_image_to_host(image_path):
    """Upload an image to freeimage.host and return the public URL."""
    try:
        with open(image_path, "rb") as f:
            resp = requests.post(
                "https://freeimage.host/api/1/upload",
                data={"type": "file", "action": "upload", "key": FREEIMAGE_API_KEY},
                files={"source": f},
                timeout=30
            )
        data = resp.json()
        url = data.get("image", {}).get("url")
        if url:
            logger.info(f"Uploaded {Path(image_path).name} → {url}")
            return url
        logger.error(f"Upload failed for {image_path}: {data}")
        return None
    except Exception as e:
        logger.error(f"Upload error for {image_path}: {e}")
        return None


def late_create_post(platform, account_id, content, media_items, scheduled_for):
    """Create a post via Late API. Supports all platforms."""
    if not LATE_API_KEY:
        logger.error("LATE_API_KEY not set")
        return None

    # Map platform names to Late's expected values
    platform_map = {
        "Instagram": "instagram",
        "LinkedIn": "linkedin",
        "Pinterest": "pinterest",
        "Facebook": "facebook",
        "GMB": "googlebusiness",
        "Reddit": "reddit",
    }
    late_platform = platform_map.get(platform, platform.lower())

    payload = {
        "content": content,
        "platforms": [{"platform": late_platform, "accountId": account_id}],
        "scheduledFor": scheduled_for
    }

    # Only include media if we have items (LinkedIn text posts don't need images)
    if media_items:
        payload["mediaItems"] = media_items

    try:
        resp = requests.post(
            f"{LATE_API_BASE}/posts",
            headers={
                "Authorization": f"Bearer {LATE_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        data = resp.json()
        if "post" in data:
            post_id = data["post"]["_id"]
            logger.info(f"Late post created ({late_platform}): {post_id}")
            return post_id
        logger.error(f"Late post failed ({late_platform}): {data}")
        return None
    except Exception as e:
        logger.error(f"Late API error: {e}")
        return None


def pick_hero_image(project_path):
    """Pick the best hero image from a project folder.
    Priority: twilight exterior > blue hour > exterior > first landscape image.
    """
    if not project_path or not os.path.isdir(project_path):
        return None

    images = sorted([f for f in os.listdir(project_path) if f.endswith(".jpg")])
    if not images:
        return None

    # Priority search
    for keyword in ["twilight", "blue-hour", "exterior-front"]:
        match = next((img for img in images if keyword in img), None)
        if match:
            return os.path.join(project_path, match)

    # Fallback: any exterior
    match = next((img for img in images if "exterior" in img), None)
    if match:
        return os.path.join(project_path, match)

    # Fallback: first wide shot (likely landscape)
    for img in images:
        if any(kw in img for kw in ["living", "kitchen", "dining", "aerial"]):
            return os.path.join(project_path, img)

    # Last resort: first image
    return os.path.join(project_path, images[0])


def curate_carousel_images(project_path, playbook, exclude_images=None, count=10):
    """Use filename analysis + carousel framework to curate a storytelling sequence.

    The carousel framework defines roles: Hook → Authority → Variety → Lifestyle → Detail → Closer.
    We match images to roles using filename keywords (SEO-named files contain room, feature, mood).

    Returns list of filenames in story order.
    """
    if not project_path or not os.path.isdir(project_path):
        return []

    all_images = sorted([f for f in os.listdir(project_path) if f.endswith(".jpg")])
    if not all_images:
        return []

    exclude = set(exclude_images or [])
    available = [img for img in all_images if img not in exclude]
    if len(available) < count:
        available = all_images  # Not enough unused, use full library

    # Categorize images by filename keywords
    categories = {
        "exterior_twilight": [],
        "exterior_day": [],
        "aerial": [],
        "kitchen": [],
        "living": [],
        "dining": [],
        "bedroom": [],
        "bathroom": [],
        "detail": [],
        "lifestyle": [],
        "other": [],
    }

    for img in available:
        name = img.lower()
        if ("twilight" in name or "blue-hour" in name or "warm-glow" in name) and "exterior" in name:
            categories["exterior_twilight"].append(img)
        elif "aerial" in name or "drone" in name:
            categories["aerial"].append(img)
        elif "exterior" in name:
            categories["exterior_day"].append(img)
        elif "kitchen" in name or "island" in name or "range" in name:
            categories["kitchen"].append(img)
        elif "living" in name or "fireplace" in name or "lounge" in name:
            categories["living"].append(img)
        elif "dining" in name:
            categories["dining"].append(img)
        elif "bedroom" in name or "master" in name or "guest-bed" in name:
            categories["bedroom"].append(img)
        elif "bathroom" in name or "ensuite" in name or "vanity" in name or "tub" in name or "shower" in name or "powder" in name:
            categories["bathroom"].append(img)
        elif any(kw in name for kw in ["detail", "hardware", "texture", "millwork", "bracket", "beam", "timber", "stone-", "tile", "fixture", "sauna", "closet", "pantry", "mudroom", "staircase"]):
            categories["detail"].append(img)
        elif any(kw in name for kw in ["hot-tub", "deck", "patio", "outdoor", "dock", "pool", "fire-pit"]):
            categories["lifestyle"].append(img)
        else:
            categories["other"].append(img)

    # Build carousel sequence following the framework
    # 1: Hook — twilight exterior (scroll-stop)
    # 2: Authority — hero interior (kitchen or living, shows lighting skill)
    # 3: Authority — second strong interior (different room)
    # 4: Variety — wide/spatial (dining or living with view)
    # 5: Variety — unexpected (bedroom, bathroom, or unique element)
    # 6: Variety — editorial/tight (detail or other interior)
    # 7: Lifestyle — aspirational (outdoor living, hot tub, deck)
    # 8: Lifestyle — second lifestyle or warm interior
    # 9: Detail — craft shot (millwork, material, hardware)
    # 10: Closer — aerial or second exterior (bookend)

    def pick(category_list, fallback_lists=None):
        """Pick and remove one image from category, with fallbacks."""
        if category_list:
            return category_list.pop(0)
        if fallback_lists:
            for fb in fallback_lists:
                if fb:
                    return fb.pop(0)
        return None

    sequence = []

    # Slide 1: Hook — twilight exterior
    s1 = pick(categories["exterior_twilight"], [categories["exterior_day"]])
    if s1: sequence.append(s1)

    # Slide 2: Authority — kitchen (hero interior)
    s2 = pick(categories["kitchen"], [categories["living"]])
    if s2: sequence.append(s2)

    # Slide 3: Authority — living room or different interior
    s3 = pick(categories["living"], [categories["dining"], categories["kitchen"]])
    if s3: sequence.append(s3)

    # Slide 4: Variety — dining or wide spatial
    s4 = pick(categories["dining"], [categories["living"], categories["kitchen"]])
    if s4: sequence.append(s4)

    # Slide 5: Variety — bedroom or bathroom (unexpected)
    s5 = pick(categories["bedroom"], [categories["bathroom"]])
    if s5: sequence.append(s5)

    # Slide 6: Variety — bathroom or other
    s6 = pick(categories["bathroom"], [categories["bedroom"], categories["other"]])
    if s6: sequence.append(s6)

    # Slide 7: Lifestyle — outdoor/deck/hot tub
    s7 = pick(categories["lifestyle"], [categories["exterior_day"], categories["other"]])
    if s7: sequence.append(s7)

    # Slide 8: Lifestyle — second lifestyle or warm interior
    s8 = pick(categories["lifestyle"], [categories["living"], categories["bedroom"], categories["other"]])
    if s8: sequence.append(s8)

    # Slide 9: Detail — craft/material shot
    s9 = pick(categories["detail"], [categories["other"], categories["bathroom"]])
    if s9: sequence.append(s9)

    # Slide 10: Closer — aerial or second exterior
    s10 = pick(categories["aerial"], [categories["exterior_day"], categories["exterior_twilight"]])
    if s10: sequence.append(s10)

    # Fill remaining slots if we're short
    remaining = []
    for cat_list in categories.values():
        remaining.extend(cat_list)
    while len(sequence) < count and remaining:
        img = remaining.pop(0)
        if img not in sequence:
            sequence.append(img)

    logger.info(f"  Carousel curated: {len(sequence)} slides")
    for i, img in enumerate(sequence):
        roles = ["Hook", "Authority", "Authority", "Variety", "Variety", "Variety", "Lifestyle", "Lifestyle", "Detail", "Closer"]
        role = roles[i] if i < len(roles) else "Extra"
        logger.info(f"    {i+1}. [{role}] {img}")

    return sequence[:count]


def notion_update_page_content(page_id, image_urls, caption, hashtags, post_type, project_name):
    """Update a Notion page's body with images, caption, and hashtags.

    image_urls: single URL string (hero) or list of URLs (carousel).
    """
    if not NOTION_API_KEY:
        return

    if isinstance(image_urls, str):
        image_urls = [image_urls] if image_urls else []

    # Build page content blocks
    children = []

    # Images — show all for carousels, single for others
    for i, url in enumerate(image_urls):
        if not url:
            continue
        label = f"{project_name} — Slide {i+1}" if len(image_urls) > 1 else project_name
        children.append({
            "object": "block",
            "type": "image",
            "image": {
                "type": "external",
                "external": {"url": url},
                "caption": [{"type": "text", "text": {"content": label}}]
            }
        })

    # Divider
    children.append({"object": "block", "type": "divider", "divider": {}})

    # Caption heading
    children.append({
        "object": "block", "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Caption"}}]}
    })

    # Caption as quote
    if caption:
        children.append({
            "object": "block", "type": "quote",
            "quote": {"rich_text": [{"type": "text", "text": {"content": caption[:2000]}}]}
        })

    # Divider
    children.append({"object": "block", "type": "divider", "divider": {}})

    # Hashtags
    if hashtags:
        children.append({
            "object": "block", "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": "Hashtags"}}]}
        })
        children.append({
            "object": "block", "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": hashtags[:2000]}}],
                "language": "plain text"
            }
        })

    try:
        resp = requests.patch(
            f"{NOTION_API_BASE}/blocks/{page_id}/children",
            headers=notion_headers(),
            json={"children": children},
            timeout=30
        )
        if resp.status_code == 200:
            logger.info(f"Notion page content updated: {page_id} ({len(image_urls)} images)")
        else:
            logger.warning(f"Notion content update failed ({resp.status_code}): {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"Notion content update error: {e}")


def call_tool(script_name, *args):
    """Call another tool script via subprocess."""
    script = TOOLS_DIR / script_name
    cmd = [sys.executable, str(script)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        logger.warning(f"{script_name} failed: {result.stderr[:200]}")
    return result


def generate_caption_for_post(project_data, platform, post_type, pillar, hook, playbook, projects_dir, specific_images=None):
    """Generate a real caption using Claude Vision via generate_captions.py internals.

    Returns the caption string or a placeholder if generation fails.
    """
    if not ANTHROPIC_API_KEY:
        logger.warning("No ANTHROPIC_API_KEY — using placeholder caption")
        return None

    try:
        from generate_captions import get_client, generate_caption, encode_image_b64, BRAND_VOICE, PLATFORM_RULES

        # Map post types to generate_captions content types
        type_map = {
            "Carousel": "carousel",
            "Single": "single",
            "Reel": "reel",
            "Text": "insight",
            "Pins": "pin",
            "Pin": "pin",
        }
        content_type = type_map.get(post_type, "carousel")

        # Map platform names
        platform_lower = platform.lower()
        if platform_lower == "linkedin":
            # Pick linkedin content type based on pillar
            pillar_to_li = {
                "Project Showcase": "project",
                "Client Spotlight": "client",
                "Educational": "insight",
                "Personal / Brand": "insight",
            }
            content_type = pillar_to_li.get(pillar, "project")

        # Check if platform/type combo exists in rules
        if platform_lower not in PLATFORM_RULES or content_type not in PLATFORM_RULES.get(platform_lower, {}):
            # Try fallback types
            if platform_lower == "instagram" and pillar == "Process & BTS":
                content_type = "behindthescenes"
            elif platform_lower == "instagram" and pillar == "Educational":
                content_type = "educational"
            else:
                content_type = list(PLATFORM_RULES.get(platform_lower, {}).keys())[0] if PLATFORM_RULES.get(platform_lower) else "carousel"

        # Build project context
        project_name = project_data.get("name", "Unknown")
        client_name = project_data.get("client", "")
        location = project_data.get("location", "")
        features = ", ".join(project_data.get("features", []))
        client_handle = project_data.get("client_handle", "")

        # Get brand voice from playbook if available
        voice = playbook.get("brand_voice", {})
        voice_override = f"""
Brand voice: {voice.get('tone', 'Professional but warm.')}
Perspective: {voice.get('perspective', 'First person singular.')}
Words to USE: {', '.join(voice.get('vocabulary', {}).get('use', []))}
Words to AVOID: {', '.join(voice.get('vocabulary', {}).get('avoid', []))}
"""

        project_context = f"""Project: {project_name}
Client/Builder: {client_name}
Location: {location}
Standout features: {features}
Notable trades to tag: {client_handle}
"""
        if hook:
            project_context += f"Suggested hook (use this or a variation): {hook}\n"

        # Load images for Vision — use specific carousel images if provided
        hero_images = []
        if project_data.get("path"):
            proj_path = os.path.join(projects_dir, project_data["path"])
            if os.path.isdir(proj_path):
                if specific_images:
                    # Send first, middle, last + any detail shot for full context
                    sample_indices = [0]
                    if len(specific_images) > 4:
                        sample_indices.append(len(specific_images) // 2)
                    if len(specific_images) > 1:
                        sample_indices.append(len(specific_images) - 1)
                    for i, img in enumerate(specific_images):
                        if any(kw in img.lower() for kw in ["detail", "texture", "hardware", "millwork", "vanity", "staircase"]) and i not in sample_indices:
                            sample_indices.append(i)
                            break
                    for idx in sorted(set(sample_indices)):
                        if idx < len(specific_images):
                            full_path = os.path.join(proj_path, specific_images[idx])
                            if os.path.exists(full_path):
                                hero_images.append({"path": Path(full_path), "subject": "", "category": "", "hero_score": 0})
                else:
                    # Default: pick 2-3 hero images
                    images = sorted([f for f in os.listdir(proj_path) if f.endswith(".jpg")])
                    hero_candidates = []
                    for kw in ["twilight", "exterior-front", "kitchen", "living", "dining"]:
                        match = next((img for img in images if kw in img), None)
                        if match and match not in hero_candidates:
                            hero_candidates.append(match)
                        if len(hero_candidates) >= 3:
                            break
                    if not hero_candidates and images:
                        hero_candidates = images[:3]
                    for img_name in hero_candidates:
                        full_path = os.path.join(proj_path, img_name)
                        hero_images.append({"path": Path(full_path), "subject": "", "category": "", "hero_score": 0})

        # Generate caption
        client_api = get_client()
        caption = generate_caption(
            client_api,
            project_context,
            platform_lower,
            content_type,
            hero_images=hero_images if hero_images else None
        )

        if caption:
            logger.info(f"Caption generated ({len(caption)} chars) for {project_name} {platform}")
            return caption
        return None

    except Exception as e:
        logger.warning(f"Caption generation failed: {e}")
        return None


def notion_headers():
    """Get Notion API headers."""
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }


def notion_create_page(properties):
    """Create a page in the Content Calendar Notion database.

    If NOTION_API_KEY is set, creates directly via API.
    Otherwise, queues to JSON file for later push via Claude Code MCP.
    """
    if not NOTION_API_KEY:
        # Queue for later push
        queue = []
        if NOTION_QUEUE_FILE.exists():
            with open(NOTION_QUEUE_FILE) as f:
                queue = json.load(f)
        queue.append(properties)
        with open(NOTION_QUEUE_FILE, "w") as f:
            json.dump(queue, f, indent=2)
        return "queued"

    # Build Notion API page creation payload
    notion_props = {}

    for key, value in properties.items():
        if not value:
            continue
        if key == "Post":
            notion_props["Post"] = {"title": [{"text": {"content": str(value)}}]}
        elif key.startswith("date:"):
            # Handle date properties — extract field name
            parts = key.split(":")
            field_name = parts[1]
            sub_field = parts[2]  # start, end, is_datetime
            if field_name not in notion_props:
                notion_props[field_name] = {"date": {"start": None}}
            if sub_field == "start":
                notion_props[field_name]["date"]["start"] = value
            elif sub_field == "end" and value:
                notion_props[field_name]["date"]["end"] = value
        elif key in ("Status", "Platform", "Post Type", "Pillar", "Funnel Stage", "Account", "Engagement Prediction", "Quality Score"):
            notion_props[key] = {"select": {"name": str(value)}}
        else:
            # Rich text fields
            notion_props[key] = {"rich_text": [{"text": {"content": str(value)[:2000]}}]}

    payload = {
        "parent": {"database_id": NOTION_CONTENT_DB_ID},
        "properties": notion_props
    }

    try:
        resp = requests.post(
            f"{NOTION_API_BASE}/pages",
            headers=notion_headers(),
            json=payload,
            timeout=15
        )
        if resp.status_code == 200:
            page_id = resp.json().get("id", "")
            logger.info(f"Notion page created: {page_id}")
            return page_id
        else:
            logger.error(f"Notion create failed ({resp.status_code}): {resp.text[:200]}")
            # Fall back to queue
            queue = []
            if NOTION_QUEUE_FILE.exists():
                with open(NOTION_QUEUE_FILE) as f:
                    queue = json.load(f)
            queue.append(properties)
            with open(NOTION_QUEUE_FILE, "w") as f:
                json.dump(queue, f, indent=2)
            return "queued"
    except Exception as e:
        logger.error(f"Notion API error: {e}")
        return None


def notion_query_approved_today():
    """Query Notion for posts with Status=Approved and Scheduled Date=today."""
    if not NOTION_API_KEY:
        logger.warning("No NOTION_API_KEY — cannot query Notion directly. Use Claude Code MCP.")
        return []

    today = get_today()
    # Query all approved posts (scheduled for today or any date)
    # The agent publishes whatever is approved — the scheduled date
    # is used for the Late/Postiz scheduling time, not as a gate.
    payload = {
        "filter": {
            "property": "Status", "select": {"equals": "Approved"}
        }
    }

    try:
        resp = requests.post(
            f"{NOTION_API_BASE}/databases/{NOTION_CONTENT_DB_ID}/query",
            headers=notion_headers(),
            json=payload,
            timeout=15
        )
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            logger.info(f"Found {len(results)} approved posts for {today}")
            return results
        else:
            logger.error(f"Notion query failed ({resp.status_code}): {resp.text[:200]}")
            return []
    except Exception as e:
        logger.error(f"Notion query error: {e}")
        return []


def notion_update_status(page_id, status, post_id=None, published_url=None):
    """Update a Notion page's status and optionally set Post ID and Published URL."""
    if not NOTION_API_KEY:
        return

    props = {}
    if status:
        props["Status"] = {"select": {"name": status}}
    if post_id:
        props["Post ID"] = {"rich_text": [{"text": {"content": post_id}}]}
    if published_url:
        props["Published URL"] = {"rich_text": [{"text": {"content": published_url}}]}

    try:
        resp = requests.patch(
            f"{NOTION_API_BASE}/pages/{page_id}",
            headers=notion_headers(),
            json={"properties": props},
            timeout=15
        )
        if resp.status_code == 200:
            logger.info(f"Notion page {page_id} → {status}")
        else:
            logger.error(f"Notion update failed: {resp.text[:200]}")
    except Exception as e:
        logger.error(f"Notion update error: {e}")


# ── MODE: STATUS ────────────────────────────────────────

def mode_status():
    """Show quick queue status across all accounts."""
    accounts = load_accounts()
    lines = ["<b>📋 The Publicist — Queue Status</b>", ""]

    # Count posts by status (would query Notion in full implementation)
    for slug, acct in accounts.items():
        playbook = load_playbook(slug)
        if not playbook:
            lines.append(f"<b>{acct['label']}</b>: No playbook")
            continue

        platforms = list(acct.get("platforms", {}).keys())
        lines.append(f"<b>{acct['label']}</b>")
        lines.append(f"  Platforms: {', '.join(platforms)}")

        # Check rotation state
        rotation = load_rotation_state()
        acct_rotation = rotation.get(slug, {})
        if acct_rotation.get("last_posted"):
            last_project = list(acct_rotation["last_posted"].keys())[-1] if acct_rotation["last_posted"] else "none"
            lines.append(f"  Last posted project: {last_project}")
        else:
            lines.append(f"  No posts yet")

        # Check photo assets
        projects_dir = acct.get("projects_dir", "")
        if projects_dir and Path(projects_dir).exists():
            project_count = sum(1 for p in Path(projects_dir).iterdir() if p.is_dir())
            lines.append(f"  Photo projects available: {project_count}")

        lines.append("")

    lines.append(f"📅 Today: {get_today()}")
    lines.append(f"🔗 Notion Calendar: https://notion.so/{NOTION_CONTENT_DB_ID}")

    msg = "\n".join(lines)
    print(msg)
    send_telegram(msg)


# ── MODE: ROTATE ────────────────────────────────────────

def mode_rotate():
    """Update project rotation state — scan Photo Assets, track what's been posted."""
    accounts = load_accounts()
    state = load_rotation_state()

    for slug, acct in accounts.items():
        playbook = load_playbook(slug)
        if not playbook:
            continue

        projects_dir = acct.get("projects_dir", "")
        if not projects_dir or not Path(projects_dir).exists():
            continue

        # Initialize account state if needed
        if slug not in state:
            state[slug] = {"last_posted": {}, "post_counts": {}, "queue_position": 0}

        # Scan available projects from playbook
        available_projects = []
        for proj in playbook.get("projects", []):
            if proj.get("photo_count", 0) > 0 and proj.get("status") != "no_assets":
                available_projects.append(proj["slug"])

        # Sort by: least posted first, then least recently posted
        counts = state[slug].get("post_counts", {})
        last_posted = state[slug].get("last_posted", {})

        def sort_key(slug):
            count = counts.get(slug, 0)
            last = last_posted.get(slug, "2000-01-01")
            return (count, last)

        available_projects.sort(key=sort_key)

        # Week-over-week variety check — if the last week's first project
        # is the same as this week's first, rotate forward
        last_week_first = state[slug].get("last_week_first_project")
        if available_projects and last_week_first == available_projects[0] and len(available_projects) > 1:
            available_projects.append(available_projects.pop(0))
            logger.info(f"  Variety check: rotated {last_week_first} to avoid week-over-week repeat")

        state[slug]["project_queue"] = available_projects

        logger.info(f"{acct['label']}: {len(available_projects)} projects in rotation queue")
        logger.info(f"  Queue order: {', '.join(available_projects)}")

    save_rotation_state(state)
    print(f"Rotation state updated for {len(accounts)} accounts")
    send_telegram(f"🔄 <b>Rotation Updated</b>\n{len(accounts)} accounts refreshed")


# ── MODE: PLAN ──────────────────────────────────────────

def mode_plan():
    """Build next week's content calendar in Notion for all accounts."""
    accounts = load_accounts()
    state = load_rotation_state()
    week_dates = get_week_dates()
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    total_posts = 0

    for slug, acct in accounts.items():
        playbook = load_playbook(slug)
        if not playbook:
            continue

        # Skip accounts with no connected platforms
        has_connected = any(
            p.get("account_id") or p.get("integration_id")
            for p in acct.get("platforms", {}).values()
        )
        if not has_connected and acct["type"] == "client":
            logger.info(f"Skipping {acct['label']} — no connected platforms")
            continue

        schedule = playbook.get("weekly_schedule", [])
        if not schedule:
            continue

        # Get project queue
        acct_state = state.get(slug, {})
        project_queue = acct_state.get("project_queue", [])
        if not project_queue:
            logger.warning(f"{acct['label']}: No projects in rotation queue. Run 'rotate' first.")
            continue

        queue_pos = acct_state.get("queue_position", 0)
        projects_data = {p["slug"]: p for p in playbook.get("projects", []) if p.get("photo_count", 0) > 0}

        # Build posts for each scheduled slot
        for slot in schedule:
            day_name = slot["day"]
            if day_name not in day_names:
                continue

            day_idx = day_names.index(day_name)
            post_date = week_dates[day_idx]

            # Pick project from queue (round-robin)
            project_slug = project_queue[queue_pos % len(project_queue)]
            project_data = projects_data.get(project_slug, {})

            # Determine post title
            project_name = project_data.get("name", project_slug.replace("-", " ").title())
            platform = slot["platform"].title()
            post_type = slot["type"].title()
            pillar = slot.get("pillar", "Showcase")

            title = f"{project_name} — {platform} {post_type}"

            # Select hook from playbook
            hook = ""
            hook_key = f"{pillar.lower().replace(' & ', '_').replace(' ', '_')}_ig"
            hooks = playbook.get("hook_library", {}).get(hook_key, [])
            if hooks:
                hook_idx = (queue_pos + day_idx) % len(hooks)
                hook = hooks[hook_idx]

            # Get collaborator tags
            collaborators = project_data.get("client_handle", "")

            # Get hashtag set
            hashtag_rotation = playbook.get("hashtag_rotation", {})
            pillar_key = pillar.lower().replace(" & ", "_").replace(" ", "_")
            if pillar_key == "project_showcase":
                pillar_key = "project_reveal"
            sets = hashtag_rotation.get(pillar_key, {})
            hashtag_set = sets.get("set_a", "") if (queue_pos % 2 == 0) else sets.get("set_b", "")

            # ── STEP 1: Curate images FIRST so caption sees what it's writing about ──
            image_paths = ""
            if project_data.get("path"):
                base_dir = acct.get("projects_dir", "")
                full_path = os.path.join(base_dir, project_data["path"])
                if os.path.isdir(full_path):
                    if slot["type"] == "carousel":
                        # Use carousel framework to curate storytelling sequence
                        curated = curate_carousel_images(full_path, playbook)
                        image_paths = ", ".join(curated)
                    elif slot["type"] == "pins":
                        count = slot.get("count", 5)
                        images = sorted([f for f in os.listdir(full_path) if f.endswith(".jpg")])
                        image_paths = ", ".join(images[:count])
                    else:
                        # Single — pick a hero shot
                        hero = pick_hero_image(full_path)
                        image_paths = os.path.basename(hero) if hero else ""

            # ── STEP 2: Generate caption USING the selected images via Vision ──
            selected_images = [i.strip() for i in image_paths.split(",") if i.strip()] if image_paths else None
            caption = generate_caption_for_post(
                project_data, platform, post_type, pillar, hook,
                playbook, acct.get("projects_dir", ""),
                specific_images=selected_images
            )
            if not caption:
                # Fallback to placeholder if generation fails
                caption = f"{hook}\n\n[Caption to be generated for {project_name} — {pillar} angle on {platform}]" if hook else f"[Caption to be generated for {project_name} — {pillar} angle on {platform}]"

            # Determine funnel stage
            funnel_map = {
                "Project Showcase": "Awareness",
                "Process & BTS": "Trust",
                "Client Spotlight": "Trust",
                "Educational": "Consideration",
                "Personal / Brand": "Trust",
                "Detail & Material": "Awareness",
                "Awards & Press": "Trust"
            }
            funnel_stage = funnel_map.get(pillar, "Awareness")

            # Map pillar to Notion option
            pillar_notion_map = {
                "Project Showcase": "Showcase",
                "Process & BTS": "BTS",
                "Client Spotlight": "Client Spotlight",
                "Educational": "Educational",
                "Personal / Brand": "Personal",
                "Detail & Material": "Detail",
                "Awards & Press": "Awards"
            }
            pillar_notion = pillar_notion_map.get(pillar, "Showcase")

            # Account label for Notion
            account_notion_map = {
                "matt-anthony": "Matt Anthony",
                "lrd-studio": "LRD Studio",
                "balmoral": "Balmoral"
            }
            account_notion = account_notion_map.get(slug, acct["label"])

            # Predict engagement type based on content
            engagement_map = {
                ("carousel", "Project Showcase"): "High Save",
                ("carousel", "Educational"): "Share-Worthy",
                ("carousel", "Client Spotlight"): "Share-Worthy",
                ("reel", "Project Showcase"): "Share-Worthy",
                ("reel", "Process & BTS"): "High Save",
                ("single", "Project Showcase"): "Standard",
                ("text", "Educational"): "Conversation Starter",
                ("text", "Personal / Brand"): "Conversation Starter",
                ("pins", "Project Showcase"): "Standard",
            }
            engagement_pred = engagement_map.get(
                (slot["type"], pillar),
                "Standard"
            )

            # Quality score — check caption against voice rules
            quality = "Publish Ready"
            if caption and "[Caption to be generated" in caption:
                quality = "Needs Edit"
            elif caption:
                avoid_words = playbook.get("brand_voice", {}).get("vocabulary", {}).get("avoid", [])
                caption_lower = caption.lower()
                if any(word.lower() in caption_lower for word in avoid_words):
                    quality = "Voice Mismatch"

            # Set expiry date (7 days from now)
            expires_date = (date.today() + timedelta(days=7)).isoformat()

            # Create Notion page
            post_entry = {
                "Post": title,
                "Status": "Ready for Review",
                "Platform": platform,
                "Post Type": post_type,
                "Pillar": pillar_notion,
                "Funnel Stage": funnel_stage,
                "date:Scheduled Date:start": post_date.isoformat(),
                "date:Expires:start": expires_date,
                "Account": account_notion,
                "Project": project_name,
                "Client": project_data.get("client", ""),
                "Caption": caption[:2000],
                "Hashtags": hashtag_set[:2000],
                "Image Paths": image_paths[:2000],
                "Hook": hook,
                "Collaborators": collaborators,
                "Engagement Prediction": engagement_pred,
                "Quality Score": quality
            }

            # Push to Notion
            result = notion_create_page(post_entry)
            status_tag = "→ Notion" if result and result != "queued" else "→ queued"

            # Upload images and add page content (if page was created in Notion)
            if result and result != "queued" and result is not None:
                uploaded_urls = []
                if project_data.get("path"):
                    base_dir = acct.get("projects_dir", "")
                    proj_full_path = os.path.join(base_dir, project_data["path"])

                    if slot["type"] == "carousel":
                        # Upload all carousel images (up to 10)
                        images = sorted([f for f in os.listdir(proj_full_path) if f.endswith(".jpg")])
                        carousel_images = images[:10]
                        for img_name in carousel_images:
                            img_path = os.path.join(proj_full_path, img_name)
                            url = upload_image_to_host(img_path)
                            if url:
                                uploaded_urls.append(url)
                    else:
                        # Single/reel/pins — just the hero
                        hero_path = pick_hero_image(proj_full_path)
                        if hero_path:
                            url = upload_image_to_host(hero_path)
                            if url:
                                uploaded_urls.append(url)

                    if uploaded_urls:
                        status_tag += f" 📷x{len(uploaded_urls)}"

                # Add rich content to page body
                notion_update_page_content(
                    result, uploaded_urls, caption, hashtag_set,
                    post_type, project_name
                )

            logger.info(f"  {post_date} | {platform} | {post_type} | {project_name} | {pillar} {status_tag}")
            total_posts += 1

            # Advance queue position for non-pin posts
            if slot["type"] != "pins":
                queue_pos += 1

        # Save queue position and track first project for variety check
        if slug in state:
            state[slug]["queue_position"] = queue_pos
            if project_queue:
                state[slug]["last_week_first_project"] = project_queue[0]

    save_rotation_state(state)

    msg = f"📋 <b>Weekly Plan Generated</b>\n{total_posts} posts planned for {week_dates[0]} — {week_dates[-1]}\n\n🔗 Review: https://notion.so/{NOTION_CONTENT_DB_ID}"
    print(msg)
    send_telegram(msg)


# ── MODE: PUBLISH ───────────────────────────────────────

def mode_publish():
    """Read today's approved posts from Notion → upload images → schedule."""
    today = get_today()
    accounts = load_accounts()
    state = load_rotation_state()

    logger.info(f"Publish mode — checking for approved posts on {today}")

    # Query Notion for approved posts
    approved_posts = notion_query_approved_today()

    if not approved_posts:
        logger.info("No approved posts for today")
        # Check queue file as fallback info
        if NOTION_QUEUE_FILE.exists():
            with open(NOTION_QUEUE_FILE) as f:
                queue = json.load(f)
            if queue:
                logger.info(f"{len(queue)} posts queued but not yet in Notion. Push queue first.")
        send_telegram(f"📤 <b>Publish Check</b>\nNo approved posts for {today}")
        return

    published_count = 0
    failed_count = 0

    for post in approved_posts:
        page_id = post["id"]
        props = post.get("properties", {})

        # Extract properties
        title = ""
        title_prop = props.get("Post", {}).get("title", [])
        if title_prop:
            title = title_prop[0].get("text", {}).get("content", "")

        platform = props.get("Platform", {}).get("select", {}).get("name", "")
        caption_parts = props.get("Caption", {}).get("rich_text", [])
        caption = caption_parts[0].get("text", {}).get("content", "") if caption_parts else ""
        hashtags_parts = props.get("Hashtags", {}).get("rich_text", [])
        hashtags = hashtags_parts[0].get("text", {}).get("content", "") if hashtags_parts else ""
        image_paths_parts = props.get("Image Paths", {}).get("rich_text", [])
        image_paths_str = image_paths_parts[0].get("text", {}).get("content", "") if image_paths_parts else ""

        account_name = props.get("Account", {}).get("select", {}).get("name", "")
        post_type = props.get("Post Type", {}).get("select", {}).get("name", "")

        # Map account name to slug
        account_slug_map = {"Matt Anthony": "matt-anthony", "LRD Studio": "lrd-studio", "Balmoral": "balmoral"}
        account_slug = account_slug_map.get(account_name, "matt-anthony")
        acct = accounts.get(account_slug, {})

        # Build full caption with hashtags
        full_caption = caption
        if hashtags:
            full_caption += f"\n\n{hashtags}"

        logger.info(f"Publishing: {title} → {platform}")

        # Get scheduled time
        sched_date = props.get("Scheduled Date", {}).get("date", {})
        sched_time = sched_date.get("start", today) if sched_date else today
        # Default to 9am PT (17:00 UTC)
        scheduled_for = f"{sched_time}T17:00:00Z"

        # All platforms publish through Late
        platform_key = platform.lower()
        platform_config = acct.get("platforms", {}).get(platform_key, {})
        account_id = platform_config.get("account_id")

        if not account_id:
            logger.warning(f"No Late account_id for {account_name}/{platform} — skipping")
            failed_count += 1
            continue

        # Parse image paths and upload
        image_files = [p.strip() for p in image_paths_str.split(",") if p.strip()]
        media_items = []
        projects_dir = acct.get("projects_dir", "")

        # Text-only posts don't need images
        needs_images = post_type not in ("Text",)

        if needs_images and image_files:
            for img_file in image_files[:10]:
                full_img_path = None
                if os.path.isabs(img_file) and os.path.exists(img_file):
                    full_img_path = img_file
                else:
                    for root, dirs, files in os.walk(projects_dir):
                        if img_file in files:
                            full_img_path = os.path.join(root, img_file)
                            break

                if full_img_path:
                    url = upload_image_to_host(full_img_path)
                    if url:
                        media_items.append({"url": url, "type": "image"})
                else:
                    logger.warning(f"Image not found: {img_file}")

            if not media_items:
                logger.warning(f"No images uploaded for {title} — skipping")
                failed_count += 1
                continue

        # Schedule via Late API
        post_id = late_create_post(platform, account_id, full_caption, media_items, scheduled_for)
        if post_id:
            notion_update_status(page_id, "Scheduled", post_id=post_id)
            published_count += 1

            # Update rotation state
            project_parts = props.get("Project", {}).get("rich_text", [])
            project_name = project_parts[0].get("text", {}).get("content", "") if project_parts else ""
            if account_slug in state:
                state[account_slug].setdefault("last_posted", {})[project_name.lower().replace(" ", "-")] = today
                state[account_slug].setdefault("post_counts", {})[project_name.lower().replace(" ", "-")] = \
                    state[account_slug].get("post_counts", {}).get(project_name.lower().replace(" ", "-"), 0) + 1
        else:
            failed_count += 1

    save_rotation_state(state)

    msg = f"📤 <b>Published {published_count} posts</b>"
    if failed_count:
        msg += f" ({failed_count} failed)"
    msg += f"\nDate: {today}"
    print(msg)
    send_telegram(msg)


# ── MODE: NOTIFY ────────────────────────────────────────

def mode_notify():
    """Send Telegram summary linking to Notion calendar for review."""
    accounts = load_accounts()
    state = load_rotation_state()

    lines = [
        "<b>📋 Weekly Content Calendar Ready for Review</b>",
        "",
        f"🔗 <a href='https://notion.so/{NOTION_CONTENT_DB_ID}'>Open in Notion</a>",
        ""
    ]

    for slug, acct in accounts.items():
        playbook = load_playbook(slug)
        if not playbook:
            continue
        schedule = playbook.get("weekly_schedule", [])
        if not schedule:
            continue

        has_connected = any(
            p.get("account_id") or p.get("integration_id")
            for p in acct.get("platforms", {}).values()
        )
        if not has_connected and acct["type"] == "client":
            continue

        post_count = len(schedule)
        platforms = list(set(s["platform"] for s in schedule))
        lines.append(f"<b>{acct['label']}</b>: {post_count} posts across {', '.join(platforms)}")

    # Check for stale posts (approved but past expiry)
    if NOTION_API_KEY:
        try:
            stale_resp = requests.post(
                f"{NOTION_API_BASE}/databases/{NOTION_CONTENT_DB_ID}/query",
                headers=notion_headers(),
                json={"filter": {"and": [
                    {"property": "Status", "select": {"equals": "Ready for Review"}},
                    {"property": "Expires", "date": {"on_or_before": get_today()}}
                ]}},
                timeout=15
            )
            stale_count = len(stale_resp.json().get("results", []))
            if stale_count > 0:
                lines.append(f"⚠️ <b>{stale_count} stale post(s)</b> — past 7-day review window")
                lines.append("")
        except Exception:
            pass

    lines.append("")
    lines.append("Review and approve by Monday morning. Approved posts auto-publish daily at 9am.")
    lines.append(f"\n📋 <a href='https://notion.so/{NOTION_CONTENT_DB_ID}'>Approval instructions</a>")

    msg = "\n".join(lines)
    print(msg)
    send_telegram(msg)


# ── MODE: REPORT ────────────────────────────────────────

def late_fetch_analytics(account_id, from_date=None, to_date=None):
    """Fetch post analytics from Late.dev REST API."""
    if not LATE_API_KEY:
        logger.warning("No LATE_API_KEY — cannot fetch analytics")
        return []
    if not from_date:
        from_date = (date.today() - timedelta(days=90)).isoformat()
    if not to_date:
        to_date = date.today().isoformat()
    try:
        resp = requests.get(
            f"{LATE_API_BASE}/analytics",
            headers={"Authorization": f"Bearer {LATE_API_KEY}"},
            params={"accountId": account_id, "from": from_date, "to": to_date},
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("posts", [])
        else:
            logger.error(f"Late analytics error ({resp.status_code}): {resp.text[:200]}")
            return []
    except Exception as e:
        logger.error(f"Late analytics fetch error: {e}")
        return []


def notion_sync_analytics(posts_data):
    """Sync Late analytics into Notion pages.

    For each post with analytics, find or create a Notion page and update metrics.
    Returns (synced_count, created_count).
    """
    if not NOTION_API_KEY:
        logger.warning("No NOTION_API_KEY — cannot sync to Notion")
        return 0, 0

    # Get all existing pages from Notion to match by Post URL or Post ID
    existing = {}
    try:
        resp = requests.post(
            f"{NOTION_API_BASE}/databases/{NOTION_CONTENT_DB_ID}/query",
            headers=notion_headers(),
            json={"page_size": 100},
            timeout=15
        )
        if resp.status_code == 200:
            for page in resp.json().get("results", []):
                props = page.get("properties", {})
                # Index by Post URL
                url = props.get("Post URL", {}).get("url")
                if url:
                    existing[url] = page["id"]
                # Also index by post ID in rich text
                pid_rt = props.get("Post ID", {}).get("rich_text", [])
                if pid_rt:
                    pid = pid_rt[0].get("plain_text", "")
                    if pid:
                        existing[pid] = page["id"]
    except Exception as e:
        logger.warning(f"Failed to query existing Notion pages: {e}")

    synced = 0
    created = 0
    now = datetime.utcnow().isoformat()[:19]

    for post in posts_data:
        analytics = post.get("analytics", {})
        if not analytics:
            continue

        platform_url = post.get("platformPostUrl", "")
        platform_post_id = ""
        for p in post.get("platforms", []):
            if p.get("platformPostId"):
                platform_post_id = p["platformPostId"]
                break

        er = analytics.get("engagementRate", 0)
        er_decimal = er / 100.0 if er > 1 else er

        update_props = {
            "Impressions": {"number": analytics.get("impressions", 0)},
            "Reach": {"number": analytics.get("reach", 0)},
            "Likes": {"number": analytics.get("likes", 0)},
            "Comments Count": {"number": analytics.get("comments", 0)},
            "Shares": {"number": analytics.get("shares", 0)},
            "Saves": {"number": analytics.get("saves", 0)},
            "Engagement Rate": {"number": er_decimal},
            "Analytics Updated": {"date": {"start": now}},
        }
        if platform_url:
            update_props["Post URL"] = {"url": platform_url}

        # Find existing page
        page_id = existing.get(platform_url) or existing.get(platform_post_id)

        if page_id:
            # Update existing page
            try:
                resp = requests.patch(
                    f"{NOTION_API_BASE}/pages/{page_id}",
                    headers=notion_headers(),
                    json={"properties": update_props},
                    timeout=15
                )
                if resp.status_code == 200:
                    synced += 1
                else:
                    logger.warning(f"Failed to update {page_id}: {resp.status_code}")
            except Exception as e:
                logger.warning(f"Notion update error: {e}")
        else:
            # Create new page with analytics + post info
            content = post.get("content", "")
            caption_preview = content[:80].replace("\n", " ") if content else "Untitled"
            pub_date = post.get("publishedAt", "")[:10]
            media_type = post.get("mediaType", "image")
            platform = post.get("platform", "instagram")

            create_props = {
                **update_props,
                "Post": {"title": [{"text": {"content": caption_preview}}]},
                "Platform": {"select": {"name": platform.capitalize() if platform != "instagram" else "Instagram"}},
                "Post Type": {"select": {"name": media_type.capitalize() if media_type else "Image"}},
                "Status": {"select": {"name": "Published"}},
                "Account": {"select": {"name": "Matt Anthony"}},
            }
            if pub_date:
                create_props["Scheduled Date"] = {"date": {"start": pub_date}}
            if platform_post_id:
                create_props["Post ID"] = {"rich_text": [{"text": {"content": platform_post_id}}]}
            if content:
                create_props["Caption"] = {"rich_text": [{"text": {"content": content[:2000]}}]}

            try:
                resp = requests.post(
                    f"{NOTION_API_BASE}/pages",
                    headers=notion_headers(),
                    json={"parent": {"database_id": NOTION_CONTENT_DB_ID}, "properties": create_props},
                    timeout=15
                )
                if resp.status_code == 200:
                    created += 1
                    new_id = resp.json().get("id", "")
                    if platform_url:
                        existing[platform_url] = new_id
                else:
                    logger.warning(f"Failed to create page: {resp.status_code} {resp.text[:200]}")
            except Exception as e:
                logger.warning(f"Notion create error: {e}")

    return synced, created


def mode_report():
    """Weekly analytics report — syncs Late data to Notion + sends Telegram summary."""
    today = date.today()
    week_ago = today - timedelta(days=7)

    accounts = load_accounts()
    matt = accounts.get("matt-anthony", {})
    ig_account_id = matt.get("platforms", {}).get("instagram", {}).get("account_id")

    if not ig_account_id:
        logger.error("No Instagram account ID configured")
        return

    # Fetch analytics from Late REST API
    logger.info("Fetching analytics from Late.dev...")
    posts = late_fetch_analytics(ig_account_id, from_date="2025-01-01", to_date=today.isoformat())

    if not posts:
        msg = "📊 <b>Weekly Report</b>\n\nNo analytics data available from Late.dev."
        print(msg)
        send_telegram(msg)
        return

    # Sync to Notion
    logger.info(f"Syncing {len(posts)} posts to Notion...")
    synced, created = notion_sync_analytics(posts)
    logger.info(f"Notion sync: {synced} updated, {created} created")

    # Calculate weekly stats (posts from last 7 days)
    weekly_posts = [p for p in posts if p.get("publishedAt", "")[:10] >= week_ago.isoformat()]
    all_posts = posts

    def calc_stats(post_list):
        if not post_list:
            return {"count": 0, "impressions": 0, "reach": 0, "likes": 0, "comments": 0, "shares": 0, "saves": 0, "avg_er": 0}
        total_imp = sum(p.get("analytics", {}).get("impressions", 0) for p in post_list)
        total_reach = sum(p.get("analytics", {}).get("reach", 0) for p in post_list)
        total_likes = sum(p.get("analytics", {}).get("likes", 0) for p in post_list)
        total_comments = sum(p.get("analytics", {}).get("comments", 0) for p in post_list)
        total_shares = sum(p.get("analytics", {}).get("shares", 0) for p in post_list)
        total_saves = sum(p.get("analytics", {}).get("saves", 0) for p in post_list)
        ers = [p.get("analytics", {}).get("engagementRate", 0) for p in post_list if p.get("analytics", {}).get("engagementRate")]
        avg_er = sum(ers) / len(ers) if ers else 0
        return {
            "count": len(post_list), "impressions": total_imp, "reach": total_reach,
            "likes": total_likes, "comments": total_comments, "shares": total_shares,
            "saves": total_saves, "avg_er": avg_er
        }

    ws = calc_stats(weekly_posts)
    total = calc_stats(all_posts)

    # Find top performer
    top = max(all_posts, key=lambda p: p.get("analytics", {}).get("reach", 0))
    top_a = top.get("analytics", {})
    top_content = top.get("content", "")[:60].replace("\n", " ")

    # Sort posts by reach for ranking
    ranked = sorted(all_posts, key=lambda p: p.get("analytics", {}).get("reach", 0), reverse=True)

    # Create Notion weekly summary page
    report_title = f"Weekly Report — {week_ago.strftime('%b %d')} to {today.strftime('%b %d, %Y')}"
    if NOTION_API_KEY:
        logger.info("Creating weekly summary page in Notion...")
        children = []

        # Header
        children.append({
            "object": "block", "type": "heading_1",
            "heading_1": {"rich_text": [{"type": "text", "text": {"content": "This Week"}}]}
        })

        # Weekly stats callout
        if ws["count"] > 0:
            weekly_summary = (
                f"Posts: {ws['count']}  |  Reach: {ws['reach']:,}  |  Impressions: {ws['impressions']:,}\n"
                f"Likes: {ws['likes']}  |  Comments: {ws['comments']}  |  Shares: {ws['shares']}  |  Saves: {ws['saves']}\n"
                f"Avg Engagement Rate: {ws['avg_er']:.1f}%"
            )
        else:
            weekly_summary = "No posts published this week."
        children.append({
            "object": "block", "type": "callout",
            "callout": {
                "icon": {"type": "emoji", "emoji": "📊"},
                "rich_text": [{"type": "text", "text": {"content": weekly_summary}}]
            }
        })

        children.append({"object": "block", "type": "divider", "divider": {}})

        # All time stats
        children.append({
            "object": "block", "type": "heading_1",
            "heading_1": {"rich_text": [{"type": "text", "text": {"content": "All Time"}}]}
        })
        all_time_summary = (
            f"Total Posts: {total['count']}  |  Total Reach: {total['reach']:,}  |  Total Impressions: {total['impressions']:,}\n"
            f"Total Likes: {total['likes']}  |  Comments: {total['comments']}  |  Shares: {total['shares']}  |  Saves: {total['saves']}\n"
            f"Avg Engagement Rate: {total['avg_er']:.1f}%"
        )
        children.append({
            "object": "block", "type": "callout",
            "callout": {
                "icon": {"type": "emoji", "emoji": "📈"},
                "rich_text": [{"type": "text", "text": {"content": all_time_summary}}]
            }
        })

        children.append({"object": "block", "type": "divider", "divider": {}})

        # Top performer
        children.append({
            "object": "block", "type": "heading_1",
            "heading_1": {"rich_text": [{"type": "text", "text": {"content": "Top Performer"}}]}
        })
        top_url = top.get("platformPostUrl", "")
        top_caption = top.get("content", "")[:300]
        top_summary = (
            f"Reach: {top_a.get('reach',0):,}  |  Impressions: {top_a.get('impressions',0):,}\n"
            f"Likes: {top_a.get('likes',0)}  |  Comments: {top_a.get('comments',0)}  |  "
            f"Shares: {top_a.get('shares',0)}  |  Saves: {top_a.get('saves',0)}  |  "
            f"ER: {top_a.get('engagementRate',0):.1f}%"
        )
        children.append({
            "object": "block", "type": "callout",
            "callout": {
                "icon": {"type": "emoji", "emoji": "🏆"},
                "rich_text": [{"type": "text", "text": {"content": top_summary}}]
            }
        })
        if top_url:
            children.append({
                "object": "block", "type": "bookmark",
                "bookmark": {"url": top_url}
            })
        if top_caption:
            children.append({
                "object": "block", "type": "quote",
                "quote": {"rich_text": [{"type": "text", "text": {"content": top_caption}}]}
            })

        # Top post thumbnail
        top_thumb = top.get("thumbnailUrl", "")
        if top_thumb:
            children.append({
                "object": "block", "type": "image",
                "image": {"type": "external", "external": {"url": top_thumb}}
            })

        children.append({"object": "block", "type": "divider", "divider": {}})

        # Post-by-post breakdown table (as numbered list)
        children.append({
            "object": "block", "type": "heading_1",
            "heading_1": {"rich_text": [{"type": "text", "text": {"content": "All Posts — Ranked by Reach"}}]}
        })
        for i, p in enumerate(ranked):
            a = p.get("analytics", {})
            pub = p.get("publishedAt", "")[:10]
            content_short = p.get("content", "")[:50].replace("\n", " ")
            media = p.get("mediaType", "image")
            url = p.get("platformPostUrl", "")
            line = (
                f"{pub}  |  {media}  |  Reach: {a.get('reach',0):,}  |  "
                f"ER: {a.get('engagementRate',0):.1f}%  |  "
                f"{a.get('likes',0)} likes, {a.get('shares',0)} shares, {a.get('saves',0)} saves"
            )
            text_parts = [{"type": "text", "text": {"content": f"{content_short}\n{line}"}}]
            if url:
                text_parts.append({"type": "text", "text": {"content": f"\n{url}", "link": {"url": url}}})
            children.append({
                "object": "block", "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": text_parts}
            })

        # Create the page in the Social Media database
        report_props = {
            "Post": {"title": [{"text": {"content": report_title}}]},
            "Post Type": {"select": {"name": "Report"}},
            "Status": {"select": {"name": "Published"}},
            "Account": {"select": {"name": "Matt Anthony"}},
            "Platform": {"select": {"name": "Instagram"}},
            "Scheduled Date": {"date": {"start": today.isoformat()}},
            "Impressions": {"number": total["impressions"]},
            "Reach": {"number": total["reach"]},
            "Likes": {"number": total["likes"]},
            "Comments Count": {"number": total["comments"]},
            "Shares": {"number": total["shares"]},
            "Saves": {"number": total["saves"]},
            "Engagement Rate": {"number": total["avg_er"] / 100.0},
            "Analytics Updated": {"date": {"start": datetime.utcnow().isoformat()[:19]}},
        }

        try:
            resp = requests.post(
                f"{NOTION_API_BASE}/pages",
                headers=notion_headers(),
                json={
                    "parent": {"database_id": NOTION_CONTENT_DB_ID},
                    "properties": report_props,
                    "children": children
                },
                timeout=30
            )
            if resp.status_code == 200:
                page_id = resp.json().get("id", "")
                page_url = resp.json().get("url", "")
                logger.info(f"Weekly report page created: {page_url}")
            else:
                logger.error(f"Failed to create report page: {resp.status_code} {resp.text[:300]}")
                page_url = ""
        except Exception as e:
            logger.error(f"Notion report page error: {e}")
            page_url = ""
    else:
        page_url = ""

    # Build Telegram message
    lines = [
        f"<b>📊 Weekly Social Media Report</b>",
        f"<i>{week_ago.strftime('%b %d')} — {today.strftime('%b %d, %Y')}</i>",
        "",
        f"<b>This Week:</b>",
        f"  Posts: {ws['count']}",
        f"  Reach: {ws['reach']:,}",
        f"  Impressions: {ws['impressions']:,}",
        f"  Engagement: {ws['likes']} likes, {ws['comments']} comments, {ws['shares']} shares, {ws['saves']} saves",
        f"  Avg ER: {ws['avg_er']:.1f}%",
        "",
        f"<b>All Time ({total['count']} posts):</b>",
        f"  Total Reach: {total['reach']:,}",
        f"  Total Impressions: {total['impressions']:,}",
        f"  Avg ER: {total['avg_er']:.1f}%",
        "",
        f"<b>🏆 Top Post:</b>",
        f"  {top_content}",
        f"  Reach: {top_a.get('reach',0):,} | {top_a.get('shares',0)} shares | {top_a.get('saves',0)} saves",
        "",
        f"<b>Notion:</b> {synced} updated, {created} new pages",
    ]
    if page_url:
        lines.append(f"<a href=\"{page_url}\">View Full Report</a>")

    msg = "\n".join(lines)
    print(msg)
    send_telegram(msg)


# ── MAIN ────────────────────────────────────────────────

def notion_get_comments(page_id):
    """Get comments from a Notion page via API. Returns list of comment texts."""
    if not NOTION_API_KEY:
        return []
    try:
        resp = requests.get(
            f"{NOTION_API_BASE}/comments?block_id={page_id}",
            headers=notion_headers(),
            timeout=15
        )
        if resp.status_code != 200:
            return []
        comments = resp.json().get("results", [])
        # Extract text from each comment, most recent first
        texts = []
        for c in reversed(comments):
            parts = c.get("rich_text", [])
            text = "".join(p.get("text", {}).get("content", "") for p in parts)
            author = c.get("created_by", {}).get("name", "Unknown")
            created = c.get("created_time", "")[:10]
            if text.strip():
                texts.append({"text": text, "author": author, "date": created, "id": c.get("discussion_id", "")})
        return texts
    except Exception as e:
        logger.warning(f"Failed to get comments for {page_id}: {e}")
        return []


def notion_add_comment(page_id, text):
    """Add a comment to a Notion page via API."""
    if not NOTION_API_KEY:
        return
    try:
        requests.post(
            f"{NOTION_API_BASE}/comments",
            headers=notion_headers(),
            json={
                "parent": {"page_id": page_id},
                "rich_text": [{"text": {"content": text[:2000]}}]
            },
            timeout=15
        )
    except Exception as e:
        logger.warning(f"Failed to add comment: {e}")


def mode_revise():
    """Full post regeneration for posts marked 'Revision Needed'.
    Reads Client Notes feedback, then rebuilds the entire post:
    new image selection, new caption via Vision, new page content."""
    if not NOTION_API_KEY:
        logger.warning("No NOTION_API_KEY — cannot query Notion")
        return

    logger.info("Checking for posts needing revision...")

    try:
        resp = requests.post(
            f"{NOTION_API_BASE}/databases/{NOTION_CONTENT_DB_ID}/query",
            headers=notion_headers(),
            json={"filter": {"property": "Status", "select": {"equals": "Revision Needed"}}},
            timeout=15
        )
        posts = resp.json().get("results", [])
    except Exception as e:
        logger.error(f"Notion query error: {e}")
        return

    if not posts:
        logger.info("No posts needing revision")
        return

    logger.info(f"Found {len(posts)} posts needing revision")
    accounts = load_accounts()
    revised_count = 0

    for post in posts:
        page_id = post["id"]
        props = post.get("properties", {})

        title_prop = props.get("Post", {}).get("title", [])
        title = title_prop[0].get("text", {}).get("content", "") if title_prop else ""

        # Get feedback from Client Notes
        notes_parts = props.get("Client Notes", {}).get("rich_text", [])
        client_notes = notes_parts[0].get("text", {}).get("content", "") if notes_parts else ""

        if not client_notes:
            logger.warning(f"Skipping {title} — no feedback in Client Notes")
            continue

        # Check for duplicate feedback
        revision_parts = props.get("Revision History", {}).get("rich_text", [])
        revision_history = revision_parts[0].get("text", {}).get("content", "") if revision_parts else ""
        if client_notes in revision_history:
            logger.info(f"Skipping {title} — same feedback as last revision. Update Client Notes to trigger new revision.")
            continue

        # Get current state
        caption_parts = props.get("Caption", {}).get("rich_text", [])
        old_caption = caption_parts[0].get("text", {}).get("content", "") if caption_parts else ""
        project_parts = props.get("Project", {}).get("rich_text", [])
        project_name = project_parts[0].get("text", {}).get("content", "") if project_parts else ""
        platform = props.get("Platform", {}).get("select", {}).get("name", "")
        post_type = props.get("Post Type", {}).get("select", {}).get("name", "")
        pillar_name = props.get("Pillar", {}).get("select", {}).get("name", "")
        account_name = props.get("Account", {}).get("select", {}).get("name", "")
        hook_parts = props.get("Hook", {}).get("rich_text", [])
        old_hook = hook_parts[0].get("text", {}).get("content", "") if hook_parts else ""

        account_slug_map = {"Matt Anthony": "matt-anthony", "LRD Studio": "lrd-studio", "Balmoral": "balmoral"}
        account_slug = account_slug_map.get(account_name, "matt-anthony")
        acct = accounts.get(account_slug, {})
        playbook = load_playbook(account_slug)

        if not playbook:
            logger.warning(f"Skipping {title} — no playbook")
            continue

        logger.info(f"Full revision: {title}")
        logger.info(f"  Feedback: {client_notes[:150]}")

        # Mark as In Revision
        notion_update_status(page_id, "In Revision")

        # Find project data in playbook
        project_data = {}
        for p in playbook.get("projects", []):
            if p.get("name", "").lower() in project_name.lower() or project_name.lower() in p.get("name", "").lower():
                project_data = p
                break

        projects_dir = acct.get("projects_dir", "")
        proj_path = os.path.join(projects_dir, project_data.get("path", "")) if project_data.get("path") else ""

        # === STEP 1: RE-SELECT IMAGES ===
        new_image_paths = ""
        uploaded_urls = []

        if proj_path and os.path.isdir(proj_path):
            # Get previously used images to select DIFFERENT ones
            old_paths_parts = props.get("Image Paths", {}).get("rich_text", [])
            old_paths = old_paths_parts[0].get("text", {}).get("content", "") if old_paths_parts else ""
            old_images = [i.strip() for i in old_paths.split(",") if i.strip()]

            if post_type in ("Carousel", "carousel"):
                # Use carousel framework to curate a storytelling sequence
                # Exclude previously used images to get fresh selection
                selected = curate_carousel_images(proj_path, playbook, exclude_images=old_images)
                new_image_paths = ", ".join(selected)

                # Upload all carousel images
                for img_name in selected:
                    img_full = os.path.join(proj_path, img_name)
                    url = upload_image_to_host(img_full)
                    if url:
                        uploaded_urls.append(url)
            else:
                # Single/reel/pin — pick a different hero
                all_images = sorted([f for f in os.listdir(proj_path) if f.endswith(".jpg")])
                unused = [img for img in all_images if img not in old_images]
                if unused:
                    # Pick best unused exterior/hero
                    hero_name = next((img for img in unused if "twilight" in img or "exterior" in img), unused[0])
                else:
                    hero_name = os.path.basename(pick_hero_image(proj_path) or "")

                new_image_paths = hero_name
                if hero_name:
                    url = upload_image_to_host(os.path.join(proj_path, hero_name))
                    if url:
                        uploaded_urls.append(url)

            logger.info(f"  New images selected: {len(uploaded_urls)} uploaded")

        # === STEP 2: REGENERATE CAPTION WITH VISION ON THE NEW IMAGES ===
        new_selected = [i.strip() for i in new_image_paths.split(",") if i.strip()] if new_image_paths else None
        new_caption = None
        if ANTHROPIC_API_KEY and project_data:
            new_caption = generate_caption_for_post(
                project_data, platform, post_type, pillar_name,
                old_hook, playbook, projects_dir,
                specific_images=new_selected
            )

            # If we got a caption, refine it with the specific feedback
            if new_caption and client_notes:
                try:
                    from generate_captions import get_client as get_ai_client
                    voice = playbook.get("brand_voice", {})

                    refine_prompt = f"""Adjust this caption based on the client's specific feedback.

GENERATED CAPTION:
{new_caption}

CLIENT FEEDBACK:
{client_notes}

BRAND VOICE: {voice.get('tone', '')}
Words to AVOID: {', '.join(voice.get('vocabulary', {}).get('avoid', []))}

Apply the feedback. Write ONLY the final caption. No preamble."""

                    ai_client = get_ai_client()
                    message = ai_client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1024,
                        messages=[{"role": "user", "content": refine_prompt}],
                    )
                    new_caption = message.content[0].text
                    logger.info(f"  Caption refined with feedback ({len(new_caption)} chars)")
                except Exception as e:
                    logger.warning(f"  Caption refinement failed: {e}")

        if not new_caption:
            new_caption = old_caption  # Keep old if generation failed

        # === STEP 3: UPDATE NOTION ===
        # Update properties
        revision_log = f"Full revision {get_today()}\nFeedback: {client_notes[:300]}\n\nPrevious caption: {old_caption[:400]}"

        update_props = {
            "Caption": {"rich_text": [{"text": {"content": new_caption[:2000]}}]},
            "Status": {"select": {"name": "Ready for Review"}},
            "Quality Score": {"select": {"name": "Publish Ready"}},
            "Revision History": {"rich_text": [{"text": {"content": revision_log[:2000]}}]},
        }
        if new_image_paths:
            update_props["Image Paths"] = {"rich_text": [{"text": {"content": new_image_paths[:2000]}}]}

        requests.patch(
            f"{NOTION_API_BASE}/pages/{page_id}",
            headers=notion_headers(),
            json={"properties": update_props},
            timeout=15
        )

        # === STEP 4: REBUILD PAGE BODY ===
        # Delete existing content blocks first
        try:
            blocks_resp = requests.get(
                f"{NOTION_API_BASE}/blocks/{page_id}/children",
                headers=notion_headers(),
                timeout=15
            )
            if blocks_resp.status_code == 200:
                for block in blocks_resp.json().get("results", []):
                    requests.delete(
                        f"{NOTION_API_BASE}/blocks/{block['id']}",
                        headers=notion_headers(),
                        timeout=10
                    )
        except Exception:
            pass

        # Get hashtags
        hashtags_parts = props.get("Hashtags", {}).get("rich_text", [])
        hashtags = hashtags_parts[0].get("text", {}).get("content", "") if hashtags_parts else ""

        # Rebuild with new images and caption
        notion_update_page_content(
            page_id, uploaded_urls, new_caption, hashtags,
            post_type, project_name
        )

        # Add comment confirming the revision
        notion_add_comment(page_id,
            f"Post fully revised — new images selected, caption rewritten based on your feedback. Please review and approve.")

        logger.info(f"  Full revision complete — {len(uploaded_urls)} new images, new caption")
        revised_count += 1

    if revised_count > 0:
        msg = f"✏️ <b>Full Revisions Complete</b>\n{revised_count}/{len(posts)} posts rebuilt with new images + captions"
        print(msg)
        send_telegram(msg)


def mode_email_notify():
    """Email each client a digest of posts ready for their review.
    Looks at all client accounts in social_accounts.json, queries Notion for
    Status='Ready for Review', sends a Gmail with a portal link.
    """
    import base64
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    if not NOTION_API_KEY:
        logger.warning("No NOTION_API_KEY")
        return

    accounts = load_accounts()
    portal_url = os.getenv("PORTAL_URL", "https://portal.mattanthonyphoto.com")

    # Map account slug → client email — would come from a clients.json or env
    CLIENT_EMAILS = {
        "lrd-studio": "lauren@lrdstudio.ca",
        "balmoral": "info@balmoralconstruction.ca",
        "matt-anthony": "info@mattanthonyphoto.com",
    }

    sent_count = 0
    for slug, account in accounts.items():
        if account.get("type") != "client":
            continue

        client_email = CLIENT_EMAILS.get(slug)
        if not client_email:
            logger.info(f"No email for {slug}, skipping")
            continue

        label = account.get("label", slug)

        # Query approvals for this client
        try:
            resp = requests.post(
                f"{NOTION_API_BASE}/databases/{NOTION_CONTENT_DB_ID}/query",
                headers=notion_headers(),
                json={"filter": {"and": [
                    {"property": "Account", "select": {"equals": label}},
                    {"property": "Status", "select": {"equals": "Ready for Review"}},
                ]}},
                timeout=15
            )
            posts = resp.json().get("results", [])
        except Exception as e:
            logger.error(f"Failed to query {slug}: {e}")
            continue

        if not posts:
            logger.info(f"{slug}: no pending approvals, skipping email")
            continue

        # Build the email
        post_list_html = ""
        for p in posts[:10]:
            title = (p.get("properties", {}).get("Post", {}).get("title", [{}])[0].get("plain_text", "Untitled"))
            platform = p.get("properties", {}).get("Platform", {}).get("select", {}).get("name", "")
            scheduled = p.get("properties", {}).get("Scheduled Date", {}).get("date", {}).get("start", "")
            post_list_html += f"""
              <tr>
                <td style="padding: 12px 0; border-bottom: 1px solid #E5E1D8;">
                  <p style="margin: 0; font-family: Georgia, serif; font-size: 16px; color: #1A1A18;">{title}</p>
                  <p style="margin: 4px 0 0; font-family: Helvetica, sans-serif; font-size: 12px; color: #8A8579;">{platform}{' · ' + scheduled if scheduled else ''}</p>
                </td>
              </tr>
            """

        html = f"""<!DOCTYPE html>
<html>
<body style="margin: 0; padding: 0; background-color: #F6F4F0; font-family: Helvetica, Arial, sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #F6F4F0; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table width="500" cellpadding="0" cellspacing="0" style="background-color: white; border-radius: 8px; padding: 40px;">
          <tr><td>
            <p style="margin: 0 0 8px; font-family: Helvetica, sans-serif; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #8A8579;">Your Client Portal</p>
            <h1 style="margin: 0 0 24px; font-family: Georgia, serif; font-size: 28px; font-weight: 300; color: #1A1A18;">
              {len(posts)} post{'s' if len(posts) > 1 else ''} ready for your review
            </h1>
            <p style="margin: 0 0 24px; font-family: Helvetica, sans-serif; font-size: 14px; line-height: 1.6; color: #1A1A18;">
              Hi {label},<br><br>
              I've drafted new content for you. Take a moment to review and approve, request changes, or scrap any post you don't love.
            </p>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
              {post_list_html}
            </table>
            <a href="{portal_url}/approvals" style="display: inline-block; background-color: #C9A96E; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-family: Helvetica, sans-serif; font-size: 14px; font-weight: 500;">
              Review in Portal →
            </a>
            <p style="margin: 32px 0 0; font-family: Helvetica, sans-serif; font-size: 12px; color: #8A8579; line-height: 1.6;">
              Reply to this email if you need anything urgent.<br>
              — Matt
            </p>
          </td></tr>
        </table>
        <p style="margin-top: 24px; font-family: Helvetica, sans-serif; font-size: 11px; color: #8A8579;">
          Matt Anthony Photography · Squamish, BC
        </p>
      </td>
    </tr>
  </table>
</body>
</html>
"""

        try:
            from agent_utils import get_gmail_service
            svc = get_gmail_service()
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"{len(posts)} post{'s' if len(posts) > 1 else ''} ready for your review"
            msg["From"] = "info@mattanthonyphoto.com"
            msg["To"] = client_email
            msg.attach(MIMEText(html, "html"))
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            svc.users().messages().send(userId="me", body={"raw": raw}).execute()
            logger.info(f"✓ Sent approval email to {client_email} ({len(posts)} posts)")
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to email {client_email}: {e}")

    msg = f"📧 <b>Email notifications sent</b>\n{sent_count} clients notified"
    print(msg)
    if sent_count > 0:
        send_telegram(msg)


def mode_regenerate():
    """Find posts marked Cancelled with 'DECLINED' note and generate fresh replacements.
    Triggered after a client clicks Decline in the portal."""
    if not NOTION_API_KEY:
        logger.warning("No NOTION_API_KEY")
        return

    logger.info("Checking for declined posts to regenerate...")
    try:
        resp = requests.post(
            f"{NOTION_API_BASE}/databases/{NOTION_CONTENT_DB_ID}/query",
            headers=notion_headers(),
            json={"filter": {"and": [
                {"property": "Status", "select": {"equals": "Cancelled"}},
                {"property": "Client Notes", "rich_text": {"contains": "DECLINED"}},
            ]}},
            timeout=15
        )
        posts = resp.json().get("results", [])
    except Exception as e:
        logger.error(f"Notion query error: {e}")
        return

    if not posts:
        logger.info("No declined posts to regenerate")
        return

    logger.info(f"Found {len(posts)} declined posts — archiving and regenerating")

    archived = 0
    for post in posts:
        page_id = post["id"]
        # Archive the declined page
        try:
            requests.patch(
                f"{NOTION_API_BASE}/pages/{page_id}",
                headers=notion_headers(),
                json={"archived": True},
                timeout=15
            )
            archived += 1
        except Exception as e:
            logger.warning(f"Failed to archive {page_id}: {e}")

    logger.info(f"Archived {archived} declined posts")

    # Trigger fresh planning to fill the slots
    logger.info("Running plan mode to generate replacement posts...")
    try:
        mode_plan()
    except Exception as e:
        logger.error(f"Plan mode failed: {e}")

    msg = f"♻️ <b>Regeneration Complete</b>\n{archived} declined posts archived, fresh content generated"
    print(msg)
    send_telegram(msg)


MODES = {
    "plan": mode_plan,
    "publish": mode_publish,
    "rotate": mode_rotate,
    "notify": mode_notify,
    "report": mode_report,
    "revise": mode_revise,
    "regenerate": mode_regenerate,
    "email": mode_email_notify,
    "status": mode_status,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in MODES:
        print(f"Usage: python3 {sys.argv[0]} <{'|'.join(MODES.keys())}>")
        sys.exit(1)

    mode = sys.argv[1]
    logger.info(f"The Publicist — {mode} mode — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    MODES[mode]()
