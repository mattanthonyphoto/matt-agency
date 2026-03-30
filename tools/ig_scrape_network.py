"""Scrape your own Instagram followers/following, score against ICPs, and output prospects.

Usage:
  python3 tools/ig_scrape_network.py login              # Login and save session (do this first)
  python3 tools/ig_scrape_network.py scrape              # Scrape followers + following with bios
  python3 tools/ig_scrape_network.py score               # Score scraped profiles against ICPs
  python3 tools/ig_scrape_network.py export              # Export qualified prospects to CSV
  python3 tools/ig_scrape_network.py push                # Push top prospects to IG DM Tracker sheet

Requires: pip install instaloader
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

import instaloader

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / ".tmp" / "ig_network"
FOLLOWERS_FILE = DATA_DIR / "followers.json"
FOLLOWING_FILE = DATA_DIR / "following.json"
SCORED_FILE = DATA_DIR / "scored_prospects.json"
EXPORT_FILE = DATA_DIR / "qualified_prospects.csv"

# Your account
YOUR_USERNAME = "mattanthonyphoto"

# ---------------------------------------------------------------------------
# ICP keyword scoring
# ---------------------------------------------------------------------------

# Keywords and their ICP category + weight
ICP_KEYWORDS = {
    # Builders (primary)
    "builder": ("Builder", 10),
    "custom home": ("Builder", 10),
    "custom homes": ("Builder", 10),
    "home builder": ("Builder", 10),
    "general contractor": ("Builder", 8),
    "construction": ("Builder", 6),
    "renovations": ("Builder", 5),
    "luxury homes": ("Builder", 8),
    "new builds": ("Builder", 7),
    "framing": ("Builder", 4),
    "residential construction": ("Builder", 8),
    "design build": ("Builder", 9),
    "design-build": ("Builder", 9),

    # Architects (primary)
    "architect": ("Architect", 10),
    "architecture": ("Architect", 9),
    "architectural": ("Architect", 9),
    "aibc": ("Architect", 10),
    "raic": ("Architect", 10),
    "design studio": ("Architect", 6),

    # Interior Designers (primary)
    "interior design": ("Interior Designer", 10),
    "interior designer": ("Interior Designer", 10),
    "interiors": ("Interior Designer", 7),
    "interior styling": ("Interior Designer", 8),
    "home staging": ("Interior Designer", 6),
    "idcec": ("Interior Designer", 9),

    # Secondary ICPs
    "landscape architect": ("Landscape", 8),
    "landscape design": ("Landscape", 7),
    "landscaping": ("Landscape", 4),
    "millwork": ("Millwork", 8),
    "cabinetry": ("Millwork", 7),
    "cabinet": ("Millwork", 6),
    "woodwork": ("Millwork", 5),
    "windows": ("Windows & Doors", 6),
    "doors": ("Windows & Doors", 5),
    "fenestration": ("Windows & Doors", 8),
    "lighting design": ("Lighting", 8),
    "flooring": ("Flooring & Stone", 7),
    "stone": ("Flooring & Stone", 5),
    "tile": ("Flooring & Stone", 5),
    "hardware": ("Hardware & Fixtures", 5),
    "fixtures": ("Hardware & Fixtures", 5),
    "plumbing": ("Hardware & Fixtures", 4),

    # Real estate (low priority but worth noting)
    "real estate": ("Real Estate", 3),
    "realtor": ("Real Estate", 3),
    "realty": ("Real Estate", 3),
}

# Location signals for BC / Sea-to-Sky / Vancouver
LOCATION_KEYWORDS = [
    "vancouver", "bc", "british columbia", "squamish", "whistler",
    "north vancouver", "west vancouver", "burnaby", "surrey",
    "sea to sky", "sea-to-sky", "pemberton", "lions bay",
    "sunshine coast", "victoria", "kelowna", "kamloops",
    "langley", "white rock", "coquitlam", "port moody",
    "canada", "yvr", "pacific northwest", "pnw",
]

# Negative signals — skip these
SKIP_KEYWORDS = [
    "photographer", "photography", "videographer", "videography",
    "model", "influencer", "blogger", "podcast", "music",
    "fitness", "gym", "personal trainer", "yoga",
    "crypto", "nft", "forex", "trading",
]


def get_loader():
    """Get an Instaloader instance with session if available."""
    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )
    session_file = DATA_DIR / f"session-{YOUR_USERNAME}"
    if session_file.exists():
        L.load_session_from_file(YOUR_USERNAME, str(session_file))
        print(f"Loaded saved session for @{YOUR_USERNAME}")
    return L


def cmd_login(args):
    """Interactive login — saves session for reuse."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    L = instaloader.Instaloader(quiet=True)

    print(f"Logging in as @{YOUR_USERNAME}...")
    print("You'll be prompted for your password.")
    print("If you have 2FA, you'll be prompted for that too.\n")

    try:
        L.login(YOUR_USERNAME, input("Password: "))
    except instaloader.TwoFactorAuthRequiredException:
        # instaloader handles 2FA prompt internally in newer versions
        print("\n2FA required — check your authenticator app or SMS.")
        L.two_factor_login(input("2FA code: "))

    session_file = DATA_DIR / f"session-{YOUR_USERNAME}"
    L.save_session_to_file(str(session_file))
    print(f"\nSession saved to {session_file}")
    print("You can now run: python3 tools/ig_scrape_network.py scrape")


def cmd_scrape(args):
    """Scrape followers and following with profile info."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    L = get_loader()

    if not L.context.is_logged_in:
        print("Not logged in. Run: python3 tools/ig_scrape_network.py login")
        sys.exit(1)

    profile = instaloader.Profile.from_username(L.context, YOUR_USERNAME)
    print(f"Account: @{YOUR_USERNAME}")
    print(f"Followers: {profile.followers}")
    print(f"Following: {profile.followees}")

    # Scrape followers
    print(f"\nScraping followers...")
    followers = []
    for i, f in enumerate(profile.get_followers()):
        followers.append(_profile_to_dict(f, "follower"))
        if (i + 1) % 50 == 0:
            print(f"  ...{i + 1} followers scraped")
            # Rate limiting — Instagram gets suspicious with rapid requests
            time.sleep(2)
        elif (i + 1) % 10 == 0:
            time.sleep(0.5)

    with open(FOLLOWERS_FILE, "w") as fp:
        json.dump(followers, fp, indent=2)
    print(f"Saved {len(followers)} followers to {FOLLOWERS_FILE}")

    # Scrape following
    print(f"\nScraping following...")
    following = []
    for i, f in enumerate(profile.get_followees()):
        following.append(_profile_to_dict(f, "following"))
        if (i + 1) % 50 == 0:
            print(f"  ...{i + 1} following scraped")
            time.sleep(2)
        elif (i + 1) % 10 == 0:
            time.sleep(0.5)

    with open(FOLLOWING_FILE, "w") as fp:
        json.dump(following, fp, indent=2)
    print(f"Saved {len(following)} following to {FOLLOWING_FILE}")

    print(f"\nDone! Total profiles scraped: {len(followers) + len(following)}")
    print("Next: python3 tools/ig_scrape_network.py score")


def _profile_to_dict(profile, relationship):
    """Extract useful fields from an Instaloader Profile object."""
    return {
        "username": profile.username,
        "full_name": profile.full_name or "",
        "biography": profile.biography or "",
        "external_url": profile.external_url or "",
        "followers": profile.followers,
        "following": profile.followees,
        "is_business": profile.is_business_account,
        "business_category": profile.business_category_name or "",
        "is_verified": profile.is_verified,
        "is_private": profile.is_private,
        "posts": profile.mediacount,
        "relationship": relationship,
    }


def cmd_score(args):
    """Score scraped profiles against ICPs."""
    # Load both lists and deduplicate
    profiles = {}

    for filepath, rel in [(FOLLOWERS_FILE, "follower"), (FOLLOWING_FILE, "following")]:
        if not filepath.exists():
            print(f"Missing {filepath} — run scrape first")
            sys.exit(1)
        with open(filepath) as fp:
            for p in json.load(fp):
                username = p["username"]
                if username in profiles:
                    # Mark as mutual if in both lists
                    profiles[username]["relationship"] = "mutual"
                else:
                    profiles[username] = p

    print(f"Total unique profiles: {len(profiles)}")

    # Score each profile
    scored = []
    for username, p in profiles.items():
        searchable = f"{p['full_name']} {p['biography']} {p['business_category']}".lower()

        # Skip photographers and irrelevant accounts
        if any(kw in searchable for kw in SKIP_KEYWORDS):
            continue

        # Skip very small or likely personal accounts (< 50 posts, < 100 followers)
        if p["posts"] < 20 and p["followers"] < 100:
            continue

        # Score against ICP keywords
        best_icp = None
        best_score = 0
        all_matches = []

        for keyword, (icp, weight) in ICP_KEYWORDS.items():
            if keyword in searchable:
                all_matches.append((keyword, icp, weight))
                if weight > best_score:
                    best_score = weight
                    best_icp = icp

        if best_score == 0:
            continue

        # Location bonus
        location_match = any(loc in searchable for loc in LOCATION_KEYWORDS)
        if location_match:
            best_score += 5

        # Business account bonus
        if p["is_business"]:
            best_score += 2

        # Engagement potential (not too big, not too small)
        if 500 <= p["followers"] <= 50000:
            best_score += 2

        scored.append({
            **p,
            "icp": best_icp,
            "score": best_score,
            "location_match": location_match,
            "keyword_matches": [(kw, icp) for kw, icp, _ in all_matches],
        })

    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)

    with open(SCORED_FILE, "w") as fp:
        json.dump(scored, fp, indent=2)

    # Summary
    icp_counts = {}
    for p in scored:
        icp_counts[p["icp"]] = icp_counts.get(p["icp"], 0) + 1

    print(f"\nQualified prospects: {len(scored)}")
    print(f"\nBy ICP:")
    for icp, count in sorted(icp_counts.items(), key=lambda x: -x[1]):
        print(f"  {icp}: {count}")

    bc_count = sum(1 for p in scored if p["location_match"])
    mutual_count = sum(1 for p in scored if p["relationship"] == "mutual")
    print(f"\nBC/PNW located: {bc_count}")
    print(f"Mutual follows: {mutual_count}")
    print(f"\nTop 20 prospects:")
    for p in scored[:20]:
        loc = " [BC]" if p["location_match"] else ""
        rel = f" ({p['relationship']})"
        print(f"  {p['score']:3d} | @{p['username']:25s} | {p['icp']:20s} | {p['full_name']}{loc}{rel}")

    print(f"\nNext: python3 tools/ig_scrape_network.py export")


def cmd_export(args):
    """Export qualified prospects to CSV."""
    if not SCORED_FILE.exists():
        print("No scored data. Run: python3 tools/ig_scrape_network.py score")
        sys.exit(1)

    with open(SCORED_FILE) as fp:
        scored = json.load(fp)

    # Filter: score >= 8 for "qualified"
    min_score = args.min_score if hasattr(args, 'min_score') else 8
    qualified = [p for p in scored if p["score"] >= min_score]

    with open(EXPORT_FILE, "w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=[
            "username", "full_name", "icp", "score", "relationship",
            "location_match", "biography", "external_url", "followers",
            "is_business", "business_category", "posts",
        ])
        writer.writeheader()
        for p in qualified:
            writer.writerow({
                "username": p["username"],
                "full_name": p["full_name"],
                "icp": p["icp"],
                "score": p["score"],
                "relationship": p["relationship"],
                "location_match": p["location_match"],
                "biography": p["biography"],
                "external_url": p["external_url"],
                "followers": p["followers"],
                "is_business": p["is_business"],
                "business_category": p["business_category"],
                "posts": p["posts"],
            })

    print(f"Exported {len(qualified)} qualified prospects (score >= {min_score}) to {EXPORT_FILE}")

    # Quick breakdown
    icp_counts = {}
    for p in qualified:
        icp_counts[p["icp"]] = icp_counts.get(p["icp"], 0) + 1
    for icp, count in sorted(icp_counts.items(), key=lambda x: -x[1]):
        print(f"  {icp}: {count}")


def cmd_push(args):
    """Push qualified prospects to the IG DM Tracker Google Sheet."""
    if not SCORED_FILE.exists():
        print("No scored data. Run score first.")
        sys.exit(1)

    with open(SCORED_FILE) as fp:
        scored = json.load(fp)

    min_score = args.min_score if hasattr(args, 'min_score') else 10
    qualified = [p for p in scored if p["score"] >= min_score]

    print(f"Found {len(qualified)} prospects with score >= {min_score}")
    print("Pushing to IG DM Tracker via ig_dm_tracker.py add-prospect...\n")

    # Import the tracker's add function
    sys.path.insert(0, str(PROJECT_ROOT / "tools"))
    import subprocess

    for p in qualified:
        cmd = [
            sys.executable, str(PROJECT_ROOT / "tools" / "ig_dm_tracker.py"),
            "add-prospect",
            "--handle", p["username"],
            "--name", p["full_name"] or p["username"],
            "--icp", p["icp"],
            "--source", f"ig-{p['relationship']}",
        ]
        if p.get("external_url"):
            cmd.extend(["--website", p["external_url"]])

        result = subprocess.run(cmd, capture_output=True, text=True)
        status = "OK" if result.returncode == 0 else "FAIL"
        print(f"  [{status}] @{p['username']} ({p['icp']}, score {p['score']})")

    print(f"\nDone! {len(qualified)} prospects added to IG DM Tracker.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Scrape your IG network and find prospects")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("login", help="Login to Instagram and save session")
    sub.add_parser("scrape", help="Scrape followers + following with bios")
    sub.add_parser("score", help="Score profiles against ICPs")

    export_p = sub.add_parser("export", help="Export qualified prospects to CSV")
    export_p.add_argument("--min-score", type=int, default=8)

    push_p = sub.add_parser("push", help="Push top prospects to IG DM Tracker sheet")
    push_p.add_argument("--min-score", type=int, default=10)

    args = parser.parse_args()

    if args.command == "login":
        cmd_login(args)
    elif args.command == "scrape":
        cmd_scrape(args)
    elif args.command == "score":
        cmd_score(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "push":
        cmd_push(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
