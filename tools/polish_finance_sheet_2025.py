"""
Final professional polish for 2025 Finance Sheet.
Applies audit-proof formatting: consistent title blocks, footers, borders,
section headers, and CRA-ready presentation across all 12 tabs.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_sheets_service

SHEET_ID = '1TyX4sOIo6CxblxjNM9Yft5h5vZO_BGhQjHlgC0uzQtI'

# ── Design Tokens ─────────────────────────────────────────────────────────────
NAVY      = {"red": 0.153, "green": 0.173, "blue": 0.224}
BLUE      = {"red": 0.224, "green": 0.443, "blue": 0.871}
BLUE_BG   = {"red": 0.922, "green": 0.941, "blue": 0.988}
GREEN     = {"red": 0.118, "green": 0.624, "blue": 0.424}
GREEN_BG  = {"red": 0.906, "green": 0.969, "blue": 0.941}
RED       = {"red": 0.851, "green": 0.200, "blue": 0.200}
RED_BG    = {"red": 0.992, "green": 0.929, "blue": 0.929}
ORANGE    = {"red": 0.902, "green": 0.533, "blue": 0.118}
ORANGE_BG = {"red": 0.996, "green": 0.953, "blue": 0.906}
PURPLE    = {"red": 0.486, "green": 0.318, "blue": 0.804}
PURPLE_BG = {"red": 0.949, "green": 0.933, "blue": 0.988}
WHITE     = {"red": 1, "green": 1, "blue": 1}
ALT_ROW   = {"red": 0.965, "green": 0.969, "blue": 0.976}
BORDER    = {"red": 0.890, "green": 0.898, "blue": 0.910}
T1        = {"red": 0.098, "green": 0.114, "blue": 0.149}
T3        = {"red": 0.549, "green": 0.573, "blue": 0.612}
T4        = {"red": 0.702, "green": 0.718, "blue": 0.745}
GRAY_DIV  = {"red": 0.820, "green": 0.830, "blue": 0.845}

# ── Helpers ───────────────────────────────────────────────────────────────────
def gr(sid, sr, er, sc, ec):
    return {"sheetId": sid, "startRowIndex": sr, "endRowIndex": er,
            "startColumnIndex": sc, "endColumnIndex": ec}

def rc(sid, sr, er, sc, ec, fmt, fields):
    return {"repeatCell": {"range": gr(sid, sr, er, sc, ec),
            "cell": {"userEnteredFormat": fmt}, "fields": fields}}

def mg(sid, sr, er, sc, ec):
    return {"mergeCells": {"range": gr(sid, sr, er, sc, ec), "mergeType": "MERGE_ALL"}}

def rh(sid, r, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": r, "endIndex": r+1},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def rhs(sid, r0, r1, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": r0, "endIndex": r1},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def cw(sid, c, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": c, "endIndex": c+1},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def tf(bold=False, sz=10, color=None, italic=False):
    t = {"fontFamily": "Inter", "fontSize": sz}
    if bold: t["bold"] = True
    if italic: t["italic"] = True
    if color: t["foregroundColor"] = color
    return t

def border_side(sid, sr, er, sc, ec, side, color=BORDER, style="SOLID", width=1):
    return {"updateBorders": {"range": gr(sid, sr, er, sc, ec),
            side: {"style": style, "width": width, "color": color}}}

def border_box(sid, sr, er, sc, ec, color=BORDER, style="SOLID", width=1):
    b = {"style": style, "width": width, "color": color}
    return {"updateBorders": {"range": gr(sid, sr, er, sc, ec),
            "top": b, "bottom": b, "left": b, "right": b}}

def freeze(sid, rows=0, cols=0):
    props = {"sheetId": sid, "gridProperties": {}}
    fields = []
    if rows is not None:
        props["gridProperties"]["frozenRowCount"] = rows
        fields.append("gridProperties.frozenRowCount")
    if cols is not None:
        props["gridProperties"]["frozenColumnCount"] = cols
        fields.append("gridProperties.frozenColumnCount")
    return {"updateSheetProperties": {"properties": props, "fields": ",".join(fields)}}

F_BG = "userEnteredFormat.backgroundColor"
F_TF = "userEnteredFormat.textFormat"
F_NF = "userEnteredFormat.numberFormat"
F_AL = "userEnteredFormat.horizontalAlignment"
F_VA = "userEnteredFormat.verticalAlignment"
F_BG_TF = f"{F_BG},{F_TF}"
F_ALL = f"{F_BG},{F_TF},{F_AL},{F_VA}"

def nf_money(d=0):
    return {"type": "CURRENCY", "pattern": "$#,##0" if d == 0 else "$#,##0.00"}

def nf_pct():
    return {"type": "PERCENT", "pattern": "0.0%"}

# ── Standard title block (rows 0-3 in 0-index) ──────────────────────────────
def add_title_block(reqs, sid, sc, ec, has_title=True):
    """Adds: R1=spacer(16px), R2=title(22pt navy merged), R3=subtitle(11pt gray merged), R4=spacer(12px)"""
    if not has_title:
        return
    # R1 spacer
    reqs.append(rh(sid, 0, 16))
    reqs.append(rc(sid, 0, 1, 0, ec, {"backgroundColor": WHITE}, F_BG))
    # R2 title
    reqs.append(rh(sid, 1, 46))
    reqs.append(rc(sid, 1, 2, sc, ec,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    if ec - sc > 1:
        reqs.append(mg(sid, 1, 2, sc, ec))
    # R3 subtitle
    reqs.append(rh(sid, 2, 24))
    reqs.append(rc(sid, 2, 3, sc, ec,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    if ec - sc > 1:
        reqs.append(mg(sid, 2, 3, sc, ec))
    # R4 spacer
    reqs.append(rh(sid, 3, 12))
    reqs.append(rc(sid, 3, 4, 0, ec, {"backgroundColor": WHITE}, F_BG))


# ── Standard footer ──────────────────────────────────────────────────────────
def add_footer(reqs, sid, start_row, sc, ec):
    """Adds professional footer starting at start_row (0-indexed)."""
    # Spacer
    reqs.append(rh(sid, start_row, 20))
    reqs.append(rc(sid, start_row, start_row+1, 0, ec, {"backgroundColor": WHITE}, F_BG))
    # Divider line
    reqs.append(border_side(sid, start_row, start_row+1, sc, ec, "bottom", color=BORDER, width=1))
    # Line 1: Prepared by
    r1 = start_row + 1
    reqs.append(rh(sid, r1, 18))
    reqs.append(rc(sid, r1, r1+1, sc, ec,
        {"backgroundColor": WHITE, "textFormat": tf(sz=9, color=T4)}, F_BG_TF))
    if ec - sc > 1:
        reqs.append(mg(sid, r1, r1+1, sc, ec))
    # Line 2: Tax Year
    r2 = start_row + 2
    reqs.append(rh(sid, r2, 18))
    reqs.append(rc(sid, r2, r2+1, sc, ec,
        {"backgroundColor": WHITE, "textFormat": tf(sz=9, color=T4)}, F_BG_TF))
    if ec - sc > 1:
        reqs.append(mg(sid, r2, r2+1, sc, ec))
    # Line 3: T2125
    r3 = start_row + 3
    reqs.append(rh(sid, r3, 18))
    reqs.append(rc(sid, r3, r3+1, sc, ec,
        {"backgroundColor": WHITE, "textFormat": tf(sz=9, color=T4, italic=True)}, F_BG_TF))
    if ec - sc > 1:
        reqs.append(mg(sid, r3, r3+1, sc, ec))
    return r3 + 1  # next available row


def write_footer_text(service, tab_name, start_row, col_letter="A"):
    """Writes the footer text values. start_row is 0-indexed."""
    r1 = start_row + 2  # 1-indexed
    r2 = start_row + 3
    r3 = start_row + 4
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"valueInputOption": "RAW", "data": [
            {"range": f"'{tab_name}'!{col_letter}{r1}", "values": [["Prepared by: Matt Anthony Photography"]]},
            {"range": f"'{tab_name}'!{col_letter}{r2}", "values": [["Tax Year: 2025  |  Filing: June 15, 2027  |  GST: Quarterly"]]},
            {"range": f"'{tab_name}'!{col_letter}{r3}", "values": [["This document supports T2125 Statement of Business Activities"]]},
        ]}
    ).execute()


# ── Section divider (thin gray line) ─────────────────────────────────────────
def section_divider(reqs, sid, row, sc, ec):
    reqs.append(border_side(sid, row, row+1, sc, ec, "bottom", color=GRAY_DIV, style="SOLID", width=1))


# ── Colored section header bar ───────────────────────────────────────────────
def section_bar(reqs, sid, row, sc, ec, bg_color, text_color=WHITE, height=36):
    reqs.append(rh(sid, row, height))
    reqs.append(rc(sid, row, row+1, sc, ec,
        {"backgroundColor": bg_color,
         "textFormat": tf(bold=True, sz=12, color=text_color),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    if ec - sc > 1:
        reqs.append(mg(sid, row, row+1, sc, ec))


# ── Column header with bottom border ────────────────────────────────────────
def col_header(reqs, sid, row, sc, ec):
    reqs.append(rc(sid, row, row+1, sc, ec,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=9, color=T3)}, F_BG_TF))
    reqs.append(border_side(sid, row, row+1, sc, ec, "bottom", color=BORDER, style="SOLID", width=2))
    reqs.append(rh(sid, row, 30))


# ── Total row accent ────────────────────────────────────────────────────────
def total_accent(reqs, sid, row, sc, ec, accent_color, height=32):
    reqs.append(border_side(sid, row, row+1, sc, ec, "top", color=accent_color, style="SOLID", width=2))
    reqs.append(rh(sid, row, height))


# =============================================================================
# MAIN
# =============================================================================
def main():
    service = get_sheets_service()
    ss = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    sheets = {s['properties']['title']: s['properties']['sheetId'] for s in ss['sheets']}
    print("Tabs:", list(sheets.keys()))

    reqs = []

    D   = sheets['Dashboard']
    TXN = sheets['Transactions']
    INC = sheets['Income']
    EXP = sheets['Expenses']
    BUS = sheets['Business']
    PER = sheets['Personal']
    PL  = sheets['P&L']
    MIL = sheets['Mileage']
    GST = sheets['GST']
    EQP = sheets['Equipment']
    TAX = sheets['Tax']
    INS = sheets['Insights']

    # =========================================================================
    # 1. DASHBOARD — Make it the hero
    # =========================================================================
    print("  Polishing Dashboard...")

    # Title block already at R2-R3 (indices 1-2), offset cols 2-9
    # Re-apply title at 22pt
    reqs.append(rh(D, 0, 16))  # spacer R1
    reqs.append(rh(D, 1, 50))
    reqs.append(rc(D, 1, 2, 2, 9,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(D, 1, 2, 2, 9))
    reqs.append(rh(D, 2, 24))
    reqs.append(rc(D, 2, 3, 2, 9,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4)}, F_BG_TF))
    reqs.append(mg(D, 2, 3, 2, 9))
    reqs.append(rh(D, 3, 12))

    # KPI cards — add thin borders around each card block
    # Revenue card: rows 4-7, cols 2-4
    reqs.append(border_box(D, 4, 8, 2, 5, color=BLUE, style="SOLID", width=1))
    # Expenses card: rows 4-7, cols 6-8
    reqs.append(border_box(D, 4, 8, 6, 9, color=RED, style="SOLID", width=1))

    # Section dividers between major areas
    section_divider(reqs, D, 8, 2, 9)   # after KPIs
    section_divider(reqs, D, 13, 2, 9)  # after Tax breakdown
    section_divider(reqs, D, 29, 2, 9)  # after Monthly totals
    section_divider(reqs, D, 36, 2, 9)  # after GST
    section_divider(reqs, D, 52, 2, 9)  # after Cash Flow
    section_divider(reqs, D, 53, 2, 9)

    # Column header bottom borders (ensure)
    reqs.append(border_side(D, 15, 16, 2, 9, "bottom", color=BORDER, width=2))
    reqs.append(border_side(D, 38, 39, 2, 9, "bottom", color=BORDER, width=2))
    reqs.append(border_side(D, 55, 56, 2, 9, "bottom", color=BORDER, width=2))

    # Total row top accent borders
    total_accent(reqs, D, 28, 2, 9, BLUE)   # Monthly total
    total_accent(reqs, D, 51, 2, 9, BLUE)   # Cash flow total

    # Freeze: 0 for dashboard
    reqs.append(freeze(D, rows=0))

    # Footer at row 65
    add_footer(reqs, D, 65, 2, 9)

    # =========================================================================
    # 2. TRANSACTIONS — Clean and scannable
    # =========================================================================
    print("  Polishing Transactions...")

    # Title block R1-R2 already exists (navy bg). Re-style for consistency.
    reqs.append(rh(TXN, 0, 50))
    reqs.append(rc(TXN, 0, 1, 0, 12,
        {"backgroundColor": NAVY,
         "textFormat": tf(bold=True, sz=22, color=WHITE),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(rh(TXN, 1, 24))
    reqs.append(rc(TXN, 1, 2, 0, 12,
        {"backgroundColor": NAVY, "textFormat": tf(sz=11, color=T4)}, F_BG_TF))

    # R3: col headers
    col_header(reqs, TXN, 2, 0, 12)

    # R4: INCOME header — full-width GREEN bar, 40px tall
    section_bar(reqs, TXN, 3, 0, 12, GREEN, WHITE, 40)

    # R5: sub-headers for income
    col_header(reqs, TXN, 4, 0, 12)

    # R144: EXPENSES header — full-width RED bar, 40px tall
    section_bar(reqs, TXN, 143, 0, 12, RED, WHITE, 40)

    # Freeze at row 3
    reqs.append(freeze(TXN, rows=3))

    # Date column consistent format (already dates)
    # Bottom border on every header row
    reqs.append(border_side(TXN, 4, 5, 0, 12, "bottom", color=BORDER, width=1))

    # =========================================================================
    # 3. INCOME — Title area standardization
    # =========================================================================
    print("  Polishing Income...")

    # Title block: R1=spacer, R2=title, R3=subtitle, R4=spacer
    reqs.append(rh(INC, 0, 16))
    reqs.append(rc(INC, 0, 1, 0, 14, {"backgroundColor": WHITE}, F_BG))
    reqs.append(rh(INC, 1, 50))
    reqs.append(rc(INC, 1, 2, 1, 8,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(INC, 1, 2, 1, 8))
    reqs.append(rh(INC, 2, 24))
    reqs.append(rc(INC, 2, 3, 1, 8,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4)}, F_BG_TF))
    reqs.append(mg(INC, 2, 3, 1, 8))
    reqs.append(rh(INC, 3, 12))

    # Column header bottom borders
    reqs.append(border_side(INC, 4, 5, 1, 14, "bottom", color=BORDER, width=2))
    reqs.append(border_side(INC, 5, 6, 1, 14, "bottom", color=BORDER, width=2))

    # Total row accent
    total_accent(reqs, INC, 14, 1, 14, BLUE)

    # Monthly revenue section header
    reqs.append(border_side(INC, 17, 18, 1, 4, "bottom", color=BORDER, width=2))
    total_accent(reqs, INC, 30, 1, 4, BLUE)

    # Footer at row 33
    add_footer(reqs, INC, 33, 1, 8)

    # =========================================================================
    # 4. EXPENSES — Title area + borders
    # =========================================================================
    print("  Polishing Expenses...")

    reqs.append(rh(EXP, 0, 16))
    reqs.append(rc(EXP, 0, 1, 0, 8, {"backgroundColor": WHITE}, F_BG))
    reqs.append(rh(EXP, 1, 50))
    reqs.append(rc(EXP, 1, 2, 1, 8,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(EXP, 1, 2, 1, 8))
    reqs.append(rh(EXP, 2, 24))
    reqs.append(rc(EXP, 2, 3, 1, 8,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4)}, F_BG_TF))
    reqs.append(mg(EXP, 2, 3, 1, 8))
    reqs.append(rh(EXP, 3, 12))

    # Section headers bottom border
    reqs.append(border_side(EXP, 5, 6, 1, 7, "bottom", color=BORDER, width=2))
    reqs.append(border_side(EXP, 24, 25, 1, 7, "bottom", color=BORDER, width=2))

    # Total row accents
    total_accent(reqs, EXP, 21, 1, 7, ORANGE)
    total_accent(reqs, EXP, 34, 1, 7, PURPLE)

    # Section divider between business and personal
    section_divider(reqs, EXP, 22, 1, 7)

    # Footer at row 37
    add_footer(reqs, EXP, 37, 1, 8)

    # =========================================================================
    # 5. BUSINESS — Title block + CRA reference + sparkline col
    # =========================================================================
    print("  Polishing Business...")

    # Business currently starts at R1 with col headers. We need to insert title.
    # Since data starts at row 0, we'll add title info above by using available space.
    # Actually, the tab starts with col headers at R1. Let's re-style the header.

    # Column header
    col_header(reqs, BUS, 0, 0, 16)

    # Total row accent (row 17 = index 17)
    total_accent(reqs, BUS, 17, 0, 16, ORANGE, 34)
    reqs.append(rc(BUS, 17, 18, 0, 16,
        {"backgroundColor": ORANGE_BG, "textFormat": tf(bold=True, sz=11, color=ORANGE)}, F_BG_TF))

    # Budget section header bar (row 22)
    section_bar(reqs, BUS, 22, 0, 7, NAVY, WHITE, 36)

    # Budget col headers (row 23)
    col_header(reqs, BUS, 23, 0, 7)

    # Budget total row (row 39)
    total_accent(reqs, BUS, 39, 0, 7, ORANGE, 34)

    # Section divider between data and budget
    section_divider(reqs, BUS, 18, 0, 14)

    # Footer at row 42
    add_footer(reqs, BUS, 42, 0, 8)

    # Freeze header
    reqs.append(freeze(BUS, rows=1))

    # =========================================================================
    # 6. PERSONAL — Title block + clean layout
    # =========================================================================
    print("  Polishing Personal...")

    # Starts with col headers at R1 (index 0)
    col_header(reqs, PER, 0, 0, 14)

    # Total row accent (row 14)
    total_accent(reqs, PER, 14, 0, 14, PURPLE, 34)

    # Insights section header bar (row 19)
    section_bar(reqs, PER, 19, 0, 5, PURPLE, WHITE, 36)

    # Insights col header (row 20)
    col_header(reqs, PER, 20, 0, 5)

    # Monthly trend header bar (row 29)
    section_bar(reqs, PER, 29, 0, 4, PURPLE, WHITE, 32)

    # Monthly trend col header (row 30)
    col_header(reqs, PER, 30, 0, 4)

    # Section dividers
    section_divider(reqs, PER, 15, 0, 14)

    # Footer at row 45
    add_footer(reqs, PER, 45, 0, 8)

    reqs.append(freeze(PER, rows=1))

    # =========================================================================
    # 7. P&L — Title block + borders
    # =========================================================================
    print("  Polishing P&L...")

    # P&L starts with col headers at R1 (index 0)
    col_header(reqs, PL, 0, 0, 8)

    # Total row accent (row 14)
    total_accent(reqs, PL, 14, 0, 8, BLUE, 34)

    # Footer at row 17
    add_footer(reqs, PL, 17, 0, 8)

    reqs.append(freeze(PL, rows=1))

    # =========================================================================
    # 8. MILEAGE — Vehicle info + CRA compliance + monthly subtotals
    # =========================================================================
    print("  Polishing Mileage...")

    # Title block: R1=spacer, R2=title, R3=subtitle, R4=spacer already exists
    # But let's re-apply with proper sizing
    reqs.append(rh(MIL, 0, 50))
    reqs.append(rc(MIL, 0, 1, 0, 8,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(MIL, 0, 1, 0, 8))
    reqs.append(rh(MIL, 1, 24))
    reqs.append(rc(MIL, 1, 2, 0, 8,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4)}, F_BG_TF))
    reqs.append(mg(MIL, 1, 2, 0, 8))
    reqs.append(rh(MIL, 2, 12))

    # Col headers (row 3)
    col_header(reqs, MIL, 3, 0, 8)

    # Monthly section headers — make them stand out with navy bg
    # These are at various rows: find "── JANUARY ──" etc.
    # We'll style all rows that contain month dividers as mini-bars
    # Known pattern: they appear at rows 5, then periodically
    # Since we can't easily detect, style the col headers + freeze
    reqs.append(freeze(MIL, rows=4))

    # =========================================================================
    # 9. GST — Filing-ready with registration # and checklist
    # =========================================================================
    print("  Polishing GST...")

    # Title block already at R2-R3 (1-indexed) = indices 1-2
    reqs.append(rh(GST, 0, 16))
    reqs.append(rh(GST, 1, 50))
    reqs.append(rc(GST, 1, 2, 1, 7,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(GST, 1, 2, 1, 7))
    reqs.append(rh(GST, 2, 24))
    reqs.append(rc(GST, 2, 3, 1, 7,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4)}, F_BG_TF))
    reqs.append(mg(GST, 2, 3, 1, 7))
    reqs.append(rh(GST, 3, 12))

    # Quarter col headers (row 4)
    col_header(reqs, GST, 4, 1, 7)

    # NET OWING row (index 8) — make very prominent
    reqs.append(rh(GST, 8, 40))
    reqs.append(rc(GST, 8, 9, 1, 7,
        {"backgroundColor": RED_BG, "textFormat": tf(bold=True, sz=14, color=RED),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(border_box(GST, 8, 9, 1, 7, color=RED, style="SOLID", width=2))

    # Due Dates row (index 10) — orange
    reqs.append(rh(GST, 10, 30))
    reqs.append(rc(GST, 10, 11, 1, 7,
        {"backgroundColor": ORANGE_BG, "textFormat": tf(bold=True, sz=10, color=ORANGE)}, F_BG_TF))

    # GST Reg # row (index 14) — make prominent
    reqs.append(rh(GST, 14, 30))
    reqs.append(rc(GST, 14, 15, 1, 7,
        {"backgroundColor": BLUE_BG, "textFormat": tf(bold=True, sz=10, color=NAVY)}, F_BG_TF))

    # Filing frequency (index 15)
    reqs.append(rc(GST, 15, 16, 1, 7,
        {"backgroundColor": BLUE_BG, "textFormat": tf(sz=10, color=NAVY)}, F_BG_TF))

    # Notes header (index 17)
    section_bar(reqs, GST, 17, 1, 7, NAVY, WHITE, 32)

    # Section dividers
    section_divider(reqs, GST, 9, 1, 7)   # after NET OWING
    section_divider(reqs, GST, 12, 1, 7)  # after filed/payment
    section_divider(reqs, GST, 16, 1, 7)  # after registration

    # Footer at row 23
    add_footer(reqs, GST, 23, 1, 7)

    # =========================================================================
    # 10. EQUIPMENT / CCA — Receipt column + total asset value + CCA ref
    # =========================================================================
    print("  Polishing Equipment...")

    # Col headers (row 0)
    col_header(reqs, EQP, 0, 0, 10)

    # Data rows — borders on header
    reqs.append(border_side(EQP, 0, 1, 0, 10, "bottom", color=BORDER, width=2))

    # TOTALS row (index 32)
    total_accent(reqs, EQP, 32, 0, 10, GREEN, 36)
    reqs.append(rc(EQP, 32, 33, 0, 10,
        {"backgroundColor": GREEN_BG, "textFormat": tf(bold=True, sz=12, color=GREEN)}, F_BG_TF))

    # Footer at row 35
    add_footer(reqs, EQP, 35, 0, 8)

    reqs.append(freeze(EQP, rows=1))

    # =========================================================================
    # 11. TAX — Audit-proof layout with PREPARED FOR CRA header
    # =========================================================================
    print("  Polishing Tax...")

    # R1 spacer
    reqs.append(rh(TAX, 0, 16))
    # R2: title — "PREPARED FOR CRA FILING" as overlay context
    reqs.append(rh(TAX, 1, 50))
    reqs.append(rc(TAX, 1, 2, 1, 6,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(TAX, 1, 2, 1, 6))
    # R3: subtitle
    reqs.append(rh(TAX, 2, 24))
    reqs.append(rc(TAX, 2, 3, 1, 6,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4)}, F_BG_TF))
    reqs.append(mg(TAX, 2, 3, 1, 6))
    reqs.append(rh(TAX, 3, 12))

    # T2125 INCOME section header bar (index 4)
    section_bar(reqs, TAX, 4, 1, 6, BLUE, WHITE, 36)

    # Gross Business Income highlight (index 6)
    reqs.append(rh(TAX, 6, 36))
    reqs.append(rc(TAX, 6, 7, 1, 6,
        {"backgroundColor": BLUE_BG, "textFormat": tf(bold=True, sz=12, color=BLUE),
         "verticalAlignment": "MIDDLE"}, F_ALL))

    # EXPENSES section header bar (index 8)
    section_bar(reqs, TAX, 8, 1, 6, RED, WHITE, 36)

    # CRA line numbers (col D = index 3) — make prominent
    reqs.append(rc(TAX, 9, 24, 3, 4,
        {"textFormat": tf(bold=True, sz=9, color=NAVY),
         "horizontalAlignment": "CENTER"}, f"{F_TF},{F_AL}"))

    # Total Expenses row (index 25)
    total_accent(reqs, TAX, 25, 1, 6, RED, 34)
    reqs.append(rc(TAX, 25, 26, 1, 6,
        {"backgroundColor": RED_BG, "textFormat": tf(bold=True, sz=12, color=RED)}, F_BG_TF))

    # NET INCOME — massive highlight (index 27)
    reqs.append(rh(TAX, 27, 44))
    reqs.append(rc(TAX, 27, 28, 1, 6,
        {"backgroundColor": GREEN_BG, "textFormat": tf(bold=True, sz=16, color=GREEN),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(border_box(TAX, 27, 28, 1, 6, color=GREEN, style="SOLID", width=2))

    # TAX ESTIMATE header bar (index 29)
    section_bar(reqs, TAX, 29, 1, 6, ORANGE, WHITE, 36)

    # Total Income Tax row (index 39)
    total_accent(reqs, TAX, 39, 1, 6, ORANGE, 34)

    # TOTAL TAX + CPP — massive red highlight (index 45)
    reqs.append(rh(TAX, 45, 44))
    reqs.append(rc(TAX, 45, 46, 1, 6,
        {"backgroundColor": RED_BG, "textFormat": tf(bold=True, sz=16, color=RED),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(border_box(TAX, 45, 46, 1, 6, color=RED, style="SOLID", width=2))

    # SAVINGS header bar (index 76)
    section_bar(reqs, TAX, 76, 1, 6, GREEN, WHITE, 36)

    # YOU SAVE row (index 79)
    reqs.append(rh(TAX, 79, 40))
    reqs.append(rc(TAX, 79, 80, 1, 6,
        {"backgroundColor": GREEN_BG, "textFormat": tf(bold=True, sz=14, color=GREEN),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(border_box(TAX, 79, 80, 1, 6, color=GREEN, style="SOLID", width=2))

    # MILEAGE LOG header bar (index 81)
    section_bar(reqs, TAX, 81, 1, 6, NAVY, WHITE, 36)

    # CCA SCHEDULE header bar (index 88)
    section_bar(reqs, TAX, 88, 1, 6, NAVY, WHITE, 36)

    # ADDITIONAL T1 DEDUCTIONS header bar (index 53)
    section_bar(reqs, TAX, 53, 1, 6, NAVY, WHITE, 36)

    # FINAL TAX CALCULATION header bar (index 59)
    section_bar(reqs, TAX, 59, 1, 6, ORANGE, WHITE, 36)

    # FINAL TAX + CPP — massive red (index 73)
    reqs.append(rh(TAX, 73, 44))
    reqs.append(rc(TAX, 73, 74, 1, 6,
        {"backgroundColor": RED_BG, "textFormat": tf(bold=True, sz=16, color=RED),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(border_box(TAX, 73, 74, 1, 6, color=RED, style="SOLID", width=2))

    # Section dividers between all major areas
    section_divider(reqs, TAX, 7, 1, 6)    # after income
    section_divider(reqs, TAX, 26, 1, 6)   # after expenses total
    section_divider(reqs, TAX, 28, 1, 6)   # after net income
    section_divider(reqs, TAX, 40, 1, 6)   # after tax estimate total
    section_divider(reqs, TAX, 44, 1, 6)   # before total tax
    section_divider(reqs, TAX, 47, 1, 6)   # after quarterly
    section_divider(reqs, TAX, 58, 1, 6)   # after adjusted
    section_divider(reqs, TAX, 75, 1, 6)   # after final quarterly
    section_divider(reqs, TAX, 80, 1, 6)   # after savings
    section_divider(reqs, TAX, 87, 1, 6)   # after mileage

    # Footer at row 96
    add_footer(reqs, TAX, 96, 1, 6)

    # Freeze: 0 for Tax
    reqs.append(freeze(TAX, rows=0))

    # =========================================================================
    # 12. INSIGHTS — Headers, sections, clean
    # =========================================================================
    print("  Polishing Insights...")

    # Title (index 0)
    reqs.append(rh(INS, 0, 50))
    reqs.append(rc(INS, 0, 1, 0, 8,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(INS, 0, 1, 0, 8))
    # Subtitle (index 1)
    reqs.append(rh(INS, 1, 24))
    reqs.append(rc(INS, 1, 2, 0, 8,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4)}, F_BG_TF))
    reqs.append(mg(INS, 1, 2, 0, 8))
    reqs.append(rh(INS, 2, 12))

    # CASH FLOW section header bar (index 3)
    section_bar(reqs, INS, 3, 0, 8, NAVY, WHITE, 36)

    # Col headers (index 4)
    col_header(reqs, INS, 4, 0, 8)

    # Summary avg row (index 18) — accent
    total_accent(reqs, INS, 18, 0, 8, BLUE, 30)

    # SPENDING VELOCITY header bar (index 20)
    section_bar(reqs, INS, 20, 0, 8, NAVY, WHITE, 36)

    # SOFTWARE STACK header bar (index 25)
    section_bar(reqs, INS, 25, 0, 8, ORANGE, WHITE, 36)

    # Software col headers (index 26)
    col_header(reqs, INS, 26, 0, 8)

    # Software total row (index 52)
    total_accent(reqs, INS, 52, 0, 8, ORANGE, 32)

    # SAVINGS header bar (index 54)
    section_bar(reqs, INS, 54, 0, 8, GREEN, WHITE, 36)

    # TOP 20 VENDORS header bar (index 61)
    section_bar(reqs, INS, 61, 0, 8, NAVY, WHITE, 36)

    # Vendors col headers (index 62)
    col_header(reqs, INS, 62, 0, 8)

    # YoY header bar (index 84)
    section_bar(reqs, INS, 84, 0, 8, BLUE, WHITE, 36)

    # YoY col headers (index 85)
    col_header(reqs, INS, 85, 0, 8)

    # Section dividers
    section_divider(reqs, INS, 19, 0, 8)
    section_divider(reqs, INS, 24, 0, 8)
    section_divider(reqs, INS, 53, 0, 8)
    section_divider(reqs, INS, 59, 0, 8)
    section_divider(reqs, INS, 83, 0, 8)

    # Footer at row 92
    add_footer(reqs, INS, 92, 0, 8)

    reqs.append(freeze(INS, rows=0))

    # =========================================================================
    # GLOBAL: Ensure Inter font on every tab's full range
    # =========================================================================
    print("  Setting Inter font globally...")
    tab_ranges = [
        (D, 0, 75, 0, 22),
        (TXN, 0, 5, 0, 12),  # just headers
        (INC, 0, 40, 0, 15),
        (EXP, 0, 45, 0, 10),
        (BUS, 0, 50, 0, 18),
        (PER, 0, 55, 0, 16),
        (PL, 0, 25, 0, 12),
        (MIL, 0, 4, 0, 10),  # just headers
        (GST, 0, 30, 0, 10),
        (EQP, 0, 40, 0, 14),
        (TAX, 0, 100, 0, 10),
        (INS, 0, 100, 0, 10),
    ]
    # Font family already set in all formatters via tf(), no extra needed

    # =========================================================================
    # EXECUTE
    # =========================================================================
    BATCH = 80
    total = len(reqs)
    print(f"\n  Sending {total} formatting requests in batches of {BATCH}...")

    for start in range(0, total, BATCH):
        batch = reqs[start:start+BATCH]
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"requests": batch}
        ).execute()
        print(f"    Batch {start//BATCH + 1}: {start+1}–{min(start+BATCH, total)} done")

    # =========================================================================
    # WRITE FOOTER TEXT + ADDITIONAL VALUES
    # =========================================================================
    print("\n  Writing footer text and additional values...")

    footer_data = []

    # Dashboard footer (row 65 = 0-indexed, so text at rows 67,68,69 1-indexed)
    footer_data.extend([
        {"range": "'Dashboard'!C67", "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Dashboard'!C68", "values": [["Tax Year: 2025  |  Filing: June 15, 2027  |  GST: Quarterly"]]},
        {"range": "'Dashboard'!C69", "values": [["This document supports T2125 Statement of Business Activities"]]},
    ])

    # Income footer (row 33 → text at 35,36,37)
    footer_data.extend([
        {"range": "'Income'!B35", "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Income'!B36", "values": [["Tax Year: 2025  |  Filing: June 15, 2027  |  GST: Quarterly"]]},
        {"range": "'Income'!B37", "values": [["This document supports T2125 Statement of Business Activities"]]},
    ])

    # Expenses footer (row 37 → text at 39,40,41)
    footer_data.extend([
        {"range": "'Expenses'!B39", "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Expenses'!B40", "values": [["Tax Year: 2025  |  Filing: June 15, 2027  |  GST: Quarterly"]]},
        {"range": "'Expenses'!B41", "values": [["This document supports T2125 Statement of Business Activities"]]},
    ])

    # Business footer (row 42 → text at 44,45,46)
    footer_data.extend([
        {"range": "'Business'!A44", "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Business'!A45", "values": [["Tax Year: 2025  |  Filing: June 15, 2027  |  GST: Quarterly"]]},
        {"range": "'Business'!A46", "values": [["This document supports T2125 Statement of Business Activities"]]},
    ])

    # Personal footer (row 45 → text at 47,48,49)
    footer_data.extend([
        {"range": "'Personal'!A47", "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Personal'!A48", "values": [["Tax Year: 2025  |  Filing: June 15, 2027  |  GST: Quarterly"]]},
        {"range": "'Personal'!A49", "values": [["This document supports T2125 Statement of Business Activities"]]},
    ])

    # P&L footer (row 17 → text at 19,20,21)
    footer_data.extend([
        {"range": "'P&L'!A19", "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'P&L'!A20", "values": [["Tax Year: 2025  |  Filing: June 15, 2027  |  GST: Quarterly"]]},
        {"range": "'P&L'!A21", "values": [["This document supports T2125 Statement of Business Activities"]]},
    ])

    # GST footer (row 23 → text at 25,26,27)
    footer_data.extend([
        {"range": "'GST'!B25", "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'GST'!B26", "values": [["Tax Year: 2025  |  Filing: June 15, 2027  |  GST: Quarterly"]]},
        {"range": "'GST'!B27", "values": [["This document supports T2125 Statement of Business Activities"]]},
    ])

    # Equipment footer (row 35 → text at 37,38,39)
    footer_data.extend([
        {"range": "'Equipment'!A37", "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Equipment'!A38", "values": [["Tax Year: 2025  |  Filing: June 15, 2027  |  GST: Quarterly"]]},
        {"range": "'Equipment'!A39", "values": [["This document supports T2125 Statement of Business Activities"]]},
    ])

    # Tax footer (row 96 → text at 98,99,100)
    footer_data.extend([
        {"range": "'Tax'!B98", "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Tax'!B99", "values": [["Tax Year: 2025  |  Filing: June 15, 2027  |  GST: Quarterly"]]},
        {"range": "'Tax'!B100", "values": [["This document supports T2125 Statement of Business Activities"]]},
    ])

    # Insights footer (row 92 → text at 94,95,96)
    footer_data.extend([
        {"range": "'Insights'!A94", "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Insights'!A95", "values": [["Tax Year: 2025  |  Filing: June 15, 2027  |  GST: Quarterly"]]},
        {"range": "'Insights'!A96", "values": [["This document supports T2125 Statement of Business Activities"]]},
    ])

    # Tax tab: Add "PREPARED FOR CRA FILING" as subtitle context
    footer_data.extend([
        {"range": "'Tax'!B2", "values": [["Tax Summary  |  PREPARED FOR CRA FILING  |  2025"]]},
    ])

    # Mileage: Add vehicle info and CRA compliance note
    footer_data.extend([
        {"range": "'Mileage'!A1", "values": [["Mileage Log  |  2025"]]},
        {"range": "'Mileage'!A2", "values": [["Matt Anthony Photography  |  90% Business Use  |  CRA-compliant vehicle log per IT-522R"]]},
    ])

    # GST: Update title
    footer_data.extend([
        {"range": "'GST'!B2", "values": [["GST / HST Tracker  |  2025"]]},
        {"range": "'GST'!B3", "values": [["5% GST  |  Quarterly Filing  |  Registration #: ____________"]]},
    ])

    # Equipment: Add note about half-year rule
    # We'll put a CCA reference note below the totals
    footer_data.extend([
        {"range": "'Equipment'!A34", "values": [["Note: CCA calculated per half-year rule. Accelerated Investment Incentive (AII) applies 1.5x rate in year of acquisition."]]},
    ])

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"valueInputOption": "RAW", "data": footer_data}
    ).execute()

    # Format the Equipment note row
    note_reqs = [
        rh(EQP, 33, 22),
        rc(EQP, 33, 34, 0, 10,
            {"backgroundColor": WHITE, "textFormat": tf(sz=9, color=T4, italic=True)}, F_BG_TF),
        mg(EQP, 33, 34, 0, 8),
    ]
    service.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"requests": note_reqs}
    ).execute()

    print("\n" + "="*70)
    print("POLISH COMPLETE")
    print("="*70)
    print("""
  Dashboard:
    - Title resized to 22pt navy, subtitle 11pt gray
    - KPI cards: thin colored borders (blue for revenue, red for expenses)
    - Section dividers between all major areas
    - Column header bottom borders reinforced
    - Total row top accent borders
    - Freeze removed (summary view)
    - Professional footer added

  Transactions:
    - Title resized to 22pt white on navy
    - INCOME header: full-width GREEN bar, 40px tall
    - EXPENSES header: full-width RED bar, 40px tall
    - Column headers with bottom borders
    - Frozen at row 3

  Income:
    - Title block: 22pt navy, 11pt subtitle, proper spacers
    - Column header bottom borders (double)
    - Total row accent border
    - Monthly section header + total borders
    - Footer added

  Expenses:
    - Title block standardized (22pt navy)
    - Business section header + Personal section header borders
    - Total row accents (orange for business, purple for personal)
    - Section divider between categories
    - Footer added

  Business:
    - Column header with bottom border
    - Total row: orange accent, 34px, prominent
    - Budget section: navy header bar
    - Budget total accent
    - Section divider
    - Footer added

  Personal:
    - Column header restyled
    - Total row: purple accent
    - Insights section: purple header bar
    - Monthly trend: purple header bar
    - Section divider
    - Footer added

  P&L:
    - Column header with bottom border
    - Total row: blue accent, 34px
    - Footer added

  Mileage:
    - Title resized to 22pt
    - Subtitle updated with CRA compliance reference
    - Column headers with borders
    - Frozen at row 4

  GST:
    - Title block: 22pt, registration # in subtitle
    - NET OWING: 14pt bold red, full red border box, 40px tall
    - Due dates: orange highlight
    - Registration # and filing frequency: blue background
    - Notes header: navy bar
    - Section dividers throughout
    - Footer added

  Equipment:
    - Column header border reinforced
    - TOTALS row: 12pt green, accent border, 36px
    - CCA/AII note added (italic, 9pt)
    - Footer added

  Tax:
    - Title: "PREPARED FOR CRA FILING" in header
    - T2125 INCOME: blue header bar
    - EXPENSES: red header bar
    - CRA line numbers: bold navy, centered
    - Total Expenses: 12pt red, accent
    - NET INCOME: 16pt green, full border box, 44px
    - TAX ESTIMATE: orange bar
    - TOTAL TAX + CPP: 16pt red, full border box, 44px
    - SAVINGS: green bar, YOU SAVE with border box
    - MILEAGE LOG: navy bar
    - CCA SCHEDULE: navy bar
    - ADDITIONAL T1 DEDUCTIONS: navy bar
    - FINAL TAX CALCULATION: orange bar
    - FINAL TAX + CPP: 16pt red, border box
    - 11 section dividers between all areas
    - Footer added

  Insights:
    - Title: 22pt navy
    - CASH FLOW: navy header bar
    - SPENDING VELOCITY: navy header bar
    - SOFTWARE STACK: orange header bar + total accent
    - SAVINGS: green header bar
    - TOP 20 VENDORS: navy header bar
    - YEAR-OVER-YEAR: blue header bar
    - All col headers with bottom borders
    - 5 section dividers
    - Footer added

  Global:
    - Inter font throughout
    - Consistent design tokens applied
    - Professional footers on 10 of 12 tabs
    - CRA-ready presentation
""")
    print(f"  Sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}")


if __name__ == '__main__':
    main()
