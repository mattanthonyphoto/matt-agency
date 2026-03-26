"""Social media image pipeline — analyzes and processes project photos for all platforms.

Uses Claude Vision to analyze each image and determine the best crop strategy,
then generates platform-optimized exports that respect the original composition.

Subcommands:
  analyze      Analyze images and generate a processing manifest
  process      Process images using the manifest (or auto-analyze first)
  batch        Full pipeline: analyze + process all images in a folder

Usage:
  # Full pipeline — analyze and process in one step
  python tools/resize_images.py batch \
    --input-dir ./originals/ \
    --output-dir ./social/ \
    --seo-prefix "the-perch-sunshine-coast-bc"

  # Two-step — analyze first, review manifest, then process
  python tools/resize_images.py analyze \
    --input-dir ./originals/ \
    --output manifest.json

  python tools/resize_images.py process \
    --manifest manifest.json \
    --output-dir ./social/
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageFilter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ── Instagram format specs ──────────────────────────────────

IG_FORMATS = {
    "portrait": {"width": 1080, "height": 1350, "ratio": "4:5"},
    "square": {"width": 1080, "height": 1080, "ratio": "1:1"},
    "landscape": {"width": 1080, "height": 566, "ratio": "1.91:1"},
}

# ── All output specs ────────────────────────────────────────

OUTPUT_SPECS = {
    "ig_feed": {"quality": 92, "max_side": 1080},
    "ig_story": {"width": 1080, "height": 1920, "quality": 90},
    "linkedin": {"width": 1200, "height": 628, "quality": 92},
    "linkedin_carousel": {"width": 1080, "height": 1350, "quality": 92},
    "pinterest": {"width": 1000, "height": 1500, "quality": 92},
    "web": {"width": 1600, "height": 900, "quality": 88},
}


def encode_image_b64(path, max_dim=1024):
    """Encode an image to base64 for Claude Vision, resized to save tokens."""
    img = Image.open(path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    import io
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75)
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def analyze_images_with_vision(image_paths):
    """Use Claude Vision to analyze each image and recommend crop strategies."""
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    results = []
    # Process in batches of 5 to stay within limits
    batch_size = 5
    for batch_start in range(0, len(image_paths), batch_size):
        batch = image_paths[batch_start:batch_start + batch_size]
        content = []

        for i, path in enumerate(batch):
            img = Image.open(path)
            w, h = img.size
            orientation = "landscape" if w > h else ("portrait" if h > w else "square")

            content.append({
                "type": "text",
                "text": f"IMAGE {batch_start + i + 1}: {path.name} ({w}x{h}, {orientation})"
            })
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": encode_image_b64(path),
                }
            })

        content.append({
            "type": "text",
            "text": """For each image above, return a JSON array with one object per image:
{
  "filename": "the filename",
  "subject": "brief description of main subject/focal point",
  "composition": "wide_landscape" | "standard_landscape" | "portrait" | "detail_close" | "aerial",
  "ig_best_format": "landscape" | "square" | "portrait",
  "crop_gravity": "center" | "left" | "right" | "top" | "bottom" | "top_left" | "top_right" | "bottom_left" | "bottom_right",
  "crop_notes": "what to protect when cropping — e.g. 'keep fire pit in lower left and full building'",
  "pinterest_viable": true/false (does this image work as a 2:3 vertical pin without losing the subject?),
  "story_viable": true/false (does this image work as 9:16 vertical without major loss?),
  "hero_score": 1-10 (how strong is this as a standalone post or carousel opener?),
  "category": "exterior" | "interior" | "detail" | "aerial" | "twilight" | "lifestyle"
}

Rules:
- Wide panoramic landscapes should be ig_best_format "landscape" — never force to portrait
- Interiors with strong vertical lines can go portrait
- Aerials are usually landscape or square
- hero_score 8-10 = carousel opener or standalone post, 5-7 = carousel filler, 1-4 = Pinterest/web only
- crop_gravity tells the crop algorithm where the subject weight is

Return ONLY the JSON array, no markdown fences."""
        })

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": content}]
        )

        batch_results = json.loads(response.content[0].text)
        results.extend(batch_results)
        print(f"  Analyzed {min(batch_start + batch_size, len(image_paths))}/{len(image_paths)} images...")

    return results


def gravity_crop(img, target_w, target_h, gravity="center"):
    """Crop image to target aspect ratio using gravity-based positioning."""
    img_w, img_h = img.size
    target_ratio = target_w / target_h
    img_ratio = img_w / img_h

    if abs(img_ratio - target_ratio) < 0.01:
        return img.resize((target_w, target_h), Image.LANCZOS)

    if img_ratio > target_ratio:
        # Wider than target — crop sides
        new_w = int(img_h * target_ratio)
        if gravity in ("left", "top_left", "bottom_left"):
            left = 0
        elif gravity in ("right", "top_right", "bottom_right"):
            left = img_w - new_w
        else:
            left = (img_w - new_w) // 2
        crop_box = (left, 0, left + new_w, img_h)
    else:
        # Taller than target — crop top/bottom
        new_h = int(img_w / target_ratio)
        if gravity in ("top", "top_left", "top_right"):
            top = 0
        elif gravity in ("bottom", "bottom_left", "bottom_right"):
            top = img_h - new_h
        else:
            top = (img_h - new_h) // 2
        crop_box = (0, top, img_w, top + new_h)

    cropped = img.crop(crop_box)
    return cropped.resize((target_w, target_h), Image.LANCZOS)


def letterbox(img, target_w, target_h, bg_color=None):
    """Fit image inside target dimensions with blurred background fill."""
    img_w, img_h = img.size
    scale = min(target_w / img_w, target_h / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    resized = img.resize((new_w, new_h), Image.LANCZOS)

    if bg_color:
        canvas = Image.new("RGB", (target_w, target_h), bg_color)
    else:
        # Blurred background from the image itself
        bg = img.resize((target_w, target_h), Image.LANCZOS)
        canvas = bg.filter(ImageFilter.GaussianBlur(radius=40))
        # Darken the blur slightly
        from PIL import ImageEnhance
        canvas = ImageEnhance.Brightness(canvas).enhance(0.4)

    x = (target_w - new_w) // 2
    y = (target_h - new_h) // 2
    canvas.paste(resized, (x, y))
    return canvas


def process_image(img_path, analysis, output_dir, seo_name):
    """Process a single image based on its analysis."""
    img = Image.open(img_path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    gravity = analysis.get("crop_gravity", "center")
    ig_format = analysis.get("ig_best_format", "portrait")
    pin_viable = analysis.get("pinterest_viable", True)
    story_viable = analysis.get("story_viable", False)
    outputs = {}

    # ── Instagram Feed ──
    ig_spec = IG_FORMATS[ig_format]
    ig_dir = output_dir / "instagram"
    ig_dir.mkdir(parents=True, exist_ok=True)
    ig_img = gravity_crop(img, ig_spec["width"], ig_spec["height"], gravity)
    ig_path = ig_dir / f"{seo_name}.jpg"
    ig_img.save(ig_path, "JPEG", quality=92, optimize=True)
    outputs["instagram"] = {"path": str(ig_path), "format": ig_format, "size": f"{ig_spec['width']}x{ig_spec['height']}"}

    # ── Instagram Story (only if viable, otherwise letterbox) ──
    story_dir = output_dir / "stories"
    story_dir.mkdir(parents=True, exist_ok=True)
    if story_viable:
        story_img = gravity_crop(img, 1080, 1920, gravity)
    else:
        story_img = letterbox(img, 1080, 1920)
    story_path = story_dir / f"{seo_name}.jpg"
    story_img.save(story_path, "JPEG", quality=90, optimize=True)
    outputs["story"] = {"path": str(story_path), "letterboxed": not story_viable}

    # ── LinkedIn ──
    li_dir = output_dir / "linkedin"
    li_dir.mkdir(parents=True, exist_ok=True)
    li_img = gravity_crop(img, 1200, 628, gravity)
    li_path = li_dir / f"{seo_name}.jpg"
    li_img.save(li_path, "JPEG", quality=92, optimize=True)
    outputs["linkedin"] = {"path": str(li_path), "size": "1200x628"}

    # ── Pinterest (only if the image works vertically) ──
    if pin_viable:
        pin_dir = output_dir / "pinterest"
        pin_dir.mkdir(parents=True, exist_ok=True)
        pin_img = gravity_crop(img, 1000, 1500, gravity)
        pin_path = pin_dir / f"{seo_name}.jpg"
        pin_img.save(pin_path, "JPEG", quality=92, optimize=True)
        outputs["pinterest"] = {"path": str(pin_path), "size": "1000x1500"}

    # ── Web / Journal ──
    web_dir = output_dir / "web"
    web_dir.mkdir(parents=True, exist_ok=True)
    web_img = gravity_crop(img, 1600, 900, gravity)
    web_path = web_dir / f"{seo_name}.jpg"
    web_img.save(web_path, "JPEG", quality=88, optimize=True)
    outputs["web"] = {"path": str(web_path), "size": "1600x900"}

    return outputs


# ── CLI Commands ────────────────────────────────────────────


def cmd_analyze(args):
    """Analyze images and generate a manifest."""
    input_dir = Path(args.input_dir)
    extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
    images = sorted([f for f in input_dir.iterdir() if f.suffix.lower() in extensions])

    if not images:
        print(f"No images found in {input_dir}")
        return 1

    print(f"Analyzing {len(images)} images with Claude Vision...")
    analyses = analyze_images_with_vision(images)

    # Attach file paths
    for i, a in enumerate(analyses):
        a["source_path"] = str(images[i])

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(analyses, f, indent=2)

    print(f"\nManifest saved to {output_path}")
    print(f"\nSummary:")

    # Print summary table
    for a in analyses:
        hero = a.get("hero_score", 0)
        star = " ***" if hero >= 8 else ""
        print(f"  [{hero:>2}/10] {a['filename'][:50]:50s} IG:{a['ig_best_format']:9s} gravity:{a['crop_gravity']:12s} pin:{str(a.get('pinterest_viable', '?')):5s}{star}")

    hero_count = sum(1 for a in analyses if a.get("hero_score", 0) >= 8)
    print(f"\n  {hero_count} hero images (8+), {len(analyses)} total")
    return 0


def cmd_process(args):
    """Process images using a manifest."""
    manifest_path = Path(args.manifest)
    output_dir = Path(args.output_dir)

    with open(manifest_path) as f:
        analyses = json.load(f)

    print(f"Processing {len(analyses)} images...")
    print(f"Output: {output_dir}\n")

    all_outputs = []
    for i, analysis in enumerate(analyses, 1):
        source = Path(analysis["source_path"])
        seo_name = args.seo_prefix + f"-{i:02d}" if args.seo_prefix else source.stem

        print(f"[{i}/{len(analyses)}] {source.name}")
        hero = analysis.get("hero_score", 0)
        ig_fmt = analysis.get("ig_best_format", "portrait")
        print(f"  IG: {ig_fmt}, gravity: {analysis.get('crop_gravity', 'center')}, hero: {hero}/10")

        outputs = process_image(source, analysis, output_dir, seo_name)

        for platform, info in outputs.items():
            kb = Path(info["path"]).stat().st_size / 1024
            extra = f" ({info.get('format', info.get('size', ''))})"
            lb = " [letterboxed]" if info.get("letterboxed") else ""
            print(f"    {platform:12s} {kb:>6.0f} KB{extra}{lb}")

        analysis["outputs"] = outputs
        analysis["seo_name"] = seo_name
        all_outputs.append(analysis)
        print()

    # Save updated manifest with output paths
    result_path = output_dir / "manifest.json"
    with open(result_path, "w") as f:
        json.dump(all_outputs, f, indent=2)

    # Print posting recommendations
    print("=" * 60)
    print("POSTING RECOMMENDATIONS")
    print("=" * 60)

    heroes = [a for a in all_outputs if a.get("hero_score", 0) >= 8]
    carousel = [a for a in all_outputs if a.get("hero_score", 0) >= 5]
    pin_images = [a for a in all_outputs if a.get("pinterest_viable")]

    print(f"\nHero shots (standalone posts / carousel openers): {len(heroes)}")
    for a in heroes:
        print(f"  [{a['hero_score']}/10] {a['seo_name']} — {a.get('subject', '')}")

    print(f"\nCarousel-worthy (5+ score): {len(carousel)}")
    print(f"Pinterest-viable: {len(pin_images)}")

    ig_formats = {}
    for a in all_outputs:
        fmt = a.get("ig_best_format", "unknown")
        ig_formats[fmt] = ig_formats.get(fmt, 0) + 1
    print(f"\nIG format breakdown: {', '.join(f'{k}: {v}' for k, v in ig_formats.items())}")

    print(f"\nManifest with all paths: {result_path}")
    return 0


def cmd_batch(args):
    """Full pipeline: analyze + process."""
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
    images = sorted([f for f in input_dir.iterdir() if f.suffix.lower() in extensions])

    if not images:
        print(f"No images found in {input_dir}")
        return 1

    print(f"Found {len(images)} images in {input_dir}")
    print(f"Output: {output_dir}\n")

    # Step 1: Analyze
    print("Step 1: Analyzing images with Claude Vision...")
    analyses = analyze_images_with_vision(images)

    for i, a in enumerate(analyses):
        a["source_path"] = str(images[i])

    print()

    # Step 2: Process
    print("Step 2: Processing images...\n")
    all_outputs = []
    for i, analysis in enumerate(analyses, 1):
        source = Path(analysis["source_path"])
        seo_name = args.seo_prefix + f"-{i:02d}" if args.seo_prefix else source.stem

        print(f"[{i}/{len(images)}] {source.name}")
        hero = analysis.get("hero_score", 0)
        ig_fmt = analysis.get("ig_best_format", "portrait")
        print(f"  IG: {ig_fmt}, gravity: {analysis.get('crop_gravity', 'center')}, hero: {hero}/10")

        outputs = process_image(source, analysis, output_dir, seo_name)

        for platform, info in outputs.items():
            kb = Path(info["path"]).stat().st_size / 1024
            extra = f" ({info.get('format', info.get('size', ''))})"
            lb = " [letterboxed]" if info.get("letterboxed") else ""
            print(f"    {platform:12s} {kb:>6.0f} KB{extra}{lb}")

        analysis["outputs"] = outputs
        analysis["seo_name"] = seo_name
        all_outputs.append(analysis)
        print()

    # Save manifest
    result_path = output_dir / "manifest.json"
    with open(result_path, "w") as f:
        json.dump(all_outputs, f, indent=2)

    # Print summary
    print("=" * 60)
    print("POSTING RECOMMENDATIONS")
    print("=" * 60)

    heroes = [a for a in all_outputs if a.get("hero_score", 0) >= 8]
    carousel = [a for a in all_outputs if a.get("hero_score", 0) >= 5]
    pin_images = [a for a in all_outputs if a.get("pinterest_viable")]

    print(f"\nHero shots (standalone posts / carousel openers): {len(heroes)}")
    for a in heroes:
        print(f"  [{a['hero_score']}/10] {a['seo_name']} — {a.get('subject', '')}")

    print(f"\nCarousel-worthy (5+ score): {len(carousel)}")
    print(f"Pinterest-viable: {len(pin_images)}")

    ig_formats = {}
    for a in all_outputs:
        fmt = a.get("ig_best_format", "unknown")
        ig_formats[fmt] = ig_formats.get(fmt, 0) + 1
    print(f"\nIG format breakdown: {', '.join(f'{k}: {v}' for k, v in ig_formats.items())}")

    categories = {}
    for a in all_outputs:
        cat = a.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    print(f"Categories: {', '.join(f'{k}: {v}' for k, v in categories.items())}")

    print(f"\nAll outputs in: {output_dir}")
    print(f"Manifest: {result_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Smart social media image pipeline with AI-powered crop analysis"
    )
    sub = parser.add_subparsers(dest="command")

    # --- analyze ---
    an = sub.add_parser("analyze", help="Analyze images and generate crop manifest")
    an.add_argument("--input-dir", required=True, help="Directory of source images")
    an.add_argument("--output", default="manifest.json", help="Output manifest path")

    # --- process ---
    pr = sub.add_parser("process", help="Process images using a manifest")
    pr.add_argument("--manifest", required=True, help="Path to analysis manifest")
    pr.add_argument("--output-dir", required=True, help="Output directory")
    pr.add_argument("--seo-prefix", help="SEO filename prefix")

    # --- batch ---
    ba = sub.add_parser("batch", help="Full pipeline: analyze + process")
    ba.add_argument("--input-dir", required=True, help="Directory of source images")
    ba.add_argument("--output-dir", required=True, help="Output directory")
    ba.add_argument("--seo-prefix", help="SEO filename prefix")

    args = parser.parse_args()

    if args.command == "analyze":
        return cmd_analyze(args)
    elif args.command == "process":
        return cmd_process(args)
    elif args.command == "batch":
        return cmd_batch(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
