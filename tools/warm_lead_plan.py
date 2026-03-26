"""One-command warm lead plan — audit, generate marketing plan, publish, update Pipeline.

Usage:
    python3 tools/warm_lead_plan.py \
      --company "Ridgeline Homes" --owner "Jake" \
      --website "https://ridgelinehomes.ca" \
      --email "jake@ridgelinehomes.ca" \
      [--location "Squamish BC"] [--no-publish] [--no-pipeline]
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from tools.google_sheets_auth import get_sheets_service
from tools.batch_plans import process_builder, generate_dm, slugify

PIPELINE_SHEET_ID = "1m8q6yIqq3jzYGkLwgFVD6d_WlAzMFgz-gRekdysE1IQ"

# Unified Pipeline column indices (A:T)
P_COMPANY = 0
P_CONTACT = 1
P_EMAIL = 2
P_ICP = 4
P_SOURCE = 5
P_STAGE = 6
P_DATE_ADDED = 7
P_LAST_ACTIVITY = 8
P_SIGNAL = 9
P_PLAN_SENT = 12
P_PLAN_URL = 13
P_NEXT_ACTION = 15
P_NOTES = 19


def update_pipeline(company, contact, icp, email, plan_url):
    """Update or add lead in unified Pipeline with plan sent info."""
    sheets = get_sheets_service()

    # Read existing Pipeline
    try:
        result = sheets.spreadsheets().values().get(
            spreadsheetId=PIPELINE_SHEET_ID,
            range="'Pipeline'!A:T",
        ).execute()
        rows = result.get("values", [])
    except Exception as e:
        print(f"  WARNING: Could not read Pipeline: {e}", file=sys.stderr)
        return

    today = datetime.now().strftime("%Y-%m-%d")

    # Check if email already exists in Pipeline (col C, index 2)
    target_email = email.lower().strip()
    for row_idx, row in enumerate(rows[1:], start=2):
        while len(row) < 20:
            row.append("")
        if row[P_EMAIL].lower().strip() == target_email:
            # Update existing row
            updates = [
                {"range": f"'Pipeline'!G{row_idx}", "values": [["Engaged"]]},          # Stage
                {"range": f"'Pipeline'!I{row_idx}", "values": [[today]]},               # Last Activity
                {"range": f"'Pipeline'!J{row_idx}", "values": [[f"Plan sent {today}"]]},# Signal
                {"range": f"'Pipeline'!M{row_idx}", "values": [[today]]},               # Plan Sent
                {"range": f"'Pipeline'!N{row_idx}", "values": [[plan_url]]},            # Plan URL
                {"range": f"'Pipeline'!P{row_idx}", "values": [["Wait for response (5 days)"]]},  # Next Action
            ]
            sheets.spreadsheets().values().batchUpdate(
                spreadsheetId=PIPELINE_SHEET_ID,
                body={"valueInputOption": "USER_ENTERED", "data": updates},
            ).execute()
            print(f"  Updated Pipeline row {row_idx} with plan URL")
            return

    # Add new row if not found
    new_row = [""] * 20
    new_row[P_COMPANY] = company
    new_row[P_CONTACT] = contact
    new_row[P_EMAIL] = email
    new_row[P_ICP] = icp
    new_row[P_SOURCE] = "Cold Email"
    new_row[P_STAGE] = "Engaged"
    new_row[P_DATE_ADDED] = today
    new_row[P_LAST_ACTIVITY] = today
    new_row[P_SIGNAL] = f"Plan sent {today}"
    new_row[P_PLAN_SENT] = today
    new_row[P_PLAN_URL] = plan_url
    new_row[P_NEXT_ACTION] = "Wait for response (5 days)"

    sheets.spreadsheets().values().append(
        spreadsheetId=PIPELINE_SHEET_ID,
        range="'Pipeline'!A:T",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [new_row]},
    ).execute()
    print(f"  Added new Pipeline entry for {company}")


def main():
    parser = argparse.ArgumentParser(description="Generate and publish a marketing plan for a warm lead")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--owner", required=True, help="Contact/owner name")
    parser.add_argument("--website", required=True, help="Company website URL")
    parser.add_argument("--email", required=True, help="Contact email")
    parser.add_argument("--location", default=None, help="Company location (e.g. 'Squamish BC')")
    parser.add_argument("--icp", default="Builder", help="ICP category (default: Builder)")
    parser.add_argument("--no-publish", action="store_true", help="Generate but don't publish")
    parser.add_argument("--no-pipeline", action="store_true", help="Skip Pipeline tab update")
    args = parser.parse_args()

    slug = slugify(args.company)
    publish = not args.no_publish

    print(f"\n{'=' * 60}")
    print(f"  WARM LEAD PLAN: {args.company}")
    print(f"  Contact: {args.owner} <{args.email}>")
    print(f"  Website: {args.website}")
    print(f"  Publish: {'Yes' if publish else 'No'}")
    print(f"{'=' * 60}")

    # Build the row dict that process_builder expects
    row = {
        "Company Name": args.company,
        "Website": args.website,
        "Owner Name": args.owner,
        "Location": args.location or "",
    }

    # Run the full pipeline: audit → config → generate → publish
    result = process_builder(row, index=0, publish=publish)

    if result.get("status") != "OK":
        print(f"\n  FAILED: {result.get('reason', 'Unknown error')}")
        return 1

    plan_url = result["plan_url"]

    # Update Pipeline tab
    if not args.no_pipeline:
        print(f"\n  [5/5] Updating Pipeline...")
        update_pipeline(args.company, args.owner, args.icp, args.email, plan_url)

    # Generate DM message
    dm = generate_dm(args.company, args.owner, plan_url)

    print(f"\n{'=' * 60}")
    print(f"  COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Plan URL: {plan_url}")
    print(f"  Config:   business/sales/configs/{slug}-marketing-plan.json")
    print(f"\n  DM Message:")
    print(f"  {dm}")
    print(f"\n  Email to: {args.email}")
    print(f"{'=' * 60}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
