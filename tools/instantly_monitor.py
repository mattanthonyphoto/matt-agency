"""Instantly engagement monitor — pull lead signals, update Output Sheet, sync Pipeline.

Subcommands:
  pull-leads      Fetch lead-level engagement from Instantly, update Output Sheet Status col
  warm-leads      Return JSON of leads with strong signals (replied, opened 3+)
  sync-pipeline   Upsert warm leads from all ICP tabs into the unified Sales Pipeline
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.google_sheets_auth import get_sheets_service

load_dotenv(PROJECT_ROOT / ".env")

INSTANTLY_API_KEY = os.getenv("INSTANTLY_API_KEY", "")
INSTANTLY_BASE = "https://api.instantly.ai"
OUTPUT_SHEET_ID = "1brgQYbtCZwH1fFS3vYjMaW9IGf8iK37qeDBY2l06r8A"
PIPELINE_SHEET_ID = "1m8q6yIqq3jzYGkLwgFVD6d_WlAzMFgz-gRekdysE1IQ"

# Campaign IDs — update these as new campaigns launch
CAMPAIGN_MAP = {
    "builders": "6c2e1a93-0c62-4051-baed-9d2c12fb701f",
    "architects": "4f7a3a69-b717-4f74-9fe4-f4de12aa54e5",
    "designers": "53b09fc1-f942-4b75-af46-946ff9dfdc21",
}

# Output Sheet column layout (A:W) — col L is Status (index 11)
STATUS_COL_INDEX = 11  # L
NOTES_COL_INDEX = 22   # W
EMAIL_COL_INDEX = 6     # G

# ICP tabs in the Output Sheet
ICP_TABS = ["Builders", "Architects", "Interior Designers"]

# Unified Pipeline column indices (A:T)
P_COMPANY = 0
P_CONTACT = 1
P_EMAIL = 2
P_PHONE = 3
P_ICP = 4
P_SOURCE = 5
P_STAGE = 6
P_DATE_ADDED = 7
P_LAST_ACTIVITY = 8
P_SIGNAL = 9
P_PLAN_SENT = 12
P_PLAN_URL = 13
P_NEXT_ACTION = 15
P_ACTION_DATE = 16
P_NOTES = 19

# Statuses that should not be overwritten by Instantly signals
MANUAL_STATUSES = {
    "meeting booked", "in conversation", "proposal sent",
    "won", "lost", "not interested", "do not contact",
}

# Status priority (higher = stronger signal)
STATUS_PRIORITY = {
    "Replied": 5,
    "Interested": 4,
    "Opened 3+": 3,
    "Opened": 2,
    "Bounced": 1,
    "Completed": 0,
}


def _headers():
    return {
        "Authorization": f"Bearer {INSTANTLY_API_KEY}",
        "Content-Type": "application/json",
    }


def _fetch_leads_from_instantly(campaign_id, filter_val=None, limit=100):
    """Fetch leads from Instantly API v2 with optional filter."""
    all_leads = []
    cursor = None

    while True:
        payload = {
            "campaign": campaign_id,
            "limit": limit,
        }
        if filter_val:
            payload["filter"] = filter_val
        if cursor:
            payload["starting_after"] = cursor

        try:
            resp = requests.post(
                f"{INSTANTLY_BASE}/api/v2/leads/list",
                headers=_headers(),
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"ERROR: Instantly API failed: {e}", file=sys.stderr)
            break

        items = data.get("items", [])
        all_leads.extend(items)

        cursor = data.get("next_starting_after")
        if not cursor or len(items) < limit:
            break

    return all_leads


def _classify_lead(lead):
    """Classify a lead's engagement level from Instantly data."""
    reply_count = lead.get("email_reply_count", 0) or 0
    open_count = lead.get("email_open_count", 0) or 0
    status_code = lead.get("status", 0)

    # Bounced
    if status_code == -1:
        return "Bounced", f"Bounced"

    # Replied
    if reply_count > 0:
        ts = lead.get("timestamp_last_reply", "")
        date_str = _format_ts(ts)
        return "Replied", f"Replied {date_str}"

    # Opened 3+
    if open_count >= 3:
        return "Opened 3+", f"Opened {open_count}x"

    # Opened
    if open_count >= 1:
        return "Opened", f"Opened {open_count}x"

    # Completed sequence but no engagement
    if status_code == 3:
        return "Completed", "Sequence complete, no engagement"

    return None, None


def _format_ts(ts_str):
    """Format an ISO timestamp to 'Mar 25' style."""
    if not ts_str:
        return ""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d")
    except (ValueError, TypeError):
        return ""


# ── pull-leads ──────────────────────────────────────────────

def pull_leads(args):
    """Fetch engagement data from Instantly and update Output Sheet Status column."""
    campaigns = {}
    if args.campaign == "all":
        campaigns = CAMPAIGN_MAP
    elif args.campaign in CAMPAIGN_MAP:
        campaigns = {args.campaign: CAMPAIGN_MAP[args.campaign]}
    else:
        print(f"ERROR: Unknown campaign '{args.campaign}'. Options: {', '.join(CAMPAIGN_MAP.keys())}, all")
        return 1

    sheets = get_sheets_service()
    total_updated = 0

    for campaign_name, campaign_id in campaigns.items():
        print(f"\n--- {campaign_name.upper()} ---", file=sys.stderr)

        # Fetch all leads with any engagement
        leads = _fetch_leads_from_instantly(campaign_id)
        print(f"Fetched {len(leads)} leads from Instantly", file=sys.stderr)

        if not leads:
            continue

        # Build email-to-signal map
        signals = {}
        for lead in leads:
            email = (lead.get("email") or "").lower().strip()
            if not email:
                continue
            status, signal = _classify_lead(lead)
            if status:
                signals[email] = {"status": status, "signal": signal}

        if not signals:
            print("No engagement signals found", file=sys.stderr)
            continue

        # Determine which output tab to update
        tab_map = {
            "builders": "Builders",
            "architects": "Architects",
            "designers": "Interior Designers",
        }
        output_tab = tab_map.get(campaign_name, "Builders")

        # Read current output sheet to find email column and current statuses
        try:
            result = sheets.spreadsheets().values().get(
                spreadsheetId=OUTPUT_SHEET_ID,
                range=f"'{output_tab}'!A:W",
            ).execute()
            rows = result.get("values", [])
        except Exception as e:
            print(f"ERROR reading sheet: {e}", file=sys.stderr)
            continue

        if len(rows) < 2:
            continue

        # Find rows to update
        updates = []
        for row_idx, row in enumerate(rows[1:], start=2):  # 1-indexed, skip header
            while len(row) < 23:
                row.append("")

            email = row[EMAIL_COL_INDEX].lower().strip()
            if email not in signals:
                continue

            current_status = row[STATUS_COL_INDEX].strip().lower()

            # Don't overwrite manual statuses
            if current_status in MANUAL_STATUSES:
                continue

            new_status = signals[email]["status"]
            new_signal = signals[email]["signal"]

            # Don't downgrade status
            current_priority = STATUS_PRIORITY.get(row[STATUS_COL_INDEX].strip(), -1)
            new_priority = STATUS_PRIORITY.get(new_status, 0)
            if new_priority <= current_priority:
                continue

            # Update Status (col L) and append to Notes (col W)
            timestamp = datetime.now().strftime("%b %d %H:%M")
            note_append = f"[{timestamp}] {new_signal}"
            existing_notes = row[NOTES_COL_INDEX].strip()
            if existing_notes:
                new_notes = f"{existing_notes} | {note_append}"
            else:
                new_notes = note_append

            updates.append({
                "range": f"'{output_tab}'!L{row_idx}",
                "values": [[new_status]],
            })
            updates.append({
                "range": f"'{output_tab}'!W{row_idx}",
                "values": [[new_notes]],
            })

        if updates:
            sheets.spreadsheets().values().batchUpdate(
                spreadsheetId=OUTPUT_SHEET_ID,
                body={"valueInputOption": "USER_ENTERED", "data": updates},
            ).execute()
            total_updated += len(updates) // 2
            print(f"Updated {len(updates) // 2} leads in {output_tab}", file=sys.stderr)
        else:
            print(f"No new updates for {output_tab}", file=sys.stderr)

    print(f"\nTotal leads updated: {total_updated}")
    return 0


# ── warm-leads ──────────────────────────────────────────────

def warm_leads(args):
    """Return JSON of leads with strong engagement signals."""
    campaigns = CAMPAIGN_MAP
    warm = []

    for campaign_name, campaign_id in campaigns.items():
        leads = _fetch_leads_from_instantly(campaign_id)

        for lead in leads:
            status, signal = _classify_lead(lead)
            if status in ("Replied", "Interested", "Opened 3+"):
                warm.append({
                    "email": lead.get("email", ""),
                    "first_name": lead.get("first_name", ""),
                    "last_name": lead.get("last_name", ""),
                    "company": lead.get("company_name", ""),
                    "campaign": campaign_name,
                    "status": status,
                    "signal": signal,
                    "open_count": lead.get("email_open_count", 0),
                    "reply_count": lead.get("email_reply_count", 0),
                    "last_open": lead.get("timestamp_last_open", ""),
                    "last_reply": lead.get("timestamp_last_reply", ""),
                })

    # Sort: Replied first, then by open count desc
    warm.sort(key=lambda x: (-STATUS_PRIORITY.get(x["status"], 0), -(x["open_count"] or 0)))

    print(json.dumps(warm, indent=2))
    return 0


# ── sync-pipeline ───────────────────────────────────────────

def sync_pipeline(args):
    """Read all ICP tabs for leads with engagement, upsert into unified Pipeline."""
    sheets = get_sheets_service()

    # Read existing Pipeline data to avoid duplicates
    try:
        result = sheets.spreadsheets().values().get(
            spreadsheetId=PIPELINE_SHEET_ID,
            range="'Pipeline'!A:T",
        ).execute()
        pipeline_rows = result.get("values", [])
    except Exception:
        pipeline_rows = []

    # Build set of emails already in Pipeline
    existing_emails = set()
    if len(pipeline_rows) > 1:
        for row in pipeline_rows[1:]:
            if len(row) > P_EMAIL:
                existing_emails.add(row[P_EMAIL].lower().strip())

    # Scan all ICP tabs for leads with non-blank Status
    new_pipeline_rows = []
    today = datetime.now().strftime("%Y-%m-%d")

    for tab in ICP_TABS:
        try:
            result = sheets.spreadsheets().values().get(
                spreadsheetId=OUTPUT_SHEET_ID,
                range=f"'{tab}'!A:W",
            ).execute()
            rows = result.get("values", [])
        except Exception:
            continue

        if len(rows) < 2:
            continue

        for row in rows[1:]:
            while len(row) < 23:
                row.append("")

            status = row[STATUS_COL_INDEX].strip()
            email = row[EMAIL_COL_INDEX].lower().strip()

            # Only sync leads with ENGAGEMENT statuses
            engagement_statuses = {
                "replied", "interested", "opened 3+", "opened", "bounced",
                "meeting booked", "in conversation", "proposal sent",
                "plan sent", "won", "lost",
            }
            if status.lower() not in engagement_statuses or email in existing_emails:
                continue

            # Extract signal from Notes
            notes = row[NOTES_COL_INDEX].strip()
            signal_text = status
            if "[" in notes:
                parts = notes.split("|")
                last_part = parts[-1].strip() if parts else notes
                if "]" in last_part:
                    signal_text = last_part.split("]", 1)[-1].strip()

            # Map Instantly status to unified Stage
            stage = "Engaged"
            if status.lower() == "bounced":
                stage = "Dormant"
            elif status.lower() in ("meeting booked",):
                stage = "Discovery Booked"
            elif status.lower() in ("proposal sent",):
                stage = "Proposal Sent"
            elif status.lower() in ("won",):
                stage = "Won"
            elif status.lower() in ("lost",):
                stage = "Lost"

            # Build new row matching unified schema (A:T)
            new_row = [""] * 20
            new_row[P_COMPANY] = row[0]                # Company
            new_row[P_CONTACT] = row[1]                # Decision Maker
            new_row[P_EMAIL] = row[EMAIL_COL_INDEX]    # Email
            new_row[P_PHONE] = row[7] if len(row) > 7 else ""  # Phone (col H in output)
            new_row[P_ICP] = row[5]                    # ICP
            new_row[P_SOURCE] = "Cold Email"
            new_row[P_STAGE] = stage
            new_row[P_DATE_ADDED] = today
            new_row[P_LAST_ACTIVITY] = today
            new_row[P_SIGNAL] = signal_text
            new_row[P_NOTES] = ""

            new_pipeline_rows.append(new_row)
            existing_emails.add(email)

    if new_pipeline_rows:
        sheets.spreadsheets().values().append(
            spreadsheetId=PIPELINE_SHEET_ID,
            range="'Pipeline'!A:T",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": new_pipeline_rows},
        ).execute()
        print(f"Added {len(new_pipeline_rows)} leads to Pipeline")
    else:
        print("Pipeline is up to date, no new leads to add")

    return 0


# ── CLI ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Instantly engagement monitor")
    sub = parser.add_subparsers(dest="command")

    pl = sub.add_parser("pull-leads", help="Fetch engagement data, update Output Sheet")
    pl.add_argument("--campaign", required=True,
                    help=f"Campaign key ({', '.join(CAMPAIGN_MAP.keys())}) or 'all'")

    sub.add_parser("warm-leads", help="Return warm leads as JSON")

    sub.add_parser("sync-pipeline", help="Sync warm leads to Pipeline tab")

    args = parser.parse_args()

    if not INSTANTLY_API_KEY:
        print("ERROR: INSTANTLY_API_KEY not set in .env")
        return 1

    if args.command == "pull-leads":
        return pull_leads(args)
    elif args.command == "warm-leads":
        return warm_leads(args)
    elif args.command == "sync-pipeline":
        return sync_pipeline(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
