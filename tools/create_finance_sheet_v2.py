"""
Matt Anthony Photography — Ultimate Finance Tracker v2
Interactive, beautifully designed, tax-ready for CRA.
One entry point (Transactions tab) with auto-sorting everywhere else.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.google_sheets_auth import get_sheets_service, get_drive_service

YEAR = 2026

# ═══════════════════════════════════════════
# DESIGN SYSTEM
# ═══════════════════════════════════════════
# Palette — dark modern theme with accent colors
BG_DARK = {"red": 0.102, "green": 0.110, "blue": 0.122}       # #1A1C1F — main dark bg
BG_CARD = {"red": 0.145, "green": 0.153, "blue": 0.169}       # #252730 — card bg
BG_ROW_ALT = {"red": 0.165, "green": 0.173, "blue": 0.192}    # #2A2C31 — alternating row
BG_INPUT = {"red": 0.192, "green": 0.200, "blue": 0.220}      # #313338 — input fields
WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}
TEXT_PRIMARY = {"red": 0.933, "green": 0.937, "blue": 0.945}   # #EEEFF1
TEXT_SECONDARY = {"red": 0.600, "green": 0.616, "blue": 0.647} # #999DA5
TEXT_MUTED = {"red": 0.420, "green": 0.435, "blue": 0.463}     # #6B6F76

# Accent colors
BLUE = {"red": 0.235, "green": 0.478, "blue": 0.859}          # #3C7ADB
BLUE_SOFT = {"red": 0.180, "green": 0.290, "blue": 0.480}     # #2E4A7A
GREEN = {"red": 0.196, "green": 0.718, "blue": 0.486}         # #32B77C
GREEN_SOFT = {"red": 0.140, "green": 0.300, "blue": 0.220}    # #244D38
RED = {"red": 0.906, "green": 0.318, "blue": 0.318}           # #E75151
RED_SOFT = {"red": 0.380, "green": 0.160, "blue": 0.160}      # #612929
ORANGE = {"red": 0.949, "green": 0.608, "blue": 0.224}        # #F29B39
ORANGE_SOFT = {"red": 0.380, "green": 0.260, "blue": 0.120}   # #61421F
PURPLE = {"red": 0.545, "green": 0.365, "blue": 0.847}        # #8B5DD8
PURPLE_SOFT = {"red": 0.260, "green": 0.180, "blue": 0.400}   # #422E66

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# T2125 business categories
BIZ_CATEGORIES = [
    "Advertising & Marketing",
    "Professional Fees",
    "Vehicle",
    "Insurance",
    "Interest & Bank Charges",
    "Office Supplies (<$500)",
    "Rent / Co-working",
    "Software & Subscriptions",
    "Travel",
    "Telephone & Internet",
    "Subcontractors",
    "Meals & Entertainment",
    "Home Office",
    "Equipment (CCA)",
    "Other Business",
]

PERSONAL_CATEGORIES = [
    "Housing",
    "Utilities",
    "Groceries",
    "Dining Out",
    "Transportation",
    "Health & Fitness",
    "Subscriptions",
    "Clothing",
    "Entertainment",
    "Travel (Personal)",
    "Savings/Investments",
    "Other Personal",
]

ALL_CATEGORIES = BIZ_CATEGORIES + PERSONAL_CATEGORIES


def create_spreadsheet():
    sheets = get_sheets_service()

    tab_defs = [
        ("Dashboard", 0),
        ("Transactions", 1),
        ("Business Summary", 2),
        ("Personal Summary", 3),
        ("Monthly P&L", 4),
        ("GST-HST", 5),
        ("Mileage Log", 6),
        ("Equipment CCA", 7),
        ("Tax Summary", 8),
    ]

    sheet_props = []
    tab_colors = [BLUE, GREEN, ORANGE, PURPLE, BLUE, RED, TEXT_SECONDARY, GREEN, RED]
    for i, (name, _) in enumerate(tab_defs):
        props = {
            "properties": {
                "sheetId": i,
                "title": name,
                "index": i,
                "tabColorStyle": {"rgbColor": tab_colors[i]},
                "gridProperties": {
                    "frozenRowCount": 3 if name == "Transactions" else (0 if name == "Dashboard" else 1),
                    "rowCount": 1000 if name == "Transactions" else 500,
                    "columnCount": 20,
                }
            }
        }
        sheet_props.append(props)

    ss = sheets.spreadsheets().create(body={
        "properties": {
            "title": f"Matt Anthony — Finance {YEAR}",
            "locale": "en_CA",
            "defaultFormat": {
                "backgroundColor": BG_DARK,
                "textFormat": {
                    "foregroundColorStyle": {"rgbColor": TEXT_PRIMARY},
                    "fontFamily": "Inter",
                    "fontSize": 10,
                }
            }
        },
        "sheets": sheet_props
    }).execute()

    ss_id = ss["spreadsheetId"]
    ss_url = ss["spreadsheetUrl"]
    print(f"Created: {ss_url}")

    # ═══════════════════════════════════════════
    # TAB 1: TRANSACTIONS (The Main Entry Point)
    # ═══════════════════════════════════════════
    txn_data = [
        ["", "", "", "", "", "", "", "", "", "", "", ""],
        ["  TRANSACTIONS", "", "", "", "", "", "", "", "", "", f"  {YEAR} FINANCE TRACKER", ""],
        ["", "", "", "", "", "", "", "", "", "", "", ""],
        ["  Date", "  Vendor / Payee", "  Description", "  Amount", "  Business?", "  Category",
         "  Biz Split %", "  GST Included", "  Receipt?", "  Payment Method", "  Account", "  Notes"],
    ]
    # Pre-fill 500 rows with defaults
    for i in range(500):
        row_num = i + 5
        txn_data.append([
            "", "", "", "",
            False,  # Business? checkbox
            "",     # Category dropdown
            "100%", # Biz split default
            "",     # GST
            False,  # Receipt checkbox
            "",     # Payment method
            "",     # Account
            "",     # Notes
        ])

    # ═══════════════════════════════════════════
    # TAB 0: DASHBOARD
    # ═══════════════════════════════════════════
    dash_data = [
        ["", "", "", "", "", "", "", "", "", ""],
        [f"  FINANCE DASHBOARD", "", "", "", "", "", "", "", f"  {YEAR}", ""],
        ["  Matt Anthony Photography", "", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", "", ""],
        # ── KPI Row ──
        ["", "  REVENUE", "", "  EXPENSES", "", "  NET PROFIT", "", "  TAX OWING", "", ""],
        ["", "  YTD", "", "  YTD", "", "  YTD", "", "  Estimated", "", ""],
        ["",
         "=SUMPRODUCT((Transactions!E5:E1000=TRUE)*(Transactions!D5:D1000>0)*Transactions!D5:D1000)",
         "",
         "=SUMPRODUCT((Transactions!E5:E1000=TRUE)*(Transactions!D5:D1000<0)*ABS(Transactions!D5:D1000))",
         "",
         "=B7-D7",
         "",
         "='Tax Summary'!C44",
         "", ""],
        ["", "", "", "", "", "", "", "", "", ""],
        # ── Revenue Target ──
        ["", "  REVENUE TARGET", "", "", "", "  BUSINESS EXPENSES", "", "", "", ""],
        ["", "  Target", f"  {172900}", "  % Complete", "=IF(C10>0,B7/C10,0)",
         "  Software & Subs", "=SUMPRODUCT((Transactions!E5:E1000=TRUE)*(Transactions!D5:D1000<0)*(Transactions!F5:F1000=\"Software & Subscriptions\")*ABS(Transactions!D5:D1000))", "", "", ""],
        ["", "  Achieved", "=B7", "  Remaining", "=C10-C11",
         "  Travel", "=SUMPRODUCT((Transactions!E5:E1000=TRUE)*(Transactions!D5:D1000<0)*(Transactions!F5:F1000=\"Travel\")*ABS(Transactions!D5:D1000))", "", "", ""],
        ["", "  Monthly Avg", '=IF(MONTH(TODAY())>0,B7/MONTH(TODAY()),0)', "  Run Rate", "=C12*12",
         "  Advertising", "=SUMPRODUCT((Transactions!E5:E1000=TRUE)*(Transactions!D5:D1000<0)*(Transactions!F5:F1000=\"Advertising & Marketing\")*ABS(Transactions!D5:D1000))", "", "", ""],
        ["", "", "", "", "",
         "  Rent / Co-working", "=SUMPRODUCT((Transactions!E5:E1000=TRUE)*(Transactions!D5:D1000<0)*(Transactions!F5:F1000=\"Rent / Co-working\")*ABS(Transactions!D5:D1000))", "", "", ""],
        ["", "", "", "", "",
         "  Phone & Internet", "=SUMPRODUCT((Transactions!E5:E1000=TRUE)*(Transactions!D5:D1000<0)*(Transactions!F5:F1000=\"Telephone & Internet\")*ABS(Transactions!D5:D1000))", "", "", ""],
        ["", "", "", "", "", "", "", "", "", ""],
        # ── Monthly Trend ──
        ["", "  MONTHLY BREAKDOWN", "", "", "", "", "", "", "", ""],
        ["", "  Month", "  Revenue", "  Biz Expenses", "  Personal", "  Net Biz Profit", "  Margin", "", "", ""],
    ]
    for i, m in enumerate(MONTHS):
        mn = i + 1
        row = [
            "",
            f"  {m}",
            f'=SUMPRODUCT((Transactions!E5:E1000=TRUE)*(Transactions!D5:D1000>0)*(MONTH(DATEVALUE(Transactions!A5:A1000))={mn})*Transactions!D5:D1000)',
            f'=SUMPRODUCT((Transactions!E5:E1000=TRUE)*(Transactions!D5:D1000<0)*(MONTH(DATEVALUE(Transactions!A5:A1000))={mn})*ABS(Transactions!D5:D1000))',
            f'=SUMPRODUCT((Transactions!E5:E1000=FALSE)*(Transactions!D5:D1000<0)*(MONTH(DATEVALUE(Transactions!A5:A1000))={mn})*ABS(Transactions!D5:D1000))',
            f"=C{18+i}-D{18+i}",
            f"=IF(C{18+i}>0,F{18+i}/C{18+i},0)",
            "", "", ""
        ]
        dash_data.append(row)
    dash_data.append(["", "  TOTAL", "=SUM(C18:C29)", "=SUM(D18:D29)", "=SUM(E18:E29)", "=SUM(F18:F29)", "=IF(C30>0,F30/C30,0)", "", "", ""])
    dash_data.append(["", "", "", "", "", "", "", "", "", ""])
    # ── Personal spending section ──
    dash_data.append(["", "  PERSONAL SPENDING", "", "", "", "  GST SUMMARY", "", "", "", ""])
    dash_data.append(["", "  Dining Out",
                      "=SUMPRODUCT((Transactions!E5:E1000=FALSE)*(Transactions!D5:D1000<0)*(Transactions!F5:F1000=\"Dining Out\")*ABS(Transactions!D5:D1000))",
                      "", "",
                      "  GST Collected (on sales)", "=SUMPRODUCT((Transactions!E5:E1000=TRUE)*(Transactions!D5:D1000>0)*Transactions!H5:H1000)", "", "", ""])
    dash_data.append(["", "  Groceries",
                      "=SUMPRODUCT((Transactions!E5:E1000=FALSE)*(Transactions!D5:D1000<0)*(Transactions!F5:F1000=\"Groceries\")*ABS(Transactions!D5:D1000))",
                      "", "",
                      "  ITCs (GST on biz purchases)", "=SUMPRODUCT((Transactions!E5:E1000=TRUE)*(Transactions!D5:D1000<0)*Transactions!H5:H1000)", "", "", ""])
    dash_data.append(["", "  Health & Fitness",
                      "=SUMPRODUCT((Transactions!E5:E1000=FALSE)*(Transactions!D5:D1000<0)*(Transactions!F5:F1000=\"Health & Fitness\")*ABS(Transactions!D5:D1000))",
                      "", "",
                      "  Net GST Owing", "=G33-G34", "", "", ""])
    dash_data.append(["", "  Subscriptions",
                      "=SUMPRODUCT((Transactions!E5:E1000=FALSE)*(Transactions!D5:D1000<0)*(Transactions!F5:F1000=\"Subscriptions\")*ABS(Transactions!D5:D1000))",
                      "", "", "", "", "", "", ""])
    dash_data.append(["", "  Entertainment / Travel",
                      "=SUMPRODUCT((Transactions!E5:E1000=FALSE)*(Transactions!D5:D1000<0)*((Transactions!F5:F1000=\"Entertainment\")+(Transactions!F5:F1000=\"Travel (Personal)\"))*ABS(Transactions!D5:D1000))",
                      "", "", "", "", "", "", ""])

    # ═══════════════════════════════════════════
    # TAB 2: BUSINESS SUMMARY
    # ═══════════════════════════════════════════
    biz_data = [
        ["  T2125 CATEGORY", "  CRA Line", "  YTD Total"] + [f"  {m}" for m in MONTHS],
    ]
    t2125_lines = {
        "Advertising & Marketing": "8521",
        "Professional Fees": "8590",
        "Vehicle": "8615",
        "Insurance": "8690",
        "Interest & Bank Charges": "8710",
        "Office Supplies (<$500)": "8811",
        "Rent / Co-working": "8860",
        "Software & Subscriptions": "8871",
        "Travel": "8910",
        "Telephone & Internet": "8945",
        "Subcontractors": "9060",
        "Meals & Entertainment": "9270",
        "Home Office": "9281",
        "Equipment (CCA)": "9936",
        "Other Business": "9270",
    }
    for cat in BIZ_CATEGORIES:
        line = t2125_lines.get(cat, "")
        row = [f"  {cat}", f"  {line}",
               f"=SUM(D{len(biz_data)+1}:O{len(biz_data)+1})"]
        for mn in range(1, 13):
            row.append(
                f'=SUMPRODUCT((Transactions!E$5:E$1000=TRUE)*(Transactions!D$5:D$1000<0)*(Transactions!F$5:F$1000="{cat}")*(MONTH(DATEVALUE(Transactions!A$5:A$1000))={mn})*ABS(Transactions!D$5:D$1000))'
            )
        biz_data.append(row)
    # Total row
    biz_data.append(["", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
    total_row_num = len(biz_data) + 1
    biz_data.append(["  TOTAL BUSINESS EXPENSES", "", f"=SUM(C2:C{total_row_num-2})"] +
                    [f"=SUM({chr(ord('D')+i)}2:{chr(ord('D')+i)}{total_row_num-2})" for i in range(12)])

    # ═══════════════════════════════════════════
    # TAB 3: PERSONAL SUMMARY
    # ═══════════════════════════════════════════
    pers_data = [
        ["  CATEGORY", "  YTD Total"] + [f"  {m}" for m in MONTHS],
    ]
    for cat in PERSONAL_CATEGORIES:
        row = [f"  {cat}", f"=SUM(C{len(pers_data)+1}:N{len(pers_data)+1})"]
        for mn in range(1, 13):
            row.append(
                f'=SUMPRODUCT((Transactions!E$5:E$1000=FALSE)*(Transactions!D$5:D$1000<0)*(Transactions!F$5:F$1000="{cat}")*(MONTH(DATEVALUE(Transactions!A$5:A$1000))={mn})*ABS(Transactions!D$5:D$1000))'
            )
        pers_data.append(row)
    pers_data.append(["", "", "", "", "", "", "", "", "", "", "", "", "", ""])
    p_total_row = len(pers_data) + 1
    pers_data.append(["  TOTAL PERSONAL", f"=SUM(B2:B{p_total_row-2})"] +
                     [f"=SUM({chr(ord('C')+i)}2:{chr(ord('C')+i)}{p_total_row-2})" for i in range(12)])

    # ═══════════════════════════════════════════
    # TAB 4: MONTHLY P&L
    # ═══════════════════════════════════════════
    pnl_data = [
        ["  MONTH", "  Revenue", "  COGS/Expenses", "  Gross Profit", "  Margin %", "  Cumulative Rev", "  Cumulative Profit", "  vs Target"],
    ]
    for i, m in enumerate(MONTHS):
        r = i + 2
        pnl_data.append([
            f"  {m}",
            f"='Dashboard'!C{18+i}", f"='Dashboard'!D{18+i}",
            f"=B{r}-C{r}", f"=IF(B{r}>0,D{r}/B{r},0)",
            f"=SUM(B$2:B{r})", f"=SUM(D$2:D{r})",
            f"=F{r}-({172900}/12*{i+1})",
        ])
    pnl_data.append(["", "", "", "", "", "", "", ""])
    pnl_data.append(["  TOTAL", "=SUM(B2:B13)", "=SUM(C2:C13)", "=SUM(D2:D13)",
                     "=IF(B15>0,D15/B15,0)", "", "", ""])

    # ═══════════════════════════════════════════
    # TAB 5: GST-HST
    # ═══════════════════════════════════════════
    gst_data = [
        ["  GST/HST TRACKER — 5% (BC)", "", "", "", "", "", ""],
        ["", "", "", "", "", "", ""],
        ["", "  Q1 (Jan–Mar)", "  Q2 (Apr–Jun)", "  Q3 (Jul–Sep)", "  Q4 (Oct–Dec)", "  YTD TOTAL", ""],
        ["  GST Collected",
         "=SUMPRODUCT((Transactions!E$5:E$1000=TRUE)*(Transactions!D$5:D$1000>0)*((MONTH(DATEVALUE(Transactions!A$5:A$1000))>=1)*(MONTH(DATEVALUE(Transactions!A$5:A$1000))<=3))*Transactions!H$5:H$1000)",
         "=SUMPRODUCT((Transactions!E$5:E$1000=TRUE)*(Transactions!D$5:D$1000>0)*((MONTH(DATEVALUE(Transactions!A$5:A$1000))>=4)*(MONTH(DATEVALUE(Transactions!A$5:A$1000))<=6))*Transactions!H$5:H$1000)",
         "=SUMPRODUCT((Transactions!E$5:E$1000=TRUE)*(Transactions!D$5:D$1000>0)*((MONTH(DATEVALUE(Transactions!A$5:A$1000))>=7)*(MONTH(DATEVALUE(Transactions!A$5:A$1000))<=9))*Transactions!H$5:H$1000)",
         "=SUMPRODUCT((Transactions!E$5:E$1000=TRUE)*(Transactions!D$5:D$1000>0)*((MONTH(DATEVALUE(Transactions!A$5:A$1000))>=10)*(MONTH(DATEVALUE(Transactions!A$5:A$1000))<=12))*Transactions!H$5:H$1000)",
         "=SUM(B4:E4)", ""],
        ["  ITCs (GST Paid)",
         "=SUMPRODUCT((Transactions!E$5:E$1000=TRUE)*(Transactions!D$5:D$1000<0)*((MONTH(DATEVALUE(Transactions!A$5:A$1000))>=1)*(MONTH(DATEVALUE(Transactions!A$5:A$1000))<=3))*Transactions!H$5:H$1000)",
         "=SUMPRODUCT((Transactions!E$5:E$1000=TRUE)*(Transactions!D$5:D$1000<0)*((MONTH(DATEVALUE(Transactions!A$5:A$1000))>=4)*(MONTH(DATEVALUE(Transactions!A$5:A$1000))<=6))*Transactions!H$5:H$1000)",
         "=SUMPRODUCT((Transactions!E$5:E$1000=TRUE)*(Transactions!D$5:D$1000<0)*((MONTH(DATEVALUE(Transactions!A$5:A$1000))>=7)*(MONTH(DATEVALUE(Transactions!A$5:A$1000))<=9))*Transactions!H$5:H$1000)",
         "=SUMPRODUCT((Transactions!E$5:E$1000=TRUE)*(Transactions!D$5:D$1000<0)*((MONTH(DATEVALUE(Transactions!A$5:A$1000))>=10)*(MONTH(DATEVALUE(Transactions!A$5:A$1000))<=12))*Transactions!H$5:H$1000)",
         "=SUM(B5:E5)", ""],
        ["  NET GST OWING", "=B4-B5", "=C4-C5", "=D4-D5", "=E4-E5", "=SUM(B6:E6)", ""],
        ["", "", "", "", "", "", ""],
        ["  Due Dates:", "  Apr 30", "  Jul 31", "  Oct 31", "  Jan 31", "", ""],
        ["  Filed?", "", "", "", "", "", ""],
        ["  Payment Date", "", "", "", "", "", ""],
        ["", "", "", "", "", "", ""],
        ["  GST Registration #:", "", "", "", "", "", ""],
        ["  Filing Frequency:", "  Quarterly", "", "", "", "", ""],
    ]

    # ═══════════════════════════════════════════
    # TAB 6: MILEAGE LOG
    # ═══════════════════════════════════════════
    mile_data = [
        ["  Date", "  From", "  To", "  Client / Purpose", "  KM", "  Type", "  Notes"],
        ["", "", "", "", "", "", ""],
    ]
    for _ in range(200):
        mile_data.append(["", "", "", "", "", "", ""])
    # Summary at top — we'll put it in a separate area
    mile_summary = [
        ["", "", "", "", "", "", "", "", "  MILEAGE SUMMARY"],
        ["", "", "", "", "", "", "", "", "  Total KM"],
        ["", "", "", "", "", "", "", "", "=SUM(E2:E201)"],
        ["", "", "", "", "", "", "", "", "  Business KM"],
        ["", "", "", "", "", "", "", "", '=SUMIF(F2:F201,"Business",E2:E201)'],
        ["", "", "", "", "", "", "", "", "  Business %"],
        ["", "", "", "", "", "", "", "", "=IF(I3>0,I5/I3,0)"],
        ["", "", "", "", "", "", "", "", "  CRA Deduction"],
        ["", "", "", "", "", "", "", "", "=IF(I5<=5000,I5*0.72,5000*0.72+(I5-5000)*0.66)"],
    ]

    # ═══════════════════════════════════════════
    # TAB 7: EQUIPMENT CCA
    # ═══════════════════════════════════════════
    cca_data = [
        ["  Asset", "  Date Acquired", "  CCA Class", "  Rate", "  Cost", "  UCC Start", "  CCA Claimed", "  UCC End", "  Notes"],
    ]
    for i in range(30):
        r = i + 2
        cca_data.append(["", "", "", "", "", "", f"=IF(F{r}>0,F{r}*D{r},\"\")", f"=IF(F{r}>0,F{r}-G{r},\"\")", ""])
    cca_data.append(["", "", "", "", "", "", "", "", ""])
    cca_data.append(["  TOTALS", "", "", "", f"=SUM(E2:E31)", f"=SUM(F2:F31)", f"=SUM(G2:G31)", f"=SUM(H2:H31)", ""])

    # ═══════════════════════════════════════════
    # TAB 8: TAX SUMMARY
    # ═══════════════════════════════════════════
    tax_data = [
        ["", "  T2125 — STATEMENT OF BUSINESS INCOME", "", ""],
        ["", "", "", ""],
        ["", "  LINE ITEM", "  AMOUNT", "  CRA LINE"],
        ["", "", "", ""],
        ["", "  Gross Business Income", "=SUMPRODUCT((Transactions!E5:E1000=TRUE)*(Transactions!D5:D1000>0)*Transactions!D5:D1000)", "  8299"],
        ["", "", "", ""],
        ["", "  EXPENSES", "", ""],
        ["", "  Advertising & Marketing", "='Business Summary'!C2", "  8521"],
        ["", "  Professional Fees", "='Business Summary'!C3", "  8590"],
        ["", "  Vehicle Expenses", "='Business Summary'!C4", "  8615"],
        ["", "  Insurance", "='Business Summary'!C5", "  8690"],
        ["", "  Interest & Bank Charges", "='Business Summary'!C6", "  8710"],
        ["", "  Office Supplies", "='Business Summary'!C7", "  8811"],
        ["", "  Rent / Co-working", "='Business Summary'!C8", "  8860"],
        ["", "  Software & Subscriptions", "='Business Summary'!C9", "  8871"],
        ["", "  Travel", "='Business Summary'!C10", "  8910"],
        ["", "  Telephone & Internet", "='Business Summary'!C11", "  8945"],
        ["", "  Subcontractors", "='Business Summary'!C12", "  9060"],
        ["", "  Meals & Entertainment (50%)", "='Business Summary'!C13*0.5", "  9270"],
        ["", "  Home Office", "='Business Summary'!C14", "  9281"],
        ["", "  CCA", "='Equipment CCA'!G33", "  9936"],
        ["", "  Other", "='Business Summary'!C16", "  —"],
        ["", "", "", ""],
        ["", "  Total Expenses", "=SUM(C8:C22)", "  9369"],
        ["", "", "", ""],
        ["", "  NET BUSINESS INCOME", "=C5-C24", "  9946"],
        ["", "", "", ""],
        ["", "  INCOME TAX ESTIMATE", "", ""],
        ["", "", "", ""],
        ["", "  Federal Tax", "=IF(C26<=57375,C26*0.15,57375*0.15+(C26-57375)*0.205)", ""],
        ["", "  Basic Personal Credit", -2506, ""],
        ["", "  Federal After Credits", "=MAX(0,C30+C31)", ""],
        ["", "", "", ""],
        ["", "  BC Provincial Tax", "=IF(C26<=47937,C26*0.0506,47937*0.0506+(C26-47937)*0.077)", ""],
        ["", "  BC Personal Credit", -596, ""],
        ["", "  BC After Credits", "=MAX(0,C34+C35)", ""],
        ["", "", "", ""],
        ["", "  TOTAL INCOME TAX", "=C32+C36", ""],
        ["", "", "", ""],
        ["", "  CPP SELF-EMPLOYMENT", "", ""],
        ["", "  CPP Base", "=IF(C26>3500,MIN((C26-3500)*0.119,7735.50),0)", ""],
        ["", "  CPP2", "=IF(C26>73200,MIN((C26-73200)*0.08,396),0)", ""],
        ["", "  Total CPP", "=C41+C42", ""],
        ["", "", "", ""],
        ["", "  TOTAL TAX + CPP", "=C38+C43", ""],
        ["", "  Quarterly Installment", "=C44/4", ""],
        ["", "", "", ""],
        ["", "  RRSP Room (18%)", "=MIN(C26*0.18,32490)", ""],
        ["", "  RRSP Contribution", "", "  Enter actual"],
        ["", "  RRSP Tax Savings", "=C49*0.30", "  ~30% marginal"],
    ]

    # ═══════════════════════════════════════════
    # WRITE ALL DATA
    # ═══════════════════════════════════════════
    data_updates = [
        {"range": f"Transactions!A1:L{len(txn_data)}", "values": txn_data},
        {"range": f"Dashboard!A1:J{len(dash_data)}", "values": dash_data},
        {"range": f"'Business Summary'!A1:O{len(biz_data)}", "values": biz_data},
        {"range": f"'Personal Summary'!A1:N{len(pers_data)}", "values": pers_data},
        {"range": f"'Monthly P&L'!A1:H{len(pnl_data)}", "values": pnl_data},
        {"range": f"'GST-HST'!A1:G{len(gst_data)}", "values": gst_data},
        {"range": f"'Mileage Log'!A1:G{len(mile_data)}", "values": mile_data},
        {"range": f"'Mileage Log'!I1:I{len(mile_summary)}", "values": [[r[8]] for r in mile_summary]},
        {"range": f"'Equipment CCA'!A1:I{len(cca_data)}", "values": cca_data},
        {"range": f"'Tax Summary'!A1:D{len(tax_data)}", "values": tax_data},
    ]

    sheets.spreadsheets().values().batchUpdate(
        spreadsheetId=ss_id,
        body={"valueInputOption": "USER_ENTERED", "data": data_updates}
    ).execute()
    print("All data written.")

    # ═══════════════════════════════════════════
    # FORMATTING & INTERACTIVITY
    # ═══════════════════════════════════════════
    reqs = []

    # ── Column widths ──
    # Transactions tab
    txn_col_widths = [110, 220, 200, 110, 90, 200, 90, 110, 80, 130, 120, 200]
    for i, w in enumerate(txn_col_widths):
        reqs.append(col_width(1, i, w))

    # Dashboard
    dash_col_widths = [20, 180, 130, 130, 130, 180, 150, 150, 120, 20]
    for i, w in enumerate(dash_col_widths):
        reqs.append(col_width(0, i, w))

    # Business Summary
    for i in range(15):
        reqs.append(col_width(2, i, 130 if i > 1 else (250 if i == 0 else 80)))

    # ── Row heights ──
    reqs.append(row_height(1, 0, 15))   # Spacer
    reqs.append(row_height(1, 1, 45))   # Title
    reqs.append(row_height(1, 2, 10))   # Spacer
    reqs.append(row_height(1, 3, 36))   # Header

    reqs.append(row_height(0, 0, 15))
    reqs.append(row_height(0, 1, 50))
    reqs.append(row_height(0, 2, 25))
    reqs.append(row_height(0, 3, 15))
    reqs.append(row_height(0, 4, 30))
    reqs.append(row_height(0, 5, 20))
    reqs.append(row_height(0, 6, 45))
    reqs.append(row_height(0, 7, 15))

    # ── TRANSACTIONS TAB FORMATTING ──
    # Title bar
    reqs.append(fmt(1, 1, 2, 0, 12, bold=True, size=18, fg=WHITE, bg=BG_CARD))
    # Header row
    reqs.append(fmt(1, 3, 4, 0, 12, bold=True, size=10, fg=TEXT_SECONDARY, bg=BG_CARD))
    # Alternating rows for data area
    for r in range(4, 504):
        bg = BG_ROW_ALT if r % 2 == 0 else BG_DARK
        reqs.append(fmt(1, r, r+1, 0, 12, bg=bg))
    # Input field backgrounds
    for r in range(4, 504):
        reqs.append(fmt(1, r, r+1, 0, 4, bg=BG_INPUT))  # Date, Vendor, Desc, Amount inputs

    # ── DASHBOARD FORMATTING ──
    reqs.append(merge(0, 1, 2, 1, 7))  # Title
    reqs.append(fmt(0, 1, 2, 1, 7, bold=True, size=22, fg=WHITE, bg=BG_DARK))
    reqs.append(fmt(0, 2, 3, 1, 7, size=11, fg=TEXT_MUTED, bg=BG_DARK))

    # KPI cards
    kpi_positions = [(1, 2), (3, 4), (5, 6), (7, 8)]
    kpi_colors = [BLUE_SOFT, RED_SOFT, GREEN_SOFT, ORANGE_SOFT]
    kpi_fg = [BLUE, RED, GREEN, ORANGE]
    for (c1, c2), bg_color, fg_color in zip(kpi_positions, kpi_colors, kpi_fg):
        reqs.append(fmt(0, 4, 5, c1, c2+1, bold=True, size=10, fg=TEXT_SECONDARY, bg=bg_color))
        reqs.append(fmt(0, 5, 6, c1, c2+1, size=9, fg=TEXT_MUTED, bg=bg_color))
        reqs.append(fmt(0, 6, 7, c1, c2+1, bold=True, size=20, fg=fg_color, bg=bg_color))
    # KPI borders
    for (c1, c2), bg_color in zip(kpi_positions, kpi_colors):
        reqs.append(border_bottom(0, 6, c1, c2+1, kpi_fg[kpi_positions.index((c1,c2))]))

    # Revenue target section
    reqs.append(fmt(0, 8, 9, 1, 5, bold=True, size=12, fg=WHITE, bg=BG_DARK))
    reqs.append(fmt(0, 8, 9, 5, 9, bold=True, size=12, fg=WHITE, bg=BG_DARK))
    for r in range(9, 14):
        reqs.append(fmt(0, r, r+1, 1, 5, size=10, fg=TEXT_PRIMARY, bg=BG_CARD))
        reqs.append(fmt(0, r, r+1, 5, 9, size=10, fg=TEXT_PRIMARY, bg=BG_CARD))

    # Monthly breakdown header
    reqs.append(fmt(0, 16, 17, 1, 9, bold=True, size=12, fg=WHITE, bg=BG_DARK))
    reqs.append(fmt(0, 17, 18, 1, 9, bold=True, size=9, fg=TEXT_SECONDARY, bg=BG_CARD))
    # Monthly rows
    for r in range(18, 30):
        bg = BG_CARD if r % 2 == 0 else BG_ROW_ALT
        reqs.append(fmt(0, r, r+1, 1, 9, size=10, fg=TEXT_PRIMARY, bg=bg))
    # Total row
    reqs.append(fmt(0, 29, 30, 1, 9, bold=True, size=11, fg=WHITE, bg=BLUE_SOFT))

    # Personal + GST section
    reqs.append(fmt(0, 31, 32, 1, 5, bold=True, size=12, fg=WHITE, bg=BG_DARK))
    reqs.append(fmt(0, 31, 32, 5, 9, bold=True, size=12, fg=WHITE, bg=BG_DARK))
    for r in range(32, 38):
        reqs.append(fmt(0, r, r+1, 1, 5, size=10, fg=TEXT_PRIMARY, bg=BG_CARD))
        reqs.append(fmt(0, r, r+1, 5, 9, size=10, fg=TEXT_PRIMARY, bg=BG_CARD))

    # ── BUSINESS SUMMARY FORMATTING ──
    reqs.append(fmt(2, 0, 1, 0, 15, bold=True, size=10, fg=TEXT_SECONDARY, bg=BG_CARD))
    for r in range(1, len(biz_data)):
        bg = BG_CARD if r % 2 == 0 else BG_ROW_ALT
        reqs.append(fmt(2, r, r+1, 0, 15, size=10, fg=TEXT_PRIMARY, bg=bg))
    # Total row
    reqs.append(fmt(2, len(biz_data)-1, len(biz_data), 0, 15, bold=True, size=11, fg=ORANGE, bg=BG_CARD))

    # ── PERSONAL SUMMARY FORMATTING ──
    reqs.append(fmt(3, 0, 1, 0, 14, bold=True, size=10, fg=TEXT_SECONDARY, bg=BG_CARD))
    for r in range(1, len(pers_data)):
        bg = BG_CARD if r % 2 == 0 else BG_ROW_ALT
        reqs.append(fmt(3, r, r+1, 0, 14, size=10, fg=TEXT_PRIMARY, bg=bg))
    reqs.append(fmt(3, len(pers_data)-1, len(pers_data), 0, 14, bold=True, size=11, fg=PURPLE, bg=BG_CARD))

    # ── MONTHLY P&L FORMATTING ──
    reqs.append(fmt(4, 0, 1, 0, 8, bold=True, size=10, fg=TEXT_SECONDARY, bg=BG_CARD))
    for r in range(1, 13):
        bg = BG_CARD if r % 2 == 0 else BG_ROW_ALT
        reqs.append(fmt(4, r, r+1, 0, 8, size=10, fg=TEXT_PRIMARY, bg=bg))
    reqs.append(fmt(4, 14, 15, 0, 8, bold=True, size=11, fg=BLUE, bg=BG_CARD))

    # ── GST TAB FORMATTING ──
    reqs.append(fmt(5, 0, 1, 0, 7, bold=True, size=14, fg=WHITE, bg=BG_CARD))
    reqs.append(fmt(5, 2, 3, 0, 7, bold=True, size=10, fg=TEXT_SECONDARY, bg=BG_CARD))
    for r in [3, 4, 5]:
        reqs.append(fmt(5, r, r+1, 0, 7, size=11, fg=TEXT_PRIMARY, bg=BG_ROW_ALT if r != 5 else RED_SOFT))
    reqs.append(fmt(5, 5, 6, 0, 7, bold=True, size=12, fg=RED, bg=RED_SOFT))

    # ── TAX SUMMARY FORMATTING ──
    reqs.append(fmt(8, 0, 1, 0, 4, bold=True, size=14, fg=WHITE, bg=BG_CARD))
    reqs.append(fmt(8, 2, 3, 0, 4, bold=True, size=10, fg=TEXT_SECONDARY, bg=BG_CARD))
    reqs.append(fmt(8, 4, 5, 1, 3, bold=True, size=12, fg=GREEN, bg=GREEN_SOFT))  # Revenue
    reqs.append(fmt(8, 25, 26, 1, 3, bold=True, size=14, fg=GREEN, bg=GREEN_SOFT))  # Net income
    reqs.append(fmt(8, 43, 44, 1, 3, bold=True, size=14, fg=RED, bg=RED_SOFT))  # Total tax
    reqs.append(fmt(8, 44, 45, 1, 3, bold=True, size=11, fg=ORANGE, bg=ORANGE_SOFT))  # Quarterly

    # ── NUMBER FORMATS ──
    # Currency on Transactions amount
    reqs.append(num_fmt(1, 4, 504, 3, 4, "$#,##0.00"))
    reqs.append(num_fmt(1, 4, 504, 7, 8, "$#,##0.00"))
    # Currency on Dashboard
    reqs.append(num_fmt(0, 6, 7, 1, 9, "$#,##0"))
    reqs.append(num_fmt(0, 9, 14, 2, 8, "$#,##0"))
    reqs.append(num_fmt(0, 18, 31, 2, 6, "$#,##0"))
    reqs.append(num_fmt(0, 32, 38, 2, 4, "$#,##0"))
    reqs.append(num_fmt(0, 32, 38, 6, 8, "$#,##0"))
    # Percentage
    reqs.append(num_fmt(0, 10, 11, 4, 5, "0.0%"))
    reqs.append(num_fmt(0, 18, 31, 6, 7, "0.0%"))
    # Currency on summaries
    reqs.append(num_fmt(2, 1, 20, 2, 15, "$#,##0.00"))
    reqs.append(num_fmt(3, 1, 16, 1, 14, "$#,##0.00"))
    reqs.append(num_fmt(4, 1, 16, 1, 4, "$#,##0.00"))
    reqs.append(num_fmt(4, 1, 16, 5, 8, "$#,##0.00"))
    reqs.append(num_fmt(4, 1, 16, 4, 5, "0.0%"))
    reqs.append(num_fmt(5, 3, 7, 1, 6, "$#,##0.00"))
    reqs.append(num_fmt(8, 4, 50, 2, 3, "$#,##0.00"))

    # ── DATA VALIDATION ──
    # Business? checkbox (column E)
    reqs.append({
        "setDataValidation": {
            "range": {"sheetId": 1, "startRowIndex": 4, "endRowIndex": 504, "startColumnIndex": 4, "endColumnIndex": 5},
            "rule": {"condition": {"type": "BOOLEAN"}, "strict": True}
        }
    })
    # Receipt? checkbox (column I)
    reqs.append({
        "setDataValidation": {
            "range": {"sheetId": 1, "startRowIndex": 4, "endRowIndex": 504, "startColumnIndex": 8, "endColumnIndex": 9},
            "rule": {"condition": {"type": "BOOLEAN"}, "strict": True}
        }
    })
    # Category dropdown (column F)
    reqs.append({
        "setDataValidation": {
            "range": {"sheetId": 1, "startRowIndex": 4, "endRowIndex": 504, "startColumnIndex": 5, "endColumnIndex": 6},
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": c} for c in ALL_CATEGORIES]
                },
                "showCustomUi": True,
                "strict": False,
            }
        }
    })
    # Payment method dropdown (column J)
    reqs.append({
        "setDataValidation": {
            "range": {"sheetId": 1, "startRowIndex": 4, "endRowIndex": 504, "startColumnIndex": 9, "endColumnIndex": 10},
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": v} for v in ["Visa", "Debit", "E-Transfer", "Cash", "PayPal", "Other"]]
                },
                "showCustomUi": True,
                "strict": False,
            }
        }
    })
    # Account dropdown (column K)
    reqs.append({
        "setDataValidation": {
            "range": {"sheetId": 1, "startRowIndex": 4, "endRowIndex": 504, "startColumnIndex": 10, "endColumnIndex": 11},
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": v} for v in ["Personal Card", "Business Account", "Personal Account", "Cash"]]
                },
                "showCustomUi": True,
                "strict": False,
            }
        }
    })
    # Biz Split % dropdown (column G)
    reqs.append({
        "setDataValidation": {
            "range": {"sheetId": 1, "startRowIndex": 4, "endRowIndex": 504, "startColumnIndex": 6, "endColumnIndex": 7},
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": v} for v in ["100%", "75%", "50%", "25%", "0%"]]
                },
                "showCustomUi": True,
                "strict": False,
            }
        }
    })
    # Mileage type dropdown
    reqs.append({
        "setDataValidation": {
            "range": {"sheetId": 6, "startRowIndex": 1, "endRowIndex": 201, "startColumnIndex": 5, "endColumnIndex": 6},
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": v} for v in ["Business", "Personal"]]
                },
                "showCustomUi": True,
                "strict": False,
            }
        }
    })

    # ── CONDITIONAL FORMATTING ──
    # Green row when Business=TRUE on Transactions
    reqs.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": 1, "startRowIndex": 4, "endRowIndex": 504, "startColumnIndex": 0, "endColumnIndex": 12}],
                "booleanRule": {
                    "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=$E5=TRUE"}]},
                    "format": {"backgroundColor": GREEN_SOFT}
                }
            },
            "index": 0
        }
    })
    # Red text for negative amounts (expenses)
    reqs.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": 1, "startRowIndex": 4, "endRowIndex": 504, "startColumnIndex": 3, "endColumnIndex": 4}],
                "booleanRule": {
                    "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=$D5<0"}]},
                    "format": {"textFormat": {"foregroundColorStyle": {"rgbColor": RED}}}
                }
            },
            "index": 1
        }
    })
    # Green text for positive amounts (income)
    reqs.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": 1, "startRowIndex": 4, "endRowIndex": 504, "startColumnIndex": 3, "endColumnIndex": 4}],
                "booleanRule": {
                    "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=$D5>0"}]},
                    "format": {"textFormat": {"foregroundColorStyle": {"rgbColor": GREEN}}}
                }
            },
            "index": 2
        }
    })
    # Highlight missing receipt on business transactions
    reqs.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": 1, "startRowIndex": 4, "endRowIndex": 504, "startColumnIndex": 8, "endColumnIndex": 9}],
                "booleanRule": {
                    "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND($E5=TRUE,$I5=FALSE,$D5<>0,$D5<>\"\")"}]},
                    "format": {"backgroundColor": RED_SOFT}
                }
            },
            "index": 3
        }
    })

    # ── CHARTS ──
    # Revenue vs Expenses monthly bar chart
    reqs.append({
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Monthly Revenue vs Expenses",
                    "titleTextFormat": {"foregroundColorStyle": {"rgbColor": TEXT_PRIMARY}, "fontSize": 12, "bold": True},
                    "backgroundColor": BG_CARD,
                    "basicChart": {
                        "chartType": "COLUMN",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {"position": "BOTTOM_AXIS", "title": "", "format": {"foregroundColorStyle": {"rgbColor": TEXT_SECONDARY}}},
                            {"position": "LEFT_AXIS", "title": "", "format": {"foregroundColorStyle": {"rgbColor": TEXT_SECONDARY}}},
                        ],
                        "domains": [{"domain": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 0, "endColumnIndex": 1}]}}}],
                        "series": [
                            {"series": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 1, "endColumnIndex": 2}]}},
                             "color": BLUE, "targetAxis": "LEFT_AXIS"},
                            {"series": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 2, "endColumnIndex": 3}]}},
                             "color": RED, "targetAxis": "LEFT_AXIS"},
                        ],
                        "headerCount": 1,
                    }
                },
                "position": {"overlayPosition": {"anchorCell": {"sheetId": 0, "rowIndex": 4, "columnIndex": 10}, "widthPixels": 550, "heightPixels": 320}}
            }
        }
    })

    # Cumulative revenue line chart
    reqs.append({
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Cumulative Profit",
                    "titleTextFormat": {"foregroundColorStyle": {"rgbColor": TEXT_PRIMARY}, "fontSize": 12, "bold": True},
                    "backgroundColor": BG_CARD,
                    "basicChart": {
                        "chartType": "LINE",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {"position": "BOTTOM_AXIS", "format": {"foregroundColorStyle": {"rgbColor": TEXT_SECONDARY}}},
                            {"position": "LEFT_AXIS", "format": {"foregroundColorStyle": {"rgbColor": TEXT_SECONDARY}}},
                        ],
                        "domains": [{"domain": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 0, "endColumnIndex": 1}]}}}],
                        "series": [
                            {"series": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 5, "endColumnIndex": 6}]}},
                             "color": BLUE},
                            {"series": {"sourceRange": {"sources": [{"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 6, "endColumnIndex": 7}]}},
                             "color": GREEN},
                        ],
                        "headerCount": 1,
                    }
                },
                "position": {"overlayPosition": {"anchorCell": {"sheetId": 0, "rowIndex": 20, "columnIndex": 10}, "widthPixels": 550, "heightPixels": 320}}
            }
        }
    })

    # Execute all formatting
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=ss_id,
        body={"requests": reqs}
    ).execute()
    print("Formatting, interactivity, and charts applied.")

    # Save ID
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            content = f.read()
        content = content.replace(
            f"FINANCE_SHEET_ID=170BPV2tw3uFCuutaxw2lnIXYG-9vmOIbUzbp5n7ey8g",
            f"FINANCE_SHEET_ID={ss_id}"
        )
        with open(env_path, "w") as f:
            f.write(content)

    print(f"\nDone! → {ss_url}")
    return ss_id, ss_url


# ═══════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════
def col_width(sheet_id, col, width):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": col, "endIndex": col + 1},
        "properties": {"pixelSize": width}, "fields": "pixelSize"
    }}

def row_height(sheet_id, row, height):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": row, "endIndex": row + 1},
        "properties": {"pixelSize": height}, "fields": "pixelSize"
    }}

def fmt(sheet_id, r1, r2, c1, c2, bold=False, size=10, fg=None, bg=None):
    cell_fmt = {"textFormat": {"bold": bold, "fontSize": size, "fontFamily": "Inter"}}
    if fg:
        cell_fmt["textFormat"]["foregroundColorStyle"] = {"rgbColor": fg}
    if bg:
        cell_fmt["backgroundColor"] = bg
    return {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2},
        "cell": {"userEnteredFormat": cell_fmt},
        "fields": "userEnteredFormat(textFormat,backgroundColor)"
    }}

def num_fmt(sheet_id, r1, r2, c1, c2, pattern):
    return {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": pattern}}},
        "fields": "userEnteredFormat.numberFormat"
    }}

def merge(sheet_id, r1, r2, c1, c2):
    return {"mergeCells": {
        "range": {"sheetId": sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2},
        "mergeType": "MERGE_ALL"
    }}

def border_bottom(sheet_id, row, c1, c2, color):
    return {"updateBorders": {
        "range": {"sheetId": sheet_id, "startRowIndex": row, "endRowIndex": row + 1, "startColumnIndex": c1, "endColumnIndex": c2},
        "bottom": {"style": "SOLID_MEDIUM", "colorStyle": {"rgbColor": color}}
    }}


if __name__ == "__main__":
    ss_id, ss_url = create_spreadsheet()
