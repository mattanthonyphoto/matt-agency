#!/usr/bin/env python3
"""
Download all Squarespace CDN images referenced in the site code blocks.
Extracts unique URLs, downloads them, and creates a mapping file for URL rewriting.

Usage:
    python tools/download-site-images.py                  # Extract URLs only (dry run)
    python tools/download-site-images.py --download       # Download all images
    python tools/download-site-images.py --download --dir ./images  # Custom output dir
"""

import re
import os
import json
import hashlib
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
CODE_BLOCKS = ROOT / "business" / "website" / "code-blocks"
DEFAULT_IMAGE_DIR = ROOT / ".tmp" / "site-images"
MAPPING_FILE = ROOT / "business" / "website" / "image-mapping.json"

# Match Squarespace CDN URLs
SQS_PATTERN = re.compile(r'https://images\.squarespace-cdn\.com/content/[^"\'>\s)]+')


def extract_all_urls():
    """Extract all unique Squarespace image URLs from code blocks."""
    urls = set()
    file_refs = defaultdict(list)  # url -> list of files that reference it

    for html_file in CODE_BLOCKS.rglob("*.html"):
        content = html_file.read_text()
        matches = SQS_PATTERN.findall(content)
        for url in matches:
            urls.add(url)
            rel_path = str(html_file.relative_to(CODE_BLOCKS))
            if rel_path not in file_refs[url]:
                file_refs[url].append(rel_path)

    return urls, file_refs


def url_to_filename(url):
    """Extract clean filename from Squarespace URL."""
    # Get the path part, strip query params
    path = url.split("?")[0]
    parts = path.split("/")
    filename = parts[-1]

    # If filename is empty or just a hash, use hash of full URL
    if not filename or len(filename) < 5:
        h = hashlib.md5(url.encode()).hexdigest()[:12]
        filename = f"image-{h}.jpg"

    return filename


def download_image(url, output_dir):
    """Download a single image. Returns (filename, success)."""
    filename = url_to_filename(url)
    output_path = output_dir / filename

    # Skip if already downloaded
    if output_path.exists() and output_path.stat().st_size > 0:
        return filename, True

    # Strip format parameter for highest quality download
    clean_url = url.split("?")[0]

    try:
        req = urllib.request.Request(clean_url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
            output_path.write_bytes(data)
            size_kb = len(data) / 1024
            return filename, True
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        print(f"  FAILED: {filename} — {e}")
        return filename, False


def main():
    parser = argparse.ArgumentParser(description="Download Squarespace images")
    parser.add_argument("--download", action="store_true", help="Actually download images")
    parser.add_argument("--dir", type=str, help="Output directory for images")
    args = parser.parse_args()

    output_dir = Path(args.dir) if args.dir else DEFAULT_IMAGE_DIR

    print("Scanning code blocks for Squarespace image URLs...")
    urls, file_refs = extract_all_urls()

    print(f"\nFound {len(urls)} unique image URLs across {sum(len(v) for v in file_refs.values())} references\n")

    # Deduplicate by filename (same image referenced with different format params)
    filename_map = {}  # filename -> canonical URL
    url_to_file = {}   # full URL -> filename

    for url in sorted(urls):
        filename = url_to_filename(url)
        if filename not in filename_map:
            filename_map[filename] = url
        url_to_file[url] = filename

    unique_files = len(filename_map)
    print(f"Unique filenames: {unique_files} (some URLs point to same image with different format params)\n")

    if not args.download:
        # Dry run — just show what would be downloaded
        print("Top 20 images by reference count:")
        by_count = sorted(file_refs.items(), key=lambda x: len(x[1]), reverse=True)
        for url, refs in by_count[:20]:
            fn = url_to_filename(url)
            print(f"  {fn} — referenced in {len(refs)} files")

        print(f"\nRun with --download to download all {unique_files} images")
        print(f"Output directory: {output_dir}")

        # Save mapping even in dry run
        mapping = {url: url_to_file[url] for url in sorted(urls)}
        MAPPING_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(MAPPING_FILE, "w") as f:
            json.dump(mapping, f, indent=2)
        print(f"URL mapping saved to: {MAPPING_FILE}")
        return

    # Download
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading to: {output_dir}\n")

    success = 0
    failed = 0
    skipped = 0

    for i, (filename, canonical_url) in enumerate(sorted(filename_map.items()), 1):
        output_path = output_dir / filename
        if output_path.exists() and output_path.stat().st_size > 0:
            skipped += 1
            continue

        fname, ok = download_image(canonical_url, output_dir)
        if ok:
            success += 1
            size = (output_dir / fname).stat().st_size / 1024
            print(f"  [{i}/{unique_files}] {fname} ({size:.0f}KB)")
        else:
            failed += 1

    # Save mapping
    mapping = {url: url_to_file[url] for url in sorted(urls)}
    with open(MAPPING_FILE, "w") as f:
        json.dump(mapping, f, indent=2)

    total_size = sum(f.stat().st_size for f in output_dir.iterdir() if f.is_file()) / (1024 * 1024)

    print(f"\nDone!")
    print(f"  Downloaded: {success}")
    print(f"  Skipped (already exists): {skipped}")
    print(f"  Failed: {failed}")
    print(f"  Total size: {total_size:.1f}MB")
    print(f"  Output: {output_dir}")
    print(f"  Mapping: {MAPPING_FILE}")


if __name__ == "__main__":
    main()
