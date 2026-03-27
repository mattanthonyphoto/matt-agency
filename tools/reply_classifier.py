#!/usr/bin/env python3
"""Reply Classifier — Monitors Instantly for cold email replies, classifies, creates GHL contacts, alerts via Telegram."""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from agent_utils import (
    send_telegram, get_instantly_replies, ghl_get, GHL_LOC, GHL_BASE, GHL_HEADERS
)
import requests

def classify_reply(text):
    text_lower = text.lower()
    if any(w in text_lower for w in ["out of office", "ooo", "auto-reply", "away from", "on vacation", "maternity", "returning"]):
        return "⚪ OOO", "ooo"
    if any(w in text_lower for w in ["unsubscribe", "remove me", "stop emailing", "take me off", "opt out", "don't contact"]):
        return "🔴 UNSUBSCRIBE", "unsubscribe"
    if any(w in text_lower for w in ["wrong person", "no longer", "not the right", "try reaching", "forward this to", "suggest you contact"]):
        return "🔵 WRONG PERSON", "wrong_person"
    if any(w in text_lower for w in ["not interested", "no thanks", "not right now", "already have", "not looking", "no need", "too expensive", "budget"]):
        return "🟠 OBJECTION", "objection"
    if any(w in text_lower for w in ["pricing", "rates", "cost", "how much", "packages", "quote", "fee"]):
        return "🟡 PRICING QUESTION", "interested"
    if any(w in text_lower for w in ["interested", "tell me more", "love to", "sounds great", "let's chat", "availability", "schedule", "book", "call", "meet", "portfolio"]):
        return "🟢 INTERESTED", "interested"
    return "🟡 NEEDS REVIEW", "review"

def create_ghl_contact(email, first_name, last_name, company, source):
    data = {
        "locationId": GHL_LOC,
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "companyName": company,
        "tags": ["cold-email-reply", "warm-lead"],
        "source": source,
    }
    r = requests.post(f"{GHL_BASE}/contacts/", headers={**GHL_HEADERS, "Content-Type": "application/json"}, json=data)
    return r.ok

def run():
    replies = get_instantly_replies()
    if not replies:
        print("No replies found or API error")
        return

    reply_list = replies if isinstance(replies, list) else replies.get("data", replies.get("items", []))
    if not reply_list:
        print("No new replies")
        return

    # Filter to last 2 hours
    cutoff = datetime.utcnow() - timedelta(hours=2)
    new_replies = []
    for r in reply_list:
        try:
            ts = r.get("timestamp", r.get("created_at", ""))
            if ts:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
                if dt > cutoff:
                    new_replies.append(r)
        except:
            new_replies.append(r)  # include if can't parse date

    if not new_replies:
        print("No replies in last 2 hours")
        return

    alert_lines = []
    for r in new_replies:
        sender = r.get("from_address_email", r.get("from", "unknown"))
        sender_name = r.get("from_address_name", sender.split("@")[0])
        body = r.get("body", r.get("text", ""))[:200]
        subject = r.get("subject", "")
        campaign = r.get("campaign_name", r.get("campaign_id", "Unknown"))

        label, action_type = classify_reply(body)

        # Extract company from email domain
        domain = sender.split("@")[-1] if "@" in sender else ""
        company = domain.split(".")[0].title() if domain else ""

        action_taken = "Flagged for review"
        if action_type == "interested":
            parts = sender_name.split()
            first = parts[0] if parts else ""
            last = parts[-1] if len(parts) > 1 else ""
            if create_ghl_contact(sender, first, last, company, f"Cold Email - {campaign}"):
                action_taken = "GHL contact created + tagged warm-lead"
            else:
                action_taken = "GHL contact creation failed — create manually"

        alert_lines.append(
            f"• {label} <b>{company or sender_name}</b> — {sender_name}\n"
            f"   Campaign: {campaign}\n"
            f"   Summary: {body[:100]}\n"
            f"   Action: {action_taken}"
        )

    if alert_lines:
        now = datetime.now().strftime("%I:%M %p, %B %d")
        msg = f"""<b>📨 NEW COLD EMAIL REPLIES</b>
<i>{now}</i>

{chr(10).join(alert_lines)}"""
        send_telegram(msg)
        print(f"✅ Classified {len(alert_lines)} replies, sent to Telegram")
    else:
        print("No actionable replies")

if __name__ == "__main__":
    run()
