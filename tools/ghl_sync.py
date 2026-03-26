#!/usr/bin/env python3
"""
ghl_sync.py — Pull all invoices from GoHighLevel and output to JSON for Notion sync.

Usage:
    python tools/ghl_sync.py              # Full sync, writes JSON
    python tools/ghl_sync.py --dry-run    # Preview only, no file writes

Env vars required (.env):
    GHL_API_KEY
    GHL_LOCATION_ID

Outputs:
    .tmp/ghl_invoices_latest.json   — All invoices from GHL
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
TMP_DIR = PROJECT_ROOT / ".tmp"
OUTPUT_FILE = TMP_DIR / "ghl_invoices_latest.json"

GHL_BASE_URL = "https://services.leadconnectorhq.com"
GHL_INVOICES_ENDPOINT = "/invoices/"
PAGE_SIZE = 100

NOTION_DB_ID = "1b497d29-a8f4-47e1-9bf1-303581b10843"
NOTION_DATASOURCE_ID = "2c55e155-3526-4649-9bdb-c0ee6917476b"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_env():
    """Load environment variables from .env file."""
    if not ENV_PATH.exists():
        print(f"ERROR: .env file not found at {ENV_PATH}")
        sys.exit(1)
    load_dotenv(ENV_PATH)

    api_key = os.getenv("GHL_API_KEY")
    location_id = os.getenv("GHL_LOCATION_ID")

    if not api_key or not location_id:
        print("ERROR: GHL_API_KEY and GHL_LOCATION_ID must be set in .env")
        sys.exit(1)

    return api_key, location_id


def fetch_all_invoices(api_key: str, location_id: str) -> list[dict]:
    """Fetch all invoices from GHL, handling pagination."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Version": "2021-07-28",
        "Accept": "application/json",
    }

    all_invoices = []
    offset = 0

    while True:
        params = {
            "altType": "location",
            "altId": location_id,
            "limit": PAGE_SIZE,
            "offset": offset,
            "status": "all",
        }

        print(f"  Fetching invoices (offset={offset})...")

        try:
            resp = requests.get(
                f"{GHL_BASE_URL}{GHL_INVOICES_ENDPOINT}",
                headers=headers,
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"ERROR: GHL API returned {resp.status_code}: {resp.text}")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Request failed: {e}")
            sys.exit(1)

        data = resp.json()
        invoices = data.get("invoices", data.get("data", []))

        if not invoices:
            break

        all_invoices.extend(invoices)
        offset += PAGE_SIZE

        # If we got fewer than PAGE_SIZE results, we've reached the end
        if len(invoices) < PAGE_SIZE:
            break

    return all_invoices


def load_previous_sync() -> dict:
    """Load previously synced invoices from the output file, if it exists."""
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, "r") as f:
                data = json.load(f)
            return {inv.get("_id", inv.get("id", "")): inv for inv in data.get("invoices", [])}
        except (json.JSONDecodeError, KeyError):
            return {}
    return {}


def extract_invoice_number(invoice: dict) -> str:
    """Extract a usable invoice number/ID from an invoice object."""
    return invoice.get("invoiceNumber", invoice.get("number", invoice.get("_id", invoice.get("id", "unknown"))))


def extract_amount(invoice: dict) -> float:
    """Extract total amount from an invoice. GHL returns amounts in dollars."""
    amount = invoice.get("total", invoice.get("amount", invoice.get("amountDue", 0)))
    return float(amount) if amount else 0.0


def extract_date(invoice: dict) -> str:
    """Extract and format the invoice date."""
    date_str = invoice.get("issueDate", invoice.get("createdAt", invoice.get("dueDate", "")))
    if not date_str:
        return "unknown"
    try:
        # Handle ISO format
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return str(date_str)[:10]


def extract_year(invoice: dict) -> str:
    """Extract year from invoice date."""
    date = extract_date(invoice)
    if date and date != "unknown":
        return date[:4]
    return "unknown"


def compute_summary(invoices: list[dict], previous: dict) -> dict:
    """Compute sync summary stats."""
    total = len(invoices)

    current_ids = set()
    for inv in invoices:
        inv_id = inv.get("_id", inv.get("id", ""))
        current_ids.add(inv_id)

    previous_ids = set(previous.keys())
    new_ids = current_ids - previous_ids
    new_invoices = [inv for inv in invoices if inv.get("_id", inv.get("id", "")) in new_ids]

    # Revenue by year
    revenue_by_year = defaultdict(float)
    for inv in invoices:
        year = extract_year(inv)
        revenue_by_year[year] += extract_amount(inv)

    # Revenue by status
    revenue_by_status = defaultdict(float)
    count_by_status = defaultdict(int)
    for inv in invoices:
        status = inv.get("status", "unknown")
        revenue_by_status[status] += extract_amount(inv)
        count_by_status[status] += 1

    return {
        "total_invoices": total,
        "previously_synced": len(previous_ids),
        "new_since_last_sync": len(new_ids),
        "new_invoices": new_invoices,
        "revenue_by_year": dict(revenue_by_year),
        "revenue_by_status": dict(revenue_by_status),
        "count_by_status": dict(count_by_status),
    }


def print_summary(summary: dict):
    """Print a human-readable sync summary."""
    print("\n" + "=" * 60)
    print("GHL INVOICE SYNC SUMMARY")
    print("=" * 60)
    print(f"  Total invoices in GHL:    {summary['total_invoices']}")
    print(f"  Previously synced:        {summary['previously_synced']}")
    print(f"  New since last sync:      {summary['new_since_last_sync']}")

    print("\n  Revenue by Year:")
    for year in sorted(summary["revenue_by_year"].keys()):
        amt = summary["revenue_by_year"][year]
        print(f"    {year}: ${amt:,.2f}")

    print("\n  Invoices by Status:")
    for status, count in sorted(summary["count_by_status"].items()):
        amt = summary["revenue_by_status"][status]
        print(f"    {status}: {count} invoices (${amt:,.2f})")

    if summary["new_invoices"]:
        print(f"\n  New Invoices to Add to Notion ({summary['new_since_last_sync']}):")
        print(f"  Notion DB: {NOTION_DB_ID}")
        print("  -" * 30)
        for inv in summary["new_invoices"]:
            num = extract_invoice_number(inv)
            amt = extract_amount(inv)
            date = extract_date(inv)
            status = inv.get("status", "unknown")
            name = inv.get("contactName", inv.get("name", inv.get("title", "—")))
            print(f"    #{num} | {date} | {name} | ${amt:,.2f} | {status}")
    else:
        print("\n  No new invoices to sync. Notion is up to date.")

    print("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Sync GHL invoices to JSON for Notion.")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, do not write files.")
    args = parser.parse_args()

    print("GHL Invoice Sync")
    print("-" * 40)

    # Load credentials
    api_key, location_id = load_env()
    print(f"  Location ID: {location_id}")

    # Load previous sync data
    previous = load_previous_sync()
    if previous:
        print(f"  Previous sync found: {len(previous)} invoices on file")
    else:
        print("  No previous sync found (first run)")

    # Fetch from GHL
    print("\nFetching invoices from GHL...")
    invoices = fetch_all_invoices(api_key, location_id)
    print(f"  Retrieved {len(invoices)} invoices total")

    # Compute and print summary
    summary = compute_summary(invoices, previous)
    print_summary(summary)

    # Write output
    if args.dry_run:
        print("\n[DRY RUN] No files written.")
    else:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        output = {
            "synced_at": datetime.now().isoformat(),
            "location_id": location_id,
            "total_count": len(invoices),
            "invoices": invoices,
        }
        with open(OUTPUT_FILE, "w") as f:
            json.dump(output, f, indent=2, default=str)
        print(f"\nInvoice data written to {OUTPUT_FILE}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
