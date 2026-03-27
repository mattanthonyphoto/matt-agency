#!/usr/bin/env python3
"""
Instagram Story Generator — Matt Anthony Photography

Generates branded 1080x1920 story images with text overlays.
Uses brand fonts (Josefin Sans, DM Sans, Cormorant Garamond) and colors.

Templates:
  new_post    — "New on the feed" reshare teaser
  project     — Project name + location + builder tag
  insight     — Photography tip or industry insight
  split       — This or that (two images side by side)
  stat        — Bold statistic or fact
  cta         — Call to action (booking, link in bio)
  quote       — Editorial quote on photo background

Usage:
  python tools/story_generator.py generate \
    --template new_post \
    --image "path/to/photo.jpg" \
    --text "The Perch — Full Project Reveal" \
    --output "output/story.jpg"

  python tools/story_generator.py batch \
    --config stories.json \
    --output-dir "output/stories/"

  python tools/story_generator.py week \
    --project-dir "Photo Assets/Client/Project" \
    --project "The Perch" \
    --output-dir "output/stories/"
"""

import argparse
import json
import os
import sys
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# ============================================================
# Brand Constants
# ============================================================

STORY_W, STORY_H = 1080, 1920

FONTS_DIR = os.path.join(os.path.dirname(__file__), "reel-generator", "public", "fonts")
if not os.path.exists(FONTS_DIR):
    FONTS_DIR = os.path.join(os.path.dirname(__file__), "..", ".tmp", "fonts")

COLORS = {
    "ink": (26, 26, 24),
    "paper": (246, 244, 240),
    "gold": (201, 169, 110),
    "warm_muted": (184, 151, 90),
    "stone": (138, 133, 121),
    "light_stone": (217, 213, 205),
    "off_white": (238, 236, 230),
}

# Safe zones (avoid IG UI overlay)
SAFE_TOP = 180      # Below profile pic / close button
SAFE_BOTTOM = 280   # Above reply bar / send message
SAFE_SIDE = 60      # Side padding


def load_font(name, size):
    """Load a brand font by shorthand name."""
    font_map = {
        "josefin": "JosefinSans-Regular.ttf",
        "josefin-bold": "JosefinSans-Bold.ttf",
        "dm": "DMSans-Regular.ttf",
        "dm-medium": "DMSans-Medium.ttf",
        "dm-bold": "DMSans-Bold.ttf",
        "dm-light": "DMSans-Light.ttf",
        "dm-italic": "DMSans-Italic.ttf",
        "cormorant": "CormorantGaramond-Regular.ttf",
        "cormorant-light": "CormorantGaramond-Light.ttf",
        "cormorant-bold": "CormorantGaramond-Bold.ttf",
    }
    path = os.path.join(FONTS_DIR, font_map.get(name, name))
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        print(f"Warning: Font {path} not found, using default")
        return ImageFont.load_default()


def prepare_bg(image_path, darken=0.45, blur=0):
    """Load image, crop to 9:16, darken, optional blur."""
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    target_ratio = STORY_W / STORY_H  # 0.5625

    current_ratio = w / h
    if current_ratio > target_ratio:
        # Too wide — crop sides
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        # Too tall — crop top/bottom
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))

    img = img.resize((STORY_W, STORY_H), Image.LANCZOS)

    if blur > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur))

    if darken > 0:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1 - darken)

    return img


def draw_text_block(draw, text, x, y, font, color, max_width, line_spacing=1.3, align="left"):
    """Draw wrapped text block. Returns total height used."""
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split()
        current_line = ""
        for word in words:
            test = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_width and current_line:
                lines.append(current_line)
                current_line = word
            else:
                current_line = test
        if current_line:
            lines.append(current_line)

    total_height = 0
    bbox_sample = draw.textbbox((0, 0), "Ag", font=font)
    line_h = (bbox_sample[3] - bbox_sample[1]) * line_spacing

    for line in lines:
        if not line:
            total_height += line_h * 0.5
            continue
        if align == "center":
            bbox = draw.textbbox((0, 0), line, font=font)
            lw = bbox[2] - bbox[0]
            lx = x + (max_width - lw) / 2
        elif align == "right":
            bbox = draw.textbbox((0, 0), line, font=font)
            lw = bbox[2] - bbox[0]
            lx = x + max_width - lw
        else:
            lx = x
        draw.text((lx, y + total_height), line, fill=color, font=font)
        total_height += line_h

    return total_height


def draw_gold_line(draw, x, y, width, thickness=2):
    """Draw a horizontal gold accent line."""
    draw.rectangle([x, y, x + width, y + thickness], fill=COLORS["gold"])


def draw_gradient_overlay(img, start_y, height, color=(0, 0, 0), start_alpha=0, end_alpha=180):
    """Draw a gradient overlay on the image."""
    overlay = Image.new("RGBA", (STORY_W, height), (0, 0, 0, 0))
    for i in range(height):
        alpha = int(start_alpha + (end_alpha - start_alpha) * (i / height))
        for x in range(STORY_W):
            overlay.putpixel((x, i), (*color, alpha))
    img.paste(Image.alpha_composite(
        img.crop((0, start_y, STORY_W, start_y + height)).convert("RGBA"),
        overlay
    ).convert("RGB"), (0, start_y))
    return img


# ============================================================
# Template: new_post
# ============================================================

def template_new_post(image_path, title, subtitle=None, output_path=None):
    """
    'New on the feed' style story.
    Full photo background with bottom text bar.
    """
    bg = prepare_bg(image_path, darken=0.15)
    bg = draw_gradient_overlay(bg, STORY_H - 700, 700, end_alpha=220)
    draw = ImageDraw.Draw(bg)

    # "NEW POST" label
    label_font = load_font("josefin-bold", 24)
    label_y = STORY_H - SAFE_BOTTOM - 320
    draw.text((SAFE_SIDE, label_y), "N E W   P O S T", fill=COLORS["gold"], font=label_font)

    # Gold line
    draw_gold_line(draw, SAFE_SIDE, label_y + 38, 80)

    # Title — larger, more room to breathe
    title_font = load_font("cormorant-bold", 64)
    h = draw_text_block(draw, title, SAFE_SIDE, label_y + 56,
                        title_font, COLORS["paper"], STORY_W - SAFE_SIDE * 2,
                        line_spacing=1.2)

    # Subtitle — positioned dynamically below title
    if subtitle:
        sub_font = load_font("dm", 26)
        draw_text_block(draw, subtitle, SAFE_SIDE, label_y + 56 + h + 16,
                        sub_font, COLORS["light_stone"], STORY_W - SAFE_SIDE * 2)

    if output_path:
        bg.save(output_path, quality=95)
    return bg


# ============================================================
# Template: project
# ============================================================

def template_project(image_path, project_name, location, builder=None, output_path=None):
    """
    Project showcase story.
    Photo with project info bar at bottom.
    """
    bg = prepare_bg(image_path, darken=0.2)
    bg = draw_gradient_overlay(bg, STORY_H - 700, 700, end_alpha=210)
    draw = ImageDraw.Draw(bg)

    base_y = STORY_H - SAFE_BOTTOM - 300

    # Location pin
    loc_font = load_font("dm-medium", 24)
    draw.text((SAFE_SIDE, base_y), f"\u2022  {location.upper()}", fill=COLORS["gold"], font=loc_font)

    # Gold line
    draw_gold_line(draw, SAFE_SIDE, base_y + 40, 120)

    # Project name
    name_font = load_font("cormorant-bold", 64)
    h = draw_text_block(draw, project_name, SAFE_SIDE, base_y + 56,
                        name_font, COLORS["paper"], STORY_W - SAFE_SIDE * 2)

    # Builder
    if builder:
        builder_font = load_font("dm", 24)
        draw.text((SAFE_SIDE, base_y + 56 + h + 10), builder,
                  fill=COLORS["stone"], font=builder_font)

    if output_path:
        bg.save(output_path, quality=95)
    return bg


# ============================================================
# Template: insight
# ============================================================

def template_insight(image_path, text, attribution=None, output_path=None):
    """
    Photography insight or tip.
    Darkened photo with centered text.
    """
    bg = prepare_bg(image_path, darken=0.55)
    draw = ImageDraw.Draw(bg)

    # Gold line top accent
    line_w = 60
    draw_gold_line(draw, (STORY_W - line_w) // 2, STORY_H // 2 - 180, line_w)

    # Main text
    text_font = load_font("cormorant-light", 48)
    max_w = STORY_W - SAFE_SIDE * 2 - 40
    h = draw_text_block(draw, text, SAFE_SIDE + 20, STORY_H // 2 - 140,
                        text_font, COLORS["paper"], max_w, align="center", line_spacing=1.5)

    # Gold line bottom accent
    draw_gold_line(draw, (STORY_W - line_w) // 2, STORY_H // 2 - 140 + h + 20, line_w)

    # Attribution
    if attribution:
        attr_font = load_font("dm-light", 22)
        draw_text_block(draw, attribution, SAFE_SIDE + 20, STORY_H // 2 - 140 + h + 50,
                        attr_font, COLORS["stone"], max_w, align="center")

    if output_path:
        bg.save(output_path, quality=95)
    return bg


# ============================================================
# Template: stat
# ============================================================

def template_stat(image_path, number, label, context=None, output_path=None):
    """
    Bold statistic story.
    Big number with supporting context.
    """
    bg = prepare_bg(image_path, darken=0.6, blur=8)
    draw = ImageDraw.Draw(bg)

    center_y = STORY_H // 2 - 120

    # Big number
    num_font = load_font("josefin-bold", 140)
    bbox = draw.textbbox((0, 0), number, font=num_font)
    num_w = bbox[2] - bbox[0]
    draw.text(((STORY_W - num_w) // 2, center_y), number,
              fill=COLORS["gold"], font=num_font)

    # Label
    label_font = load_font("dm-medium", 32)
    draw_text_block(draw, label.upper(), SAFE_SIDE, center_y + 170,
                    label_font, COLORS["paper"], STORY_W - SAFE_SIDE * 2, align="center")

    # Context
    if context:
        ctx_font = load_font("dm-light", 24)
        draw_text_block(draw, context, SAFE_SIDE + 40, center_y + 240,
                        ctx_font, COLORS["stone"], STORY_W - SAFE_SIDE * 2 - 80,
                        align="center", line_spacing=1.5)

    if output_path:
        bg.save(output_path, quality=95)
    return bg


# ============================================================
# Template: cta
# ============================================================

def template_cta(image_path, headline, subtext, cta_text="LINK IN BIO", output_path=None):
    """
    Call to action story.
    Photo with CTA button-style text at bottom.
    """
    bg = prepare_bg(image_path, darken=0.3)
    bg = draw_gradient_overlay(bg, STORY_H - 800, 800, end_alpha=220)
    draw = ImageDraw.Draw(bg)

    base_y = STORY_H - SAFE_BOTTOM - 340

    # Headline
    head_font = load_font("cormorant-bold", 52)
    h = draw_text_block(draw, headline, SAFE_SIDE, base_y,
                        head_font, COLORS["paper"], STORY_W - SAFE_SIDE * 2)

    # Subtext
    sub_font = load_font("dm-light", 26)
    draw_text_block(draw, subtext, SAFE_SIDE, base_y + h + 16,
                    sub_font, COLORS["light_stone"], STORY_W - SAFE_SIDE * 2)

    # CTA button
    btn_y = base_y + h + 100
    btn_font = load_font("josefin-bold", 24)
    bbox = draw.textbbox((0, 0), cta_text, font=btn_font)
    btn_w = bbox[2] - bbox[0] + 60
    btn_h = bbox[3] - bbox[1] + 30
    btn_x = (STORY_W - btn_w) // 2

    # Draw button outline
    draw.rounded_rectangle([btn_x, btn_y, btn_x + btn_w, btn_y + btn_h],
                           radius=4, outline=COLORS["gold"], width=2)
    draw.text((btn_x + 30, btn_y + 10), cta_text, fill=COLORS["gold"], font=btn_font)

    if output_path:
        bg.save(output_path, quality=95)
    return bg


# ============================================================
# Template: quote
# ============================================================

def template_quote(image_path, quote_text, attribution=None, output_path=None):
    """
    Editorial quote on photo.
    Large opening quotation mark, elegant typography.
    """
    bg = prepare_bg(image_path, darken=0.55)
    draw = ImageDraw.Draw(bg)

    center_y = STORY_H // 2 - 200

    # Large quotation mark
    quote_mark_font = load_font("cormorant-bold", 200)
    draw.text((SAFE_SIDE, center_y - 100), "\u201C", fill=COLORS["gold"], font=quote_mark_font)

    # Quote text
    quote_font = load_font("cormorant-light", 44)
    max_w = STORY_W - SAFE_SIDE * 2 - 20
    h = draw_text_block(draw, quote_text, SAFE_SIDE + 10, center_y + 60,
                        quote_font, COLORS["paper"], max_w, line_spacing=1.5)

    # Gold line
    draw_gold_line(draw, SAFE_SIDE + 10, center_y + 60 + h + 20, 80)

    # Attribution
    if attribution:
        attr_font = load_font("dm", 24)
        draw.text((SAFE_SIDE + 10, center_y + 60 + h + 40), attribution,
                  fill=COLORS["stone"], font=attr_font)

    if output_path:
        bg.save(output_path, quality=95)
    return bg


# ============================================================
# Template: split (This or That)
# ============================================================

def template_split(image_path_1, image_path_2, label_1, label_2, question=None, output_path=None):
    """
    This or That split comparison.
    Two images stacked with labels.
    """
    canvas = Image.new("RGB", (STORY_W, STORY_H), COLORS["ink"])
    draw = ImageDraw.Draw(canvas)

    # Question at top
    if question:
        q_font = load_font("josefin-bold", 30)
        draw_text_block(draw, question.upper(), SAFE_SIDE, SAFE_TOP + 20,
                        q_font, COLORS["gold"], STORY_W - SAFE_SIDE * 2, align="center")

    # Two images
    img_h = 700
    gap = 20
    top_y = SAFE_TOP + 100

    img1 = prepare_bg(image_path_1, darken=0.1)
    img1 = img1.crop((0, (STORY_H - img_h) // 2, STORY_W, (STORY_H + img_h) // 2))
    canvas.paste(img1, (0, top_y))

    img2 = prepare_bg(image_path_2, darken=0.1)
    img2 = img2.crop((0, (STORY_H - img_h) // 2, STORY_W, (STORY_H + img_h) // 2))
    canvas.paste(img2, (0, top_y + img_h + gap))

    # Labels on each image
    draw = ImageDraw.Draw(canvas)
    label_font = load_font("josefin-bold", 28)

    # Label 1
    draw.text((SAFE_SIDE, top_y + img_h - 60), label_1.upper(),
              fill=COLORS["paper"], font=label_font)
    # Label 2
    draw.text((SAFE_SIDE, top_y + img_h + gap + img_h - 60), label_2.upper(),
              fill=COLORS["paper"], font=label_font)

    if output_path:
        canvas.save(output_path, quality=95)
    return canvas


# ============================================================
# Weekly batch generator
# ============================================================

def generate_week(project_dir, project_name, client=None, location=None,
                  architect=None, output_dir=None):
    """
    Generate 7 daily stories for one week using project images.
    Returns list of (day, template, output_path) tuples.
    """
    if output_dir is None:
        output_dir = os.path.join(project_dir, "social", "stories", "weekly")
    os.makedirs(output_dir, exist_ok=True)

    # Find available images
    orig_dir = os.path.join(project_dir, "originals")
    if not os.path.exists(orig_dir):
        print(f"Error: No originals directory at {orig_dir}")
        return []

    images = sorted([
        os.path.join(orig_dir, f) for f in os.listdir(orig_dir)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ])

    if len(images) < 7:
        print(f"Warning: Only {len(images)} images, some stories will reuse photos")
        while len(images) < 10:
            images.extend(images[:3])

    stories = []

    # Day 1: New Post teaser
    out = os.path.join(output_dir, "day1-new-post.jpg")
    template_new_post(images[0], f"{project_name}\nFull Project Reveal",
                      "See our latest post", out)
    stories.append(("Day 1", "new_post", out))

    # Day 2: Project showcase
    out = os.path.join(output_dir, "day2-project.jpg")
    template_project(images[2], project_name,
                     location or "British Columbia",
                     f"Built by {client}" if client else None, out)
    stories.append(("Day 2", "project", out))

    # Day 3: Insight
    out = os.path.join(output_dir, "day3-insight.jpg")
    template_insight(images[4],
                     "The best architectural photography\nhappens when you understand\nthe design intent before\nyou pick up the camera.",
                     "Matt Anthony Photography", out)
    stories.append(("Day 3", "insight", out))

    # Day 4: Stat
    out = os.path.join(output_dir, "day4-stat.jpg")
    template_stat(images[6], "3.1x",
                  "more engagement on carousels",
                  "Check our latest carousel to see\nwhy they outperform every time.", out)
    stories.append(("Day 4", "stat", out))

    # Day 5: Quote
    out = os.path.join(output_dir, "day5-quote.jpg")
    template_quote(images[8],
                   "Every project I photograph is someone's answer to a specific question about how to live in a specific place.",
                   "Matt Anthony", out)
    stories.append(("Day 5", "quote", out))

    # Day 6: CTA
    out = os.path.join(output_dir, "day6-cta.jpg")
    template_cta(images[10] if len(images) > 10 else images[1],
                 "Spring and summer\nshoots are booking now.",
                 "Sea-to-Sky, Sunshine Coast, Vancouver,\nFraser Valley, and Okanagan.",
                 "BOOK A DISCOVERY CALL", out)
    stories.append(("Day 6", "cta", out))

    # Day 7: This or That
    out = os.path.join(output_dir, "day7-split.jpg")
    template_split(images[3], images[7],
                   "Mountain Modern", "Coastal Retreat",
                   "Which setting would you build in?", out)
    stories.append(("Day 7", "split", out))

    print(f"\nGenerated {len(stories)} stories in {output_dir}")
    for day, tmpl, path in stories:
        print(f"  {day}: {tmpl} -> {os.path.basename(path)}")

    return stories


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Instagram Story Generator")
    sub = parser.add_subparsers(dest="command")

    # generate
    gen = sub.add_parser("generate", help="Generate a single story")
    gen.add_argument("--template", required=True,
                     choices=["new_post", "project", "insight", "stat", "cta", "quote", "split"])
    gen.add_argument("--image", required=True, help="Background image path")
    gen.add_argument("--image2", help="Second image (for split template)")
    gen.add_argument("--text", required=True, help="Primary text")
    gen.add_argument("--subtitle", help="Secondary text")
    gen.add_argument("--output", required=True, help="Output path")

    # week
    wk = sub.add_parser("week", help="Generate 7 daily stories from a project")
    wk.add_argument("--project-dir", required=True, help="Path to project folder")
    wk.add_argument("--project", required=True, help="Project name")
    wk.add_argument("--client", help="Builder/client name")
    wk.add_argument("--location", help="Location")
    wk.add_argument("--architect", help="Architect name")
    wk.add_argument("--output-dir", help="Output directory")

    # batch
    bt = sub.add_parser("batch", help="Generate stories from JSON config")
    bt.add_argument("--config", required=True, help="JSON config file")
    bt.add_argument("--output-dir", required=True, help="Output directory")

    args = parser.parse_args()

    if args.command == "generate":
        if args.template == "new_post":
            template_new_post(args.image, args.text, args.subtitle, args.output)
        elif args.template == "project":
            parts = args.text.split("|")
            template_project(args.image, parts[0].strip(),
                           parts[1].strip() if len(parts) > 1 else "BC",
                           args.subtitle, args.output)
        elif args.template == "insight":
            template_insight(args.image, args.text, args.subtitle, args.output)
        elif args.template == "stat":
            parts = args.text.split("|")
            template_stat(args.image, parts[0].strip(),
                         parts[1].strip() if len(parts) > 1 else "",
                         args.subtitle, args.output)
        elif args.template == "cta":
            template_cta(args.image, args.text, args.subtitle or "", args.output)
        elif args.template == "quote":
            template_quote(args.image, args.text, args.subtitle, args.output)
        elif args.template == "split":
            if not args.image2:
                print("Error: --image2 required for split template")
                sys.exit(1)
            parts = args.text.split("|")
            template_split(args.image, args.image2,
                          parts[0].strip(), parts[1].strip() if len(parts) > 1 else "",
                          args.subtitle, args.output)
        print(f"Story saved to {args.output}")

    elif args.command == "week":
        generate_week(args.project_dir, args.project,
                      args.client, args.location, args.architect, args.output_dir)

    elif args.command == "batch":
        with open(args.config) as f:
            config = json.load(f)
        os.makedirs(args.output_dir, exist_ok=True)
        for i, story in enumerate(config):
            tmpl = story["template"]
            out = os.path.join(args.output_dir, story.get("filename", f"story-{i+1}.jpg"))
            img = story["image"]
            text = story["text"]

            if tmpl == "new_post":
                template_new_post(img, text, story.get("subtitle"), out)
            elif tmpl == "project":
                template_project(img, text, story.get("location", "BC"),
                               story.get("builder"), out)
            elif tmpl == "insight":
                template_insight(img, text, story.get("attribution"), out)
            elif tmpl == "stat":
                template_stat(img, text, story.get("label", ""),
                            story.get("context"), out)
            elif tmpl == "cta":
                template_cta(img, text, story.get("subtext", ""),
                           story.get("cta_text", "LINK IN BIO"), out)
            elif tmpl == "quote":
                template_quote(img, text, story.get("attribution"), out)
            elif tmpl == "split":
                template_split(img, story["image2"],
                             story.get("label1", ""), story.get("label2", ""),
                             text, out)
            print(f"  Generated: {out}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
