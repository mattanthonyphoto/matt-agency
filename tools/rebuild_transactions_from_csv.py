"""
Rebuild 2025 Transactions tab from 4 bank CSV files.
Parses all CSVs, categorizes, writes to Google Sheets with formatting.
"""
import sys
import os
import csv
import re
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_sheets_service

SPREADSHEET_ID = "1TyX4sOIo6CxblxjNM9Yft5h5vZO_BGhQjHlgC0uzQtI"
SHEET_NAME = "Transactions"

EXCEL_EPOCH = date(1899, 12, 30)

CSV_FILES = [
    {
        "path": "/Users/matthewfernandes/Downloads/download-transactions (4).csv",
        "label": "Personal Card",
        "payment": "Visa",
        "account_num": "1351",
        "default_business": False,
    },
    {
        "path": "/Users/matthewfernandes/Downloads/download-transactions (5).csv",
        "label": "Chequing",
        "payment": "Debit",
        "account_num": "2950",
        "default_business": False,
    },
    {
        "path": "/Users/matthewfernandes/Downloads/download-transactions (6).csv",
        "label": "Business Card",
        "payment": "Visa",
        "account_num": "7714",
        "default_business": True,
    },
    {
        "path": "/Users/matthewfernandes/Downloads/download-transactions (7).csv",
        "label": "Business Chequing",
        "payment": "Debit",
        "account_num": "9124",
        "default_business": True,
    },
]

def to_serial(d):
    if isinstance(d, datetime):
        d = d.date()
    if isinstance(d, date):
        return (d - EXCEL_EPOCH).days
    return None

def parse_date(s):
    """Parse M/D/YYYY date string."""
    parts = s.strip().split("/")
    if len(parts) == 3:
        return date(int(parts[2]), int(parts[0]), int(parts[1]))
    return None

def clean_vendor(desc):
    """Extract a clean vendor name from description (max ~30 chars)."""
    d = desc.upper().strip()
    # Remove common prefixes
    for prefix in ["CONTACTLESS INTERAC PURCHASE - \\d+ ", "INTERAC PURCHASE - \\d+ ",
                    "MISC PAYMENT ", "SQ \\*", "SP "]:
        d = re.sub(prefix, "", d)
    # Remove location suffixes
    d = re.sub(r"\s+(SQUAMISH|GARIBALDI HIG|GARIBALDIHIGH|WHISTLER|VANCOUVER|BURNABY|"
               r"NORTH VANCO|VICTORIA|RICHMOND|SURREY|COQUITLAM|LANGLEY|TORONTO|"
               r"OTTAWA|MONTREAL|LONDON|STOCKHOLM|HTTPSSQUARESP|AMZN\.COM/BILL|"
               r"AMZN\.COM/BIL|WWW\.AMAZON\.CA|AMAZON\.CA/PRI|855-222-8603|"
               r"855-4178537|650-5434800|415-8576933|4085366000|WWW\.JASONPERR|"
               r"AIRBNB\.COM|GOHIGHLEVEL\.C|INSTANTLY\.AI|OPENAI\.COM|SHEETMAGIC\.AI|"
               r"LEADGENJAY\.CO|HTTPSSQUARESP).*$", "", d)
    # Remove order/ref codes
    d = re.sub(r"\s*[A-Z0-9]{8,}.*$", "", d)
    d = re.sub(r"\s*\d+\.\d+ USD @ [\d.]+$", "", d)
    d = re.sub(r"\s*#\d+.*$", "", d)
    d = re.sub(r"\s*\*.*$", "", d)
    d = re.sub(r"\s+- \d+$", "", d)
    # Trim
    d = d.strip().strip(",").strip()
    if len(d) > 35:
        d = d[:35].strip()
    # Title case
    if d:
        d = d.title()
    return d if d else desc[:35].strip().title()

def clean_description(desc):
    """Truncate description to 40 chars."""
    return desc.strip()[:40]

def is_card_payment(amount, desc):
    """Skip card payments (positive amount + PAYMENT in desc)."""
    d = desc.upper()
    if amount > 0 and "PAYMENT" in d and ("THANK YOU" in d or "MERCI" in d or "PAI EMENT" in d):
        return True
    return False

def is_internal_transfer(desc):
    """Skip internal bank transfers."""
    d = desc.upper()
    if "ONLINE BANKING TRANSFER" in d:
        return True
    return False

# ---------- CATEGORIZATION ----------

def categorize(desc, amount, account_label, default_biz):
    """Return (business: bool, category: str, split: str, notes: str)."""
    d = desc.upper()
    amt = amount  # negative = expense, positive = income/refund

    # --- INCOME (positive amounts) ---
    if amt > 0:
        # Stripe
        if "STRIPE" in d:
            return True, "Stripe (Revenue)", "100%", ""
        # E-transfer received - business clients
        if "E-TRANSFER RECEIVED" in d:
            biz_clients = ["BALMORAL", "SHALA YOGA", "DARREN JUKES", "VERNON PETTY",
                           "RACHELLE VICTORIA", "ETERNAL NECTAR", "SOUTHPAW",
                           "PWC WINDOW", "SALISH", "OMAR", "SEBASTIAN",
                           "WOOD BECOMES WATER", "JUAN", "WILDLIFE", "BOOKKEEPER",
                           "RBC PAYEDGE"]
            for client in biz_clients:
                if client in d:
                    return True, "E-Transfer (Revenue)", "100%", ""
            # Self transfer
            if "MATTHEW FERNANDES" in d or "MATTHEWANTHONYFERNANDES" in d:
                return False, "Other Personal", "100%", ""
            # Unknown e-transfer - default based on account
            return default_biz, "E-Transfer (Revenue)" if default_biz else "Other Personal", "100%", ""
        # Mobile/ATM deposit
        if "MOBILE CHEQUE DEPOSIT" in d or "ATM DEPOSIT" in d:
            return True, "Deposit (Revenue)", "100%", ""
        # GST / CWB
        if "GST" in d and "CANADA" in d:
            return False, "Government Benefits", "100%", ""
        if "CANADA WORKERS" in d or "CWB" in d:
            return False, "Government Benefits", "100%", ""
        # Refunds (Amazon, Adobe, MEC etc) - keep as expense offsets
        if any(x in d for x in ["AMAZON", "ADOBE", "MEC", "MOUNTAIN EQUIPMENT"]):
            return default_biz if account_label == "Business Card" else False, _cat_for_refund(d), "100%", "Refund"
        # Default positive on business accounts
        if default_biz:
            return True, "Other Income", "100%", ""
        return False, "Other Personal", "100%", ""

    # --- EXPENSES (negative amounts) ---
    # Advertising & Marketing
    if any(x in d for x in ["HIGHLEVEL", "GOHIGHLEVEL"]):
        return True, "Advertising & Marketing", "100%", ""
    if any(x in d for x in ["FACEBK", "FACEBOOK"]):
        return True, "Advertising & Marketing", "100%", ""
    if "RESIDENT ADVISOR" in d:
        return True, "Advertising & Marketing", "100%", ""
    if "EVENTBRITE" in d:
        return True, "Advertising & Marketing", "100%", ""
    if "SEA TO SKY GONDOLA" in d:
        return True, "Advertising & Marketing", "100%", ""

    # Software & Subscriptions
    software_kw = ["INSTANTLY", "LEADGENJAY", "OPENAI", "CHATGPT", "SQUARESPACE", "SQSP",
                   "GOOGLE*GSUITE", "GOOGLE *WORKSPACE", "GOOGLE*WORKSPACE",
                   "BUFFER", "CLICKUP", "EPIDEMIC SOUND", "QUICKBOOKS", "INTUIT*QBOOKS",
                   "SOUNDSTRIPE", "DROPBOX", "PROEDU", "GAMUT", "SHEETMAGIC",
                   "AUTOIGDM", "N8N", "PADDLE.NET", "TRUSTED LEADS", "QWILR",
                   "TINYPNG", "MANYCHAT", "MAIL AUTOMATION", "XAI", "X.AI",
                   "NETFLIX", "AUDIBLE", "SPOTIFY", "BEATPORT", "TEMPO DIGITAL",
                   "RULE 1 INVESTING"]
    if any(x in d for x in software_kw):
        return True, "Software & Subscriptions", "100%", ""

    # Adobe - software
    if "ADOBE" in d:
        return True, "Software & Subscriptions", "100%", ""

    # Equipment (CCA)
    if "DJI" in d:
        return True, "Equipment (CCA)", "100%", ""
    if "CAMERA CANADA" in d:
        return True, "Equipment (CCA)", "100%", ""
    if "AFFIRM" in d:
        return True, "Equipment (CCA)", "100%", ""
    if "APPLE STORE" in d or "APPLE.COM" in d:
        return True, "Equipment (CCA)", "100%", ""
    # Amazon - check amount
    if "AMAZON" in d:
        if abs(amt) > 500:
            return True, "Equipment (CCA)", "100%", ""
        else:
            return True, "Office Supplies (<$500)", "100%", ""

    # Office Supplies
    if any(x in d for x in ["HOME DEPOT", "CANADIAN TIRE", "RONA"]):
        return True, "Office Supplies (<$500)", "100%", ""
    if "CPC" in d and "SCP" in d:
        return True, "Office Supplies (<$500)", "100%", ""
    if "UPS" in d and ("STORE" in d or "UPS #" in d or len(d) < 20):
        return True, "Office Supplies (<$500)", "100%", ""

    # Vehicle
    gas_kw = ["PETRO-CANADA", "PETRO CANADA", "CHEVRON", "CHV", "SHELL", "ESSO",
              "CANCO", "OTTER CO-OP", "SQUAMISH VALLEY GAS"]
    if any(x in d for x in gas_kw):
        return True, "Vehicle", "100%", ""
    parking_kw = ["EASYPARK", "VILLAGE PARKING", "PAY PARKING", "HONK PARKING", "IMPARK"]
    if any(x in d for x in parking_kw):
        return True, "Vehicle", "100%", ""
    if "PARKING" in d and "CITY OF VANCOUVER" not in d:
        return True, "Vehicle", "100%", ""
    if "GREAT CANADIAN OIL" in d:
        return True, "Vehicle", "100%", ""
    if "BC FERRIES" in d or "BCF" in d:
        return True, "Vehicle", "100%", ""
    if "ICBC" in d:
        return True, "Vehicle", "70%", ""
    if "CITY OF VANCOUVER" in d and "PARKING" in d:
        return False, "Transportation", "100%", ""

    # Insurance
    if "COOPERATORS" in d:
        return True, "Insurance", "70%", ""

    # Telephone & Internet
    if "ROGERS" in d:
        return True, "Telephone & Internet", "100%", ""

    # Interest & Bank Charges
    if "MONTHLY FEE" in d or "ANNUAL FEE" in d:
        return True, "Interest & Bank Charges", "100%", ""
    if "PURCHASE INTEREST" in d or "INTEREST CHARGE" in d:
        return True, "Interest & Bank Charges", "100%", ""
    if "LOAN INTEREST" in d:
        return True, "Interest & Bank Charges", "100%", ""

    # Rent / Co-working
    if "FILI SPACE" in d:
        return True, "Rent / Co-working", "100%", ""
    if "SACRED DANCE" in d:
        return True, "Rent / Co-working", "100%", ""

    # Professional Fees
    if "TRANSPORT CANADA" in d:
        return True, "Professional Fees", "100%", ""
    if "TURBOTAX" in d or "INTUIT*TURBOTAX" in d:
        return True, "Professional Fees", "100%", ""

    # Travel
    if "AIRBNB" in d:
        return True, "Travel", "50%", ""

    # Mattanthonyphoto
    if "MATTANTHONYPHOTO" in d:
        return True, "Software & Subscriptions", "100%", "Website hosting test"

    # --- PERSONAL ---
    # Housing
    if "E-TRANSFER SENT" in d and "RENT" in d:
        return False, "Housing", "100%", ""

    # Savings/Investments
    if any(x in d for x in ["QUESTRADE", "SHAKEPAY"]):
        return False, "Savings/Investments", "100%", ""

    # ATM/Cash
    if "ATM WITHDRAWAL" in d or "CASH WITHDRAWAL" in d:
        return False, "Other Personal", "100%", ""

    # CRA
    if "CCRA" in d or ("CRA" in d and "PAD" in d):
        return False, "Other Personal", "100%", ""

    # Afterpay
    if "AFTERPAY" in d:
        return False, "Other Personal", "100%", ""

    # E-transfer sent (personal)
    if "E-TRANSFER SENT" in d:
        return False, "Other Personal", "100%", ""

    # Groceries
    grocery_kw = ["COSTCO", "WAL-MART", "WALMART", "SAFEWAY", "SAVE ON", "SAVE-ON",
                  "THRIFTY", "SUPERSTORE", "BUY LOW", "FRESH ST", "IGA", "NESTERS",
                  "HECTOR", "CLEVELAND MEATS"]
    if any(x in d for x in grocery_kw):
        return False, "Groceries", "100%", ""
    if "LONDON DRUGS" in d:
        return False, "Groceries", "100%", ""

    # Clothing
    if any(x in d for x in ["MARKS/", "MARKS #", "#829 MARKS", "MEC ", "MOUNTAIN EQUIPMENT",
                             "SP DU/ER", "CREATIVE STITCHES"]):
        return False, "Clothing", "100%", ""

    # Entertainment
    ent_kw = ["LIQUOR", "BC LIQUOR", "SCANDINAVE", "BELTANE", "SHAMBHALA",
              "TICKETMASTER", "CINEPLEX", "HR MACMILLAN", "RED ROOM", "FOUR VISIONS"]
    if any(x in d for x in ent_kw):
        return False, "Entertainment", "100%", ""

    # Pets
    if "BOSLEYS" in d:
        return False, "Other Personal", "100%", ""

    # Health & Fitness
    if any(x in d for x in ["CLIMB GROUNDUP", "BODY ENERGY"]):
        return False, "Health & Fitness", "100%", ""

    # Dining Out
    dining_kw = ["TIM HORTONS", "DOMINOS", "BARBURRITO", "PUREBREAD", "ESSENCE OF INDIA",
                 "NOODLEBOX", "RAMEN BUTCHER", "A-FRAME", "BUVETTE", "TRICKSTER",
                 "SUNNY CHIBAS", "CLOUDBURST", "LOCAVORE", "BACKCOUNTRY",
                 "FC FUNCTION", "MCDONALDS", "MCDONALD'S", "SUBWAY", "STARBUCKS",
                 "BLENZ", "WAVES COFFEE", "BREKA", "JJ BEAN", "CACTUS CLUB",
                 "EARLS", "JOEYS", "WHITE SPOT", "DENNY", "BOSTON PIZZA",
                 "A&W", "PANAGO", "PIZZA", "CAFE", "RESTAURANT", "GRILL",
                 "SUSHI", "THAI", "POKE", "BURRITO", "TACO", "BREW",
                 "MEDITERRANEAN G", "WONDERLANDS", "SEA TO SKY HOTEL",
                 "COPPER COIL", "NORMAN RUIZ", "PEAKED PIES", "ZEPHYR",
                 "FERGIES", "BACK BOWL", "SPLITZ"]
    if any(x in d for x in dining_kw):
        return False, "Dining Out", "100%", ""

    # Transportation
    if "RIDEHUB" in d:
        return False, "Transportation", "100%", ""
    if any(x in d for x in ["BLACK TOP", "CHECKER CAB"]):
        return False, "Transportation", "100%", ""

    # PayPal - default to personal unless on business account
    if "PAYPAL" in d:
        if default_biz:
            return True, "Other Business", "100%", "PayPal"
        return False, "Other Personal", "100%", "PayPal"

    # Default for business card
    if default_biz:
        return True, "Other Business", "100%", ""

    # Default personal
    return False, "Other Personal", "100%", ""


def _cat_for_refund(d):
    if "AMAZON" in d:
        return "Office Supplies (<$500)"
    if "ADOBE" in d:
        return "Software & Subscriptions"
    if "MEC" in d or "MOUNTAIN EQUIPMENT" in d:
        return "Clothing"
    return "Other Personal"


def parse_all_csvs():
    """Parse all 4 CSV files, return list of transaction dicts."""
    all_txns = []
    for cfg in CSV_FILES:
        path = cfg["path"]
        label = cfg["label"]
        payment = cfg["payment"]
        default_biz = cfg["default_business"]

        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            count = 0
            skipped = 0
            for row in reader:
                desc1 = row.get("Description 1", "").strip()
                desc2 = row.get("Description 2", "").strip()
                full_desc = f"{desc1} {desc2}".strip() if desc2 else desc1
                date_str = row.get("Transaction Date", "").strip()
                cad = row.get("CAD$", "").strip()

                if not date_str or not cad:
                    continue

                try:
                    amount = float(cad.replace(",", ""))
                except ValueError:
                    continue

                # Skip card payments
                if is_card_payment(amount, full_desc):
                    skipped += 1
                    continue

                # Skip internal transfers
                if is_internal_transfer(full_desc):
                    skipped += 1
                    continue

                d = parse_date(date_str)
                if not d:
                    continue

                business, category, split, notes = categorize(full_desc, amount, label, default_biz)

                # GST calc for business expenses (negative amounts)
                gst = 0
                if business and amount < 0:
                    split_pct = float(split.replace("%", "")) / 100.0
                    gst = round(abs(amount) * split_pct * 5 / 105, 2)

                vendor = clean_vendor(full_desc)
                description = clean_description(full_desc)

                all_txns.append({
                    "date_serial": to_serial(d),
                    "date_obj": d,
                    "vendor": vendor,
                    "description": description,
                    "amount": amount,
                    "business": business,
                    "category": category,
                    "split": split,
                    "gst": gst,
                    "receipt": False,
                    "payment": payment,
                    "account": label,
                    "notes": notes,
                })
                count += 1

            print(f"  {label} ({cfg['account_num']}): {count} transactions loaded, {skipped} skipped")

    return all_txns


def build_sheet_data(txns):
    """Split into income/expenses, sort, build rows."""
    income = sorted([t for t in txns if t["amount"] > 0], key=lambda t: t["date_serial"])
    expenses = sorted([t for t in txns if t["amount"] <= 0], key=lambda t: t["date_serial"])

    print(f"\nIncome transactions: {len(income)}")
    print(f"Expense transactions: {len(expenses)}")
    print(f"Total income: ${sum(t['amount'] for t in income):,.2f}")
    print(f"Total expenses: ${sum(t['amount'] for t in expenses):,.2f}")

    def to_row(t):
        return [
            t["date_serial"],       # A: Date
            t["vendor"],            # B: Vendor
            t["description"],       # C: Description
            t["amount"],            # D: Amount
            t["business"],          # E: Business
            t["category"],          # F: Category
            t["split"],             # G: Split%
            t["gst"],              # H: GST
            False,                  # I: Receipt
            t["payment"],           # J: Payment
            t["account"],           # K: Account
            t["notes"],             # L: Notes
        ]

    rows = []

    # Row 1-3: leave blank (title area - don't touch)
    rows.append([])  # row 1
    rows.append([])  # row 2
    rows.append([])  # row 3

    # Row 4: INCOME header
    inc_start = 6
    inc_end = 5 + len(income)
    rows.append([
        "INCOME", "", "",
        f"=SUM(D{inc_start}:D{inc_end})",
        "", "", "", "", "", "",
        f"{len(income)} transactions", ""
    ])

    # Row 5: Column headers
    rows.append(["Date", "Vendor", "Description", "", "Business", "Category", "", "", "Receipt", "Payment", "Account", "Notes"])

    # Income rows (row 6+)
    for t in income:
        rows.append(to_row(t))

    # 2 blank spacer rows
    rows.append([])
    rows.append([])

    # EXPENSES header
    exp_header_row = len(rows) + 1
    exp_start = exp_header_row + 2
    exp_end = exp_start + len(expenses) - 1
    rows.append([
        "EXPENSES", "", "",
        f"=SUM(D{exp_start}:D{exp_end})",
        "", "", "", "", "", "",
        f"{len(expenses)} transactions", ""
    ])

    # Column headers for expenses
    rows.append(["Date", "Vendor", "Description", "", "Business", "Category", "", "", "Receipt", "Payment", "Account", "Notes"])

    # Expense rows
    for t in expenses:
        rows.append(to_row(t))

    return rows, income, expenses, inc_start, inc_end, exp_header_row, exp_start, exp_end


def get_sheet_id(service, spreadsheet_id, sheet_name):
    """Get the sheetId for a named tab."""
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for s in meta["sheets"]:
        if s["properties"]["title"] == sheet_name:
            return s["properties"]["sheetId"]
    return None


def write_to_sheets(rows, income, expenses, inc_start, inc_end, exp_header_row, exp_start, exp_end):
    service = get_sheets_service()
    sheet_id = get_sheet_id(service, SPREADSHEET_ID, SHEET_NAME)

    if sheet_id is None:
        print(f"Sheet '{SHEET_NAME}' not found!")
        return

    total_rows = len(rows)
    print(f"\nTotal rows to write: {total_rows}")

    # Step 1: Clear existing data (rows 4+) keeping title area
    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{SHEET_NAME}'!A4:Z10000"
    ).execute()
    print("Cleared existing data from row 4+")

    # Step 2: Write all data starting from row 1
    # We write rows 4+ (index 3+) to preserve title area
    write_rows = rows[3:]  # skip first 3 empty placeholder rows

    # Batch write in chunks to avoid limits
    chunk_size = 500
    for i in range(0, len(write_rows), chunk_size):
        chunk = write_rows[i:i+chunk_size]
        start_row = 4 + i
        end_row = start_row + len(chunk) - 1
        range_str = f"'{SHEET_NAME}'!A{start_row}:L{end_row}"

        body = {"values": chunk}
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_str,
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        print(f"  Wrote rows {start_row}-{end_row}")

    # Step 3: Add month helper in column N
    month_formulas = []
    for r in range(inc_start, inc_end + 1):
        month_formulas.append([f'=TEXT(A{r},"MMM")'])

    if month_formulas:
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{SHEET_NAME}'!N{inc_start}:N{inc_end}",
            valueInputOption="USER_ENTERED",
            body={"values": month_formulas}
        ).execute()

    exp_month_formulas = []
    for r in range(exp_start, exp_end + 1):
        exp_month_formulas.append([f'=TEXT(A{r},"MMM")'])

    if exp_month_formulas:
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{SHEET_NAME}'!N{exp_start}:N{exp_end}",
            valueInputOption="USER_ENTERED",
            body={"values": exp_month_formulas}
        ).execute()
    print("Added month helpers in column N")

    # Step 4: Formatting requests
    requests = []

    # Hide column N
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": 13,  # N = index 13
                "endIndex": 14
            },
            "properties": {"hiddenByUser": True},
            "fields": "hiddenByUser"
        }
    })

    # Date format on column A
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 3,
                "endRowIndex": total_rows,
                "startColumnIndex": 0,
                "endColumnIndex": 1
            },
            "cell": {
                "userEnteredFormat": {
                    "numberFormat": {
                        "type": "DATE",
                        "pattern": "MMM d, yyyy"
                    }
                }
            },
            "fields": "userEnteredFormat.numberFormat"
        }
    })

    # Amount format on column D
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 3,
                "endRowIndex": total_rows,
                "startColumnIndex": 3,
                "endColumnIndex": 4
            },
            "cell": {
                "userEnteredFormat": {
                    "numberFormat": {
                        "type": "CURRENCY",
                        "pattern": "$#,##0.00;($#,##0.00)"
                    }
                }
            },
            "fields": "userEnteredFormat.numberFormat"
        }
    })

    # INCOME header row (row 4) - green background, bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 3,
                "endRowIndex": 4,
                "startColumnIndex": 0,
                "endColumnIndex": 12
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.85, "green": 0.95, "blue": 0.85},
                    "textFormat": {"bold": True, "fontSize": 11}
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    })

    # Income column headers (row 5) - bold, grey bg
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 4,
                "endRowIndex": 5,
                "startColumnIndex": 0,
                "endColumnIndex": 12
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                    "textFormat": {"bold": True, "fontSize": 10}
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    })

    # EXPENSES header row - red background, bold
    exp_header_idx = exp_header_row - 1  # 0-indexed
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": exp_header_idx,
                "endRowIndex": exp_header_idx + 1,
                "startColumnIndex": 0,
                "endColumnIndex": 12
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.95, "green": 0.85, "blue": 0.85},
                    "textFormat": {"bold": True, "fontSize": 11}
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    })

    # Expense column headers - bold, grey bg
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": exp_header_idx + 1,
                "endRowIndex": exp_header_idx + 2,
                "startColumnIndex": 0,
                "endColumnIndex": 12
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                    "textFormat": {"bold": True, "fontSize": 10}
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    })

    # Checkboxes on column E (Business) for income rows
    for start, end in [(inc_start - 1, inc_end), (exp_start - 1, exp_end)]:
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start,
                    "endRowIndex": end,
                    "startColumnIndex": 4,
                    "endColumnIndex": 5
                },
                "cell": {
                    "dataValidation": {
                        "condition": {"type": "BOOLEAN"},
                        "strict": True
                    }
                },
                "fields": "dataValidation"
            }
        })

    # Checkboxes on column I (Receipt)
    for start, end in [(inc_start - 1, inc_end), (exp_start - 1, exp_end)]:
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start,
                    "endRowIndex": end,
                    "startColumnIndex": 8,
                    "endColumnIndex": 9
                },
                "cell": {
                    "dataValidation": {
                        "condition": {"type": "BOOLEAN"},
                        "strict": True
                    }
                },
                "fields": "dataValidation"
            }
        })

    # Category dropdown on column F
    categories = [
        "Stripe (Revenue)", "E-Transfer (Revenue)", "Deposit (Revenue)", "Other Income",
        "Government Benefits",
        "Advertising & Marketing", "Software & Subscriptions", "Equipment (CCA)",
        "Office Supplies (<$500)", "Vehicle", "Insurance", "Telephone & Internet",
        "Interest & Bank Charges", "Rent / Co-working", "Professional Fees",
        "Travel", "Meals & Entertainment", "Other Business",
        "Housing", "Groceries", "Dining Out", "Entertainment", "Health & Fitness",
        "Clothing", "Transportation", "Savings/Investments", "Other Personal"
    ]
    for start, end in [(inc_start - 1, inc_end), (exp_start - 1, exp_end)]:
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start,
                    "endRowIndex": end,
                    "startColumnIndex": 5,
                    "endColumnIndex": 6
                },
                "cell": {
                    "dataValidation": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [{"userEnteredValue": c} for c in categories]
                        },
                        "showCustomUi": True,
                        "strict": False
                    }
                },
                "fields": "dataValidation"
            }
        })

    # Split% dropdown on column G
    splits = ["100%", "70%", "50%", "30%", "0%"]
    for start, end in [(inc_start - 1, inc_end), (exp_start - 1, exp_end)]:
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start,
                    "endRowIndex": end,
                    "startColumnIndex": 6,
                    "endColumnIndex": 7
                },
                "cell": {
                    "dataValidation": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [{"userEnteredValue": s} for s in splits]
                        },
                        "showCustomUi": True,
                        "strict": False
                    }
                },
                "fields": "dataValidation"
            }
        })

    # Conditional formatting: blue bg for business=TRUE rows
    for start, end in [(inc_start - 1, inc_end), (exp_start - 1, exp_end)]:
        requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sheet_id,
                        "startRowIndex": start,
                        "endRowIndex": end,
                        "startColumnIndex": 0,
                        "endColumnIndex": 12
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "CUSTOM_FORMULA",
                            "values": [{"userEnteredValue": f"=$E{start+1}=TRUE"}]
                        },
                        "format": {
                            "backgroundColor": {"red": 0.88, "green": 0.93, "blue": 1.0}
                        }
                    }
                },
                "index": 0
            }
        })

    # Conditional formatting: red text for negative amounts
    for start, end in [(inc_start - 1, inc_end), (exp_start - 1, exp_end)]:
        requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sheet_id,
                        "startRowIndex": start,
                        "endRowIndex": end,
                        "startColumnIndex": 3,
                        "endColumnIndex": 4
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "CUSTOM_FORMULA",
                            "values": [{"userEnteredValue": f"=$D{start+1}<0"}]
                        },
                        "format": {
                            "textFormat": {"foregroundColor": {"red": 0.8, "green": 0.1, "blue": 0.1}}
                        }
                    }
                },
                "index": 0
            }
        })

    # Conditional formatting: green text for positive amounts
    for start, end in [(inc_start - 1, inc_end), (exp_start - 1, exp_end)]:
        requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sheet_id,
                        "startRowIndex": start,
                        "endRowIndex": end,
                        "startColumnIndex": 3,
                        "endColumnIndex": 4
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "CUSTOM_FORMULA",
                            "values": [{"userEnteredValue": f"=$D{start+1}>0"}]
                        },
                        "format": {
                            "textFormat": {"foregroundColor": {"red": 0.1, "green": 0.6, "blue": 0.1}}
                        }
                    }
                },
                "index": 0
            }
        })

    # Alternating white / #F7F8FA rows for data sections
    for start, end in [(inc_start - 1, inc_end), (exp_start - 1, exp_end)]:
        requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sheet_id,
                        "startRowIndex": start,
                        "endRowIndex": end,
                        "startColumnIndex": 0,
                        "endColumnIndex": 12
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "CUSTOM_FORMULA",
                            "values": [{"userEnteredValue": f"=MOD(ROW(),2)=0"}]
                        },
                        "format": {
                            "backgroundColor": {"red": 0.969, "green": 0.973, "blue": 0.98}
                        }
                    }
                },
                "index": 99  # lower priority
            }
        })

    # Execute all formatting
    if requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": requests}
        ).execute()
        print("Applied all formatting")

    print("\nDone! Sheet rebuilt successfully.")


def print_summary(income, expenses):
    """Print summary stats."""
    inc_total = sum(t["amount"] for t in income)
    exp_total = sum(t["amount"] for t in expenses)
    biz_exp = sum(t["amount"] for t in expenses if t["business"])
    per_exp = sum(t["amount"] for t in expenses if not t["business"])

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Income rows: {len(income)}")
    print(f"Income total: ${inc_total:,.2f}")
    print(f"Expense rows: {len(expenses)}")
    print(f"Expense total: ${exp_total:,.2f}")
    print(f"Business expense total: ${biz_exp:,.2f}")
    print(f"Personal expense total: ${per_exp:,.2f}")

    print("\nTop 10 Business Expense Categories:")
    cat_totals = {}
    for t in expenses:
        if t["business"]:
            cat = t["category"]
            cat_totals[cat] = cat_totals.get(cat, 0) + t["amount"]

    sorted_cats = sorted(cat_totals.items(), key=lambda x: x[1])
    for i, (cat, total) in enumerate(sorted_cats[:10], 1):
        print(f"  {i}. {cat}: ${total:,.2f}")


if __name__ == "__main__":
    print("Parsing CSV files...")
    txns = parse_all_csvs()
    print(f"\nTotal transactions: {len(txns)}")

    print("\nBuilding sheet data...")
    rows, income, expenses, inc_start, inc_end, exp_header_row, exp_start, exp_end = build_sheet_data(txns)

    print("\nWriting to Google Sheets...")
    write_to_sheets(rows, income, expenses, inc_start, inc_end, exp_header_row, exp_start, exp_end)

    print_summary(income, expenses)
