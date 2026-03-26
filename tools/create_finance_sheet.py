"""
Create comprehensive personal & business finance spreadsheet for Matt Anthony Photography.
Tax-ready for CRA (sole proprietor, GST registered, BC Canada).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.google_sheets_auth import get_sheets_service, get_drive_service
import json
from datetime import datetime

YEAR = 2026

# ── Color palette ──
WHITE = {"red": 1, "green": 1, "blue": 1}
DARK = {"red": 0.13, "green": 0.13, "blue": 0.13}
ACCENT = {"red": 0.16, "green": 0.50, "blue": 0.73}  # Steel blue
ACCENT_LIGHT = {"red": 0.85, "green": 0.92, "blue": 0.97}
GREEN = {"red": 0.22, "green": 0.56, "blue": 0.24}
GREEN_LIGHT = {"red": 0.85, "green": 0.94, "blue": 0.85}
RED = {"red": 0.80, "green": 0.20, "blue": 0.20}
RED_LIGHT = {"red": 0.97, "green": 0.87, "blue": 0.87}
YELLOW_LIGHT = {"red": 1.0, "green": 0.97, "blue": 0.85}
GRAY_LIGHT = {"red": 0.95, "green": 0.95, "blue": 0.95}
GRAY_MED = {"red": 0.85, "green": 0.85, "blue": 0.85}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def create_spreadsheet():
    sheets_svc = get_sheets_service()
    drive_svc = get_drive_service()

    # ── Define all tabs ──
    tab_defs = [
        ("Dashboard", "4A90D2"),
        ("Income", "27AE60"),
        ("Business Expenses", "E67E22"),
        ("Personal Expenses", "8E44AD"),
        ("GST-HST Tracker", "C0392B"),
        ("Mileage Log", "2C3E50"),
        ("Equipment CCA", "16A085"),
        ("Tax Summary", "D35400"),
        ("Monthly P&L", "2980B9"),
        ("Savings Recs", "1ABC9C"),
    ]

    sheet_props = []
    for i, (name, color) in enumerate(tab_defs):
        r, g, b = int(color[:2], 16)/255, int(color[2:4], 16)/255, int(color[4:], 16)/255
        sheet_props.append({
            "properties": {
                "sheetId": i,
                "title": name,
                "index": i,
                "tabColorStyle": {"rgbColor": {"red": r, "green": g, "blue": b}},
                "gridProperties": {"frozenRowCount": 1 if i > 0 else 0}
            }
        })

    spreadsheet = sheets_svc.spreadsheets().create(body={
        "properties": {"title": f"Matt Anthony — Finance Tracker {YEAR}"},
        "sheets": sheet_props
    }).execute()

    ss_id = spreadsheet["spreadsheetId"]
    ss_url = spreadsheet["spreadsheetUrl"]
    print(f"Created: {ss_url}")

    # ── Build all tab content ──
    requests = []
    data_updates = []

    # ═══════════════════════════════════════════
    # TAB 0: DASHBOARD
    # ═══════════════════════════════════════════
    dashboard_data = [
        [f"MATT ANTHONY PHOTOGRAPHY — {YEAR} FINANCE DASHBOARD", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", ""],
        ["KEY METRICS", "", "", "", "MONTHLY TREND", "", "", ""],
        ["", "", "", "", "", "", "", ""],
        ["Gross Revenue (YTD)", "", f"='Income'!B2", "", "Month", "Revenue", "Expenses", "Net"],
    ]
    for i, m in enumerate(MONTHS):
        row = ["", "", "", "", m,
               f"='Monthly P&L'!B{i+3}",
               f"='Monthly P&L'!C{i+3}",
               f"='Monthly P&L'!D{i+3}"]
        if i == 0:
            row[0] = "Total Business Expenses (YTD)"
            row[2] = f"='Business Expenses'!N2"
        elif i == 1:
            row[0] = "Net Profit (YTD)"
            row[2] = "=C5-C6"
        elif i == 2:
            row[0] = "Profit Margin"
            row[2] = '=IF(C5>0,C7/C5,0)'
        elif i == 3:
            row[0] = "GST Owing (Current Quarter)"
            row[2] = f"='GST-HST Tracker'!E18"
        elif i == 4:
            row[0] = "Est. Income Tax Owing"
            row[2] = f"='Tax Summary'!B20"
        elif i == 5:
            row[0] = "CPP Self-Employed"
            row[2] = f"='Tax Summary'!B23"
        elif i == 6:
            row[0] = ""
            row[2] = ""
        elif i == 7:
            row[0] = "REVENUE TARGET"
            row[2] = ""
        elif i == 8:
            row[0] = "Annual Target"
            row[2] = 172900
        elif i == 9:
            row[0] = "Achieved"
            row[2] = "=C5"
        elif i == 10:
            row[0] = "Remaining"
            row[2] = "=C14-C15"
        elif i == 11:
            row[0] = "% Complete"
            row[2] = "=IF(C14>0,C15/C14,0)"
        dashboard_data.append(row)

    # Spending breakdown section
    dashboard_data.append(["", "", "", "", "", "", "", ""])
    dashboard_data.append(["TOP EXPENSE CATEGORIES", "", "", "", "BUSINESS vs PERSONAL SPLIT", "", "", ""])
    dashboard_data.append(["Category", "Amount", "% of Total", "", "Type", "Amount", "% of Income", ""])
    dashboard_data.append(["Advertising", f"='Business Expenses'!N3", "=IF(C5>0,B21/C5,0)", "",
                          "Business Expenses", "=C6", "=IF(C5>0,F21/C5,0)", ""])
    dashboard_data.append(["Vehicle", f"='Business Expenses'!N5", "=IF(C5>0,B22/C5,0)", "",
                          "Personal Expenses", f"='Personal Expenses'!N2", "=IF(C5>0,F22/C5,0)", ""])
    dashboard_data.append(["Equipment/Supplies", f"='Business Expenses'!N8", "=IF(C5>0,B23/C5,0)", "",
                          "Taxes (Est.)", "=C10+C11", "=IF(C5>0,F23/C5,0)", ""])
    dashboard_data.append(["Software/Subscriptions", f"='Business Expenses'!N10", "=IF(C5>0,B24/C5,0)", "",
                          "Owner Draw", "=3000*MONTH(TODAY())", "=IF(C5>0,F24/C5,0)", ""])
    dashboard_data.append(["Insurance", f"='Business Expenses'!N6", "=IF(C5>0,B25/C5,0)", "", "", "", "", ""])
    data_updates.append({"range": f"Dashboard!A1:H{len(dashboard_data)}", "values": dashboard_data})

    # ═══════════════════════════════════════════
    # TAB 1: INCOME
    # ═══════════════════════════════════════════
    income_header = ["INCOME TRACKER", "YTD Total", "", "", "", "", "", "", "", "", "", "", "", ""]
    income_header[2] = "Jan"
    income_header[3] = "Feb"
    income_header[4] = "Mar"
    income_header[5] = "Apr"
    income_header[6] = "May"
    income_header[7] = "Jun"
    income_header[8] = "Jul"
    income_header[9] = "Aug"
    income_header[10] = "Sep"
    income_header[11] = "Oct"
    income_header[12] = "Nov"
    income_header[13] = "Dec"

    income_data = [
        ["Category", "YTD Total"] + MONTHS,
        ["TOTAL REVENUE", "=SUM(C2:N2)"] + [f"=SUM(C3:C6)" for _ in MONTHS],
        ["Project Photography", "=SUM(C3:N3)"] + ["" for _ in MONTHS],
        ["Retainers", "=SUM(C4:N4)"] + ["" for _ in MONTHS],
        ["Licensing/Cost-Share", "=SUM(C5:N5)"] + ["" for _ in MONTHS],
        ["Other (Hosting/Subs)", "=SUM(C6:N6)"] + ["" for _ in MONTHS],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["INVOICE LOG", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["Date", "Client", "Description", "Category", "Amount (pre-tax)", "GST Collected", "Total", "Payment Status", "Payment Date", "Notes", "", "", "", ""],
    ]
    # Add 50 empty rows for invoice entries
    for _ in range(50):
        income_data.append(["", "", "", "", "", "", "", "", "", "", "", "", "", ""])

    # Fix the monthly total formulas to reference invoice log
    for m_idx in range(12):
        col_letter = chr(ord('C') + m_idx)
        month_num = m_idx + 1
        # Total revenue per month sums from categories
        income_data[1][m_idx + 2] = f"=SUM({col_letter}3:{col_letter}6)"

    data_updates.append({"range": f"Income!A1:N{len(income_data)}", "values": income_data})

    # ═══════════════════════════════════════════
    # TAB 2: BUSINESS EXPENSES (CRA T2125 Categories)
    # ═══════════════════════════════════════════
    biz_exp = [
        ["T2125 EXPENSE CATEGORY", "YTD Total"] + MONTHS,
        ["TOTAL BUSINESS EXPENSES", "=SUM(C2:N2)"] + [f"=SUM(C3:C16)" for _ in MONTHS],
        ["Line 8521 — Advertising & Marketing", "=SUM(C3:N3)"] + ["" for _ in MONTHS],
        ["Line 8590 — Professional Fees (Accounting/Legal)", "=SUM(C4:N4)"] + ["" for _ in MONTHS],
        ["Line 8615 — Vehicle (Fuel, Maintenance, Parking)", "=SUM(C5:N5)"] + ["" for _ in MONTHS],
        ["Line 8690 — Insurance (Business)", "=SUM(C6:N6)"] + ["" for _ in MONTHS],
        ["Line 8710 — Interest & Bank Charges", "=SUM(C7:N7)"] + ["" for _ in MONTHS],
        ["Line 8811 — Office Supplies & Equipment <$500", "=SUM(C8:N8)"] + ["" for _ in MONTHS],
        ["Line 8860 — Rent (Studio/Storage)", "=SUM(C9:N9)"] + ["" for _ in MONTHS],
        ["Line 8871 — Software & Subscriptions", "=SUM(C10:N10)"] + ["" for _ in MONTHS],
        ["Line 8910 — Travel (Accommodation, Flights)", "=SUM(C11:N11)"] + ["" for _ in MONTHS],
        ["Line 8945 — Telephone & Internet", "=SUM(C12:N12)"] + ["" for _ in MONTHS],
        ["Line 9060 — Subcontractors", "=SUM(C13:N13)"] + ["" for _ in MONTHS],
        ["Line 9270 — Meals & Entertainment (50%)", "=SUM(C14:N14)"] + ["" for _ in MONTHS],
        ["Line 9281 — Home Office (See Tax Summary)", "=SUM(C15:N15)"] + ["" for _ in MONTHS],
        ["Other Business Expenses", "=SUM(C16:N16)"] + ["" for _ in MONTHS],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["EXPENSE LOG", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["Date", "Vendor/Payee", "Description", "T2125 Category", "Amount (pre-tax)", "GST Paid (ITC)", "Total Paid", "Payment Method", "Receipt?", "Account (Biz/Personal)", "Notes", "", "", ""],
    ]
    for _ in range(100):
        biz_exp.append(["", "", "", "", "", "", "", "", "", "", "", "", "", ""])

    # Fix monthly total formulas
    for m_idx in range(12):
        col_letter = chr(ord('C') + m_idx)
        biz_exp[1][m_idx + 2] = f"=SUM({col_letter}3:{col_letter}16)"

    data_updates.append({"range": f"Business Expenses!A1:N{len(biz_exp)}", "values": biz_exp})

    # ═══════════════════════════════════════════
    # TAB 3: PERSONAL EXPENSES
    # ═══════════════════════════════════════════
    personal = [
        ["PERSONAL EXPENSE CATEGORY", "YTD Total"] + MONTHS,
        ["TOTAL PERSONAL EXPENSES", "=SUM(C2:N2)"] + [f"=SUM(C3:C13)" for _ in MONTHS],
        ["Housing (Rent/Mortgage)", "=SUM(C3:N3)"] + ["" for _ in MONTHS],
        ["Utilities (Hydro, Gas, Water)", "=SUM(C4:N4)"] + ["" for _ in MONTHS],
        ["Groceries & Household", "=SUM(C5:N5)"] + ["" for _ in MONTHS],
        ["Dining Out", "=SUM(C6:N6)"] + ["" for _ in MONTHS],
        ["Transportation (Personal)", "=SUM(C7:N7)"] + ["" for _ in MONTHS],
        ["Health & Fitness", "=SUM(C8:N8)"] + ["" for _ in MONTHS],
        ["Personal Subscriptions", "=SUM(C9:N9)"] + ["" for _ in MONTHS],
        ["Clothing", "=SUM(C10:N10)"] + ["" for _ in MONTHS],
        ["Entertainment", "=SUM(C11:N11)"] + ["" for _ in MONTHS],
        ["Savings/Investments", "=SUM(C12:N12)"] + ["" for _ in MONTHS],
        ["Other Personal", "=SUM(C13:N13)"] + ["" for _ in MONTHS],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["EXPENSE LOG", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["Date", "Vendor", "Description", "Category", "Amount", "Payment Method", "Account (Biz/Personal)", "Notes", "", "", "", "", "", ""],
    ]
    for _ in range(80):
        personal.append(["", "", "", "", "", "", "", "", "", "", "", "", "", ""])

    for m_idx in range(12):
        col_letter = chr(ord('C') + m_idx)
        personal[1][m_idx + 2] = f"=SUM({col_letter}3:{col_letter}13)"

    data_updates.append({"range": f"Personal Expenses!A1:N{len(personal)}", "values": personal})

    # ═══════════════════════════════════════════
    # TAB 4: GST/HST TRACKER
    # ═══════════════════════════════════════════
    gst = [
        ["GST/HST TRACKER — 5% (BC)", "YTD Total"] + MONTHS,
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["GST COLLECTED (on sales)", "=SUM(C3:N3)"] + ["" for _ in MONTHS],
        ["GST PAID (Input Tax Credits)", "=SUM(C4:N4)"] + ["" for _ in MONTHS],
        ["NET GST OWING", "=B3-B4"] + [f"={chr(ord('C')+i)}3-{chr(ord('C')+i)}4" for i in range(12)],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["QUARTERLY FILING SUMMARY", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["Quarter", "Period", "GST Collected", "ITCs (GST Paid)", "Net Owing", "Due Date", "Filed?", "Payment Date", "", "", "", "", "", ""],
        ["Q1", "Jan–Mar", "=SUM(C3:E3)", "=SUM(C4:E4)", "=C9-D9", "Apr 30", "", "", "", "", "", "", "", ""],
        ["Q2", "Apr–Jun", "=SUM(F3:H3)", "=SUM(F4:H4)", "=C10-D10", "Jul 31", "", "", "", "", "", "", "", ""],
        ["Q3", "Jul–Sep", "=SUM(I3:K3)", "=SUM(I4:K4)", "=C11-D11", "Oct 31", "", "", "", "", "", "", "", ""],
        ["Q4", "Oct–Dec", "=SUM(L3:N3)", "=SUM(L4:N4)", "=C12-D12", "Jan 31", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["ANNUAL TOTAL", "", "=SUM(C9:C12)", "=SUM(D9:D12)", "=SUM(E9:E12)", "", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["NOTES:", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["• GST Registration # — enter here", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["• Filing frequency: Quarterly", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["• ITCs = GST paid on business purchases (from Business Expenses GST column)", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["• Keep ALL receipts for 6 years", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ]
    data_updates.append({"range": f"GST-HST Tracker!A1:N{len(gst)}", "values": gst})

    # ═══════════════════════════════════════════
    # TAB 5: MILEAGE LOG
    # ═══════════════════════════════════════════
    mileage = [
        ["CRA VEHICLE / MILEAGE LOG", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", ""],
        ["Vehicle:", "", "Year/Make/Model here", "", "CRA Rate (2026):", "$0.72/km first 5,000 | $0.66/km after", "", "", ""],
        ["Total KM (YTD):", "", "=SUM(F6:F200)", "", "Business KM:", "=SUMIF(G6:G200,\"Business\",F6:F200)", "", "", ""],
        ["Business %:", "", "=IF(C4>0,F4/C4,0)", "", "Deduction:", "=IF(F4<=5000,F4*0.72,5000*0.72+(F4-5000)*0.66)", "", "", ""],
        ["", "", "", "", "", "", "", "", ""],
        ["Date", "From", "To", "Purpose/Client", "Round Trip KM", "KM", "Type (Business/Personal)", "Notes", ""],
    ]
    for _ in range(150):
        mileage.append(["", "", "", "", "", "", "", "", ""])

    data_updates.append({"range": f"Mileage Log!A1:I{len(mileage)}", "values": mileage})

    # ═══════════════════════════════════════════
    # TAB 6: EQUIPMENT CCA (Capital Cost Allowance)
    # ═══════════════════════════════════════════
    cca = [
        ["CAPITAL COST ALLOWANCE (CCA) SCHEDULE", "", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", "", ""],
        ["CRA CCA CLASSES FOR PHOTOGRAPHY", "", "", "", "", "", "", "", "", ""],
        ["Class", "Rate", "Description", "Examples", "", "", "", "", "", ""],
        ["Class 8", "20%", "Machinery, equipment, furniture", "Camera bodies, lenses, lighting, tripods", "", "", "", "", "", ""],
        ["Class 10", "30%", "Motor vehicles", "Vehicle used for business", "", "", "", "", "", ""],
        ["Class 10.1", "30%", "Passenger vehicle >$37,000", "Luxury vehicle (max CCA on $37K)", "", "", "", "", "", ""],
        ["Class 12", "100%", "Tools, software <$500", "Small accessories, single-use software", "", "", "", "", "", ""],
        ["Class 50", "55%", "Computer equipment", "Computers, monitors, hard drives", "", "", "", "", "", ""],
        ["Class 46", "30%", "Data network equipment", "Routers, servers", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", "", ""],
        ["ASSET REGISTER", "", "", "", "", "", "", "", "", ""],
        ["Asset", "Date Acquired", "CCA Class", "Cost", "UCC Start of Year", "CCA Rate", "CCA Claimed", "UCC End of Year", "Notes", ""],
        ["", "", "", "", "", "", "", "", "", ""],
    ]
    for _ in range(30):
        cca.append(["", "", "", "", "", "", "", "", "", ""])

    # Add formulas for first few asset rows
    for row_idx in range(14, 44):
        r = row_idx + 1
        cca[row_idx] = ["", "", "", "", "", "",
                        f"=IF(E{r}>0,E{r}*F{r},\"\")",
                        f"=IF(E{r}>0,E{r}-G{r},\"\")", "", ""]

    cca.append(["", "", "", "", "", "", "", "", "", ""])
    cca.append(["TOTALS", "", "", "=SUM(D14:D43)", "=SUM(E14:E43)", "", "=SUM(G14:G43)", "=SUM(H14:H43)", "", ""])
    cca.append(["", "", "", "", "", "", "", "", "", ""])
    cca.append(["NOTES:", "", "", "", "", "", "", "", "", ""])
    cca.append(["• Half-year rule: In year of acquisition, CCA is calculated on 50% of net additions", "", "", "", "", "", "", "", "", ""])
    cca.append(["• Accelerated Investment Incentive: First-year enhanced allowance may apply", "", "", "", "", "", "", "", "", ""])
    cca.append(["• Dispose of asset: reduce UCC by lesser of proceeds or original cost", "", "", "", "", "", "", "", "", ""])

    data_updates.append({"range": f"Equipment CCA!A1:J{len(cca)}", "values": cca})

    # ═══════════════════════════════════════════
    # TAB 7: TAX SUMMARY
    # ═══════════════════════════════════════════
    tax = [
        [f"TAX SUMMARY — {YEAR} (SOLE PROPRIETOR, BC)", "", "", "", ""],
        ["", "", "", "", ""],
        ["T2125 — STATEMENT OF BUSINESS INCOME", "", "", "", ""],
        ["", "", "", "", ""],
        ["Gross Business Income", f"='Income'!B2", "", "← Line 8299", ""],
        ["", "", "", "", ""],
        ["EXPENSES (from Business Expenses tab)", "", "", "", ""],
        ["Advertising", f"='Business Expenses'!B3", "", "← Line 8521", ""],
        ["Professional Fees", f"='Business Expenses'!B4", "", "← Line 8590", ""],
        ["Vehicle Expenses", f"='Business Expenses'!B5", "", "← Line 8615", ""],
        ["Insurance", f"='Business Expenses'!B6", "", "← Line 8690", ""],
        ["Interest & Bank Charges", f"='Business Expenses'!B7", "", "← Line 8710", ""],
        ["Office Supplies", f"='Business Expenses'!B8", "", "← Line 8811", ""],
        ["Rent", f"='Business Expenses'!B9", "", "← Line 8860", ""],
        ["Software/Subscriptions", f"='Business Expenses'!B10", "", "← Line 8871", ""],
        ["Travel", f"='Business Expenses'!B11", "", "← Line 8910", ""],
        ["Telephone/Internet", f"='Business Expenses'!B12", "", "← Line 8945", ""],
        ["Subcontractors", f"='Business Expenses'!B13", "", "← Line 9060", ""],
        ["Meals (50%)", f"='Business Expenses'!B14", "", "← Line 9270", ""],
        ["Home Office", f"='Business Expenses'!B15", "", "← Line 9281", ""],
        ["CCA (from Equipment tab)", f"='Equipment CCA'!G45", "", "← Line 9936", ""],
        ["Other Expenses", f"='Business Expenses'!B16", "", "", ""],
        ["Total Expenses", "=SUM(B8:B22)", "", "← Line 9369", ""],
        ["", "", "", "", ""],
        ["NET BUSINESS INCOME", "=B5-B23", "", "← Line 9946", ""],
        ["", "", "", "", ""],
        ["ESTIMATED TAX (2026 Rates)", "", "", "", ""],
        ["", "", "", "", ""],
        ["Federal Tax (est. 15% on first $57,375 + 20.5% above)", "=IF(B25<=57375,B25*0.15,57375*0.15+(B25-57375)*0.205)", "", "", ""],
        ["Basic Personal Amount Credit", -2506, "", "← $16,705 × 15%", ""],
        ["Federal Tax After Credits", "=MAX(0,B29+B30)", "", "", ""],
        ["", "", "", "", ""],
        ["BC Provincial Tax (5.06% on first $47,937 + 7.7% above)", "=IF(B25<=47937,B25*0.0506,47937*0.0506+(B25-47937)*0.077)", "", "", ""],
        ["BC Basic Personal Credit", -596, "", "← $11,981 × 5.06%", ""],
        ["BC Tax After Credits", "=MAX(0,B33+B34)", "", "", ""],
        ["", "", "", "", ""],
        ["TOTAL INCOME TAX (Est.)", "=B31+B35", "", "", ""],
        ["", "", "", "", ""],
        ["CPP SELF-EMPLOYMENT (2026 Est.)", "", "", "", ""],
        ["CPP Base Contribution", "=IF(B25>3500,MIN((B25-3500)*0.1190,7735.50),0)", "", "Employee + employer portions", ""],
        ["CPP2 (above $73,200)", "=IF(B25>73200,MIN((B25-73200)*0.08,396),0)", "", "Second ceiling contributions", ""],
        ["Total CPP", "=B40+B41", "", "", ""],
        ["", "", "", "", ""],
        ["TOTAL TAX + CPP", "=B37+B42", "", "", ""],
        ["", "", "", "", ""],
        ["QUARTERLY INSTALLMENTS", "", "", "", ""],
        ["Recommended Quarterly Payment", "=B44/4", "", "", ""],
        ["", "", "", "", ""],
        ["HOME OFFICE DEDUCTION CALCULATOR", "", "", "", ""],
        ["Total Home Sq Ft", "", "", "Enter your home size", ""],
        ["Office Sq Ft", "", "", "Enter office area", ""],
        ["Business Use %", "=IF(B50>0,B51/B50,0)", "", "", ""],
        ["", "", "", "", ""],
        ["Eligible Expenses:", "", "", "", ""],
        ["Rent/Mortgage Interest", "", "", "Annual amount", ""],
        ["Utilities", "", "", "Annual amount", ""],
        ["Insurance (Home)", "", "", "Annual amount", ""],
        ["Maintenance", "", "", "Annual amount", ""],
        ["Total Home Expenses", "=SUM(B55:B58)", "", "", ""],
        ["Home Office Deduction", "=B59*B52", "", "Enter on T2125 Line 9281", ""],
        ["", "", "", "", ""],
        ["RRSP", "", "", "", ""],
        ["Estimated RRSP Room (18% of earned income)", "=B25*0.18", "", "Max $32,490 for 2026", ""],
        ["RRSP Contributions Made", "", "", "Enter actual contributions", ""],
        ["Tax Savings from RRSP", "=B64*0.30", "", "Approx marginal rate 30%", ""],
    ]
    data_updates.append({"range": f"Tax Summary!A1:E{len(tax)}", "values": tax})

    # ═══════════════════════════════════════════
    # TAB 8: MONTHLY P&L
    # ═══════════════════════════════════════════
    pnl = [
        ["MONTHLY PROFIT & LOSS", "", "", "", "", "", ""],
        ["Month", "Revenue", "Business Expenses", "Net Profit", "Margin %", "Cumulative Revenue", "Cumulative Profit"],
    ]
    for i, m in enumerate(MONTHS):
        col = chr(ord('C') + i)
        row_num = i + 3
        pnl.append([
            m,
            f"='Income'!{col}2",
            f"='Business Expenses'!{col}2",
            f"=B{row_num}-C{row_num}",
            f"=IF(B{row_num}>0,D{row_num}/B{row_num},0)",
            f"=SUM(B$3:B{row_num})",
            f"=SUM(D$3:D{row_num})",
        ])
    pnl.append(["", "", "", "", "", "", ""])
    pnl.append(["ANNUAL TOTAL", "=SUM(B3:B14)", "=SUM(C3:C14)", "=SUM(D3:D14)",
                "=IF(B16>0,D16/B16,0)", "", ""])
    pnl.append(["", "", "", "", "", "", ""])
    pnl.append(["COMPARISON TO TARGET", "", "", "", "", "", ""])
    pnl.append(["Revenue Target", 172900, "", "", "", "", ""])
    pnl.append(["Actual Revenue", "=B16", "", "", "", "", ""])
    pnl.append(["Variance", "=B20-B19", "", "", "", "", ""])
    pnl.append(["% of Target", "=IF(B19>0,B20/B19,0)", "", "", "", "", ""])
    pnl.append(["", "", "", "", "", "", ""])
    pnl.append(["Monthly Avg Revenue", "=B16/MAX(1,COUNTA(B3:B14)-COUNTBLANK(B3:B14))", "", "", "", "", ""])
    pnl.append(["Months Remaining", f"=12-MONTH(TODAY())+1", "", "", "", "", ""])
    pnl.append(["Run Rate (Projected Annual)", "=B24*12", "", "", "", "", ""])

    data_updates.append({"range": f"Monthly P&L!A1:G{len(pnl)}", "values": pnl})

    # ═══════════════════════════════════════════
    # TAB 9: SAVINGS RECOMMENDATIONS
    # ═══════════════════════════════════════════
    savings = [
        [f"SAVINGS & TAX OPTIMIZATION — {YEAR}", ""],
        ["", ""],
        ["TAX DEDUCTIONS CHECKLIST", "Status"],
        ["Home office deduction claimed?", ""],
        ["Vehicle mileage log maintained?", ""],
        ["All equipment in CCA schedule?", ""],
        ["Professional development/courses deducted?", ""],
        ["Phone/internet business % claimed?", ""],
        ["All software subscriptions tracked?", ""],
        ["Meals with clients logged (50% deductible)?", ""],
        ["Insurance (equipment, liability) deducted?", ""],
        ["", ""],
        ["COST-SAVING OPPORTUNITIES", "Potential Savings"],
        ["Review software subscriptions — cancel unused", ""],
        ["Bundle insurance policies", ""],
        ["Track ALL mileage (many miss 20%+ of trips)", ""],
        ["Maximize RRSP before deadline", "=IF('Tax Summary'!B62-'Tax Summary'!B64>0,'Tax Summary'!B65,0)"],
        ["Claim home office (many sole props miss this)", "='Tax Summary'!B60"],
        ["GST ITCs — ensure ALL business GST claimed", ""],
        ["Time invoices to optimize quarterly installments", ""],
        ["", ""],
        ["SPENDING ALERTS", ""],
        ["Dining vs Groceries ratio", "=IF('Personal Expenses'!B5>0,'Personal Expenses'!B6/'Personal Expenses'!B5,\"N/A\")"],
        ["Business expense as % of revenue", "=IF('Income'!B2>0,'Business Expenses'!B2/'Income'!B2,\"N/A\")"],
        ["Personal spend as % of income", "=IF('Income'!B2>0,'Personal Expenses'!B2/'Income'!B2,\"N/A\")"],
        ["", ""],
        ["BC-SPECIFIC CONSIDERATIONS", ""],
        ["• BC PST is NOT reclaimable (unlike GST) — factor into costs", ""],
        ["• BC climate action tax credit — file to receive", ""],
        ["• BC Training Tax Credit — if any courses/workshops taken", ""],
        ["• ICBC — business use vehicle must be declared", ""],
        ["", ""],
        ["QUARTERLY REVIEW NOTES", ""],
        ["Q1 Review:", ""],
        ["Q2 Review:", ""],
        ["Q3 Review:", ""],
        ["Q4 Review:", ""],
    ]
    data_updates.append({"range": f"Savings Recs!A1:B{len(savings)}", "values": savings})

    # ── Batch update all data ──
    sheets_svc.spreadsheets().values().batchUpdate(
        spreadsheetId=ss_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": data_updates
        }
    ).execute()
    print("All data written.")

    # ── Formatting requests ──
    fmt_requests = []

    # Format Dashboard header
    fmt_requests.append(merge_cells(0, 0, 1, 0, 8))
    fmt_requests.append(format_range(0, 0, 1, 0, 8, bold=True, size=16, bg=DARK, fg=WHITE))

    # Format section headers on Dashboard
    fmt_requests.append(format_range(0, 2, 3, 0, 4, bold=True, size=12, bg=ACCENT, fg=WHITE))
    fmt_requests.append(format_range(0, 2, 3, 4, 8, bold=True, size=12, bg=ACCENT, fg=WHITE))
    fmt_requests.append(format_range(0, 4, 5, 0, 3, bold=True, bg=ACCENT_LIGHT))

    # Format all tab headers (row 1)
    for sheet_id in range(1, 10):
        fmt_requests.append(format_range(sheet_id, 0, 1, 0, 14, bold=True, size=11, bg=DARK, fg=WHITE))

    # Format Income categories
    fmt_requests.append(format_range(1, 1, 2, 0, 14, bold=True, bg=ACCENT_LIGHT))

    # Format Business Expenses - total row
    fmt_requests.append(format_range(2, 1, 2, 0, 14, bold=True, bg=ACCENT_LIGHT))

    # Format GST quarterly summary headers
    fmt_requests.append(format_range(4, 8, 9, 0, 8, bold=True, bg=ACCENT_LIGHT))

    # Format Tax Summary section headers
    fmt_requests.append(format_range(7, 2, 3, 0, 5, bold=True, size=12, bg=ACCENT, fg=WHITE))
    fmt_requests.append(format_range(7, 24, 25, 0, 5, bold=True, size=11, bg=GREEN_LIGHT))
    fmt_requests.append(format_range(7, 36, 37, 0, 5, bold=True, size=11, bg=YELLOW_LIGHT))
    fmt_requests.append(format_range(7, 43, 44, 0, 5, bold=True, size=12, bg=RED_LIGHT))

    # Format Monthly P&L header row
    fmt_requests.append(format_range(8, 1, 2, 0, 7, bold=True, bg=ACCENT_LIGHT))
    fmt_requests.append(format_range(8, 15, 16, 0, 7, bold=True, bg=ACCENT_LIGHT))

    # Format Savings Recs
    fmt_requests.append(format_range(9, 0, 1, 0, 2, bold=True, size=14, bg=DARK, fg=WHITE))
    fmt_requests.append(format_range(9, 2, 3, 0, 2, bold=True, bg=ACCENT, fg=WHITE))
    fmt_requests.append(format_range(9, 12, 13, 0, 2, bold=True, bg=GREEN, fg=WHITE))

    # Auto-resize columns for key tabs
    for sheet_id in [0, 1, 2, 3, 4, 7, 8]:
        fmt_requests.append({
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": 14
                }
            }
        })

    # Number formatting — currency for money columns
    for sheet_id in [1, 2, 3]:  # Income, Biz Expenses, Personal
        fmt_requests.append(number_format(sheet_id, 1, 200, 1, 14, "$#,##0.00"))

    # Percentage formatting on Dashboard
    fmt_requests.append(number_format(0, 7, 8, 2, 3, "0.0%"))  # Profit margin
    fmt_requests.append(number_format(0, 16, 17, 2, 3, "0.0%"))  # % complete

    # Percentage formatting on P&L
    fmt_requests.append(number_format(8, 2, 16, 4, 5, "0.0%"))

    # Currency on Tax Summary
    fmt_requests.append(number_format(7, 4, 65, 1, 2, "$#,##0.00"))

    # Currency on P&L
    fmt_requests.append(number_format(8, 2, 16, 1, 4, "$#,##0.00"))
    fmt_requests.append(number_format(8, 2, 16, 5, 7, "$#,##0.00"))

    # ── Add charts ──
    # Revenue vs Expenses bar chart on Dashboard
    fmt_requests.append({
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Monthly Revenue vs Expenses",
                    "basicChart": {
                        "chartType": "COLUMN",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {"position": "BOTTOM_AXIS", "title": "Month"},
                            {"position": "LEFT_AXIS", "title": "Amount ($)"},
                        ],
                        "domains": [{
                            "domain": {"sourceRange": {"sources": [{"sheetId": 8, "startRowIndex": 1, "endRowIndex": 14, "startColumnIndex": 0, "endColumnIndex": 1}]}}
                        }],
                        "series": [
                            {"series": {"sourceRange": {"sources": [{"sheetId": 8, "startRowIndex": 1, "endRowIndex": 14, "startColumnIndex": 1, "endColumnIndex": 2}]}}, "color": {"red": 0.16, "green": 0.50, "blue": 0.73}},
                            {"series": {"sourceRange": {"sources": [{"sheetId": 8, "startRowIndex": 1, "endRowIndex": 14, "startColumnIndex": 2, "endColumnIndex": 3}]}}, "color": {"red": 0.80, "green": 0.20, "blue": 0.20}},
                        ],
                        "headerCount": 1,
                    }
                },
                "position": {"overlayPosition": {"anchorCell": {"sheetId": 0, "rowIndex": 4, "columnIndex": 4}, "widthPixels": 600, "heightPixels": 300}}
            }
        }
    })

    # Cumulative revenue line chart
    fmt_requests.append({
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Cumulative Revenue vs Target",
                    "basicChart": {
                        "chartType": "LINE",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {"position": "BOTTOM_AXIS", "title": "Month"},
                            {"position": "LEFT_AXIS", "title": "Revenue ($)"},
                        ],
                        "domains": [{
                            "domain": {"sourceRange": {"sources": [{"sheetId": 8, "startRowIndex": 1, "endRowIndex": 14, "startColumnIndex": 0, "endColumnIndex": 1}]}}
                        }],
                        "series": [
                            {"series": {"sourceRange": {"sources": [{"sheetId": 8, "startRowIndex": 1, "endRowIndex": 14, "startColumnIndex": 5, "endColumnIndex": 6}]}}, "color": {"red": 0.16, "green": 0.50, "blue": 0.73}},
                            {"series": {"sourceRange": {"sources": [{"sheetId": 8, "startRowIndex": 1, "endRowIndex": 14, "startColumnIndex": 6, "endColumnIndex": 7}]}}, "color": {"red": 0.22, "green": 0.56, "blue": 0.24}},
                        ],
                        "headerCount": 1,
                    }
                },
                "position": {"overlayPosition": {"anchorCell": {"sheetId": 8, "rowIndex": 17, "columnIndex": 0}, "widthPixels": 700, "heightPixels": 350}}
            }
        }
    })

    # Expense category pie chart on Dashboard
    fmt_requests.append({
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Top Business Expense Categories",
                    "pieChart": {
                        "legendPosition": "RIGHT_LEGEND",
                        "domain": {"sourceRange": {"sources": [{"sheetId": 0, "startRowIndex": 20, "endRowIndex": 25, "startColumnIndex": 0, "endColumnIndex": 1}]}},
                        "series": {"sourceRange": {"sources": [{"sheetId": 0, "startRowIndex": 20, "endRowIndex": 25, "startColumnIndex": 1, "endColumnIndex": 2}]}},
                    }
                },
                "position": {"overlayPosition": {"anchorCell": {"sheetId": 0, "rowIndex": 18, "columnIndex": 4}, "widthPixels": 450, "heightPixels": 300}}
            }
        }
    })

    # Execute all formatting
    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=ss_id,
        body={"requests": fmt_requests}
    ).execute()
    print("Formatting and charts applied.")

    # ── Save spreadsheet ID to .env ──
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, ".env")
    env_content = ""
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            env_content = f.read()
    if "FINANCE_SHEET_ID" not in env_content:
        with open(env_path, "a") as f:
            f.write(f"\nFINANCE_SHEET_ID={ss_id}\n")
    print(f"\nSpreadsheet ID saved to .env")
    print(f"\nDone! Open your sheet: {ss_url}")
    return ss_id, ss_url


def merge_cells(sheet_id, start_row, end_row, start_col, end_col):
    return {
        "mergeCells": {
            "range": {"sheetId": sheet_id, "startRowIndex": start_row, "endRowIndex": end_row, "startColumnIndex": start_col, "endColumnIndex": end_col},
            "mergeType": "MERGE_ALL"
        }
    }


def format_range(sheet_id, start_row, end_row, start_col, end_col, bold=False, size=10, bg=None, fg=None):
    fmt = {"textFormat": {"bold": bold, "fontSize": size}}
    if fg:
        fmt["textFormat"]["foregroundColorStyle"] = {"rgbColor": fg}
    if bg:
        fmt["backgroundColor"] = bg
    return {
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": start_row, "endRowIndex": end_row, "startColumnIndex": start_col, "endColumnIndex": end_col},
            "cell": {"userEnteredFormat": fmt},
            "fields": "userEnteredFormat(textFormat,backgroundColor)"
        }
    }


def number_format(sheet_id, start_row, end_row, start_col, end_col, pattern):
    return {
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": start_row, "endRowIndex": end_row, "startColumnIndex": start_col, "endColumnIndex": end_col},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": pattern}}},
            "fields": "userEnteredFormat.numberFormat"
        }
    }


if __name__ == "__main__":
    ss_id, ss_url = create_spreadsheet()
