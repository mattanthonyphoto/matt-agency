"""Content calendar — creates and manages the Google Sheet that serves as
the operational backbone for social media scheduling.

Subcommands:
  create       Create a new content calendar Google Sheet with all tabs/formatting
  populate     Push a project's content plan into the calendar
  status       Show current calendar status (scheduled, overdue, gaps)

Usage:
  python tools/content_calendar.py create \
    --title "Matt Anthony — Content Calendar 2026"

  python tools/content_calendar.py populate \
    --sheet-id "YOUR_SHEET_ID" \
    --project-dir "Photo Assets/Summerhill Fine Homes/The Perch"

  python tools/content_calendar.py status \
    --sheet-id "YOUR_SHEET_ID"
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

# ── Google Sheets auth ──────────────────────────────────────

def get_sheets_service():
    """Authenticate and return Google Sheets API service."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = None
    token_path = PROJECT_ROOT / "token.json"
    creds_path = PROJECT_ROOT / "credentials.json"

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())

    return build("sheets", "v4", credentials=creds)


# ── Calendar structure ──────────────────────────────────────

CALENDAR_HEADERS = [
    "Date",              # A
    "Day",               # B
    "Time",              # C
    "Platform",          # D
    "Type",              # E
    "Pillar",            # F
    "Project",           # G
    "Description",       # H
    "Caption",           # I
    "Hashtag Set",       # J
    "Image Files",       # K
    "Status",            # L - NEW / DRAFT / REVIEW / APPROVED / SCHEDULED / PUBLISHED
    "Requires Manual",   # M
    "Manual Notes",      # N
    "IG Engagement",     # O
    "IG Saves",          # P
    "IG Shares",         # Q
    "LI Impressions",    # R
    "Pin Clicks",        # S
    "Notes",             # T
]

DASHBOARD_HEADERS = [
    "Metric", "This Week", "Last Week", "Change", "Target", "Status"
]

IDEAS_HEADERS = [
    "Idea", "Platform", "Type", "Pillar", "Priority", "Project", "Notes", "Added"
]

STATUS_COLORS = {
    "NEW": {"red": 0.85, "green": 0.92, "blue": 1.0},        # Light blue
    "DRAFT": {"red": 1.0, "green": 0.95, "blue": 0.8},       # Light yellow
    "REVIEW": {"red": 1.0, "green": 0.88, "blue": 0.7},      # Orange-ish
    "APPROVED": {"red": 0.8, "green": 0.95, "blue": 0.8},    # Light green
    "SCHEDULED": {"red": 0.85, "green": 0.8, "blue": 0.95},  # Light purple
    "PUBLISHED": {"red": 0.9, "green": 0.9, "blue": 0.9},    # Light grey
}


def cmd_create(args):
    """Create a new content calendar Google Sheet."""
    service = get_sheets_service()

    # Create the spreadsheet
    spreadsheet = {
        "properties": {"title": args.title or "Content Calendar 2026"},
        "sheets": [
            {"properties": {"title": "Content Calendar", "index": 0}},
            {"properties": {"title": "Dashboard", "index": 1}},
            {"properties": {"title": "Ideas Bank", "index": 2}},
            {"properties": {"title": "Analytics", "index": 3}},
        ]
    }

    result = service.spreadsheets().create(body=spreadsheet).execute()
    sheet_id = result["spreadsheetId"]
    print(f"Created spreadsheet: {sheet_id}")
    print(f"URL: https://docs.google.com/spreadsheets/d/{sheet_id}")

    # Get sheet IDs for formatting
    sheets_meta = result.get("sheets", [])
    tab_ids = {s["properties"]["title"]: s["properties"]["sheetId"] for s in sheets_meta}

    # ── Write headers ──
    batch_data = [
        {
            "range": "'Content Calendar'!A1",
            "values": [CALENDAR_HEADERS],
        },
        {
            "range": "'Dashboard'!A1",
            "values": [
                DASHBOARD_HEADERS,
                ["Posts This Week", "", "", "", "14", ""],
                ["IG Posts", "", "", "", "5", ""],
                ["LI Posts", "", "", "", "4", ""],
                ["Pinterest Pins", "", "", "", "20", ""],
                ["Avg IG Engagement", "", "", "", "3%", ""],
                ["Avg IG Saves", "", "", "", "15", ""],
                ["LI Impressions (weekly)", "", "", "", "500", ""],
                ["Website Traffic from Social", "", "", "", "50", ""],
                ["", "", "", "", "", ""],
                ["Content Queue Depth", "", "", "", "14 days", ""],
                ["Projects in Pipeline", "", "", "", "", ""],
            ],
        },
        {
            "range": "'Ideas Bank'!A1",
            "values": [IDEAS_HEADERS],
        },
        {
            "range": "'Analytics'!A1",
            "values": [
                ["Date", "Platform", "Post Type", "Project", "Impressions", "Reach",
                 "Engagement", "Saves", "Shares", "Comments", "Link Clicks", "Profile Visits"],
            ],
        },
    ]

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet_id,
        body={"valueInputOption": "RAW", "data": batch_data},
    ).execute()

    # ── Formatting ──
    requests = []

    # Freeze header rows
    for tab_name, tab_id in tab_ids.items():
        requests.append({
            "updateSheetProperties": {
                "properties": {"sheetId": tab_id, "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }
        })

    # Bold headers
    for tab_id in tab_ids.values():
        requests.append({
            "repeatCell": {
                "range": {"sheetId": tab_id, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": True},
                        "backgroundColor": {"red": 0.15, "green": 0.15, "blue": 0.15},
                        "horizontalAlignment": "CENTER",
                        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                    }
                },
                "fields": "userEnteredFormat(textFormat,backgroundColor,horizontalAlignment)",
            }
        })

    # Status column data validation
    cal_tab_id = tab_ids["Content Calendar"]
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": cal_tab_id,
                "startRowIndex": 1,
                "endRowIndex": 500,
                "startColumnIndex": 11,  # Column L (Status)
                "endColumnIndex": 12,
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": s} for s in STATUS_COLORS.keys()],
                },
                "showCustomUi": True,
                "strict": True,
            }
        }
    })

    # Platform column data validation
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": cal_tab_id,
                "startRowIndex": 1,
                "endRowIndex": 500,
                "startColumnIndex": 3,  # Column D (Platform)
                "endColumnIndex": 4,
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": p} for p in ["instagram", "linkedin", "pinterest"]],
                },
                "showCustomUi": True,
            }
        }
    })

    # Column widths for content calendar
    col_widths = {
        0: 100,   # Date
        1: 80,    # Day
        2: 60,    # Time
        3: 90,    # Platform
        4: 90,    # Type
        5: 90,    # Pillar
        6: 120,   # Project
        7: 200,   # Description
        8: 300,   # Caption
        9: 100,   # Hashtag Set
        10: 150,  # Image Files
        11: 90,   # Status
        12: 50,   # Requires Manual
        13: 200,  # Manual Notes
    }

    for col_idx, width in col_widths.items():
        requests.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": cal_tab_id,
                    "dimension": "COLUMNS",
                    "startIndex": col_idx,
                    "endIndex": col_idx + 1,
                },
                "properties": {"pixelSize": width},
                "fields": "pixelSize",
            }
        })

    # Conditional formatting for status column
    for status, color in STATUS_COLORS.items():
        requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": cal_tab_id,
                        "startRowIndex": 1,
                        "endRowIndex": 500,
                        "startColumnIndex": 11,
                        "endColumnIndex": 12,
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "TEXT_EQ",
                            "values": [{"userEnteredValue": status}],
                        },
                        "format": {"backgroundColor": color},
                    }
                },
                "index": 0,
            }
        })

    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": requests},
    ).execute()

    print(f"\nContent Calendar created with 4 tabs:")
    print(f"  1. Content Calendar — posting schedule with status tracking")
    print(f"  2. Dashboard — KPIs and targets")
    print(f"  3. Ideas Bank — evergreen content backlog")
    print(f"  4. Analytics — raw engagement data")
    print(f"\nSheet ID: {sheet_id}")
    print(f"Add this to your .env:")
    print(f"  CONTENT_CALENDAR_SHEET_ID={sheet_id}")

    return 0


def cmd_populate(args):
    """Push a project's content plan into the calendar."""
    service = get_sheets_service()
    project_dir = Path(args.project_dir)

    # Load content plan
    plan_path = project_dir / "social" / "content-plan.json"
    if not plan_path.exists():
        print(f"ERROR: No content plan found at {plan_path}")
        print("Run social_media_manager.py ingest or plan first.")
        return 1

    with open(plan_path) as f:
        plan = json.load(f)

    # Load carousel plan for captions
    carousel_captions = {}
    carousel_path = project_dir / "social" / "carousel-plan.json"
    if carousel_path.exists():
        with open(carousel_path) as f:
            carousels = json.load(f)
        for cs in carousels:
            caps = cs.get("captions", {})
            name = cs.get("name", "")
            carousel_captions[name] = caps.get("main_caption", caps.get("post_caption", ""))

    # Load standalone captions
    standalone = {}
    captions_path = project_dir / "captions" / "standalone-captions.json"
    if captions_path.exists():
        with open(captions_path) as f:
            standalone = json.load(f).get("captions", {})

    # Build rows
    rows = []
    for week in plan.get("weeks", []):
        for post in week.get("posts", []):
            # Try to find the right caption
            caption = ""
            desc = post.get("description", "")

            # Check carousel captions first
            for carousel_name, carousel_cap in carousel_captions.items():
                if carousel_name and carousel_name in desc:
                    caption = carousel_cap
                    break

            # Fall back to standalone captions
            if not caption:
                source = post.get("caption_source", "")
                if "Instagram Carousel" in source or (post["type"] == "carousel" and post["platform"] == "instagram"):
                    caption = standalone.get("Instagram Carousel", "")
                elif "Instagram Reel" in source:
                    caption = standalone.get("Instagram Reel", "")
                elif "Instagram Detail" in source:
                    caption = standalone.get("Instagram Detail/Single", "")
                elif "LinkedIn Industry" in source:
                    caption = standalone.get("LinkedIn Industry Insight", "")
                elif "LinkedIn Project" in source:
                    caption = standalone.get("LinkedIn Project Story", "")
                elif "Pinterest" in source:
                    caption = standalone.get("Pinterest Pin", "")

            row = [
                post.get("date", ""),
                post.get("day", ""),
                post.get("time", ""),
                post.get("platform", ""),
                post.get("type", ""),
                post.get("pillar", ""),
                plan.get("project", ""),
                desc,
                caption[:1000] if caption else "",  # Truncate very long captions
                "",  # Hashtag set
                "",  # Image files
                post.get("status", "DRAFT").upper(),
                "YES" if post.get("requires_manual") else "",
                post.get("manual_reason", ""),
                "",  # IG Engagement
                "",  # IG Saves
                "",  # IG Shares
                "",  # LI Impressions
                "",  # Pin Clicks
                post.get("notes", ""),
            ]
            rows.append(row)

    sheet_id = args.sheet_id or os.getenv("CONTENT_CALENDAR_SHEET_ID")
    if not sheet_id:
        print("ERROR: No sheet ID. Provide --sheet-id or set CONTENT_CALENDAR_SHEET_ID in .env")
        return 1

    # Find the next empty row
    existing = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range="'Content Calendar'!A:A",
    ).execute()
    next_row = len(existing.get("values", [])) + 1

    # Write rows
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"'Content Calendar'!A{next_row}",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()

    print(f"Populated {len(rows)} posts into Content Calendar")
    print(f"  Project: {plan.get('project', 'Unknown')}")
    print(f"  Date range: {rows[0][0]} to {rows[-1][0]}")
    print(f"  Starting at row {next_row}")
    print(f"\nOpen the sheet to review and set statuses to APPROVED when ready.")

    return 0


def cmd_status(args):
    """Show current calendar status."""
    service = get_sheets_service()

    sheet_id = args.sheet_id or os.getenv("CONTENT_CALENDAR_SHEET_ID")
    if not sheet_id:
        print("ERROR: No sheet ID.")
        return 1

    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range="'Content Calendar'!A:T",
    ).execute()

    rows = result.get("values", [])
    if len(rows) < 2:
        print("Calendar is empty.")
        return 0

    headers = rows[0]
    today = datetime.now().strftime("%Y-%m-%d")

    # Analyze
    total = len(rows) - 1
    by_status = {}
    overdue = []
    upcoming_week = []

    for row in rows[1:]:
        # Pad row to match headers
        while len(row) < len(headers):
            row.append("")

        date = row[0]
        status = row[11] if len(row) > 11 else ""
        by_status[status] = by_status.get(status, 0) + 1

        if date < today and status in ("DRAFT", "NEW", "REVIEW", "APPROVED"):
            overdue.append(row)

    print(f"\n{'='*60}")
    print(f"CONTENT CALENDAR STATUS")
    print(f"{'='*60}")
    print(f"\n  Total posts: {total}")
    print(f"  By status:")
    for status, count in sorted(by_status.items()):
        print(f"    {status or 'BLANK':12s} {count}")

    if overdue:
        print(f"\n  OVERDUE: {len(overdue)} posts past their scheduled date")
        for row in overdue[:5]:
            print(f"    {row[0]}  {row[3]:10s} {row[4]:10s} {row[7][:40]}")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Content calendar management")
    sub = parser.add_subparsers(dest="command")

    cr = sub.add_parser("create", help="Create a new content calendar sheet")
    cr.add_argument("--title", default="Matt Anthony — Content Calendar 2026", help="Sheet title")

    pop = sub.add_parser("populate", help="Push content plan to calendar")
    pop.add_argument("--sheet-id", default="", help="Google Sheet ID")
    pop.add_argument("--project-dir", required=True, help="Project directory with content-plan.json")

    st = sub.add_parser("status", help="Show calendar status")
    st.add_argument("--sheet-id", default="", help="Google Sheet ID")

    args = parser.parse_args()

    if args.command == "create":
        return cmd_create(args)
    elif args.command == "populate":
        return cmd_populate(args)
    elif args.command == "status":
        return cmd_status(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
