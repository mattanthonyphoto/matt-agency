"""Instagram DM Outreach Tracker — Google Sheets-backed prospect management.

Subcommands:
  create-sheet   Create the IG DM Tracker Google Sheet with all tabs and formatting
  add-prospect   Add a prospect to the tracker (manual or from cold email list)
  update-status  Update a prospect's DM status
  get-queue      Get today's DM queue (prospects ready for outreach)
  prep-dm        Store a pre-written personalized DM for a prospect (Claude writes, Matt sends)
  log-dm         Log a sent DM with template used
  get-follow-ups Get prospects due for follow-up
  stats          Show outreach stats summary
  batch-prep     Get all "Ready to DM" prospects with their details for Claude to research and write DMs
  scout          Pull last 20 posts from a prospect's IG to find things to comment on during warm-up
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.google_sheets_auth import get_sheets_service

load_dotenv(PROJECT_ROOT / ".env")

# Will be set after sheet creation — update this ID
TRACKER_SHEET_ID = os.environ.get("IG_DM_TRACKER_SHEET_ID", "")

# Pipeline sheet for syncing warm leads
PIPELINE_SHEET_ID = "1m8q6yIqq3jzYGkLwgFVD6d_WlAzMFgz-gRekdysE1IQ"

# DM status progression
STATUSES = [
    "New",           # Just added, no engagement yet
    "Warming",       # Liking posts, reacting to stories
    "DM Sent",       # First DM sent
    "Replied",       # They responded
    "In Conversation",  # Active back-and-forth
    "Call Booked",   # Discovery call scheduled
    "Plan Sent",     # Marketing plan delivered
    "Won",           # Converted to client
    "Not Interested",  # Declined or ghosted after follow-up
    "No Response",   # No reply after 2 follow-ups
]

ICP_TYPES = ["Builder", "Architect", "Interior Designer", "Millwork", "Windows",
             "Landscape", "Lighting", "Flooring", "Hardware", "Envelope"]

HEADERS = [
    "Company", "Contact Name", "IG Handle", "DM Message", "ICP Type", "Region",
    "Website", "Email", "Status", "Warm-Up Started", "DM Sent Date",
    "Template Used", "Follow-Up 1 Date", "Follow-Up 2 Date",
    "Reply Date", "Reply Summary", "Next Action", "Next Action Date",
    "Plan URL", "Pipeline Synced", "Source", "Notes"
]

TEMPLATE_HEADERS = [
    "Template ID", "ICP Type", "Template Name", "Angle",
    "Opening Line", "Body", "CTA", "Use Count", "Response Rate"
]

STATS_HEADERS = [
    "Week", "DMs Sent", "Replies", "Reply Rate",
    "Calls Booked", "Plans Sent", "Conversions"
]


def get_sheets():
    return get_sheets_service()


# ── create-sheet ────────────────────────────────────────────

def create_sheet(args):
    """Create the IG DM Tracker sheet with Prospects, Templates, and Stats tabs."""
    sheets = get_sheets()

    body = {
        "properties": {"title": "Instagram DM Outreach Tracker"},
        "sheets": [
            {
                "properties": {"title": "Prospects", "sheetId": 0},
                "data": [{"rowData": [{"values": [
                    {"userEnteredValue": {"stringValue": h},
                     "userEnteredFormat": {
                         "backgroundColor": {"red": 0.15, "green": 0.15, "blue": 0.15},
                         "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 0.84, "blue": 0.4}},
                     }}
                    for h in HEADERS
                ]}]}],
            },
            {
                "properties": {"title": "DM Templates", "sheetId": 1},
                "data": [{"rowData": [{"values": [
                    {"userEnteredValue": {"stringValue": h},
                     "userEnteredFormat": {
                         "backgroundColor": {"red": 0.15, "green": 0.15, "blue": 0.15},
                         "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 0.84, "blue": 0.4}},
                     }}
                    for h in TEMPLATE_HEADERS
                ]}]}],
            },
            {
                "properties": {"title": "Weekly Stats", "sheetId": 2},
                "data": [{"rowData": [{"values": [
                    {"userEnteredValue": {"stringValue": h},
                     "userEnteredFormat": {
                         "backgroundColor": {"red": 0.15, "green": 0.15, "blue": 0.15},
                         "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 0.84, "blue": 0.4}},
                     }}
                    for h in STATS_HEADERS
                ]}]}],
            },
        ],
    }

    result = sheets.spreadsheets().create(body=body).execute()
    sheet_id = result["spreadsheetId"]
    url = result["spreadsheetUrl"]

    # Set column widths for Prospects tab
    requests = [
        {"updateDimensionProperties": {
            "range": {"sheetId": 0, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
            "properties": {"pixelSize": w},
            "fields": "pixelSize",
        }}
        for i, w in enumerate([180, 150, 140, 350, 130, 120, 200, 200, 120, 110, 110,
                                120, 110, 110, 110, 250, 150, 110, 250, 80, 100, 300])
    ]

    # Freeze header row
    requests.append({
        "updateSheetProperties": {
            "properties": {"sheetId": 0, "gridProperties": {"frozenRowCount": 1}},
            "fields": "gridProperties.frozenRowCount",
        }
    })
    requests.append({
        "updateSheetProperties": {
            "properties": {"sheetId": 1, "gridProperties": {"frozenRowCount": 1}},
            "fields": "gridProperties.frozenRowCount",
        }
    })

    # Status column data validation
    requests.append({
        "setDataValidation": {
            "range": {"sheetId": 0, "startRowIndex": 1, "endRowIndex": 500,
                      "startColumnIndex": 8, "endColumnIndex": 9},
            "rule": {
                "condition": {"type": "ONE_OF_LIST",
                              "values": [{"userEnteredValue": s} for s in STATUSES]},
                "showCustomUi": True, "strict": False,
            },
        }
    })

    # ICP Type data validation
    requests.append({
        "setDataValidation": {
            "range": {"sheetId": 0, "startRowIndex": 1, "endRowIndex": 500,
                      "startColumnIndex": 4, "endColumnIndex": 5},
            "rule": {
                "condition": {"type": "ONE_OF_LIST",
                              "values": [{"userEnteredValue": t} for t in ICP_TYPES]},
                "showCustomUi": True, "strict": False,
            },
        }
    })

    # Conditional formatting for status column
    status_colors = {
        "New": {"red": 0.9, "green": 0.9, "blue": 0.9},
        "Warming": {"red": 1.0, "green": 0.95, "blue": 0.8},
        "DM Sent": {"red": 0.8, "green": 0.9, "blue": 1.0},
        "Replied": {"red": 0.8, "green": 1.0, "blue": 0.8},
        "In Conversation": {"red": 0.7, "green": 0.95, "blue": 0.7},
        "Call Booked": {"red": 0.6, "green": 0.9, "blue": 0.6},
        "Plan Sent": {"red": 0.85, "green": 0.8, "blue": 1.0},
        "Won": {"red": 1.0, "green": 0.84, "blue": 0.4},
        "Not Interested": {"red": 1.0, "green": 0.8, "blue": 0.8},
        "No Response": {"red": 0.85, "green": 0.85, "blue": 0.85},
    }

    for status, color in status_colors.items():
        requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": 0, "startRowIndex": 1, "endRowIndex": 500,
                                "startColumnIndex": 8, "endColumnIndex": 9}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": status}]},
                        "format": {"backgroundColor": color},
                    },
                },
                "index": 0,
            }
        })

    sheets.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, body={"requests": requests}
    ).execute()

    print(f"Sheet created: {url}")
    print(f"Sheet ID: {sheet_id}")
    print(f"\nAdd to .env: IG_DM_TRACKER_SHEET_ID={sheet_id}")
    return 0


# ── add-prospect ────────────────────────────────────────────

def add_prospect(args):
    """Add a prospect to the tracker."""
    sheets = get_sheets()

    row = [
        args.company, args.contact, args.ig_handle, "",  # DM Message (empty)
        args.icp_type, args.region or "", args.website or "", args.email or "",
        "New",  # Status
        "", "", "", "", "", "", "",  # DM tracking fields
        "", "",  # Next action fields
        "", "No",  # Plan URL, Pipeline Synced
        args.source or "Manual", args.notes or "",
    ]

    sheets.spreadsheets().values().append(
        spreadsheetId=TRACKER_SHEET_ID,
        range="Prospects!A:V",
        valueInputOption="USER_ENTERED",
        body={"values": [row]},
    ).execute()

    print(f"Added: {args.company} (@{args.ig_handle}) — {args.icp_type}")
    return 0


# ── update-status ───────────────────────────────────────────

def update_status(args):
    """Update a prospect's status by IG handle or company name."""
    sheets = get_sheets()

    result = sheets.spreadsheets().values().get(
        spreadsheetId=TRACKER_SHEET_ID, range="Prospects!A:V"
    ).execute()
    rows = result.get("values", [])

    target = args.identifier.lower()
    match_row = None
    for i, row in enumerate(rows[1:], start=2):
        company = row[0].lower() if len(row) > 0 else ""
        handle = row[2].lower().lstrip("@") if len(row) > 2 else ""
        if target in company or target == handle:
            match_row = i
            break

    if not match_row:
        print(f"ERROR: No prospect found matching '{args.identifier}'")
        return 1

    # Update status (column I = index 8)
    sheets.spreadsheets().values().update(
        spreadsheetId=TRACKER_SHEET_ID,
        range=f"Prospects!I{match_row}",
        valueInputOption="USER_ENTERED",
        body={"values": [[args.status]]},
    ).execute()

    # Update relevant date fields based on status
    today = datetime.now().strftime("%Y-%m-%d")
    if args.status == "Warming":
        sheets.spreadsheets().values().update(
            spreadsheetId=TRACKER_SHEET_ID,
            range=f"Prospects!J{match_row}",
            valueInputOption="USER_ENTERED",
            body={"values": [[today]]},
        ).execute()
    elif args.status == "DM Sent":
        sheets.spreadsheets().values().update(
            spreadsheetId=TRACKER_SHEET_ID,
            range=f"Prospects!K{match_row}",
            valueInputOption="USER_ENTERED",
            body={"values": [[today]]},
        ).execute()
    elif args.status == "Replied":
        sheets.spreadsheets().values().update(
            spreadsheetId=TRACKER_SHEET_ID,
            range=f"Prospects!O{match_row}",
            valueInputOption="USER_ENTERED",
            body={"values": [[today]]},
        ).execute()

    if args.notes:
        sheets.spreadsheets().values().update(
            spreadsheetId=TRACKER_SHEET_ID,
            range=f"Prospects!V{match_row}",
            valueInputOption="USER_ENTERED",
            body={"values": [[args.notes]]},
        ).execute()

    print(f"Updated: {args.identifier} → {args.status}")
    return 0


# ── log-dm ──────────────────────────────────────────────────

def log_dm(args):
    """Log a sent DM for a prospect."""
    sheets = get_sheets()

    result = sheets.spreadsheets().values().get(
        spreadsheetId=TRACKER_SHEET_ID, range="Prospects!A:V"
    ).execute()
    rows = result.get("values", [])

    target = args.identifier.lower()
    match_row = None
    for i, row in enumerate(rows[1:], start=2):
        company = row[0].lower() if len(row) > 0 else ""
        handle = row[2].lower().lstrip("@") if len(row) > 2 else ""
        if target in company or target == handle:
            match_row = i
            break

    if not match_row:
        print(f"ERROR: No prospect found matching '{args.identifier}'")
        return 1

    today = datetime.now().strftime("%Y-%m-%d")
    current_row = rows[match_row - 1]

    # Determine if this is first DM, follow-up 1, or follow-up 2
    dm_sent = current_row[10] if len(current_row) > 10 else ""
    fu1 = current_row[12] if len(current_row) > 12 else ""

    updates = []
    if not dm_sent:
        updates.append({"range": f"Prospects!I{match_row}", "values": [["DM Sent"]]})
        updates.append({"range": f"Prospects!K{match_row}", "values": [[today]]})
        updates.append({"range": f"Prospects!L{match_row}", "values": [[args.template or ""]]})
        updates.append({"range": f"Prospects!D{match_row}", "values": [[args.message or ""]]})
        # Set follow-up 1 date to 4 days from now
        fu1_date = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")
        updates.append({"range": f"Prospects!Q{match_row}", "values": [["Follow up if no reply"]]})
        updates.append({"range": f"Prospects!R{match_row}", "values": [[fu1_date]]})
    elif not fu1:
        updates.append({"range": f"Prospects!M{match_row}", "values": [[today]]})
        fu2_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        updates.append({"range": f"Prospects!Q{match_row}", "values": [["Final follow-up"]]})
        updates.append({"range": f"Prospects!R{match_row}", "values": [[fu2_date]]})
    else:
        updates.append({"range": f"Prospects!N{match_row}", "values": [[today]]})
        updates.append({"range": f"Prospects!Q{match_row}", "values": [["Mark No Response if silent"]]})
        fu_final = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        updates.append({"range": f"Prospects!R{match_row}", "values": [[fu_final]]})

    for update in updates:
        sheets.spreadsheets().values().update(
            spreadsheetId=TRACKER_SHEET_ID,
            range=update["range"],
            valueInputOption="USER_ENTERED",
            body={"values": update["values"]},
        ).execute()

    print(f"Logged DM to {args.identifier} on {today}")
    return 0


# ── get-queue ───────────────────────────────────────────────

def get_queue(args):
    """Get today's DM queue — prospects ready for outreach."""
    sheets = get_sheets()

    result = sheets.spreadsheets().values().get(
        spreadsheetId=TRACKER_SHEET_ID, range="Prospects!A:V"
    ).execute()
    rows = result.get("values", [])

    if len(rows) < 2:
        print(json.dumps({"warm_up": [], "ready_to_dm": [], "follow_ups": []}))
        return 0

    today = datetime.now().strftime("%Y-%m-%d")
    warm_up = []
    ready_to_dm = []
    follow_ups = []

    for row in rows[1:]:
        if len(row) < 9:
            continue

        company = row[0] if len(row) > 0 else ""
        contact = row[1] if len(row) > 1 else ""
        handle = row[2] if len(row) > 2 else ""
        icp = row[4] if len(row) > 4 else ""
        status = row[8] if len(row) > 8 else ""
        warm_start = row[9] if len(row) > 9 else ""
        next_action_date = row[17] if len(row) > 17 else ""

        prospect = {"company": company, "contact": contact, "handle": handle, "icp": icp}

        if status == "New":
            warm_up.append(prospect)
        elif status == "Warming":
            # Ready to DM if warming for 2+ days
            if warm_start:
                try:
                    start = datetime.strptime(warm_start, "%Y-%m-%d")
                    if (datetime.now() - start).days >= 2:
                        ready_to_dm.append(prospect)
                    else:
                        warm_up.append({**prospect, "note": f"Warming since {warm_start}, continue engaging"})
                except ValueError:
                    ready_to_dm.append(prospect)
            else:
                ready_to_dm.append(prospect)
        elif status in ("DM Sent", "Plan Sent") and next_action_date:
            if next_action_date <= today:
                follow_ups.append({**prospect, "status": status,
                                   "action": row[16] if len(row) > 16 else "Follow up"})

    limit = args.limit if hasattr(args, "limit") else 25
    output = {
        "date": today,
        "warm_up": warm_up[:10],
        "ready_to_dm": ready_to_dm[:limit],
        "follow_ups": follow_ups,
        "totals": {
            "warming": len(warm_up),
            "ready": len(ready_to_dm),
            "follow_ups_due": len(follow_ups),
        },
    }

    print(json.dumps(output, indent=2))
    return 0


# ── get-follow-ups ──────────────────────────────────────────

def get_follow_ups(args):
    """Get prospects due for follow-up."""
    sheets = get_sheets()

    result = sheets.spreadsheets().values().get(
        spreadsheetId=TRACKER_SHEET_ID, range="Prospects!A:V"
    ).execute()
    rows = result.get("values", [])

    today = datetime.now().strftime("%Y-%m-%d")
    due = []

    for row in rows[1:]:
        if len(row) < 18:
            continue
        next_date = row[17] if len(row) > 17 else ""
        status = row[8] if len(row) > 8 else ""
        if next_date and next_date <= today and status not in ("Won", "Not Interested", "No Response"):
            due.append({
                "company": row[0],
                "contact": row[1] if len(row) > 1 else "",
                "handle": row[2] if len(row) > 2 else "",
                "icp": row[4] if len(row) > 4 else "",
                "status": status,
                "action": row[16] if len(row) > 16 else "",
                "due": next_date,
            })

    print(json.dumps(due, indent=2))
    return 0


# ── stats ───────────────────────────────────────────────────

def stats(args):
    """Show outreach stats summary."""
    sheets = get_sheets()

    result = sheets.spreadsheets().values().get(
        spreadsheetId=TRACKER_SHEET_ID, range="Prospects!A:V"
    ).execute()
    rows = result.get("values", [])

    counts = {}
    icp_counts = {}
    for row in rows[1:]:
        status = row[8] if len(row) > 8 else "Unknown"
        icp = row[4] if len(row) > 4 else "Unknown"
        counts[status] = counts.get(status, 0) + 1
        icp_counts[icp] = icp_counts.get(icp, 0) + 1

    total = len(rows) - 1
    replied = counts.get("Replied", 0) + counts.get("In Conversation", 0) + counts.get("Call Booked", 0) + counts.get("Won", 0)
    dm_sent = sum(v for k, v in counts.items() if k not in ("New", "Warming"))
    reply_rate = f"{replied / dm_sent * 100:.0f}%" if dm_sent > 0 else "N/A"

    output = {
        "total_prospects": total,
        "by_status": counts,
        "by_icp": icp_counts,
        "dms_sent": dm_sent,
        "replies": replied,
        "reply_rate": reply_rate,
        "calls_booked": counts.get("Call Booked", 0),
        "plans_sent": counts.get("Plan Sent", 0),
        "conversions": counts.get("Won", 0),
    }

    print(json.dumps(output, indent=2))
    return 0


# ── prep-dm ─────────────────────────────────────────────────

def prep_dm(args):
    """Store a pre-written personalized DM for a prospect. Claude writes it, Matt copy-pastes it."""
    sheets = get_sheets()

    result = sheets.spreadsheets().values().get(
        spreadsheetId=TRACKER_SHEET_ID, range="Prospects!A:V"
    ).execute()
    rows = result.get("values", [])

    target = args.identifier.lower()
    match_row = None
    for i, row in enumerate(rows[1:], start=2):
        company = row[0].lower() if len(row) > 0 else ""
        handle = row[2].lower().lstrip("@") if len(row) > 2 else ""
        if target in company or target == handle:
            match_row = i
            break

    if not match_row:
        print(f"ERROR: No prospect found matching '{args.identifier}'")
        return 1

    today = datetime.now().strftime("%Y-%m-%d")
    updates = [
        {"range": f"Prospects!D{match_row}", "values": [[args.message]]},
        {"range": f"Prospects!Q{match_row}", "values": [["Send pre-written DM"]]},
        {"range": f"Prospects!R{match_row}", "values": [[today]]},
    ]

    # Set status to Warming if it's New (Claude prepped it, Matt still needs to warm up)
    # Set Next Action Date to today if warm enough, or +2 days if new
    current_row = rows[match_row - 1]
    current_status = current_row[8] if len(current_row) > 8 else ""
    warm_start = current_row[9] if len(current_row) > 9 else ""

    if current_status == "New":
        # New prospect — set to warming, DM ready in 2 days
        send_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        updates.append({"range": f"Prospects!I{match_row}", "values": [["Warming"]]})
        updates.append({"range": f"Prospects!J{match_row}", "values": [[today]]})
        updates.append({"range": f"Prospects!R{match_row}", "values": [[send_date]]})
    elif current_status == "Warming" and warm_start:
        try:
            start = datetime.strptime(warm_start, "%Y-%m-%d")
            if (datetime.now() - start).days >= 2:
                updates.append({"range": f"Prospects!R{match_row}", "values": [[today]]})
        except ValueError:
            updates.append({"range": f"Prospects!R{match_row}", "values": [[today]]})

    if args.angle:
        updates.append({"range": f"Prospects!L{match_row}", "values": [[args.angle]]})

    if args.notes:
        updates.append({"range": f"Prospects!V{match_row}", "values": [[args.notes]]})

    for update in updates:
        sheets.spreadsheets().values().update(
            spreadsheetId=TRACKER_SHEET_ID,
            range=update["range"],
            valueInputOption="USER_ENTERED",
            body={"values": update["values"]},
        ).execute()

    print(f"Prepped DM for {args.identifier}: {args.message[:80]}...")
    return 0


# ── batch-prep ──────────────────────────────────────────────

def batch_prep(args):
    """Get all prospects that need DMs written. Returns full details for Claude to research."""
    sheets = get_sheets()

    result = sheets.spreadsheets().values().get(
        spreadsheetId=TRACKER_SHEET_ID, range="Prospects!A:V"
    ).execute()
    rows = result.get("values", [])

    today = datetime.now().strftime("%Y-%m-%d")
    needs_prep = []
    needs_follow_up = []
    ready_to_send = []

    for row in rows[1:]:
        if len(row) < 9:
            continue

        company = row[0] if len(row) > 0 else ""
        contact = row[1] if len(row) > 1 else ""
        handle = row[2] if len(row) > 2 else ""
        dm_message = row[3] if len(row) > 3 else ""
        icp = row[4] if len(row) > 4 else ""
        region = row[5] if len(row) > 5 else ""
        website = row[6] if len(row) > 6 else ""
        email = row[7] if len(row) > 7 else ""
        status = row[8] if len(row) > 8 else ""
        warm_start = row[9] if len(row) > 9 else ""
        next_action = row[16] if len(row) > 16 else ""
        next_date = row[17] if len(row) > 17 else ""
        notes = row[21] if len(row) > 21 else ""

        prospect = {
            "company": company, "contact": contact, "handle": handle,
            "icp": icp, "region": region, "website": website, "email": email,
            "status": status, "notes": notes,
        }

        # Needs a DM written (new or warming with no message prepped)
        if status in ("New", "Warming") and not dm_message:
            if status == "Warming" and warm_start:
                try:
                    start = datetime.strptime(warm_start, "%Y-%m-%d")
                    prospect["days_warming"] = (datetime.now() - start).days
                except ValueError:
                    prospect["days_warming"] = 0
            needs_prep.append(prospect)

        # Has a prepped message, ready to send
        elif status == "Warming" and dm_message and next_action == "Send pre-written DM":
            if not next_date or next_date <= today:
                ready_to_send.append({**prospect, "message": dm_message})

        # Needs a follow-up written
        elif status in ("DM Sent", "Plan Sent") and next_date and next_date <= today:
            prospect["action"] = next_action
            prospect["original_dm"] = dm_message
            needs_follow_up.append(prospect)

    output = {
        "date": today,
        "needs_dm_written": needs_prep[:args.limit],
        "ready_to_send": ready_to_send,
        "needs_follow_up": needs_follow_up,
        "totals": {
            "needs_prep": len(needs_prep),
            "ready_to_send": len(ready_to_send),
            "needs_follow_up": len(needs_follow_up),
        },
    }

    print(json.dumps(output, indent=2))
    return 0


# ── scout ──────────────────────────────────────────────────

SCOUT_CACHE_DIR = PROJECT_ROOT / ".tmp" / "ig_scout"


def _get_instaloader():
    """Get an Instaloader instance with saved session."""
    import instaloader

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
    session_file = PROJECT_ROOT / ".tmp" / "ig_network" / f"session-mattanthonyphoto"
    if session_file.exists():
        L.load_session_from_file("mattanthonyphoto", str(session_file))
    else:
        print("ERROR: No saved Instagram session found.")
        print("Run: python3 tools/ig_scrape_network.py login")
        sys.exit(1)
    return L


def scout(args):
    """Pull the last N posts from a prospect's IG and output commentable content."""
    import instaloader

    handle = args.identifier.lower().lstrip("@")
    count = args.count
    cache_hours = args.cache_hours

    # Check cache first
    SCOUT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = SCOUT_CACHE_DIR / f"{handle}.json"

    if cache_file.exists() and not args.refresh:
        cached = json.load(open(cache_file))
        cached_at = datetime.strptime(cached["scouted_at"], "%Y-%m-%d %H:%M")
        if (datetime.now() - cached_at).total_seconds() < cache_hours * 3600:
            print(json.dumps(cached, indent=2))
            return 0

    L = _get_instaloader()

    try:
        profile = instaloader.Profile.from_username(L.context, handle)
    except instaloader.exceptions.ProfileNotExistsException:
        print(f"ERROR: Profile @{handle} not found")
        return 1
    except instaloader.exceptions.ConnectionException as e:
        print(f"ERROR: Connection issue — {e}")
        return 1

    posts = []
    for i, post in enumerate(profile.get_posts()):
        if i >= count:
            break

        caption = post.caption or ""
        # Truncate very long captions for readability
        caption_preview = caption[:300] + ("..." if len(caption) > 300 else "")

        post_data = {
            "date": post.date_utc.strftime("%Y-%m-%d"),
            "likes": post.likes,
            "comments": post.comments,
            "caption": caption_preview,
            "full_caption": caption,
            "is_video": post.is_video,
            "video_view_count": post.video_view_count if post.is_video else None,
            "hashtags": list(post.caption_hashtags) if post.caption_hashtags else [],
            "tagged_users": list(post.tagged_users) if post.tagged_users else [],
            "shortcode": post.shortcode,
            "url": f"https://www.instagram.com/p/{post.shortcode}/",
        }

        # Flag high-engagement posts (good candidates for commenting)
        avg_likes = profile.mediacount and (profile.followers * 0.03)  # rough 3% benchmark
        if post.likes > avg_likes if avg_likes else post.likes > 50:
            post_data["high_engagement"] = True

        posts.append(post_data)

        # Rate limiting
        if (i + 1) % 5 == 0:
            import time
            time.sleep(1)

    output = {
        "handle": handle,
        "full_name": profile.full_name,
        "followers": profile.followers,
        "following": profile.followees,
        "total_posts": profile.mediacount,
        "biography": profile.biography or "",
        "is_private": profile.is_private,
        "scouted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "posts": posts,
        "summary": {
            "posts_fetched": len(posts),
            "total_likes": sum(p["likes"] for p in posts),
            "total_comments": sum(p["comments"] for p in posts),
            "avg_likes": round(sum(p["likes"] for p in posts) / len(posts)) if posts else 0,
            "avg_comments": round(sum(p["comments"] for p in posts) / len(posts)) if posts else 0,
            "video_count": sum(1 for p in posts if p["is_video"]),
            "photo_count": sum(1 for p in posts if not p["is_video"]),
            "frequently_tagged": _top_tagged(posts),
        },
    }

    # Cache the result
    with open(cache_file, "w") as fp:
        json.dump(output, fp, indent=2)

    print(json.dumps(output, indent=2))
    return 0


def _top_tagged(posts):
    """Find the most frequently tagged users across posts."""
    tag_counts = {}
    for p in posts:
        for user in p.get("tagged_users", []):
            tag_counts[user] = tag_counts.get(user, 0) + 1
    return sorted(tag_counts.items(), key=lambda x: -x[1])[:5]


# ── CLI ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Instagram DM Outreach Tracker")
    sub = parser.add_subparsers(dest="command")

    # create-sheet
    sub.add_parser("create-sheet", help="Create the tracker Google Sheet")

    # add-prospect
    ap = sub.add_parser("add-prospect", help="Add a prospect")
    ap.add_argument("--company", required=True)
    ap.add_argument("--contact", required=True)
    ap.add_argument("--ig-handle", required=True)
    ap.add_argument("--icp-type", required=True, choices=ICP_TYPES)
    ap.add_argument("--region", default="")
    ap.add_argument("--website", default="")
    ap.add_argument("--email", default="")
    ap.add_argument("--source", default="Manual")
    ap.add_argument("--notes", default="")

    # update-status
    us = sub.add_parser("update-status", help="Update prospect status")
    us.add_argument("identifier", help="Company name or IG handle")
    us.add_argument("--status", required=True, choices=STATUSES)
    us.add_argument("--notes", default="")

    # log-dm
    ld = sub.add_parser("log-dm", help="Log a sent DM")
    ld.add_argument("identifier", help="Company name or IG handle")
    ld.add_argument("--template", default="")
    ld.add_argument("--message", default="")

    # prep-dm
    pd = sub.add_parser("prep-dm", help="Store a pre-written DM for a prospect")
    pd.add_argument("identifier", help="Company name or IG handle")
    pd.add_argument("--message", required=True, help="The full DM message to store")
    pd.add_argument("--angle", default="", help="DM angle (e.g., craft-recognition, awards, design-intent)")
    pd.add_argument("--notes", default="", help="Research notes about the prospect")

    # batch-prep
    bp = sub.add_parser("batch-prep", help="Get prospects needing DMs written")
    bp.add_argument("--limit", type=int, default=15)

    # get-queue
    gq = sub.add_parser("get-queue", help="Get today's DM queue")
    gq.add_argument("--limit", type=int, default=25)

    # get-follow-ups
    sub.add_parser("get-follow-ups", help="Get follow-ups due")

    # stats
    sub.add_parser("stats", help="Show outreach stats")

    # scout
    sc = sub.add_parser("scout", help="Pull last N posts from a prospect's IG for warm-up comment ideas")
    sc.add_argument("identifier", help="IG handle (with or without @)")
    sc.add_argument("--count", type=int, default=20, help="Number of posts to pull (default 20)")
    sc.add_argument("--cache-hours", type=int, default=48, help="Use cached data if less than N hours old (default 48)")
    sc.add_argument("--refresh", action="store_true", help="Ignore cache and re-fetch")

    args = parser.parse_args()

    commands = {
        "create-sheet": create_sheet,
        "add-prospect": add_prospect,
        "update-status": update_status,
        "prep-dm": prep_dm,
        "batch-prep": batch_prep,
        "log-dm": log_dm,
        "get-queue": get_queue,
        "get-follow-ups": get_follow_ups,
        "stats": stats,
        "scout": scout,
    }

    if args.command in commands:
        return commands[args.command](args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)
