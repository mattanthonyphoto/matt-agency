"""
Matt Anthony Photography — Finance Tracker v4
Clean light theme. Premium minimal design.
"""
import sys, os, csv, re
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.google_sheets_auth import get_sheets_service, get_drive_service

YEAR = 2026

# ═══════════════════════════════════════════
# DESIGN TOKENS — Light, clean, minimal
# ═══════════════════════════════════════════
C = {
    "white":    {"red": 1.0, "green": 1.0, "blue": 1.0},
    "bg":       {"red": 0.976, "green": 0.980, "blue": 0.984},   # #F9FAFB soft gray bg
    "card":     {"red": 1.0, "green": 1.0, "blue": 1.0},         # #FFFFFF cards
    "row_alt":  {"red": 0.969, "green": 0.973, "blue": 0.980},   # #F7F8FA subtle alt
    "border":   {"red": 0.906, "green": 0.914, "blue": 0.929},   # #E7E9ED
    "border_l": {"red": 0.937, "green": 0.941, "blue": 0.949},   # #EFF0F2 lighter border
    "input":    {"red": 0.957, "green": 0.961, "blue": 0.969},   # #F4F5F7 input bg
    # Text
    "t1":       {"red": 0.098, "green": 0.114, "blue": 0.149},   # #191D26 primary
    "t2":       {"red": 0.357, "green": 0.380, "blue": 0.427},   # #5B616D secondary
    "t3":       {"red": 0.549, "green": 0.573, "blue": 0.612},   # #8C929C muted
    "t4":       {"red": 0.702, "green": 0.718, "blue": 0.745},   # #B3B7BE disabled
    # Accents
    "blue":     {"red": 0.224, "green": 0.443, "blue": 0.871},   # #3971DE
    "blue_bg":  {"red": 0.922, "green": 0.941, "blue": 0.988},   # #EBF0FC
    "blue_l":   {"red": 0.957, "green": 0.969, "blue": 0.996},   # #F4F7FE
    "green":    {"red": 0.118, "green": 0.624, "blue": 0.424},   # #1E9F6C
    "green_bg": {"red": 0.906, "green": 0.969, "blue": 0.941},   # #E7F7F0
    "green_l":  {"red": 0.949, "green": 0.984, "blue": 0.969},   # #F2FBF7
    "red":      {"red": 0.851, "green": 0.200, "blue": 0.200},   # #D93333
    "red_bg":   {"red": 0.992, "green": 0.929, "blue": 0.929},   # #FDED ED
    "red_l":    {"red": 0.996, "green": 0.957, "blue": 0.957},   # #FEF4F4
    "orange":   {"red": 0.902, "green": 0.533, "blue": 0.118},   # #E6881E
    "orange_bg":{"red": 0.996, "green": 0.953, "blue": 0.906},   # #FEF3E7
    "purple":   {"red": 0.486, "green": 0.318, "blue": 0.804},   # #7C51CD
    "purple_bg":{"red": 0.949, "green": 0.933, "blue": 0.988},   # #F2EEFC
    "cyan":     {"red": 0.059, "green": 0.588, "blue": 0.682},   # #0F96AE
    "cyan_bg":  {"red": 0.906, "green": 0.969, "blue": 0.980},   # #E7F7FA
    "navy":     {"red": 0.153, "green": 0.173, "blue": 0.224},   # #272C39
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

# ── Transaction categorization ──
RULES = [
    (r"GOOGLE\*WORKSPACE|GOOGLE \*Workspace", True, "Software & Subscriptions", "Google Workspace", 100),
    (r"Adobe Inc", True, "Software & Subscriptions", "Adobe Creative Cloud", 100),
    (r"INSTANTLY", True, "Software & Subscriptions", "Instantly (Cold Email)", 100),
    (r"BUFFER PLAN", True, "Software & Subscriptions", "Buffer (Social Media)", 100),
    (r"OPENROUTER", True, "Software & Subscriptions", "OpenRouter (AI)", 100),
    (r"LEADGENJAY", True, "Software & Subscriptions", "LeadGenJay", 100),
    (r"APIFY", True, "Software & Subscriptions", "Apify (Scraping)", 100),
    (r"CLICKUP", True, "Software & Subscriptions", "ClickUp", 100),
    (r"EpidemicSound", True, "Software & Subscriptions", "Epidemic Sound", 100),
    (r"Dropbox", True, "Software & Subscriptions", "Dropbox", 100),
    (r"INTUIT.*QBooks", True, "Software & Subscriptions", "QuickBooks", 100),
    (r"HIGHLEVEL", True, "Software & Subscriptions", "GoHighLevel (CRM)", 100),
    (r"ICYPEAS", True, "Software & Subscriptions", "IcyPeas (Email Verify)", 100),
    (r"OPENAI.*CHATGPT", True, "Software & Subscriptions", "ChatGPT Plus", 100),
    (r"Audible", True, "Software & Subscriptions", "Audible (Prof Dev)", 100),
    (r"EXPRESSVPN", True, "Software & Subscriptions", "ExpressVPN", 100),
    (r"SHOWPASS", True, "Advertising & Marketing", "Event / Networking", 100),
    (r"OUTPOST LANKA", True, "Rent / Co-working", "Outpost Lanka", 100),
    (r"AIRALO", True, "Travel", "Airalo eSIM", 50),
    (r"ONWARD TICKET", True, "Travel", "Onward Ticket", 50),
    (r"CATHAYPACAIR", True, "Travel", "Cathay Pacific Flight", 50),
    (r"AIR ASIA", True, "Travel", "AirAsia Flight", 50),
    (r"DEPARTMENT OF IMMIGRATION|DEPT OF IMMIGRATION", True, "Travel", "Visa Fee", 50),
    (r"A4 RESIDENCE COLOMBO", True, "Travel", "Accommodation (Sri Lanka)", 50),
    (r"Clear Point Wild Forest", True, "Travel", "Accommodation (Sri Lanka)", 50),
    (r"XDT\*MEGATIX", True, "Travel", "Event (Bali)", 50),
    # Personal
    (r"BACKCOUNTRY BREWING", False, "Dining Out", "Backcountry Brewing", 0),
    (r"IL MUNDO", False, "Dining Out", "Il Mundo", 0),
    (r"PUREBREAD", False, "Dining Out", "Purebread Bakery", 0),
    (r"DOMINOS", False, "Dining Out", "Domino's Pizza", 0),
    (r"RAMEN BUTCHER", False, "Dining Out", "Ramen Butcher", 0),
    (r"Buddha 2", False, "Dining Out", "Buddha 2", 0),
    (r"CRABAPPLE CAFE", False, "Dining Out", "Crabapple Cafe", 0),
    (r"STARBUCKS", False, "Dining Out", "Starbucks", 0),
    (r"SUBWAY", False, "Dining Out", "Subway", 0),
    (r"BARBURRITO", False, "Dining Out", "Barburrito", 0),
    (r"BAKED BATU", False, "Dining Out", "Baked (Bali)", 0),
    (r"ZIN CAFE", False, "Dining Out", "Zin Cafe (Bali)", 0),
    (r"GAYA GELATO", False, "Dining Out", "Gaya Gelato (Bali)", 0),
    (r"SOOGI ROLL", False, "Dining Out", "Soogi Roll (Bali)", 0),
    (r"AVOCADO FACTORY", False, "Dining Out", "Avocado Factory (Bali)", 0),
    (r"GOAT FATHER", False, "Dining Out", "Goat Father (Bali)", 0),
    (r"MOTION PERERENAN", False, "Dining Out", "Motion (Bali)", 0),
    (r"KAYUNAN WARUNG", False, "Dining Out", "Kayunan Warung (Bali)", 0),
    (r"RUSTERS", False, "Dining Out", "Rusters (Bali)", 0),
    (r"CLEAR CAFE", False, "Dining Out", "Clear Cafe (Bali)", 0),
    (r"GIGI SUSU", False, "Dining Out", "Gigi Susu (Bali)", 0),
    (r"REVOLVER INTER", False, "Dining Out", "Revolver (Bali)", 0),
    (r"ALCHEMY CANGGU", False, "Dining Out", "Alchemy (Bali)", 0),
    (r"AHH-YUM", False, "Dining Out", "Ahh-Yum (Malaysia)", 0),
    (r"PLAN B CAFE", False, "Dining Out", "Plan B (Sri Lanka)", 0),
    (r"STICK SURF CLUB", False, "Dining Out", "Stick Surf (Sri Lanka)", 0),
    (r"LAMANA", False, "Dining Out", "Lamana (Sri Lanka)", 0),
    (r"JAVA LOUNGE", False, "Dining Out", "Java Lounge (Sri Lanka)", 0),
    (r"AHANGAMA DAIRIES", False, "Dining Out", "Ahangama Dairies", 0),
    (r"ZIPPI PVT", False, "Dining Out", "Zippi (Sri Lanka)", 0),
    (r"TUGU BALI", False, "Dining Out", "Tugu Bali", 0),
    (r"H A C PERERA", False, "Dining Out", "H A C Perera (Sri Lanka)", 0),
    (r"DEVILLE COFFEE", False, "Dining Out", "Deville Coffee", 0),
    (r"COMPASS VENDING", False, "Dining Out", "Compass Vending", 0),
    (r"MOON THAI EXPRESS", False, "Dining Out", "Moon Thai (HK)", 0),
    (r"2410311_HKG.*Gordon", False, "Dining Out", "Gordon Ramsay (HK)", 0),
    (r"CHAI RESTAURANTS", False, "Dining Out", "Chai Restaurant", 0),
    (r"TRAFIQ CAFE", False, "Dining Out", "Trafiq Cafe", 0),
    (r"CONTINENTAL COFFEE", False, "Dining Out", "Continental Coffee", 0),
    (r"SUSHI SEN", False, "Dining Out", "Sushi Sen", 0),
    (r"Noodlebox", False, "Dining Out", "Noodlebox", 0),
    (r"ESSENCE OF INDIA", False, "Dining Out", "Essence of India", 0),
    (r"SEA TO SKY HOTEL", False, "Dining Out", "Sea to Sky Hotel", 0),
    (r"Brackendale Art Ga", False, "Dining Out", "Brackendale Art Gallery", 0),
    (r"FOX & OAK", False, "Dining Out", "Fox & Oak", 0),
    (r"CLOUDBURST CAFE", False, "Dining Out", "Cloudburst Cafe", 0),
    (r"SHEN HENG CHANG", False, "Dining Out", "Food (Taiwan)", 0),
    (r"WHSMITH", False, "Dining Out", "WHSmith (Bali)", 0),
    (r"HOME DEPOT", False, "Groceries", "Home Depot", 0),
    (r"HECTOR.S YOUR INDEPEND", False, "Groceries", "Hector's IGA", 0),
    (r"DOLLARAMA", False, "Groceries", "Dollarama", 0),
    (r"LONDON DRUGS", False, "Groceries", "London Drugs", 0),
    (r"SWAN MART", False, "Groceries", "Swan Mart (Bali)", 0),
    (r"NESTERS MARKET", False, "Groceries", "Nesters Market", 0),
    (r"CHV.*WESTMOUNT", False, "Groceries", "Cheese Shop", 0),
    (r"MARKS SQUAMISH", False, "Clothing", "Mark's", 0),
    (r"MOUNTAIN EQUIPMENT", False, "Clothing", "MEC", 0),
    (r"COASTAL CRYSTALS", False, "Clothing", "Coastal Crystals", 0),
    (r"Spotify", False, "Subscriptions", "Spotify", 0),
    (r"APPLE\.COM/BILL", False, "Subscriptions", "Apple Services", 0),
    (r"CLIMB GROUNDUP", False, "Health & Fitness", "Ground Up Climbing", 0),
    (r"BAMBU FITNESS", False, "Health & Fitness", "Bambu Fitness (Bali)", 0),
    (r"MISSION YOGA", False, "Health & Fitness", "Mission Yoga (Bali)", 0),
    (r"ALCHEMY YOGA", False, "Health & Fitness", "Alchemy Yoga (Bali)", 0),
    (r"SENSES YOGA", False, "Health & Fitness", "Senses Yoga (Sri Lanka)", 0),
    (r"UBER", False, "Transportation", "Uber", 0),
    (r"CITY OF VANCOUVER PARKING", False, "Transportation", "Parking", 0),
    (r"AIR-SERV", False, "Transportation", "Gas Station", 0),
    (r"SQUAMISHCONNECTOR", False, "Transportation", "Squamish Connector", 0),
]

def categorize(desc):
    for pattern, is_biz, cat, name, split in RULES:
        if re.search(pattern, desc, re.IGNORECASE):
            return is_biz, cat, name, split
    return False, "Other Personal", desc.split("  ")[0].strip()[:30], 0

def calc_gst(amt):
    return round(abs(amt) / 1.05 * 0.05, 2)

def parse_csv(path):
    """Parse bank CSV into transaction rows matching sheet columns:
    Date | Vendor | Description | Amount | Business? | Category | Split% | GST | Receipt? | Payment | Account | Notes
    """
    rows = []
    with open(path, "r") as f:
        for row in csv.DictReader(f):
            amt_str = row.get("CAD$", "").strip()
            if not amt_str: continue
            amount = float(amt_str)
            desc = f"{row.get('Description 1', '')} {row.get('Description 2', '')}".strip()
            date = row.get("Transaction Date", "").strip()
            if amount > 0 and "PAYMENT" in desc.upper(): continue

            is_biz, cat, name, split_pct = categorize(desc)
            gst = calc_gst(amount) if is_biz and amount < 0 else 0

            if split_pct == 50 and amount < 0:
                half = round(amount / 2, 2)
                gst_half = calc_gst(half)
                rows.append([date, name, f"50% business", half, True, cat, "50%", gst_half, False, "Visa", "Personal Card", "50/50 split"])
                pcat = "Travel (Personal)" if cat == "Travel" else "Entertainment"
                rows.append([date, name, f"50% personal", half, False, pcat, "0%", 0, False, "Visa", "Personal Card", "50/50 split"])
            else:
                rows.append([date, name, desc.split("  ")[0][:40], amount, is_biz, cat, "100%" if is_biz else "0%", gst, False, "Visa", "Personal Card", ""])

    rows.sort(key=lambda x: datetime.strptime(x[0], "%m/%d/%Y"))
    return rows


def create():
    svc = get_sheets_service()
    CSV = "/Users/matthewfernandes/Downloads/download-transactions.csv"

    # Parse transactions first so we know the data
    txn_rows = parse_csv(CSV)
    print(f"Parsed {len(txn_rows)} transactions")

    # ── Create spreadsheet ──
    tabs = [
        ("Dashboard", 0, 0, 22),
        ("Transactions", 1, 3, 14),
        ("Business", 2, 1, 18),
        ("Personal", 3, 1, 16),
        ("P&L", 4, 1, 12),
        ("GST", 5, 0, 10),
        ("Mileage", 6, 1, 12),
        ("Equipment", 7, 1, 14),
        ("Tax", 8, 0, 10),
    ]
    tab_colors = [C["blue"],C["green"],C["orange"],C["purple"],C["blue"],C["red"],C["t3"],C["green"],C["red"]]
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
    sid = sp["spreadsheetId"]
    url = sp["spreadsheetUrl"]
    print(f"Created: {url}")

    # ═══════════════════════════════════════════
    # DASHBOARD
    # ═══════════════════════════════════════════
    TQ = "Transactions"  # Tab ref for formulas
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
        # KPI values
        ["", "",
         f"=SUMPRODUCT(({TQ}!E4:E1000=TRUE)*({TQ}!D4:D1000>0)*{TQ}!D4:D1000)", "",
         "", "",
         f"=SUMPRODUCT(({TQ}!E4:E1000=TRUE)*({TQ}!D4:D1000<0)*ABS({TQ}!D4:D1000))", "",
         "", "",
         "=C6-G6", "",
         "", "",
         "='Tax'!B44", "",
         "", ""],
        [""] * 18,
        # Submetrics
        ["", "",
         "of $172,900 target", f"=IF(172900>0,C6/172900,0)",
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
        r = 13 + i
        row = [""] * 18
        row[2] = m
        row[3] = f"=SUMPRODUCT(({TQ}!E$4:E$1000=TRUE)*({TQ}!D$4:D$1000>0)*(MONTH(DATEVALUE({TQ}!A$4:A$1000))={mn})*{TQ}!D$4:D$1000)"
        row[4] = f"=SUMPRODUCT(({TQ}!E$4:E$1000=TRUE)*({TQ}!D$4:D$1000<0)*(MONTH(DATEVALUE({TQ}!A$4:A$1000))={mn})*ABS({TQ}!D$4:D$1000))"
        row[5] = f"=D{r}-E{r}"
        row[6] = f"=IF(D{r}>0,F{r}/D{r},0)"
        # Right side: spending categories
        cats_list = ["Software & Subscriptions", "Travel", "Rent / Co-working", "Telephone & Internet",
                     "Advertising & Marketing", "Dining Out", "Groceries", "Health & Fitness",
                     "Subscriptions", "Entertainment", "Transportation", "Clothing"]
        if i < len(cats_list):
            cat = cats_list[i]
            is_biz = cat in BIZ_CATS
            biz_flag = "TRUE" if is_biz else "FALSE"
            row[10] = cat
            row[11] = f"=SUMPRODUCT(({TQ}!E$4:E$1000={biz_flag})*({TQ}!D$4:D$1000<0)*({TQ}!F$4:F$1000=\"{cat}\")*ABS({TQ}!D$4:D$1000))"
            row[12] = f"=IF(C6>0,L{r}/C6,0)"
        d.append(row)

    # Total row
    tr = [""] * 18
    tr[2] = "Total"
    tr[3] = "=SUM(D13:D24)"
    tr[4] = "=SUM(E13:E24)"
    tr[5] = "=SUM(F13:F24)"
    tr[6] = "=IF(D25>0,F25/D25,0)"
    d.append(tr)

    d.append([""] * 18)
    # GST row
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
    gst_row3[11] = "=L27-L28"
    d.append(gst_row3)

    # ═══════════════════════════════════════════
    # TRANSACTIONS
    # ═══════════════════════════════════════════
    t = [
        ["Date", "Vendor", "Description", "Amount", "Business", "Category", "Split %", "GST", "Receipt", "Payment", "Account", "Notes", "", ""],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],  # spacer
        ["", "", "", "TOTALS:", f"=SUMPRODUCT((E4:E1000=TRUE)*(D4:D1000<0)*ABS(D4:D1000))", "business expenses", "", f"=SUMPRODUCT((E4:E1000=TRUE)*ABS(H4:H1000))", "total GST", "", "", "", "", ""],
    ]
    # Data rows
    for row in txn_rows:
        t.append(row)

    # ═══════════════════════════════════════════
    # BUSINESS SUMMARY
    # ═══════════════════════════════════════════
    b = [["Category", "CRA Line", "YTD"] + MONTHS + ["", "Trend"]]
    for cat in BIZ_CATS:
        r = len(b) + 1
        row = [cat, T2125.get(cat, ""), f"=SUM(D{r}:O{r})"]
        for mn in range(1, 13):
            row.append(f"=SUMPRODUCT(({TQ}!E$4:E$1000=TRUE)*({TQ}!D$4:D$1000<0)*({TQ}!F$4:F$1000=\"{cat}\")*(MONTH(DATEVALUE({TQ}!A$4:A$1000))={mn})*ABS({TQ}!D$4:D$1000))")
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
            row.append(f"=SUMPRODUCT(({TQ}!E$4:E$1000=FALSE)*({TQ}!D$4:D$1000<0)*({TQ}!F$4:F$1000=\"{cat}\")*(MONTH(DATEVALUE({TQ}!A$4:A$1000))={mn})*ABS({TQ}!D$4:D$1000))")
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
            f"=SUMPRODUCT(({TQ}!E$4:E$1000=TRUE)*({TQ}!D$4:D$1000>0)*(MONTH(DATEVALUE({TQ}!A$4:A$1000))={mn})*{TQ}!D$4:D$1000)",
            f"=SUMPRODUCT(({TQ}!E$4:E$1000=TRUE)*({TQ}!D$4:D$1000<0)*(MONTH(DATEVALUE({TQ}!A$4:A$1000))={mn})*ABS({TQ}!D$4:D$1000))",
            f"=B{r}-C{r}", f"=IF(B{r}>0,D{r}/B{r},0)",
            f"=SUM(B$2:B{r})", f"=SUM(D$2:D{r})",
            f"=F{r}-({172900}/12*{mn})", "",
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
    for label, op, sign in [("GST Collected", ">", ""), ("ITCs (GST Paid)", "<", "")]:
        row = ["", label]
        for q_start, q_end in [(1,3),(4,6),(7,9),(10,12)]:
            row.append(f"=SUMPRODUCT(({TQ}!E$4:E$1000=TRUE)*({TQ}!D$4:D$1000{op}0)*((MONTH(DATEVALUE({TQ}!A$4:A$1000))>={q_start})*(MONTH(DATEVALUE({TQ}!A$4:A$1000))<={q_end}))*{TQ}!H$4:H$1000)")
        row += [f"=SUM(C{len(g)+1}:F{len(g)+1})", ""]
        g.append(row)
    g.append([""] * 8)
    g.append(["", "NET OWING", f"=C6-C7", f"=D6-D7", f"=E6-E7", f"=F6-F7", f"=SUM(C9:F9)", ""])
    g.append([""] * 8)
    g.append(["", "Due Date", "Apr 30", "Jul 31", "Oct 31", "Jan 31", "", ""])
    g.append(["", "Filed?", False, False, False, False, "", ""])
    g.append(["", "Payment Date", "", "", "", "", "", ""])

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
        ["", "Gross Business Income", f"=SUMPRODUCT(({TQ}!E4:E1000=TRUE)*({TQ}!D4:D1000>0)*{TQ}!D4:D1000)", "8299", "", ""],
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

    # ── EQUIPMENT ──
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

    # ── MILEAGE ──
    mi = [["Date", "From", "To", "Client / Purpose", "KM", "Type", "Notes", "", "", "Summary", "", ""]]
    mi.append(["","","","","","","","","","Total KM","=SUM(E2:E500)",""])
    mi.append(["","","","","","","","","","Business KM",'=SUMIF(F2:F500,"Business",E2:E500)',""])
    mi.append(["","","","","","","","","","Business %","=IF(K2>0,K3/K2,0)",""])
    mi.append(["","","","","","","","","","CRA Deduction","=IF(K3<=5000,K3*0.72,5000*0.72+(K3-5000)*0.66)",""])
    for _ in range(100):
        mi.append([""]*12)

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
        {"range": f"Mileage!A1:L{len(mi)}", "values": mi},
    ]
    svc.spreadsheets().values().batchUpdate(
        spreadsheetId=sid, body={"valueInputOption": "USER_ENTERED", "data": updates}
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

    # Sub-metrics row
    R.append(f_(0, 7, 8, 2, 18, size=9, fg=C["t3"]))

    # Monthly section
    R.append(f_(0, 10, 11, 2, 9, bold=True, size=14, fg=C["navy"]))
    R.append(f_(0, 10, 11, 10, 16, bold=True, size=14, fg=C["navy"]))
    R.append(f_(0, 11, 12, 2, 9, bold=True, size=9, fg=C["t3"], bg=C["white"]))
    R.append(f_(0, 11, 12, 10, 16, bold=True, size=9, fg=C["t3"], bg=C["white"]))
    for i in range(12):
        row = 12 + i
        bg = C["white"] if i % 2 == 0 else C["bg"]
        R.append(f_(0, row, row+1, 2, 9, size=10, fg=C["t1"], bg=bg))
        R.append(f_(0, row, row+1, 10, 16, size=10, fg=C["t1"], bg=bg))
    R.append(f_(0, 24, 25, 2, 9, bold=True, size=11, fg=C["blue"], bg=C["blue_bg"]))

    # GST summary
    R.append(f_(0, 26, 27, 2, 9, bold=True, size=14, fg=C["navy"]))
    for i in range(3):
        R.append(f_(0, 27+i, 28+i, 10, 14, size=10, fg=C["t1"], bg=C["white"]))
    R.append(f_(0, 29, 30, 10, 14, bold=True, fg=C["red"], bg=C["red_bg"]))

    # Dashboard number formats
    R.append(nf(0, 5, 6, 2, 4, "$#,##0"))
    R.append(nf(0, 5, 6, 6, 8, "$#,##0"))
    R.append(nf(0, 5, 6, 10, 12, "$#,##0"))
    R.append(nf(0, 5, 6, 14, 16, "$#,##0"))
    R.append(nf(0, 12, 25, 3, 6, "$#,##0"))
    R.append(nf(0, 12, 25, 6, 7, "0.0%"))
    R.append(nf(0, 12, 25, 11, 12, "$#,##0"))
    R.append(nf(0, 12, 25, 12, 13, "0.0%"))
    R.append(nf(0, 7, 8, 3, 4, "0.0%"))
    R.append(nf(0, 7, 8, 11, 12, "0.0%"))
    R.append(nf(0, 27, 30, 11, 12, "$#,##0.00"))

    # Dashboard col widths
    dw = [10,10,140,110,110,90,140,110,110,20,140,110,80,10,10,10,10,10]
    for i, w in enumerate(dw):
        R.append(cw(0, i, w))

    # ── TRANSACTIONS ──
    R.append(f_(1, 0, 1, 0, 14, bold=True, size=9, fg=C["t3"], bg=C["white"]))
    R.append(rh(1, 0, 30))
    R.append(f_(1, 2, 3, 0, 14, bold=True, size=9, fg=C["t2"], bg=C["blue_bg"]))
    tw = [100, 170, 170, 100, 75, 180, 65, 85, 65, 90, 110, 170, 10, 10]
    for i, w in enumerate(tw):
        R.append(cw(1, i, w))
    # Alternating rows
    for r in range(3, len(t)):
        bg = C["white"] if r % 2 == 1 else C["bg"]
        R.append(f_(1, r, r+1, 0, 14, size=10, fg=C["t1"], bg=bg))
    R.append(nf(1, 3, 600, 3, 4, "$#,##0.00"))
    R.append(nf(1, 3, 600, 7, 8, "$#,##0.00"))

    # ── BUSINESS ──
    R.append(f_(2, 0, 1, 0, 17, bold=True, size=9, fg=C["t3"], bg=C["white"]))
    R.append(rh(2, 0, 30))
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

    # ── TAX ──
    R.append(f_(8, 1, 2, 1, 4, bold=True, size=18, fg=C["navy"]))
    R.append(f_(8, 2, 3, 1, 4, size=10, fg=C["t3"]))
    R.append(f_(8, 4, 5, 1, 4, bold=True, size=11, fg=C["blue"]))
    R.append(f_(8, 6, 7, 1, 4, bold=True, size=14, fg=C["green"], bg=C["green_bg"]))
    R.append(f_(8, 8, 9, 1, 4, bold=True, size=10, fg=C["t2"]))
    for r in range(9, 25):
        bg = C["white"] if r % 2 == 0 else C["bg"]
        R.append(f_(8, r, r+1, 1, 4, size=10, fg=C["t2"], bg=bg))
    R.append(f_(8, 25, 26, 1, 4, bold=True, fg=C["orange"], bg=C["orange_bg"]))
    R.append(f_(8, 27, 28, 1, 4, bold=True, size=14, fg=C["green"], bg=C["green_bg"]))
    R.append(f_(8, 39, 40, 1, 4, bold=True, fg=C["t1"], bg=C["white"]))
    R.append(f_(8, 44, 45, 1, 4, bold=True, size=14, fg=C["red"], bg=C["red_bg"]))
    R.append(f_(8, 45, 46, 1, 4, bold=True, size=11, fg=C["orange"], bg=C["orange_bg"]))
    R.append(nf(8, 6, 51, 2, 3, "$#,##0.00"))
    txw = [15, 180, 120, 80, 10, 10]
    for i, w in enumerate(txw):
        R.append(cw(8, i, w))

    # ── DATA VALIDATION ──
    R.append(dv_bool(1, 3, 600, 4, 5))     # Business checkbox
    R.append(dv_bool(1, 3, 600, 8, 9))     # Receipt checkbox
    R.append(dv_list(1, 3, 600, 5, 6, ALL_CATS))
    R.append(dv_list(1, 3, 600, 6, 7, ["100%","75%","50%","25%","0%"]))
    R.append(dv_list(1, 3, 600, 9, 10, ["Visa","Debit","E-Transfer","Cash","PayPal"]))
    R.append(dv_list(1, 3, 600, 10, 11, ["Personal Card","Business Account","Personal Account","Cash"]))
    R.append(dv_list(6, 1, 200, 5, 6, ["Business","Personal"]))
    R.append(dv_bool(5, 11, 12, 2, 6))

    # ── CONDITIONAL FORMATTING ──
    # Business rows get soft blue bg
    R.append(cf(1, 3, 600, 0, 14, "=$E4=TRUE", C["blue_l"]))
    # Negative amounts red text
    R.append(cf_text(1, 3, 600, 3, 4, "=$D4<0", C["red"]))
    # Positive amounts green text
    R.append(cf_text(1, 3, 600, 3, 4, "=$D4>0", C["green"]))
    # Missing receipt on business = soft red
    R.append(cf(1, 3, 600, 8, 9, "=AND($E4=TRUE,$I4=FALSE,$D4<>\"\",$D4<>0)", C["red_bg"]))
    # P&L profit coloring
    R.append(cf_text(4, 1, 14, 3, 4, "=$D2<0", C["red"]))
    R.append(cf_text(4, 1, 14, 3, 4, "=$D2>0", C["green"]))

    # ── CHARTS ──
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

    svc.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": R}).execute()
    print("Formatting applied.")

    # Save ID
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            content = f.read()
        content = re.sub(r"FINANCE_SHEET_ID=.*", f"FINANCE_SHEET_ID={sid}", content)
        with open(env_path, "w") as f:
            f.write(content)

    print(f"\n→ {url}")
    return sid, url


# ═══════════════════════════════════════════
# HELPERS
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
def border_all(s, r1, r2, c1, c2, color):
    bdr = {"style": "SOLID", "colorStyle": {"rgbColor": color}}
    return {"updateBorders": {"range": {"sheetId": s, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}, "top": bdr, "bottom": bdr, "left": bdr, "right": bdr}}
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
