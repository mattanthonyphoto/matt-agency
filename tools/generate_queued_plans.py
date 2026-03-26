"""Process queued marketing plan requests from the unified Sales Pipeline.

Reads leads with Stage="New Lead" and Source="Lead Magnet" that have no Plan URL yet.

Usage:
    python3 tools/generate_queued_plans.py             # process all queued
    python3 tools/generate_queued_plans.py --limit 3    # process up to 3
    python3 tools/generate_queued_plans.py --dry-run    # show what would run
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
from tools.batch_plans import process_builder, generate_dm, slugify

load_dotenv(PROJECT_ROOT / ".env")

PIPELINE_SHEET_ID = "1m8q6yIqq3jzYGkLwgFVD6d_WlAzMFgz-gRekdysE1IQ"
DELIVERY_WEBHOOK = "https://n8n.srv1277163.hstgr.cloud/webhook/marketing-plan-deliver"

# Unified Pipeline column indices (A:T)
P_COMPANY = 0
P_CONTACT = 1
P_EMAIL = 2
P_ICP = 4
P_SOURCE = 5
P_STAGE = 6
P_LAST_ACTIVITY = 8
P_SIGNAL = 9
P_PLAN_SENT = 12
P_PLAN_URL = 13
P_NEXT_ACTION = 15
P_NOTES = 19


def read_queued():
    """Read leads from Pipeline that are lead magnet requests without a plan yet."""
    sheets = get_sheets_service()
    try:
        result = sheets.spreadsheets().values().get(
            spreadsheetId=PIPELINE_SHEET_ID,
            range="'Pipeline'!A:T",
        ).execute()
        rows = result.get("values", [])
    except Exception as e:
        print(f"ERROR reading Pipeline: {e}")
        return []

    if len(rows) < 2:
        return []

    queued = []
    for row_idx, row in enumerate(rows[1:], start=2):
        while len(row) < 20:
            row.append("")

        source = row[P_SOURCE].strip()
        plan_url = row[P_PLAN_URL].strip()
        stage = row[P_STAGE].strip()

        # Lead Magnet leads that haven't received a plan yet
        if source == "Lead Magnet" and not plan_url and stage not in ("Won", "Lost", "Dormant", "Do Not Contact"):
            queued.append({
                "row_idx": row_idx,
                "company": row[P_COMPANY],
                "first_name": row[P_CONTACT],
                "email": row[P_EMAIL],
                "icp": row[P_ICP],
                "website": "",  # May need to be pulled from notes or looked up
                "stage": stage,
            })

    return queued


def update_row(row_idx, plan_url="", error=""):
    """Update a Pipeline row with plan generation result."""
    sheets = get_sheets_service()
    today = datetime.now().strftime("%Y-%m-%d")

    updates = []
    if plan_url:
        updates = [
            {"range": f"'Pipeline'!G{row_idx}", "values": [["Engaged"]]},
            {"range": f"'Pipeline'!I{row_idx}", "values": [[today]]},
            {"range": f"'Pipeline'!J{row_idx}", "values": [[f"Plan sent {today}"]]},
            {"range": f"'Pipeline'!M{row_idx}", "values": [[today]]},
            {"range": f"'Pipeline'!N{row_idx}", "values": [[plan_url]]},
            {"range": f"'Pipeline'!P{row_idx}", "values": [["Wait for response (5 days)"]]},
        ]
    elif error:
        updates = [
            {"range": f"'Pipeline'!J{row_idx}", "values": [[f"Plan failed: {error}"]]},
            {"range": f"'Pipeline'!I{row_idx}", "values": [[today]]},
        ]

    if updates:
        sheets.spreadsheets().values().batchUpdate(
            spreadsheetId=PIPELINE_SHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates},
        ).execute()


def send_delivery_email(email, first_name, company, plan_url):
    """Trigger the delivery email via n8n webhook."""
    try:
        resp = requests.post(
            DELIVERY_WEBHOOK,
            json={
                "email": email,
                "firstName": first_name,
                "company": company,
                "planUrl": plan_url,
            },
            timeout=15,
        )
        if resp.status_code < 300:
            print(f"  Delivery email triggered for {email}")
        else:
            print(f"  WARNING: Delivery webhook returned {resp.status_code}", file=sys.stderr)
    except requests.RequestException as e:
        print(f"  WARNING: Delivery webhook failed: {e}", file=sys.stderr)
        print(f"  Manual send needed: {plan_url} → {email}")


def main():
    parser = argparse.ArgumentParser(description="Process queued marketing plan requests")
    parser.add_argument("--limit", type=int, default=0, help="Max plans to generate (0 = all)")
    parser.add_argument("--dry-run", action="store_true", help="Show queued requests without generating")
    parser.add_argument("--no-email", action="store_true", help="Skip sending delivery emails")
    args = parser.parse_args()

    queued = read_queued()

    if not queued:
        print("No queued plan requests.")
        return 0

    if args.limit > 0:
        queued = queued[:args.limit]

    print(f"\n{'=' * 60}")
    print(f"  QUEUED PLAN REQUESTS: {len(queued)}")
    print(f"{'=' * 60}")

    if args.dry_run:
        for q in queued:
            print(f"\n  {q['company']}")
            print(f"    Contact: {q['first_name']} <{q['email']}>")
            print(f"    ICP: {q['icp']} | Stage: {q['stage']}")
        return 0

    success = 0
    failed = 0

    for q in queued:
        print(f"\n--- Processing: {q['company']} ---")

        # Build the row dict for process_builder
        row = {
            "Company Name": q["company"],
            "Website": q["website"],
            "Owner Name": q["first_name"],
            "Location": "",
        }

        try:
            result = process_builder(row, index=0, publish=True)

            if result.get("status") == "OK":
                plan_url = result["plan_url"]
                update_row(q["row_idx"], plan_url=plan_url)

                # Send delivery email
                if not args.no_email:
                    send_delivery_email(q["email"], q["first_name"], q["company"], plan_url)

                success += 1
                print(f"  OK: {plan_url}")
            else:
                reason = result.get("reason", "Unknown error")
                update_row(q["row_idx"], error=reason)
                failed += 1
                print(f"  FAILED: {reason}")

        except Exception as e:
            update_row(q["row_idx"], error=str(e))
            failed += 1
            print(f"  FAILED: {e}")

    print(f"\n{'=' * 60}")
    print(f"  COMPLETE: {success} generated, {failed} failed")
    print(f"{'=' * 60}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
