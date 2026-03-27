#!/usr/bin/env python3
"""The Operator — Proactive agent that does work: DM prep, follow-up drafting, content prep, lead processing, review requests.
Run with a mode argument: dm | followup | content | leads | reviews"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from agent_utils import (
    send_telegram, search_gmail, get_ghl_contacts, get_ghl_opportunities,
    get_instantly_campaigns, ghl_get, GHL_LOC, GHL_BASE, GHL_HEADERS,
    get_google_creds
)
import requests
from googleapiclient.discovery import build
import gspread
from google.oauth2.credentials import Credentials

# === GOOGLE SHEETS ===
def get_sheets_client():
    creds = get_google_creds()
    return gspread.authorize(creds)

# === MODE: DM PREP ===
def dm_prep():
    """Research prospects and write personalized IG DMs. Drop in tracker sheet."""
    send_telegram(
        "<b>📱 DM PREP AGENT</b>\n"
        "<i>Running daily prospect research...</i>\n\n"
        "Checking GHL contacts for IG-ready prospects..."
    )

    contacts = get_ghl_contacts(100)
    contact_list = contacts.get("contacts", [])

    # Find contacts with tags suggesting they're prospects, not clients
    prospects = []
    for c in contact_list:
        tags = c.get("tags", [])
        company = c.get("companyName", "")
        email = c.get("email", "")
        name = c.get("contactName", c.get("firstName", ""))
        website = c.get("website", "")

        # Skip if no company or already converted
        if not company:
            continue
        if any(t in tags for t in ["client", "paid", "converted"]):
            continue

        prospects.append({
            "name": name,
            "company": company,
            "email": email,
            "website": website,
            "tags": tags,
        })

    if not prospects:
        send_telegram("No new prospects found for DM outreach today.")
        return

    # Generate personalized DM drafts for top 10
    dm_lines = []
    for p in prospects[:10]:
        company = p["company"]
        name = p["name"].split()[0] if p["name"] else "there"
        website = p["website"] or f"(no website on file)"

        # Personalized DM template — references their company specifically
        dm = (
            f"Hey {name}, I came across {company}'s work and really like what you're doing. "
            f"I'm an architectural photographer based in Squamish — I work with builders and designers "
            f"across the Sea to Sky and Vancouver. Would love to connect."
        )

        dm_lines.append(
            f"• <b>{company}</b> — {name}\n"
            f"   🌐 {website}\n"
            f"   💬 {dm}"
        )

    msg = (
        f"<b>📱 DM PREP — {len(dm_lines)} Ready</b>\n"
        f"<i>{datetime.now().strftime('%A, %B %d')}</i>\n\n"
        f"Open Instagram and send these:\n\n"
        + "\n\n".join(dm_lines)
        + "\n\n<i>Copy each message, find them on IG, send. 15 min max.</i>"
    )
    send_telegram(msg)
    print(f"✅ DM Prep: {len(dm_lines)} DMs ready")


# === MODE: FOLLOW-UP DRAFTER ===
def followup_drafter():
    """Check GHL pipeline for stale deals, draft follow-up emails."""
    opps = get_ghl_opportunities()
    opp_list = opps.get("opportunities", [])
    now = datetime.now()

    stale = []
    for o in opp_list:
        if o.get("status") != "open":
            continue
        name = o.get("name", "Unknown")
        last_change = o.get("lastStageChangeAt", o.get("updatedAt", ""))
        contact = o.get("contact", {})
        email = contact.get("email", "")
        contact_name = contact.get("name", "")
        company = contact.get("companyName", "")

        try:
            last_dt = datetime.fromisoformat(last_change.replace("Z", "+00:00")).replace(tzinfo=None)
            age = (now - last_dt).days
        except:
            age = 99

        if age >= 3 and email:
            stale.append({
                "name": name,
                "contact_name": contact_name,
                "company": company,
                "email": email,
                "age": age,
            })

    if not stale:
        print("No stale deals found")
        return

    # Draft follow-up emails in Gmail
    gmail_svc = build("gmail", "v1", credentials=get_google_creds())
    drafts_created = []

    for deal in stale[:5]:  # Max 5 follow-ups per run
        first_name = deal["contact_name"].split()[0] if deal["contact_name"] else "there"
        company = deal["company"] or deal["name"]

        subject = f"Following up — {company}"
        body = (
            f"Hi {first_name},\n\n"
            f"Just wanted to check in on this — I know things get busy. "
            f"If the timing is still right, I'd love to get a quick call on the books "
            f"to make sure we're set up for a great shoot.\n\n"
            f"Here's my calendar if it's easier to grab a time directly:\n"
            f"https://mattanthonyphoto.com/discovery-call\n\n"
            f"No rush at all — just don't want this to slip through the cracks.\n\n"
            f"Best,\nMatt"
        )

        import base64
        from email.mime.text import MIMEText
        msg = MIMEText(body)
        msg["to"] = deal["email"]
        msg["subject"] = subject
        msg["from"] = "info@mattanthonyphoto.com"
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        try:
            gmail_svc.users().drafts().create(
                userId="me", body={"message": {"raw": raw}}
            ).execute()
            drafts_created.append(deal)
        except Exception as e:
            print(f"Failed to create draft for {deal['email']}: {e}")

    if drafts_created:
        lines = []
        for d in drafts_created:
            lines.append(f"• <b>{d['company'] or d['name']}</b> — {d['contact_name']} ({d['age']}d stale)\n   📧 Draft ready in Gmail → {d['email']}")

        msg = (
            f"<b>📝 FOLLOW-UP DRAFTER</b>\n"
            f"<i>{datetime.now().strftime('%A, %B %d')} — {len(drafts_created)} drafts created</i>\n\n"
            + "\n\n".join(lines)
            + "\n\n<i>Open Gmail drafts, review, and hit send.</i>"
        )
        send_telegram(msg)
        print(f"✅ Follow-up Drafter: {len(drafts_created)} drafts created")
    else:
        print("No drafts created")


# === MODE: CONTENT OPERATOR ===
def content_operator():
    """Read content calendar, generate today's ready-to-post caption."""
    today = datetime.now()
    day_name = today.strftime("%A")

    # Read the instagram posting guide from repo
    guide_path = os.path.join(os.path.dirname(__file__), "..", "business", "marketing", "social-media", "instagram-posting-guide.md")

    guide_content = ""
    if os.path.exists(guide_path):
        with open(guide_path, "r") as f:
            guide_content = f.read()

    # Find today's content in the guide
    today_str = today.strftime("%B %d")
    today_short = today.strftime("%b %d")

    # Look for today's date or day of week in the guide
    relevant_section = ""
    lines = guide_content.split("\n")
    capturing = False
    for i, line in enumerate(lines):
        if today_str in line or today_short in line or (day_name in line and not capturing):
            capturing = True
            relevant_section += line + "\n"
        elif capturing and line.startswith("#"):
            break
        elif capturing:
            relevant_section += line + "\n"

    if not relevant_section:
        # Generic content suggestion based on day
        projects = ["The Perch", "Warbler Residences", "Eagle Residence", "Sugarloaf", "Fitzsimmons North"]
        handles = {
            "The Perch": "@summerhillfinehomes, @atelier_michel_laflamme",
            "Warbler Residences": "@balmoralconstruction, @shelter_residential_design, @britt.lothrop",
            "Eagle Residence": "@balmoralconstruction",
            "Sugarloaf": "@balmoralconstruction, @starkarchitecture, @britt.lothrop",
            "Fitzsimmons North": "@balmoralconstruction, @shelter_residential_design",
        }
        project = projects[today.day % len(projects)]
        partner = handles.get(project, "")

        relevant_section = f"Suggested: {project} carousel or single"

        msg = f"""<b>📱 CONTENT TODAY</b>
<i>{today.strftime('%A, %B %d')}</i>

━━━━━━━━━━━━━━━
<b>📸 INSTAGRAM</b>
━━━━━━━━━━━━━━━
Type: Carousel (4-5 images)
Project: {project}
Credits: {partner}

Caption:
The details that make a home feel intentional.

Every material choice, every sight line, every moment of light — it all adds up. This project brought together an incredible team, and it shows in every frame.

Built by {partner.split(',')[0] if partner else 'an incredible team'}
📍 Sea-to-Sky Corridor, BC

Save this for your next build ↗️

#architecturephotography #westcoastmodern #seatolsky #customhomebuilder #interiordesign

━━━━━━━━━━━━━━━
<b>💼 LINKEDIN</b>
━━━━━━━━━━━━━━━
What separates good construction from great? The details you don't notice — because they just work.

This {project} project is a masterclass in material selection and spatial flow. Every corner reveals something considered.

If you're a builder investing in quality, your work deserves to be documented at this level.

→ mattanthonyphoto.com/discovery-call

━━━━━━━━━━━━━━━
<b>📌 PINTEREST</b>
━━━━━━━━━━━━━━━
{project} | Luxury Custom Home Photography | Sea-to-Sky BC | Modern West Coast Architecture | Interior Design Inspiration | Professional Architectural Photography by Matt Anthony"""
    else:
        msg = f"""<b>📱 CONTENT TODAY</b>
<i>{today.strftime('%A, %B %d')}</i>

━━━━━━━━━━━━━━━
From your posting guide:

{relevant_section[:2000]}

━━━━━━━━━━━━━━━
<i>Copy caption, grab images from Photo Assets, post to IG.</i>"""

    send_telegram(msg)
    print("✅ Content Operator: today's content sent")


# === MODE: LEAD PROCESSOR ===
def lead_processor():
    """Process raw leads from secondary ICP tabs into qualified output."""
    INPUT_SHEET_ID = "1qaeT6nURloVQx48dPtJODUz55IrqQEyRJ5xmnJJjoVs"

    # ICP tabs in priority order
    TABS = ["Millwork", "Windows", "Steel", "Landscape", "Lighting", "Flooring", "Hardware", "Envelope"]

    try:
        gc = get_sheets_client()
        sheet = gc.open_by_key(INPUT_SHEET_ID)
    except Exception as e:
        send_telegram(f"<b>⚠️ Lead Processor Error</b>\nCouldn't open input sheet: {e}")
        return

    processed_count = 0
    tab_processed = ""

    for tab_name in TABS:
        try:
            ws = sheet.worksheet(tab_name)
        except:
            continue

        rows = ws.get_all_records()
        unprocessed = [r for r in rows if not r.get("Processed")]

        if not unprocessed:
            continue

        tab_processed = tab_name
        batch = unprocessed[:50]  # Process 50 at a time

        for row in batch:
            company = row.get("Company Name", "")
            website = row.get("Website", "")
            if not company:
                continue
            processed_count += 1

        # Mark as processed (find rows and update)
        # For now, just report what's available
        break  # Process one tab per run

    if processed_count > 0:
        msg = (
            f"<b>🔄 LEAD PROCESSOR</b>\n"
            f"<i>{datetime.now().strftime('%A, %B %d')}</i>\n\n"
            f"Tab: <b>{tab_processed}</b>\n"
            f"Unprocessed leads found: {processed_count}\n\n"
            f"Ready to run cold email pipeline on these leads.\n"
            f"Run: <code>python3 tools/cold_email.py</code> with {tab_processed} tab.\n\n"
            f"<i>Remaining tabs: {', '.join(t for t in TABS if t != tab_processed)}</i>"
        )
        send_telegram(msg)
        print(f"✅ Lead Processor: {processed_count} leads ready in {tab_processed}")
    else:
        print("No unprocessed leads found in any tab")


# === MODE: REVIEW HARVESTER ===
def review_harvester():
    """Check for recently completed projects, draft Google review request emails."""
    # Search Gmail for recent invoices sent (indicates project completion)
    recent_invoices = search_gmail("subject:invoice from:me newer_than:30d", 20)

    # Check GHL for contacts that could leave reviews
    contacts = get_ghl_contacts(100)
    contact_list = contacts.get("contacts", [])

    # Find clients (tagged as client or with invoice history)
    reviewable = []
    for c in contact_list:
        tags = c.get("tags", [])
        name = c.get("contactName", c.get("firstName", ""))
        email = c.get("email", "")
        company = c.get("companyName", "")

        if not email or not name:
            continue

        # Look for clients who've been tagged or invoiced
        if any(t in tags for t in ["client", "project-complete", "delivered"]):
            if "review-requested" not in tags:
                reviewable.append({
                    "name": name,
                    "email": email,
                    "company": company,
                })

    if not reviewable:
        # Check known happy clients who haven't been asked
        known_clients = [
            {"name": "Kyle Paisley", "email": "kyle@summerhillfinehomes.com", "company": "Summerhill Fine Homes"},
            {"name": "Jordan Maddox", "email": "jordan@sitelinesarchitecture.com", "company": "Sitelines Architecture"},
            {"name": "Jason Craig", "email": "jason@kozehomes.ca", "company": "Koze Homes"},
        ]
        reviewable = known_clients

    if not reviewable:
        print("No clients to request reviews from")
        return

    # Draft review request emails
    gmail_svc = build("gmail", "v1", credentials=get_google_creds())
    drafts_created = []

    for client in reviewable[:3]:  # Max 3 per run
        first_name = client["name"].split()[0]

        subject = f"Quick favour, {first_name}?"
        body = (
            f"Hi {first_name},\n\n"
            f"Hope all is well! I really enjoyed working on the project with {client['company']} "
            f"and I'm grateful for the opportunity.\n\n"
            f"If you have a spare minute, a Google review would mean the world to me. "
            f"It helps other builders and designers find my work.\n\n"
            f"Here's the direct link (takes 30 seconds):\n"
            f"https://g.page/r/CYUoPFBM2z9HEAE/review\n\n"
            f"No pressure at all — and thanks again for a great project.\n\n"
            f"Best,\nMatt"
        )

        import base64
        from email.mime.text import MIMEText
        msg = MIMEText(body)
        msg["to"] = client["email"]
        msg["subject"] = subject
        msg["from"] = "info@mattanthonyphoto.com"
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        try:
            gmail_svc.users().drafts().create(
                userId="me", body={"message": {"raw": raw}}
            ).execute()
            drafts_created.append(client)
        except Exception as e:
            print(f"Failed to create draft for {client['email']}: {e}")

    if drafts_created:
        lines = [f"• <b>{d['company']}</b> — {d['name']}" for d in drafts_created]
        msg = (
            f"<b>⭐ REVIEW HARVESTER</b>\n"
            f"<i>{len(drafts_created)} review requests drafted</i>\n\n"
            + "\n".join(lines)
            + f"\n\n🔗 Review link: g.page/r/CYUoPFBM2z9HEAE/review"
            + "\n\n<i>Open Gmail drafts, review, and send.</i>"
        )
        send_telegram(msg)
        print(f"✅ Review Harvester: {len(drafts_created)} drafts created")


# === MAIN ===
MODES = {
    "dm": dm_prep,
    "followup": followup_drafter,
    "content": content_operator,
    "leads": lead_processor,
    "reviews": review_harvester,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in MODES:
        print(f"Usage: python3 operator.py <{'|'.join(MODES.keys())}>")
        sys.exit(1)

    mode = sys.argv[1]
    print(f"🔧 Running Operator: {mode}")
    MODES[mode]()
