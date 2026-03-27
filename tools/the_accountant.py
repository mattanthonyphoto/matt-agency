#!/usr/bin/env python3
"""The Accountant — Financial agent: invoice chasing, expense tracking, tax reminders.
Modes: invoices | expenses | tax"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from agent_utils import (
    send_telegram, search_gmail, get_ghl_invoices, get_google_creds
)
import requests
import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build


# === MODE: INVOICE CHASER ===
def invoice_chaser():
    """Find overdue invoices in GHL, draft follow-up emails."""
    now = datetime.now()
    invoices_data = get_ghl_invoices()
    invoices = invoices_data.get("invoices", invoices_data.get("data", []))

    overdue = []
    for inv in invoices:
        status = inv.get("status", "").lower()
        if status not in ["sent", "viewed", "overdue", "unpaid"]:
            continue

        amount = inv.get("amount", inv.get("total", 0)) or 0
        if amount > 10000:
            amount = amount / 100
        if amount == 0:
            continue

        name = inv.get("name", inv.get("title", inv.get("contactName", "Unknown")))
        contact_email = inv.get("contactDetails", {}).get("email", "")
        invoice_num = inv.get("invoiceNumber", inv.get("number", ""))
        created = inv.get("createdAt", inv.get("created_at", ""))

        age = 0
        try:
            created_dt = datetime.fromisoformat(created.replace("Z", "+00:00")).replace(tzinfo=None)
            age = (now - created_dt).days
        except:
            pass

        if age >= 14:  # Only chase invoices 14+ days old
            overdue.append({
                "name": name,
                "email": contact_email,
                "amount": amount,
                "age": age,
                "invoice_num": invoice_num,
            })

    if not overdue:
        print("No overdue invoices found (14+ days)")
        return

    # Draft follow-up emails
    gmail_svc = build("gmail", "v1", credentials=get_google_creds())
    drafts_created = []

    for inv in overdue[:5]:
        if not inv["email"]:
            continue

        first_name = inv["name"].split()[0] if inv["name"] else "there"
        subject = f"Following up on invoice {inv['invoice_num']}" if inv["invoice_num"] else f"Following up on outstanding invoice"
        body = (
            f"Hi {first_name},\n\n"
            f"Hope you're doing well. Just a quick follow-up on the outstanding invoice "
            f"{'#' + inv['invoice_num'] + ' ' if inv['invoice_num'] else ''}"
            f"for ${inv['amount']:,.2f}.\n\n"
            f"I know things get busy — just want to make sure this didn't slip through the cracks. "
            f"Let me know if you need me to resend it or if there's anything to sort out.\n\n"
            f"Thanks,\nMatt"
        )

        msg = MIMEText(body)
        msg["to"] = inv["email"]
        msg["subject"] = subject
        msg["from"] = "info@mattanthonyphoto.com"
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        try:
            gmail_svc.users().drafts().create(
                userId="me", body={"message": {"raw": raw}}
            ).execute()
            drafts_created.append(inv)
        except Exception as e:
            print(f"Failed draft for {inv['email']}: {e}")

    lines = []
    for inv in overdue:
        status = "📧 Draft ready" if inv in drafts_created else "⚠️ No email on file"
        lines.append(
            f"• <b>{inv['name']}</b> — ${inv['amount']:,.2f} ({inv['age']} days)\n"
            f"   {status}"
        )

    msg = (
        f"<b>💳 INVOICE CHASER</b>\n"
        f"<i>{now.strftime('%A, %B %d')} — {len(overdue)} overdue</i>\n\n"
        + "\n\n".join(lines)
        + f"\n\nTotal outstanding: ${sum(i['amount'] for i in overdue):,.2f}"
        + "\n\n<i>Open Gmail drafts, review, and send.</i>"
    )
    send_telegram(msg)
    print(f"✅ Invoice Chaser: {len(overdue)} overdue, {len(drafts_created)} drafts created")


# === MODE: EXPENSE TRACKER ===
def expense_tracker():
    """Check Gmail for recent receipts and subscription charges."""
    now = datetime.now()

    # Search for receipt/charge emails
    receipts = search_gmail("subject:(receipt OR charge OR payment OR subscription OR renewal) newer_than:7d", 20)

    charges = []
    for m in receipts:
        # Skip sent emails
        if "SENT" in m.get("labels", []) and "INBOX" not in m.get("labels", []):
            continue
        sender = m["from"].split("<")[0].strip().strip('"')
        subj = m["subject"][:60]
        charges.append(f"• <b>{sender}</b> — {subj}")

    if not charges:
        print("No new charges/receipts found this week")
        return

    msg = (
        f"<b>🧾 EXPENSE TRACKER</b>\n"
        f"<i>Week of {now.strftime('%B %d')}</i>\n\n"
        f"<b>Recent charges/receipts:</b>\n\n"
        + "\n".join(charges[:15])
        + f"\n\n<i>Review and categorize in your 2026 finance sheet.</i>"
    )
    send_telegram(msg)
    print(f"✅ Expense Tracker: {len(charges)} charges found")


# === MODE: TAX REMINDERS ===
def tax_reminders():
    """Check upcoming tax deadlines and financial milestones."""
    now = datetime.now()
    month = now.month
    day = now.day

    reminders = []

    # FHSA deadline
    if month >= 9:
        days_left = (datetime(now.year, 12, 31) - now).days
        urgency = "🔴" if days_left < 30 else "🟡" if days_left < 90 else "🟢"
        reminders.append(f"{urgency} <b>FHSA</b> — Must open before Dec 31 ({days_left} days left). $8,000 tax deduction.")

    # Quarterly tax installments (Mar 15, Jun 15, Sep 15, Dec 15)
    quarterly_dates = [
        (3, 15, "Q1"), (6, 15, "Q2"), (9, 15, "Q3"), (12, 15, "Q4")
    ]
    for q_month, q_day, q_name in quarterly_dates:
        q_date = datetime(now.year, q_month, q_day)
        days_until = (q_date - now).days
        if 0 < days_until <= 30:
            reminders.append(f"🟡 <b>{q_name} Tax Installment</b> — due {q_date.strftime('%B %d')} ({days_until} days)")

    # GST filing (annual, due Jun 15 for prior year)
    gst_deadline = datetime(now.year, 6, 15)
    gst_days = (gst_deadline - now).days
    if 0 < gst_days <= 60:
        reminders.append(f"🟡 <b>GST Filing</b> — due June 15 ({gst_days} days). 2025 net owing was $266.")

    # RRSP deadline (Mar 1 for prior tax year)
    rrsp_deadline = datetime(now.year + 1, 3, 1)
    rrsp_days = (rrsp_deadline - now).days
    if rrsp_days <= 90:
        reminders.append(f"🟢 <b>RRSP Deadline</b> — Mar 1, {now.year + 1} for {now.year} tax year ({rrsp_days} days)")

    # Line of credit reminder
    reminders.append(f"📊 <b>LOC Balance</b> — $16,574 / $35,000 at 8.94%. Monthly interest: ~$123")

    # Monthly recurring costs
    reminders.append(
        f"📊 <b>Monthly Burn</b>\n"
        f"   Personal: ~$6,580\n"
        f"   Software: ~$600 (GHL $150, Instantly $140, Adobe $80, others)\n"
        f"   Revenue needed to breakeven: ~$7,200/mo\n"
        f"   Recurring revenue: $1,417.50/mo\n"
        f"   Gap: ~$5,783/mo from project work"
    )

    msg = (
        f"<b>📊 TAX & FINANCE REMINDERS</b>\n"
        f"<i>{now.strftime('%B %d, %Y')}</i>\n\n"
        + "\n\n".join(reminders)
    )
    send_telegram(msg)
    print(f"✅ Tax Reminders: {len(reminders)} items sent")


# === MAIN ===
MODES = {
    "invoices": invoice_chaser,
    "expenses": expense_tracker,
    "tax": tax_reminders,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in MODES:
        print(f"Usage: python3 the_accountant.py <{'|'.join(MODES.keys())}>")
        sys.exit(1)
    mode = sys.argv[1]
    print(f"💰 Running Accountant: {mode}")
    MODES[mode]()
