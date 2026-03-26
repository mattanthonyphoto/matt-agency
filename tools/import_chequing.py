"""Import chequing account transactions into the v4 finance sheet."""
import csv, os, sys, re
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.google_sheets_auth import get_sheets_service

SHEET_ID = "1KrEyElVbC-F4cP8asFa3BIh9PvIsKsF2mu6W9LUc1Yg"
CSV_PATH = "/Users/matthewfernandes/Downloads/download-transactions (1).csv"

# (pattern, is_business, category, clean_name, split%)
RULES = [
    # Business income
    (r"MISC PAYMENT STRIPE", True, "Software & Subscriptions", "Stripe (Client Payment)", 100),  # This is INCOME, handled specially
    # Business expenses
    (r"MONTHLY FEE", True, "Interest & Bank Charges", "Bank Monthly Fee", 100),
    (r"ROGERS WIRELESS", True, "Telephone & Internet", "Rogers Wireless", 50),
    # Insurance — split
    (r"AUTO INSURANCE ICBC", True, "Vehicle", "ICBC Auto Insurance", 50),
    (r"INSURANCE COOPERATORS", True, "Insurance", "Cooperators Insurance", 50),
    # Loan
    (r"LOAN INTEREST", True, "Interest & Bank Charges", "Loan Interest", 100),
    # Subcontractor
    (r"E-TRANSFER SENT OLGA LISSEY", True, "Subcontractors", "Olga Lissey (Subcontractor)", 100),
    # Personal
    (r"E-TRANSFER SENT.*RENT|E-TRANSFER SENT MATTHEW FERNANDES F83EX7", False, "Housing", "Rent", 0),
    (r"MISC PAYMENT AFFIRM", False, "Other Personal", "Affirm Loan Payment", 0),
    (r"MISC PAYMENT QUESTRADE", False, "Savings/Investments", "Questrade (RRSP/TFSA)", 0),
    (r"ATM WITHDRAWAL", False, "Other Personal", "ATM Cash Withdrawal", 0),
    (r"PLUS - SC", False, "Other Personal", "Foreign ATM Fee", 0),
    (r"GST CANADA", False, "Other Personal", "GST Credit (Gov)", 0),  # Gov benefit, not business
    (r"CANADA WORKERS BENEFIT", False, "Other Personal", "CWB (Gov Benefit)", 0),
    (r"MISC PAYMENT PAYPAL", False, "Other Personal", "PayPal", 0),
    (r"ONLINE BANKING TRANSFER", False, "Other Personal", "Internal Transfer", 0),
    (r"ONLINE BANKING PAYMENT", False, "Other Personal", "Bill Payment", 0),
    (r"E-TRANSFER SENT MATTHEW FERNANDES", False, "Other Personal", "E-Transfer (Self)", 0),
    (r"E-TRANSFER RECEIVED", False, "Other Personal", "E-Transfer Received", 0),
]

def categorize(desc):
    for pattern, is_biz, cat, name, split in RULES:
        if re.search(pattern, desc, re.IGNORECASE):
            return is_biz, cat, name, split
    return False, "Other Personal", desc.split("  ")[0].strip()[:30], 0

def calc_gst(amt):
    return round(abs(amt) / 1.05 * 0.05, 2)

def main():
    svc = get_sheets_service()

    # First, find current last row in Transactions
    result = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range="Transactions!A1:A1000"
    ).execute()
    existing_rows = len(result.get("values", []))
    next_row = existing_rows + 1
    print(f"Existing rows: {existing_rows}, appending from row {next_row}")

    # Parse chequing CSV
    rows = []
    stripe_income = []
    with open(CSV_PATH, "r") as f:
        for row in csv.DictReader(f):
            amt_str = row.get("CAD$", "").strip()
            if not amt_str: continue
            amount = float(amt_str)
            desc = f"{row.get('Description 1', '')} {row.get('Description 2', '')}".strip()
            date = row.get("Transaction Date", "").strip()

            is_biz, cat, name, split_pct = categorize(desc)

            # Stripe payments are BUSINESS INCOME (positive), not expenses
            if "STRIPE" in desc and amount > 0:
                gst_collected = round(amount / 1.05 * 0.05, 2)
                rows.append([date, "Stripe (Client Revenue)", "GHL → Stripe payout",
                            amount, True, "Software & Subscriptions", "100%", gst_collected,
                            True, "Debit", "Personal Account", "Business income"])
                continue

            # E-transfer received — check if business
            if "E-TRANSFER RECEIVED" in desc and amount > 0:
                rows.append([date, name, desc[:40], amount, False, "Other Personal", "0%", 0,
                            False, "E-Transfer", "Personal Account", "Check if business income"])
                continue

            # Gov benefits — income, personal
            if amount > 0 and ("GST CANADA" in desc or "CANADA WORKERS" in desc):
                rows.append([date, name, desc[:40], amount, False, "Other Personal", "0%", 0,
                            False, "Debit", "Personal Account", "Gov benefit"])
                continue

            # Internal transfers — skip (just moving money between accounts)
            if "ONLINE BANKING TRANSFER" in desc:
                continue

            # Credit card payment to visa — skip (already tracked on visa)
            if "ONLINE BANKING PAYMENT" in desc and "ROGERS" not in desc:
                continue

            # 50% split items
            if split_pct == 50 and amount < 0:
                half = round(amount / 2, 2)
                gst_half = calc_gst(half) if is_biz else 0
                rows.append([date, name, f"50% business", half, True, cat, "50%", gst_half,
                            False, "Debit", "Personal Account", "50/50 split"])
                pcat = cat.replace("Vehicle", "Transportation") if not is_biz else "Other Personal"
                rows.append([date, name, f"50% personal", half, False,
                            "Transportation" if cat == "Vehicle" else ("Subscriptions" if cat == "Telephone & Internet" else "Other Personal"),
                            "0%", 0, False, "Debit", "Personal Account", "50/50 split"])
                continue

            # Regular items
            gst = calc_gst(amount) if is_biz and amount < 0 else 0
            rows.append([date, name, desc[:40], amount, is_biz, cat,
                        "100%" if is_biz and split_pct == 100 else "0%",
                        gst, False, "Debit", "Personal Account", ""])

    rows.sort(key=lambda x: datetime.strptime(x[0], "%m/%d/%Y"))
    print(f"Chequing transactions: {len(rows)}")

    # Append to sheet
    svc.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=f"Transactions!A{next_row}:L{next_row + len(rows) - 1}",
        valueInputOption="USER_ENTERED",
        body={"values": rows}
    ).execute()

    # Summary
    biz_income = sum(r[3] for r in rows if r[4] is True and r[3] > 0)
    biz_expense = sum(abs(r[3]) for r in rows if r[4] is True and r[3] < 0)
    pers_expense = sum(abs(r[3]) for r in rows if r[4] is False and r[3] < 0)
    gst_collected = sum(r[7] for r in rows if r[4] is True and r[3] > 0)
    gst_paid = sum(r[7] for r in rows if r[4] is True and r[3] < 0)

    print(f"\n══ CHEQUING SUMMARY ══")
    print(f"Business income (Stripe): ${biz_income:,.2f}")
    print(f"GST collected: ${gst_collected:,.2f}")
    print(f"Business expenses: ${biz_expense:,.2f}")
    print(f"Personal expenses: ${pers_expense:,.2f}")
    print(f"GST ITCs: ${gst_paid:,.2f}")
    print(f"\nAppended {len(rows)} rows starting at row {next_row}")


if __name__ == "__main__":
    main()
