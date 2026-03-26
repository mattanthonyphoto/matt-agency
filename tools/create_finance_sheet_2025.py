"""
Matt Anthony Photography — 2025 Finance Sheet
Mirrors 2026 design language. Chequing + Business account CSVs.
Single row per transaction, Split% column handles partial deductions.
"""
import sys, os, csv, re
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.google_sheets_auth import get_sheets_service, get_drive_service

YEAR = 2025

# ═══════════════════════════════════════════
# DESIGN TOKENS — Light, clean, minimal (same as 2026)
# ═══════════════════════════════════════════
C = {
    "white":    {"red": 1.0, "green": 1.0, "blue": 1.0},
    "bg":       {"red": 0.976, "green": 0.980, "blue": 0.984},
    "card":     {"red": 1.0, "green": 1.0, "blue": 1.0},
    "row_alt":  {"red": 0.969, "green": 0.973, "blue": 0.980},
    "border":   {"red": 0.906, "green": 0.914, "blue": 0.929},
    "border_l": {"red": 0.937, "green": 0.941, "blue": 0.949},
    "input":    {"red": 0.957, "green": 0.961, "blue": 0.969},
    "t1":       {"red": 0.098, "green": 0.114, "blue": 0.149},
    "t2":       {"red": 0.357, "green": 0.380, "blue": 0.427},
    "t3":       {"red": 0.549, "green": 0.573, "blue": 0.612},
    "t4":       {"red": 0.702, "green": 0.718, "blue": 0.745},
    "blue":     {"red": 0.224, "green": 0.443, "blue": 0.871},
    "blue_bg":  {"red": 0.922, "green": 0.941, "blue": 0.988},
    "blue_l":   {"red": 0.957, "green": 0.969, "blue": 0.996},
    "green":    {"red": 0.118, "green": 0.624, "blue": 0.424},
    "green_bg": {"red": 0.906, "green": 0.969, "blue": 0.941},
    "green_l":  {"red": 0.949, "green": 0.984, "blue": 0.969},
    "red":      {"red": 0.851, "green": 0.200, "blue": 0.200},
    "red_bg":   {"red": 0.992, "green": 0.929, "blue": 0.929},
    "red_l":    {"red": 0.996, "green": 0.957, "blue": 0.957},
    "orange":   {"red": 0.902, "green": 0.533, "blue": 0.118},
    "orange_bg":{"red": 0.996, "green": 0.953, "blue": 0.906},
    "purple":   {"red": 0.486, "green": 0.318, "blue": 0.804},
    "purple_bg":{"red": 0.949, "green": 0.933, "blue": 0.988},
    "cyan":     {"red": 0.059, "green": 0.588, "blue": 0.682},
    "cyan_bg":  {"red": 0.906, "green": 0.969, "blue": 0.980},
    "navy":     {"red": 0.153, "green": 0.173, "blue": 0.224},
}

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
BIZ_CATS = ["Advertising & Marketing","Professional Fees","Vehicle","Insurance",
    "Interest & Bank Charges","Office Supplies (<$500)","Rent / Co-working",
    "Software & Subscriptions","Travel","Telephone & Internet","Subcontractors",
    "Meals & Entertainment","Home Office","Equipment (CCA)","Other Business"]
PERS_CATS = ["Housing","Utilities","Groceries","Dining Out","Transportation",
    "Health & Fitness","Subscriptions","Clothing","Entertainment",
    "Travel (Personal)","Savings/Investments","Other Personal"]
ALL_CATS = BIZ_CATS + PERS_CATS

T2125 = {"Advertising & Marketing":"8521","Professional Fees":"8590","Vehicle":"8615",
    "Insurance":"8690","Interest & Bank Charges":"8710","Office Supplies (<$500)":"8811",
    "Rent / Co-working":"8860","Software & Subscriptions":"8871","Travel":"8910",
    "Telephone & Internet":"8945","Subcontractors":"9060","Meals & Entertainment":"9270",
    "Home Office":"9281","Equipment (CCA)":"9936","Other Business":"—"}

# ═══════════════════════════════════════════
# CATEGORIZATION RULES FOR 2025 CHEQUING
# ═══════════════════════════════════════════
# Order matters — first match wins.
# Format: (pattern, is_business, category, clean_name, split_pct)
RULES = [
    # ── BUSINESS INCOME (positive amounts) ──
    # Stripe and e-transfers handled in parse logic, not here

    # ── 100% BUSINESS EXPENSES ──
    (r"MONTHLY FEE|Monthly fee", True, "Interest & Bank Charges", "Bank Monthly Fee", 100),
    (r"LOAN INTEREST", True, "Interest & Bank Charges", "Loan Interest", 100),
    (r"PETRO-CANADA", True, "Vehicle", "Petro-Canada (Fuel)", 100),

    # ── 100% BUSINESS (per Matt) ──
    (r"ROGERS WIRELESS", True, "Telephone & Internet", "Rogers Wireless", 100),

    # ── 50% BUSINESS ──
    (r"AUTO INSURANCE ICBC", True, "Vehicle", "ICBC Auto Insurance", 50),
    (r"INSURANCE COOPERATORS|COOPERATORS CSI", True, "Insurance", "Cooperators Insurance", 50),

    # ── PERSONAL — Housing ──
    (r"E-TRANSFER SENT.*RENT", False, "Housing", "Rent", 0),

    # ── PERSONAL — Financing (not deductible) ──
    (r"MISC PAYMENT AFFIRM", False, "Other Personal", "Affirm (Financing)", 0),

    # ── PERSONAL — Savings/Investments ──
    (r"MISC PAYMENT QUESTRADE", False, "Savings/Investments", "Questrade", 0),
    (r"E-TRANSFER SENT SHAKEPAY|E-TRANSFER.*AUTODEPOSIT SHAKEPAY|E-TRANSFER REQUEST FULFILLED.*SHAKEPAY", False, "Savings/Investments", "Shakepay (Crypto)", 0),

    # ── PERSONAL — Gov benefits ──
    (r"GST CANADA", False, "Other Personal", "GST Credit (Gov)", 0),
    (r"CANADA WORKERS BENEFIT", False, "Other Personal", "CWB (Gov Benefit)", 0),
    (r"PAD CCRA CANADA", False, "Other Personal", "CRA Tax Payment", 0),

    # ── PERSONAL — Cash ──
    (r"ATM WITHDRAWAL", False, "Other Personal", "ATM Withdrawal", 0),
    (r"CASH WITHDRAWAL", False, "Other Personal", "Cash Withdrawal", 0),

    # ── SKIP — Internal transfers ──
    (r"ONLINE BANKING TRANSFER", None, "Skip", "Internal Transfer", 0),
    (r"ONLINE BANKING LOAN PAYMENT", None, "Skip", "Loan Payment (Principal)", 0),

    # ── PERSONAL — PayPal ──
    (r"MISC PAYMENT PAYPAL", False, "Other Personal", "PayPal", 0),

    # ── PERSONAL — Dining ──
    (r"HECTOR.S YOUR I", False, "Groceries", "Hector's IGA", 0),
    (r"TIM HORTONS", False, "Dining Out", "Tim Hortons", 0),
    (r"DOMINOS PIZZA", False, "Dining Out", "Domino's Pizza", 0),
    (r"PUREBREAD", False, "Dining Out", "Purebread Bakery", 0),
    (r"LONDON DRUGS", False, "Groceries", "London Drugs", 0),
    (r"CLIMB GROUNDUP", False, "Health & Fitness", "Ground Up Climbing", 0),
    (r"BACKCOUNTRY|SQ \*BACKCOUNTRY", False, "Dining Out", "Backcountry Brewing", 0),
    (r"A-FRAME BRE", False, "Dining Out", "A-Frame Brewing", 0),
    (r"MEDITERRANEAN G", False, "Dining Out", "Mediterranean Grill", 0),
    (r"SP WONDERLANDS", False, "Entertainment", "Wonderlands", 0),
    (r"SEA TO SKY GOND", False, "Entertainment", "Sea to Sky Gondola", 0),
    (r"RIDEHUB", False, "Transportation", "RideHub", 0),
    (r"ESSENCE OF INDI", False, "Dining Out", "Essence of India", 0),
    (r"COSTCO WHOLESAL", False, "Groceries", "Costco", 0),
    (r"MIRAAS RESTAURA", False, "Dining Out", "Miraas Restaurant", 0),
    (r"SQ \*THE BUNKER", False, "Dining Out", "The Bunker", 0),
    (r"MANPUKU", False, "Dining Out", "Manpuku", 0),
    (r"SQ \*PUREBREAD", False, "Dining Out", "Purebread Bakery", 0),

    # ── PERSONAL — Olga Lissey = damage deposit ──
    (r"E-TRANSFER RECEIVED OLGA LISSEY", False, "Other Personal", "Olga Lissey (Damage Deposit)", 0),

    # ── E-transfers to self = personal ──
    (r"E-TRANSFER SENT MATTHEW FERNANDES", False, "Other Personal", "E-Transfer (Self)", 0),
    (r"E-TRANSFER REQUEST FULFILLED MATTHEW FERNANDES", False, "Other Personal", "E-Transfer (Self)", 0),
    (r"E-TRANSFER REQUEST FULFILLED$", False, "Other Personal", "E-Transfer Request", 0),
    (r"E-TRANSFER SENT", False, "Other Personal", "E-Transfer Sent", 0),
]

# Known business clients for e-transfer matching
BIZ_CLIENTS = [
    "BALMORAL", "SHALA YOGA", "DARREN JUKES", "ETERNAL NECTAR",
    "SALISH ELEMENTS", "PWC WINDOW", "RACHELLE VICTORIA",
    "JH SOUTHPAW", "SOUTHPAW HOMES", "VERNON PETTY",
    "SEBASTIAN BEAUDET", "ALAYA", "WILDLIFE DIVISION",
    "WOOD BECOMES WATER", "JUAN  SEBASTIAN", "SEBASTIANCANON",
    "RBC PAYEDGE", "BOOKKEEPER", "OMAR KASSEM",
    "RACHAEL SARAH",
]


def categorize(desc):
    """Categorize a transaction description. Returns (is_biz, category, name, split_pct)."""
    for pattern, is_biz, cat, name, split in RULES:
        if re.search(pattern, desc, re.IGNORECASE):
            return is_biz, cat, name, split
    return False, "Other Personal", desc.split("  ")[0].strip()[:30], 0


def is_business_etransfer(desc):
    """Check if an e-transfer received matches a known business client."""
    for client in BIZ_CLIENTS:
        if client.upper() in desc.upper():
            return True, client.title()
    return False, None


def calc_gst(amt):
    return round(abs(amt) / 1.05 * 0.05, 2)


def parse_csv(path, account_name):
    """Parse bank CSV. Returns list of transaction rows.
    Columns: Date | Vendor | Description | Amount | Business? | Category | Split% | GST | Receipt? | Payment | Account | Notes | Month
    """
    rows = []
    with open(path, "r") as f:
        for row in csv.DictReader(f):
            amt_str = row.get("CAD$", "").strip()
            if not amt_str:
                continue
            amount = float(amt_str)
            d1 = row.get("Description 1", "").strip()
            d2 = row.get("Description 2", "").strip()
            desc = f"{d1} {d2}".strip()
            date = row.get("Transaction Date", "").strip()

            # ── STRIPE INCOME ──
            if "STRIPE" in desc.upper() and amount > 0:
                gst_collected = calc_gst(amount)
                rows.append([date, "Stripe (Revenue)", "GHL / Stripe payout",
                            amount, True, "Other Business", "100%", gst_collected,
                            True, "Debit", account_name, "Business income"])
                continue

            # ── MOBILE CHEQUE DEPOSIT = likely client cheque ──
            if "MOBILE CHEQUE DEPOSIT" in desc and amount > 0:
                gst_collected = calc_gst(amount)
                rows.append([date, "Client Cheque", desc[:40],
                            amount, True, "Other Business", "100%", gst_collected,
                            False, "Cheque", account_name, "Verify client"])
                continue

            # ── ATM DEPOSIT = likely client cash/cheque ──
            if "ATM DEPOSIT" in desc and amount > 0:
                gst_collected = calc_gst(amount)
                rows.append([date, "Cash/Cheque Deposit", desc[:40],
                            amount, True, "Other Business", "100%", gst_collected,
                            False, "Cash", account_name, "Verify — likely client"])
                continue

            # ── E-TRANSFER RECEIVED ──
            if "E-TRANSFER RECEIVED" in desc and amount > 0:
                is_client, client_name = is_business_etransfer(desc)
                if is_client:
                    gst_collected = calc_gst(amount)
                    rows.append([date, client_name, desc[:40],
                                amount, True, "Other Business", "100%", gst_collected,
                                False, "E-Transfer", account_name, "Client payment"])
                    continue
                # Olga Lissey special case
                if "OLGA LISSEY" in desc.upper():
                    rows.append([date, "Olga Lissey", "Damage deposit return",
                                amount, False, "Other Personal", "0%", 0,
                                False, "E-Transfer", account_name, "Not business"])
                    continue
                # Unknown e-transfer — mark for review
                name_match = re.search(r"E-TRANSFER RECEIVED (.+?)(?:\s+CA\w+)?$", desc)
                vendor = name_match.group(1).strip()[:25] if name_match else desc[:25]
                rows.append([date, vendor, desc[:40],
                            amount, False, "Other Personal", "0%", 0,
                            False, "E-Transfer", account_name, "Review — may be business"])
                continue

            # ── E-TRANSFER AUTODEPOSIT (Shakepay, etc.) ──
            if "E-TRANSFER" in desc and "AUTODEPOSIT" in desc and amount > 0:
                is_biz, cat, name, split = categorize(desc)
                if is_biz is None:  # skip
                    continue
                # Check if it's a known client
                is_client, client_name = is_business_etransfer(desc)
                if is_client:
                    gst_collected = calc_gst(amount)
                    rows.append([date, client_name, desc[:40],
                                amount, True, "Other Business", "100%", gst_collected,
                                False, "E-Transfer", account_name, "Client payment"])
                    continue
                rows.append([date, name, desc[:40],
                            amount, is_biz if is_biz is not None else False,
                            cat, "0%", 0,
                            False, "E-Transfer", account_name, ""])
                continue

            # ── Apply rules ──
            is_biz, cat, name, split_pct = categorize(desc)

            # Skip internal transfers
            if is_biz is None or cat == "Skip":
                continue

            # ── BUSINESS INCOME from Online Banking Transfer (rare but check) ──
            if "ONLINE BANKING TRANSFER" in desc:
                continue  # Already caught by rules above

            # ── Handle splits: SINGLE ROW, Split% column ──
            if split_pct == 50:
                gst = calc_gst(amount) if amount < 0 else 0
                rows.append([date, name, desc[:40],
                            amount, True, cat, "50%", gst,
                            False, "Debit", account_name, "50% deductible"])
                continue

            # ── Regular transaction ──
            gst = calc_gst(amount) if is_biz and amount < 0 else 0
            split_str = "100%" if is_biz else "0%"
            rows.append([date, name, desc[:40],
                        amount, is_biz, cat, split_str, gst,
                        False, "Debit", account_name, ""])

    return rows


def create():
    svc = get_sheets_service()

    # Parse both CSVs
    chq_path = "/Users/matthewfernandes/Downloads/download-transactions (5).csv"
    biz_path = "/Users/matthewfernandes/Downloads/download-transactions (7).csv"

    txn_rows = parse_csv(chq_path, "Chequing")
    txn_rows += parse_csv(biz_path, "Business Account")

    # Sort all by date
    txn_rows.sort(key=lambda x: datetime.strptime(x[0], "%m/%d/%Y"))
    print(f"Parsed {len(txn_rows)} transactions total")

    # Quick stats
    biz_income = sum(r[3] for r in txn_rows if r[4] is True and r[3] > 0)
    biz_expense = sum(abs(r[3]) for r in txn_rows if r[4] is True and r[3] < 0)
    print(f"Business income: ${biz_income:,.2f}")
    print(f"Business expenses: ${biz_expense:,.2f}")

    # ── Create spreadsheet ──
    tabs = [
        ("Dashboard", 0, 0, 22),
        ("Transactions", 1, 3, 14),
        ("Business", 2, 1, 18),
        ("Personal", 3, 1, 16),
        ("P&L", 4, 1, 12),
        ("GST", 5, 0, 10),
        ("Equipment", 6, 1, 14),
        ("Tax", 7, 0, 10),
    ]
    tab_colors = [C["blue"], C["green"], C["orange"], C["purple"], C["blue"], C["red"], C["green"], C["red"]]
    sheet_props = []
    for name, sid, frozen, cols in tabs:
        sheet_props.append({"properties": {
            "sheetId": sid, "title": name, "index": sid,
            "tabColorStyle": {"rgbColor": tab_colors[sid]},
            "gridProperties": {"frozenRowCount": frozen, "rowCount": 1000 if sid == 1 else 200, "columnCount": cols}
        }})

    sp = svc.spreadsheets().create(body={
        "properties": {
            "title": f"Matt Anthony — Finance {YEAR}",
            "locale": "en_CA",
            "defaultFormat": {
                "backgroundColor": C["bg"],
                "textFormat": {"foregroundColorStyle": {"rgbColor": C["t1"]}, "fontFamily": "Inter", "fontSize": 10}
            }
        },
        "sheets": sheet_props
    }).execute()
    sheet_id = sp["spreadsheetId"]
    url = sp["spreadsheetUrl"]
    print(f"Created: {url}")

    # ═══════════════════════════════════════════
    # TAB REFERENCES — formulas use Split% factor
    # ═══════════════════════════════════════════
    TQ = "Transactions"
    # Split factor formula component: multiply amounts by Split%
    # =IF(G$4:G$1000="",1,VALUE(SUBSTITUTE(G$4:G$1000,"%",""))/100)
    SF = 'IF({tq}!G$4:G$1000="",1,VALUE(SUBSTITUTE({tq}!G$4:G$1000,"%",""))/100)'.format(tq=TQ)
    # Month helper: handles both date serial numbers AND text dates
    MH = 'IFERROR(MONTH({tq}!A$4:A$1000),IFERROR(VALUE(LEFT({tq}!A$4:A$1000,FIND("/",{tq}!A$4:A$1000)-1)),0))'.format(tq=TQ)

    # ═══════════════════════════════════════════
    # DASHBOARD
    # ═══════════════════════════════════════════
    d = [
        [""] * 18,
        ["", "", f"Finance Dashboard  ·  {YEAR}", "","","","","","","","","","","","","","",""],
        ["", "", "Matt Anthony Photography","","","","","","","","","","","","","","",""],
        [""] * 18,
        # KPI labels
        ["", "",
         "Revenue", "",
         "", "",
         "Expenses", "",
         "", "",
         "Net Profit", "",
         "", "",
         "Est. Tax + CPP", "",
         "", ""],
        # KPI values — use Split% factor
        ["", "",
         f"=SUMPRODUCT(({TQ}!E4:E1000=TRUE)*({TQ}!D4:D1000>0)*{TQ}!D4:D1000*({SF}))", "",
         "", "",
         f"=SUMPRODUCT(({TQ}!E4:E1000=TRUE)*({TQ}!D4:D1000<0)*ABS({TQ}!D4:D1000)*({SF}))", "",
         "", "",
         "=C6-G6", "",
         "", "",
         "='Tax'!B44", "",
         "", ""],
        [""] * 18,
        # Submetrics
        ["", "",
         "of $105,237 actual", f"=IF(105237>0,C6/105237,0)",
         "", "",
         f"=SUMPRODUCT(({TQ}!E4:E1000=FALSE)*({TQ}!D4:D1000<0)*ABS({TQ}!D4:D1000))", "personal spending",
         "", "",
         "margin", "=IF(C6>0,K6/C6,0)",
         "", "",
         "quarterly installment", "=O6/4",
         "", ""],
        [""] * 18,
        [""] * 18,
        # ── MONTHLY BREAKDOWN ──
        ["", "", "Monthly Breakdown", "","","","","","","", "Spending by Category","","","","","","",""],
        # Headers
        ["", "", "Month", "Revenue", "Expenses", "Net", "Margin", "", "",
         "", "Category", "Amount", "% of Rev", "", "", "", "", ""],
    ]

    # Monthly rows
    for i, m in enumerate(MONTHS):
        mn = i + 1
        r = 13 + i  # sheet row (1-indexed)
        row = [""] * 18
        row[2] = m
        row[3] = f"=SUMPRODUCT(({TQ}!E$4:E$1000=TRUE)*({TQ}!D$4:D$1000>0)*({MH}={mn})*{TQ}!D$4:D$1000*({SF}))"
        row[4] = f"=SUMPRODUCT(({TQ}!E$4:E$1000=TRUE)*({TQ}!D$4:D$1000<0)*({MH}={mn})*ABS({TQ}!D$4:D$1000)*({SF}))"
        row[5] = f"=D{r+1}-E{r+1}"
        row[6] = f"=IF(D{r+1}>0,F{r+1}/D{r+1},0)"
        cats_list = ["Software & Subscriptions", "Travel", "Rent / Co-working", "Telephone & Internet",
                     "Advertising & Marketing", "Dining Out", "Groceries", "Health & Fitness",
                     "Subscriptions", "Entertainment", "Transportation", "Clothing"]
        if i < len(cats_list):
            cat = cats_list[i]
            is_biz = cat in BIZ_CATS
            biz_flag = "TRUE" if is_biz else "FALSE"
            row[10] = cat
            row[11] = f'=SUMPRODUCT(({TQ}!E$4:E$1000={biz_flag})*({TQ}!D$4:D$1000<0)*({TQ}!F$4:F$1000="{cat}")*ABS({TQ}!D$4:D$1000)*({SF}))'
            row[12] = f"=IF(C6>0,L{r+1}/C6,0)"
        d.append(row)

    # Total row (row 25 in sheet = index 24)
    tr = [""] * 18
    tr[2] = "Total"
    tr[3] = "=SUM(D14:D25)"
    tr[4] = "=SUM(E14:E25)"
    tr[5] = "=SUM(F14:F25)"
    tr[6] = "=IF(D26>0,F26/D26,0)"
    d.append(tr)

    d.append([""] * 18)
    # GST summary
    gst_row = [""] * 18
    gst_row[2] = "GST Summary"
    gst_row[10] = "Collected"
    gst_row[11] = f"=SUMPRODUCT(({TQ}!E4:E1000=TRUE)*({TQ}!D4:D1000>0)*{TQ}!H4:H1000)"
    d.append(gst_row)
    gst_row2 = [""] * 18
    gst_row2[10] = "ITCs"
    gst_row2[11] = f"=SUMPRODUCT(({TQ}!E4:E1000=TRUE)*({TQ}!D4:D1000<0)*{TQ}!H4:H1000)"
    d.append(gst_row2)
    gst_row3 = [""] * 18
    gst_row3[10] = "Net Owing"
    gst_row3[11] = "=L28-L29"
    d.append(gst_row3)

    # ═══════════════════════════════════════════
    # TRANSACTIONS — Header rows then data
    # ═══════════════════════════════════════════
    t = [
        # Row 1: Title
        [f"Transactions  ·  {YEAR}", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        # Row 2: Subtitle
        ["All bank transactions — chequing + business account", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        # Row 3: Summary row
        ["", "", "", "TOTALS:",
         f"=SUMPRODUCT((E4:E1000=TRUE)*(D4:D1000>0)*D4:D1000*({SF.replace(TQ+'!', '')}))",
         "revenue",
         f"=SUMPRODUCT((E4:E1000=TRUE)*(D4:D1000<0)*ABS(D4:D1000)*({SF.replace(TQ+'!', '')}))",
         "expenses",
         f"=SUMPRODUCT((E4:E1000=TRUE)*ABS(H4:H1000))", "total GST",
         "", "", "", ""],
        # Row 4: Headers (frozen)
        ["Date", "Vendor", "Description", "Amount", "Business", "Category", "Split %", "GST", "Receipt", "Payment", "Account", "Notes", "Month", ""],
    ]
    # Data rows starting at row 5 (index 4)
    for row in txn_rows:
        # Add Month helper formula as col M (index 12)
        r_idx = len(t) + 1  # 1-indexed sheet row
        month_formula = f'=IF(A{r_idx}="",0,IFERROR(MONTH(A{r_idx}),IFERROR(VALUE(LEFT(A{r_idx},FIND("/",A{r_idx})-1)),0)))'
        t.append(row + [month_formula, ""])

    # ═══════════════════════════════════════════
    # BUSINESS SUMMARY — formulas ref Transactions
    # ═══════════════════════════════════════════
    b = [["Category", "CRA Line", "YTD"] + MONTHS + ["", "Trend"]]
    for cat in BIZ_CATS:
        r = len(b) + 1
        row = [cat, T2125.get(cat, ""), f"=SUM(D{r}:O{r})"]
        for mn in range(1, 13):
            row.append(f'=SUMPRODUCT(({TQ}!E$4:E$1000=TRUE)*({TQ}!D$4:D$1000<0)*({TQ}!F$4:F$1000="{cat}")*({MH}={mn})*ABS({TQ}!D$4:D$1000)*({SF}))')
        row += ["", f'=SPARKLINE(D{r}:O{r},{{"charttype","line";"linewidth",2;"color","#E6881E"}})']
        b.append(row)
    b.append([""] * 17)
    b.append(["TOTAL", "", f"=SUM(C2:C16)"] + [f"=SUM({chr(68+i)}2:{chr(68+i)}16)" for i in range(12)] + ["", ""])

    # ═══════════════════════════════════════════
    # PERSONAL SUMMARY
    # ═══════════════════════════════════════════
    p = [["Category", "YTD"] + MONTHS + ["", "Trend"]]
    for cat in PERS_CATS:
        r = len(p) + 1
        row = [cat, f"=SUM(C{r}:N{r})"]
        for mn in range(1, 13):
            row.append(f'=SUMPRODUCT(({TQ}!E$4:E$1000=FALSE)*({TQ}!D$4:D$1000<0)*({TQ}!F$4:F$1000="{cat}")*({MH}={mn})*ABS({TQ}!D$4:D$1000))')
        row += ["", f'=SPARKLINE(C{r}:N{r},{{"charttype","line";"linewidth",2;"color","#7C51CD"}})']
        p.append(row)
    p.append([""] * 16)
    p.append(["TOTAL", f"=SUM(B2:B13)"] + [f"=SUM({chr(67+i)}2:{chr(67+i)}13)" for i in range(12)] + ["",""])

    # ═══════════════════════════════════════════
    # P&L
    # ═══════════════════════════════════════════
    pl = [["Month", "Revenue", "Expenses", "Profit", "Margin", "Cumul Rev", "Cumul Profit", "vs Target", "", "Trend"]]
    for i, m in enumerate(MONTHS):
        mn = i + 1; r = i + 2
        pl.append([m,
            f"=SUMPRODUCT(({TQ}!E$4:E$1000=TRUE)*({TQ}!D$4:D$1000>0)*({MH}={mn})*{TQ}!D$4:D$1000*({SF}))",
            f"=SUMPRODUCT(({TQ}!E$4:E$1000=TRUE)*({TQ}!D$4:D$1000<0)*({MH}={mn})*ABS({TQ}!D$4:D$1000)*({SF}))",
            f"=B{r}-C{r}", f"=IF(B{r}>0,D{r}/B{r},0)",
            f"=SUM(B$2:B{r})", f"=SUM(D$2:D{r})",
            f"=F{r}-({105237}/12*{mn})", "",
            "" if i > 0 else f'=SPARKLINE({{D2,D3,D4,D5,D6,D7,D8,D9,D10,D11,D12,D13}},{{"charttype","line";"linewidth",2;"color","#1E9F6C"}})'])
    pl.append([""]* 10)
    pl.append(["TOTAL","=SUM(B2:B13)","=SUM(C2:C13)","=SUM(D2:D13)","=IF(B15>0,D15/B15,0)","","","","",""])

    # ═══════════════════════════════════════════
    # GST
    # ═══════════════════════════════════════════
    g = [
        [""] * 8,
        ["", "GST / HST Tracker", "", "", "", "", "", ""],
        ["", f"5% GST  ·  Quarterly Filing  ·  {YEAR}", "", "", "", "", "", ""],
        [""] * 8,
        ["", "", "Q1 (Jan–Mar)", "Q2 (Apr–Jun)", "Q3 (Jul–Sep)", "Q4 (Oct–Dec)", "YTD", ""],
    ]
    for label, op in [("GST Collected", ">"), ("ITCs (GST Paid)", "<")]:
        row = ["", label]
        for q_start, q_end in [(1,3),(4,6),(7,9),(10,12)]:
            row.append(f"=SUMPRODUCT(({TQ}!E$4:E$1000=TRUE)*({TQ}!D$4:D$1000{op}0)*(({MH}>={q_start})*({MH}<={q_end}))*{TQ}!H$4:H$1000)")
        row += [f"=SUM(C{len(g)+1}:F{len(g)+1})", ""]
        g.append(row)
    g.append([""] * 8)
    g.append(["", "NET OWING", f"=C6-C7", f"=D6-D7", f"=E6-E7", f"=F6-F7", f"=SUM(C9:F9)", ""])
    g.append([""] * 8)
    g.append(["", "Due Date", "Apr 30", "Jul 31", "Oct 31", "Jan 31", "", ""])
    g.append(["", "Filed?", False, False, False, False, "", ""])
    g.append(["", "Payment Date", "", "", "", "", "", ""])

    # ═══════════════════════════════════════════
    # EQUIPMENT
    # ═══════════════════════════════════════════
    eq = [["Asset", "Acquired", "CCA Class", "Rate", "Cost", "UCC Start", "CCA Claimed", "UCC End", "Notes", "", "", "Common Classes"]]
    classes_ref = [("Class 8","20%","Camera, lenses, lighting"),("Class 10","30%","Vehicle"),("Class 12","100%","Tools <$500"),("Class 50","55%","Computers")]
    for i in range(30):
        r = i+2
        row = ["","","","","","",f"=IF(F{r}>0,F{r}*D{r},\"\")",f"=IF(F{r}>0,F{r}-G{r},\"\")", "","","",""]
        if i < len(classes_ref):
            row[11] = f"{classes_ref[i][0]} — {classes_ref[i][1]} — {classes_ref[i][2]}"
        eq.append(row)
    eq.append([""]*12)
    eq.append(["TOTALS","","","",f"=SUM(E2:E31)",f"=SUM(F2:F31)",f"=SUM(G2:G31)",f"=SUM(H2:H31)","","","",""])

    # ═══════════════════════════════════════════
    # TAX SUMMARY
    # ═══════════════════════════════════════════
    tx = [
        [""] * 6,
        ["", f"Tax Summary  ·  {YEAR}", "", "", "", ""],
        ["", "Sole Proprietor  ·  BC, Canada", "", "", "", ""],
        [""] * 6,
        ["", "T2125 INCOME", "", "CRA Line", "", ""],
        [""] * 6,
        ["", "Gross Business Income", f"=SUMPRODUCT(({TQ}!E4:E1000=TRUE)*({TQ}!D4:D1000>0)*{TQ}!D4:D1000*({SF}))", "8299", "", ""],
        [""] * 6,
        ["", "EXPENSES", "", "", "", ""],
    ]
    expenses = [
        ("Advertising", "='Business'!C2", "8521"),
        ("Professional Fees", "='Business'!C3", "8590"),
        ("Vehicle", "='Business'!C4", "8615"),
        ("Insurance", "='Business'!C5", "8690"),
        ("Interest & Bank", "='Business'!C6", "8710"),
        ("Office Supplies", "='Business'!C7", "8811"),
        ("Rent / Co-working", "='Business'!C8", "8860"),
        ("Software & Subs", "='Business'!C9", "8871"),
        ("Travel", "='Business'!C10", "8910"),
        ("Phone & Internet", "='Business'!C11", "8945"),
        ("Subcontractors", "='Business'!C12", "9060"),
        ("Meals (50%)", "='Business'!C13*0.5", "9270"),
        ("Home Office", "='Business'!C14", "9281"),
        ("CCA", "='Equipment'!G33", "9936"),
        ("Other", "='Business'!C16", "—"),
    ]
    for name, formula, line in expenses:
        tx.append(["", name, formula, line, "", ""])
    tx.append([""] * 6)
    tx.append(["", "Total Expenses", "=SUM(C10:C24)", "9369", "", ""])
    tx.append([""] * 6)
    tx.append(["", "NET INCOME", "=C7-C26", "9946", "", ""])
    tx.append([""] * 6)
    tx.append(["", "TAX ESTIMATE", "", "", "", ""])
    tx.append([""] * 6)
    # 2025 federal brackets
    tx.append(["", "Federal Tax", "=IF(C28<=57375,C28*0.15,57375*0.15+(C28-57375)*0.205)", "", "", ""])
    tx.append(["", "Personal Credit", -2506, "", "", ""])
    tx.append(["", "Federal Net", "=MAX(0,C32+C33)", "", "", ""])
    tx.append([""] * 6)
    tx.append(["", "BC Provincial", "=IF(C28<=47937,C28*0.0506,47937*0.0506+(C28-47937)*0.077)", "", "", ""])
    tx.append(["", "BC Credit", -596, "", "", ""])
    tx.append(["", "BC Net", "=MAX(0,C36+C37)", "", "", ""])
    tx.append([""] * 6)
    tx.append(["", "Total Income Tax", "=C34+C38", "", "", ""])
    tx.append([""] * 6)
    tx.append(["", "CPP Self-Employed", "=IF(C28>3500,MIN((C28-3500)*0.119,7735.50),0)", "", "", ""])
    tx.append(["", "CPP2", "=IF(C28>73200,MIN((C28-73200)*0.08,396),0)", "", "", ""])
    tx.append(["", "Total CPP", "=C42+C43", "", "", ""])
    tx.append([""] * 6)
    tx.append(["", "TOTAL TAX + CPP", "=C40+C44", "", "", ""])
    tx.append(["", "Quarterly Installment", "=C45/4", "", "", ""])
    tx.append([""] * 6)
    tx.append(["", "RRSP Room (18%)", "=MIN(C28*0.18,32490)", "", "", ""])
    tx.append(["", "RRSP Contributions", "", "enter actual", "", ""])
    tx.append(["", "RRSP Tax Savings", "=C50*0.30", "~30% marginal", "", ""])

    # ═══════════════════════════════════════════
    # WRITE ALL DATA
    # ═══════════════════════════════════════════
    updates = [
        {"range": f"Dashboard!A1:R{len(d)}", "values": d},
        {"range": f"Transactions!A1:N{len(t)}", "values": t},
        {"range": f"Business!A1:Q{len(b)}", "values": b},
        {"range": f"Personal!A1:P{len(p)}", "values": p},
        {"range": f"'P&L'!A1:J{len(pl)}", "values": pl},
        {"range": f"GST!A1:H{len(g)}", "values": g},
        {"range": f"Tax!A1:F{len(tx)}", "values": tx},
        {"range": f"Equipment!A1:L{len(eq)}", "values": eq},
    ]
    svc.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet_id, body={"valueInputOption": "USER_ENTERED", "data": updates}
    ).execute()
    print(f"Data written — {len(txn_rows)} transactions loaded.")

    # ═══════════════════════════════════════════
    # FORMATTING
    # ═══════════════════════════════════════════
    R = []

    # ── DASHBOARD ──
    R.append(merge(0,1,2,2,8))
    R.append(f_(0,1,2,2,8, bold=True, size=22, fg=C["navy"]))
    R.append(f_(0,2,3,2,8, size=11, fg=C["t3"]))

    # KPI cards
    kpis = [(2,4,"blue"),(6,8,"red"),(10,12,"green"),(14,16,"orange")]
    for c1, c2, color in kpis:
        for row in range(4, 9):
            R.append(f_(0, row, row+1, c1, c2, bg=C["white"]))
        R.append(f_(0, 4, 5, c1, c2, bold=True, size=9, fg=C["t3"], bg=C["white"]))
        R.append(f_(0, 5, 6, c1, c2, bold=True, size=24, fg=C[color], bg=C["white"]))
        R.append(border_top(0, 4, c1, c2, C[color]))
        R.append(border_all(0, 4, 8, c1, c2, C["border_l"]))

    R.append(f_(0, 7, 8, 2, 18, size=9, fg=C["t3"]))
    R.append(f_(0, 10, 11, 2, 9, bold=True, size=14, fg=C["navy"]))
    R.append(f_(0, 10, 11, 10, 16, bold=True, size=14, fg=C["navy"]))
    R.append(f_(0, 11, 12, 2, 9, bold=True, size=9, fg=C["t3"], bg=C["white"]))
    R.append(f_(0, 11, 12, 10, 16, bold=True, size=9, fg=C["t3"], bg=C["white"]))
    # Monthly data rows
    for i in range(12):
        row = 12 + i
        bg = C["white"] if i % 2 == 0 else C["bg"]
        R.append(f_(0, row+1, row+2, 2, 9, size=10, fg=C["t1"], bg=bg))
        R.append(f_(0, row+1, row+2, 10, 16, size=10, fg=C["t1"], bg=bg))
    R.append(f_(0, 25, 26, 2, 9, bold=True, size=11, fg=C["blue"], bg=C["blue_bg"]))

    # GST summary section
    R.append(f_(0, 27, 28, 2, 9, bold=True, size=14, fg=C["navy"]))
    for i in range(3):
        R.append(f_(0, 28+i, 29+i, 10, 14, size=10, fg=C["t1"], bg=C["white"]))
    R.append(f_(0, 30, 31, 10, 14, bold=True, fg=C["red"], bg=C["red_bg"]))

    # Dashboard number formats
    R.append(nf(0, 5, 6, 2, 4, "$#,##0"))
    R.append(nf(0, 5, 6, 6, 8, "$#,##0"))
    R.append(nf(0, 5, 6, 10, 12, "$#,##0"))
    R.append(nf(0, 5, 6, 14, 16, "$#,##0"))
    R.append(nf(0, 13, 26, 3, 6, "$#,##0"))
    R.append(nf(0, 13, 26, 6, 7, "0.0%"))
    R.append(nf(0, 13, 26, 11, 12, "$#,##0"))
    R.append(nf(0, 13, 26, 12, 13, "0.0%"))
    R.append(nf(0, 7, 8, 3, 4, "0.0%"))
    R.append(nf(0, 7, 8, 11, 12, "0.0%"))
    R.append(nf(0, 28, 31, 11, 12, "$#,##0.00"))

    dw = [10,10,140,110,110,90,140,110,110,20,140,110,80,10,10,10,10,10]
    for i, w in enumerate(dw):
        R.append(cw(0, i, w))

    # ── TRANSACTIONS ──
    # Title rows
    R.append(f_(1, 0, 1, 0, 14, bold=True, size=16, fg=C["navy"]))
    R.append(f_(1, 1, 2, 0, 14, size=10, fg=C["t3"]))
    # Summary row
    R.append(f_(1, 2, 3, 0, 14, bold=True, size=9, fg=C["t2"], bg=C["blue_bg"]))
    # Header row
    R.append(f_(1, 3, 4, 0, 14, bold=True, size=9, fg=C["t3"], bg=C["white"]))
    R.append(rh(1, 3, 30))
    # Border under header
    R.append(border_bottom(1, 3, 0, 14, C["border"]))

    tw = [100, 170, 170, 100, 75, 180, 65, 85, 65, 90, 110, 170, 50, 10]
    for i, w in enumerate(tw):
        R.append(cw(1, i, w))
    # Alternating rows
    for r in range(4, len(t)):
        bg = C["white"] if r % 2 == 0 else C["bg"]
        R.append(f_(1, r, r+1, 0, 14, size=10, fg=C["t1"], bg=bg))
    R.append(nf(1, 4, 600, 3, 4, "$#,##0.00"))
    R.append(nf(1, 4, 600, 7, 8, "$#,##0.00"))
    # Hide Month column (M = index 12)
    R.append(hide_col(1, 12, 13))

    # ── BUSINESS ──
    R.append(f_(2, 0, 1, 0, 17, bold=True, size=9, fg=C["t3"], bg=C["white"]))
    R.append(rh(2, 0, 30))
    R.append(border_bottom(2, 0, 0, 17, C["border"]))
    for i in range(15):
        bg = C["white"] if i % 2 == 0 else C["bg"]
        R.append(f_(2, i+1, i+2, 0, 17, size=10, fg=C["t1"], bg=bg))
    R.append(f_(2, len(b)-1, len(b), 0, 17, bold=True, size=11, fg=C["orange"], bg=C["orange_bg"]))
    R.append(nf(2, 1, 20, 2, 16, "$#,##0"))
    bw = [200, 55, 85] + [70]*12 + [10, 110]
    for i, w in enumerate(bw):
        R.append(cw(2, i, w))

    # ── PERSONAL ──
    R.append(f_(3, 0, 1, 0, 16, bold=True, size=9, fg=C["t3"], bg=C["white"]))
    R.append(border_bottom(3, 0, 0, 16, C["border"]))
    for i in range(12):
        bg = C["white"] if i % 2 == 0 else C["bg"]
        R.append(f_(3, i+1, i+2, 0, 16, size=10, fg=C["t1"], bg=bg))
    R.append(f_(3, len(p)-1, len(p), 0, 16, bold=True, size=11, fg=C["purple"], bg=C["purple_bg"]))
    R.append(nf(3, 1, 16, 1, 15, "$#,##0"))
    pw = [160, 85] + [70]*12 + [10, 110]
    for i, w in enumerate(pw):
        R.append(cw(3, i, w))

    # ── P&L ──
    R.append(f_(4, 0, 1, 0, 10, bold=True, size=9, fg=C["t3"], bg=C["white"]))
    R.append(border_bottom(4, 0, 0, 10, C["border"]))
    for i in range(12):
        bg = C["white"] if i % 2 == 0 else C["bg"]
        R.append(f_(4, i+1, i+2, 0, 10, size=10, fg=C["t1"], bg=bg))
    R.append(f_(4, 14, 15, 0, 10, bold=True, size=11, fg=C["blue"], bg=C["blue_bg"]))
    R.append(nf(4, 1, 16, 1, 4, "$#,##0"))
    R.append(nf(4, 1, 16, 5, 8, "$#,##0"))
    R.append(nf(4, 1, 16, 4, 5, "0.0%"))

    # ── GST ──
    R.append(f_(5, 1, 2, 1, 7, bold=True, size=18, fg=C["navy"]))
    R.append(f_(5, 2, 3, 1, 7, size=10, fg=C["t3"]))
    R.append(f_(5, 4, 5, 1, 7, bold=True, size=9, fg=C["t3"], bg=C["white"]))
    R.append(f_(5, 5, 6, 1, 7, size=11, fg=C["green"], bg=C["white"]))
    R.append(f_(5, 6, 7, 1, 7, size=11, fg=C["red"], bg=C["white"]))
    R.append(f_(5, 8, 9, 1, 7, bold=True, size=12, fg=C["red"], bg=C["red_bg"]))
    R.append(nf(5, 5, 10, 2, 7, "$#,##0.00"))

    # ── EQUIPMENT ──
    R.append(f_(6, 0, 1, 0, 12, bold=True, size=9, fg=C["t3"], bg=C["white"]))
    R.append(border_bottom(6, 0, 0, 12, C["border"]))
    for i in range(30):
        bg = C["white"] if i % 2 == 0 else C["bg"]
        R.append(f_(6, i+1, i+2, 0, 12, size=10, fg=C["t1"], bg=bg))
    R.append(f_(6, 32, 33, 0, 12, bold=True, size=11, fg=C["green"], bg=C["green_bg"]))
    R.append(nf(6, 1, 33, 4, 8, "$#,##0.00"))

    # ── TAX ──
    R.append(f_(7, 1, 2, 1, 4, bold=True, size=18, fg=C["navy"]))
    R.append(f_(7, 2, 3, 1, 4, size=10, fg=C["t3"]))
    R.append(f_(7, 4, 5, 1, 4, bold=True, size=11, fg=C["blue"]))
    R.append(f_(7, 6, 7, 1, 4, bold=True, size=14, fg=C["green"], bg=C["green_bg"]))
    R.append(f_(7, 8, 9, 1, 4, bold=True, size=10, fg=C["t2"]))
    for r in range(9, 25):
        bg = C["white"] if r % 2 == 0 else C["bg"]
        R.append(f_(7, r, r+1, 1, 4, size=10, fg=C["t2"], bg=bg))
    R.append(f_(7, 25, 26, 1, 4, bold=True, fg=C["orange"], bg=C["orange_bg"]))
    R.append(f_(7, 27, 28, 1, 4, bold=True, size=14, fg=C["green"], bg=C["green_bg"]))
    R.append(f_(7, 39, 40, 1, 4, bold=True, fg=C["t1"], bg=C["white"]))
    R.append(f_(7, 44, 45, 1, 4, bold=True, size=14, fg=C["red"], bg=C["red_bg"]))
    R.append(f_(7, 45, 46, 1, 4, bold=True, size=11, fg=C["orange"], bg=C["orange_bg"]))
    R.append(nf(7, 6, 51, 2, 3, "$#,##0.00"))
    txw = [15, 180, 120, 80, 10, 10]
    for i, w in enumerate(txw):
        R.append(cw(7, i, w))

    # ═══════════════════════════════════════════
    # DATA VALIDATION
    # ═══════════════════════════════════════════
    R.append(dv_bool(1, 4, 600, 4, 5))     # Business checkbox
    R.append(dv_bool(1, 4, 600, 8, 9))     # Receipt checkbox
    R.append(dv_list(1, 4, 600, 5, 6, ALL_CATS))
    R.append(dv_list(1, 4, 600, 6, 7, ["100%","75%","50%","25%","0%"]))
    R.append(dv_list(1, 4, 600, 9, 10, ["Visa","Debit","E-Transfer","Cash","Cheque","PayPal"]))
    R.append(dv_list(1, 4, 600, 10, 11, ["Chequing","Business Account","Personal Card","Cash"]))
    R.append(dv_bool(5, 11, 12, 2, 6))     # GST Filed checkboxes

    # ═══════════════════════════════════════════
    # CONDITIONAL FORMATTING
    # ═══════════════════════════════════════════
    # Business rows get soft blue bg
    R.append(cf(1, 4, 600, 0, 14, "=$E5=TRUE", C["blue_l"]))
    # Negative amounts red text
    R.append(cf_text(1, 4, 600, 3, 4, "=$D5<0", C["red"]))
    # Positive amounts green text
    R.append(cf_text(1, 4, 600, 3, 4, "=$D5>0", C["green"]))
    # Missing receipt on business = soft red
    R.append(cf(1, 4, 600, 8, 9, "=AND($E5=TRUE,$I5=FALSE,$D5<>\"\",$D5<>0)", C["red_bg"]))
    # P&L profit coloring
    R.append(cf_text(4, 1, 14, 3, 4, "=$D2<0", C["red"]))
    R.append(cf_text(4, 1, 14, 3, 4, "=$D2>0", C["green"]))

    # ═══════════════════════════════════════════
    # CHARTS on P&L
    # ═══════════════════════════════════════════
    R.append({"addChart": {"chart": {
        "spec": {
            "title": "Revenue vs Expenses",
            "titleTextFormat": {"foregroundColorStyle": {"rgbColor": C["t2"]}, "fontSize": 11, "bold": True, "fontFamily": "Inter"},
            "backgroundColor": C["white"],
            "basicChart": {
                "chartType": "COLUMN", "legendPosition": "BOTTOM_LEGEND",
                "axis": [
                    {"position": "BOTTOM_AXIS", "format": {"foregroundColorStyle": {"rgbColor": C["t3"]}, "fontFamily": "Inter", "fontSize": 9}},
                    {"position": "LEFT_AXIS", "format": {"foregroundColorStyle": {"rgbColor": C["t3"]}, "fontFamily": "Inter", "fontSize": 9}},
                ],
                "domains": [{"domain": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 0, "endColumnIndex": 1}]}}}],
                "series": [
                    {"series": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 1, "endColumnIndex": 2}]}}, "color": C["blue"]},
                    {"series": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 2, "endColumnIndex": 3}]}}, "color": C["red"]},
                ],
                "headerCount": 1,
            }
        },
        "position": {"overlayPosition": {"anchorCell": {"sheetId": 4, "rowIndex": 16, "columnIndex": 0}, "widthPixels": 620, "heightPixels": 340}}
    }}})

    R.append({"addChart": {"chart": {
        "spec": {
            "title": "Cumulative Revenue & Profit",
            "titleTextFormat": {"foregroundColorStyle": {"rgbColor": C["t2"]}, "fontSize": 11, "bold": True, "fontFamily": "Inter"},
            "backgroundColor": C["white"],
            "basicChart": {
                "chartType": "LINE", "legendPosition": "BOTTOM_LEGEND",
                "axis": [
                    {"position": "BOTTOM_AXIS", "format": {"foregroundColorStyle": {"rgbColor": C["t3"]}, "fontFamily": "Inter"}},
                    {"position": "LEFT_AXIS", "format": {"foregroundColorStyle": {"rgbColor": C["t3"]}, "fontFamily": "Inter"}},
                ],
                "domains": [{"domain": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 0, "endColumnIndex": 1}]}}}],
                "series": [
                    {"series": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 5, "endColumnIndex": 6}]}}, "color": C["blue"]},
                    {"series": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 6, "endColumnIndex": 7}]}}, "color": C["green"]},
                ],
                "headerCount": 1,
            }
        },
        "position": {"overlayPosition": {"anchorCell": {"sheetId": 4, "rowIndex": 16, "columnIndex": 6}, "widthPixels": 520, "heightPixels": 340}}
    }}})

    # Execute all formatting
    svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": R}).execute()
    print("Formatting applied.")

    # ── Save sheet ID to .env ──
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            content = f.read()
        if "FINANCE_SHEET_2025_ID" in content:
            content = re.sub(r"FINANCE_SHEET_2025_ID=.*", f"FINANCE_SHEET_2025_ID={sheet_id}", content)
        else:
            content = content.rstrip() + f"\nFINANCE_SHEET_2025_ID={sheet_id}\n"
        with open(env_path, "w") as f:
            f.write(content)
    print(f"Sheet ID saved to .env as FINANCE_SHEET_2025_ID={sheet_id}")

    print(f"\n{'='*60}")
    print(f"DONE: {url}")
    print(f"{'='*60}")
    return sheet_id, url


# ═══════════════════════════════════════════
# HELPERS (same as v4)
# ═══════════════════════════════════════════
def cw(s, c, w):
    return {"updateDimensionProperties": {"range": {"sheetId": s, "dimension": "COLUMNS", "startIndex": c, "endIndex": c+1}, "properties": {"pixelSize": w}, "fields": "pixelSize"}}

def rh(s, r, h):
    return {"updateDimensionProperties": {"range": {"sheetId": s, "dimension": "ROWS", "startIndex": r, "endIndex": r+1}, "properties": {"pixelSize": h}, "fields": "pixelSize"}}

def f_(s, r1, r2, c1, c2, bold=False, size=10, fg=None, bg=None):
    cell = {"textFormat": {"bold": bold, "fontSize": size, "fontFamily": "Inter"}}
    if fg: cell["textFormat"]["foregroundColorStyle"] = {"rgbColor": fg}
    if bg: cell["backgroundColor"] = bg
    return {"repeatCell": {"range": {"sheetId": s, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}, "cell": {"userEnteredFormat": cell}, "fields": "userEnteredFormat(textFormat,backgroundColor)"}}

def nf(s, r1, r2, c1, c2, pat):
    return {"repeatCell": {"range": {"sheetId": s, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}, "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": pat}}}, "fields": "userEnteredFormat.numberFormat"}}

def merge(s, r1, r2, c1, c2):
    return {"mergeCells": {"range": {"sheetId": s, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}, "mergeType": "MERGE_ALL"}}

def border_top(s, r, c1, c2, color):
    return {"updateBorders": {"range": {"sheetId": s, "startRowIndex": r, "endRowIndex": r+1, "startColumnIndex": c1, "endColumnIndex": c2}, "top": {"style": "SOLID_MEDIUM", "colorStyle": {"rgbColor": color}}}}

def border_bottom(s, r, c1, c2, color):
    return {"updateBorders": {"range": {"sheetId": s, "startRowIndex": r, "endRowIndex": r+1, "startColumnIndex": c1, "endColumnIndex": c2}, "bottom": {"style": "SOLID", "colorStyle": {"rgbColor": color}}}}

def border_all(s, r1, r2, c1, c2, color):
    bdr = {"style": "SOLID", "colorStyle": {"rgbColor": color}}
    return {"updateBorders": {"range": {"sheetId": s, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}, "top": bdr, "bottom": bdr, "left": bdr, "right": bdr}}

def hide_col(s, c1, c2):
    return {"updateDimensionProperties": {"range": {"sheetId": s, "dimension": "COLUMNS", "startIndex": c1, "endIndex": c2}, "properties": {"hiddenByUser": True}, "fields": "hiddenByUser"}}

def dv_bool(s, r1, r2, c1, c2):
    return {"setDataValidation": {"range": {"sheetId": s, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}, "rule": {"condition": {"type": "BOOLEAN"}, "strict": True}}}

def dv_list(s, r1, r2, c1, c2, vals):
    return {"setDataValidation": {"range": {"sheetId": s, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}, "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in vals]}, "showCustomUi": True, "strict": False}}}

def cf(s, r1, r2, c1, c2, formula, bg):
    return {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": s, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": formula}]}, "format": {"backgroundColor": bg}}}, "index": 0}}

def cf_text(s, r1, r2, c1, c2, formula, fg):
    return {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": s, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": formula}]}, "format": {"textFormat": {"foregroundColorStyle": {"rgbColor": fg}}}}}, "index": 0}}


if __name__ == "__main__":
    create()
