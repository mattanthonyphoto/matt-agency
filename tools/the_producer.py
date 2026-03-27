#!/usr/bin/env python3
"""The Producer — Production management: shoot prep, editor handoff, delivery tracking, cost-share.
Modes: prep | handoff | delivery | costshare"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from agent_utils import (
    send_telegram, search_gmail, get_ghl_opportunities, get_ghl_contacts,
    _calendar_api_call, get_google_creds
)
import requests


# === MODE: SHOOT PREP ===
def shoot_prep():
    """Check tomorrow's calendar for shoots, send prep checklist."""
    tomorrow = datetime.now() + timedelta(days=1)
    start = tomorrow.replace(hour=0, minute=0, second=0).isoformat() + "-07:00"
    end = tomorrow.replace(hour=23, minute=59, second=59).isoformat() + "-07:00"

    events = _calendar_api_call(start, end)

    shoot_events = []
    for e in events:
        summary = e.get("summary", "").lower()
        if any(w in summary for w in ["shoot", "photo", "session", "project", "site visit"]):
            shoot_events.append(e)

    if not shoot_events:
        # Check if any event descriptions mention photography
        for e in events:
            desc = e.get("description", "").lower()
            if any(w in desc for w in ["shoot", "photo", "camera", "drone", "twilight"]):
                shoot_events.append(e)

    if not shoot_events:
        print("No shoots tomorrow (no alert sent)")
        return

    for e in shoot_events:
        summary = e.get("summary", "Untitled")
        location = e.get("location", "TBD")
        start_time = e.get("start", {}).get("dateTime", "")
        description = e.get("description", "")

        try:
            dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            time_str = dt.strftime("%-I:%M %p")
        except:
            time_str = "TBD"

        # Check weather (simple)
        weather_note = "Check weather.gc.ca for Squamish/Whistler forecast"

        msg = f"""<b>📸 SHOOT PREP — TOMORROW</b>
<i>{tomorrow.strftime('%A, %B %d')}</i>

━━━━━━━━━━━━━━━
<b>{summary}</b>
⏰ {time_str}
📍 {location}

━━━━━━━━━━━━━━━
<b>CHECKLIST</b>
━━━━━━━━━━━━━━━
☐ Camera bodies charged (2x)
☐ Lenses: 16-35mm, 24-70mm, 70-200mm
☐ Tripod + L-bracket
☐ Drone charged + spare batteries
☐ Memory cards formatted
☐ Flash + triggers (if interior)
☐ Shot list reviewed
☐ Location scouted (Google Maps)
☐ Client confirmed
☐ Parking/access sorted

━━━━━━━━━━━━━━━
<b>🌤️ WEATHER</b>
━━━━━━━━━━━━━━━
{weather_note}

━━━━━━━━━━━━━━━
<b>📝 NOTES</b>
━━━━━━━━━━━━━━━
{description[:300] if description else 'No notes in calendar event.'}

<i>Pack tonight. Leave 30 min early for Sea-to-Sky.</i>"""

        send_telegram(msg)
    print(f"✅ Shoot Prep: {len(shoot_events)} shoot(s) prepped")


# === MODE: EDITOR HANDOFF ===
def editor_handoff():
    """Check for recently completed shoots that need editor handoff."""
    # Search Gmail for recent shoot-related sent emails (indicates shoot happened)
    recent = search_gmail("(subject:shoot OR subject:photos OR subject:delivery) from:me newer_than:7d", 10)

    # Check GHL for projects in production stage
    opps = get_ghl_opportunities()
    opp_list = opps.get("opportunities", [])

    production = []
    for o in opp_list:
        if o.get("status") != "open":
            continue
        # Check if in production pipeline
        pipeline = o.get("pipelineId", "")
        stage = o.get("pipelineStageId", "")
        name = o.get("name", "Unknown")
        contact = o.get("contact", {})

        # Production pipeline ID from GHL setup
        if pipeline in ["gwY9Bs918EJnG31qua09", "vPYWW2NnhYFcdc7SfwyS"]:
            production.append({
                "name": name,
                "contact": contact.get("name", ""),
                "company": contact.get("companyName", ""),
            })

    if not production:
        print("No projects in production pipeline")
        return

    lines = []
    for p in production:
        lines.append(
            f"• <b>{p['name']}</b>\n"
            f"   Client: {p['company'] or p['contact']}\n"
            f"   ☐ Cull selects\n"
            f"   ☐ Create Dropbox folder\n"
            f"   ☐ Email Alena: photo count + style direction + deadline\n"
            f"   ☐ Set delivery deadline (7 days from today)"
        )

    msg = (
        f"<b>🎬 EDITOR HANDOFF</b>\n"
        f"<i>{datetime.now().strftime('%A, %B %d')}</i>\n\n"
        f"Projects in production:\n\n"
        + "\n\n".join(lines)
        + "\n\n<b>Editor:</b> Alena Machinskaia (alenamachin@gmail.com, $2.50/photo)"
        + "\n\n<i>Cull today, send to Alena tonight.</i>"
    )
    send_telegram(msg)
    print(f"✅ Editor Handoff: {len(production)} projects flagged")


# === MODE: DELIVERY TRACKER ===
def delivery_tracker():
    """Track projects post-shoot — alert if delivery is overdue."""
    opps = get_ghl_opportunities()
    opp_list = opps.get("opportunities", [])
    now = datetime.now()

    alerts = []
    for o in opp_list:
        if o.get("status") != "open":
            continue
        pipeline = o.get("pipelineId", "")
        # Production pipelines
        if pipeline not in ["gwY9Bs918EJnG31qua09", "vPYWW2NnhYFcdc7SfwyS"]:
            continue

        name = o.get("name", "Unknown")
        last_change = o.get("lastStageChangeAt", o.get("updatedAt", ""))
        try:
            last_dt = datetime.fromisoformat(last_change.replace("Z", "+00:00")).replace(tzinfo=None)
            age = (now - last_dt).days
        except:
            age = 0

        if age >= 10:
            alerts.append(f"🔴 <b>{name}</b> — {age} days since last update. Client expecting delivery!")
        elif age >= 7:
            alerts.append(f"🟡 <b>{name}</b> — {age} days. Standard delivery window closing.")
        elif age >= 5:
            alerts.append(f"🟢 <b>{name}</b> — {age} days. Edits should be coming back from Alena.")

    if not alerts:
        print("No delivery alerts (no projects in production or all on track)")
        return

    msg = (
        f"<b>📦 DELIVERY TRACKER</b>\n"
        f"<i>{now.strftime('%A, %B %d')}</i>\n\n"
        + "\n\n".join(alerts)
        + "\n\n<i>SOP: Deliver within 7 days of shoot. 10+ days = client anxiety.</i>"
    )
    send_telegram(msg)
    print(f"✅ Delivery Tracker: {len(alerts)} alerts")


# === MODE: COST-SHARE TRIGGER ===
def costshare_trigger():
    """After project delivery, identify cost-share opportunities (30% licensing fee)."""
    # Search for recent delivery emails
    deliveries = search_gmail("subject:(delivery OR final OR photos OR dropbox) from:me newer_than:14d", 10)

    if not deliveries:
        print("No recent deliveries found")
        return

    msg = (
        f"<b>💰 COST-SHARE OPPORTUNITIES</b>\n"
        f"<i>{datetime.now().strftime('%A, %B %d')}</i>\n\n"
        f"Recent deliveries found ({len(deliveries)}). For each completed project:\n\n"
        f"<b>Checklist:</b>\n"
        f"☐ Identify all parties: architect, designer, builder, sub-trades\n"
        f"☐ Draft licensing email (30% fee per additional party)\n"
        f"☐ Reference: 90% hit rate, near-100% margin\n"
        f"☐ Include portfolio link + usage terms\n\n"
        f"<b>Template opener:</b>\n"
        f"\"Hi [Name], I recently photographed [Project] with [Builder]. "
        f"I'd love to offer you licensed use of these images for your portfolio "
        f"and marketing. Here's a preview...\"\n\n"
        f"<b>2025 cost-share revenue: $7,822</b>\n"
        f"<b>2026 target: $15,000+</b>\n\n"
        f"<i>Every project is worth 1.3-1.9x its face value with cost-share.</i>"
    )
    send_telegram(msg)
    print("✅ Cost-Share Trigger sent")


# === MAIN ===
MODES = {
    "prep": shoot_prep,
    "handoff": editor_handoff,
    "delivery": delivery_tracker,
    "costshare": costshare_trigger,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in MODES:
        print(f"Usage: python3 the_producer.py <{'|'.join(MODES.keys())}>")
        sys.exit(1)
    mode = sys.argv[1]
    print(f"🎬 Running Producer: {mode}")
    MODES[mode]()
