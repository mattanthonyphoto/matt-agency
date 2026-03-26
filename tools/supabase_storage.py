"""Supabase Storage tool for uploading and managing hosted HTML files.

Usage:
    python tools/supabase_storage.py upload <file_path> [--bucket BUCKET] [--path REMOTE_PATH]
    python tools/supabase_storage.py list [--bucket BUCKET] [--prefix PREFIX]
    python tools/supabase_storage.py delete <remote_path> [--bucket BUCKET]
    python tools/supabase_storage.py url <remote_path> [--bucket BUCKET]
    python tools/supabase_storage.py setup

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env
"""

import argparse
import mimetypes
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
DEFAULT_BUCKET = "proposals"


def _headers(content_type=None):
    h = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
    }
    if content_type:
        h["Content-Type"] = content_type
    return h


def _check_config():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        print(f"  .env location: {os.path.join(BASE_DIR, '.env')}")
        print()
        print("Add these lines to your .env:")
        print("  SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co")
        print("  SUPABASE_SERVICE_ROLE_KEY=eyJ...")
        print()
        print("Get these from: Supabase Dashboard > Project Settings > API")
        sys.exit(1)


def _storage_url(path=""):
    return f"{SUPABASE_URL}/storage/v1{path}"


def ensure_bucket(bucket):
    """Create the bucket if it doesn't exist, set to public."""
    url = _storage_url("/bucket")
    resp = requests.get(url, headers=_headers())

    if resp.status_code == 200:
        existing = [b["name"] for b in resp.json()]
        if bucket in existing:
            return True

    # Create bucket
    resp = requests.post(
        url,
        headers=_headers("application/json"),
        json={
            "id": bucket,
            "name": bucket,
            "public": True,
            "file_size_limit": 10485760,  # 10MB
        },
    )

    if resp.status_code in (200, 201):
        print(f"Created public bucket: {bucket}")
        return True
    elif resp.status_code == 409:
        # Already exists
        return True
    else:
        print(f"ERROR creating bucket: {resp.status_code} — {resp.text}")
        return False


def upload_file(file_path, bucket, remote_path=None):
    """Upload a file to Supabase Storage. Returns public URL on success."""
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        return None

    if not ensure_bucket(bucket):
        return None

    # Determine remote path
    if not remote_path:
        remote_path = file_path.name

    # Detect content type
    content_type, _ = mimetypes.guess_type(str(file_path))
    if not content_type:
        content_type = "application/octet-stream"

    # Force correct types for common files
    ext = file_path.suffix.lower()
    type_map = {
        ".html": "text/html; charset=utf-8",
        ".htm": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
    }
    content_type = type_map.get(ext, content_type)

    # Upload (upsert — overwrite if exists)
    url = _storage_url(f"/object/{bucket}/{remote_path}")
    with open(file_path, "rb") as f:
        file_data = f.read()

    resp = requests.post(
        url,
        headers={
            **_headers(content_type),
            "x-upsert": "true",
        },
        data=file_data,
    )

    if resp.status_code in (200, 201):
        public_url = get_public_url(remote_path, bucket)
        file_size = len(file_data) / 1024
        print(f"Uploaded: {file_path.name} ({file_size:.1f} KB)")
        print(f"URL: {public_url}")
        return public_url
    else:
        print(f"ERROR uploading: {resp.status_code} — {resp.text}")
        return None


def list_files(bucket, prefix=""):
    """List files in a bucket."""
    _check_config()
    ensure_bucket(bucket)

    url = _storage_url(f"/object/list/{bucket}")
    body = {"prefix": prefix, "limit": 100, "offset": 0}
    resp = requests.post(url, headers=_headers("application/json"), json=body)

    if resp.status_code != 200:
        print(f"ERROR listing files: {resp.status_code} — {resp.text}")
        return []

    files = resp.json()
    if not files:
        print(f"No files in bucket '{bucket}'" + (f" with prefix '{prefix}'" if prefix else ""))
        return []

    print(f"Files in '{bucket}':" + (f" (prefix: {prefix})" if prefix else ""))
    print(f"{'Name':<50} {'Size':>10} {'Type':<25}")
    print("-" * 85)
    for f in files:
        if f.get("id"):  # Skip folder entries
            name = f.get("name", "")
            size = f.get("metadata", {}).get("size", 0)
            mime = f.get("metadata", {}).get("mimetype", "")
            size_str = f"{size / 1024:.1f} KB" if size else ""
            public_url = get_public_url(
                f"{prefix}/{name}" if prefix else name, bucket
            )
            print(f"{name:<50} {size_str:>10} {mime:<25}")
            print(f"  {public_url}")

    return files


def delete_file(remote_path, bucket):
    """Delete a file from Supabase Storage."""
    _check_config()

    url = _storage_url(f"/object/{bucket}")
    resp = requests.delete(
        url,
        headers=_headers("application/json"),
        json={"prefixes": [remote_path]},
    )

    if resp.status_code == 200:
        print(f"Deleted: {remote_path} from {bucket}")
        return True
    else:
        print(f"ERROR deleting: {resp.status_code} — {resp.text}")
        return False


def get_public_url(remote_path, bucket):
    """Get the public URL for a file."""
    return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{remote_path}"


def setup():
    """Guided setup — check config and create default bucket."""
    print("Supabase Storage Setup")
    print("=" * 40)

    if not SUPABASE_URL or not SUPABASE_KEY:
        print()
        print("Missing credentials. Add to .env:")
        print(f"  File: {os.path.join(BASE_DIR, '.env')}")
        print()
        print("  SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co")
        print("  SUPABASE_SERVICE_ROLE_KEY=eyJ...")
        print()
        print("Get these from:")
        print("  1. Go to supabase.com/dashboard")
        print("  2. Select your project (or create one)")
        print("  3. Settings > API")
        print("  4. Copy 'Project URL' and 'service_role' key")
        return

    print(f"URL: {SUPABASE_URL}")
    print(f"Key: {SUPABASE_KEY[:20]}...")
    print()

    # Test connection
    resp = requests.get(_storage_url("/bucket"), headers=_headers())
    if resp.status_code != 200:
        print(f"ERROR: Cannot connect to Supabase ({resp.status_code})")
        print("Check your SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
        return

    print(f"Connected to Supabase")
    buckets = [b["name"] for b in resp.json()]
    print(f"Existing buckets: {', '.join(buckets) if buckets else '(none)'}")
    print()

    # Create default bucket
    if ensure_bucket(DEFAULT_BUCKET):
        print(f"Default bucket '{DEFAULT_BUCKET}' is ready (public)")
    print()
    print("Setup complete. You can now upload files:")
    print(f"  python tools/supabase_storage.py upload business/sales/balmoral-retainer-proposal.html")


def main():
    parser = argparse.ArgumentParser(description="Supabase Storage manager")
    sub = parser.add_subparsers(dest="command", help="Command")

    # Upload
    p_upload = sub.add_parser("upload", help="Upload a file")
    p_upload.add_argument("file_path", help="Local file to upload")
    p_upload.add_argument("--bucket", default=DEFAULT_BUCKET, help=f"Bucket name (default: {DEFAULT_BUCKET})")
    p_upload.add_argument("--path", dest="remote_path", help="Remote path/filename (default: same as local filename)")

    # List
    p_list = sub.add_parser("list", help="List files in bucket")
    p_list.add_argument("--bucket", default=DEFAULT_BUCKET, help=f"Bucket name (default: {DEFAULT_BUCKET})")
    p_list.add_argument("--prefix", default="", help="Filter by prefix/folder")

    # Delete
    p_delete = sub.add_parser("delete", help="Delete a file")
    p_delete.add_argument("remote_path", help="Remote path to delete")
    p_delete.add_argument("--bucket", default=DEFAULT_BUCKET, help=f"Bucket name (default: {DEFAULT_BUCKET})")

    # URL
    p_url = sub.add_parser("url", help="Get public URL for a file")
    p_url.add_argument("remote_path", help="Remote path")
    p_url.add_argument("--bucket", default=DEFAULT_BUCKET, help=f"Bucket name (default: {DEFAULT_BUCKET})")

    # Setup
    sub.add_parser("setup", help="Check config and create default bucket")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "setup":
        setup()
    elif args.command == "upload":
        _check_config()
        upload_file(args.file_path, args.bucket, args.remote_path)
    elif args.command == "list":
        list_files(args.bucket, args.prefix)
    elif args.command == "delete":
        _check_config()
        delete_file(args.remote_path, args.bucket)
    elif args.command == "url":
        print(get_public_url(args.remote_path, args.bucket))


if __name__ == "__main__":
    main()
