"""
Sort and categorize transactions from bank CSV into the finance spreadsheet.
Splits business vs personal, maps to CRA T2125 categories.
"""
import csv
import os
import sys
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.google_sheets_auth import get_sheets_service

SHEET_ID = "170BPV2tw3uFCuutaxw2lnIXYG-9vmOIbUzbp5n7ey8g"

# ── Business vendor mappings ──
# (pattern, T2125 category, description override)
BUSINESS_RULES = [
    # Software & Subscriptions (Line 8871)
    (r"GOOGLE\*WORKSPACE", "Line 8871 — Software & Subscriptions", "Google Workspace"),
    (r"Adobe Inc", "Line 8871 — Software & Subscriptions", "Adobe Creative Cloud"),
    (r"INSTANTLY", "Line 8871 — Software & Subscriptions", "Instantly (Cold Email)"),
    (r"BUFFER PLAN", "Line 8871 — Software & Subscriptions", "Buffer (Social Media)"),
    (r"OPENROUTER", "Line 8871 — Software & Subscriptions", "OpenRouter (AI API)"),
    (r"LEADGENJAY", "Line 8871 — Software & Subscriptions", "LeadGenJay (Lead Scraping)"),
    (r"APIFY", "Line 8871 — Software & Subscriptions", "Apify (Web Scraping)"),
    (r"CLICKUP", "Line 8871 — Software & Subscriptions", "ClickUp (Project Mgmt)"),
    (r"EpidemicSound", "Line 8871 — Software & Subscriptions", "Epidemic Sound (Music Licensing)"),
    (r"Dropbox", "Line 8871 — Software & Subscriptions", "Dropbox (Cloud Storage)"),
    (r"INTUIT.*QBooks", "Line 8871 — Software & Subscriptions", "QuickBooks Online"),
    (r"HIGHLEVEL", "Line 8871 — Software & Subscriptions", "GoHighLevel (CRM)"),
    (r"ICYPEAS", "Line 8871 — Software & Subscriptions", "IcyPeas (Email Verification)"),
    (r"OPENAI.*CHATGPT", "Line 8871 — Software & Subscriptions", "ChatGPT Plus"),
    (r"GOOGLE \*Workspace", "Line 8871 — Software & Subscriptions", "Google Workspace"),
    # Advertising (Line 8521)
    (r"SHOWPASS", "Line 8521 — Advertising & Marketing", "Event/Networking Ticket"),
    # Professional Development (Line 8871)
    (r"Audible", "Line 8871 — Software & Subscriptions", "Audible (Professional Development)"),
    (r"EXPRESSVPN", "Line 8871 — Software & Subscriptions", "ExpressVPN"),
    # Co-working / Rent (Line 8860)
    (r"OUTPOST LANKA", "Line 8860 — Rent (Studio/Storage)", "Outpost Lanka (Co-working)"),
]

# Travel expenses that are 50% business (worked every day while traveling)
TRAVEL_BUSINESS_50_RULES = [
    (r"AIRALO", "Line 8945 — Telephone & Internet", "Airalo eSIM (Travel)"),
    (r"ONWARD TICKET", "Line 8910 — Travel (Accommodation, Flights)", "Onward Ticket"),
    (r"CATHAYPACAIR", "Line 8910 — Travel (Accommodation, Flights)", "Flight — Cathay Pacific"),
    (r"AIR ASIA", "Line 8910 — Travel (Accommodation, Flights)", "Flight — AirAsia"),
    (r"DEPARTMENT OF IMMIGRATION", "Line 8910 — Travel (Accommodation, Flights)", "Visa Fee"),
    (r"DEPT OF IMMIGRATION", "Line 8910 — Travel (Accommodation, Flights)", "Visa Fee"),
    (r"A4 RESIDENCE COLOMBO", "Line 8910 — Travel (Accommodation, Flights)", "Accommodation (Sri Lanka)"),
    (r"Clear Point Wild Forest", "Line 8910 — Travel (Accommodation, Flights)", "Accommodation (Sri Lanka)"),
    (r"XDT\*MEGATIX", "Line 8910 — Travel (Accommodation, Flights)", "Event Ticket (Bali)"),
]

# ── Personal category mappings ──
PERSONAL_RULES = [
    # Dining Out
    (r"BACKCOUNTRY BREWING", "Dining Out", None),
    (r"IL MUNDO", "Dining Out", None),
    (r"PUREBREAD", "Dining Out", None),
    (r"DOMINOS", "Dining Out", None),
    (r"RAMEN BUTCHER", "Dining Out", None),
    (r"Buddha 2", "Dining Out", None),
    (r"CRABAPPLE CAFE", "Dining Out", None),
    (r"STARBUCKS", "Dining Out", None),
    (r"SUBWAY", "Dining Out", None),
    (r"BARBURRITO", "Dining Out", None),
    (r"BAKED BATU", "Dining Out", None),
    (r"ZIN CAFE", "Dining Out", None),
    (r"GAYA GELATO", "Dining Out", None),
    (r"SOOGI ROLL", "Dining Out", None),
    (r"AVOCADO FACTORY", "Dining Out", None),
    (r"GOAT FATHER", "Dining Out", None),
    (r"MOTION PERERENAN", "Dining Out", None),
    (r"KAYUNAN WARUNG", "Dining Out", None),
    (r"RUSTERS", "Dining Out", None),
    (r"CLEAR CAFE", "Dining Out", None),
    (r"GIGI SUSU", "Dining Out", None),
    (r"REVOLVER INTER", "Dining Out", None),
    (r"ALCHEMY CANGGU", "Dining Out", None),
    (r"AHH-YUM", "Dining Out", None),
    (r"PLAN B CAFE", "Dining Out", None),
    (r"STICK SURF CLUB", "Dining Out", None),
    (r"LAMANA", "Dining Out", None),
    (r"JAVA LOUNGE", "Dining Out", None),
    (r"AHANGAMA DAIRIES", "Dining Out", None),
    (r"ZIPPI PVT", "Dining Out", None),
    (r"TUGU BALI", "Dining Out", None),
    (r"H A C PERERA", "Dining Out", None),
    (r"DEVILLE COFFEE", "Dining Out", None),
    (r"COMPASS VENDING", "Dining Out", None),
    (r"MOON THAI EXPRESS", "Dining Out", None),
    (r"2410311_HKG.*Gordon", "Dining Out", None),
    (r"CHAI RESTAURANTS", "Dining Out", None),
    (r"TRAFIQ CAFE", "Dining Out", None),
    (r"CONTINENTAL COFFEE", "Dining Out", None),
    (r"SUSHI SEN", "Dining Out", None),
    (r"Noodlebox", "Dining Out", None),
    (r"ESSENCE OF INDIA", "Dining Out", None),
    (r"SEA TO SKY HOTEL", "Dining Out", None),
    (r"Brackendale Art Ga", "Dining Out", None),
    (r"FOX & OAK", "Dining Out", None),
    (r"CLOUDBURST CAFE", "Dining Out", None),
    # Groceries & Household
    (r"HOME DEPOT", "Groceries & Household", None),
    (r"HECTOR.S YOUR INDEPEND", "Groceries & Household", None),
    (r"DOLLARAMA", "Groceries & Household", None),
    (r"LONDON DRUGS", "Groceries & Household", None),
    (r"SWAN MART", "Groceries & Household", None),
    (r"NESTERS MARKET", "Groceries & Household", None),
    (r"CHV.*WESTMOUNT CHE", "Groceries & Household", "Cheese/Groceries"),
    (r"WHSMITH", "Groceries & Household", None),
    # Clothing
    (r"MARKS SQUAMISH", "Clothing", None),
    (r"MOUNTAIN EQUIPMENT", "Clothing", None),
    (r"COASTAL CRYSTALS", "Clothing", "Gift Shop"),
    # Personal Subscriptions
    (r"Spotify", "Personal Subscriptions", None),
    (r"APPLE\.COM/BILL", "Personal Subscriptions", "Apple (iCloud/Services)"),
    # Health & Fitness
    (r"CLIMB GROUNDUP", "Health & Fitness", "Climbing Gym"),
    (r"BAMBU FITNESS", "Health & Fitness", "Gym (Bali)"),
    (r"MISSION YOGA", "Health & Fitness", "Yoga (Bali)"),
    (r"ALCHEMY YOGA", "Health & Fitness", "Yoga (Bali)"),
    (r"SENSES YOGA", "Health & Fitness", "Yoga (Sri Lanka)"),
    # Transportation
    (r"UBER", "Transportation (Personal)", None),
    (r"CITY OF VANCOUVER PARKING", "Transportation (Personal)", "Parking"),
    (r"AIR-SERV", "Transportation (Personal)", "Gas Station"),
    (r"SQUAMISHCONNECTOR", "Transportation (Personal)", "Squamish Connector Bus"),
    # Travel items NOT split (fully personal after 50% split handled elsewhere)
    (r"SHEN HENG CHANG", "Dining Out", "Food (Taiwan Airport)"),
]


def categorize_transaction(desc):
    """Return (type, category, clean_desc, split) — type is 'business', 'personal', or 'split'.
    split=1.0 means 100% business, split=0.5 means 50/50."""
    # Check 100% business rules first
    for pattern, category, override in BUSINESS_RULES:
        if re.search(pattern, desc, re.IGNORECASE):
            return "business", category, override or desc.split("  ")[0].strip(), 1.0

    # Check 50% business travel rules
    for pattern, category, override in TRAVEL_BUSINESS_50_RULES:
        if re.search(pattern, desc, re.IGNORECASE):
            return "split", category, override or desc.split("  ")[0].strip(), 0.5

    # Check personal rules
    for pattern, category, override in PERSONAL_RULES:
        if re.search(pattern, desc, re.IGNORECASE):
            return "personal", category, override or desc.split("  ")[0].strip(), 0.0

    # Default: personal / other
    return "personal", "Other Personal", desc.split("  ")[0].strip(), 0.0


def parse_transactions(csv_path):
    transactions = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            amount_str = row.get("CAD$", "0").strip()
            if not amount_str:
                continue
            amount = float(amount_str)

            desc1 = row.get("Description 1", "").strip()
            desc2 = row.get("Description 2", "").strip()
            full_desc = f"{desc1} {desc2}".strip() if desc2 else desc1

            date_str = row.get("Transaction Date", "").strip()

            transactions.append({
                "date": date_str,
                "description": full_desc,
                "amount": amount,
                "account": row.get("Account Type", ""),
                "account_num": row.get("Account Number", "")[-4:] if row.get("Account Number") else "",
            })
    return transactions


def calculate_gst(amount):
    """Estimate GST component from a GST-inclusive amount (5% GST)."""
    return round(abs(amount) / 1.05 * 0.05, 2)


def get_month_num(date_str):
    """Extract month number from date string like '1/15/2026'."""
    parts = date_str.split("/")
    return int(parts[0])


def main():
    csv_path = "/Users/matthewfernandes/Downloads/download-transactions.csv"
    transactions = parse_transactions(csv_path)

    business_txns = []
    personal_txns = []
    payments = []

    # Monthly totals for business expense categories
    biz_monthly = {}  # {category: {month: total}}
    personal_monthly = {}  # {category: {month: total}}
    gst_collected_monthly = {m: 0 for m in range(1, 13)}
    gst_paid_monthly = {m: 0 for m in range(1, 13)}

    for txn in transactions:
        amount = txn["amount"]
        desc = txn["description"]
        date = txn["date"]
        month = get_month_num(date)

        # Skip payments/credits to the card
        if amount > 0 and "PAYMENT" in desc.upper():
            payments.append(txn)
            continue

        # Refunds — keep as positive amounts in their category
        if amount > 0 and "PAYMENT" not in desc.upper():
            pass

        txn_type, category, clean_desc, biz_pct = categorize_transaction(desc)
        abs_amount = abs(amount) if amount < 0 else amount

        if txn_type == "business":
            # 100% business
            gst_amount = calculate_gst(amount) if amount < 0 else 0
            business_txns.append([
                date, clean_desc, desc.split("  ")[0].strip()[:40],
                category, round(abs_amount - gst_amount, 2) if amount < 0 else amount,
                gst_amount, abs_amount if amount < 0 else amount,
                f"Visa •{txn['account_num']}", "Yes", "Personal Card", ""
            ])
            if category not in biz_monthly:
                biz_monthly[category] = {m: 0 for m in range(1, 13)}
            biz_monthly[category][month] += abs_amount if amount < 0 else -amount
            if amount < 0:
                gst_paid_monthly[month] += gst_amount

        elif txn_type == "split":
            # 50% business, 50% personal
            biz_amount = round(abs_amount * biz_pct, 2)
            personal_amount = round(abs_amount * (1 - biz_pct), 2)
            gst_biz = round(calculate_gst(-biz_amount), 2) if amount < 0 else 0

            business_txns.append([
                date, f"{clean_desc} (50% biz)", desc.split("  ")[0].strip()[:40],
                category, round(biz_amount - gst_biz, 2), gst_biz, biz_amount,
                f"Visa •{txn['account_num']}", "Yes", "Personal Card", "50% business split"
            ])
            if category not in biz_monthly:
                biz_monthly[category] = {m: 0 for m in range(1, 13)}
            biz_monthly[category][month] += biz_amount
            if amount < 0:
                gst_paid_monthly[month] += gst_biz

            personal_txns.append([
                date, f"{clean_desc} (50% personal)", desc.split("  ")[0].strip()[:40],
                "Entertainment", personal_amount,
                f"Visa •{txn['account_num']}", "Personal Card", "50% personal split"
            ])
            if "Entertainment" not in personal_monthly:
                personal_monthly["Entertainment"] = {m: 0 for m in range(1, 13)}
            personal_monthly["Entertainment"][month] += personal_amount

        else:
            # 100% personal
            personal_txns.append([
                date, clean_desc, desc.split("  ")[0].strip()[:40],
                category, abs_amount if amount < 0 else -amount,
                f"Visa •{txn['account_num']}", "Personal Card", ""
            ])
            if category not in personal_monthly:
                personal_monthly[category] = {m: 0 for m in range(1, 13)}
            personal_monthly[category][month] += abs_amount if amount < 0 else -amount

    # Sort by date
    business_txns.sort(key=lambda x: datetime.strptime(x[0], "%m/%d/%Y") if "/" in x[0] else x[0])
    personal_txns.sort(key=lambda x: datetime.strptime(x[0], "%m/%d/%Y") if "/" in x[0] else x[0])

    print(f"Business transactions: {len(business_txns)}")
    print(f"Personal transactions: {len(personal_txns)}")
    print(f"Payments/credits skipped: {len(payments)}")

    # ── Write to Google Sheets ──
    sheets_svc = get_sheets_service()

    # T2125 category mapping to row numbers in Business Expenses tab
    t2125_row_map = {
        "Line 8521 — Advertising & Marketing": 3,
        "Line 8590 — Professional Fees (Accounting/Legal)": 4,
        "Line 8615 — Vehicle (Fuel, Maintenance, Parking)": 5,
        "Line 8690 — Insurance (Business)": 6,
        "Line 8710 — Interest & Bank Charges": 7,
        "Line 8811 — Office Supplies & Equipment <$500": 8,
        "Line 8860 — Rent (Studio/Storage)": 9,
        "Line 8871 — Software & Subscriptions": 10,
        "Line 8910 — Travel (Accommodation, Flights)": 11,
        "Line 8945 — Telephone & Internet": 12,
        "Line 9060 — Subcontractors": 13,
        "Line 9270 — Meals & Entertainment (50%)": 14,
        "Line 9281 — Home Office (See Tax Summary)": 15,
        "Other Business Expenses": 16,
    }

    personal_row_map = {
        "Housing (Rent/Mortgage)": 3,
        "Utilities (Hydro, Gas, Water)": 4,
        "Groceries & Household": 5,
        "Dining Out": 6,
        "Transportation (Personal)": 7,
        "Health & Fitness": 8,
        "Personal Subscriptions": 9,
        "Clothing": 10,
        "Entertainment": 11,
        "Savings/Investments": 12,
        "Other Personal": 13,
    }

    # Clear old data first
    clear_ranges = [
        "'Business Expenses'!C3:N16",
        "'Business Expenses'!A20:K200",
        "'Personal Expenses'!C3:N13",
        "'Personal Expenses'!A17:H200",
        "'GST-HST Tracker'!C3:N4",
    ]
    sheets_svc.spreadsheets().values().batchClear(
        spreadsheetId=SHEET_ID,
        body={"ranges": clear_ranges}
    ).execute()
    print("Cleared old data.")

    updates = []

    # ── Business expense monthly totals ──
    for category, months in biz_monthly.items():
        row = t2125_row_map.get(category)
        if row:
            for month_num, total in months.items():
                if total > 0:
                    col = chr(ord('C') + month_num - 1)  # C=Jan, D=Feb, etc.
                    updates.append({
                        "range": f"'Business Expenses'!{col}{row}",
                        "values": [[round(total, 2)]]
                    })

    # ── Personal expense monthly totals ──
    for category, months in personal_monthly.items():
        row = personal_row_map.get(category)
        if row:
            for month_num, total in months.items():
                if total > 0:
                    col = chr(ord('C') + month_num - 1)
                    updates.append({
                        "range": f"'Personal Expenses'!{col}{row}",
                        "values": [[round(total, 2)]]
                    })

    # ── GST tracker monthly totals (ITCs) ──
    for month_num, total in gst_paid_monthly.items():
        if total > 0:
            col = chr(ord('C') + month_num - 1)
            updates.append({
                "range": f"'GST-HST Tracker'!{col}4",
                "values": [[round(total, 2)]]
            })

    # ── Business expense log (starting row 19) ──
    if business_txns:
        start_row = 20  # Row 19 is header, data starts at 20
        updates.append({
            "range": f"'Business Expenses'!A{start_row}:K{start_row + len(business_txns) - 1}",
            "values": business_txns
        })

    # ── Personal expense log (starting row 16) ──
    if personal_txns:
        start_row = 17  # Row 16 is header, data starts at 17
        updates.append({
            "range": f"'Personal Expenses'!A{start_row}:H{start_row + len(personal_txns) - 1}",
            "values": personal_txns
        })

    # Batch write
    sheets_svc.spreadsheets().values().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": updates
        }
    ).execute()

    print("\nAll transactions written to Google Sheet!")

    # ── Print summary ──
    print("\n═══ BUSINESS EXPENSES SUMMARY ═══")
    biz_total = 0
    for category, months in sorted(biz_monthly.items()):
        cat_total = sum(months.values())
        if cat_total > 0:
            print(f"  {category}: ${cat_total:,.2f}")
            biz_total += cat_total
    print(f"  TOTAL: ${biz_total:,.2f}")

    print("\n═══ PERSONAL EXPENSES SUMMARY ═══")
    personal_total = 0
    for category, months in sorted(personal_monthly.items()):
        cat_total = sum(months.values())
        if cat_total > 0:
            print(f"  {category}: ${cat_total:,.2f}")
            personal_total += cat_total
    print(f"  TOTAL: ${personal_total:,.2f}")

    print(f"\n═══ GST ITCs (reclaimable): ${sum(gst_paid_monthly.values()):,.2f} ═══")


if __name__ == "__main__":
    main()
