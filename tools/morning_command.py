#!/usr/bin/env python3
"""Morning Command — Daily briefing: calendar + email + pipeline + campaigns + actions. Sends to Telegram."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from agent_utils import (
    send_telegram, get_today_events, search_gmail,
    get_ghl_opportunities, get_instantly_campaigns, get_instantly_replies
)

def format_time(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%-I:%M %p")
    except:
        return dt_str

def run():
    today = datetime.now().strftime("%A, %B %d, %Y")

    # --- CALENDAR ---
    events = get_today_events()
    cal_lines = []
    if not events:
        cal_lines.append("No events scheduled — open day for deep work")
    for e in events:
        start = e.get("start", {}).get("dateTime", e.get("start", {}).get("date", ""))
        end = e.get("end", {}).get("dateTime", "")
        summary = e.get("summary", "Untitled")
        location = e.get("location", "")
        time_str = format_time(start)
        if end:
            time_str += f" – {format_time(end)}"
        line = f"• <b>{time_str}</b> — {summary}"
        if location:
            line += f"\n   📍 {location}"
        cal_lines.append(line)

    # --- EMAIL ---
    emails = search_gmail("newer_than:1d -category:promotions -category:social -category:updates", 20)
    email_lines = []
    drafts_unsent = []
    for m in emails:
        if "DRAFT" in m["labels"] and "SENT" not in m["labels"]:
            drafts_unsent.append(m)
            continue
        if "SENT" in m["labels"] and "INBOX" not in m["labels"]:
            continue
        sender = m["from"].split("<")[0].strip().strip('"')
        subj = m["subject"][:60]
        snippet = m["snippet"][:80]
        email_lines.append(f"• <b>{sender}</b> — {subj}\n   ↳ {snippet}")
    if not email_lines:
        email_lines.append("Inbox clear")
    if drafts_unsent:
        names = [d["to"].split("<")[0].strip().strip('"')[:20] for d in drafts_unsent[:7]]
        email_lines.append(f"\n⚠️ <b>{len(drafts_unsent)} unsent drafts</b> — {', '.join(names)}")

    # --- DEAL PULSE (GHL) ---
    opps = get_ghl_opportunities()
    opp_list = opps.get("opportunities", [])
    now = datetime.now()
    red, yellow, green = [], [], []
    pipeline_value = 0
    for o in opp_list:
        if o.get("status") != "open":
            continue
        name = o.get("name", "Unknown")
        value = o.get("monetaryValue", 0) or 0
        pipeline_value += value
        last_change = o.get("lastStageChangeAt", o.get("updatedAt", ""))
        try:
            last_dt = datetime.fromisoformat(last_change.replace("Z", "+00:00")).replace(tzinfo=None)
            age = (now - last_dt).days
        except:
            age = 99
        val_str = f" (${value:,.0f})" if value else ""
        entry = f"{name}{val_str}"
        if age > 3:
            red.append(f"{entry} — {age}d stale")
        elif age > 1:
            yellow.append(entry)
        else:
            green.append(entry)

    deal_lines = []
    if red:
        deal_lines.append("🔴 " + " | ".join(red[:5]))
    if yellow:
        deal_lines.append("🟡 " + " | ".join(yellow[:5]))
    if green:
        deal_lines.append("🟢 " + " | ".join(green[:5]))
    active_count = len(red) + len(yellow) + len(green)
    deal_lines.append(f"Pipeline value: ${pipeline_value:,.0f} | Deals: {active_count}")

    # --- CAMPAIGNS (Instantly) ---
    campaigns = get_instantly_campaigns()
    camp_lines = []
    if isinstance(campaigns, list):
        camp_data = campaigns
    else:
        camp_data = campaigns.get("items", campaigns.get("data", []))
    for c in camp_data:
        name = c.get("name", "?")
        status = "Active" if c.get("status") == 1 else "Paused"
        camp_lines.append(f"{name}: {status}")
    if not camp_lines:
        camp_lines.append("Could not fetch campaign data")

    # --- BUILD MESSAGES ---
    msg1 = f"""<b>☀️ MORNING COMMAND</b>
<i>{today} · Squamish, BC</i>

━━━━━━━━━━━━━━━
<b>📅 TODAY'S SCHEDULE</b>
━━━━━━━━━━━━━━━
{chr(10).join(cal_lines)}

━━━━━━━━━━━━━━━
<b>📧 EMAIL HIGHLIGHTS</b>
━━━━━━━━━━━━━━━
{chr(10).join(email_lines)}

━━━━━━━━━━━━━━━
<b>🎯 DEAL PULSE</b>
━━━━━━━━━━━━━━━
{chr(10).join(deal_lines)}"""

    msg2 = f"""<b>📡 CAMPAIGN STATS</b>
━━━━━━━━━━━━━━━
{chr(10).join(camp_lines)}

━━━━━━━━━━━━━━━
<b>⚡ TOP 3 ACTIONS</b>
━━━━━━━━━━━━━━━
1. Follow up on any 🔴 stale deals above
2. Send any unsent Gmail drafts
3. Check Instantly unibox for new replies"""

    send_telegram(msg1)
    send_telegram(msg2)
    print("✅ Morning Command sent to Telegram")

if __name__ == "__main__":
    run()
