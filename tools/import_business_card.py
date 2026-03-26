"""Import business card transactions into the v4 finance sheet."""
import csv, os, sys, re
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.google_sheets_auth import get_sheets_service

SID = "1KrEyElVbC-F4cP8asFa3BIh9PvIsKsF2mu6W9LUc1Yg"
CSV = "/Users/matthewfernandes/Downloads/download-transactions (3).csv"

RULES = [
    # 100% Business
    (r"GOOGLE \*Workspace", True, "Software & Subscriptions", "Google Workspace", 100),
    (r"hostinger", True, "Software & Subscriptions", "Hostinger (Web Hosting)", 100),
    (r"Kindle Svcs", True, "Software & Subscriptions", "Kindle (Books)", 100),
    (r"PETRO-CANADA", True, "Vehicle", "Petro-Canada (Gas)", 100),
    (r"VILLAGE PARKING", True, "Vehicle", "Parking (Whistler)", 100),
    (r"TUGO", True, "Insurance", "TuGo (Travel Insurance)", 100),
    (r"PURCHASE INTEREST", True, "Interest & Bank Charges", "Credit Card Interest", 100),
    (r"AMAZON", True, "Office Supplies (<$500)", "Amazon (Business Supplies)", 100),
    (r"PrimeVideo", False, "Subscriptions", "Amazon Prime Video", 0),
    # 50% Business — Travel
    (r"AIRBNB", True, "Travel", "Airbnb (Accommodation)", 50),
    (r"Grab\*", True, "Travel", "Grab (Ride)", 50),
    (r"AIRASIA", True, "Travel", "AirAsia (Flight)", 50),
    (r"Prismalink.*VISAARR", True, "Travel", "Visa on Arrival (Indonesia)", 50),
]

def categorize(desc):
    for pattern, is_biz, cat, name, split in RULES:
        if re.search(pattern, desc, re.IGNORECASE):
            return is_biz, cat, name, split
    return True, "Other Business", desc.split("  ")[0].strip()[:30], 100

def calc_gst(amt):
    return round(abs(amt) / 1.05 * 0.05, 2)

def main():
    svc = get_sheets_service()

    # Find last row
    result = svc.spreadsheets().values().get(
        spreadsheetId=SID, range="Transactions!A1:A1000"
    ).execute()
    next_row = len(result.get("values", [])) + 1
    print(f"Appending from row {next_row}")

    rows = []
    with open(CSV, "r") as f:
        for row in csv.DictReader(f):
            amt_str = row.get("CAD$", "").strip()
            if not amt_str: continue
            amount = float(amt_str)
            desc = f"{row.get('Description 1', '')} {row.get('Description 2', '')}".strip()
            date = row.get("Transaction Date", "").strip()

            # Skip card payments
            if amount > 0 and "PAYMENT" in desc.upper():
                continue

            # Amazon refunds (positive amounts) — keep as negative offset
            if "AMAZON" in desc and amount > 0:
                rows.append([date, "Amazon (Return/Refund)", desc[:40], amount, True,
                            "Office Supplies (<$500)", "100%", 0, True, "Visa", "Business Card", "Refund"])
                continue

            is_biz, cat, name, split_pct = categorize(desc)

            if split_pct == 50 and amount < 0:
                half = round(amount / 2, 2)
                gst_half = calc_gst(half)
                rows.append([date, name, f"50% business", half, True, cat, "50%", gst_half,
                            False, "Visa", "Business Card", "50/50 split"])
                pcat = "Travel (Personal)" if cat == "Travel" else "Other Personal"
                rows.append([date, name, f"50% personal", half, False, pcat, "0%", 0,
                            False, "Visa", "Business Card", "50/50 split"])
            else:
                gst = calc_gst(amount) if is_biz and amount < 0 else 0
                rows.append([date, name, desc[:40], amount, is_biz, cat,
                            "100%" if is_biz else "0%", gst, False, "Visa", "Business Card", ""])

    rows.sort(key=lambda x: datetime.strptime(x[0], "%m/%d/%Y"))

    svc.spreadsheets().values().update(
        spreadsheetId=SID,
        range=f"Transactions!A{next_row}:L{next_row + len(rows) - 1}",
        valueInputOption="USER_ENTERED",
        body={"values": rows}
    ).execute()

    # Summary
    biz_expense = sum(abs(r[3]) for r in rows if r[4] is True and r[3] < 0)
    biz_income = sum(r[3] for r in rows if r[4] is True and r[3] > 0)
    pers_expense = sum(abs(r[3]) for r in rows if r[4] is False and r[3] < 0)
    gst_itc = sum(r[7] for r in rows if r[4] is True and r[3] < 0)

    print(f"\n══ BUSINESS CARD SUMMARY ══")
    print(f"Transactions: {len(rows)}")
    print(f"Business expenses: ${biz_expense:,.2f}")
    print(f"Refunds/credits: ${biz_income:,.2f}")
    print(f"Personal (50% travel splits): ${pers_expense:,.2f}")
    print(f"GST ITCs: ${gst_itc:,.2f}")

    # Category breakdown
    cats = {}
    for r in rows:
        if r[4] is True and r[3] < 0:
            cats[r[5]] = cats.get(r[5], 0) + abs(r[3])
    print(f"\nBy category:")
    for cat, amt in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat}: ${amt:,.2f}")

if __name__ == "__main__":
    main()
