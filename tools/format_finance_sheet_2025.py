"""
Comprehensive formatting for the 2025 Finance Google Sheet.
Applies a consistent design system to all 12 tabs.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_sheets_service

SHEET_ID = '1TyX4sOIo6CxblxjNM9Yft5h5vZO_BGhQjHlgC0uzQtI'

# ── Design System Colors ───────────────────────────────────────────────────────
NAVY       = {"red": 0.153, "green": 0.173, "blue": 0.224}   # #272C39 headers/titles
BLUE       = {"red": 0.224, "green": 0.443, "blue": 0.871}   # #3971DE revenue/income
BLUE_BG    = {"red": 0.922, "green": 0.941, "blue": 0.988}   # #EBF0FC
GREEN      = {"red": 0.118, "green": 0.624, "blue": 0.424}   # #1E9F6C profit/positive
GREEN_BG   = {"red": 0.906, "green": 0.969, "blue": 0.941}   # #E7F7F0
RED        = {"red": 0.851, "green": 0.200, "blue": 0.200}   # #D93333 expenses/negative
RED_BG     = {"red": 0.992, "green": 0.929, "blue": 0.929}   # #FDEDED
ORANGE     = {"red": 0.902, "green": 0.533, "blue": 0.118}   # #E6881E totals/warnings
ORANGE_BG  = {"red": 0.996, "green": 0.953, "blue": 0.906}   # #FEF3E7
PURPLE     = {"red": 0.486, "green": 0.318, "blue": 0.804}   # #7C51CD personal
PURPLE_BG  = {"red": 0.949, "green": 0.933, "blue": 0.988}   # #F2EEFC
WHITE      = {"red": 1.0,   "green": 1.0,   "blue": 1.0}
ALT_ROW    = {"red": 0.965, "green": 0.969, "blue": 0.976}   # #F7F8FA
BORDER_CLR = {"red": 0.890, "green": 0.898, "blue": 0.910}   # #E3E5E8
TEXT_PRI   = {"red": 0.098, "green": 0.114, "blue": 0.149}   # #191D26
TEXT_SEC   = {"red": 0.549, "green": 0.573, "blue": 0.612}   # #8C929C
TEXT_MUTED = {"red": 0.702, "green": 0.718, "blue": 0.745}   # #B3B7BE

# ── Helper utilities ──────────────────────────────────────────────────────────
def gr(sid, sr, er, sc, ec):
    return {"sheetId": sid, "startRowIndex": sr, "endRowIndex": er,
            "startColumnIndex": sc, "endColumnIndex": ec}

def repeat_cell(sid, sr, er, sc, ec, fmt, fields):
    return {"repeatCell": {"range": gr(sid, sr, er, sc, ec),
                           "cell": {"userEnteredFormat": fmt}, "fields": fields}}

def merge(sid, sr, er, sc, ec):
    return {"mergeCells": {"range": gr(sid, sr, er, sc, ec), "mergeType": "MERGE_ALL"}}

def row_height(sid, row0, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": row0, "endIndex": row0+1},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def rows_height(sid, row0, row1, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": row0, "endIndex": row1},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def col_width(sid, col0, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": col0, "endIndex": col0+1},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def cols_width(sid, col0, col1, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": col0, "endIndex": col1},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def freeze(sid, rows=0, cols=0):
    props = {"sheetId": sid, "gridProperties": {}}
    fields = []
    if rows: props["gridProperties"]["frozenRowCount"] = rows; fields.append("gridProperties.frozenRowCount")
    if cols: props["gridProperties"]["frozenColumnCount"] = cols; fields.append("gridProperties.frozenColumnCount")
    return {"updateSheetProperties": {"properties": props, "fields": ",".join(fields)}}

def border_bottom(sid, row0, sc, ec, color=None, style="SOLID", width=1):
    c = color or BORDER_CLR
    return {"updateBorders": {"range": gr(sid, row0, row0+1, sc, ec),
                              "bottom": {"style": style, "width": width, "color": c}}}

def border_top(sid, row0, sc, ec, color=None, style="SOLID", width=2):
    c = color or BORDER_CLR
    return {"updateBorders": {"range": gr(sid, row0, row0+1, sc, ec),
                              "top": {"style": style, "width": width, "color": c}}}

# Common format field strings
F_BG       = "userEnteredFormat.backgroundColor"
F_TF       = "userEnteredFormat.textFormat"
F_NF       = "userEnteredFormat.numberFormat"
F_AL       = "userEnteredFormat.horizontalAlignment"
F_BG_TF    = "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat"
F_BG_TF_NF = "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.numberFormat"
F_BG_NF    = "userEnteredFormat.backgroundColor,userEnteredFormat.numberFormat"
F_TF_NF    = "userEnteredFormat.textFormat,userEnteredFormat.numberFormat"
F_ALL      = "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment"

def tf(bold=False, size=10, color=None, italic=False):
    t = {"fontFamily": "Inter", "fontSize": size}
    if bold: t["bold"] = True
    if italic: t["italic"] = True
    if color: t["foregroundColor"] = color
    return t

def nf_money(decimals=0):
    return {"type": "CURRENCY", "pattern": "$#,##0" if decimals == 0 else "$#,##0.00"}

def nf_pct():
    return {"type": "PERCENT", "pattern": "0.0%"}

def nf_num():
    return {"type": "NUMBER", "pattern": "#,##0"}

# ── Reusable section builders ─────────────────────────────────────────────────

def fmt_title_row(reqs, sid, row0, sc, ec, text_color=NAVY, bg=WHITE, size=20, merge_cols=True):
    """Bold large title cell."""
    reqs.append(repeat_cell(sid, row0, row0+1, sc, ec,
        {"backgroundColor": bg, "textFormat": tf(bold=True, size=size, color=text_color),
         "verticalAlignment": "MIDDLE"},
        F_BG_TF + ",userEnteredFormat.verticalAlignment"))
    reqs.append(row_height(sid, row0, 46))
    if merge_cols and ec - sc > 1:
        reqs.append(merge(sid, row0, row0+1, sc, ec))

def fmt_subtitle_row(reqs, sid, row0, sc, ec):
    """10pt muted subtitle."""
    reqs.append(repeat_cell(sid, row0, row0+1, sc, ec,
        {"backgroundColor": WHITE, "textFormat": tf(size=10, color=TEXT_MUTED)},
        F_BG_TF))
    reqs.append(row_height(sid, row0, 22))
    if ec - sc > 1:
        reqs.append(merge(sid, row0, row0+1, sc, ec))

def fmt_section_header(reqs, sid, row0, sc, ec, color=NAVY, bg=WHITE):
    """Bold 14pt navy section header with bottom border."""
    reqs.append(repeat_cell(sid, row0, row0+1, sc, ec,
        {"backgroundColor": bg,
         "textFormat": tf(bold=True, size=14, color=color),
         "verticalAlignment": "MIDDLE"},
        F_BG_TF + ",userEnteredFormat.verticalAlignment"))
    reqs.append(border_bottom(sid, row0, sc, ec, color=BORDER_CLR, style="SOLID", width=2))
    reqs.append(row_height(sid, row0, 34))
    if ec - sc > 1:
        reqs.append(merge(sid, row0, row0+1, sc, ec))

def fmt_col_headers(reqs, sid, row0, sc, ec):
    """Bold 9pt secondary col headers on white with bottom border."""
    reqs.append(repeat_cell(sid, row0, row0+1, sc, ec,
        {"backgroundColor": WHITE,
         "textFormat": tf(bold=True, size=9, color=TEXT_SEC)},
        F_BG_TF))
    reqs.append(border_bottom(sid, row0, sc, ec, color=BORDER_CLR))
    reqs.append(row_height(sid, row0, 30))

def fmt_data_rows(reqs, sid, row0, row1, sc, ec, money_cols=None, pct_cols=None, right_cols=None):
    """Alternating white/alt rows, 10pt primary text, 26px height."""
    reqs.append(rows_height(sid, row0, row1, 26))
    for i in range(row1 - row0):
        bg = WHITE if i % 2 == 0 else ALT_ROW
        reqs.append(repeat_cell(sid, row0+i, row0+i+1, sc, ec,
            {"backgroundColor": bg, "textFormat": tf(size=10, color=TEXT_PRI)},
            F_BG_TF))
    if money_cols:
        for col in money_cols:
            reqs.append(repeat_cell(sid, row0, row1, col, col+1,
                {"numberFormat": nf_money(), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    if pct_cols:
        for col in pct_cols:
            reqs.append(repeat_cell(sid, row0, row1, col, col+1,
                {"numberFormat": nf_pct(), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    if right_cols:
        for col in right_cols:
            reqs.append(repeat_cell(sid, row0, row1, col, col+1,
                {"horizontalAlignment": "RIGHT"}, F_AL))

def fmt_total_row(reqs, sid, row0, sc, ec, bg_color, text_color, money_cols=None, pct_cols=None, size=11):
    """Bold total row with colored bg and top border."""
    reqs.append(repeat_cell(sid, row0, row0+1, sc, ec,
        {"backgroundColor": bg_color,
         "textFormat": tf(bold=True, size=size, color=text_color)},
        F_BG_TF))
    reqs.append(border_top(sid, row0, sc, ec, color=text_color, style="SOLID", width=2))
    reqs.append(row_height(sid, row0, 30))
    if money_cols:
        for col in money_cols:
            reqs.append(repeat_cell(sid, row0, row0+1, col, col+1,
                {"numberFormat": nf_money(), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    if pct_cols:
        for col in pct_cols:
            reqs.append(repeat_cell(sid, row0, row0+1, col, col+1,
                {"numberFormat": nf_pct(), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))

def fmt_spacer(reqs, sid, row0):
    reqs.append(row_height(sid, row0, 16))
    reqs.append(repeat_cell(sid, row0, row0+1, 0, 12,
        {"backgroundColor": WHITE}, F_BG))


# =============================================================================
# MAIN
# =============================================================================
def main():
    service = get_sheets_service()
    ss = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    sheets = {s['properties']['title']: s['properties']['sheetId'] for s in ss['sheets']}
    print("Sheet IDs:", sheets)

    reqs = []

    dash_id = sheets['Dashboard']
    txn_id  = sheets['Transactions']
    inc_id  = sheets['Income']
    exp_id  = sheets['Expenses']
    bus_id  = sheets['Business']
    per_id  = sheets['Personal']
    pl_id   = sheets['P&L']
    mil_id  = sheets['Mileage']
    gst_id  = sheets['GST']
    eqp_id  = sheets['Equipment']
    tax_id  = sheets['Tax']
    ins_id  = sheets['Insights']

    # =========================================================================
    # TAB: Dashboard
    # =========================================================================
    # Layout: cols C onward (index 2+). Title at R2, subtitle R3, KPIs R5-7,
    # Tax R10-13, Monthly R15-29, GST R31-32, Cash Flow R38-52, Ratios R55-62
    # All content is offset 2 cols right (cols A,B are blank spacers)
    D = dash_id

    # Global bg for dashboard
    reqs.append(repeat_cell(D, 0, 75, 0, 10,
        {"backgroundColor": WHITE, "textFormat": tf(size=10, color=TEXT_PRI)}, F_BG_TF))

    # Title / subtitle (rows 1,2 → 0-indexed)
    fmt_title_row(reqs, D, 1, 2, 9)       # R2
    fmt_subtitle_row(reqs, D, 2, 2, 9)    # R3

    # Spacer row 0, 3-4
    reqs.append(row_height(D, 0, 16))
    reqs.append(row_height(D, 3, 16))
    reqs.append(row_height(D, 4, 16))

    # KPI section R5-7 (rows 4-6)
    # R5: labels bold secondary
    reqs.append(repeat_cell(D, 4, 5, 2, 9,
        {"textFormat": tf(bold=True, size=9, color=TEXT_SEC)}, F_TF))
    reqs.append(row_height(D, 4, 26))

    # R6: big KPI numbers
    reqs.append(repeat_cell(D, 5, 6, 2, 4,
        {"textFormat": tf(bold=True, size=26, color=BLUE)}, F_TF))  # Revenue
    reqs.append(repeat_cell(D, 5, 6, 6, 8,
        {"textFormat": tf(bold=True, size=26, color=RED)}, F_TF))   # Expenses
    reqs.append(row_height(D, 5, 48))

    # R7: sub-labels
    reqs.append(repeat_cell(D, 6, 7, 2, 9,
        {"textFormat": tf(size=9, color=TEXT_MUTED)}, F_TF))
    reqs.append(row_height(D, 6, 22))

    # KPI card backgrounds (blue for revenue, red for expenses)
    reqs.append(repeat_cell(D, 4, 8, 2, 5,
        {"backgroundColor": BLUE_BG}, F_BG))
    reqs.append(repeat_cell(D, 4, 8, 6, 9,
        {"backgroundColor": RED_BG}, F_BG))

    # Spacer rows 7-9
    reqs.append(row_height(D, 7, 16))
    reqs.append(row_height(D, 8, 16))
    reqs.append(row_height(D, 9, 16))

    # Tax breakdown section R10 header, R11-13 data
    fmt_section_header(reqs, D, 9, 2, 9)  # R10

    # R11-13: tax rows
    reqs.append(repeat_cell(D, 10, 13, 2, 9,
        {"textFormat": tf(size=10, color=TEXT_PRI)}, F_TF))
    for r in range(10, 13):
        reqs.append(row_height(D, r, 26))
    # Amounts in bold navy
    reqs.append(repeat_cell(D, 10, 13, 3, 4,
        {"textFormat": tf(bold=True, size=10, color=NAVY)}, F_TF))
    reqs.append(repeat_cell(D, 10, 13, 6, 7,
        {"textFormat": tf(bold=True, size=10, color=NAVY)}, F_TF))
    # Total row R13
    reqs.append(repeat_cell(D, 12, 13, 2, 9,
        {"backgroundColor": ORANGE_BG,
         "textFormat": tf(bold=True, size=10, color=ORANGE)}, F_BG_TF))
    reqs.append(border_top(D, 12, 2, 9, color=ORANGE))

    # Spacer R14
    reqs.append(row_height(D, 13, 16))

    # Monthly Breakdown R15 header, R16 col headers, R17-28 data, R29 total
    fmt_section_header(reqs, D, 14, 2, 9)  # R15
    fmt_col_headers(reqs, D, 15, 2, 9)     # R16
    # Data rows R17-28 (indices 16-27)
    fmt_data_rows(reqs, D, 16, 28, 2, 9,
                  money_cols=[3, 4, 5], pct_cols=[6])
    # Profit/margin color: col 5 (Net) text colored
    reqs.append(repeat_cell(D, 16, 28, 5, 6,
        {"textFormat": tf(bold=True, size=10, color=GREEN)}, F_TF))
    # Total row R29
    fmt_total_row(reqs, D, 28, 2, 9, BLUE_BG, BLUE,
                  money_cols=[3, 4, 5], pct_cols=[6])

    # Spacer R30
    reqs.append(row_height(D, 29, 16))

    # GST Summary R31 (header + data combined)
    fmt_section_header(reqs, D, 30, 2, 9)  # R31
    reqs.append(repeat_cell(D, 31, 32, 2, 9,
        {"textFormat": tf(size=10, color=TEXT_PRI)}, F_TF))
    reqs.append(row_height(D, 31, 26))
    # Collected green, ITCs red
    reqs.append(repeat_cell(D, 31, 32, 3, 4,
        {"textFormat": tf(bold=True, size=10, color=GREEN)}, F_TF))
    reqs.append(repeat_cell(D, 31, 32, 6, 7,
        {"textFormat": tf(bold=True, size=10, color=RED)}, F_TF))

    # Spacers R33-37
    for r in [32, 33, 34, 35, 36]:
        reqs.append(row_height(D, r, 16))

    # Monthly Cash Flow section R38 header, R39 col headers, R40-51 data, R52 total
    fmt_section_header(reqs, D, 37, 2, 9)  # R38
    fmt_col_headers(reqs, D, 38, 2, 9)     # R39
    # Data rows R40-51 (indices 39-50)
    reqs.append(rows_height(D, 39, 51, 26))
    for i in range(12):
        bg = WHITE if i % 2 == 0 else ALT_ROW
        reqs.append(repeat_cell(D, 39+i, 40+i, 2, 9,
            {"backgroundColor": bg, "textFormat": tf(size=10, color=TEXT_PRI)}, F_BG_TF))
    # Money format cols D-G (3-6)
    reqs.append(repeat_cell(D, 39, 51, 3, 7,
        {"numberFormat": nf_money(), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    # Net (col 5) colored
    reqs.append(repeat_cell(D, 39, 51, 5, 6,
        {"textFormat": tf(bold=True, size=10, color=GREEN)}, F_TF))
    # Total row R52
    fmt_total_row(reqs, D, 51, 2, 9, BLUE_BG, BLUE, money_cols=[3, 4, 5, 6])

    # Spacers R53-54
    reqs.append(row_height(D, 52, 16))
    reqs.append(row_height(D, 53, 16))

    # Key Ratios R55 header, R56 col headers, R57-62 data
    fmt_section_header(reqs, D, 54, 2, 9)   # R55
    fmt_col_headers(reqs, D, 55, 2, 9)      # R56
    # Data rows R57-62 (indices 56-61)
    reqs.append(rows_height(D, 56, 62, 26))
    for i in range(6):
        bg = WHITE if i % 2 == 0 else ALT_ROW
        reqs.append(repeat_cell(D, 56+i, 57+i, 2, 9,
            {"backgroundColor": bg, "textFormat": tf(size=10, color=TEXT_PRI)}, F_BG_TF))
    # Values in bold colored
    ratio_colors = [GREEN, RED, GREEN, ORANGE, ORANGE, BLUE]
    for i, c in enumerate(ratio_colors):
        reqs.append(repeat_cell(D, 56+i, 57+i, 3, 4,
            {"textFormat": tf(bold=True, size=10, color=c),
             "numberFormat": nf_pct(), "horizontalAlignment": "RIGHT"}, F_TF_NF + "," + F_AL))

    # Dashboard col widths (A-J)
    for ci, w in enumerate([24, 24, 160, 110, 130, 110, 130, 110, 130, 130]):
        reqs.append(col_width(D, ci, w))

    # Freeze row 1
    reqs.append(freeze(D, rows=1))

    print("  Dashboard: formatted")

    # =========================================================================
    # TAB: Transactions (just verify freeze, apply consistent header)
    # =========================================================================
    T = txn_id
    reqs.append(freeze(T, rows=3))
    # Row 1: title
    reqs.append(repeat_cell(T, 0, 1, 0, 12,
        {"backgroundColor": NAVY,
         "textFormat": tf(bold=True, size=14, color=WHITE)}, F_BG_TF))
    reqs.append(row_height(T, 0, 44))
    # Row 2: subtitle
    reqs.append(repeat_cell(T, 1, 2, 0, 12,
        {"backgroundColor": NAVY,
         "textFormat": tf(size=9, color=TEXT_MUTED)}, F_BG_TF))
    reqs.append(row_height(T, 1, 22))
    # Row 3: col headers
    reqs.append(repeat_cell(T, 2, 3, 0, 12,
        {"backgroundColor": WHITE,
         "textFormat": tf(bold=True, size=9, color=TEXT_SEC)}, F_BG_TF))
    reqs.append(border_bottom(T, 2, 0, 12))
    reqs.append(row_height(T, 2, 30))
    print("  Transactions: freeze + header formatted")

    # =========================================================================
    # TAB: Income
    # =========================================================================
    I = inc_id
    reqs.append(repeat_cell(I, 0, 45, 0, 15,
        {"backgroundColor": WHITE, "textFormat": tf(size=10, color=TEXT_PRI)}, F_BG_TF))

    # R2: title (row 1), R3: subtitle (row 2)
    fmt_title_row(reqs, I, 1, 1, 8)
    # KPI in title row: right side
    reqs.append(repeat_cell(I, 1, 2, 4, 5,
        {"textFormat": tf(bold=True, size=9, color=TEXT_SEC)}, F_TF))
    reqs.append(repeat_cell(I, 1, 2, 5, 6,
        {"textFormat": tf(bold=True, size=16, color=GREEN)}, F_TF))
    fmt_subtitle_row(reqs, I, 2, 1, 8)

    # Spacer R4
    reqs.append(row_height(I, 3, 16))

    # R5: col headers (row 4) — multi-month spanning
    fmt_col_headers(reqs, I, 4, 1, 14)

    # R6: continuation header row (row 5)
    reqs.append(repeat_cell(I, 5, 6, 1, 14,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, size=9, color=TEXT_SEC)}, F_BG_TF))
    reqs.append(border_bottom(I, 5, 1, 14, color=BORDER_CLR))
    reqs.append(row_height(I, 5, 30))

    # R7-13: data rows (indices 6-12, 7 rows of source data)
    fmt_data_rows(reqs, I, 6, 13, 1, 14, money_cols=list(range(2, 14)))

    # Spacer R14
    reqs.append(row_height(I, 13, 16))

    # R15: TOTAL (index 14)
    fmt_total_row(reqs, I, 14, 1, 14, BLUE_BG, BLUE, money_cols=list(range(2, 14)))

    # Spacer R16
    reqs.append(row_height(I, 15, 16))

    # R17: Monthly Revenue section header (index 16)
    fmt_section_header(reqs, I, 16, 1, 4)

    # R18: col headers (index 17)
    fmt_col_headers(reqs, I, 17, 1, 4)

    # R19-30: monthly data (indices 18-29)
    fmt_data_rows(reqs, I, 18, 30, 1, 4, money_cols=[2])

    # R31: total (index 30)
    fmt_total_row(reqs, I, 30, 1, 4, BLUE_BG, BLUE, money_cols=[2])

    # Income col widths
    for ci, w in enumerate([24, 200, 110, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80]):
        reqs.append(col_width(I, ci, w))

    reqs.append(freeze(I, rows=2))
    print("  Income: formatted")

    # =========================================================================
    # TAB: Expenses
    # =========================================================================
    E = exp_id
    reqs.append(repeat_cell(E, 0, 45, 0, 10,
        {"backgroundColor": WHITE, "textFormat": tf(size=10, color=TEXT_PRI)}, F_BG_TF))

    # R2: title (row 1), R3: subtitle (row 2)
    fmt_title_row(reqs, E, 1, 1, 8)
    # KPIs in title
    reqs.append(repeat_cell(E, 1, 2, 4, 5,
        {"textFormat": tf(bold=True, size=9, color=TEXT_SEC)}, F_TF))
    reqs.append(repeat_cell(E, 1, 2, 5, 6,
        {"textFormat": tf(bold=True, size=16, color=ORANGE)}, F_TF))
    reqs.append(repeat_cell(E, 1, 2, 7, 8,
        {"textFormat": tf(bold=True, size=9, color=TEXT_SEC)}, F_TF))
    fmt_subtitle_row(reqs, E, 2, 1, 8)

    # Spacer R4
    reqs.append(row_height(E, 3, 16))

    # R5: BUSINESS EXPENSES section header (row 4)
    fmt_section_header(reqs, E, 4, 1, 7, color=ORANGE)

    # R6: col headers (row 5)
    fmt_col_headers(reqs, E, 5, 1, 7)

    # R6-20: business expense rows (rows 5-19 = indices 5-19, 15 rows)
    fmt_data_rows(reqs, E, 6, 21, 1, 7, money_cols=[4, 5])

    # Spacer R22 (index 21)
    reqs.append(row_height(E, 21, 16))

    # R22: TOTAL BUSINESS (index 21)
    fmt_total_row(reqs, E, 21, 1, 7, ORANGE_BG, ORANGE, money_cols=[4, 5])

    # Spacer R23 (index 22)
    reqs.append(row_height(E, 22, 16))

    # R24: PERSONAL EXPENSES section header (index 23)
    fmt_section_header(reqs, E, 23, 1, 7, color=PURPLE)

    # R25: col headers (index 24)
    fmt_col_headers(reqs, E, 24, 1, 7)

    # R25-33: personal rows (indices 25-32, 8 rows - Housing through Clothing)
    fmt_data_rows(reqs, E, 25, 34, 1, 7, money_cols=[4, 5])

    # Spacer R34 (index 33)
    reqs.append(row_height(E, 33, 16))

    # R35: TOTAL PERSONAL (index 34)
    fmt_total_row(reqs, E, 34, 1, 7, PURPLE_BG, PURPLE, money_cols=[4, 5])

    # Expenses col widths
    for ci, w in enumerate([24, 220, 60, 70, 110, 100, 100]):
        reqs.append(col_width(E, ci, w))

    reqs.append(freeze(E, rows=2))
    print("  Expenses: formatted")

    # =========================================================================
    # TAB: Business
    # =========================================================================
    B = bus_id
    reqs.append(repeat_cell(B, 0, 45, 0, 12,
        {"backgroundColor": WHITE, "textFormat": tf(size=10, color=TEXT_PRI)}, F_BG_TF))

    # R1: col headers (index 0) — no title row on this tab
    # Add a proper title banner
    # Shift: insert formatting for row 0 as col headers since the tab starts directly with data
    # According to actual data: R1 = col headers (index 0), R2-17 = data, R18 = TOTAL
    fmt_col_headers(reqs, B, 0, 0, 14)

    # Data rows R2-17 (indices 1-16, 16 rows)
    fmt_data_rows(reqs, B, 1, 17, 0, 14, money_cols=list(range(2, 14)))

    # R18: TOTAL (index 17)
    fmt_total_row(reqs, B, 17, 0, 14, ORANGE_BG, ORANGE, money_cols=list(range(2, 14)))

    # Spacers R19-22 (indices 18-21)
    for r in [18, 19, 20, 21]:
        reqs.append(row_height(B, r, 16))

    # R23: BUDGET section header (index 22)
    fmt_section_header(reqs, B, 22, 0, 7, color=NAVY)

    # R24: budget col headers (index 23)
    fmt_col_headers(reqs, B, 23, 0, 7)

    # R25-39: budget data rows (indices 24-38, 15 rows)
    fmt_data_rows(reqs, B, 24, 39, 0, 7, money_cols=[1, 2, 3, 4, 5])
    # Status col G (index 6) colored
    for i in range(15):
        row_0 = 24 + i
        # ON TRACK rows keep text, OVER rows get red text
        reqs.append(repeat_cell(B, row_0, row_0+1, 6, 7,
            {"textFormat": tf(bold=True, size=10, color=TEXT_PRI)}, F_TF))

    # R40: TOTAL budget row (index 39)
    fmt_total_row(reqs, B, 39, 0, 7, ORANGE_BG, ORANGE, money_cols=[1, 2, 3, 4, 5])

    # Business col widths - many months
    bus_col_widths = [220, 70, 90, 75, 75, 75, 75, 75, 75, 75, 75, 75, 75, 75, 75]
    for ci, w in enumerate(bus_col_widths[:14]):
        reqs.append(col_width(B, ci, w))

    reqs.append(freeze(B, rows=1))
    print("  Business: formatted")

    # =========================================================================
    # TAB: Personal
    # =========================================================================
    P = per_id
    reqs.append(repeat_cell(P, 0, 55, 0, 16,
        {"backgroundColor": WHITE, "textFormat": tf(size=10, color=TEXT_PRI)}, F_BG_TF))

    # R1: col headers (index 0)
    fmt_col_headers(reqs, P, 0, 0, 16)

    # R2-14: data rows (indices 1-13, 13 rows)
    fmt_data_rows(reqs, P, 1, 14, 0, 16, money_cols=list(range(1, 14)))

    # R15: TOTAL (index 14)
    fmt_total_row(reqs, P, 14, 0, 16, PURPLE_BG, PURPLE, money_cols=list(range(1, 14)))

    # Spacers R16-19 (indices 15-18)
    for r in [15, 16, 17, 18]:
        reqs.append(row_height(P, r, 16))

    # R20: Personal Insights section header (index 19)
    fmt_section_header(reqs, P, 19, 0, 5, color=PURPLE)

    # R21: col headers (index 20)
    fmt_col_headers(reqs, P, 20, 0, 5)

    # R22-28: insights data rows (indices 21-27, 7 rows)
    fmt_data_rows(reqs, P, 21, 28, 0, 5)
    # Format value col (B=1)
    reqs.append(repeat_cell(P, 21, 22, 1, 2,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    for r in [22, 23, 27]:
        reqs.append(repeat_cell(P, r, r+1, 1, 2,
            {"numberFormat": nf_money(), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(repeat_cell(P, 24, 25, 1, 2,
        {"numberFormat": nf_pct(), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))

    # Spacer R29
    reqs.append(row_height(P, 28, 16))

    # R30: Monthly trend subsection header (index 29)
    fmt_section_header(reqs, P, 29, 0, 4, color=PURPLE, bg=PURPLE_BG)

    # R31: col headers (index 30)
    fmt_col_headers(reqs, P, 30, 0, 4)

    # R32-43: monthly trend data (indices 31-42, 12 rows)
    fmt_data_rows(reqs, P, 31, 43, 0, 3, money_cols=[1])

    # Personal col widths
    per_col_widths = [200, 90, 75, 75, 75, 75, 75, 75, 75, 75, 75, 75, 75, 75, 75]
    for ci, w in enumerate(per_col_widths[:14]):
        reqs.append(col_width(P, ci, w))

    reqs.append(freeze(P, rows=1))
    print("  Personal: formatted")

    # =========================================================================
    # TAB: P&L
    # =========================================================================
    PL = pl_id
    reqs.append(repeat_cell(PL, 0, 20, 0, 12,
        {"backgroundColor": WHITE, "textFormat": tf(size=10, color=TEXT_PRI)}, F_BG_TF))

    # R1: col headers (index 0)
    fmt_col_headers(reqs, PL, 0, 0, 8)

    # R2-13: monthly data (indices 1-12, 12 rows)
    fmt_data_rows(reqs, PL, 1, 13, 0, 8,
                  money_cols=[1, 2, 3, 5, 6, 7], pct_cols=[4])
    # Revenue col blue, Expense col red, Profit col green/red
    reqs.append(repeat_cell(PL, 1, 13, 1, 2,
        {"textFormat": tf(bold=False, size=10, color=BLUE)}, F_TF))
    reqs.append(repeat_cell(PL, 1, 13, 2, 3,
        {"textFormat": tf(bold=False, size=10, color=RED)}, F_TF))
    reqs.append(repeat_cell(PL, 1, 13, 3, 4,
        {"textFormat": tf(bold=True, size=10, color=GREEN)}, F_TF))

    # Spacer R14 (index 13)
    reqs.append(row_height(PL, 13, 16))

    # R15: TOTAL (index 14)
    fmt_total_row(reqs, PL, 14, 0, 8, BLUE_BG, BLUE,
                  money_cols=[1, 2, 3, 5, 6, 7], pct_cols=[4])

    # P&L col widths
    for ci, w in enumerate([80, 100, 100, 100, 80, 100, 110, 100]):
        reqs.append(col_width(PL, ci, w))

    reqs.append(freeze(PL, rows=1))
    print("  P&L: formatted")

    # =========================================================================
    # TAB: Mileage (long tab, ~250+ rows across all months)
    # =========================================================================
    MIL = mil_id
    reqs.append(repeat_cell(MIL, 0, 300, 0, 10,
        {"backgroundColor": WHITE, "textFormat": tf(size=10, color=TEXT_PRI)}, F_BG_TF))

    # R1: title (index 0)
    fmt_title_row(reqs, MIL, 0, 0, 8)

    # R2: subtitle (index 1)
    fmt_subtitle_row(reqs, MIL, 1, 0, 8)

    # Spacer R3 (index 2)
    reqs.append(row_height(MIL, 2, 16))

    # R4: col headers (index 3)
    fmt_col_headers(reqs, MIL, 3, 0, 8)

    # Data rows R5+ (index 4+)
    # Monthly section headers (── JANUARY ──, etc.) alternate with data rows
    # We'll apply a base style to all rows 4-300, then highlight section dividers
    reqs.append(rows_height(MIL, 4, 300, 24))
    for i in range(296):
        bg = WHITE if i % 2 == 0 else ALT_ROW
        reqs.append(repeat_cell(MIL, 4+i, 5+i, 0, 8,
            {"backgroundColor": bg, "textFormat": tf(size=10, color=TEXT_PRI)}, F_BG_TF))

    # KM column (E = index 4) right-aligned number
    reqs.append(repeat_cell(MIL, 4, 300, 4, 5,
        {"horizontalAlignment": "RIGHT",
         "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}, F_AL + "," + F_NF))

    # Mileage col widths
    for ci, w in enumerate([80, 120, 150, 280, 80, 80, 160, 200]):
        reqs.append(col_width(MIL, ci, w))

    reqs.append(freeze(MIL, rows=4))
    print("  Mileage: formatted")

    # =========================================================================
    # TAB: GST
    # =========================================================================
    G = gst_id
    reqs.append(repeat_cell(G, 0, 25, 0, 8,
        {"backgroundColor": WHITE, "textFormat": tf(size=10, color=TEXT_PRI)}, F_BG_TF))

    # R2: title (index 1)
    fmt_title_row(reqs, G, 1, 1, 7)

    # R3: subtitle (index 2)
    fmt_subtitle_row(reqs, G, 2, 1, 7)

    # Spacer R4 (index 3)
    reqs.append(row_height(G, 3, 16))

    # R5: Quarter col headers (index 4)
    fmt_col_headers(reqs, G, 4, 1, 7)

    # R6: GST Collected (index 5) — green
    reqs.append(repeat_cell(G, 5, 6, 1, 7,
        {"backgroundColor": GREEN_BG,
         "textFormat": tf(bold=True, size=10, color=GREEN)}, F_BG_TF))
    reqs.append(repeat_cell(G, 5, 6, 2, 7,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(row_height(G, 5, 28))

    # R7: ITCs (index 6) — red
    reqs.append(repeat_cell(G, 6, 7, 1, 7,
        {"backgroundColor": RED_BG,
         "textFormat": tf(bold=True, size=10, color=RED)}, F_BG_TF))
    reqs.append(repeat_cell(G, 6, 7, 2, 7,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(row_height(G, 6, 28))

    # Spacer R8 (index 7)
    reqs.append(row_height(G, 7, 16))

    # R9: NET OWING (index 8) — highlight
    reqs.append(repeat_cell(G, 8, 9, 1, 7,
        {"backgroundColor": RED_BG,
         "textFormat": tf(bold=True, size=12, color=RED)}, F_BG_TF))
    reqs.append(border_top(G, 8, 1, 7, color=RED))
    reqs.append(border_bottom(G, 8, 1, 7, color=RED))
    reqs.append(repeat_cell(G, 8, 9, 2, 7,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(row_height(G, 8, 34))

    # Spacer R10 (index 9)
    reqs.append(row_height(G, 9, 16))

    # R11: Due Dates (index 10)
    reqs.append(repeat_cell(G, 10, 11, 1, 7,
        {"backgroundColor": ORANGE_BG,
         "textFormat": tf(bold=True, size=10, color=ORANGE)}, F_BG_TF))
    reqs.append(row_height(G, 10, 28))

    # R12: Filed? (index 11)
    reqs.append(repeat_cell(G, 11, 12, 1, 7,
        {"textFormat": tf(size=10, color=TEXT_PRI)}, F_TF))
    reqs.append(row_height(G, 11, 26))

    # R13: Payment Date (index 12)
    reqs.append(repeat_cell(G, 12, 13, 1, 7,
        {"textFormat": tf(size=10, color=TEXT_PRI)}, F_TF))
    reqs.append(row_height(G, 12, 26))

    # Spacers R14-17
    for r in [13, 14, 15, 16]:
        reqs.append(row_height(G, r, 16))

    # R18: NOTES section header (index 17)
    fmt_section_header(reqs, G, 17, 1, 7, color=NAVY)

    # R19-22: notes rows (indices 18-21)
    reqs.append(rows_height(G, 18, 22, 24))
    reqs.append(repeat_cell(G, 18, 22, 1, 7,
        {"textFormat": tf(size=10, color=TEXT_PRI)}, F_TF))

    # GST col widths
    for ci, w in enumerate([24, 200, 120, 120, 120, 120, 120]):
        reqs.append(col_width(G, ci, w))

    print("  GST: formatted")

    # =========================================================================
    # TAB: Equipment
    # =========================================================================
    EQ = eqp_id
    reqs.append(repeat_cell(EQ, 0, 40, 0, 10,
        {"backgroundColor": WHITE, "textFormat": tf(size=10, color=TEXT_PRI)}, F_BG_TF))

    # R1: col headers (index 0)
    fmt_col_headers(reqs, EQ, 0, 0, 8)

    # R2-13: asset rows (indices 1-12, 12 rows)
    fmt_data_rows(reqs, EQ, 1, 13, 0, 8,
                  money_cols=[4, 5, 6, 7])
    # Date col (B=1) — center
    reqs.append(repeat_cell(EQ, 1, 13, 1, 2,
        {"horizontalAlignment": "CENTER"}, F_AL))
    # Rate col (D=3) — pct
    reqs.append(repeat_cell(EQ, 1, 13, 3, 4,
        {"numberFormat": nf_pct(), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))

    # Spacer R14-32 (middle area is empty)
    reqs.append(rows_height(EQ, 13, 32, 26))

    # R33: TOTALS (index 32)
    fmt_total_row(reqs, EQ, 32, 0, 8, GREEN_BG, GREEN, money_cols=[4, 5, 6, 7])

    # Equipment col widths
    for ci, w in enumerate([220, 100, 80, 60, 100, 100, 100, 100]):
        reqs.append(col_width(EQ, ci, w))

    reqs.append(freeze(EQ, rows=1))
    print("  Equipment: formatted")

    # =========================================================================
    # TAB: Tax
    # =========================================================================
    TX = tax_id
    reqs.append(repeat_cell(TX, 0, 100, 0, 8,
        {"backgroundColor": WHITE, "textFormat": tf(size=10, color=TEXT_PRI)}, F_BG_TF))

    # R2: title (index 1)
    fmt_title_row(reqs, TX, 1, 1, 6)

    # R3: subtitle (index 2)
    fmt_subtitle_row(reqs, TX, 2, 1, 6)

    # Spacer R4
    reqs.append(row_height(TX, 3, 16))

    # R5: T2125 INCOME header (index 4)
    fmt_section_header(reqs, TX, 4, 1, 6, color=BLUE)

    # R6 blank spacer (index 5)
    reqs.append(row_height(TX, 5, 16))

    # R7: Gross Business Income (index 6) — highlight
    reqs.append(repeat_cell(TX, 6, 7, 1, 6,
        {"backgroundColor": BLUE_BG,
         "textFormat": tf(bold=True, size=11, color=BLUE)}, F_BG_TF))
    reqs.append(repeat_cell(TX, 6, 7, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(row_height(TX, 6, 32))

    # R8 blank (index 7)
    reqs.append(row_height(TX, 7, 16))

    # R9: EXPENSES header (index 8)
    fmt_section_header(reqs, TX, 8, 1, 6, color=RED)

    # R10-24: expense line items (indices 9-23, 15 rows)
    fmt_data_rows(reqs, TX, 9, 24, 1, 6)
    reqs.append(repeat_cell(TX, 9, 24, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    # CRA line col (D=3) muted text
    reqs.append(repeat_cell(TX, 9, 24, 3, 4,
        {"textFormat": tf(size=9, color=TEXT_MUTED)}, F_TF))
    # Notes col (D=3 for vehicle/home office rows) — full width muted
    reqs.append(repeat_cell(TX, 11, 12, 3, 6,
        {"textFormat": tf(size=9, color=TEXT_MUTED, italic=True)}, F_TF))
    reqs.append(repeat_cell(TX, 21, 22, 3, 6,
        {"textFormat": tf(size=9, color=TEXT_MUTED, italic=True)}, F_TF))
    reqs.append(repeat_cell(TX, 22, 23, 3, 6,
        {"textFormat": tf(size=9, color=TEXT_MUTED, italic=True)}, F_TF))
    reqs.append(repeat_cell(TX, 23, 24, 3, 6,
        {"textFormat": tf(size=9, color=TEXT_MUTED, italic=True)}, F_TF))

    # Spacer R25 (index 24)
    reqs.append(row_height(TX, 24, 16))

    # R26: Total Expenses (index 25)
    fmt_total_row(reqs, TX, 25, 1, 6, RED_BG, RED, money_cols=[2])

    # Spacer R27 (index 26)
    reqs.append(row_height(TX, 26, 16))

    # R28: NET INCOME — big highlight (index 27)
    reqs.append(repeat_cell(TX, 27, 28, 1, 6,
        {"backgroundColor": GREEN_BG,
         "textFormat": tf(bold=True, size=14, color=GREEN)}, F_BG_TF))
    reqs.append(border_top(TX, 27, 1, 6, color=GREEN, style="SOLID", width=2))
    reqs.append(border_bottom(TX, 27, 1, 6, color=GREEN, style="SOLID", width=2))
    reqs.append(repeat_cell(TX, 27, 28, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(row_height(TX, 27, 38))

    # Spacer R29 (index 28)
    reqs.append(row_height(TX, 28, 16))

    # R30: TAX ESTIMATE header (index 29)
    fmt_section_header(reqs, TX, 29, 1, 6, color=ORANGE)

    # Spacer R31 (index 30)
    reqs.append(row_height(TX, 30, 16))

    # R32-38: tax calculation rows (indices 31-37)
    fmt_data_rows(reqs, TX, 31, 38, 1, 6)
    reqs.append(repeat_cell(TX, 31, 38, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    # Credit rows (minus values) in green
    reqs.append(repeat_cell(TX, 32, 33, 2, 3,
        {"textFormat": tf(bold=True, size=10, color=GREEN)}, F_TF))
    reqs.append(repeat_cell(TX, 36, 37, 2, 3,
        {"textFormat": tf(bold=True, size=10, color=GREEN)}, F_TF))

    # Spacer R39 (index 38)
    reqs.append(row_height(TX, 38, 16))

    # R40: Total Income Tax (index 39) — orange highlight
    fmt_total_row(reqs, TX, 39, 1, 6, ORANGE_BG, ORANGE, money_cols=[2])

    # Spacer R41 (index 40)
    reqs.append(row_height(TX, 40, 16))

    # R42-44: CPP rows (indices 41-43)
    fmt_data_rows(reqs, TX, 41, 44, 1, 6)
    reqs.append(repeat_cell(TX, 41, 44, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))

    # Spacer R45 (index 44)
    reqs.append(row_height(TX, 44, 16))

    # R46: TOTAL TAX + CPP (index 45) — big highlight
    reqs.append(repeat_cell(TX, 45, 46, 1, 6,
        {"backgroundColor": RED_BG,
         "textFormat": tf(bold=True, size=14, color=RED)}, F_BG_TF))
    reqs.append(border_top(TX, 45, 1, 6, color=RED, style="SOLID", width=2))
    reqs.append(repeat_cell(TX, 45, 46, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(row_height(TX, 45, 38))

    # R47: Quarterly Installment (index 46)
    reqs.append(repeat_cell(TX, 46, 47, 1, 6,
        {"backgroundColor": ORANGE_BG,
         "textFormat": tf(size=10, color=ORANGE)}, F_BG_TF))
    reqs.append(repeat_cell(TX, 46, 47, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(row_height(TX, 46, 26))

    # Spacers R48 (index 47)
    reqs.append(row_height(TX, 47, 16))

    # R49-52: RRSP rows (indices 48-51)
    fmt_data_rows(reqs, TX, 48, 52, 1, 6)
    reqs.append(repeat_cell(TX, 48, 52, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    # RRSP Room highlight
    reqs.append(repeat_cell(TX, 48, 49, 1, 6,
        {"backgroundColor": GREEN_BG,
         "textFormat": tf(bold=True, size=10, color=GREEN)}, F_BG_TF))
    reqs.append(repeat_cell(TX, 48, 49, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))

    # R52: GST collected (index 51)
    reqs.append(repeat_cell(TX, 51, 52, 1, 6,
        {"backgroundColor": GREEN_BG,
         "textFormat": tf(bold=True, size=10, color=GREEN)}, F_BG_TF))
    reqs.append(repeat_cell(TX, 51, 52, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))

    # Spacers R53-55 (indices 52-54)
    for r in [52, 53, 54]:
        reqs.append(row_height(TX, r, 16))

    # R54: ADDITIONAL T1 DEDUCTIONS header (index 53)
    fmt_section_header(reqs, TX, 53, 1, 6, color=NAVY)

    # Spacer R55 (index 54)
    reqs.append(row_height(TX, 54, 16))

    # R56: CPP deduction (index 55)
    fmt_data_rows(reqs, TX, 55, 57, 1, 6)
    reqs.append(repeat_cell(TX, 55, 57, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))

    # Spacer R57 (index 56)
    reqs.append(row_height(TX, 56, 16))

    # R58: ADJUSTED NET INCOME (index 57)
    reqs.append(repeat_cell(TX, 57, 58, 1, 6,
        {"backgroundColor": BLUE_BG,
         "textFormat": tf(bold=True, size=11, color=BLUE)}, F_BG_TF))
    reqs.append(border_top(TX, 57, 1, 6, color=BLUE))
    reqs.append(repeat_cell(TX, 57, 58, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(row_height(TX, 57, 32))

    # Spacers R59 (index 58)
    reqs.append(row_height(TX, 58, 16))

    # R60: FINAL TAX CALCULATION header (index 59)
    fmt_section_header(reqs, TX, 59, 1, 6, color=ORANGE)

    # Spacer R61 (index 60)
    reqs.append(row_height(TX, 60, 16))

    # R62-69: revised tax calc rows (indices 61-68)
    fmt_data_rows(reqs, TX, 61, 70, 1, 6)
    reqs.append(repeat_cell(TX, 61, 70, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    # Credits in green
    reqs.append(repeat_cell(TX, 62, 63, 2, 3,
        {"textFormat": tf(bold=True, size=10, color=GREEN)}, F_TF))
    reqs.append(repeat_cell(TX, 66, 67, 2, 3,
        {"textFormat": tf(bold=True, size=10, color=GREEN)}, F_TF))

    # Spacer R70 (index 69)
    reqs.append(row_height(TX, 69, 16))

    # R71-72: Income Tax + CPP revised (indices 70-71)
    fmt_data_rows(reqs, TX, 70, 73, 1, 6)
    reqs.append(repeat_cell(TX, 70, 73, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))

    # Spacer R73 (index 72)
    reqs.append(row_height(TX, 72, 16))

    # R74: FINAL TAX + CPP (index 73) — big red
    reqs.append(repeat_cell(TX, 73, 74, 1, 6,
        {"backgroundColor": RED_BG,
         "textFormat": tf(bold=True, size=14, color=RED)}, F_BG_TF))
    reqs.append(border_top(TX, 73, 1, 6, color=RED, style="SOLID", width=2))
    reqs.append(border_bottom(TX, 73, 1, 6, color=RED, style="SOLID", width=2))
    reqs.append(repeat_cell(TX, 73, 74, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(row_height(TX, 73, 38))

    # R75: Quarterly installment revised (index 74)
    reqs.append(repeat_cell(TX, 74, 75, 1, 6,
        {"backgroundColor": ORANGE_BG,
         "textFormat": tf(size=10, color=ORANGE)}, F_BG_TF))
    reqs.append(repeat_cell(TX, 74, 75, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(row_height(TX, 74, 26))

    # Spacer R76 (index 75)
    reqs.append(row_height(TX, 75, 16))

    # R77: SAVINGS section header (index 76)
    fmt_section_header(reqs, TX, 76, 1, 6, color=GREEN)

    # R78-80: savings rows (indices 77-79)
    fmt_data_rows(reqs, TX, 77, 80, 1, 6)
    reqs.append(repeat_cell(TX, 77, 80, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    # YOU SAVE row — big green (index 79)
    reqs.append(repeat_cell(TX, 79, 80, 1, 6,
        {"backgroundColor": GREEN_BG,
         "textFormat": tf(bold=True, size=12, color=GREEN)}, F_BG_TF))
    reqs.append(repeat_cell(TX, 79, 80, 2, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(row_height(TX, 79, 34))

    # Spacer R81 (index 80)
    reqs.append(row_height(TX, 80, 16))

    # R82: MILEAGE LOG section header (index 81)
    fmt_section_header(reqs, TX, 81, 1, 6, color=NAVY)

    # R83-87: mileage rows (indices 82-86)
    fmt_data_rows(reqs, TX, 82, 87, 1, 6)
    reqs.append(repeat_cell(TX, 84, 87, 2, 3,
        {"textFormat": tf(bold=True, size=10, color=ORANGE)}, F_TF))

    # Spacer R88 (index 87)
    reqs.append(row_height(TX, 87, 16))

    # R89: CCA SCHEDULE header (index 88)
    fmt_section_header(reqs, TX, 88, 1, 6, color=NAVY)

    # Spacer R90 (index 89)
    reqs.append(row_height(TX, 89, 16))

    # R91-95: CCA rows (indices 90-94)
    fmt_data_rows(reqs, TX, 90, 95, 1, 6)
    reqs.append(repeat_cell(TX, 90, 95, 2, 3,
        {"numberFormat": nf_money(), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))

    # Tax col widths
    for ci, w in enumerate([24, 240, 120, 440, 100]):
        reqs.append(col_width(TX, ci, w))

    print("  Tax: formatted")

    # =========================================================================
    # TAB: Insights
    # =========================================================================
    INS = ins_id
    reqs.append(repeat_cell(INS, 0, 100, 0, 10,
        {"backgroundColor": WHITE, "textFormat": tf(size=10, color=TEXT_PRI)}, F_BG_TF))

    # R1: title (index 0)
    fmt_title_row(reqs, INS, 0, 0, 8)

    # R2: subtitle (index 1)
    fmt_subtitle_row(reqs, INS, 1, 0, 8)

    # Spacer R3 (index 2)
    reqs.append(row_height(INS, 2, 16))

    # R4: CASH FLOW ANALYSIS section header (index 3)
    fmt_section_header(reqs, INS, 3, 0, 8)

    # R5: col headers (index 4)
    fmt_col_headers(reqs, INS, 4, 0, 8)

    # R6-17: 12 months (indices 5-16)
    fmt_data_rows(reqs, INS, 5, 17, 0, 8, money_cols=[1, 2, 3, 4])
    reqs.append(repeat_cell(INS, 5, 17, 1, 2,
        {"textFormat": tf(bold=False, size=10, color=BLUE)}, F_TF))
    reqs.append(repeat_cell(INS, 5, 17, 2, 3,
        {"textFormat": tf(bold=False, size=10, color=RED)}, F_TF))
    reqs.append(repeat_cell(INS, 5, 17, 3, 4,
        {"textFormat": tf(bold=True, size=10, color=GREEN)}, F_TF))

    # Spacer R18 (index 17)
    reqs.append(row_height(INS, 17, 16))

    # R19: summary avg row (index 18) — blue bg
    reqs.append(repeat_cell(INS, 18, 19, 0, 8,
        {"backgroundColor": BLUE_BG,
         "textFormat": tf(bold=True, size=10, color=NAVY)}, F_BG_TF))
    reqs.append(repeat_cell(INS, 18, 19, 1, 2,
        {"numberFormat": nf_money(), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(row_height(INS, 18, 28))

    # Spacer R20 (index 19)
    reqs.append(row_height(INS, 19, 16))

    # R21: SPENDING VELOCITY section header (index 20)
    fmt_section_header(reqs, INS, 20, 0, 8)

    # R22-24: velocity rows (indices 21-23)
    fmt_data_rows(reqs, INS, 21, 25, 0, 8, money_cols=[1, 3])

    # Spacer R25 (index 24)
    reqs.append(row_height(INS, 24, 16))

    # R26: SOFTWARE STACK section header (index 25)
    fmt_section_header(reqs, INS, 25, 0, 8)

    # R27: col headers (index 26)
    fmt_col_headers(reqs, INS, 26, 0, 8)

    # R28-51: software rows (indices 27-50, 24 rows)
    fmt_data_rows(reqs, INS, 27, 51, 0, 8, money_cols=[1, 2], pct_cols=[3])

    # Spacer R52 (index 51)
    reqs.append(row_height(INS, 51, 16))

    # R53: TOTAL SOFTWARE (index 52) — orange
    reqs.append(repeat_cell(INS, 52, 53, 0, 8,
        {"backgroundColor": ORANGE_BG,
         "textFormat": tf(bold=True, size=11, color=ORANGE)}, F_BG_TF))
    reqs.append(border_top(INS, 52, 0, 8, color=ORANGE))
    reqs.append(repeat_cell(INS, 52, 53, 1, 3,
        {"numberFormat": nf_money(2), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(repeat_cell(INS, 52, 53, 3, 4,
        {"numberFormat": nf_pct(), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(row_height(INS, 52, 30))

    # Spacer R54 (index 53)
    reqs.append(row_height(INS, 53, 16))

    # R55: SAVINGS section header (index 54)
    fmt_section_header(reqs, INS, 54, 0, 8, color=GREEN)

    # R56-59: savings rows (indices 55-58)
    fmt_data_rows(reqs, INS, 55, 59, 0, 8)
    reqs.append(repeat_cell(INS, 55, 56, 1, 2,
        {"numberFormat": nf_money(), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(repeat_cell(INS, 56, 58, 1, 2,
        {"numberFormat": nf_pct(), "horizontalAlignment": "RIGHT"}, F_NF + "," + F_AL))
    reqs.append(repeat_cell(INS, 55, 58, 1, 2,
        {"textFormat": tf(bold=True, size=10, color=GREEN)}, F_TF))

    # Spacer R60 (index 59)
    reqs.append(row_height(INS, 59, 16))

    # R61 spacer (index 60)
    reqs.append(row_height(INS, 60, 16))

    # R62: TOP 20 VENDORS section header (index 61)
    fmt_section_header(reqs, INS, 61, 0, 8)

    # R63: col headers (index 62)
    fmt_col_headers(reqs, INS, 62, 0, 8)

    # R64-83: vendor rows (indices 63-82, 20 rows)
    fmt_data_rows(reqs, INS, 63, 83, 0, 8, money_cols=[2], pct_cols=[3])

    # Spacer R84 (index 83)
    reqs.append(row_height(INS, 83, 16))

    # R85: YEAR-OVER-YEAR section header (index 84)
    fmt_section_header(reqs, INS, 84, 0, 8)

    # R86: col headers (index 85)
    fmt_col_headers(reqs, INS, 85, 0, 8)

    # R87-90: YoY data (indices 86-89, 4 rows)
    fmt_data_rows(reqs, INS, 86, 90, 0, 8, money_cols=[1, 2, 3])
    # Alternating blue bg for YoY
    for i in range(4):
        bg = BLUE_BG if i % 2 == 0 else WHITE
        reqs.append(repeat_cell(INS, 86+i, 87+i, 0, 8,
            {"backgroundColor": bg}, F_BG))
    # % growth col (D=4) — text (already written as string)
    reqs.append(repeat_cell(INS, 86, 90, 4, 5,
        {"textFormat": tf(bold=True, size=10, color=GREEN)}, F_TF))

    # Insights col widths
    for ci, w in enumerate([200, 120, 120, 90, 120, 220, 100, 100, 100]):
        reqs.append(col_width(INS, ci, w))

    reqs.append(freeze(INS, rows=1))
    print("  Insights: formatted")

    # =========================================================================
    # TAB TAB COLORS — set tab colors for visual organization
    # =========================================================================
    tab_colors = {
        dash_id: NAVY,
        txn_id:  {"red": 0.4, "green": 0.4, "blue": 0.4},
        inc_id:  BLUE,
        exp_id:  ORANGE,
        bus_id:  {"red": 0.902, "green": 0.533, "blue": 0.118},
        per_id:  PURPLE,
        pl_id:   GREEN,
        mil_id:  {"red": 0.4, "green": 0.4, "blue": 0.4},
        gst_id:  GREEN,
        eqp_id:  BLUE,
        tax_id:  RED,
        ins_id:  {"red": 0.153, "green": 0.173, "blue": 0.224},
    }
    for sid, color in tab_colors.items():
        reqs.append({"updateSheetProperties": {
            "properties": {"sheetId": sid, "tabColorStyle": {"rgbColor": color}},
            "fields": "tabColorStyle"
        }})

    # =========================================================================
    # EXECUTE — send in batches of 100
    # =========================================================================
    BATCH = 100
    total = len(reqs)
    print(f"\nSending {total} formatting requests in batches of {BATCH}...")

    for start in range(0, total, BATCH):
        batch = reqs[start:start+BATCH]
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"requests": batch}
        ).execute()
        print(f"  Batch {start//BATCH + 1}: requests {start+1}–{min(start+BATCH, total)} ✓")

    print(f"\n{'='*60}")
    print("FORMATTING COMPLETE — Summary:")
    print(f"{'='*60}")
    tabs_done = [
        ("Dashboard",    "Title, subtitle, KPI cards (blue/red bg), Tax breakdown, Monthly breakdown with total, GST summary, Cash Flow section, Key Ratios section"),
        ("Transactions", "Frozen at row 3, navy header banner, col header row"),
        ("Income",       "Title/subtitle, source table headers+data, TOTAL row, Monthly Revenue section with total"),
        ("Expenses",     "Title/subtitle, Business section (orange), Personal section (purple), both with totals"),
        ("Business",     "Col headers, 15 category rows alternating, orange TOTAL, Budget vs Actual section with section header + col headers + 15 rows + total"),
        ("Personal",     "Col headers, 13 category rows alternating, purple TOTAL, Spending Insights section, Monthly Trend subsection"),
        ("P&L",          "Col headers, 12 month rows (blue/red/green colored values), TOTAL row"),
        ("Mileage",      "Title, subtitle, col headers frozen at row 4, 296 alternating data rows, KM right-aligned"),
        ("GST",          "Title, subtitle, quarter headers, green Collected, red ITCs, highlighted NET OWING, orange Due Dates, Notes section"),
        ("Equipment",    "Col headers, 12 asset rows alternating, green TOTALS row"),
        ("Tax",          "Title, T2125 Income (blue), Expenses (red), NET INCOME highlight (green), Tax calc rows, TOTAL TAX (red), CPP, FINAL TAX (red), Savings (green), Mileage section, CCA Schedule"),
        ("Insights",     "Title, Cash Flow Analysis (12mo), Spending Velocity, Software Stack (24 tools + orange total), Savings (green), Top 20 Vendors, Year-over-Year"),
    ]
    for tab, desc in tabs_done:
        print(f"\n  {tab}:")
        print(f"    {desc}")

    print(f"\n  Tab colors set: Navy=Dashboard/Insights, Blue=Income/Equipment, ")
    print(f"  Orange=Expenses/Business, Purple=Personal, Green=P&L/GST, Red=Tax, Gray=Transactions/Mileage")
    print(f"\nSheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}")


if __name__ == '__main__':
    main()
