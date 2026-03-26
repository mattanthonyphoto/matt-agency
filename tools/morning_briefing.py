"""Morning briefing tool — read unified Pipeline, prioritize leads, output daily action list.

Subcommands:
  briefing     Full morning briefing with prioritized actions
  follow-ups   Just the follow-up list (plan sent, no reply)
  stats        Pipeline summary stats
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.google_sheets_auth import get_sheets_service

load_dotenv(PROJECT_ROOT / ".env")

PIPELINE_SHEET_ID = "1m8q6yIqq3jzYGkLwgFVD6d_WlAzMFgz-gRekdysE1IQ"

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
P_SERVICE_TYPE = 10
P_EST_VALUE = 11
P_PLAN_SENT = 12
P_PLAN_URL = 13
P_DAYS_SINCE_PLAN = 14
P_NEXT_ACTION = 15
P_ACTION_DATE = 16
P_CLOSE_DATE = 17
P_LOSS_REASON = 18
P_NOTES = 19


def _read_pipeline():
    """Read all rows from the unified Pipeline."""
    sheets = get_sheets_service()
    try:
        result = sheets.spreadsheets().values().get(
            spreadsheetId=PIPELINE_SHEET_ID,
            range="'Pipeline'!A:T",
        ).execute()
        rows = result.get("values", [])
    except Exception as e:
        print(f"ERROR reading Pipeline: {e}", file=sys.stderr)
        return []

    if len(rows) < 2:
        return []

    leads = []
    for row in rows[1:]:
        while len(row) < 20:
            row.append("")
        leads.append({
            "company": row[P_COMPANY],
            "contact": row[P_CONTACT],
            "email": row[P_EMAIL],
            "phone": row[P_PHONE],
            "icp": row[P_ICP],
            "source": row[P_SOURCE],
            "stage": row[P_STAGE],
            "date_added": row[P_DATE_ADDED],
            "last_activity": row[P_LAST_ACTIVITY],
            "signal": row[P_SIGNAL],
            "service_type": row[P_SERVICE_TYPE],
            "est_value": row[P_EST_VALUE],
            "plan_sent": row[P_PLAN_SENT],
            "plan_url": row[P_PLAN_URL],
            "days_since_plan": row[P_DAYS_SINCE_PLAN],
            "next_action": row[P_NEXT_ACTION],
            "action_date": row[P_ACTION_DATE],
            "close_date": row[P_CLOSE_DATE],
            "loss_reason": row[P_LOSS_REASON],
            "notes": row[P_NOTES],
        })

    return leads


def _parse_date(date_str):
    """Try to parse a date string, return date object or None."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%b %d, %Y", "%B %d, %Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _days_since(date_str):
    """Calculate days since a date string."""
    # If it's already a number (from the sheet formula), return it
    try:
        return int(float(date_str))
    except (ValueError, TypeError):
        pass

    parsed = _parse_date(date_str)
    if isinstance(parsed, date):
        return (date.today() - parsed).days
    return None


def _read_queued_plans():
    """Read leads from Pipeline that are lead magnet requests without a plan yet."""
    sheets = get_sheets_service()
    try:
        result = sheets.spreadsheets().values().get(
            spreadsheetId=PIPELINE_SHEET_ID,
            range="'Pipeline'!A:T",
        ).execute()
        rows = result.get("values", [])
    except Exception:
        return []

    queued = []
    for row in rows[1:]:
        while len(row) < 20:
            row.append("")
        source = row[P_SOURCE].strip()
        plan_url = row[P_PLAN_URL].strip()
        stage = row[P_STAGE].strip()
        if source == "Lead Magnet" and not plan_url and stage not in ("Won", "Lost", "Dormant", "Do Not Contact"):
            queued.append({
                "company": row[P_COMPANY],
                "contact": row[P_CONTACT],
                "email": row[P_EMAIL],
                "date_added": row[P_DATE_ADDED],
            })
    return queued


def _categorize_leads(leads):
    """Sort leads into priority buckets."""
    urgent = []      # Replied — handle today
    action = []      # Follow-ups due or multi-openers
    watch = []       # Mild signals, no action needed
    stale = []       # 14+ days no movement

    for lead in leads:
        stage = lead["stage"].strip()
        days = _days_since(lead["days_since_plan"])

        # Skip closed/archived
        if stage.lower() in ("won", "lost", "dormant", "do not contact"):
            continue

        # Replied = urgent
        if "replied" in lead["signal"].lower() and stage.lower() not in ("discovery booked", "discovery done", "proposal sent"):
            lead["_action"] = "Read reply, respond personally, offer a call"
            urgent.append(lead)
            continue

        # Plan sent, 5+ days, no reply = follow-up needed
        if lead["plan_sent"] and days is not None and days >= 5 and stage.lower() not in ("discovery booked", "discovery done", "proposal sent"):
            lead["_action"] = f"Send nudge (plan sent {days} days ago, no reply)"
            action.append(lead)
            continue

        # Opened 3+ = generate plan
        if "opened" in lead["signal"].lower():
            try:
                open_count = int("".join(c for c in lead["signal"] if c.isdigit()) or "0")
            except ValueError:
                open_count = 0
            if open_count >= 3 and not lead["plan_sent"]:
                lead["_action"] = f"Generate marketing plan and send ({lead['signal']})"
                action.append(lead)
                continue

        # Stale: in pipeline 14+ days with plan sent, no movement
        if days is not None and days >= 14:
            lead["_action"] = f"Stale — {days} days since plan, consider archiving"
            stale.append(lead)
            continue

        # Everything else = watch
        lead["_action"] = "Monitor — no action needed yet"
        watch.append(lead)

    return urgent, action, watch, stale


# ── briefing ────────────────────────────────────────────────

def briefing(args):
    """Full morning briefing with prioritized actions."""
    if not args.skip_refresh:
        print("Refreshing Instantly signals...", file=sys.stderr)
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "tools" / "instantly_monitor.py"),
             "pull-leads", "--campaign", "all"],
            capture_output=True, text=True,
        )
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "tools" / "instantly_monitor.py"),
             "sync-pipeline"],
            capture_output=True, text=True,
        )

    leads = _read_pipeline()
    queued_plans = _read_queued_plans()

    if not leads and not queued_plans:
        print(f"\n=== MORNING BRIEFING — {date.today().strftime('%b %d, %Y')} ===\n")
        print("No leads in Pipeline yet. Campaigns are still warming up.")
        print("Run: python3 tools/instantly_monitor.py pull-leads --campaign all")
        return 0

    if not leads:
        leads = []

    urgent, action, watch, stale_leads = _categorize_leads(leads)

    today_str = date.today().strftime("%b %d, %Y")
    print(f"\n{'=' * 50}")
    print(f"  MORNING BRIEFING — {today_str}")
    print(f"{'=' * 50}")

    # Urgent
    if urgent:
        print(f"\n  URGENT (reply today):")
        for i, lead in enumerate(urgent, 1):
            print(f"    {i}. {lead['contact']} ({lead['company']}) — {lead['signal']}")
            print(f"       -> {lead['_action']}")
            if lead["email"]:
                print(f"       Email: {lead['email']}")
    else:
        print(f"\n  No urgent replies today.")

    # Action
    if action:
        print(f"\n  ACTION (do this morning):")
        for i, lead in enumerate(action, len(urgent) + 1):
            print(f"    {i}. {lead['contact']} ({lead['company']}) — {lead['signal']}")
            print(f"       -> {lead['_action']}")
            if lead["email"]:
                print(f"       Email: {lead['email']}")
            if lead["plan_url"]:
                print(f"       Plan: {lead['plan_url']}")

    # Watch
    if watch:
        print(f"\n  WATCH (no action needed):")
        for lead in watch:
            print(f"    - {lead['contact']} ({lead['company']}) — {lead['stage']}: {lead['signal']}")

    # Stale
    if stale_leads:
        print(f"\n  STALE (consider archiving):")
        for lead in stale_leads:
            print(f"    - {lead['contact']} ({lead['company']}) — {lead['_action']}")

    # Queued plan requests (lead magnet)
    if queued_plans:
        print(f"\n  QUEUED PLANS ({len(queued_plans)} pending):")
        for q in queued_plans:
            print(f"    {q['company']} — {q['contact']} <{q['email']}> — Added {q['date_added']}")
        print(f"    -> Run: python3 tools/generate_queued_plans.py")

    # Summary
    active_leads = [l for l in leads if l["stage"].lower() not in ("won", "lost", "dormant", "do not contact")]
    plans_sent = sum(1 for l in leads if l["plan_sent"])
    print(f"\n{'─' * 50}")
    summary_parts = [f"{len(active_leads)} active", f"{len(urgent) + len(action)} actions today", f"{plans_sent} plans sent"]
    if queued_plans:
        summary_parts.append(f"{len(queued_plans)} plans queued")
    print(f"  Pipeline: {' | '.join(summary_parts)}")
    print(f"{'─' * 50}\n")

    return 0


# ── follow-ups ──────────────────────────────────────────────

def follow_ups(args):
    """Show only leads needing follow-up (plan sent, no reply)."""
    leads = _read_pipeline()

    overdue = []
    for lead in leads:
        if lead["plan_sent"]:
            days = _days_since(lead["days_since_plan"])
            if days is not None and days >= 5 and lead["stage"].lower() not in ("discovery booked", "discovery done", "proposal sent", "won", "lost"):
                lead["_days"] = days
                overdue.append(lead)

    overdue.sort(key=lambda x: -x["_days"])

    if not overdue:
        print("No follow-ups due. All plans are either fresh or already handled.")
        return 0

    print(f"\n  FOLLOW-UPS DUE ({len(overdue)} leads):\n")
    for lead in overdue:
        print(f"  {lead['contact']} ({lead['company']})")
        print(f"    Plan sent {lead['_days']} days ago | Stage: {lead['stage']} | Source: {lead['source']}")
        print(f"    Email: {lead['email']}")
        if lead["plan_url"]:
            print(f"    Plan: {lead['plan_url']}")
        print()

    return 0


# ── stats ───────────────────────────────────────────────────

def stats(args):
    """Pipeline summary statistics."""
    leads = _read_pipeline()

    if not leads:
        print("Pipeline is empty.")
        return 0

    # Count by stage
    stage_counts = {}
    for lead in leads:
        s = lead["stage"] or "Unknown"
        stage_counts[s] = stage_counts.get(s, 0) + 1

    # Count by ICP
    icp_counts = {}
    for lead in leads:
        icp = lead["icp"] or "Unknown"
        icp_counts[icp] = icp_counts.get(icp, 0) + 1

    # Count by source
    source_counts = {}
    for lead in leads:
        src = lead["source"] or "Unknown"
        source_counts[src] = source_counts.get(src, 0) + 1

    plans_sent = sum(1 for l in leads if l["plan_sent"])
    active = [l for l in leads if l["stage"].lower() not in ("won", "lost", "dormant", "do not contact")]

    today_str = date.today().strftime("%b %d, %Y")
    print(f"\n{'=' * 50}")
    print(f"  PIPELINE STATS — {today_str}")
    print(f"{'=' * 50}")

    print(f"\n  Total leads: {len(leads)}")
    print(f"  Active leads: {len(active)}")
    print(f"  Plans sent: {plans_sent}")

    print(f"\n  By Stage:")
    for stage, count in sorted(stage_counts.items(), key=lambda x: -x[1]):
        print(f"    {stage}: {count}")

    print(f"\n  By ICP:")
    for icp, count in sorted(icp_counts.items(), key=lambda x: -x[1]):
        print(f"    {icp}: {count}")

    print(f"\n  By Source:")
    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        print(f"    {src}: {count}")

    # Follow-ups due
    overdue = 0
    for lead in leads:
        if lead["plan_sent"]:
            days = _days_since(lead["days_since_plan"])
            if days is not None and days >= 5 and lead["stage"].lower() not in ("discovery booked", "discovery done", "proposal sent", "won", "lost"):
                overdue += 1

    if overdue:
        print(f"\n  Follow-ups overdue: {overdue}")

    # Stale leads
    stale_count = 0
    for lead in leads:
        if lead["plan_sent"]:
            days = _days_since(lead["days_since_plan"])
            if days is not None and days >= 14:
                stale_count += 1

    if stale_count:
        print(f"  Stale leads (14+ days): {stale_count}")

    print(f"\n{'─' * 50}\n")
    return 0


# ── CLI ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Morning outreach briefing")
    sub = parser.add_subparsers(dest="command")

    br = sub.add_parser("briefing", help="Full morning briefing")
    br.add_argument("--skip-refresh", action="store_true",
                    help="Skip refreshing Instantly data first")

    sub.add_parser("follow-ups", help="Show follow-ups due")
    sub.add_parser("stats", help="Pipeline summary stats")

    args = parser.parse_args()

    if args.command == "briefing":
        return briefing(args)
    elif args.command == "follow-ups":
        return follow_ups(args)
    elif args.command == "stats":
        return stats(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
