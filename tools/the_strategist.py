#!/usr/bin/env python3
"""The Strategist — Learns from data, identifies patterns, suggests improvements.
Modes: campaigns | winloss | competitors | attribution"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from agent_utils import (
    send_telegram, search_gmail, get_ghl_opportunities, get_ghl_contacts,
    get_instantly_campaigns, get_instantly_replies
)
import requests
from agent_utils import INSTANTLY_HEADERS


# === MODE: CAMPAIGN ANALYSIS ===
def campaign_analysis():
    """Deep analysis of cold email campaign performance by ICP."""
    campaigns = get_instantly_campaigns()
    camp_data = campaigns if isinstance(campaigns, list) else campaigns.get("items", campaigns.get("data", []))

    if not camp_data:
        send_telegram("<b>📊 CAMPAIGN ANALYSIS</b>\nCouldn't fetch campaign data.")
        return

    lines = []
    for c in camp_data:
        name = c.get("name", "?")
        status = "Active" if c.get("status") == 1 else "Paused"
        camp_id = c.get("id", "")

        # Try to get analytics
        try:
            r = requests.get(
                f"https://api.instantly.ai/api/v2/campaigns/{camp_id}/analytics",
                headers=INSTANTLY_HEADERS
            )
            if r.ok:
                stats = r.json()
                sent = stats.get("sent", stats.get("total_sent", 0))
                opened = stats.get("opened", stats.get("total_opened", 0))
                replied = stats.get("replied", stats.get("total_replied", 0))
                bounced = stats.get("bounced", stats.get("total_bounced", 0))

                open_rate = (opened / sent * 100) if sent else 0
                reply_rate = (replied / sent * 100) if sent else 0
                bounce_rate = (bounced / sent * 100) if sent else 0

                health = "✅ HEALTHY"
                if bounce_rate > 5:
                    health = "🔴 HIGH BOUNCE"
                elif open_rate < 30:
                    health = "🟡 LOW OPENS"
                elif reply_rate > 3:
                    health = "🟢 STRONG REPLIES"

                lines.append(
                    f"<b>{name}</b> [{status}] {health}\n"
                    f"   Sent: {sent} | Opens: {open_rate:.1f}% | Replies: {reply_rate:.1f}% | Bounce: {bounce_rate:.1f}%"
                )
            else:
                lines.append(f"<b>{name}</b> [{status}]\n   Analytics: endpoint returned {r.status_code}")
        except:
            lines.append(f"<b>{name}</b> [{status}]\n   Analytics: couldn't fetch")

    # Check replies
    replies = get_instantly_replies()
    reply_list = replies if isinstance(replies, list) else replies.get("data", replies.get("items", []))
    reply_count = len(reply_list) if reply_list else 0

    msg = (
        f"<b>📊 CAMPAIGN STRATEGIST</b>\n"
        f"<i>{datetime.now().strftime('%A, %B %d')}</i>\n\n"
        + "\n\n".join(lines)
        + f"\n\n━━━━━━━━━━━━━━━\n"
        f"<b>Total replies in unibox:</b> {reply_count}\n\n"
        f"<b>💡 Recommendations:</b>\n"
        f"• If open rate <40%: test new subject lines\n"
        f"• If reply rate <2%: revisit email copy angle\n"
        f"• If bounce >5%: clean list, re-verify with Icypeas\n"
        f"• Deploy Interior Designers when Builders/Architects >80% sent"
    )
    send_telegram(msg)
    print("✅ Campaign Analysis sent")


# === MODE: WIN/LOSS ANALYSIS ===
def winloss_analysis():
    """Analyze won and lost deals for patterns."""
    opps = get_ghl_opportunities()
    opp_list = opps.get("opportunities", [])

    won = []
    lost = []
    open_deals = []

    for o in opp_list:
        status = o.get("status", "")
        name = o.get("name", "Unknown")
        value = o.get("monetaryValue", 0) or 0
        source = o.get("source", "Unknown")
        contact = o.get("contact", {})
        company = contact.get("companyName", "")
        tags = contact.get("tags", [])

        deal = {"name": name, "value": value, "source": source, "company": company, "tags": tags}

        if status == "won":
            won.append(deal)
        elif status in ["lost", "abandoned"]:
            lost.append(deal)
        elif status == "open":
            open_deals.append(deal)

    # Source analysis
    sources = {}
    for d in won:
        src = d["source"] or "Unknown"
        sources.setdefault(src, {"count": 0, "value": 0})
        sources[src]["count"] += 1
        sources[src]["value"] += d["value"]

    source_lines = []
    for src, data in sorted(sources.items(), key=lambda x: x[1]["value"], reverse=True):
        source_lines.append(f"• <b>{src}</b>: {data['count']} deals, ${data['value']:,.0f}")

    msg = (
        f"<b>📈 WIN/LOSS ANALYSIS</b>\n"
        f"<i>{datetime.now().strftime('%A, %B %d')}</i>\n\n"
        f"<b>Won:</b> {len(won)} deals (${sum(d['value'] for d in won):,.0f})\n"
        f"<b>Lost:</b> {len(lost)} deals\n"
        f"<b>Open:</b> {len(open_deals)} deals (${sum(d['value'] for d in open_deals):,.0f})\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>Revenue by Source:</b>\n"
        + ("\n".join(source_lines) if source_lines else "No source data available")
        + f"\n\n━━━━━━━━━━━━━━━\n"
        f"<b>💡 Insights:</b>\n"
        f"• Close rate: {len(won)}/{len(won)+len(lost)} ({len(won)/(len(won)+len(lost))*100:.0f}%)" if (len(won)+len(lost)) > 0 else "• Close rate: no data yet"
        + f"\n• Avg deal value: ${sum(d['value'] for d in won)/len(won):,.0f}" if won else "\n• Avg deal value: no wins tracked"
    )
    send_telegram(msg)
    print("✅ Win/Loss Analysis sent")


# === MODE: COMPETITOR WATCH ===
def competitor_watch():
    """Check competitor websites for changes."""
    competitors = [
        {"name": "Ema Peter", "url": "https://emapeter.com", "market": "Vancouver luxury"},
        {"name": "Martin Knowles", "url": "https://martinknowles.com", "market": "Vancouver architectural"},
        {"name": "Fyfe Photography", "url": "https://fyfephotography.com", "market": "BC residential"},
        {"name": "Andrew Fyfe", "url": "https://andrewfyfe.com", "market": "BC architectural"},
    ]

    results = []
    for comp in competitors:
        try:
            r = requests.get(comp["url"], timeout=10)
            status = "🟢 Online" if r.status_code == 200 else f"🟡 Status {r.status_code}"
            size = len(r.text)
            results.append(f"• <b>{comp['name']}</b> — {status} ({size:,} bytes)\n   {comp['url']} | Market: {comp['market']}")
        except Exception as e:
            results.append(f"• <b>{comp['name']}</b> — 🔴 Unreachable\n   {comp['url']}")

    msg = (
        f"<b>🔍 COMPETITOR WATCH</b>\n"
        f"<i>{datetime.now().strftime('%A, %B %d')}</i>\n\n"
        + "\n\n".join(results)
        + "\n\n<b>💡 What to monitor:</b>\n"
        f"• New portfolio additions (scroll their project pages)\n"
        f"• Pricing changes (check if they list rates)\n"
        f"• Award wins (check Architizer, Georgie, AIBC)\n"
        f"• New blog/journal content (SEO competition)\n"
        f"• Social media activity (IG post frequency)"
    )
    send_telegram(msg)
    print("✅ Competitor Watch sent")


# === MODE: ATTRIBUTION ===
def attribution_report():
    """Analyze lead sources and channel performance."""
    contacts = get_ghl_contacts(100)
    contact_list = contacts.get("contacts", [])

    sources = {}
    for c in contact_list:
        source = c.get("source", "Unknown") or "Unknown"
        tags = c.get("tags", [])
        sources.setdefault(source, {"count": 0, "tags": {}})
        sources[source]["count"] += 1
        for t in tags:
            sources[source]["tags"].setdefault(t, 0)
            sources[source]["tags"][t] += 1

    lines = []
    for src, data in sorted(sources.items(), key=lambda x: x[1]["count"], reverse=True):
        top_tags = sorted(data["tags"].items(), key=lambda x: x[1], reverse=True)[:3]
        tag_str = ", ".join(f"{t[0]}({t[1]})" for t in top_tags)
        lines.append(f"• <b>{src}</b>: {data['count']} contacts\n   Tags: {tag_str or 'none'}")

    msg = (
        f"<b>📊 ATTRIBUTION REPORT</b>\n"
        f"<i>{datetime.now().strftime('%A, %B %d')}</i>\n\n"
        f"<b>Lead Sources ({len(contact_list)} total contacts):</b>\n\n"
        + "\n\n".join(lines[:15])
        + f"\n\n━━━━━━━━━━━━━━━\n"
        f"<b>💡 Key Questions:</b>\n"
        f"• Which source converts to paid work?\n"
        f"• Which source has highest avg deal value?\n"
        f"• Where should you spend more time/money?\n\n"
        f"<i>Tag every new contact with source in GHL to improve this data.</i>"
    )
    send_telegram(msg)
    print("✅ Attribution Report sent")


# === MAIN ===
MODES = {
    "campaigns": campaign_analysis,
    "winloss": winloss_analysis,
    "competitors": competitor_watch,
    "attribution": attribution_report,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in MODES:
        print(f"Usage: python3 the_strategist.py <{'|'.join(MODES.keys())}>")
        sys.exit(1)
    mode = sys.argv[1]
    print(f"🧠 Running Strategist: {mode}")
    MODES[mode]()
