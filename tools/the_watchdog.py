#!/usr/bin/env python3
"""The Watchdog — Silent monitor that only alerts when something's wrong.
Modes: health | gbp | domains | retainer"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from agent_utils import (
    send_telegram, search_gmail, get_ghl_contacts,
    get_instantly_campaigns, get_google_creds
)
import requests


# === MODE: SYSTEM HEALTH ===
def health_check():
    """Check n8n, website, and core integrations."""
    issues = []

    # Check website
    try:
        r = requests.get("https://mattanthonyphoto.com", timeout=10)
        if r.status_code != 200:
            issues.append(f"🔴 <b>Website down</b> — mattanthonyphoto.com returned {r.status_code}")
        load_time = r.elapsed.total_seconds()
        if load_time > 5:
            issues.append(f"🟡 <b>Website slow</b> — {load_time:.1f}s load time (should be <3s)")
    except Exception as e:
        issues.append(f"🔴 <b>Website unreachable</b> — {str(e)[:100]}")

    # Check n8n
    try:
        r = requests.get("https://n8n.srv1277163.hstgr.cloud/healthz", timeout=10)
        if r.status_code != 200:
            issues.append(f"🔴 <b>n8n down</b> — returned {r.status_code}")
    except Exception as e:
        issues.append(f"🔴 <b>n8n unreachable</b> — {str(e)[:100]}")

    # Check GHL API
    try:
        from agent_utils import ghl_get, GHL_LOC
        result = ghl_get("/contacts/", {"locationId": GHL_LOC, "limit": 1})
        if not result.get("contacts") and not result.get("meta"):
            issues.append("🟡 <b>GHL API issue</b> — contacts endpoint returned empty")
    except Exception as e:
        issues.append(f"🔴 <b>GHL API down</b> — {str(e)[:100]}")

    # Check Instantly API
    try:
        campaigns = get_instantly_campaigns()
        if not campaigns:
            issues.append("🟡 <b>Instantly API issue</b> — campaigns endpoint returned empty")
    except Exception as e:
        issues.append(f"🔴 <b>Instantly API down</b> — {str(e)[:100]}")

    # Check Gmail API
    try:
        msgs = search_gmail("newer_than:1d", 1)
        # If we get here, Gmail is working
    except Exception as e:
        issues.append(f"🔴 <b>Gmail API error</b> — {str(e)[:100]}")

    # Check Balmoral website
    try:
        r = requests.get("https://balmoralconstruction.com", timeout=10)
        if r.status_code != 200:
            issues.append(f"🟡 <b>Balmoral site issue</b> — returned {r.status_code}")
    except:
        pass  # Not critical

    if issues:
        msg = (
            f"<b>🚨 WATCHDOG ALERT</b>\n"
            f"<i>{datetime.now().strftime('%A, %B %d — %I:%M %p')}</i>\n\n"
            + "\n\n".join(issues)
            + "\n\n<i>Fix these before they cost you leads.</i>"
        )
        send_telegram(msg)
        print(f"⚠️ Watchdog: {len(issues)} issues found")
    else:
        print("✅ Watchdog: all systems healthy (no alert sent)")


# === MODE: GBP MONITOR ===
def gbp_monitor():
    """Check Gmail for Google Business Profile notifications — new reviews, questions, messages."""
    alerts = []

    # Search for GBP-related emails
    gbp_emails = search_gmail("from:google subject:(review OR question OR message) newer_than:1d", 10)
    for m in gbp_emails:
        subj = m["subject"]
        snippet = m["snippet"][:100]
        if any(w in subj.lower() for w in ["review", "question", "message", "business profile"]):
            alerts.append(f"• <b>{subj}</b>\n   ↳ {snippet}")

    # Also check for direct review notifications
    review_emails = search_gmail("from:noreply@google.com subject:review newer_than:1d", 5)
    for m in review_emails:
        if m["id"] not in [e.get("id") for e in gbp_emails]:
            alerts.append(f"• <b>{m['subject']}</b>\n   ↳ {m['snippet'][:100]}")

    if alerts:
        msg = (
            f"<b>📍 GBP ALERT</b>\n"
            f"<i>{datetime.now().strftime('%A, %B %d')}</i>\n\n"
            + "\n\n".join(alerts)
            + "\n\n<i>Respond within 24 hours — it affects your ranking.</i>"
        )
        send_telegram(msg)
        print(f"✅ GBP Monitor: {len(alerts)} alerts sent")
    else:
        print("✅ GBP Monitor: no new activity (no alert sent)")


# === MODE: DOMAIN REPUTATION ===
def domain_check():
    """Check Instantly sending account health."""
    campaigns = get_instantly_campaigns()
    if not campaigns:
        send_telegram("<b>⚠️ DOMAIN CHECK</b>\nCouldn't fetch Instantly data — check API key.")
        return

    camp_data = campaigns if isinstance(campaigns, list) else campaigns.get("items", campaigns.get("data", []))

    issues = []
    healthy = []

    for c in camp_data:
        name = c.get("name", "?")
        status = c.get("status", 0)
        if status != 1:
            issues.append(f"🔴 <b>{name}</b> — Campaign paused/inactive (status: {status})")
        else:
            healthy.append(name)

    # Check sending accounts
    from agent_utils import INSTANTLY_HEADERS
    try:
        r = requests.get("https://api.instantly.ai/api/v2/accounts", headers=INSTANTLY_HEADERS)
        if r.ok:
            accounts = r.json() if isinstance(r.json(), list) else r.json().get("items", r.json().get("data", []))
            for acct in accounts:
                email = acct.get("email", "?")
                warmup_status = acct.get("warmup_status", acct.get("warmup", "unknown"))
                if isinstance(warmup_status, dict):
                    warmup_status = warmup_status.get("status", "unknown")
                healthy.append(f"{email}: warmup={warmup_status}")
    except:
        issues.append("🟡 <b>Sending accounts</b> — couldn't fetch account health")

    if issues:
        msg = (
            f"<b>📡 DOMAIN REPUTATION ALERT</b>\n"
            f"<i>{datetime.now().strftime('%A, %B %d')}</i>\n\n"
            + "\n\n".join(issues)
            + f"\n\nHealthy: {', '.join(healthy[:5])}"
        )
        send_telegram(msg)
        print(f"⚠️ Domain Check: {len(issues)} issues")
    else:
        print(f"✅ Domain Check: all healthy — {len(healthy)} accounts/campaigns OK (no alert sent)")


# === MODE: RETAINER TRACKER ===
def retainer_tracker():
    """Check retainer deliverable status for Balmoral and any other retainer clients."""
    now = datetime.now()
    month = now.strftime("%B %Y")

    # Check Gmail for Balmoral-related activity this month
    balmoral_emails = search_gmail(f"(to:marc@balmoralconstruction.com OR from:marc@balmoralconstruction.com) newer_than:30d", 20)

    sent_count = sum(1 for m in balmoral_emails if "SENT" in m.get("labels", []))
    received_count = sum(1 for m in balmoral_emails if "INBOX" in m.get("labels", []))

    # Balmoral retainer deliverables checklist
    deliverables = [
        {"task": "Website maintenance/updates", "monthly": True},
        {"task": "SEO blog post or content update", "monthly": True},
        {"task": "Monthly performance report", "monthly": True},
        {"task": "Google Business Profile update", "monthly": True},
    ]

    msg = (
        f"<b>📋 RETAINER TRACKER</b>\n"
        f"<i>{month}</i>\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>🏗️ BALMORAL CONSTRUCTION</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Revenue: $1,260/mo (web $367.50 + SEO $892.50)\n"
        f"Emails sent to Marc: {sent_count}\n"
        f"Emails from Marc: {received_count}\n\n"
        f"<b>Monthly Deliverables:</b>\n"
    )

    for d in deliverables:
        msg += f"☐ {d['task']}\n"

    msg += (
        f"\n<b>Retainer pitch ($2,500/mo)</b> sent Mar 24 — check status\n"
        f"<b>Search Console</b> access still broken — needs fix\n"
        f"<b>Fitzsimmons North</b> — next photography project\n\n"
    )

    # Check for other retainer clients
    msg += (
        f"━━━━━━━━━━━━━━━\n"
        f"<b>🧘 SHALA YOGA</b> — $105/mo hosting\n"
        f"<b>💇 CARMEN CHORNELL</b> — $52.50/mo hosting\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<i>Hosting clients = passive. No deliverables needed.</i>"
    )

    send_telegram(msg)
    print("✅ Retainer Tracker sent")


# === MAIN ===
MODES = {
    "health": health_check,
    "gbp": gbp_monitor,
    "domains": domain_check,
    "retainer": retainer_tracker,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in MODES:
        print(f"Usage: python3 the_watchdog.py <{'|'.join(MODES.keys())}>")
        sys.exit(1)
    mode = sys.argv[1]
    print(f"👁️ Running Watchdog: {mode}")
    MODES[mode]()
