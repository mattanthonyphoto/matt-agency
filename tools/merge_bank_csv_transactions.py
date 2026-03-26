"""
Merge missing bank CSV transactions into the 2025 Google Sheet.

Reads the existing Transactions tab, parses all 3 bank CSVs,
finds rows missing from the sheet (dedup by date + abs amount),
categorizes them, and rebuilds the full tab with merged data.
"""
import sys
import os
import csv
import re
from datetime import date, datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_sheets_service

SPREADSHEET_ID = "1TyX4sOIo6CxblxjNM9Yft5h5vZO_BGhQjHlgC0uzQtI"
SHEET_NAME = "Transactions"
EXCEL_EPOCH = date(1899, 12, 30)

CSV_FILES = [
    ("/Users/matthewfernandes/Downloads/download-transactions (5).csv", "Chequing", "05600-5192950"),
    ("/Users/matthewfernandes/Downloads/download-transactions (4).csv", "Personal Visa", "4510156028711351"),
    ("/Users/matthewfernandes/Downloads/download-transactions (7).csv", "Business Account", "05120-1019124"),
]


# ─── Date helpers ──────────────────────────────────────────────────────────────

def to_serial(d):
    if isinstance(d, datetime):
        d = d.date()
    if isinstance(d, date):
        return (d - EXCEL_EPOCH).days
    return None


def parse_csv_date(s):
    """Parse M/D/YYYY → date."""
    try:
        return datetime.strptime(s.strip(), "%m/%d/%Y").date()
    except Exception:
        return None


def parse_sheet_date(s):
    """Parse 'Jan 2, 2025' style → serial number for dedup."""
    try:
        return to_serial(datetime.strptime(s.strip(), "%b %d, %Y").date())
    except Exception:
        return None


def parse_sheet_amount(s):
    """Parse '$1,234.56' or '-$1,234.56' → float."""
    if not s:
        return None
    s = s.replace("$", "").replace(",", "").strip()
    try:
        return float(s)
    except Exception:
        return None


# ─── Categorisation ────────────────────────────────────────────────────────────

SKIP_PATTERNS = [
    r"PAYMENT - THANK YOU",
    r"PAI ?EMENT - MERCI",
    r"ONLINE BANKING TRANSFER",
    r"ONLINE TRANSFER",
    r"E-TRANSFER SENT MATTHEW",
    r"E-TRANSFER REQUEST FULFILLED",
    r"^PAYMENT$",
    r"INTERNET TRANSFER",
]

# (pattern, business, category, split_pct)
CATEGORISATION_RULES = [
    # Skip / internal — handled separately above

    # Business software & subscriptions
    (r"HIGHLEVEL|GOHIGHLEVEL",            True,  "Advertising & Marketing",   100),
    (r"LEADGENJAY",                        True,  "Software & Subscriptions",  100),
    (r"INSTANTLY",                         True,  "Software & Subscriptions",  100),
    (r"OPENAI|CHATGPT",                    True,  "Software & Subscriptions",  100),
    (r"SQUARESPACE|SQSP",                  True,  "Software & Subscriptions",  100),
    (r"GOOGLE\*GSUITE|GOOGLE.*WORKSPACE|GSUITE", True, "Software & Subscriptions", 100),
    (r"BUFFER",                            True,  "Software & Subscriptions",  100),
    (r"CLICKUP",                           True,  "Software & Subscriptions",  100),
    (r"EPIDEMIC SOUND",                    True,  "Software & Subscriptions",  100),
    (r"QUICKBOOKS|INTUIT\*QBOOKS",         True,  "Software & Subscriptions",  100),
    (r"SOUNDSTRIPE",                       True,  "Software & Subscriptions",  100),
    (r"PROEDU|SP PRO EDU",                 True,  "Software & Subscriptions",  100),
    (r"GAMUT",                             True,  "Software & Subscriptions",  100),
    (r"SHEETMAGIC",                        True,  "Software & Subscriptions",  100),
    (r"AUTOIGDM",                          True,  "Software & Subscriptions",  100),
    (r"DROPBOX",                           True,  "Software & Subscriptions",  100),
    (r"PADDLE\.NET(?!\*DISKDRILL)|^N8N",   True,  "Software & Subscriptions",  100),
    (r"PADDLE\.NET\*DISKDRILL|DISK DRILL", True,  "Software & Subscriptions",  100),
    (r"TRUSTED LEADS",                     True,  "Software & Subscriptions",  100),
    (r"QWILR",                             True,  "Software & Subscriptions",  100),
    (r"TINYPNG",                           True,  "Software & Subscriptions",  100),
    (r"MANYCHAT",                          True,  "Software & Subscriptions",  100),
    (r"MAIL AUTOMATION|GETMAILTRACKE",     True,  "Software & Subscriptions",  100),
    (r"BEATPORT",                          True,  "Software & Subscriptions",  100),
    (r"X\.AI|XAI",                         True,  "Software & Subscriptions",  100),
    (r"NETFLIX",                           True,  "Software & Subscriptions",  100),
    (r"AUDIBLE",                           True,  "Software & Subscriptions",  100),
    (r"SPOTIFY",                           True,  "Software & Subscriptions",  100),

    # Equipment
    (r"DJI",                               True,  "Equipment (CCA)",           100),
    (r"CAMERA CANADA",                     True,  "Equipment (CCA)",           100),
    (r"AFFIRM",                            True,  "Equipment (CCA)",           100),
    (r"APPLE STORE|APPLE\.COM/BILL",        True,  "Equipment (CCA)",           100),

    # Advertising
    (r"FACEBOOK|FACEBK",                   True,  "Advertising & Marketing",   100),
    (r"RESIDENT ADVISOR",                  True,  "Advertising & Marketing",   100),
    (r"EVENTBRITE",                        True,  "Advertising & Marketing",   100),

    # Vehicle
    (r"PETRO-CANADA|CHEVRON|SHELL|ESSO|CANCO|HUSKY|PIONEER|MOBIL|ULTRAMAR|CO-OP.*GAS|PETRO CANADA", True, "Vehicle", 100),
    (r"EASYPARK|IMPARK|HONK.*PARKING|SP\+|PARKING",    True,  "Vehicle",                   100),
    (r"GREAT CANADIAN OIL CHANGE",         True,  "Vehicle",                   100),
    (r"BC FERRIES|BCF",                    True,  "Vehicle",                   100),
    (r"ICBC",                              True,  "Vehicle",                    70),

    # Insurance
    (r"COOPERATORS|CO-OPERATORS",          True,  "Insurance",                  70),

    # Rent / co-working
    (r"FILI SPACE",                        True,  "Rent / Co-working",         100),

    # Telephone
    (r"ROGERS",                            True,  "Telephone & Internet",      100),

    # Bank charges
    (r"BANK FEE|MONTHLY FEE|^Monthly fee$|NSF|SERVICE CHARGE|ANNUAL FEE|PURCHASE INTEREST", True, "Interest & Bank Charges", 100),
    (r"LOAN INTEREST",                     True,  "Interest & Bank Charges",   100),

    # Professional fees
    (r"TRANSPORT CANADA",                  True,  "Professional Fees",         100),
    (r"TURBO TAX|INTUIT\*TURBOTAX",        True,  "Professional Fees",         100),

    # Supplies / hardware
    (r"HOME DEPOT",                        True,  "Office Supplies (<$500)",   100),
    (r"CANADIAN TIRE",                     True,  "Office Supplies (<$500)",   100),
    (r"RONA",                              True,  "Office Supplies (<$500)",   100),

    # Personal clothing
    (r"MARKS|#829 MARKS",                  False, "Clothing (Personal)",          0),
    (r"MEC MOUNTAIN EQUIPMENT|MEC\.CA",    False, "Clothing (Personal)",          0),

    # Personal pet
    (r"BOSLEYS",                           False, "Other Personal",               0),

    # Personal financial
    (r"RENT",                              False, "Housing",                      0),
    (r"QUESTRADE",                         False, "Savings/Investments",          0),
    (r"SHAKEPAY",                          False, "Savings/Investments",          0),
    (r"ATM WITHDRAWAL|ATM WITH",           False, "Other Personal",               0),
    (r"GST CANADA|CANADA WORKERS|CANADA REVENUE DEPOSITS|CRA DIRECT DEP", False, "Other Personal", 0),
    (r"CRA|PAD CCRA",                      False, "Other Personal",               0),
    (r"AFTERPAY",                          False, "Other Personal",               0),
    (r"COSTCO",                            False, "Groceries",                   50),
    (r"WAL-MART|WALMART",                  False, "Groceries",                    0),
    (r"SAFEWAY|SAVE ON|THRIFTY|REAL CDN SUPERSTORE|BUY LOW|FRESH ST",
                                           False, "Groceries",                    0),
    (r"LIQUOR STORE|BC LIQUOR|BCLS",       False, "Entertainment",                0),
    (r"SCANDINAVE SPA",                    False, "Entertainment",                0),
    (r"BELTANE|SHAMBHALA|TICKETMASTER",    False, "Entertainment",                0),
    (r"CINEPLEX",                          False, "Entertainment",                0),
]

# Amazon needs amount-based logic — handled in categorise()

KNOWN_INCOME_CLIENT_PATTERNS = [
    r"BALMORAL",
    r"SHALA YOGA",
    r"DARREN JUKES",
    r"VERNON PETTY",
    r"RACHELLE VICTORIA",
    r"ETERNAL NECTAR",
]

RESTAURANT_WORDS = {
    "RESTAURANT", "BISTRO", "CAFE", "COFFEE", "PIZZA", "SUSHI", "GRILL", "BURGER",
    "THAI", "CHINESE", "JAPANESE", "ITALIAN", "MEXICAN", "BAKERY", "KITCHEN",
    "DINER", "BAR ", "PUB ", "LOUNGE", "EATERY", "NOODLE", "RAMEN", "TACO",
    "SANDWICH", "DELI", "BAGEL", "BRUNCH", "WINGS", "STEAK", "SEAFOOD",
    "MCDONALD", "SUBWAY", "WENDY", "STARBUCKS", "TIM HORTON", "A&W",
    "DAIRY QUEEN", "BOSTON PIZZA", "WHITE SPOT", "CACTUS CLUB",
    "EARLS", "JOEYS", "Browns", "DONNELLY", "BROWN'S",
    "HECTOR'S",
}


def should_skip(desc1, desc2, amount):
    """Return True if this transaction should be skipped entirely."""
    combined = (desc1 + " " + desc2).upper()

    # Card payments (positive)
    if amount > 0 and re.search(r"PAYMENT - THANK YOU|PAI.?EMENT - MERCI", combined):
        return True

    # Internal transfers
    for pat in SKIP_PATTERNS:
        if re.search(pat, combined, re.IGNORECASE):
            return True

    # Known income e-transfers already in Excel
    for pat in KNOWN_INCOME_CLIENT_PATTERNS:
        if re.search(pat, combined, re.IGNORECASE):
            return True

    # Stripe positive — already in Excel income
    if amount > 0 and re.search(r"MISC PAYMENT STRIPE|STRIPE", combined):
        return True

    # Self e-transfer
    if re.search(r"MATTHEWANTHONYFERNANDES", combined, re.IGNORECASE):
        return True

    return False


def categorise(desc1, desc2, amount, account_type, account_number):
    """
    Returns dict with:
      business, category, split_pct, vendor, description, payment, account_label
    Returns None if the transaction should be skipped.
    """
    combined = (desc1 + " " + (desc2 or "")).strip()
    combined_upper = combined.upper()

    # Skip check
    if should_skip(desc1, desc2 or "", amount):
        return None

    # Derive payment method and account label
    if "Visa" in account_type or account_type == "Visa":
        if account_number == "4510156028711351":
            payment = "Visa"
            account_label = "Personal Card •1351"
        else:
            payment = "Visa"
            account_label = "Business Card •7714"
    else:
        payment = "Debit"
        account_label = "Chequing"

    # Business account chequing
    if account_number == "05120-1019124":
        account_label = "Business Account"

    # Vendor = first meaningful part
    vendor = desc1.strip()

    # Amazon — amount-based
    if re.search(r"AMAZON", combined_upper):
        if abs(amount) >= 500:
            return dict(business=True, category="Equipment (CCA)", split_pct=100,
                        vendor=vendor, description=combined, payment=payment, account_label=account_label)
        else:
            return dict(business=True, category="Office Supplies (<$500)", split_pct=100,
                        vendor=vendor, description=combined, payment=payment, account_label=account_label)

    # Check all rules
    for pattern, biz, cat, split in CATEGORISATION_RULES:
        if re.search(pattern, combined_upper, re.IGNORECASE):
            return dict(business=biz, category=cat, split_pct=split,
                        vendor=vendor, description=combined, payment=payment, account_label=account_label)

    # E-transfer received (positive, from chequing) — unknown
    if amount > 0 and re.search(r"E-TRANSFER|E-TRANSF", combined_upper):
        return dict(business=False, category="Other Personal", split_pct=0,
                    vendor=vendor, description=combined, payment=payment, account_label=account_label)

    # Restaurants / cafes heuristic
    for word in RESTAURANT_WORDS:
        if word in combined_upper:
            return dict(business=False, category="Dining Out", split_pct=0,
                        vendor=vendor, description=combined, payment=payment, account_label=account_label)

    # Positive income on chequing (not yet caught)
    if amount > 0 and payment == "Debit":
        return dict(business=False, category="Other Personal", split_pct=0,
                    vendor=vendor, description=combined, payment=payment, account_label=account_label)

    # Default: uncategorized expense
    return dict(business=False, category="Other Personal", split_pct=0,
                vendor=vendor, description=combined, payment=payment, account_label=account_label)


# ─── Read current sheet ────────────────────────────────────────────────────────

def read_sheet_existing(service):
    """
    Read all rows from the Transactions tab.
    Returns:
      - existing_keys: set of (date_serial, abs_amount_rounded) for dedup
      - all_rows: raw list of row lists (strings)
      - income_rows: list of row dicts already parsed
      - expense_rows: list of row dicts already parsed
      - title_rows: rows 1-3 (unchanged)
    """
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1:L2000"
    ).execute()
    raw = result.get("values", [])

    title_rows = raw[:3]  # rows 1-3

    # Parse data rows — income starts at row 6 (index 5), expenses after EXPENSES header
    income_data = []
    expense_data = []

    in_income = False
    in_expenses = False

    for row in raw[3:]:
        if not row:
            continue
        cell0 = row[0].strip() if row else ""
        if cell0 == "INCOME":
            in_income = True
            in_expenses = False
            continue
        if cell0 == "EXPENSES":
            in_income = False
            in_expenses = True
            continue
        if cell0 == "Date":
            continue  # column header row

        # Parse amount
        amount_str = row[3] if len(row) > 3 else ""
        amount = parse_sheet_amount(amount_str)
        if amount is None:
            continue

        date_serial = parse_sheet_date(cell0)

        row_dict = {
            "date_serial": date_serial,
            "vendor": row[1] if len(row) > 1 else "",
            "description": row[2] if len(row) > 2 else "",
            "amount": amount,
            "business": (row[4].upper() == "TRUE") if len(row) > 4 else False,
            "category": row[5] if len(row) > 5 else "",
            "split": row[6] if len(row) > 6 else "",
            "gst": parse_sheet_amount(row[7]) if len(row) > 7 else 0,
            "receipt": (row[8].upper() == "TRUE") if len(row) > 8 else False,
            "payment": row[9] if len(row) > 9 else "",
            "account": row[10] if len(row) > 10 else "",
            "notes": row[11] if len(row) > 11 else "",
        }

        if in_income:
            income_data.append(row_dict)
        elif in_expenses:
            expense_data.append(row_dict)

    # Build dedup key set
    existing_keys = set()
    for r in income_data + expense_data:
        if r["date_serial"] and r["amount"] is not None:
            key = (r["date_serial"], round(abs(r["amount"]), 2))
            existing_keys.add(key)

    print(f"Sheet: {len(income_data)} income rows, {len(expense_data)} expense rows")
    print(f"Dedup keys: {len(existing_keys)}")
    return existing_keys, income_data, expense_data


# ─── Parse CSVs ───────────────────────────────────────────────────────────────

def parse_csvs(existing_keys):
    """Parse all 3 CSVs and return new income/expense rows not in existing_keys."""
    new_income = []
    new_expenses = []
    skipped_count = 0
    duplicate_count = 0

    for path, source_label, account_number in CSV_FILES:
        with open(path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"\n  {source_label}: {len(rows)} rows")
        account_type = rows[0]["Account Type"] if rows else "Chequing"

        for row in rows:
            desc1 = row.get("Description 1", "").strip()
            desc2 = row.get("Description 2", "").strip()
            amount_str = row.get("CAD$", "").strip()
            date_str = row.get("Transaction Date", "").strip()

            if not amount_str or not date_str:
                continue

            try:
                amount = float(amount_str)
            except ValueError:
                continue

            txn_date = parse_csv_date(date_str)
            if not txn_date:
                continue

            date_serial = to_serial(txn_date)
            key = (date_serial, round(abs(amount), 2))

            if key in existing_keys:
                duplicate_count += 1
                continue

            # Categorise
            result = categorise(desc1, desc2, amount, account_type, account_number)
            if result is None:
                skipped_count += 1
                continue

            biz = result["business"]
            cat = result["category"]
            split_pct = result["split_pct"]
            vendor = result["vendor"]
            desc_full = result["description"]
            payment = result["payment"]
            account_label = result["account_label"]

            # GST
            if biz and amount < 0:
                gst = round(abs(amount) / 1.05 * 0.05, 4)
            else:
                gst = 0

            split_str = f"{split_pct}%"

            row_dict = {
                "date_serial": date_serial,
                "vendor": vendor,
                "description": desc_full,
                "amount": amount,
                "business": biz,
                "category": cat,
                "split": split_str,
                "gst": gst,
                "receipt": False,
                "payment": payment,
                "account": account_label,
                "notes": "",
            }

            # Add key to existing to avoid dupes across CSVs
            existing_keys.add(key)

            if amount > 0:
                new_income.append(row_dict)
            else:
                # Convert to negative (it's already negative from CSV for expenses)
                new_expenses.append(row_dict)

    print(f"\n  Duplicates (already in sheet): {duplicate_count}")
    print(f"  Skipped (transfers/payments): {skipped_count}")
    print(f"  New income rows: {len(new_income)}")
    print(f"  New expense rows: {len(new_expenses)}")
    return new_income, new_expenses


# ─── Build and write sheet ────────────────────────────────────────────────────

def build_sheet_data(income_rows, expense_rows):
    rows = []

    income_total = sum(r["amount"] for r in income_rows)
    expense_total = sum(abs(r["amount"]) for r in expense_rows)

    # INCOME section
    rows.append(["INCOME", "", "", f"Total: ${income_total:,.2f}", "", "", "", "", "", "", "", ""])
    rows.append(["Date", "Vendor", "Description", "", "Business", "Category", "", "", "Receipt", "Payment", "Account", "Notes"])
    for r in income_rows:
        rows.append([
            r["date_serial"],
            r["vendor"],
            r["description"],
            r["amount"],
            r["business"],
            r["category"],
            r["split"],
            r["gst"] if r["gst"] else 0,
            r["receipt"],
            r["payment"],
            r["account"],
            r["notes"],
        ])

    # Spacer
    rows.append([""] * 12)
    rows.append([""] * 12)

    # EXPENSES section
    rows.append(["EXPENSES", "", "", f"Total: ${expense_total:,.2f}", "", "", "", "", "", "", "", ""])
    rows.append(["Date", "Vendor", "Description", "", "Business", "Category", "", "", "Receipt", "Payment", "Account", "Notes"])
    for r in expense_rows:
        rows.append([
            r["date_serial"],
            r["vendor"],
            r["description"],
            r["amount"],
            r["business"],
            r["category"],
            r["split"],
            r["gst"] if r["gst"] else 0,
            r["receipt"],
            r["payment"],
            r["account"],
            r["notes"],
        ])

    return rows


def clear_and_write(service, sheet_id, sheet_data):
    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A4:Z3000"
    ).execute()
    print("Cleared existing data from row 4+")

    body = {"values": sheet_data}
    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A4",
        valueInputOption="RAW",
        body=body
    ).execute()
    print(f"Written {result.get('updatedRows', 0)} rows")


def apply_formatting(service, sheet_id, income_rows, expense_rows):
    requests = []

    n_income = len(income_rows)
    n_expense = len(expense_rows)

    # Row positions (0-indexed)
    income_header_row = 3        # row 4
    income_col_header = 4        # row 5
    income_data_start = 5        # row 6
    income_data_end = income_data_start + n_income

    spacer1 = income_data_end
    spacer2 = spacer1 + 1

    expense_header_row = spacer2 + 1
    expense_col_header = expense_header_row + 1
    expense_data_start = expense_col_header + 1
    expense_data_end = expense_data_start + n_expense

    def rgb(r, g, b):
        return {"red": r/255, "green": g/255, "blue": b/255}

    # INCOME header - green
    requests.append({"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": income_header_row,
                  "endRowIndex": income_header_row+1, "startColumnIndex": 0, "endColumnIndex": 12},
        "cell": {"userEnteredFormat": {"backgroundColor": rgb(52, 168, 83),
                 "textFormat": {"bold": True, "foregroundColor": rgb(255,255,255)}}},
        "fields": "userEnteredFormat(backgroundColor,textFormat)"
    }})

    # EXPENSES header - red
    requests.append({"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": expense_header_row,
                  "endRowIndex": expense_header_row+1, "startColumnIndex": 0, "endColumnIndex": 12},
        "cell": {"userEnteredFormat": {"backgroundColor": rgb(234, 67, 53),
                 "textFormat": {"bold": True, "foregroundColor": rgb(255,255,255)}}},
        "fields": "userEnteredFormat(backgroundColor,textFormat)"
    }})

    # Column header rows - gray bold
    for row in [income_col_header, expense_col_header]:
        requests.append({"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": row, "endRowIndex": row+1,
                      "startColumnIndex": 0, "endColumnIndex": 12},
            "cell": {"userEnteredFormat": {"backgroundColor": rgb(243, 243, 243),
                     "textFormat": {"bold": True}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }})

    # Date format col A
    for ds, de in [(income_data_start, income_data_end), (expense_data_start, expense_data_end)]:
        requests.append({"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": ds, "endRowIndex": de,
                      "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": "MMM d, yyyy"}}},
            "fields": "userEnteredFormat.numberFormat"
        }})

    # Amount format col D (currency)
    for ds, de in [(income_data_start, income_data_end), (expense_data_start, expense_data_end)]:
        requests.append({"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": ds, "endRowIndex": de,
                      "startColumnIndex": 3, "endColumnIndex": 4},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": '"$"#,##0.00'}}},
            "fields": "userEnteredFormat.numberFormat"
        }})

    # Business checkbox col E
    for ds, de in [(income_data_start, income_data_end), (expense_data_start, expense_data_end)]:
        requests.append({"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": ds, "endRowIndex": de,
                      "startColumnIndex": 4, "endColumnIndex": 5},
            "cell": {"dataValidation": {"condition": {"type": "BOOLEAN"}, "strict": True, "showCustomUi": True}},
            "fields": "dataValidation"
        }})

    # Receipt checkbox col I
    for ds, de in [(income_data_start, income_data_end), (expense_data_start, expense_data_end)]:
        requests.append({"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": ds, "endRowIndex": de,
                      "startColumnIndex": 8, "endColumnIndex": 9},
            "cell": {"dataValidation": {"condition": {"type": "BOOLEAN"}, "strict": True, "showCustomUi": True}},
            "fields": "dataValidation"
        }})

    # Category dropdown col F
    categories = [
        "Income", "Rent / Co-working", "Equipment (CCA)", "Advertising & Marketing",
        "Vehicle", "Software & Subscriptions", "Office Supplies (<$500)",
        "Interest & Bank Charges", "Travel", "Insurance", "Professional Fees",
        "Telephone & Internet", "Meals & Entertainment", "Other Business",
        "Entertainment", "Groceries", "Health & Fitness", "Other Personal",
        "Dining Out", "Housing", "Savings/Investments", "Clothing (Personal)",
    ]
    for ds, de in [(income_data_start, income_data_end), (expense_data_start, expense_data_end)]:
        requests.append({"setDataValidation": {
            "range": {"sheetId": sheet_id, "startRowIndex": ds, "endRowIndex": de,
                      "startColumnIndex": 5, "endColumnIndex": 6},
            "rule": {
                "condition": {"type": "ONE_OF_LIST",
                              "values": [{"userEnteredValue": c} for c in categories]},
                "strict": False, "showCustomUi": True
            }
        }})

    # Row background colors — income green tint
    income_tint = rgb(240, 250, 243)
    for idx in range(n_income):
        requests.append({"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": income_data_start+idx,
                      "endRowIndex": income_data_start+idx+1, "startColumnIndex": 0, "endColumnIndex": 12},
            "cell": {"userEnteredFormat": {"backgroundColor": income_tint}},
            "fields": "userEnteredFormat.backgroundColor"
        }})

    # Row background — expenses
    blue_tint = rgb(235, 245, 255)
    personal_tint = rgb(255, 245, 240)
    for idx, r in enumerate(expense_rows):
        bg = blue_tint if r["business"] else personal_tint
        requests.append({"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": expense_data_start+idx,
                      "endRowIndex": expense_data_start+idx+1, "startColumnIndex": 0, "endColumnIndex": 12},
            "cell": {"userEnteredFormat": {"backgroundColor": bg}},
            "fields": "userEnteredFormat.backgroundColor"
        }})

    # Amount colors
    for idx in range(n_income):
        requests.append({"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": income_data_start+idx,
                      "endRowIndex": income_data_start+idx+1, "startColumnIndex": 3, "endColumnIndex": 4},
            "cell": {"userEnteredFormat": {
                "numberFormat": {"type": "CURRENCY", "pattern": '"$"#,##0.00'},
                "textFormat": {"foregroundColor": rgb(52, 168, 83)}}},
            "fields": "userEnteredFormat(numberFormat,textFormat)"
        }})

    for idx in range(n_expense):
        requests.append({"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": expense_data_start+idx,
                      "endRowIndex": expense_data_start+idx+1, "startColumnIndex": 3, "endColumnIndex": 4},
            "cell": {"userEnteredFormat": {
                "numberFormat": {"type": "CURRENCY", "pattern": '"$"#,##0.00'},
                "textFormat": {"foregroundColor": rgb(234, 67, 53)}}},
            "fields": "userEnteredFormat(numberFormat,textFormat)"
        }})

    # Send in batches
    batch_size = 100
    total = len(requests)
    print(f"Sending {total} formatting requests in batches of {batch_size}...")
    for i in range(0, total, batch_size):
        batch = requests[i:i+batch_size]
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": batch}
        ).execute()
        print(f"  Batch {i//batch_size+1}/{(total+batch_size-1)//batch_size} done")

    print("Formatting applied.")


def print_summary(new_income, new_expenses, total_income_rows, total_expense_rows):
    print("\n" + "="*65)
    print("MERGE SUMMARY")
    print("="*65)
    print(f"\nNEW INCOME rows added:   {len(new_income)}")
    print(f"NEW EXPENSE rows added:  {len(new_expenses)}")
    print(f"\nTOTAL income rows now:   {total_income_rows}")
    print(f"TOTAL expense rows now:  {total_expense_rows}")

    if new_income:
        print("\nNew income breakdown:")
        by_cat = defaultdict(lambda: {"count": 0, "total": 0})
        for r in new_income:
            by_cat[r["category"]]["count"] += 1
            by_cat[r["category"]]["total"] += r["amount"]
        for cat, d in sorted(by_cat.items()):
            print(f"  {cat:<35} {d['count']:>4} rows  ${d['total']:>10,.2f}")

    if new_expenses:
        print("\nNew expense breakdown by category:")
        by_cat = defaultdict(lambda: {"count": 0, "total": 0})
        for r in new_expenses:
            by_cat[r["category"]]["count"] += 1
            by_cat[r["category"]]["total"] += abs(r["amount"])
        for cat, d in sorted(by_cat.items()):
            biz_flag = ""
            print(f"  {cat:<35} {d['count']:>4} rows  ${d['total']:>10,.2f}")

    new_biz = [r for r in new_expenses if r["business"]]
    new_personal = [r for r in new_expenses if not r["business"]]
    print(f"\nOf new expenses:")
    print(f"  Business:  {len(new_biz)} rows  ${sum(abs(r['amount']) for r in new_biz):,.2f}")
    print(f"  Personal:  {len(new_personal)} rows  ${sum(abs(r['amount']) for r in new_personal):,.2f}")


def main():
    print("Authenticating with Google Sheets...")
    service = get_sheets_service()

    # Get sheet ID
    meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheet_id = None
    for s in meta["sheets"]:
        if s["properties"]["title"] == SHEET_NAME:
            sheet_id = s["properties"]["sheetId"]
            break
    if sheet_id is None:
        print("ERROR: Transactions sheet not found")
        return

    print(f"\nReading existing sheet data...")
    existing_keys, income_rows, expense_rows = read_sheet_existing(service)

    print(f"\nParsing bank CSVs...")
    new_income, new_expenses = parse_csvs(existing_keys)

    # Merge and sort
    all_income = income_rows + new_income
    all_expenses = expense_rows + new_expenses

    # Sort by date serial
    all_income.sort(key=lambda r: r["date_serial"] or 0)
    all_expenses.sort(key=lambda r: r["date_serial"] or 0)

    print(f"\nMerged: {len(all_income)} income rows, {len(all_expenses)} expense rows")

    print("\nBuilding sheet data...")
    sheet_data = build_sheet_data(all_income, all_expenses)
    print(f"Total rows to write: {len(sheet_data)}")

    print("\nWriting to sheet...")
    clear_and_write(service, sheet_id, sheet_data)

    print("\nApplying formatting...")
    apply_formatting(service, sheet_id, all_income, all_expenses)

    print_summary(new_income, new_expenses, len(all_income), len(all_expenses))

    print(f"\nDone! Sheet updated.")
    print(f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")


if __name__ == "__main__":
    main()
