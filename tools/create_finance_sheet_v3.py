"""
Matt Anthony Photography — Finance Tracker v3
Premium dark-theme design. Fintech-level dashboard.
"""
import sys, os, csv, re
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.google_sheets_auth import get_sheets_service, get_drive_service

YEAR = 2026

# ═══════════════════════════════════════════
# DESIGN TOKENS
# ═══════════════════════════════════════════
C = {
    # Backgrounds
    "bg":       {"red": 0.067, "green": 0.071, "blue": 0.082},   # #111218 deep bg
    "bg2":      {"red": 0.098, "green": 0.106, "blue": 0.122},   # #191B1F elevated
    "card":     {"red": 0.122, "green": 0.133, "blue": 0.157},   # #1F2228 card
    "card_h":   {"red": 0.149, "green": 0.161, "blue": 0.192},   # #262931 card hover/alt
    "input":    {"red": 0.173, "green": 0.184, "blue": 0.216},   # #2C2F37 input field
    "border":   {"red": 0.200, "green": 0.212, "blue": 0.243},   # #33363E subtle border
    # Text
    "t1":       {"red": 0.961, "green": 0.969, "blue": 0.980},   # #F5F7FA primary
    "t2":       {"red": 0.690, "green": 0.714, "blue": 0.757},   # #B0B6C1 secondary
    "t3":       {"red": 0.443, "green": 0.463, "blue": 0.510},   # #717682 muted
    "t4":       {"red": 0.302, "green": 0.318, "blue": 0.357},   # #4D515B disabled
    # Accents
    "blue":     {"red": 0.318, "green": 0.545, "blue": 0.992},   # #518BFD
    "blue_bg":  {"red": 0.118, "green": 0.161, "blue": 0.278},   # #1E2947
    "blue_s":   {"red": 0.184, "green": 0.290, "blue": 0.529},   # #2F4A87
    "green":    {"red": 0.188, "green": 0.788, "blue": 0.510},   # #30C982
    "green_bg": {"red": 0.082, "green": 0.200, "blue": 0.141},   # #153324
    "green_s":  {"red": 0.110, "green": 0.302, "blue": 0.200},   # #1C4D33
    "red":      {"red": 0.969, "green": 0.341, "blue": 0.369},   # #F7575E
    "red_bg":   {"red": 0.251, "green": 0.098, "blue": 0.106},   # #40191B
    "red_s":    {"red": 0.353, "green": 0.122, "blue": 0.133},   # #5A1F22
    "orange":   {"red": 0.992, "green": 0.647, "blue": 0.224},   # #FDA539
    "orange_bg":{"red": 0.263, "green": 0.176, "blue": 0.082},   # #432D15
    "purple":   {"red": 0.608, "green": 0.420, "blue": 0.933},   # #9B6BEE
    "purple_bg":{"red": 0.176, "green": 0.122, "blue": 0.290},   # #2D1F4A
    "cyan":     {"red": 0.200, "green": 0.780, "blue": 0.878},   # #33C7E0
    "cyan_bg":  {"red": 0.082, "green": 0.200, "blue": 0.235},   # #15333C
    "white":    {"red": 1, "green": 1, "blue": 1},
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


def create():
    svc = get_sheets_service()

    tabs = [
        ("⬡  Dashboard", 0, 0, 30),
        ("⬡  Transactions", 1, 4, 26),
        ("⬡  Business", 2, 1, 20),
        ("⬡  Personal", 3, 1, 18),
        ("⬡  P&L", 4, 1, 12),
        ("⬡  GST / HST", 5, 0, 12),
        ("⬡  Mileage", 6, 1, 12),
        ("⬡  Equipment", 7, 1, 14),
        ("⬡  Tax Summary", 8, 0, 10),
    ]

    sheet_props = []
    tab_colors = [C["blue"],C["green"],C["orange"],C["purple"],C["blue"],C["red"],C["t3"],C["green"],C["red"]]
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
                "textFormat": {"foregroundColorStyle": {"rgbColor": C["t1"]}, "fontFamily": "Google Sans", "fontSize": 10}
            }
        },
        "sheets": sheet_props
    }).execute()

    sid = sp["spreadsheetId"]
    url = sp["spreadsheetUrl"]
    print(f"Created: {url}")

    # ═══════════════════════════════════════════
    # BUILD DATA
    # ═══════════════════════════════════════════

    # ── DASHBOARD ──
    d = []
    d.append([""] * 20)  # row 1 spacer
    d.append(["", "", "FINANCE DASHBOARD", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])  # row 2
    d.append(["", "", f"Matt Anthony Photography  ·  {YEAR}", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])  # row 3
    d.append([""] * 20)  # row 4 spacer

    # KPI CARDS — row 5-8
    d.append(["", "",                                                                          # spacer + label start
        "REVENUE", "", "",                                                                      # cols C-E
        "",                                                                                     # spacer
        "EXPENSES", "", "",                                                                     # cols G-I
        "",                                                                                     # spacer
        "NET PROFIT", "", "",                                                                   # cols K-M
        "",                                                                                     # spacer
        "TAX + CPP", "", "",                                                                    # cols O-Q
        "", "", ""])
    d.append(["", "",
        "YTD Total", "", "",
        "",
        "YTD Business", "", "",
        "",
        "YTD", "", "",
        "",
        "Estimated", "", "",
        "", "", ""])
    d.append(["", "",  # values
        "=SUMPRODUCT(('⬡  Transactions'!E5:E1000=TRUE)*('⬡  Transactions'!D5:D1000>0)*'⬡  Transactions'!D5:D1000)", "", "",
        "",
        "=SUMPRODUCT(('⬡  Transactions'!E5:E1000=TRUE)*('⬡  Transactions'!D5:D1000<0)*ABS('⬡  Transactions'!D5:D1000))", "", "",
        "",
        "=C7-G7", "", "",
        "",
        "='⬡  Tax Summary'!C44", "", "",
        "", "", ""])
    d.append(["", "",  # sparklines
        '=SPARKLINE(ARRAYFORMULA(SUMPRODUCT(('+"'⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000>0)*(MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))={1,2,3,4,5,6,7,8,9,10,11,12}))*'⬡  Transactions'!D$5:D$1000"+')),{"charttype","bar";"color1","#518BFD";"max",30000})', "", "",
        "",
        "", "", "",
        "",
        "", "", "",
        "",
        "", "", "",
        "", "", ""])
    d.append([""] * 20)  # row 9 spacer

    # TARGET PROGRESS — row 10-12
    d.append(["", "", "REVENUE TARGET", "", "", "", "", "", "", "", "MONTHLY BREAKDOWN", "", "", "", "", "", "", "", "", ""])
    d.append(["", "",
        "Target", 172900, "",
        "% Complete", "=IF(D11>0,C7/D11,0)", "",
        "", "",
        "Month", "Revenue", "Expenses", "Net", "Margin", "  ", "", "", "", ""])
    # Progress bar row
    d.append(["", "",
        "Achieved", "=C7", "",
        "Remaining", "=D11-D12", "",
        "", "", "", "", "", "", "", "", "", "", "", ""])

    # Monthly rows 13-24
    for i, m in enumerate(MONTHS):
        mn = i + 1
        r = 13 + i
        row = [""] * 20
        row[10] = m
        row[11] = f"=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000>0)*(MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))={mn})*'⬡  Transactions'!D$5:D$1000)"
        row[12] = f"=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000<0)*(MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))={mn})*ABS('⬡  Transactions'!D$5:D$1000))"
        row[13] = f"=L{r}-M{r}"
        row[14] = f"=IF(L{r}>0,N{r}/L{r},0)"
        # Inline bar
        row[15] = f'=IF(L{r}>0,SPARKLINE(L{r},{{"charttype","bar";"max",30000;"color1","#518BFD"}}),"")'
        d.append(row)
    # Total row 25
    total_row = [""] * 20
    total_row[10] = "TOTAL"
    total_row[11] = "=SUM(L13:L24)"
    total_row[12] = "=SUM(M13:M24)"
    total_row[13] = "=SUM(N13:N24)"
    total_row[14] = "=IF(L25>0,N25/L25,0)"
    d.append(total_row)

    d.append([""] * 20)  # spacer

    # EXPENSE BREAKDOWN + PERSONAL — row 27+
    d.append(["", "", "TOP BUSINESS COSTS", "", "", "", "", "", "", "", "PERSONAL SPENDING", "", "", "", "", "", "GST SUMMARY", "", "", ""])
    cats_biz = ["Software & Subscriptions", "Travel", "Rent / Co-working", "Advertising & Marketing", "Telephone & Internet"]
    cats_pers = ["Dining Out", "Groceries", "Health & Fitness", "Subscriptions", "Entertainment", "Travel (Personal)"]
    max_rows = max(len(cats_biz), len(cats_pers))
    for i in range(max_rows):
        row = [""] * 20
        if i < len(cats_biz):
            cat = cats_biz[i]
            row[2] = f"  {cat}"
            row[3] = f"=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000<0)*('⬡  Transactions'!F$5:F$1000=\"{cat}\")*ABS('⬡  Transactions'!D$5:D$1000))"
            row[4] = f'=IF(G7>0,SPARKLINE(D{28+i},{{"charttype","bar";"max",G7;"color1","#FDA539"}}),"")'
        if i < len(cats_pers):
            cat = cats_pers[i]
            row[10] = f"  {cat}"
            row[11] = f"=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=FALSE)*('⬡  Transactions'!D$5:D$1000<0)*('⬡  Transactions'!F$5:F$1000=\"{cat}\")*ABS('⬡  Transactions'!D$5:D$1000))"
        if i == 0:
            row[16] = "  GST Collected"
            row[17] = "=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000>0)*'⬡  Transactions'!H$5:H$1000)"
        elif i == 1:
            row[16] = "  ITCs (GST Paid)"
            row[17] = "=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000<0)*'⬡  Transactions'!H$5:H$1000)"
        elif i == 2:
            row[16] = "  Net GST Owing"
            row[17] = "=R28-R29"
        d.append(row)

    # ── TRANSACTIONS ──
    t = []
    t.append([""] * 16)  # spacer
    t.append(["", "TRANSACTIONS", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
    t.append(["", f"All income and expenses  ·  {YEAR}", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
    t.append([""] * 16)  # spacer between title and headers
    t.append(["", "Date", "Vendor", "Description", "Amount", "Business", "Category",
              "Split %", "GST", "Receipt", "Payment", "Account", "Notes", "", "", ""])
    for _ in range(500):
        t.append(["", "", "", "", "", False, "", "100%", "", False, "", "", "", "", "", ""])

    # ── BUSINESS SUMMARY ──
    b = [["  CRA Category", "  Line #", "  YTD"] + [f"  {m}" for m in MONTHS] + ["", "  TREND"]]
    t2125 = {"Advertising & Marketing":"8521","Professional Fees":"8590","Vehicle":"8615",
        "Insurance":"8690","Interest & Bank Charges":"8710","Office Supplies (<$500)":"8811",
        "Rent / Co-working":"8860","Software & Subscriptions":"8871","Travel":"8910",
        "Telephone & Internet":"8945","Subcontractors":"9060","Meals & Entertainment":"9270",
        "Home Office":"9281","Equipment (CCA)":"9936","Other Business":"—"}
    for cat in BIZ_CATS:
        r = len(b) + 1
        row = [f"  {cat}", f"  {t2125.get(cat,'')}", f"=SUM(D{r}:O{r})"]
        for mn in range(1, 13):
            row.append(f"=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000<0)*('⬡  Transactions'!F$5:F$1000=\"{cat}\")*(MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))={mn})*ABS('⬡  Transactions'!D$5:D$1000))")
        row.append("")
        row.append(f'=SPARKLINE(D{r}:O{r},{{"charttype","line";"linewidth",2;"color","#FDA539"}})')
        b.append(row)
    b.append([""] * 17)
    tr = len(b) + 1
    b.append(["  TOTAL", "", f"=SUM(C2:C16)"] + [f"=SUM({chr(68+i)}2:{chr(68+i)}16)" for i in range(12)] + ["", ""])

    # ── PERSONAL SUMMARY ──
    p = [["  Category", "  YTD"] + [f"  {m}" for m in MONTHS] + ["", "  TREND"]]
    for cat in PERS_CATS:
        r = len(p) + 1
        row = [f"  {cat}", f"=SUM(C{r}:N{r})"]
        for mn in range(1, 13):
            row.append(f"=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=FALSE)*('⬡  Transactions'!D$5:D$1000<0)*('⬡  Transactions'!F$5:F$1000=\"{cat}\")*(MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))={mn})*ABS('⬡  Transactions'!D$5:D$1000))")
        row.append("")
        row.append(f'=SPARKLINE(C{r}:N{r},{{"charttype","line";"linewidth",2;"color","#9B6BEE"}})')
        p.append(row)
    p.append([""] * 16)
    ptr = len(p) + 1
    p.append(["  TOTAL", f"=SUM(B2:B13)"] + [f"=SUM({chr(67+i)}2:{chr(67+i)}13)" for i in range(12)] + ["", ""])

    # ── P&L ──
    pl = [["  Month", "  Revenue", "  Expenses", "  Profit", "  Margin", "  Cumul Rev", "  Cumul Profit", "  vs Target", "", "  PROFIT TREND"]]
    for i, m in enumerate(MONTHS):
        r = i + 2
        mn = i + 1
        pl.append([
            f"  {m}",
            f"=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000>0)*(MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))={mn})*'⬡  Transactions'!D$5:D$1000)",
            f"=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000<0)*(MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))={mn})*ABS('⬡  Transactions'!D$5:D$1000))",
            f"=B{r}-C{r}", f"=IF(B{r}>0,D{r}/B{r},0)",
            f"=SUM(B$2:B{r})", f"=SUM(D$2:D{r})",
            f"=F{r}-({172900}/12*{mn})", "",
            "" if i > 0 else f'=SPARKLINE(ARRAYFORMULA({{D2,D3,D4,D5,D6,D7,D8,D9,D10,D11,D12,D13}}),{{"charttype","line";"linewidth",2;"color","#30C982"}})'
        ])
    pl.append([""] * 10)
    pl.append(["  TOTAL", "=SUM(B2:B13)", "=SUM(C2:C13)", "=SUM(D2:D13)", "=IF(B15>0,D15/B15,0)", "", "", "", "", ""])

    # ── GST ──
    g = [
        [""] * 10,
        ["", "  GST / HST TRACKER", "", "", "", "", "", "", "", ""],
        ["", f"  Registration: Enter # here  ·  Filing: Quarterly  ·  Rate: 5%", "", "", "", "", "", "", "", ""],
        [""] * 10,
        ["", "", "  Q1 (Jan–Mar)", "  Q2 (Apr–Jun)", "  Q3 (Jul–Sep)", "  Q4 (Oct–Dec)", "  YTD", "", "", ""],
        ["", "  GST Collected",
         "=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000>0)*((MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))>=1)*(MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))<=3))*'⬡  Transactions'!H$5:H$1000)",
         "=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000>0)*((MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))>=4)*(MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))<=6))*'⬡  Transactions'!H$5:H$1000)",
         "=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000>0)*((MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))>=7)*(MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))<=9))*'⬡  Transactions'!H$5:H$1000)",
         "=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000>0)*((MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))>=10)*(MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))<=12))*'⬡  Transactions'!H$5:H$1000)",
         "=SUM(C6:F6)", "", "", ""],
        ["", "  ITCs (GST Paid)",
         "=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000<0)*((MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))>=1)*(MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))<=3))*'⬡  Transactions'!H$5:H$1000)",
         "=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000<0)*((MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))>=4)*(MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))<=6))*'⬡  Transactions'!H$5:H$1000)",
         "=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000<0)*((MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))>=7)*(MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))<=9))*'⬡  Transactions'!H$5:H$1000)",
         "=SUMPRODUCT(('⬡  Transactions'!E$5:E$1000=TRUE)*('⬡  Transactions'!D$5:D$1000<0)*((MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))>=10)*(MONTH(DATEVALUE('⬡  Transactions'!A$5:A$1000))<=12))*'⬡  Transactions'!H$5:H$1000)",
         "=SUM(C7:F7)", "", "", ""],
        [""] * 10,
        ["", "  NET OWING", "=C6-C7", "=D6-D7", "=E6-E7", "=F6-F7", "=SUM(C9:F9)", "", "", ""],
        [""] * 10,
        ["", "  Due Date", "  Apr 30", "  Jul 31", "  Oct 31", "  Jan 31", "", "", "", ""],
        ["", "  Filed?", False, False, False, False, "", "", "", ""],
        ["", "  Payment Date", "", "", "", "", "", "", "", ""],
    ]

    # ── TAX SUMMARY ──
    tx = [
        [""] * 8,
        ["", "  TAX SUMMARY", "", "", "", "", "", ""],
        ["", f"  Sole Proprietor  ·  BC, Canada  ·  {YEAR}", "", "", "", "", "", ""],
        [""] * 8,
        # T2125
        ["", "  T2125 INCOME STATEMENT", "", "  CRA Line", "", "", "", ""],
        [""] * 8,
        ["", "  Gross Business Income", "=SUMPRODUCT(('⬡  Transactions'!E5:E1000=TRUE)*('⬡  Transactions'!D5:D1000>0)*'⬡  Transactions'!D5:D1000)", "  8299", "", "", "", ""],
        [""] * 8,
        ["", "  EXPENSES", "", "", "", "", "", ""],
    ]
    expenses = [
        ("Advertising & Marketing", "='⬡  Business'!C2", "8521"),
        ("Professional Fees", "='⬡  Business'!C3", "8590"),
        ("Vehicle", "='⬡  Business'!C4", "8615"),
        ("Insurance", "='⬡  Business'!C5", "8690"),
        ("Interest & Bank", "='⬡  Business'!C6", "8710"),
        ("Office Supplies", "='⬡  Business'!C7", "8811"),
        ("Rent / Co-working", "='⬡  Business'!C8", "8860"),
        ("Software & Subs", "='⬡  Business'!C9", "8871"),
        ("Travel", "='⬡  Business'!C10", "8910"),
        ("Phone & Internet", "='⬡  Business'!C11", "8945"),
        ("Subcontractors", "='⬡  Business'!C12", "9060"),
        ("Meals (50%)", "='⬡  Business'!C13*0.5", "9270"),
        ("Home Office", "='⬡  Business'!C14", "9281"),
        ("CCA", "='⬡  Equipment'!G33", "9936"),
        ("Other", "='⬡  Business'!C16", "—"),
    ]
    for name, formula, line in expenses:
        tx.append(["", f"  {name}", formula, f"  {line}", "", "", "", ""])
    tx.append([""] * 8)
    er = len(tx) + 1
    tx.append(["", "  Total Expenses", f"=SUM(C10:C24)", "  9369", "", "", "", ""])
    tx.append([""] * 8)
    tx.append(["", "  NET BUSINESS INCOME", "=C7-C26", "  9946", "", "", "", ""])
    tx.append([""] * 8)
    # Tax calc
    tx.append(["", "  ESTIMATED TAX", "", "", "", "", "", ""])
    tx.append([""] * 8)
    tx.append(["", "  Federal Tax", "=IF(C28<=57375,C28*0.15,57375*0.15+(C28-57375)*0.205)", "", "", "", "", ""])
    tx.append(["", "  Basic Personal Credit", -2506, "", "", "", "", ""])
    tx.append(["", "  Federal After Credits", "=MAX(0,C32+C33)", "", "", "", "", ""])
    tx.append([""] * 8)
    tx.append(["", "  BC Provincial Tax", "=IF(C28<=47937,C28*0.0506,47937*0.0506+(C28-47937)*0.077)", "", "", "", "", ""])
    tx.append(["", "  BC Personal Credit", -596, "", "", "", "", ""])
    tx.append(["", "  BC After Credits", "=MAX(0,C36+C37)", "", "", "", "", ""])
    tx.append([""] * 8)
    tx.append(["", "  TOTAL INCOME TAX", "=C34+C38", "", "", "", "", ""])
    tx.append([""] * 8)
    tx.append(["", "  CPP Self-Employed", "=IF(C28>3500,MIN((C28-3500)*0.119,7735.50),0)", "", "", "", "", ""])
    tx.append(["", "  CPP2", "=IF(C28>73200,MIN((C28-73200)*0.08,396),0)", "", "", "", "", ""])
    tx.append(["", "  Total CPP", "=C42+C43", "", "", "", "", ""])
    tx.append([""] * 8)
    tx.append(["", "  TOTAL TAX + CPP", "=C40+C44", "  ← Plan for this", "", "", "", ""])
    tx.append(["", "  Quarterly Installment", "=C46/4", "", "", "", "", ""])
    tx.append([""] * 8)
    tx.append(["", "  RRSP Room (18%)", "=MIN(C28*0.18,32490)", "", "", "", "", ""])
    tx.append(["", "  RRSP Contributions", "", "  Enter actual", "", "", "", ""])
    tx.append(["", "  RRSP Tax Savings", "=C50*0.30", "  ~30% marginal", "", "", "", ""])

    # ── EQUIPMENT CCA ──
    eq = [["  Asset", "  Acquired", "  CCA Class", "  Rate", "  Cost", "  UCC Start", "  CCA Claimed", "  UCC End", "  Notes", "", "", "  COMMON CLASSES"]]
    # Reference classes
    classes = [
        ("Class 8", "20%", "Camera, lenses, lighting"),
        ("Class 10", "30%", "Vehicle"),
        ("Class 12", "100%", "Tools/software <$500"),
        ("Class 50", "55%", "Computers, drives"),
    ]
    for i in range(30):
        r = i + 2
        row = ["","","","","","",f"=IF(F{r}>0,F{r}*D{r},\"\")",f"=IF(F{r}>0,F{r}-G{r},\"\")", "","","",""]
        if i < len(classes):
            row[11] = f"  {classes[i][0]} — {classes[i][1]} — {classes[i][2]}"
        eq.append(row)
    eq.append([""] * 12)
    eq.append(["  TOTALS","","","",f"=SUM(E2:E31)",f"=SUM(F2:F31)",f"=SUM(G2:G31)",f"=SUM(H2:H31)","","","",""])

    # ── MILEAGE ──
    mi = [["  Date", "  From", "  To", "  Client / Purpose", "  KM", "  Type", "  Notes", "", "", "  SUMMARY", "", ""]]
    mi.append(["","","","","","","","","","  Total KM", "=SUM(E2:E500)", ""])
    mi.append(["","","","","","","","","","  Business KM", '=SUMIF(F2:F500,"Business",E2:E500)', ""])
    mi.append(["","","","","","","","","","  Business %", "=IF(K2>0,K3/K2,0)", ""])
    mi.append(["","","","","","","","","","  CRA Deduction", "=IF(K3<=5000,K3*0.72,5000*0.72+(K3-5000)*0.66)", ""])
    for _ in range(150):
        mi.append(["","","","","","","","","","","",""])

    # ═══════════════════════════════════════════
    # WRITE DATA
    # ═══════════════════════════════════════════
    updates = [
        {"range": f"'⬡  Dashboard'!A1:T{len(d)}", "values": d},
        {"range": f"'⬡  Transactions'!A1:P{len(t)}", "values": t},
        {"range": f"'⬡  Business'!A1:Q{len(b)}", "values": b},
        {"range": f"'⬡  Personal'!A1:P{len(p)}", "values": p},
        {"range": f"'⬡  P&L'!A1:J{len(pl)}", "values": pl},
        {"range": f"'⬡  GST / HST'!A1:J{len(g)}", "values": g},
        {"range": f"'⬡  Tax Summary'!A1:H{len(tx)}", "values": tx},
        {"range": f"'⬡  Equipment'!A1:L{len(eq)}", "values": eq},
        {"range": f"'⬡  Mileage'!A1:L{len(mi)}", "values": mi},
    ]
    svc.spreadsheets().values().batchUpdate(
        spreadsheetId=sid, body={"valueInputOption": "USER_ENTERED", "data": updates}
    ).execute()
    print("Data written.")

    # ═══════════════════════════════════════════
    # FORMATTING
    # ═══════════════════════════════════════════
    R = []

    # ── DASHBOARD ──
    # Title
    R.append(merge(0, 1, 2, 2, 10))
    R.append(merge(0, 2, 3, 2, 10))
    R.append(f_(0, 1, 2, 2, 10, bold=True, size=26, fg=C["t1"]))
    R.append(f_(0, 2, 3, 2, 10, size=11, fg=C["t3"]))

    # KPI cards — each gets a card background with colored accent
    kpis = [(2, 5, "blue"), (6, 9, "orange"), (10, 13, "green"), (14, 17, "red")]
    for c1, c2, color in kpis:
        # Card bg
        for row in range(4, 9):
            R.append(f_(0, row, row+1, c1, c2, bg=C["card"]))
        # Label
        R.append(f_(0, 4, 5, c1, c2, bold=True, size=9, fg=C["t3"], bg=C["card"]))
        # Sub label
        R.append(f_(0, 5, 6, c1, c2, size=8, fg=C["t4"], bg=C["card"]))
        # Value
        R.append(f_(0, 6, 7, c1, c2, bold=True, size=22, fg=C[color], bg=C["card"]))
        # Top border accent
        R.append(border_top(0, 4, c1, c2, C[color]))
        # Bottom border
        R.append(border_bottom(0, 8, c1, c2, C["border"]))

    # Target section
    R.append(f_(0, 9, 10, 2, 9, bold=True, size=13, fg=C["t1"]))
    R.append(f_(0, 10, 11, 2, 5, size=10, fg=C["t2"], bg=C["card"]))
    R.append(f_(0, 10, 11, 5, 8, size=10, fg=C["t2"], bg=C["card"]))
    R.append(f_(0, 11, 12, 2, 5, size=10, fg=C["t2"], bg=C["card"]))
    R.append(f_(0, 11, 12, 5, 8, size=10, fg=C["t2"], bg=C["card"]))

    # Monthly header
    R.append(f_(0, 9, 10, 10, 17, bold=True, size=13, fg=C["t1"]))
    R.append(f_(0, 11, 12, 10, 17, bold=True, size=9, fg=C["t3"], bg=C["card"]))
    # Monthly rows
    for i in range(12):
        row = 12 + i
        bg = C["card"] if i % 2 == 0 else C["card_h"]
        R.append(f_(0, row, row+1, 10, 17, size=10, fg=C["t2"], bg=bg))
    R.append(f_(0, 24, 25, 10, 17, bold=True, size=11, fg=C["blue"], bg=C["blue_bg"]))

    # Bottom sections
    R.append(f_(0, 26, 27, 2, 6, bold=True, size=13, fg=C["t1"]))
    R.append(f_(0, 26, 27, 10, 14, bold=True, size=13, fg=C["t1"]))
    R.append(f_(0, 26, 27, 16, 19, bold=True, size=13, fg=C["t1"]))
    for i in range(6):
        row = 27 + i
        bg = C["card"] if i % 2 == 0 else C["card_h"]
        R.append(f_(0, row, row+1, 2, 6, size=10, fg=C["t2"], bg=bg))
        R.append(f_(0, row, row+1, 10, 13, size=10, fg=C["t2"], bg=bg))
        if i < 3:
            R.append(f_(0, row, row+1, 16, 19, size=10, fg=C["t2"], bg=bg))

    # Dashboard col widths
    dash_widths = [10, 10, 160, 120, 130, 100, 120, 120, 100, 20, 120, 110, 110, 100, 80, 130, 130, 120, 10, 10]
    for i, w in enumerate(dash_widths):
        R.append(cw(0, i, w))
    # Row heights
    R.append(rh(0, 0, 20))
    R.append(rh(0, 1, 42))
    R.append(rh(0, 2, 24))
    R.append(rh(0, 3, 16))
    for r in range(4, 9):
        R.append(rh(0, r, 32))
    R.append(rh(0, 8, 20))

    # ── TRANSACTIONS ──
    # Title
    R.append(merge(1, 1, 2, 1, 8))
    R.append(f_(1, 1, 2, 1, 8, bold=True, size=22, fg=C["t1"]))
    R.append(merge(1, 2, 3, 1, 8))
    R.append(f_(1, 2, 3, 1, 8, size=10, fg=C["t3"]))
    # Header row
    R.append(f_(1, 4, 5, 0, 16, bold=True, size=9, fg=C["t3"], bg=C["card"]))
    R.append(rh(1, 4, 32))
    # Column A spacer
    R.append(cw(1, 0, 10))
    # Data columns
    txn_widths = [10, 100, 180, 180, 110, 80, 190, 70, 90, 70, 100, 120, 180, 10, 10, 10]
    for i, w in enumerate(txn_widths):
        R.append(cw(1, i, w))
    # Alternating rows
    for r in range(5, 505):
        bg = C["bg"] if r % 2 == 0 else C["bg2"]
        R.append(f_(1, r, r+1, 0, 16, size=10, fg=C["t2"], bg=bg))
    # Amount column formatting
    R.append(nf(1, 5, 505, 4, 5, "$#,##0.00"))
    R.append(nf(1, 5, 505, 8, 9, "$#,##0.00"))

    # ── BUSINESS TAB ──
    R.append(f_(2, 0, 1, 0, 17, bold=True, size=9, fg=C["t3"], bg=C["card"]))
    R.append(rh(2, 0, 32))
    for i in range(15):
        r = i + 1
        bg = C["card"] if i % 2 == 0 else C["card_h"]
        R.append(f_(2, r, r+1, 0, 17, size=10, fg=C["t2"], bg=bg))
    R.append(f_(2, len(b)-1, len(b), 0, 17, bold=True, size=11, fg=C["orange"], bg=C["orange_bg"]))
    R.append(nf(2, 1, 20, 2, 16, "$#,##0"))
    biz_widths = [220, 60, 90] + [75]*12 + [10, 120]
    for i, w in enumerate(biz_widths):
        R.append(cw(2, i, w))

    # ── PERSONAL TAB ──
    R.append(f_(3, 0, 1, 0, 16, bold=True, size=9, fg=C["t3"], bg=C["card"]))
    for i in range(12):
        r = i + 1
        bg = C["card"] if i % 2 == 0 else C["card_h"]
        R.append(f_(3, r, r+1, 0, 16, size=10, fg=C["t2"], bg=bg))
    R.append(f_(3, len(p)-1, len(p), 0, 16, bold=True, size=11, fg=C["purple"], bg=C["purple_bg"]))
    R.append(nf(3, 1, 16, 1, 15, "$#,##0"))
    pers_widths = [180, 90] + [75]*12 + [10, 120]
    for i, w in enumerate(pers_widths):
        R.append(cw(3, i, w))

    # ── P&L TAB ──
    R.append(f_(4, 0, 1, 0, 10, bold=True, size=9, fg=C["t3"], bg=C["card"]))
    for i in range(12):
        r = i + 1
        bg = C["card"] if i % 2 == 0 else C["card_h"]
        R.append(f_(4, r, r+1, 0, 10, size=10, fg=C["t2"], bg=bg))
    R.append(f_(4, 14, 15, 0, 10, bold=True, size=11, fg=C["blue"], bg=C["blue_bg"]))
    R.append(nf(4, 1, 16, 1, 4, "$#,##0"))
    R.append(nf(4, 1, 16, 5, 8, "$#,##0"))
    R.append(nf(4, 1, 16, 4, 5, "0.0%"))

    # ── GST TAB ──
    R.append(f_(5, 1, 2, 1, 7, bold=True, size=20, fg=C["t1"]))
    R.append(f_(5, 2, 3, 1, 7, size=10, fg=C["t3"]))
    R.append(f_(5, 4, 5, 1, 7, bold=True, size=9, fg=C["t3"], bg=C["card"]))
    R.append(f_(5, 5, 6, 1, 7, size=11, fg=C["green"], bg=C["card"]))
    R.append(f_(5, 6, 7, 1, 7, size=11, fg=C["red"], bg=C["card"]))
    R.append(f_(5, 8, 9, 1, 7, bold=True, size=13, fg=C["t1"], bg=C["red_bg"]))
    R.append(nf(5, 5, 10, 2, 7, "$#,##0.00"))

    # ── TAX SUMMARY TAB ──
    R.append(f_(8, 1, 2, 1, 5, bold=True, size=22, fg=C["t1"]))
    R.append(f_(8, 2, 3, 1, 5, size=10, fg=C["t3"]))
    R.append(f_(8, 4, 5, 1, 4, bold=True, size=12, fg=C["blue"]))
    R.append(f_(8, 6, 7, 1, 4, bold=True, size=14, fg=C["green"], bg=C["green_bg"]))
    R.append(f_(8, 8, 9, 1, 4, bold=True, size=10, fg=C["t2"]))
    for r in range(9, 25):
        bg = C["card"] if r % 2 == 0 else C["bg"]
        R.append(f_(8, r, r+1, 1, 4, size=10, fg=C["t2"], bg=bg))
    R.append(f_(8, 25, 26, 1, 4, bold=True, size=10, fg=C["orange"], bg=C["orange_bg"]))
    R.append(f_(8, 27, 28, 1, 4, bold=True, size=14, fg=C["green"], bg=C["green_bg"]))
    R.append(f_(8, 29, 30, 1, 4, bold=True, size=11, fg=C["t1"]))
    R.append(f_(8, 39, 40, 1, 4, bold=True, size=14, fg=C["red"], bg=C["red_bg"]))
    R.append(f_(8, 45, 46, 1, 4, bold=True, size=16, fg=C["red"], bg=C["red_bg"]))
    R.append(f_(8, 46, 47, 1, 4, bold=True, size=12, fg=C["orange"], bg=C["orange_bg"]))
    R.append(nf(8, 6, 51, 2, 3, "$#,##0.00"))
    tax_widths = [15, 200, 130, 100, 10, 10, 10, 10]
    for i, w in enumerate(tax_widths):
        R.append(cw(8, i, w))

    # ── DATA VALIDATION ──
    # Business checkbox (col F = index 5)
    R.append(dv_bool(1, 5, 505, 5, 6))
    # Receipt checkbox (col J = index 9)
    R.append(dv_bool(1, 5, 505, 9, 10))
    # Category dropdown (col G = index 6)
    R.append(dv_list(1, 5, 505, 6, 7, ALL_CATS))
    # Split % dropdown (col H = index 7)
    R.append(dv_list(1, 5, 505, 7, 8, ["100%","75%","50%","25%","0%"]))
    # Payment dropdown (col K = index 10)
    R.append(dv_list(1, 5, 505, 10, 11, ["Visa","Debit","E-Transfer","Cash","PayPal"]))
    # Account dropdown (col L = index 11)
    R.append(dv_list(1, 5, 505, 11, 12, ["Personal Card","Business Account","Personal Account","Cash"]))
    # Mileage type
    R.append(dv_list(6, 1, 200, 5, 6, ["Business","Personal"]))
    # GST Filed checkboxes
    R.append(dv_bool(5, 11, 12, 2, 6))

    # ── CONDITIONAL FORMATTING ──
    # Business rows glow green
    R.append(cf(1, 5, 505, 0, 16, "=$F5=TRUE", C["green_bg"]))
    # Negative amounts red
    R.append(cf_text(1, 5, 505, 4, 5, "=$E5<0", C["red"]))
    # Positive amounts green
    R.append(cf_text(1, 5, 505, 4, 5, "=$E5>0", C["green"]))
    # Missing receipt warning
    R.append(cf(1, 5, 505, 9, 10, "=AND($F5=TRUE,$J5=FALSE,$E5<>\"\",$E5<>0)", C["red_bg"]))
    # P&L negative profit red
    R.append(cf_text(4, 1, 14, 3, 4, "=$D2<0", C["red"]))
    R.append(cf_text(4, 1, 14, 3, 4, "=$D2>0", C["green"]))

    # ── CHARTS ──
    # Revenue vs Expenses grouped bar
    R.append({"addChart": {"chart": {
        "spec": {
            "title": "Revenue vs Expenses",
            "titleTextFormat": {"foregroundColorStyle": {"rgbColor": C["t2"]}, "fontSize": 11, "bold": True, "fontFamily": "Google Sans"},
            "backgroundColor": C["card"],
            "basicChart": {
                "chartType": "COLUMN",
                "legendPosition": "BOTTOM_LEGEND",
                "axis": [
                    {"position": "BOTTOM_AXIS", "format": {"foregroundColorStyle": {"rgbColor": C["t3"]}, "fontFamily": "Google Sans"}},
                    {"position": "LEFT_AXIS", "format": {"foregroundColorStyle": {"rgbColor": C["t3"]}, "fontFamily": "Google Sans"}},
                ],
                "domains": [{"domain": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 0, "endColumnIndex": 1}]}}}],
                "series": [
                    {"series": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 1, "endColumnIndex": 2}]}}, "color": C["blue"]},
                    {"series": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 2, "endColumnIndex": 3}]}}, "color": C["red"]},
                ],
                "headerCount": 1,
            }
        },
        "position": {"overlayPosition": {"anchorCell": {"sheetId": 4, "rowIndex": 16, "columnIndex": 0}, "widthPixels": 650, "heightPixels": 350}}
    }}})

    # Cumulative line chart
    R.append({"addChart": {"chart": {
        "spec": {
            "title": "Cumulative Revenue & Profit",
            "titleTextFormat": {"foregroundColorStyle": {"rgbColor": C["t2"]}, "fontSize": 11, "bold": True, "fontFamily": "Google Sans"},
            "backgroundColor": C["card"],
            "basicChart": {
                "chartType": "LINE",
                "legendPosition": "BOTTOM_LEGEND",
                "axis": [
                    {"position": "BOTTOM_AXIS", "format": {"foregroundColorStyle": {"rgbColor": C["t3"]}, "fontFamily": "Google Sans"}},
                    {"position": "LEFT_AXIS", "format": {"foregroundColorStyle": {"rgbColor": C["t3"]}, "fontFamily": "Google Sans"}},
                ],
                "domains": [{"domain": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 0, "endColumnIndex": 1}]}}}],
                "series": [
                    {"series": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 5, "endColumnIndex": 6}]}}, "color": C["blue"]},
                    {"series": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 6, "endColumnIndex": 7}]}}, "color": C["green"]},
                ],
                "headerCount": 1,
            }
        },
        "position": {"overlayPosition": {"anchorCell": {"sheetId": 4, "rowIndex": 16, "columnIndex": 6}, "widthPixels": 550, "heightPixels": 350}}
    }}})

    svc.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": R}).execute()
    print("Formatting applied.")

    # Save
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            content = f.read()
        # Replace old ID
        import re as _re
        content = _re.sub(r"FINANCE_SHEET_ID=.*", f"FINANCE_SHEET_ID={sid}", content)
        with open(env_path, "w") as f:
            f.write(content)

    print(f"\n→ {url}")
    return sid, url


# ═══════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════
def cw(sid, col, w):
    return {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": col, "endIndex": col+1}, "properties": {"pixelSize": w}, "fields": "pixelSize"}}

def rh(sid, row, h):
    return {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": row, "endIndex": row+1}, "properties": {"pixelSize": h}, "fields": "pixelSize"}}

def f_(sid, r1, r2, c1, c2, bold=False, size=10, fg=None, bg=None):
    cell = {"textFormat": {"bold": bold, "fontSize": size, "fontFamily": "Google Sans"}}
    if fg: cell["textFormat"]["foregroundColorStyle"] = {"rgbColor": fg}
    if bg: cell["backgroundColor"] = bg
    return {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}, "cell": {"userEnteredFormat": cell}, "fields": "userEnteredFormat(textFormat,backgroundColor)"}}

def nf(sid, r1, r2, c1, c2, pat):
    return {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}, "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": pat}}}, "fields": "userEnteredFormat.numberFormat"}}

def merge(sid, r1, r2, c1, c2):
    return {"mergeCells": {"range": {"sheetId": sid, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}, "mergeType": "MERGE_ALL"}}

def border_top(sid, row, c1, c2, color):
    return {"updateBorders": {"range": {"sheetId": sid, "startRowIndex": row, "endRowIndex": row+1, "startColumnIndex": c1, "endColumnIndex": c2}, "top": {"style": "SOLID_MEDIUM", "colorStyle": {"rgbColor": color}}}}

def border_bottom(sid, row, c1, c2, color):
    return {"updateBorders": {"range": {"sheetId": sid, "startRowIndex": row, "endRowIndex": row+1, "startColumnIndex": c1, "endColumnIndex": c2}, "bottom": {"style": "SOLID", "colorStyle": {"rgbColor": color}}}}

def dv_bool(sid, r1, r2, c1, c2):
    return {"setDataValidation": {"range": {"sheetId": sid, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}, "rule": {"condition": {"type": "BOOLEAN"}, "strict": True}}}

def dv_list(sid, r1, r2, c1, c2, vals):
    return {"setDataValidation": {"range": {"sheetId": sid, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}, "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in vals]}, "showCustomUi": True, "strict": False}}}

def cf(sid, r1, r2, c1, c2, formula, bg):
    return {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": formula}]}, "format": {"backgroundColor": bg}}}, "index": 0}}

def cf_text(sid, r1, r2, c1, c2, formula, fg):
    return {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": formula}]}, "format": {"textFormat": {"foregroundColorStyle": {"rgbColor": fg}}}}}, "index": 0}}


if __name__ == "__main__":
    sid, url = create()
