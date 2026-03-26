"""
Format 2026 Finance Sheet — Full restoration pass.
Targets: Transactions tab (primary), then verification pass on all other tabs.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_sheets_service

SHEET_ID = '1fPpOPnAYEnfCu33h1ki9NzFGTUOkpgd4mMSQX_sT9CY'

# ── Design Tokens ──────────────────────────────────────────────────────────────
NAVY      = {"red": 0.153, "green": 0.173, "blue": 0.224}
BLUE      = {"red": 0.224, "green": 0.443, "blue": 0.871}
BLUE_BG   = {"red": 0.922, "green": 0.941, "blue": 0.988}
BLUE_L    = {"red": 0.957, "green": 0.969, "blue": 0.996}
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

# Category dropdown list
ALL_CATS = [
    "Advertising & Marketing","Professional Fees","Vehicle","Insurance",
    "Interest & Bank Charges","Office Supplies (<$500)","Rent / Co-working",
    "Software & Subscriptions","Travel","Telephone & Internet","Subcontractors",
    "Meals & Entertainment","Home Office","Equipment (CCA)","Other Business",
    "Housing","Utilities","Groceries","Dining Out","Transportation",
    "Health & Fitness","Subscriptions","Clothing","Entertainment",
    "Travel (Personal)","Savings/Investments","Other Personal"
]

# ── Helpers ────────────────────────────────────────────────────────────────────
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

F_BG      = "userEnteredFormat.backgroundColor"
F_TF      = "userEnteredFormat.textFormat"
F_NF      = "userEnteredFormat.numberFormat"
F_AL      = "userEnteredFormat.horizontalAlignment"
F_VA      = "userEnteredFormat.verticalAlignment"
F_WR      = "userEnteredFormat.wrapStrategy"
F_BG_TF   = f"{F_BG},{F_TF}"
F_ALL     = f"{F_BG},{F_TF},{F_AL},{F_VA}"
F_BG_TF_AL= f"{F_BG},{F_TF},{F_AL}"

def section_bar(reqs, sid, row, sc, ec, bg_color, text_color=WHITE, height=40):
    reqs.append(rh(sid, row, height))
    reqs.append(rc(sid, row, row+1, sc, ec,
        {"backgroundColor": bg_color,
         "textFormat": tf(bold=True, sz=14, color=text_color),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    if ec - sc > 1:
        reqs.append(mg(sid, row, row+1, sc, ec))

def col_header(reqs, sid, row, sc, ec, height=30):
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

def spacer_row(reqs, sid, row, ec, px=12):
    reqs.append(rh(sid, row, px))
    reqs.append(rc(sid, row, row+1, 0, ec, {"backgroundColor": WHITE}, F_BG))

def right_align_cols(reqs, sid, sr, er, sc, ec):
    reqs.append(rc(sid, sr, er, sc, ec, {"horizontalAlignment": "RIGHT"}, F_AL))

def section_divider(reqs, sid, row, sc, ec):
    reqs.append(border_side(sid, row, row+1, sc, ec, "bottom", color=GRAY_DIV, style="SOLID", width=1))

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
    return start_row + 4


def execute_batch(service, reqs, label="", sleep_between=1.5):
    BATCH = 50  # stay well under 60 write/min
    total = len(reqs)
    if total == 0:
        print(f"    No requests for {label}")
        return
    print(f"    Sending {total} requests for {label}...")
    for start in range(0, total, BATCH):
        batch = reqs[start:start+BATCH]
        retries = 0
        while retries < 3:
            try:
                service.spreadsheets().batchUpdate(
                    spreadsheetId=SHEET_ID,
                    body={"requests": batch}
                ).execute()
                break
            except Exception as e:
                err = str(e)
                if "429" in err or "RATE_LIMIT" in err:
                    wait = 65 if retries == 0 else 90
                    print(f"    Rate limit, waiting {wait}s...")
                    time.sleep(wait)
                    retries += 1
                elif "mergeCells" in err and "merged range" in err:
                    # Unmerge that range first, then retry
                    print(f"    Merge conflict in batch, auto-unmerging and retrying...")
                    # Find the problematic mergeCells request and pre-unmerge
                    for req in batch:
                        if "mergeCells" in req:
                            r = req["mergeCells"]["range"]
                            try:
                                service.spreadsheets().batchUpdate(
                                    spreadsheetId=SHEET_ID,
                                    body={"requests": [{"unmergeCells": {"range": r}}]}
                                ).execute()
                            except:
                                pass
                    retries += 1
                    time.sleep(1)
                else:
                    raise
        if sleep_between:
            time.sleep(sleep_between)
    print(f"    Done: {label}")


# =============================================================================
# TRANSACTIONS TAB
# Actual layout (1-indexed):
#   Row 1  (idx 0): Title "Transactions · 2026"
#   Row 2  (idx 1): Subtitle "All income and expenses"
#   Row 3  (idx 2): Spacer
#   Row 4  (idx 3): INCOME section header
#   Row 5  (idx 4): Column headers
#   Rows 6-16 (idx 5-15): 11 income data rows
#   Rows 17-18 (idx 16-17): spacer/blank between sections
#   Row 19 (idx 18): EXPENSES section header
#   Row 20 (idx 19): Column headers
#   Rows 21-203+ (idx 20+): expense data rows (183 currently)
# =============================================================================
def format_transactions(service, TXN, income_count, expense_count):
    print(f"\n[TRANSACTIONS] income={income_count} rows, expense={expense_count} rows")

    # Column indices (A=0 through N=13):
    # A=0 Date, B=1 Vendor, C=2 Description, D=3 Amount, E=4 Business(checkbox),
    # F=5 Category, G=6 %, H=7 GST, I=8 Receipt(checkbox), J=9 Payment,
    # K=10 Account, L=11 Notes, M=12 (blank), N=13 Month helper

    NCOLS = 14  # A through N

    # Rows (0-indexed):
    r_title     = 0
    r_subtitle  = 1
    r_spacer1   = 2
    r_inc_hdr   = 3   # INCOME section bar
    r_inc_cols  = 4   # column headers under INCOME
    r_inc_start = 5   # first income data row
    r_inc_end   = r_inc_start + income_count  # exclusive
    r_spacer2   = r_inc_end      # blank spacer row
    r_spacer3   = r_inc_end + 1  # blank spacer row
    r_exp_hdr   = r_inc_end + 2  # EXPENSES section bar  (= row 19 if 11 income rows)
    r_exp_cols  = r_inc_end + 3  # column headers under EXPENSES
    r_exp_start = r_inc_end + 4  # first expense data row
    r_exp_end   = r_exp_start + expense_count  # exclusive

    # Footer sits 2 rows after last expense row
    r_footer    = r_exp_end + 2

    print(f"  Layout: inc_hdr={r_inc_hdr+1}, inc_cols={r_inc_cols+1}, "
          f"inc_data={r_inc_start+1}-{r_inc_end}, "
          f"exp_hdr={r_exp_hdr+1}, exp_cols={r_exp_cols+1}, "
          f"exp_data={r_exp_start+1}-{r_exp_end}, "
          f"footer={r_footer+1}")

    # ── Step 1: Unmerge anything that might be merged in title area ──────────
    unmerge_reqs = []
    for row in [r_title, r_subtitle, r_inc_hdr, r_exp_hdr]:
        unmerge_reqs.append(um(TXN, row, row+1, 0, NCOLS))
    try:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID, body={"requests": unmerge_reqs}
        ).execute()
    except Exception as e:
        print(f"    (unmerge warning: {e})")
    time.sleep(0.3)

    reqs = []

    # ── Row 1: Title ──────────────────────────────────────────────────────────
    # Bold 22pt navy, white bg, 48px tall, merged across A:N
    reqs.append(rh(TXN, r_title, 48))
    reqs.append(rc(TXN, r_title, r_title+1, 0, NCOLS,
        {"backgroundColor": WHITE,
         "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(TXN, r_title, r_title+1, 0, NCOLS))

    # ── Row 2: Subtitle ───────────────────────────────────────────────────────
    # 11pt muted gray (#B3B7BE ≈ T4 token), 22px tall, merged
    reqs.append(rh(TXN, r_subtitle, 22))
    reqs.append(rc(TXN, r_subtitle, r_subtitle+1, 0, NCOLS,
        {"backgroundColor": WHITE,
         "textFormat": tf(sz=11, color=T4),
         "verticalAlignment": "MIDDLE"}, F_BG_TF))
    reqs.append(mg(TXN, r_subtitle, r_subtitle+1, 0, NCOLS))

    # ── Row 3: Spacer ─────────────────────────────────────────────────────────
    reqs.append(rh(TXN, r_spacer1, 12))
    reqs.append(rc(TXN, r_spacer1, r_spacer1+1, 0, NCOLS, {"backgroundColor": WHITE}, F_BG))

    # Freeze rows 1-3 (freeze row index = 3)
    reqs.append(freeze(TXN, rows=3))

    # ── Row 4 (idx 3): INCOME section bar ────────────────────────────────────
    # Full-width green bar, bold 14pt green text on green bg, 40px
    reqs.append(rh(TXN, r_inc_hdr, 40))
    reqs.append(rc(TXN, r_inc_hdr, r_inc_hdr+1, 0, NCOLS,
        {"backgroundColor": GREEN_BG,
         "textFormat": tf(bold=True, sz=14, color=GREEN),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    # Merge A through M (leave N/col13 for month helper value display)
    reqs.append(mg(TXN, r_inc_hdr, r_inc_hdr+1, 0, 13))
    # Amount cell (col D, idx 3) — large bold green, right-aligned, $#,##0 format
    # (Already merged into the header merge — amount shown in merged cell as SUM)
    # We'll put the SUM formula in the merged cell and right-align
    reqs.append(rc(TXN, r_inc_hdr, r_inc_hdr+1, 0, 13,
        {"horizontalAlignment": "RIGHT",
         "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}, f"{F_AL},{F_NF}"))

    # ── Row 5 (idx 4): Column headers under INCOME ────────────────────────────
    col_header(reqs, TXN, r_inc_cols, 0, NCOLS, height=30)

    # ── Income data rows ──────────────────────────────────────────────────────
    if income_count > 0:
        alt_rows(reqs, TXN, r_inc_start, r_inc_end, 0, NCOLS)
        reqs.append(rhs(TXN, r_inc_start, r_inc_end, 26))
        # Inter 10pt for all data
        reqs.append(rc(TXN, r_inc_start, r_inc_end, 0, NCOLS,
            {"textFormat": tf(sz=10)}, F_TF))
        # Amount col D (idx 3): right-align, $#,##0.00
        reqs.append(rc(TXN, r_inc_start, r_inc_end, 3, 4,
            {"horizontalAlignment": "RIGHT",
             "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}},
            f"{F_AL},{F_NF}"))
        # Conditional formatting: positive amounts = green text (income rows always positive)
        reqs.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [gr(TXN, r_inc_start, r_inc_end, 3, 4)],
                    "booleanRule": {
                        "condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "0"}]},
                        "format": {"textFormat": {"foregroundColor": GREEN}}
                    }
                },
                "index": 0
            }
        })

    # ── Spacer rows between INCOME and EXPENSES ───────────────────────────────
    for r in [r_spacer2, r_spacer3]:
        reqs.append(rh(TXN, r, 12))
        reqs.append(rc(TXN, r, r+1, 0, NCOLS, {"backgroundColor": WHITE}, F_BG))

    # ── EXPENSES section bar ──────────────────────────────────────────────────
    reqs.append(rh(TXN, r_exp_hdr, 40))
    reqs.append(rc(TXN, r_exp_hdr, r_exp_hdr+1, 0, NCOLS,
        {"backgroundColor": RED_BG,
         "textFormat": tf(bold=True, sz=14, color=RED),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(TXN, r_exp_hdr, r_exp_hdr+1, 0, 13))
    reqs.append(rc(TXN, r_exp_hdr, r_exp_hdr+1, 0, 13,
        {"horizontalAlignment": "RIGHT",
         "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}, f"{F_AL},{F_NF}"))

    # ── Column headers under EXPENSES ─────────────────────────────────────────
    col_header(reqs, TXN, r_exp_cols, 0, NCOLS, height=30)

    # ── Expense data rows ─────────────────────────────────────────────────────
    if expense_count > 0:
        alt_rows(reqs, TXN, r_exp_start, r_exp_end, 0, NCOLS)
        reqs.append(rhs(TXN, r_exp_start, r_exp_end, 26))
        # Inter 10pt for all data
        reqs.append(rc(TXN, r_exp_start, r_exp_end, 0, NCOLS,
            {"textFormat": tf(sz=10)}, F_TF))
        # Amount col D (idx 3): right-align, $#,##0.00
        reqs.append(rc(TXN, r_exp_start, r_exp_end, 3, 4,
            {"horizontalAlignment": "RIGHT",
             "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}},
            f"{F_AL},{F_NF}"))
        # Conditional: negative = red text, positive = green text
        reqs.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [gr(TXN, r_exp_start, r_exp_end, 3, 4)],
                    "booleanRule": {
                        "condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "0"}]},
                        "format": {"textFormat": {"foregroundColor": RED}}
                    }
                },
                "index": 0
            }
        })
        reqs.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [gr(TXN, r_exp_start, r_exp_end, 3, 4)],
                    "booleanRule": {
                        "condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "0"}]},
                        "format": {"textFormat": {"foregroundColor": GREEN}}
                    }
                },
                "index": 0
            }
        })
        # Business col E (idx 4) conditional: TRUE = soft blue bg
        reqs.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [gr(TXN, r_exp_start, r_exp_end, 0, NCOLS - 1)],
                    "booleanRule": {
                        "condition": {
                            "type": "CUSTOM_FORMULA",
                            "values": [{"userEnteredValue": f"=$E{r_exp_start+1}=TRUE"}]
                        },
                        "format": {"backgroundColor": BLUE_L}
                    }
                },
                "index": 0
            }
        })

    # ── Date column format: "MMM d, yyyy" ─────────────────────────────────────
    # Apply to all data rows (income + expense), col A (idx 0)
    all_data_rows = []
    if income_count > 0:
        all_data_rows.append((r_inc_start, r_inc_end))
    if expense_count > 0:
        all_data_rows.append((r_exp_start, r_exp_end))

    for sr, er in all_data_rows:
        reqs.append(rc(TXN, sr, er, 0, 1,
            {"numberFormat": {"type": "DATE", "pattern": "MMM d, yyyy"}}, F_NF))

    # ── Column widths ─────────────────────────────────────────────────────────
    # A=Date 105px, B=Vendor 180px, C=Description 200px, D=Amount 110px,
    # E=Business 80px, F=Category 200px, G=% 60px, H=GST 90px,
    # I=Receipt 80px, J=Payment 90px, K=Account 120px, L=Notes 140px,
    # M=blank 20px, N=Month (hidden)
    col_widths = [105, 180, 200, 110, 80, 200, 60, 90, 80, 90, 120, 140, 20]
    for c, w in enumerate(col_widths):
        reqs.append(cw(TXN, c, w))

    # Hide column N (index 13) — month helper
    reqs.append({"updateDimensionProperties": {
        "range": {"sheetId": TXN, "dimension": "COLUMNS", "startIndex": 13, "endIndex": 14},
        "properties": {"hiddenByUser": True},
        "fields": "hiddenByUser"
    }})

    # ── Footer ────────────────────────────────────────────────────────────────
    add_footer(reqs, TXN, r_footer, 0, 13)

    # ── Global Inter font on Transactions ─────────────────────────────────────
    reqs.append(rc(TXN, 0, r_footer + 5, 0, NCOLS,
        {"textFormat": {"fontFamily": "Inter"}},
        "userEnteredFormat.textFormat.fontFamily"))

    execute_batch(service, reqs, "Transactions")

    # ── Write text values ─────────────────────────────────────────────────────
    val_data = [
        # Title row — re-confirm text
        {"range": "Transactions!A1", "values": [["Transactions · 2026"]]},
        {"range": "Transactions!A2", "values": [["All income and expenses  ·  Tax Year 2026"]]},
        # INCOME header with SUM formula
        {"range": f"Transactions!A{r_inc_hdr+1}",
         "values": [[f"INCOME  ·  Total: =SUM(D{r_inc_start+1}:D{r_inc_end})"]]},
        # EXPENSES header with SUM formula
        {"range": f"Transactions!A{r_exp_hdr+1}",
         "values": [[f"EXPENSES  ·  Total: =SUM(D{r_exp_start+1}:D{r_exp_end})"]]},
        # Footer text
        {"range": f"Transactions!A{r_footer+2}", "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": f"Transactions!A{r_footer+3}", "values": [["Tax Year: 2026  |  Filing: June 15, 2028  |  GST: Quarterly"]]},
        {"range": f"Transactions!A{r_footer+4}", "values": [["This document supports T2125 Statement of Business Activities"]]},
    ]
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": val_data}
    ).execute()

    # ── Checkboxes for Business (E) and Receipt (I) columns ───────────────────
    checkbox_reqs = []
    for sr, er in all_data_rows:
        # Business col E (idx 4)
        checkbox_reqs.append({
            "setDataValidation": {
                "range": gr(TXN, sr, er, 4, 5),
                "rule": {
                    "condition": {"type": "BOOLEAN"},
                    "strict": True,
                    "showCustomUi": True
                }
            }
        })
        # Receipt col I (idx 8)
        checkbox_reqs.append({
            "setDataValidation": {
                "range": gr(TXN, sr, er, 8, 9),
                "rule": {
                    "condition": {"type": "BOOLEAN"},
                    "strict": True,
                    "showCustomUi": True
                }
            }
        })
        # Category dropdown col F (idx 5)
        checkbox_reqs.append({
            "setDataValidation": {
                "range": gr(TXN, sr, er, 5, 6),
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": [{"userEnteredValue": c} for c in ALL_CATS]
                    },
                    "strict": False,
                    "showCustomUi": True
                }
            }
        })

    if checkbox_reqs:
        # Send in batches of 50
        for start in range(0, len(checkbox_reqs), 50):
            batch = checkbox_reqs[start:start+50]
            service.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID, body={"requests": batch}
            ).execute()
        print("    Applied checkboxes + category dropdowns")

    print(f"  Transactions tab: DONE")
    return {
        "r_inc_hdr": r_inc_hdr, "r_inc_cols": r_inc_cols,
        "r_inc_start": r_inc_start, "r_inc_end": r_inc_end,
        "r_exp_hdr": r_exp_hdr, "r_exp_cols": r_exp_cols,
        "r_exp_start": r_exp_start, "r_exp_end": r_exp_end,
        "r_footer": r_footer
    }


# =============================================================================
# HELPER: Read Transactions layout dynamically
# =============================================================================
def read_transactions_layout(service):
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range='Transactions!A1:A500',
        valueRenderOption='FORMATTED_VALUE'
    ).execute()
    rows = result.get('values', [])

    income_count = 0
    expense_count = 0
    in_income = False
    in_expense = False

    for i, r in enumerate(rows):
        v = r[0].strip() if r and r[0] else ''
        if v.startswith('INCOME'):
            in_income = True
            in_expense = False
            continue
        if v.startswith('EXPENSES'):
            in_expense = True
            in_income = False
            continue
        if v == 'Date':
            continue
        if v and in_income:
            income_count += 1
        elif v and in_expense:
            expense_count += 1

    return income_count, expense_count


# =============================================================================
# OTHER TABS — Quick verification + re-apply any lost formatting
# =============================================================================
def format_dashboard(service, D, reqs):
    print("\n[DASHBOARD] Re-applying title block, KPI borders, section dividers...")
    reqs.append(rh(D, 0, 16))
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
    # KPI card borders
    reqs.append(border_box(D, 4, 8, 2, 5, color=BLUE, style="SOLID", width=1))
    reqs.append(border_box(D, 4, 8, 6, 9, color=RED, style="SOLID", width=1))
    # Section dividers
    for row in [8, 13, 29, 36, 52, 53]:
        reqs.append(border_side(D, row, row+1, 2, 9, "bottom", color=GRAY_DIV))
    # Col header borders
    for row in [15, 38, 55]:
        reqs.append(border_side(D, row, row+1, 2, 9, "bottom", color=BORDER, width=2))
    # Total accents
    total_accent(reqs, D, 28, 2, 9, BLUE)
    total_accent(reqs, D, 51, 2, 9, BLUE)
    reqs.append(freeze(D, rows=0))
    add_footer(reqs, D, 65, 2, 9)


def format_income(service, INC, reqs):
    print("\n[INCOME] Re-applying title block, green totals...")
    reqs.append(rh(INC, 0, 16))
    reqs.append(rc(INC, 0, 1, 0, 14, {"backgroundColor": WHITE}, F_BG))
    reqs.append(rh(INC, 1, 50))
    reqs.append(rc(INC, 1, 2, 1, 9,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(INC, 1, 2, 1, 9))
    reqs.append(rh(INC, 2, 24))
    reqs.append(rc(INC, 2, 3, 1, 9,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4)}, F_BG_TF))
    reqs.append(mg(INC, 2, 3, 1, 9))
    reqs.append(rh(INC, 3, 12))
    # Column header borders
    reqs.append(border_side(INC, 4, 5, 1, 14, "bottom", color=BORDER, width=2))
    reqs.append(border_side(INC, 5, 6, 1, 14, "bottom", color=BORDER, width=2))
    # Total accent
    total_accent(reqs, INC, 14, 1, 14, GREEN)
    reqs.append(rc(INC, 14, 15, 1, 14,
        {"backgroundColor": GREEN_BG, "textFormat": tf(bold=True, sz=11, color=GREEN)}, F_BG_TF))
    # Monthly section
    reqs.append(border_side(INC, 17, 18, 1, 4, "bottom", color=BORDER, width=2))
    total_accent(reqs, INC, 30, 1, 4, GREEN)
    add_footer(reqs, INC, 33, 1, 8)


def format_expenses(service, EXP, reqs):
    print("\n[EXPENSES] Re-applying title block, orange/purple sections...")
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
    reqs.append(border_side(EXP, 5, 6, 1, 7, "bottom", color=BORDER, width=2))
    reqs.append(border_side(EXP, 24, 25, 1, 7, "bottom", color=BORDER, width=2))
    # Business section header (orange)
    reqs.append(rh(EXP, 4, 36))
    reqs.append(rc(EXP, 4, 5, 1, 7,
        {"backgroundColor": ORANGE_BG, "textFormat": tf(bold=True, sz=14, color=ORANGE),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(EXP, 4, 5, 1, 7))
    total_accent(reqs, EXP, 21, 1, 7, ORANGE)
    reqs.append(rc(EXP, 21, 22, 1, 7,
        {"backgroundColor": ORANGE_BG, "textFormat": tf(bold=True, sz=11, color=ORANGE)}, F_BG_TF))
    section_divider(reqs, EXP, 22, 1, 7)
    # Personal section header (purple)
    reqs.append(rh(EXP, 23, 36))
    reqs.append(rc(EXP, 23, 24, 1, 7,
        {"backgroundColor": PURPLE_BG, "textFormat": tf(bold=True, sz=14, color=PURPLE),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(EXP, 23, 24, 1, 7))
    total_accent(reqs, EXP, 34, 1, 7, PURPLE)
    add_footer(reqs, EXP, 37, 1, 8)


def format_business(service, BUS, reqs):
    print("\n[BUSINESS] Re-applying title + KPIs, orange total, budget section...")
    # Title block (already has rows)
    reqs.append(rh(BUS, 1, 48))
    reqs.append(rc(BUS, 1, 2, 0, 6,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(BUS, 1, 2, 0, 6))
    reqs.append(rh(BUS, 2, 22))
    reqs.append(rc(BUS, 2, 3, 0, 6,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4),
         "verticalAlignment": "MIDDLE"}, F_BG_TF))
    reqs.append(mg(BUS, 2, 3, 0, 6))
    # KPI cards: YTD (orange), Monthly Avg (blue)
    reqs.append(rc(BUS, 1, 2, 7, 9,
        {"backgroundColor": ORANGE_BG, "textFormat": tf(bold=True, sz=14, color=ORANGE),
         "verticalAlignment": "MIDDLE", "horizontalAlignment": "CENTER"}, F_ALL))
    reqs.append(mg(BUS, 1, 2, 7, 9))
    reqs.append(border_box(BUS, 1, 2, 7, 9, color=ORANGE, style="SOLID", width=1))
    reqs.append(rc(BUS, 1, 2, 9, 11,
        {"backgroundColor": BLUE_BG, "textFormat": tf(bold=True, sz=14, color=BLUE),
         "verticalAlignment": "MIDDLE", "horizontalAlignment": "CENTER"}, F_ALL))
    reqs.append(mg(BUS, 1, 2, 9, 11))
    reqs.append(border_box(BUS, 1, 2, 9, 11, color=BLUE, style="SOLID", width=1))
    # Col header at row 4 (idx 4)
    col_header(reqs, BUS, 4, 0, 17, 32)
    # TOTAL row (idx 21)
    reqs.append(rh(BUS, 21, 30))
    reqs.append(rc(BUS, 21, 22, 0, 17,
        {"backgroundColor": ORANGE_BG, "textFormat": tf(bold=True, sz=11, color=ORANGE)}, F_BG_TF))
    total_accent(reqs, BUS, 21, 0, 17, ORANGE, 30)
    section_divider(reqs, BUS, 22, 0, 17)
    # Budget section header (navy, idx 26)
    section_bar(reqs, BUS, 26, 0, 7, NAVY, WHITE, 36)
    col_header(reqs, BUS, 27, 0, 7)
    total_accent(reqs, BUS, 43, 0, 7, BLUE, 30)
    reqs.append(rc(BUS, 43, 44, 0, 7,
        {"backgroundColor": BLUE_BG, "textFormat": tf(bold=True, sz=11, color=BLUE)}, F_BG_TF))
    reqs.append(freeze(BUS, rows=5))
    add_footer(reqs, BUS, 46, 0, 8)


def format_personal(service, PER, reqs):
    print("\n[PERSONAL] Re-applying title + KPIs, purple total, insights...")
    reqs.append(rh(PER, 1, 48))
    reqs.append(rc(PER, 1, 2, 0, 5,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(PER, 1, 2, 0, 5))
    reqs.append(rh(PER, 2, 22))
    reqs.append(rc(PER, 2, 3, 0, 5,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4)}, F_BG_TF))
    reqs.append(mg(PER, 2, 3, 0, 5))
    # KPI cards: YTD (purple), Monthly Avg (blue)
    reqs.append(rc(PER, 1, 2, 6, 8,
        {"backgroundColor": PURPLE_BG, "textFormat": tf(bold=True, sz=14, color=PURPLE),
         "verticalAlignment": "MIDDLE", "horizontalAlignment": "CENTER"}, F_ALL))
    reqs.append(mg(PER, 1, 2, 6, 8))
    reqs.append(border_box(PER, 1, 2, 6, 8, color=PURPLE, style="SOLID", width=1))
    reqs.append(rc(PER, 1, 2, 8, 10,
        {"backgroundColor": BLUE_BG, "textFormat": tf(bold=True, sz=14, color=BLUE),
         "verticalAlignment": "MIDDLE", "horizontalAlignment": "CENTER"}, F_ALL))
    reqs.append(mg(PER, 1, 2, 8, 10))
    reqs.append(border_box(PER, 1, 2, 8, 10, color=BLUE, style="SOLID", width=1))
    # Col headers at idx 4
    col_header(reqs, PER, 4, 0, 16)
    # TOTAL (idx 18)
    reqs.append(rh(PER, 18, 32))
    reqs.append(rc(PER, 18, 19, 0, 16,
        {"backgroundColor": PURPLE_BG, "textFormat": tf(bold=True, sz=11, color=PURPLE)}, F_BG_TF))
    total_accent(reqs, PER, 18, 0, 16, PURPLE, 32)
    section_divider(reqs, PER, 19, 0, 14)
    # Insights section (navy, idx 23)
    section_bar(reqs, PER, 23, 0, 5, NAVY, WHITE, 36)
    col_header(reqs, PER, 24, 0, 5)
    # Monthly trend (blue, idx 33)
    section_bar(reqs, PER, 33, 0, 4, BLUE, WHITE, 32)
    col_header(reqs, PER, 34, 0, 4)
    reqs.append(freeze(PER, rows=5))
    add_footer(reqs, PER, 49, 0, 8)


def format_pl(service, PL, reqs):
    print("\n[P&L] Re-applying title + KPIs, blue total, charts should exist...")
    reqs.append(rh(PL, 1, 48))
    reqs.append(rc(PL, 1, 2, 0, 4,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(PL, 1, 2, 0, 4))
    reqs.append(rh(PL, 2, 22))
    reqs.append(rc(PL, 2, 3, 0, 4,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4)}, F_BG_TF))
    reqs.append(mg(PL, 2, 3, 0, 4))
    # KPI cards: Revenue (blue), Profit (red), Margin (green)
    reqs.append(rc(PL, 1, 2, 5, 7,
        {"backgroundColor": BLUE_BG, "textFormat": tf(bold=True, sz=14, color=BLUE),
         "verticalAlignment": "MIDDLE", "horizontalAlignment": "CENTER"}, F_ALL))
    reqs.append(mg(PL, 1, 2, 5, 7))
    reqs.append(border_box(PL, 1, 2, 5, 7, color=BLUE, style="SOLID", width=1))
    reqs.append(rc(PL, 1, 2, 7, 9,
        {"backgroundColor": RED_BG, "textFormat": tf(bold=True, sz=14, color=RED),
         "verticalAlignment": "MIDDLE", "horizontalAlignment": "CENTER"}, F_ALL))
    reqs.append(mg(PL, 1, 2, 7, 9))
    reqs.append(border_box(PL, 1, 2, 7, 9, color=RED, style="SOLID", width=1))
    reqs.append(rc(PL, 1, 2, 9, 11,
        {"backgroundColor": GREEN_BG, "textFormat": tf(bold=True, sz=14, color=GREEN),
         "verticalAlignment": "MIDDLE", "horizontalAlignment": "CENTER"}, F_ALL))
    reqs.append(mg(PL, 1, 2, 9, 11))
    reqs.append(border_box(PL, 1, 2, 9, 11, color=GREEN, style="SOLID", width=1))
    # Col headers idx 4
    col_header(reqs, PL, 4, 0, 10, 32)
    # Data rows idx 5-16
    alt_rows(reqs, PL, 5, 17, 0, 10)
    reqs.append(rhs(PL, 5, 17, 26))
    # TOTAL idx 18 (blue)
    reqs.append(rh(PL, 18, 34))
    reqs.append(rc(PL, 18, 19, 0, 10,
        {"backgroundColor": BLUE_BG, "textFormat": tf(bold=True, sz=11, color=BLUE)}, F_BG_TF))
    total_accent(reqs, PL, 18, 0, 10, BLUE, 34)
    reqs.append(freeze(PL, rows=5))


def format_mileage(service, MIL, reqs):
    print("\n[MILEAGE] Re-applying title, CRA subtitle, monthly headers...")
    reqs.append(rh(MIL, 0, 48))
    reqs.append(rc(MIL, 0, 1, 0, 8,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(MIL, 0, 1, 0, 8))
    reqs.append(rh(MIL, 1, 22))
    reqs.append(rc(MIL, 1, 2, 0, 8,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4),
         "verticalAlignment": "MIDDLE"}, F_BG_TF))
    reqs.append(mg(MIL, 1, 2, 0, 8))
    spacer_row(reqs, MIL, 2, 8, 12)
    col_header(reqs, MIL, 3, 0, 8, 32)
    reqs.append(freeze(MIL, rows=4))


def format_gst(service, GST, reqs):
    print("\n[GST] Re-applying title, green collected, red ITCs, red NET OWING...")
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
    # Col headers (row 4)
    col_header(reqs, GST, 4, 1, 7)
    # GST Collected row (idx 5) — green
    reqs.append(rh(GST, 5, 32))
    reqs.append(rc(GST, 5, 6, 1, 7,
        {"backgroundColor": GREEN_BG, "textFormat": tf(bold=True, sz=11, color=GREEN),
         "verticalAlignment": "MIDDLE"}, F_BG_TF))
    # ITCs row (idx 6) — red
    reqs.append(rh(GST, 6, 32))
    reqs.append(rc(GST, 6, 7, 1, 7,
        {"backgroundColor": RED_BG, "textFormat": tf(bold=True, sz=11, color=RED),
         "verticalAlignment": "MIDDLE"}, F_BG_TF))
    # NET OWING (idx 8) — big red box
    reqs.append(rh(GST, 8, 40))
    reqs.append(rc(GST, 8, 9, 1, 7,
        {"backgroundColor": RED_BG, "textFormat": tf(bold=True, sz=14, color=RED),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(border_box(GST, 8, 9, 1, 7, color=RED, style="SOLID", width=2))
    # Due dates row (idx 10) — orange
    reqs.append(rh(GST, 10, 30))
    reqs.append(rc(GST, 10, 11, 1, 7,
        {"backgroundColor": ORANGE_BG, "textFormat": tf(bold=True, sz=10, color=ORANGE)}, F_BG_TF))
    # GST Reg # row (idx 14)
    reqs.append(rh(GST, 14, 30))
    reqs.append(rc(GST, 14, 15, 1, 7,
        {"backgroundColor": BLUE_BG, "textFormat": tf(bold=True, sz=10, color=NAVY)}, F_BG_TF))
    reqs.append(rc(GST, 15, 16, 1, 7,
        {"backgroundColor": BLUE_BG, "textFormat": tf(sz=10, color=NAVY)}, F_BG_TF))
    # Notes header (idx 17)
    section_bar(reqs, GST, 17, 1, 7, NAVY, WHITE, 32)
    # Section dividers
    for row in [9, 12, 16]:
        section_divider(reqs, GST, row, 1, 7)
    add_footer(reqs, GST, 23, 1, 7)


def format_equipment(service, EQP, reqs):
    print("\n[EQUIPMENT] Re-applying title + KPIs, green totals, CCA reference...")
    reqs.append(rh(EQP, 1, 48))
    reqs.append(rc(EQP, 1, 2, 0, 5,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(EQP, 1, 2, 0, 5))
    reqs.append(rh(EQP, 2, 22))
    reqs.append(rc(EQP, 2, 3, 0, 5,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4)}, F_BG_TF))
    reqs.append(mg(EQP, 2, 3, 0, 5))
    # KPI: Total Assets (blue), CCA (green), Tax Savings (orange)
    for (sc, ec, bg, fg) in [(5,7,BLUE_BG,BLUE),(7,9,GREEN_BG,GREEN),(9,11,ORANGE_BG,ORANGE)]:
        reqs.append(rc(EQP, 1, 2, sc, ec,
            {"backgroundColor": bg, "textFormat": tf(bold=True, sz=14, color=fg),
             "verticalAlignment": "MIDDLE", "horizontalAlignment": "CENTER"}, F_ALL))
        reqs.append(mg(EQP, 1, 2, sc, ec))
        reqs.append(border_box(EQP, 1, 2, sc, ec, color=fg, style="SOLID", width=1))
    # Col headers idx 4
    col_header(reqs, EQP, 4, 0, 12, 32)
    # Asset rows idx 5-16 alternating
    alt_rows(reqs, EQP, 5, 17, 0, 12)
    reqs.append(rhs(EQP, 5, 17, 26))
    spacer_row(reqs, EQP, 17, 14, 16)
    section_divider(reqs, EQP, 17, 0, 10)
    # CCA class reference (navy bar, idx 19)
    section_bar(reqs, EQP, 19, 0, 8, NAVY, WHITE, 36)
    alt_rows(reqs, EQP, 20, 24, 0, 8)
    reqs.append(rhs(EQP, 20, 24, 26))
    reqs.append(rh(EQP, 25, 8))
    reqs.append(rh(EQP, 26, 40))
    reqs.append(rc(EQP, 26, 27, 0, 10,
        {"backgroundColor": BLUE_BG, "textFormat": tf(sz=9, color=NAVY, italic=True)}, F_BG_TF))
    reqs.append(mg(EQP, 26, 27, 0, 10))
    reqs.append(freeze(EQP, rows=5))
    add_footer(reqs, EQP, 28, 0, 8)


def format_tax(service, TAX, reqs):
    print("\n[TAX] Re-applying PREPARED FOR CRA FILING, colored section bars, prominent rows...")
    reqs.append(rh(TAX, 0, 16))
    reqs.append(rh(TAX, 1, 50))
    reqs.append(rc(TAX, 1, 2, 1, 6,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(TAX, 1, 2, 1, 6))
    reqs.append(rh(TAX, 2, 24))
    reqs.append(rc(TAX, 2, 3, 1, 6,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4)}, F_BG_TF))
    reqs.append(mg(TAX, 2, 3, 1, 6))
    reqs.append(rh(TAX, 3, 12))
    # T2125 INCOME section header (blue, idx 4)
    section_bar(reqs, TAX, 4, 1, 6, BLUE, WHITE, 36)
    # Gross Business Income highlight (idx 6)
    reqs.append(rh(TAX, 6, 36))
    reqs.append(rc(TAX, 6, 7, 1, 6,
        {"backgroundColor": BLUE_BG, "textFormat": tf(bold=True, sz=12, color=BLUE),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    # EXPENSES section bar (red, idx 8)
    section_bar(reqs, TAX, 8, 1, 6, RED, WHITE, 36)
    # CRA line numbers (col D=idx 3) bold navy
    reqs.append(rc(TAX, 9, 24, 3, 4,
        {"textFormat": tf(bold=True, sz=9, color=NAVY),
         "horizontalAlignment": "CENTER"}, f"{F_TF},{F_AL}"))
    # Total Expenses (idx 25)
    total_accent(reqs, TAX, 25, 1, 6, RED, 34)
    reqs.append(rc(TAX, 25, 26, 1, 6,
        {"backgroundColor": RED_BG, "textFormat": tf(bold=True, sz=12, color=RED)}, F_BG_TF))
    # NET INCOME (idx 27)
    reqs.append(rh(TAX, 27, 44))
    reqs.append(rc(TAX, 27, 28, 1, 6,
        {"backgroundColor": GREEN_BG, "textFormat": tf(bold=True, sz=16, color=GREEN),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(border_box(TAX, 27, 28, 1, 6, color=GREEN, style="SOLID", width=2))
    # TAX ESTIMATE bar (orange, idx 29)
    section_bar(reqs, TAX, 29, 1, 6, ORANGE, WHITE, 36)
    # Total Income Tax (idx 39)
    total_accent(reqs, TAX, 39, 1, 6, ORANGE, 34)
    # TOTAL TAX + CPP (idx 45)
    reqs.append(rh(TAX, 45, 44))
    reqs.append(rc(TAX, 45, 46, 1, 6,
        {"backgroundColor": RED_BG, "textFormat": tf(bold=True, sz=16, color=RED),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(border_box(TAX, 45, 46, 1, 6, color=RED, style="SOLID", width=2))
    # SAVINGS bar (green, idx 76)
    section_bar(reqs, TAX, 76, 1, 6, GREEN, WHITE, 36)
    # YOU SAVE (idx 79)
    reqs.append(rh(TAX, 79, 40))
    reqs.append(rc(TAX, 79, 80, 1, 6,
        {"backgroundColor": GREEN_BG, "textFormat": tf(bold=True, sz=14, color=GREEN),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(border_box(TAX, 79, 80, 1, 6, color=GREEN, style="SOLID", width=2))
    # MILEAGE LOG (navy, idx 81)
    section_bar(reqs, TAX, 81, 1, 6, NAVY, WHITE, 36)
    # CCA SCHEDULE (navy, idx 88)
    section_bar(reqs, TAX, 88, 1, 6, NAVY, WHITE, 36)
    # ADDITIONAL T1 DEDUCTIONS (navy, idx 53)
    section_bar(reqs, TAX, 53, 1, 6, NAVY, WHITE, 36)
    # FINAL TAX CALCULATION (orange, idx 59)
    section_bar(reqs, TAX, 59, 1, 6, ORANGE, WHITE, 36)
    # FINAL TAX + CPP (red, idx 73)
    reqs.append(rh(TAX, 73, 44))
    reqs.append(rc(TAX, 73, 74, 1, 6,
        {"backgroundColor": RED_BG, "textFormat": tf(bold=True, sz=16, color=RED),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(border_box(TAX, 73, 74, 1, 6, color=RED, style="SOLID", width=2))
    # Section dividers
    for row in [7, 26, 28, 40, 44, 47, 58, 75, 80, 87]:
        section_divider(reqs, TAX, row, 1, 6)
    add_footer(reqs, TAX, 96, 1, 6)
    reqs.append(freeze(TAX, rows=0))


def format_insights(service, INS, reqs):
    print("\n[INSIGHTS] Re-applying section header bars...")
    reqs.append(rh(INS, 0, 50))
    reqs.append(rc(INS, 0, 1, 0, 8,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(INS, 0, 1, 0, 8))
    reqs.append(rh(INS, 1, 24))
    reqs.append(rc(INS, 1, 2, 0, 8,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4)}, F_BG_TF))
    reqs.append(mg(INS, 1, 2, 0, 8))
    reqs.append(rh(INS, 2, 12))
    # CASH FLOW (navy, idx 3)
    section_bar(reqs, INS, 3, 0, 8, NAVY, WHITE, 36)
    col_header(reqs, INS, 4, 0, 8)
    total_accent(reqs, INS, 18, 0, 8, BLUE, 30)
    # SPENDING VELOCITY (navy, idx 20)
    section_bar(reqs, INS, 20, 0, 8, NAVY, WHITE, 36)
    # SOFTWARE STACK (orange, idx 25)
    section_bar(reqs, INS, 25, 0, 8, ORANGE, WHITE, 36)
    col_header(reqs, INS, 26, 0, 8)
    total_accent(reqs, INS, 52, 0, 8, ORANGE, 32)
    # SAVINGS (green, idx 54)
    section_bar(reqs, INS, 54, 0, 8, GREEN, WHITE, 36)
    # TOP 20 VENDORS (navy, idx 61)
    section_bar(reqs, INS, 61, 0, 8, NAVY, WHITE, 36)
    col_header(reqs, INS, 62, 0, 8)
    # YoY (blue, idx 84)
    section_bar(reqs, INS, 84, 0, 8, BLUE, WHITE, 36)
    col_header(reqs, INS, 85, 0, 8)
    # Section dividers
    for row in [19, 24, 53, 59, 83]:
        section_divider(reqs, INS, row, 0, 8)
    add_footer(reqs, INS, 92, 0, 8)
    reqs.append(freeze(INS, rows=0))


# =============================================================================
# MAIN
# =============================================================================
def main():
    service = get_sheets_service()

    # Get all sheet IDs
    ss = service.spreadsheets().get(spreadsheetId=SHEET_ID, fields='sheets.properties').execute()
    sheets = {s['properties']['title']: s['properties']['sheetId'] for s in ss['sheets']}
    print("Tabs found:", list(sheets.keys()))

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

    # ── TRANSACTIONS (primary focus) ──────────────────────────────────────────
    # First, clear any existing conditional format rules on Transactions
    print("\nClearing conditional format rules on Transactions...")
    # Read current conditional rules
    ss_full = service.spreadsheets().get(
        spreadsheetId=SHEET_ID,
        ranges=['Transactions'],
        fields='sheets.conditionalFormats'
    ).execute()
    existing_rules = []
    for sheet in ss_full.get('sheets', []):
        existing_rules = sheet.get('conditionalFormats', [])
        break

    if existing_rules:
        # Delete all existing conditional rules (delete from highest index first)
        del_reqs = []
        for i in range(len(existing_rules) - 1, -1, -1):
            del_reqs.append({"deleteConditionalFormatRule": {"sheetId": TXN, "index": i}})
        if del_reqs:
            service.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID, body={"requests": del_reqs}
            ).execute()
            print(f"    Cleared {len(del_reqs)} existing conditional rules")

    # Read actual layout
    income_count, expense_count = read_transactions_layout(service)
    print(f"  Found: {income_count} income rows, {expense_count} expense rows")

    layout = format_transactions(service, TXN, income_count, expense_count)

    # ── Pre-unmerge all potentially merged areas on other tabs ───────────────
    print("\nPre-unmerging existing merges on all tabs...")
    unmerge_reqs = []
    # Dashboard title area
    for row in [1, 2]:
        unmerge_reqs.append(um(D, row, row+1, 2, 9))
    # Income
    for row in [1, 2, 14]:
        unmerge_reqs.append(um(INC, row, row+1, 1, 14))
    # Expenses
    for row in [1, 2, 4, 23]:
        unmerge_reqs.append(um(EXP, row, row+1, 1, 8))
    # Business
    for row in [1, 2]:
        unmerge_reqs.append(um(BUS, row, row+1, 0, 14))
    for row in [7, 9, 11]:
        unmerge_reqs.append(um(BUS, row, row+1, 7, 14))
    # Personal
    for row in [1, 2]:
        unmerge_reqs.append(um(PER, row, row+1, 0, 12))
    for row in [6, 8, 10]:
        unmerge_reqs.append(um(PER, row, row+1, 6, 12))
    # P&L
    for row in [1, 2]:
        unmerge_reqs.append(um(PL, row, row+1, 0, 12))
    for row in [5, 7, 9]:
        unmerge_reqs.append(um(PL, row, row+1, 5, 12))
    # Mileage
    for row in [0, 1]:
        unmerge_reqs.append(um(MIL, row, row+1, 0, 8))
    # GST
    for row in [1, 2, 17]:
        unmerge_reqs.append(um(GST, row, row+1, 1, 7))
    # Equipment
    for row in [1, 2, 19, 26]:
        unmerge_reqs.append(um(EQP, row, row+1, 0, 12))
    for row in [1, 7, 9]:
        unmerge_reqs.append(um(EQP, row, row+1, 5, 12))
    # Tax
    for row in [1, 2, 4, 8, 29, 53, 59, 76, 81, 88]:
        unmerge_reqs.append(um(TAX, row, row+1, 1, 6))
    # Insights
    for row in [0, 1, 3, 20, 25, 54, 61, 84]:
        unmerge_reqs.append(um(INS, row, row+1, 0, 8))

    # Send unmerge requests, tolerating errors on already-unmerged cells
    BATCH = 50
    for start in range(0, len(unmerge_reqs), BATCH):
        batch = unmerge_reqs[start:start+BATCH]
        try:
            service.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID, body={"requests": batch}
            ).execute()
        except Exception as e:
            # Some cells aren't merged — that's fine, continue
            print(f"    (unmerge batch tolerating error: {str(e)[:80]})")
        time.sleep(0.2)
    print("    Pre-unmerge complete")

    # ── ALL OTHER TABS — one tab at a time to avoid merge conflicts ──────────
    print("\nFormatting all other tabs (one at a time)...")

    tab_formatters = [
        ("Dashboard", D,   format_dashboard),
        ("Income",    INC, format_income),
        ("Expenses",  EXP, format_expenses),
        ("Business",  BUS, format_business),
        ("Personal",  PER, format_personal),
        ("P&L",       PL,  format_pl),
        ("Mileage",   MIL, format_mileage),
        ("GST",       GST, format_gst),
        ("Equipment", EQP, format_equipment),
        ("Tax",       TAX, format_tax),
        ("Insights",  INS, format_insights),
    ]

    for tab_name, sid, formatter in tab_formatters:
        reqs = []
        formatter(service, sid, reqs)
        # Add Inter font for this tab
        reqs.append(rc(sid, 0, 100, 0, 20,
            {"textFormat": {"fontFamily": "Inter"}},
            "userEnteredFormat.textFormat.fontFamily"))
        execute_batch(service, reqs, tab_name, sleep_between=2)
        time.sleep(1)

    # ── Footer text values for other tabs ─────────────────────────────────────
    print("\nWriting footer text values...")
    footer_data = [
        {"range": "'Dashboard'!C67",   "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Dashboard'!C68",   "values": [["Tax Year: 2026  |  Filing: June 15, 2028  |  GST: Quarterly"]]},
        {"range": "'Dashboard'!C69",   "values": [["This document supports T2125 Statement of Business Activities"]]},
        {"range": "'Income'!B35",      "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Income'!B36",      "values": [["Tax Year: 2026  |  Filing: June 15, 2028  |  GST: Quarterly"]]},
        {"range": "'Income'!B37",      "values": [["This document supports T2125 Statement of Business Activities"]]},
        {"range": "'Expenses'!B39",    "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Expenses'!B40",    "values": [["Tax Year: 2026  |  Filing: June 15, 2028  |  GST: Quarterly"]]},
        {"range": "'Expenses'!B41",    "values": [["This document supports T2125 Statement of Business Activities"]]},
        {"range": "'Business'!A48",    "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Business'!A49",    "values": [["Tax Year: 2026  |  Filing: June 15, 2028  |  GST: Quarterly"]]},
        {"range": "'Business'!A50",    "values": [["This document supports T2125 Statement of Business Activities"]]},
        {"range": "'Personal'!A51",    "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Personal'!A52",    "values": [["Tax Year: 2026  |  Filing: June 15, 2028  |  GST: Quarterly"]]},
        {"range": "'Personal'!A53",    "values": [["This document supports T2125 Statement of Business Activities"]]},
        {"range": "'P&L'!A23",         "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'P&L'!A24",         "values": [["Tax Year: 2026  |  Filing: June 15, 2028  |  GST: Quarterly"]]},
        {"range": "'P&L'!A25",         "values": [["This document supports T2125 Statement of Business Activities"]]},
        {"range": "'GST'!B25",         "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'GST'!B26",         "values": [["Tax Year: 2026  |  Filing: June 15, 2028  |  GST: Quarterly"]]},
        {"range": "'GST'!B27",         "values": [["This document supports T2125 Statement of Business Activities"]]},
        {"range": "'Equipment'!A30",   "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Equipment'!A31",   "values": [["Tax Year: 2026  |  Filing: June 15, 2028  |  GST: Quarterly"]]},
        {"range": "'Equipment'!A32",   "values": [["This document supports T2125 Statement of Business Activities"]]},
        {"range": "'Tax'!B98",         "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Tax'!B99",         "values": [["Tax Year: 2026  |  Filing: June 15, 2028  |  GST: Quarterly"]]},
        {"range": "'Tax'!B100",        "values": [["This document supports T2125 Statement of Business Activities"]]},
        {"range": "'Insights'!A94",    "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": "'Insights'!A95",    "values": [["Tax Year: 2026  |  Filing: June 15, 2028  |  GST: Quarterly"]]},
        {"range": "'Insights'!A96",    "values": [["This document supports T2125 Statement of Business Activities"]]},
        {"range": "'Mileage'!A1",      "values": [["Mileage Log — 2026"]]},
        {"range": "'Mileage'!A2",      "values": [["CRA-compliant vehicle log  ·  90% business use  ·  IT-522R"]]},
    ]
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"valueInputOption": "RAW", "data": footer_data}
    ).execute()
    print("    Footer text written")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("FORMATTING COMPLETE")
    print("=" * 70)
    print(f"""
TRANSACTIONS TAB (primary):
  - Row 1: "Transactions · 2026" — bold 22pt navy, white bg, 48px, merged A:N
  - Row 2: Subtitle — 11pt muted gray (T4), 22px, merged
  - Row 3: Spacer — 12px
  - Freeze: rows 1-3 (frozenRowCount=3)
  - INCOME header: green bg (#E7F7F0), bold 14pt green (#1E9F6C), 40px, merged A:M
    with right-aligned $#,##0 SUM formula
  - Income col headers: bold 9pt gray on white, bottom border, 30px
  - {income_count} income data rows: alternating white/#F7F8FA, 26px, Inter 10pt
    Date: MMM d, yyyy format
    Amount col D: right-aligned $#,##0.00, green text for positive
  - 2 spacer rows (12px) between sections
  - EXPENSES header: red bg (#FDEDED), bold 14pt red, 40px, merged A:M
    with right-aligned $#,##0 SUM formula
  - Expense col headers: same treatment as income
  - {expense_count} expense data rows: alternating, 26px, Inter 10pt
    Amount: $#,##0.00, red for negative / green for positive
    Business rows (col E = TRUE): soft blue bg (#F4F7FE)
  - Date col (A): 105px | Vendor (B): 180px | Desc (C): 200px | Amount (D): 110px
    Business (E): 80px | Category (F): 200px | % (G): 60px | GST (H): 90px
    Receipt (I): 80px | Payment (J): 90px | Account (K): 120px | Notes (L): 140px
  - Column N (month helper): hidden
  - Checkboxes: Business (E) + Receipt (I) for all data rows
  - Category dropdown (F): 27 ALL_CATS options
  - Footer: 3 muted italic lines at bottom

ALL OTHER TABS (verification + restoration):
  Dashboard: title 22pt navy, KPI borders, section dividers, footer
  Income: title block, green totals, footer
  Expenses: title block, orange/purple section bars, totals, footer
  Business: title + KPI cards (orange/blue), orange total, navy budget bar, footer
  Personal: title + KPI cards (purple/blue), purple total, insights/trend bars, footer
  P&L: title + KPI cards (blue/red/green), blue total, alternating rows, freeze
  Mileage: title 22pt, CRA subtitle, col headers, freeze row 4
  GST: title 22pt, green collected bar, red ITCs bar, red NET OWING box,
       orange due dates, blue registration row, navy notes bar, section dividers
  Equipment: title + KPI cards (blue/green/orange), alternating rows,
             navy CCA reference bar, AII note in blue-bg italic
  Tax: PREPARED FOR CRA FILING, blue income bar, red expenses bar,
       green NET INCOME box (16pt), red TOTAL TAX box (16pt),
       green SAVINGS bar + YOU SAVE box, 10+ section dividers
  Insights: title 22pt, navy/orange/green/blue section bars, col headers,
            section dividers, footer

  All tabs: 2026 footer text ("Tax Year: 2026 | Filing: June 15, 2028")
  Font: Inter throughout
""")
    print(f"  Sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}")


if __name__ == '__main__':
    main()
