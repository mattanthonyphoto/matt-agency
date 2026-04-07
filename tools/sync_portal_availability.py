#!/usr/bin/env python3
"""Sync Matt's Google Calendar busy windows to the portal so the booking form
can show real availability.

Writes tools/client-portal/data/availability.json with:
- busy_dates: list of YYYY-MM-DD strings where Matt has events
- last_synced: ISO timestamp

The portal book page reads this and disables those dates in the date picker.

Run as a cron (suggest hourly) to keep it fresh.

Usage: python3 tools/sync_portal_availability.py
"""
import os
import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

OUTPUT = PROJECT_ROOT / "tools" / "client-portal" / "data" / "availability.json"
DAYS_AHEAD = 90


def get_busy_dates():
    """Use existing _calendar_api_call which works with current token scope."""
    try:
        from agent_utils import _calendar_api_call
    except Exception as e:
        print(f"Failed to load agent_utils: {e}")
        return []

    now = datetime.utcnow()
    end = now + timedelta(days=DAYS_AHEAD)

    try:
        events = _calendar_api_call(
            now.isoformat() + "Z",
            end.isoformat() + "Z"
        )
    except Exception as e:
        print(f"Calendar fetch failed: {e}")
        return []

    busy_dates = set()
    for event in events or []:
        # Skip declined events and all-day events that aren't real holds
        status = event.get("status", "")
        if status == "cancelled":
            continue

        start_obj = event.get("start", {})
        end_obj = event.get("end", {})
        start = start_obj.get("dateTime", start_obj.get("date", ""))[:10]
        end_d = end_obj.get("dateTime", end_obj.get("date", ""))[:10]

        if start:
            busy_dates.add(start)
        if end_d and end_d != start:
            try:
                sd = datetime.fromisoformat(start).date()
                ed = datetime.fromisoformat(end_d).date()
                cur = sd
                while cur <= ed:
                    busy_dates.add(cur.isoformat())
                    cur += timedelta(days=1)
            except Exception:
                pass

    return sorted(busy_dates)


def main():
    print(f"Fetching busy windows for next {DAYS_AHEAD} days...")
    busy_dates = get_busy_dates()
    print(f"Found {len(busy_dates)} busy dates")

    output = {
        "busy_dates": busy_dates,
        "last_synced": datetime.utcnow().isoformat() + "Z",
        "days_ahead": DAYS_AHEAD,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {OUTPUT}")
    if busy_dates:
        print(f"  First busy: {busy_dates[0]}")
        print(f"  Last busy: {busy_dates[-1]}")


if __name__ == "__main__":
    main()
