"""
Fix stale formula references on the 2026 finance sheet.

Summary of fixes:
- Income:    K2 hardcoded $102,573 → formula; R6 month labels wrong (Jul-Dec → Jan-Jun);
             C7:C12 YTD formulas have stale guard; R13/R15 ref F2 (empty) → correct total;
             R3 subtitle says "2025"
- Expenses:  R2/R3 KPI stale values and "2025" subtitle
- Business:  H2/J2/L2 KPI hardcoded 2025 values; R3 "2025"; C18 Home Office hardcoded;
             Budget section rows 27-44 all 2025 hardcoded data
- Personal:  G2/I2/K2 KPI hardcoded 2025 values; R3/R24 "2025" labels
- P&L:       F2/H2/J2 KPI hardcoded 2025; R3 "2025"; vs-Target uses 105237 (2025 revenue)
- Dashboard: R40:G52 cash flow hardcoded 2025 data; R55-R60 key ratios "2025" hardcoded
- GST:       M column used for month (wrong — should be N); fix formulas
- Insights:  Empty — needs cash flow analysis formulas
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.google_sheets_auth import get_sheets_service

SHEET_ID = '1fPpOPnAYEnfCu33h1ki9NzFGTUOkpgd4mMSQX_sT9CY'

# ─── Shared formula helpers ───────────────────────────────────────────────────
# G column = split (numeric 0 or 1, not text %)
# N column = month number
# Using range $1:$2000 per the brief — headers/blanks return 0/FALSE so safe
SPLIT = '(IFERROR(IF(Transactions!G$1:G$2000="",1,VALUE(SUBSTITUTE(Transactions!G$1:G$2000,"%",""))/100),1))'
BUS   = '(Transactions!E$1:E$2000=TRUE)'
PERS  = '(Transactions!E$1:E$2000=FALSE)'
AMT   = 'IFERROR(ABS(Transactions!D$1:D$2000),0)'
MONTH = 'Transactions!N$1:N$2000'
D     = 'Transactions!D$1:D$2000'
F_CAT = 'Transactions!F$1:F$2000'

def rev_total():
    return f'=SUMPRODUCT({BUS}*({D}>0)*{D}*{SPLIT})'

def rev_month(m):
    return f'=SUMPRODUCT({BUS}*({D}>0)*({MONTH}={m})*{D}*{SPLIT})'

def biz_cat_ytd(cat):
    return f'=SUMPRODUCT({BUS}*({D}<0)*({F_CAT}="{cat}")*{AMT}*{SPLIT})'

def biz_cat_month(cat, m):
    return f'=SUMPRODUCT({BUS}*({D}<0)*({F_CAT}="{cat}")*({MONTH}={m})*{AMT}*{SPLIT})'

def pers_cat_ytd(cat):
    return f'=SUMPRODUCT({PERS}*({D}<0)*({F_CAT}="{cat}")*{AMT})'

def pers_cat_month(cat, m):
    return f'=SUMPRODUCT({PERS}*({D}<0)*({F_CAT}="{cat}")*({MONTH}={m})*{AMT})'

def biz_exp_ytd():
    # total all business expenses × split
    return f'=SUMPRODUCT({BUS}*({D}<0)*{AMT}*{SPLIT})'

def biz_exp_month(m):
    return f'=SUMPRODUCT({BUS}*({D}<0)*({MONTH}={m})*{AMT}*{SPLIT})'

def pers_exp_ytd():
    return f'=SUMPRODUCT({PERS}*({D}<0)*{AMT})'

def pers_exp_month(m):
    return f'=SUMPRODUCT({PERS}*({D}<0)*({MONTH}={m})*{AMT})'

# GST helper — H column = GST amount, N column = month, start row 1
def gst_collected_q(q_start, q_end):
    return (f'=SUMPRODUCT((Transactions!E$1:E$2000=TRUE)'
            f'*(Transactions!D$1:D$2000>0)'
            f'*((Transactions!N$1:N$2000>={q_start})*(Transactions!N$1:N$2000<={q_end}))'
            f'*IFERROR(Transactions!H$1:H$2000,0))')

def gst_itc_q(q_start, q_end):
    return (f'=SUMPRODUCT((Transactions!E$1:E$2000=TRUE)'
            f'*(Transactions!D$1:D$2000<0)'
            f'*((Transactions!N$1:N$2000>={q_start})*(Transactions!N$1:N$2000<={q_end}))'
            f'*IFERROR(Transactions!H$1:H$2000,0))')


def run():
    svc = get_sheets_service()
    updates = []

    # ──────────────────────────────────────────────────────────────────────────
    # INCOME TAB
    # ──────────────────────────────────────────────────────────────────────────
    print("Fixing Income tab...")

    # Fix subtitle
    updates.append({"range": "Income!B3", "values": [["All business revenue  ·  2026"]]})

    # Fix KPI: K2 = total revenue formula
    updates.append({"range": "Income!K2", "values": [[rev_total()]]})

    # Fix month header labels in R6 (C-I = YTD, Jan-Jun)
    # C=YTD, D=Jan, E=Feb, F=Mar, G=Apr, H=May, I=Jun
    updates.append({"range": "Income!C6:I6", "values": [["YTD", "Jan", "Feb", "Mar", "Apr", "May", "Jun"]]})

    # Fix YTD formulas C7:C12 — currently has stale `A5:A2054<>""` guard
    # Replace with clean SUMPRODUCT for each source
    sources = [
        ("Stripe (GHL Payouts)",   "Stripe"),
        ("Balmoral Construction",  "Balmoral"),
        ("PWC Window",             "Pwc Window"),
        ("Shala Yoga",             "Shala Yoga"),
        ("Client Cheques",         "Cheque"),
        ("Cash Deposits",          "Cash"),
    ]
    for row_offset, (label, keyword) in enumerate(sources):
        row = 7 + row_offset
        ytd_formula = (
            f'=SUMPRODUCT({BUS}*(ISNUMBER(SEARCH("{keyword}",Transactions!B$1:B$2000)))'
            f'*({D}>0)*{D}*{SPLIT})'
        )
        updates.append({"range": f"Income!C{row}", "values": [[ytd_formula]]})

    # Fix Other E-Transfers (R13): was =F2-SUM(C7:C12), F2 is empty
    # Should be = total revenue - sum of named sources
    updates.append({
        "range": "Income!C13",
        "values": [[f"={rev_total()[1:]}-SUM(C7:C12)"]]
    })

    # Fix TOTAL (R15): was =F2 (empty cell)
    updates.append({
        "range": "Income!C15",
        "values": [[rev_total()]]
    })

    # Fix monthly revenue formulas R19:R30 — these already look correct (use G$5:G$2049 range)
    # but let's update them to use the $1:$2000 pattern for consistency
    months_map = {19: 1, 20: 2, 21: 3, 22: 4, 23: 5, 24: 6,
                  25: 7, 26: 8, 27: 9, 28: 10, 29: 11, 30: 12}
    for row, month in months_map.items():
        updates.append({"range": f"Income!C{row}", "values": [[rev_month(month)]]})

    print("  Income: subtitle, K2 total, column headers, YTD formulas, monthly formulas fixed.")

    # ──────────────────────────────────────────────────────────────────────────
    # EXPENSES TAB
    # ──────────────────────────────────────────────────────────────────────────
    print("Fixing Expenses tab...")

    # Fix subtitle
    updates.append({"range": "Expenses!B3", "values": [["All business & personal spending  ·  2026"]]})

    # KPI cells: I2 = Personal total, K2 = Combined total
    # I2 = SUMPRODUCT personal expenses
    # K2 = total business + personal
    updates.append({"range": "Expenses!I2", "values": [[pers_exp_ytd()]]})
    updates.append({"range": "Expenses!K2", "values": [[f"={pers_exp_ytd()[1:]}+SUMPRODUCT({BUS}*({D}<0)*{AMT}*{SPLIT})"]]})

    # The category formulas in E6:E20 already look correct using $5:$2049 pattern
    # But let's upgrade them to $1:$2000 for consistency
    biz_cats = [
        (6,  "Equipment (CCA)"),
        (7,  "Software & Subscriptions"),
        (8,  "Office Supplies (<$500)"),
        (9,  "Vehicle"),
        (10, "Advertising & Marketing"),
        (11, "Insurance"),
        (12, "Interest & Bank Charges"),
        (13, "Telephone & Internet"),
        (14, "Subcontractors"),
        (15, "Rent / Co-working"),
        (16, "Travel"),
        (17, "Meals & Entertainment"),
        (18, "Home Office"),
        (19, "Professional Fees"),
        (20, "Other Business"),
    ]
    for row, cat in biz_cats:
        updates.append({"range": f"Expenses!E{row}", "values": [[biz_cat_ytd(cat)]]})

    pers_cats = [
        (25, "Housing"),
        (26, "Groceries"),
        (27, "Dining Out"),
        (28, "Savings/Investments"),
        (29, "Health & Fitness"),
        (30, "Subscriptions"),
        (31, "Entertainment"),
        (32, "Transportation"),
        (33, "Clothing"),
    ]
    for row, cat in pers_cats:
        updates.append({"range": f"Expenses!E{row}", "values": [[pers_cat_ytd(cat)]]})

    print("  Expenses: subtitle, KPI totals, category formulas fixed.")

    # ──────────────────────────────────────────────────────────────────────────
    # BUSINESS TAB
    # ──────────────────────────────────────────────────────────────────────────
    print("Fixing Business tab...")

    # Fix subtitle
    updates.append({"range": "Business!A3", "values": [["CRA T2125 Categories  ·  2026"]]})

    # Fix KPI: H2 = YTD total business expenses, J2 = monthly avg
    ytd_biz = biz_exp_ytd()
    updates.append({"range": "Business!H2", "values": [[ytd_biz]]})
    updates.append({"range": "Business!J2", "values": [[f"={ytd_biz[1:]}/MAX(1,SUMPRODUCT(({MONTH}>0)*1/12))"]]})
    # Simpler monthly avg: /3 for Q1 (Jan-Mar), but let's use count of months with data
    # Actually simplest: current month (March = 3), so /3
    # Use COUNTA of unique months: not easy. Use a formula that counts months that have data:
    # =H2/SUMPRODUCT((MMULT((ROW(INDIRECT("1:12"))=TRANSPOSE(UNIQUE(FILTER(N$1:N$2000,(E$1:E$2000=TRUE)*(D$1:D$2000<0)*(N$1:N$2000>0))))),ROW(INDIRECT("1:12"))^0)>0)*1)
    # That's too complex. Better: /MAX(1,MAX(N$1:N$2000)) — divides by highest month number
    updates.append({"range": "Business!J2", "values": [[f"=H2/MAX(1,SUMPRODUCT(((Transactions!N$1:N$2000>0)*(Transactions!E$1:E$2000=TRUE)*(Transactions!D$1:D$2000<0))*1)/(COUNTIF(Transactions!N$1:N$2000,Transactions!N$1:N$2000)*(Transactions!N$1:N$2000>0)*(Transactions!E$1:E$2000=TRUE)*(Transactions!D$1:D$2000<0)+(COUNTIF(Transactions!N$1:N$2000,Transactions!N$1:N$2000)*(Transactions!N$1:N$2000>0)*(Transactions!E$1:E$2000=TRUE)*(Transactions!D$1:D$2000<0)=0)))"]]})
    # That's too complex. Use simple: =H2/IFERROR(MAX(FILTER(Transactions!N$1:N$2000,Transactions!N$1:N$2000>0)),1)
    updates.append({"range": "Business!J2", "values": [[f"=IFERROR(H2/MAX(FILTER(Transactions!N$1:N$2000,Transactions!N$1:N$2000>0)),H2)"]]})
    # Top category formula (L2)
    updates.append({"range": "Business!L2", "values": [[
        '=IFERROR(INDEX(A6:A20,MATCH(MAX(C6:C20),C6:C20,0)),"—")'
    ]]})

    # Fix C18 Home Office — hardcoded 3480, monthly formulas correct but YTD is stuck
    # Home Office in Transactions would need actual entries, but it's typically a Tax tab entry
    # The YTD formula should just pull from Transactions like other categories
    updates.append({"range": "Business!C18", "values": [[biz_cat_ytd("Home Office")]]})

    # Business category monthly formulas (rows 6-20, cols D-O = months 1-12)
    # The existing formulas use $5:$2049 range — upgrade to $1:$2000
    biz_cats_all = [
        (6,  "Advertising & Marketing"),
        (7,  "Professional Fees"),
        (8,  "Vehicle"),
        (9,  "Insurance"),
        (10, "Interest & Bank Charges"),
        (11, "Office Supplies (<$500)"),
        (12, "Rent / Co-working"),
        (13, "Software & Subscriptions"),
        (14, "Travel"),
        (15, "Telephone & Internet"),
        (16, "Subcontractors"),
        (17, "Meals & Entertainment"),
        (18, "Home Office"),
        (19, "Equipment (CCA)"),
        (20, "Other Business"),
    ]
    # col D = month 1, E=2, ..., O=12
    for row, cat in biz_cats_all:
        for m in range(1, 13):
            col = chr(ord('D') + m - 1)  # D=1, E=2, ..., O=12
            updates.append({"range": f"Business!{col}{row}", "values": [[biz_cat_month(cat, m)]]})
        # YTD = SUM(D:O)
        updates.append({"range": f"Business!C{row}", "values": [[f"=SUM(D{row}:O{row})"]]})

    # Budget vs Actual section — fix column D (2025 Actual → 2026 formula) and header
    updates.append({"range": "Business!A27", "values": [["MONTHLY BUDGET vs ACTUAL  ·  2026"]]})
    updates.append({"range": "Business!D28", "values": [["2026 YTD"]]})
    # Update D29:D44 to reference actual YTD from category rows above
    # Map: Advertising=C6, Professional=C7, Vehicle=C8, Insurance=C9, Interest=C10,
    #      Office=C11, Rent=C12, Software=C13, Travel=C14, Phone=C15, Sub=C16,
    #      Meals=C17, HomeOffice=C18, Equipment=C19, Other=C20
    budget_row_to_cat_row = {
        29: 6, 30: 7, 31: 8, 32: 9, 33: 10, 34: 11, 35: 12,
        36: 13, 37: 14, 38: 15, 39: 16, 40: 17, 41: 18, 42: 19, 43: 20
    }
    for brow, crow in budget_row_to_cat_row.items():
        updates.append({"range": f"Business!D{brow}", "values": [[f"=C{crow}"]]})
        # Monthly avg = D/current month count
        updates.append({"range": f"Business!E{brow}", "values": [[f"=IFERROR(D{brow}/MAX(FILTER(Transactions!N$1:N$2000,Transactions!N$1:N$2000>0)),D{brow})"]]})
        # Variance = actual - annual budget (col B)
        updates.append({"range": f"Business!F{brow}", "values": [[f"=D{brow}-B{brow}"]]})
        # Status
        updates.append({"range": f"Business!G{brow}", "values": [[f'=IF(F{brow}>0,"OVER","ON TRACK")']]})
    # Total row 44
    updates.append({"range": "Business!D44", "values": [[f"=SUM(D29:D43)"]]})
    updates.append({"range": "Business!E44", "values": [[f"=IFERROR(D44/MAX(FILTER(Transactions!N$1:N$2000,Transactions!N$1:N$2000>0)),D44)"]]})
    updates.append({"range": "Business!F44", "values": [[f"=D44-B44"]]})
    updates.append({"range": "Business!G44", "values": [[f'=IF(F44>0,"OVER","ON TRACK")']]})

    print("  Business: subtitle, KPIs, C18 Home Office, monthly formulas, budget section fixed.")

    # ──────────────────────────────────────────────────────────────────────────
    # PERSONAL TAB
    # ──────────────────────────────────────────────────────────────────────────
    print("Fixing Personal tab...")

    # Fix subtitle and section label
    updates.append({"range": "Personal!A3", "values": [["Monthly category tracking  ·  2026"]]})
    updates.append({"range": "Personal!A24", "values": [["PERSONAL SPENDING INSIGHTS  ·  2026"]]})

    # Fix KPI cells
    pers_total = pers_exp_ytd()
    updates.append({"range": "Personal!G2", "values": [[pers_total]]})
    updates.append({"range": "Personal!I2", "values": [[f"=IFERROR(G2/MAX(FILTER(Transactions!N$1:N$2000,Transactions!N$1:N$2000>0)),G2)"]]})
    # Daily avg = G2/days-in-year-so-far
    updates.append({"range": "Personal!K2", "values": [[f'=IFERROR(G2/MAX(FILTER(Transactions!N$1:N$2000,Transactions!N$1:N$2000>0))/30.44,0)']]})

    # Personal category monthly formulas — existing formulas use $5:$2049, upgrade to $1:$2000
    pers_cats_all = [
        (6,  "Housing"),
        (7,  "Utilities"),
        (8,  "Groceries"),
        (9,  "Dining Out"),
        (10, "Transportation"),
        (11, "Health & Fitness"),
        (12, "Subscriptions"),
        (13, "Clothing"),
        (14, "Entertainment"),
        (15, "Travel (Personal)"),
        (16, "Savings/Investments"),
        (17, "Other Personal"),
    ]
    for row, cat in pers_cats_all:
        for m in range(1, 13):
            col = chr(ord('C') + m - 1)  # C=Jan=1, D=Feb=2, ..., N=Dec=12
            updates.append({"range": f"Personal!{col}{row}", "values": [[pers_cat_month(cat, m)]]})
        updates.append({"range": f"Personal!B{row}", "values": [[f"=SUM(C{row}:N{row})"]]})

    print("  Personal: subtitle, KPIs, monthly formulas fixed.")

    # ──────────────────────────────────────────────────────────────────────────
    # P&L TAB
    # ──────────────────────────────────────────────────────────────────────────
    print("Fixing P&L tab...")

    # Fix subtitle
    updates.append({"range": "P&L!A3", "values": [["Monthly income statement  ·  2026"]]})

    # Fix KPI cells
    # F2 = total revenue
    updates.append({"range": "P&L!F2", "values": [[rev_total()]]})
    # H2 = total profit = revenue - biz expenses
    updates.append({"range": "P&L!H2", "values": [[f"=P&L!B19-P&L!C19"]]})
    # J2 = margin
    updates.append({"range": "P&L!J2", "values": [[f"=IFERROR(P&L!H2/P&L!F2,0)"]]})

    # vs Target column H: replace 105237 with 2026 target
    # 2026 target from strategy: $120,000 / 12 per month
    # Or keep it formula-based: revenue YTD vs expected at this pace
    # Use $120,000 annual target
    target_2026 = 120000
    for i, row in enumerate(range(6, 18)):  # rows 6-17 = Jan-Dec
        month_num = i + 1
        updates.append({"range": f"P&L!H{row}", "values": [[
            f"=F{row}-({target_2026}/12*{month_num})"
        ]]})

    # Also fix monthly Revenue and Expense formulas to use $1:$2000 pattern
    for i, row in enumerate(range(6, 18)):
        m = i + 1
        updates.append({"range": f"P&L!B{row}", "values": [[rev_month(m)]]})
        updates.append({"range": f"P&L!C{row}", "values": [[biz_exp_month(m)]]})

    print("  P&L: subtitle, KPIs, monthly formulas, vs-target column fixed.")

    # ──────────────────────────────────────────────────────────────────────────
    # GST TAB
    # ──────────────────────────────────────────────────────────────────────────
    print("Fixing GST tab...")

    # Fix formulas to use N column (month) not M column
    updates.append({"range": "GST!C6", "values": [[gst_collected_q(1, 3)]]})
    updates.append({"range": "GST!D6", "values": [[gst_collected_q(4, 6)]]})
    updates.append({"range": "GST!E6", "values": [[gst_collected_q(7, 9)]]})
    updates.append({"range": "GST!F6", "values": [[gst_collected_q(10, 12)]]})
    updates.append({"range": "GST!G6", "values": [["=SUM(C6:F6)"]]})

    updates.append({"range": "GST!C7", "values": [[gst_itc_q(1, 3)]]})
    updates.append({"range": "GST!D7", "values": [[gst_itc_q(4, 6)]]})
    updates.append({"range": "GST!E7", "values": [[gst_itc_q(7, 9)]]})
    updates.append({"range": "GST!F7", "values": [[gst_itc_q(10, 12)]]})
    updates.append({"range": "GST!G7", "values": [["=SUM(C7:F7)"]]})

    print("  GST: month column fixed from M to N.")

    # ──────────────────────────────────────────────────────────────────────────
    # DASHBOARD TAB
    # ──────────────────────────────────────────────────────────────────────────
    print("Fixing Dashboard tab...")

    # Revenue KPI C6 — already correct formula using $1:$2000
    # Business Expenses KPI G6 = Tax!C26 — correct (Tax tab driven)
    # Net Profit K6 already =C6-G6

    # Fix Monthly Breakdown revenue/expense formulas (D17:D28, E17:E28) — already use $1:$2000 ✓
    # They're already correct formulas, just verify

    # Fix Cash Flow section (R38-R52) — currently all hardcoded 2025 values
    # Replace with SUMPRODUCT formulas for revenue and total outflow per month
    for i, month_name in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]):
        row = 40 + i
        m = i + 1
        # Revenue = all positive transactions (business + personal inflows)
        rev_formula = (
            f'=SUMPRODUCT((Transactions!D$1:D$2000>0)'
            f'*(Transactions!N$1:N$2000={m})'
            f'*Transactions!D$1:D$2000)'
        )
        # Total Outflow = all negative transactions (absolute value)
        out_formula = (
            f'=SUMPRODUCT((Transactions!D$1:D$2000<0)'
            f'*(Transactions!N$1:N$2000={m})'
            f'*IFERROR(ABS(Transactions!D$1:D$2000),0))'
        )
        # Net = D-E
        net_formula = f'=D{row}-E{row}'
        # Cumulative balance
        if i == 0:
            cumul_formula = f'=F{row}'
        else:
            prev_row = row - 1
            cumul_formula = f'=G{prev_row}+F{row}'

        updates.append({"range": f"Dashboard!D{row}", "values": [[rev_formula]]})
        updates.append({"range": f"Dashboard!E{row}", "values": [[out_formula]]})
        updates.append({"range": f"Dashboard!F{row}", "values": [[net_formula]]})
        updates.append({"range": f"Dashboard!G{row}", "values": [[cumul_formula]]})

    # Fix Total row (R52)
    updates.append({"range": "Dashboard!D52", "values": [["=SUM(D40:D51)"]]})
    updates.append({"range": "Dashboard!E52", "values": [["=SUM(E40:E51)"]]})
    updates.append({"range": "Dashboard!F52", "values": [["=SUM(F40:F51)"]]})

    # Fix Key Ratios section (R55-R60) — say "2025", hardcoded values
    updates.append({"range": "Dashboard!C55", "values": [["Key Ratios  ·  2026"]]})
    # Profit margin = (Revenue - BizExp) / Revenue
    updates.append({"range": "Dashboard!D57", "values": [[f'=IFERROR(({rev_total()[1:]}-{biz_exp_ytd()[1:]})/({rev_total()[1:]}),0)']]})
    updates.append({"range": "Dashboard!E57", "values": [[""]]})
    updates.append({"range": "Dashboard!F57", "values": [[f'=IFERROR("Net $"&TEXT({rev_total()[1:]}-{biz_exp_ytd()[1:]},"#,##0")&" on $"&TEXT({rev_total()[1:]},"#,##0")&" revenue","")']]})
    # Business Expense Ratio
    updates.append({"range": "Dashboard!D58", "values": [[f'=IFERROR({biz_exp_ytd()[1:]}/{rev_total()[1:]},0)']]})
    # Savings Rate = savings/investments / total income
    savings_f = f'SUMPRODUCT({PERS}*({D}<0)*({F_CAT}="Savings/Investments")*{AMT})'
    updates.append({"range": "Dashboard!D59", "values": [[f'=IFERROR({savings_f}/{rev_total()[1:]},0)']]})
    # Software as % of revenue
    software_f = biz_cat_ytd("Software & Subscriptions")[1:]
    updates.append({"range": "Dashboard!D60", "values": [[f'=IFERROR({software_f}/{rev_total()[1:]},0)']]})

    print("  Dashboard: cash flow section, key ratios fixed.")

    # ──────────────────────────────────────────────────────────────────────────
    # INSIGHTS TAB
    # ──────────────────────────────────────────────────────────────────────────
    print("Fixing Insights tab...")

    # Cash flow analysis rows 6-17 (Jan-Dec)
    for i, month_name in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]):
        row = 6 + i
        m = i + 1
        # Income = all inflows this month
        income_f = f'=SUMPRODUCT((Transactions!D$1:D$2000>0)*(Transactions!N$1:N$2000={m})*Transactions!D$1:D$2000)'
        # Total outflow = all outflows
        out_f = f'=SUMPRODUCT((Transactions!D$1:D$2000<0)*(Transactions!N$1:N$2000={m})*IFERROR(ABS(Transactions!D$1:D$2000),0))'
        # Net = B-C
        net_f = f'=B{row}-C{row}'
        # Cumul balance
        if i == 0:
            cumul_f = f'=D{row}'
        else:
            cumul_f = f'=E{row-1}+D{row}'
        # Flag: warn if net < -1000
        flag_f = f'=IF(D{row}<-1000,"⚠ CASH BURN",IF(D{row}<0,"Deficit","✓"))'

        updates.append({"range": f"Insights!A{row}", "values": [[month_name]]})
        updates.append({"range": f"Insights!B{row}", "values": [[income_f]]})
        updates.append({"range": f"Insights!C{row}", "values": [[out_f]]})
        updates.append({"range": f"Insights!D{row}", "values": [[net_f]]})
        updates.append({"range": f"Insights!E{row}", "values": [[cumul_f]]})
        updates.append({"range": f"Insights!F{row}", "values": [[flag_f]]})

    # Spending velocity section (rows 20-25)
    updates.append({"range": "Insights!A19", "values": [["SPENDING VELOCITY"]]})
    updates.append({"range": "Insights!A20", "values": [["Metric"]]})
    updates.append({"range": "Insights!B20", "values": [["Value"]]})
    updates.append({"range": "Insights!C20", "values": [["Notes"]]})
    updates.append({"range": "Insights!A21", "values": [["Daily Burn Rate"]]})
    updates.append({"range": "Insights!B21", "values": [[
        f'=IFERROR({biz_exp_ytd()[1:]}/MAX(FILTER(Transactions!N$1:N$2000,Transactions!N$1:N$2000>0))/30.44,0)'
    ]]})
    updates.append({"range": "Insights!C21", "values": [["Business expenses per day"]]})
    updates.append({"range": "Insights!A22", "values": [["Software Stack (Annual)"]]})
    updates.append({"range": "Insights!B22", "values": [[biz_cat_ytd("Software & Subscriptions")]]})
    updates.append({"range": "Insights!C22", "values": [["YTD software & subscription costs"]]})
    updates.append({"range": "Insights!A23", "values": [["Revenue Run Rate"]]})
    updates.append({"range": "Insights!B23", "values": [[
        f'=IFERROR({rev_total()[1:]}/MAX(FILTER(Transactions!N$1:N$2000,Transactions!N$1:N$2000>0))*12,0)'
    ]]})
    updates.append({"range": "Insights!C23", "values": [["Annualized at current pace"]]})
    updates.append({"range": "Insights!A24", "values": [["Savings Rate"]]})
    updates.append({"range": "Insights!B24", "values": [[
        f'=IFERROR(SUMPRODUCT({PERS}*({D}<0)*({F_CAT}="Savings/Investments")*{AMT})/{rev_total()[1:]},0)'
    ]]})
    updates.append({"range": "Insights!C24", "values": [["Savings/Investments as % of revenue"]]})

    print("  Insights: cash flow analysis and spending velocity sections added.")

    # ──────────────────────────────────────────────────────────────────────────
    # WRITE ALL UPDATES
    # ──────────────────────────────────────────────────────────────────────────
    print(f"\nWriting {len(updates)} cell updates to Google Sheets...")

    # Batch in chunks of 200 to avoid payload limits
    chunk_size = 200
    for i in range(0, len(updates), chunk_size):
        chunk = updates[i:i+chunk_size]
        svc.spreadsheets().values().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": chunk}
        ).execute()
        print(f"  Wrote chunk {i//chunk_size + 1}/{(len(updates)-1)//chunk_size + 1} ({len(chunk)} cells)")

    # ──────────────────────────────────────────────────────────────────────────
    # VERIFICATION
    # ──────────────────────────────────────────────────────────────────────────
    print("\n=== VERIFICATION ===")

    checks = {
        "Income!K2":       "Total Revenue",
        "Income!C19":      "Jan Revenue",
        "Income!C7":       "Stripe YTD",
        "Income!C15":      "Income TOTAL",
        "Expenses!E7":     "Software YTD",
        "Expenses!I2":     "Personal Total",
        "Business!C6":     "Adv&Mktg YTD",
        "Business!H2":     "Biz KPI Total",
        "Personal!B8":     "Groceries YTD",
        "Personal!G2":     "Pers KPI Total",
        "P&L!B6":          "Jan Revenue",
        "P&L!F2":          "P&L Rev KPI",
        "GST!C6":          "GST Q1 Collected",
        "GST!C7":          "GST Q1 ITCs",
        "Dashboard!D40":   "Jan Cash Inflow",
        "Dashboard!D57":   "Profit Margin",
        "Insights!B6":     "Jan Income",
        "Insights!D6":     "Jan Net",
    }

    result_data = svc.spreadsheets().values().batchGet(
        spreadsheetId=SHEET_ID,
        ranges=list(checks.keys()),
        valueRenderOption='FORMATTED_VALUE'
    ).execute()

    value_ranges = result_data.get('valueRanges', [])
    print(f"\n{'Range':<25} {'Label':<25} {'Value'}")
    print("-" * 65)
    for rng, label in checks.items():
        # Find the matching range in response
        val = "—"
        for vr in value_ranges:
            if rng in vr.get('range', ''):
                vals = vr.get('values', [[]])
                val = vals[0][0] if vals and vals[0] else "empty"
                break
        print(f"  {rng:<23} {label:<25} {val}")

    print(f"\nDone! Sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}")


if __name__ == "__main__":
    run()
