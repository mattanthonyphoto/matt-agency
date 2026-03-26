"""
Finish remaining polish: P&L charts + Mileage + Equipment tabs.
(Income, Expenses, Business, Personal done. P&L formatting done, just needs charts.)
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_sheets_service

SHEET_ID = '1TyX4sOIo6CxblxjNM9Yft5h5vZO_BGhQjHlgC0uzQtI'

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
CYAN      = {"red": 0.059, "green": 0.588, "blue": 0.682}
CYAN_BG   = {"red": 0.906, "green": 0.961, "blue": 0.973}
WHITE     = {"red": 1, "green": 1, "blue": 1}
ALT_ROW   = {"red": 0.965, "green": 0.969, "blue": 0.976}
BORDER    = {"red": 0.890, "green": 0.898, "blue": 0.910}
T1        = {"red": 0.098, "green": 0.114, "blue": 0.149}
T3        = {"red": 0.549, "green": 0.573, "blue": 0.612}
T4        = {"red": 0.702, "green": 0.718, "blue": 0.745}
GRAY_DIV  = {"red": 0.820, "green": 0.830, "blue": 0.845}

def gr(sid, sr, er, sc, ec):
    return {"sheetId": sid, "startRowIndex": sr, "endRowIndex": er,
            "startColumnIndex": sc, "endColumnIndex": ec}

def rc(sid, sr, er, sc, ec, fmt, fields):
    return {"repeatCell": {"range": gr(sid, sr, er, sc, ec),
            "cell": {"userEnteredFormat": fmt}, "fields": fields}}

def mg(sid, sr, er, sc, ec):
    return {"mergeCells": {"range": gr(sid, sr, er, sc, ec), "mergeType": "MERGE_ALL"}}

def um(sid, sr, er, sc, ec):
    return {"unmergeCells": {"range": gr(sid, sr, er, sc, ec)}}

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
F_AL = "userEnteredFormat.horizontalAlignment"
F_VA = "userEnteredFormat.verticalAlignment"
F_BG_TF = f"{F_BG},{F_TF}"
F_ALL = f"{F_BG},{F_TF},{F_AL},{F_VA}"
F_BG_TF_AL = f"{F_BG},{F_TF},{F_AL}"

def section_bar(reqs, sid, row, sc, ec, bg_color, text_color=WHITE, height=36):
    reqs.append(rh(sid, row, height))
    reqs.append(rc(sid, row, row+1, sc, ec,
        {"backgroundColor": bg_color,
         "textFormat": tf(bold=True, sz=12, color=text_color),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    if ec - sc > 1:
        reqs.append(mg(sid, row, row+1, sc, ec))

def col_header(reqs, sid, row, sc, ec, height=32):
    reqs.append(rc(sid, row, row+1, sc, ec,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=9, color=T3)}, F_BG_TF))
    reqs.append(border_side(sid, row, row+1, sc, ec, "bottom", color=BORDER, style="SOLID", width=2))
    reqs.append(rh(sid, row, height))

def total_accent(reqs, sid, row, sc, ec, accent_color, height=32):
    reqs.append(border_side(sid, row, row+1, sc, ec, "top", color=accent_color, style="SOLID", width=2))
    reqs.append(rh(sid, row, height))

def alt_rows(reqs, sid, start, end, sc, ec):
    for r in range(start, end):
        bg = ALT_ROW if (r - start) % 2 == 1 else WHITE
        reqs.append(rc(sid, r, r+1, sc, ec, {"backgroundColor": bg}, F_BG))

def section_divider(reqs, sid, row, sc, ec):
    reqs.append(border_side(sid, row, row+1, sc, ec, "bottom", color=GRAY_DIV, style="SOLID", width=1))

def spacer_row(reqs, sid, row, ec, px=12):
    reqs.append(rh(sid, row, px))
    reqs.append(rc(sid, row, row+1, 0, ec, {"backgroundColor": WHITE}, F_BG))

def right_align_cols(reqs, sid, sr, er, sc, ec):
    reqs.append(rc(sid, sr, er, sc, ec, {"horizontalAlignment": "RIGHT"}, F_AL))

def add_footer(reqs, sid, start_row, sc, ec):
    reqs.append(rh(sid, start_row, 20))
    reqs.append(rc(sid, start_row, start_row+1, 0, ec, {"backgroundColor": WHITE}, F_BG))
    reqs.append(border_side(sid, start_row, start_row+1, sc, ec, "bottom", color=BORDER, width=1))
    for i in range(1, 4):
        r = start_row + i
        reqs.append(rh(sid, r, 18))
        reqs.append(rc(sid, r, r+1, sc, ec,
            {"backgroundColor": WHITE, "textFormat": tf(sz=9, color=T4, italic=(i==3))}, F_BG_TF))
        if ec - sc > 1:
            reqs.append(mg(sid, r, r+1, sc, ec))

def execute_batch(service, reqs, label=""):
    BATCH = 80
    total = len(reqs)
    if total == 0:
        return
    print(f"    Sending {total} requests for {label}...")
    for start in range(0, total, BATCH):
        batch = reqs[start:start+BATCH]
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"requests": batch}
        ).execute()
    print(f"    Done: {label}")


def main():
    service = get_sheets_service()
    ss = service.spreadsheets().get(spreadsheetId=SHEET_ID, fields='sheets.properties').execute()
    sheets = {s['properties']['title']: s['properties']['sheetId'] for s in ss['sheets']}

    PL  = sheets['P&L']
    MIL = sheets['Mileage']
    EQP = sheets['Equipment']

    # =========================================================================
    # P&L CHARTS
    # =========================================================================
    print("\n[5/7] P&L CHARTS")

    # Write P&L values (footer already written by formatting pass)
    val_data = [
        {"range": "'P&L'!A2", "values": [["Profit & Loss"]]},
        {"range": "'P&L'!A3", "values": [["Monthly income statement  ·  2025"]]},
        {"range": "'P&L'!F2", "values": [["$102,573"]]},
        {"range": "'P&L'!F3", "values": [["Revenue"]]},
        {"range": "'P&L'!H2", "values": [["-$3,634"]]},
        {"range": "'P&L'!H3", "values": [["Profit"]]},
        {"range": "'P&L'!J2", "values": [["-3.5%"]]},
        {"range": "'P&L'!J3", "values": [["Margin"]]},
        {"range": "'P&L'!A23", "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'P&L'!A24", "values": [["Tax Year: 2025  |  Filing: June 15, 2027  |  GST: Quarterly"]]},
        {"range": "'P&L'!A25", "values": [["This document supports T2125 Statement of Business Activities"]]},
    ]
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"valueInputOption": "RAW", "data": val_data}
    ).execute()

    chart_reqs = [
        {"addChart": {
            "chart": {
                "spec": {
                    "title": "Revenue vs Expenses",
                    "titleTextFormat": {"foregroundColorStyle": {"rgbColor": T3}, "fontSize": 11, "bold": True, "fontFamily": "Inter"},
                    "basicChart": {
                        "chartType": "COLUMN",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {"position": "BOTTOM_AXIS", "format": {"fontFamily": "Inter", "fontSize": 9, "foregroundColorStyle": {"rgbColor": T4}}},
                            {"position": "LEFT_AXIS", "format": {"fontFamily": "Inter", "fontSize": 9, "foregroundColorStyle": {"rgbColor": T4}}}
                        ],
                        "domains": [{"domain": {"sourceRange": {"sources": [gr(PL, 5, 17, 0, 1)]}}}],
                        "series": [
                            {"series": {"sourceRange": {"sources": [gr(PL, 5, 17, 1, 2)]}}, "colorStyle": {"rgbColor": BLUE}, "targetAxis": "LEFT_AXIS"},
                            {"series": {"sourceRange": {"sources": [gr(PL, 5, 17, 2, 3)]}}, "colorStyle": {"rgbColor": RED}, "targetAxis": "LEFT_AXIS"}
                        ],
                        "headerCount": 0,
                    },
                    "backgroundColorStyle": {"rgbColor": WHITE},
                },
                "position": {"overlayPosition": {"anchorCell": {"sheetId": PL, "rowIndex": 21, "columnIndex": 0}, "widthPixels": 650, "heightPixels": 350}}
            }
        }},
        {"addChart": {
            "chart": {
                "spec": {
                    "title": "Cumulative Profit",
                    "titleTextFormat": {"foregroundColorStyle": {"rgbColor": T3}, "fontSize": 11, "bold": True, "fontFamily": "Inter"},
                    "basicChart": {
                        "chartType": "LINE",
                        "legendPosition": "NO_LEGEND",
                        "axis": [
                            {"position": "BOTTOM_AXIS", "format": {"fontFamily": "Inter", "fontSize": 9, "foregroundColorStyle": {"rgbColor": T4}}},
                            {"position": "LEFT_AXIS", "format": {"fontFamily": "Inter", "fontSize": 9, "foregroundColorStyle": {"rgbColor": T4}}}
                        ],
                        "domains": [{"domain": {"sourceRange": {"sources": [gr(PL, 5, 17, 0, 1)]}}}],
                        "series": [
                            {"series": {"sourceRange": {"sources": [gr(PL, 5, 17, 6, 7)]}}, "colorStyle": {"rgbColor": GREEN}, "targetAxis": "LEFT_AXIS"}
                        ],
                        "headerCount": 0,
                    },
                    "backgroundColorStyle": {"rgbColor": WHITE},
                },
                "position": {"overlayPosition": {"anchorCell": {"sheetId": PL, "rowIndex": 21, "columnIndex": 7}, "widthPixels": 550, "heightPixels": 350}}
            }
        }}
    ]
    service.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"requests": chart_reqs}
    ).execute()
    print("  P&L charts: DONE")

    # =========================================================================
    # 6. MILEAGE TAB
    # =========================================================================
    print("\n[6/7] MILEAGE TAB")
    reqs = []

    reqs.append(rh(MIL, 0, 48))
    reqs.append(rc(MIL, 0, 1, 0, 8,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(MIL, 0, 1, 0, 8))

    reqs.append(rh(MIL, 1, 22))
    reqs.append(rc(MIL, 1, 2, 0, 8,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(MIL, 1, 2, 0, 8))

    spacer_row(reqs, MIL, 2, 8, 12)
    col_header(reqs, MIL, 3, 0, 8, 32)

    # Monthly section headers
    month_header_rows = [5, 12, 30, 42, 64, 87, 104, 136, 156, 172, 193, 203]
    for r in month_header_rows:
        reqs.append(rh(MIL, r, 28))
        reqs.append(rc(MIL, r, r+1, 0, 8,
            {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=10, color=NAVY)}, F_BG_TF))

    # Alternating per section
    sections = [
        (6, 11), (13, 29), (31, 41), (43, 63), (65, 86), (88, 103),
        (105, 135), (137, 155), (157, 171), (173, 192), (194, 202), (204, 223),
    ]
    for start, end in sections:
        alt_rows(reqs, MIL, start, end+1, 0, 8)

    local_rows = [10, 28, 40, 62, 85, 102, 134, 154, 170, 191, 201, 222]
    for r in local_rows:
        reqs.append(rc(MIL, r, r+1, 0, 8,
            {"textFormat": tf(sz=10, color=T3, italic=True)}, F_TF))

    for start, end in sections:
        reqs.append(rhs(MIL, start, end+1, 22))

    # SUMMARY
    section_bar(reqs, MIL, 225, 0, 8, NAVY, WHITE, 36)
    alt_rows(reqs, MIL, 226, 232, 0, 8)
    reqs.append(rhs(MIL, 226, 232, 26))
    right_align_cols(reqs, MIL, 226, 232, 4, 6)

    reqs.append(rc(MIL, 229, 230, 0, 8,
        {"backgroundColor": GREEN_BG, "textFormat": tf(bold=True, sz=11, color=GREEN)}, F_BG_TF))
    reqs.append(rc(MIL, 231, 232, 0, 8,
        {"backgroundColor": WHITE, "textFormat": tf(sz=9, color=T4, italic=True)}, F_BG_TF))

    # GAS RECEIPT LOG
    section_bar(reqs, MIL, 234, 0, 6, ORANGE, WHITE, 36)
    reqs.append(rh(MIL, 235, 22))
    reqs.append(rc(MIL, 235, 236, 0, 6,
        {"backgroundColor": ORANGE_BG, "textFormat": tf(sz=10, color=ORANGE)}, F_BG_TF))
    reqs.append(mg(MIL, 235, 236, 0, 6))

    spacer_row(reqs, MIL, 236, 8, 8)
    col_header(reqs, MIL, 237, 0, 6, 30)

    alt_rows(reqs, MIL, 238, 302, 0, 6)
    reqs.append(rhs(MIL, 238, 302, 22))
    right_align_cols(reqs, MIL, 238, 302, 3, 6)

    # FUEL SUMMARY
    reqs.append(rh(MIL, 303, 30))
    reqs.append(rc(MIL, 303, 304, 0, 6,
        {"backgroundColor": GREEN_BG, "textFormat": tf(bold=True, sz=11, color=GREEN)}, F_BG_TF))
    total_accent(reqs, MIL, 303, 0, 6, GREEN, 30)

    alt_rows(reqs, MIL, 304, 308, 0, 8)
    reqs.append(rhs(MIL, 304, 308, 24))
    right_align_cols(reqs, MIL, 304, 308, 3, 6)

    # Column widths
    reqs.append(cw(MIL, 0, 80))
    reqs.append(cw(MIL, 1, 120))
    reqs.append(cw(MIL, 2, 180))
    reqs.append(cw(MIL, 3, 220))
    reqs.append(cw(MIL, 4, 100))
    reqs.append(cw(MIL, 5, 80))
    reqs.append(cw(MIL, 6, 200))
    reqs.append(cw(MIL, 7, 180))

    reqs.append(freeze(MIL, rows=4))

    execute_batch(service, reqs, "Mileage formatting")

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"valueInputOption": "RAW", "data": [
            {"range": "'Mileage'!A1", "values": [["Mileage Log — 2025"]]},
            {"range": "'Mileage'!A2", "values": [["CRA-compliant vehicle log  ·  90% business use  ·  IT-522R"]]},
        ]}
    ).execute()
    print("  Mileage tab: DONE")

    # =========================================================================
    # 7. EQUIPMENT TAB
    # =========================================================================
    print("\n[7/7] EQUIPMENT TAB")

    # Unmerge existing merges
    unmerge_reqs = [
        um(EQP, 33, 34, 0, 8),
        um(EQP, 36, 37, 0, 8),
        um(EQP, 37, 38, 0, 8),
        um(EQP, 38, 39, 0, 8),
    ]
    service.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"requests": unmerge_reqs}
    ).execute()
    time.sleep(0.5)

    # Insert 4 rows for title block
    service.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"requests": [
            {"insertDimension": {
                "range": {"sheetId": EQP, "dimension": "ROWS", "startIndex": 0, "endIndex": 4},
                "inheritFromBefore": False
            }}
        ]}
    ).execute()
    time.sleep(1)

    reqs = []

    spacer_row(reqs, EQP, 0, 14, 16)
    reqs.append(rh(EQP, 1, 48))
    reqs.append(rc(EQP, 1, 2, 0, 5,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(EQP, 1, 2, 0, 5))

    # KPI cards
    reqs.append(rc(EQP, 1, 2, 5, 7,
        {"backgroundColor": BLUE_BG, "textFormat": tf(bold=True, sz=14, color=BLUE),
         "verticalAlignment": "MIDDLE", "horizontalAlignment": "CENTER"}, F_ALL))
    reqs.append(mg(EQP, 1, 2, 5, 7))
    reqs.append(border_box(EQP, 1, 2, 5, 7, color=BLUE, style="SOLID", width=1))

    reqs.append(rc(EQP, 1, 2, 7, 9,
        {"backgroundColor": GREEN_BG, "textFormat": tf(bold=True, sz=14, color=GREEN),
         "verticalAlignment": "MIDDLE", "horizontalAlignment": "CENTER"}, F_ALL))
    reqs.append(mg(EQP, 1, 2, 7, 9))
    reqs.append(border_box(EQP, 1, 2, 7, 9, color=GREEN, style="SOLID", width=1))

    reqs.append(rc(EQP, 1, 2, 9, 11,
        {"backgroundColor": ORANGE_BG, "textFormat": tf(bold=True, sz=14, color=ORANGE),
         "verticalAlignment": "MIDDLE", "horizontalAlignment": "CENTER"}, F_ALL))
    reqs.append(mg(EQP, 1, 2, 9, 11))
    reqs.append(border_box(EQP, 1, 2, 9, 11, color=ORANGE, style="SOLID", width=1))

    reqs.append(rh(EQP, 2, 22))
    reqs.append(rc(EQP, 2, 3, 0, 5,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(EQP, 2, 3, 0, 5))
    for sc, ec, bg in [(5,7,BLUE_BG),(7,9,GREEN_BG),(9,11,ORANGE_BG)]:
        reqs.append(rc(EQP, 2, 3, sc, ec,
            {"backgroundColor": bg, "textFormat": tf(sz=9, color=T3),
             "horizontalAlignment": "CENTER"}, F_BG_TF_AL))
        reqs.append(mg(EQP, 2, 3, sc, ec))

    spacer_row(reqs, EQP, 3, 14, 12)

    # Column headers (shifted)
    col_header(reqs, EQP, 4, 0, 12, 32)

    # 12 asset rows
    alt_rows(reqs, EQP, 5, 17, 0, 12)
    reqs.append(rhs(EQP, 5, 17, 26))
    right_align_cols(reqs, EQP, 5, 17, 4, 9)

    spacer_row(reqs, EQP, 17, 14, 16)
    section_divider(reqs, EQP, 17, 0, 10)

    # CCA CLASS REFERENCE
    section_bar(reqs, EQP, 19, 0, 8, NAVY, WHITE, 36)
    alt_rows(reqs, EQP, 20, 24, 0, 8)
    reqs.append(rhs(EQP, 20, 24, 26))

    reqs.append(rh(EQP, 25, 8))
    reqs.append(rh(EQP, 26, 40))
    reqs.append(rc(EQP, 26, 27, 0, 10,
        {"backgroundColor": BLUE_BG, "textFormat": tf(sz=9, color=NAVY, italic=True)}, F_BG_TF))
    reqs.append(mg(EQP, 26, 27, 0, 10))

    # Column widths
    reqs.append(cw(EQP, 0, 230))
    reqs.append(cw(EQP, 1, 100))
    reqs.append(cw(EQP, 2, 80))
    reqs.append(cw(EQP, 3, 60))
    reqs.append(cw(EQP, 4, 100))
    reqs.append(cw(EQP, 5, 100))
    reqs.append(cw(EQP, 6, 100))
    reqs.append(cw(EQP, 7, 100))
    reqs.append(cw(EQP, 8, 180))
    reqs.append(cw(EQP, 9, 30))
    reqs.append(cw(EQP, 10, 30))
    reqs.append(cw(EQP, 11, 220))

    add_footer(reqs, EQP, 28, 0, 8)
    reqs.append(freeze(EQP, rows=5))

    execute_batch(service, reqs, "Equipment formatting")

    val_data = [
        {"range": "'Equipment'!A2", "values": [["Equipment Register"]]},
        {"range": "'Equipment'!A3", "values": [["Capital Cost Allowance Schedule  ·  AII Applied  ·  2025"]]},
        {"range": "'Equipment'!F2", "values": [["$37,501"]]},
        {"range": "'Equipment'!F3", "values": [["Total Assets"]]},
        {"range": "'Equipment'!H2", "values": [["$4,406"]]},
        {"range": "'Equipment'!H3", "values": [["CCA This Year"]]},
        {"range": "'Equipment'!J2", "values": [["$1,322"]]},
        {"range": "'Equipment'!J3", "values": [["Tax Savings (est)"]]},
        {"range": "'Equipment'!A20", "values": [
            ["Class 8", "20%", "Camera bodies, lenses, lighting, drones, accessories"],
            ["Class 10", "30%", "Motor vehicles"],
            ["Class 12", "100%", "Tools, utensils, kitchen ware <$500"],
            ["Class 50", "55%", "Computers, monitors, electronic data processing equipment"],
        ]},
        {"range": "'Equipment'!A27", "values": [["AII Note: The Accelerated Investment Incentive applies a 1.5x multiplier to CCA rates in the year an asset is acquired. This enhanced deduction was applied to all 2025 acquisitions."]]},
        {"range": "'Equipment'!A30", "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Equipment'!A31", "values": [["Tax Year: 2025  |  Filing: June 15, 2027  |  GST: Quarterly"]]},
        {"range": "'Equipment'!A32", "values": [["This document supports T2125 Statement of Business Activities"]]},
    ]
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"valueInputOption": "RAW", "data": val_data}
    ).execute()
    print("  Equipment tab: DONE")

    # Global Inter font
    print("\nApplying Inter font on remaining tabs...")
    reqs = []
    for sid, sr, er, sc, ec in [
        (PL, 0, 30, 0, 12),
        (MIL, 0, 310, 0, 8),
        (EQP, 0, 35, 0, 12),
    ]:
        reqs.append(rc(sid, sr, er, sc, ec,
            {"textFormat": {"fontFamily": "Inter"}},
            "userEnteredFormat.textFormat.fontFamily"))

    execute_batch(service, reqs, "Global Inter font")

    print("\n" + "="*70)
    print("REMAINING TABS POLISHED")
    print("="*70)
    print(f"\n  Sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}")


if __name__ == '__main__':
    main()
