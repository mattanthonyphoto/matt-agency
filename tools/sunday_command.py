#!/usr/bin/env python3
"""Sunday Command — Weekly business review: revenue, pipeline, campaigns, cash flow, week ahead. Sends to Telegram."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from agent_utils import (
    send_telegram, get_week_events, search_gmail,
    get_ghl_opportunities, get_ghl_invoices, get_instantly_campaigns
)

def format_time(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%-I:%M %p")
    except:
        return dt_str

def run():
    now = datetime.now()
    week_start = now.strftime("%B %d")
    week_end = (now + timedelta(days=6)).strftime("%B %d, %Y")

    # === REVENUE ===
    invoices_data = get_ghl_invoices()
    invoices = invoices_data.get("invoices", invoices_data.get("data", []))
    ytd_revenue = 0
    outstanding = []
    month_revenue = 0
    for inv in invoices:
        amount = inv.get("amount", inv.get("total", 0)) or 0
        # Convert cents to dollars if needed
        if amount > 10000:
            amount = amount / 100
        status = inv.get("status", "").lower()
        name = inv.get("name", inv.get("title", inv.get("contactName", "Unknown")))
        created = inv.get("createdAt", inv.get("created_at", ""))

        if status in ["paid", "completed"]:
            # Check if 2026
            if "2026" in str(created):
                ytd_revenue += amount
                if now.strftime("%Y-%m") in str(created):
                    month_revenue += amount
        elif status in ["sent", "viewed", "overdue", "unpaid"]:
            age_str = ""
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00")).replace(tzinfo=None)
                age = (now - created_dt).days
                age_str = f" ({age}d)"
            except:
                pass
            outstanding.append(f"{name}: ${amount:,.0f}{age_str}")

    recurring = 1417.50
    ytd_with_recurring = ytd_revenue + (recurring * now.month)
    gap = 125000 - ytd_with_recurring
    months_left = 12 - now.month
    required_pace = gap / months_left if months_left > 0 else gap

    # === PIPELINE ===
    opps = get_ghl_opportunities()
    opp_list = opps.get("opportunities", [])
    hot, warm, nurture, stale_list = [], [], [], []
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
        if age > 7:
            stale_list.append(name)
        val_str = f" (${value:,.0f})" if value else ""
        if age <= 3:
            hot.append(f"{name}{val_str}")
        elif age <= 7:
            warm.append(f"{name}{val_str}")
        else:
            nurture.append(f"{name}{val_str}")

    # === CAMPAIGNS ===
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

    # === WEEK AHEAD ===
    events = get_week_events()
    day_map = {}
    for e in events:
        start = e.get("start", {}).get("dateTime", e.get("start", {}).get("date", ""))
        summary = e.get("summary", "Untitled")
        try:
            dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            day = dt.strftime("%A %b %d")
        except:
            day = "TBD"
        day_map.setdefault(day, []).append(summary)
    week_lines = []
    for day, items in sorted(day_map.items()):
        week_lines.append(f"<b>{day}</b>: {', '.join(items[:3])}")
    if not week_lines:
        week_lines.append("Calendar is open — block time for prospecting")

    # === PAYMENT EMAILS ===
    payment_emails = search_gmail("payment OR e-transfer OR invoice newer_than:7d", 10)
    payment_notes = []
    for m in payment_emails:
        if "INBOX" in m["labels"]:
            sender = m["from"].split("<")[0].strip().strip('"')
            payment_notes.append(f"{sender}: {m['subject'][:50]}")

    # === BUILD MESSAGES ===
    outstanding_str = "\n".join(outstanding[:5]) if outstanding else "None"

    msg1 = f"""<b>📊 SUNDAY COMMAND</b>
<i>Week of {week_start} – {week_end}</i>

━━━━━━━━━━━━━━━
<b>💰 REVENUE</b>
━━━━━━━━━━━━━━━
YTD (est): ${ytd_with_recurring:,.0f} / $125,000 ({ytd_with_recurring/1250:.0f}%)
This month: ${month_revenue + recurring:,.0f}
Recurring: $1,417.50/mo
Gap remaining: ${gap:,.0f}
Required pace: ${required_pace:,.0f}/mo for {months_left} months

💳 Outstanding:
{outstanding_str}

━━━━━━━━━━━━━━━
<b>🎯 PIPELINE</b>
━━━━━━━━━━━━━━━
Total value: ${pipeline_value:,.0f} | Open deals: {len(hot)+len(warm)+len(nurture)}
🔴 Hot: {', '.join(hot[:5]) if hot else 'None'}
🟡 Warm: {', '.join(warm[:5]) if warm else 'None'}
🟢 Nurture: {', '.join(nurture[:5]) if nurture else 'None'}
Stale (>7d): {len(stale_list)}"""

    msg2 = f"""<b>📡 COLD EMAIL</b>
━━━━━━━━━━━━━━━
{chr(10).join(camp_lines)}

━━━━━━━━━━━━━━━
<b>⚠️ CASH FLOW</b>
━━━━━━━━━━━━━━━
Monthly burn: ~$7,200 (personal $6,580 + software ~$600)
Recurring revenue: $1,417.50/mo
Gap to breakeven: ~$5,783/mo from project work
LOC balance: $16,574 / $35,000 (8.94%)

🔔 FHSA: Must open before Dec 31, 2026 ($8,000 deduction)
🔔 Steel Wood: $1,575 outstanding since Jul 2025"""

    msg3 = f"""<b>📅 WEEK AHEAD</b>
━━━━━━━━━━━━━━━
{chr(10).join(week_lines)}

━━━━━━━━━━━━━━━
<b>⚡ TOP 3 PRIORITIES</b>
━━━━━━━━━━━━━━━
1. Close any stale deals — {len(stale_list)} opportunities aging out
2. Follow up Balmoral retainer pitch (sent Mar 24)
3. Send all unsent Gmail drafts from networking

━━━━━━━━━━━━━━━
<b>💡 WEEKLY INSIGHT</b>
━━━━━━━━━━━━━━━
{len(hot)+len(warm)} active pipeline deals against a ${required_pace:,.0f}/mo target. At avg $4,000/deal, you need ~{int(required_pace/4000)+1} closes per month. Every stale deal is lost momentum — follow up before they go cold."""

    send_telegram(msg1)
    send_telegram(msg2)
    send_telegram(msg3)
    print("✅ Sunday Command sent to Telegram (3 messages)")

if __name__ == "__main__":
    run()
