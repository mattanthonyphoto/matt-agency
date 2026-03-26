"""Publish HTML proposals to GitHub Pages.

Usage:
    python3 tools/publish_proposal.py upload <file_path> --client <slug> --name <filename>
    python3 tools/publish_proposal.py list [--client <slug>]
    python3 tools/publish_proposal.py url <client>/<filename>
    python3 tools/publish_proposal.py delete <client>/<filename>

Publishes to: https://mattanthonyphoto.github.io/matt-proposals/{client}/{filename}
Repo: github.com/mattanthonyphoto/matt-proposals
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = "mattanthonyphoto/matt-proposals"
PAGES_URL = "https://mattanthonyphoto.github.io/matt-proposals"
CLONE_DIR = "/tmp/matt-proposals"


def _run(cmd, cwd=None, check=True):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=isinstance(cmd, str))
    if check and result.returncode != 0:
        print(f"ERROR: {result.stderr.strip()}")
        sys.exit(1)
    return result


def _clone_repo():
    """Clone or pull the latest repo."""
    if os.path.exists(CLONE_DIR):
        _run("git pull origin main", cwd=CLONE_DIR)
    else:
        _run(f"gh repo clone {REPO} {CLONE_DIR}")


def upload(file_path, client, name):
    """Upload a file to the proposals repo."""
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        return None

    _clone_repo()

    # Create client directory
    client_dir = os.path.join(CLONE_DIR, client)
    os.makedirs(client_dir, exist_ok=True)

    # Copy file
    dest = os.path.join(client_dir, name)
    shutil.copy2(file_path, dest)

    # Commit and push
    _run("git add -A", cwd=CLONE_DIR)

    # Check if there are changes to commit
    status = _run("git status --porcelain", cwd=CLONE_DIR)
    if not status.stdout.strip():
        url = f"{PAGES_URL}/{client}/{name}"
        print(f"No changes — file already up to date")
        print(f"URL: {url}")
        return url

    _run(f'git commit -m "Update {client}/{name}"', cwd=CLONE_DIR)
    _run("git push origin main", cwd=CLONE_DIR)

    url = f"{PAGES_URL}/{client}/{name}"
    size = file_path.stat().st_size / 1024
    print(f"Published: {client}/{name} ({size:.1f} KB)")
    print(f"URL: {url}")
    print(f"(May take 30-60 seconds for GitHub Pages to update)")
    return url


def list_files(client=None):
    """List published files."""
    _clone_repo()

    base = os.path.join(CLONE_DIR, client) if client else CLONE_DIR
    if not os.path.exists(base):
        print(f"No files found" + (f" for client '{client}'" if client else ""))
        return

    print(f"Published proposals:")
    print("-" * 70)
    for root, dirs, files in os.walk(base):
        # Skip .git and root index
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in sorted(files):
            if f == "index.html" and root == CLONE_DIR:
                continue
            rel = os.path.relpath(os.path.join(root, f), CLONE_DIR)
            size = os.path.getsize(os.path.join(root, f)) / 1024
            url = f"{PAGES_URL}/{rel}"
            print(f"  {rel:<50} {size:>6.1f} KB")
            print(f"  {url}")
            print()


def delete(remote_path):
    """Delete a published file."""
    _clone_repo()

    full_path = os.path.join(CLONE_DIR, remote_path)
    if not os.path.exists(full_path):
        print(f"ERROR: File not found: {remote_path}")
        return False

    os.remove(full_path)
    _run("git add -A", cwd=CLONE_DIR)
    _run(f'git commit -m "Remove {remote_path}"', cwd=CLONE_DIR)
    _run("git push origin main", cwd=CLONE_DIR)
    print(f"Deleted: {remote_path}")
    return True


def get_url(remote_path):
    """Get the public URL for a file."""
    url = f"{PAGES_URL}/{remote_path}"
    print(url)
    return url


def main():
    parser = argparse.ArgumentParser(description="Publish proposals to GitHub Pages")
    sub = parser.add_subparsers(dest="command")

    p_upload = sub.add_parser("upload", help="Publish a proposal")
    p_upload.add_argument("file_path", help="Local HTML file")
    p_upload.add_argument("--client", required=True, help="Client slug (e.g. balmoral)")
    p_upload.add_argument("--name", required=True, help="Filename (e.g. creative-partner-proposal.html)")

    p_list = sub.add_parser("list", help="List published files")
    p_list.add_argument("--client", help="Filter by client")

    p_url = sub.add_parser("url", help="Get public URL")
    p_url.add_argument("remote_path", help="Path (e.g. balmoral/proposal.html)")

    p_delete = sub.add_parser("delete", help="Delete a published file")
    p_delete.add_argument("remote_path", help="Path to delete")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "upload":
        upload(args.file_path, args.client, args.name)
    elif args.command == "list":
        list_files(args.client)
    elif args.command == "url":
        get_url(args.remote_path)
    elif args.command == "delete":
        delete(args.remote_path)


if __name__ == "__main__":
    main()
