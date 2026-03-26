"""
Professional redesign of the Financial Map spreadsheet.
Reads current content of all 6 tabs, then applies a premium financial consulting-style design.

Optimized: Uses wide-range formatting to minimize API requests. Includes retry with backoff.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_sheets_service

MAP_ID = '1nrzAfXzRiFIQpa85one6iuMXASIBbgPrwDoI6TwH9KU'

# ── Design Tokens ────────────────────────────────────────────────────────────
CHARCOAL    = {"red": 0.153, "green": 0.173, "blue": 0.224}
DARK_TEXT   = {"red": 0.227, "green": 0.247, "blue": 0.278}
BLUE        = {"red": 0.224, "green": 0.443, "blue": 0.871}
GREEN       = {"red": 0.118, "green": 0.624, "blue": 0.424}
RED         = {"red": 0.851, "green": 0.200, "blue": 0.200}
ORANGE      = {"red": 0.902, "green": 0.533, "blue": 0.118}
PURPLE      = {"red": 0.482, "green": 0.318, "blue": 0.804}
WHITE       = {"red": 1, "green": 1, "blue": 1}
GREY_666    = {"red": 0.400, "green": 0.400, "blue": 0.400}

ZEBRA       = {"red": 0.973, "green": 0.976, "blue": 0.980}
SECTION_BG  = {"red": 0.941, "green": 0.945, "blue": 0.953}
COL_HDR_BG  = CHARCOAL
TOTAL_BG    = {"red": 0.961, "green": 0.969, "blue": 1.000}
GRAND_BG    = {"red": 0.922, "green": 0.933, "blue": 0.980}
ACT_TINT    = {"red": 0.973, "green": 0.976, "blue": 0.992}

KPI_BLUE_BG   = {"red": 0.961, "green": 0.969, "blue": 1.000}
KPI_RED_BG    = {"red": 0.996, "green": 0.961, "blue": 0.961}
KPI_GREEN_BG  = {"red": 0.949, "green": 0.980, "blue": 0.961}
KPI_ORANGE_BG = {"red": 0.996, "green": 0.973, "blue": 0.941}
PALE_GREEN    = {"red": 0.906, "green": 0.965, "blue": 0.933}
PALE_BLUE     = {"red": 0.922, "green": 0.933, "blue": 0.980}
PALE_RED      = {"red": 0.988, "green": 0.925, "blue": 0.925}
PALE_ORANGE   = {"red": 0.988, "green": 0.953, "blue": 0.906}

MUTED       = {"red": 0.545, "green": 0.573, "blue": 0.608}
SUBTITLE_C  = {"red": 0.702, "green": 0.718, "blue": 0.741}

BORDER_LIGHT = {"red": 0.933, "green": 0.937, "blue": 0.949}
BORDER_MED   = {"red": 0.820, "green": 0.827, "blue": 0.843}

# ── Helpers ──────────────────────────────────────────────────────────────────
def gr(sid, sr, er, sc, ec):
    return {"sheetId": sid, "startRowIndex": sr, "endRowIndex": er,
            "startColumnIndex": sc, "endColumnIndex": ec}

def rc(sid, sr, er, sc, ec, fmt, fields):
    return {"repeatCell": {"range": gr(sid, sr, er, sc, ec),
            "cell": {"userEnteredFormat": fmt}, "fields": fields}}

def rhs(sid, r0, r1, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": r0, "endIndex": r1},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def cws(sid, c0, c1, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": c0, "endIndex": c1},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def border_bottom(sid, sr, er, sc, ec, color=BORDER_LIGHT, style="SOLID", width=1):
    return {"updateBorders": {"range": gr(sid, sr, er, sc, ec),
            "bottom": {"style": style, "width": width, "color": color}}}

def border_top(sid, sr, er, sc, ec, color=BORDER_LIGHT, style="SOLID", width=1):
    return {"updateBorders": {"range": gr(sid, sr, er, sc, ec),
            "top": {"style": style, "width": width, "color": color}}}

def clear_borders(sid, sr, er, sc, ec):
    n = {"style": "NONE"}
    return {"updateBorders": {"range": gr(sid, sr, er, sc, ec),
            "top": n, "bottom": n, "left": n, "right": n,
            "innerHorizontal": n, "innerVertical": n}}

def hide_gridlines(sid):
    return {"updateSheetProperties": {
        "properties": {"sheetId": sid, "gridProperties": {"hideGridlines": True}},
        "fields": "gridProperties.hideGridlines"}}

def set_tab_color(sid, color):
    return {"updateSheetProperties": {
        "properties": {"sheetId": sid, "tabColor": color},
        "fields": "tabColor"}}

def freeze_rows(sid, count):
    return {"updateSheetProperties": {
        "properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": count}},
        "fields": "gridProperties.frozenRowCount"}}

def number_fmt(sid, sr, er, sc, ec, pattern):
    return {"repeatCell": {"range": gr(sid, sr, er, sc, ec),
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": pattern}}},
            "fields": "userEnteredFormat.numberFormat"}}

def pct_fmt(sid, sr, er, sc, ec):
    return {"repeatCell": {"range": gr(sid, sr, er, sc, ec),
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0%"}}},
            "fields": "userEnteredFormat.numberFormat"}}

F_BG = "userEnteredFormat.backgroundColor"
F_TF = "userEnteredFormat.textFormat"
F_AL = "userEnteredFormat.horizontalAlignment"
F_VA = "userEnteredFormat.verticalAlignment"
F_BG_TF = f"{F_BG},{F_TF}"
F_ALL = f"{F_BG},{F_TF},{F_AL},{F_VA}"


def execute_with_retry(service, reqs, label=""):
    """Execute batch requests with exponential backoff on 429s."""
    if not reqs:
        print(f"  {label}: No requests")
        return

    print(f"  {label}: {len(reqs)} requests...")
    delay = 5
    for attempt in range(5):
        try:
            service.spreadsheets().batchUpdate(
                spreadsheetId=MAP_ID,
                body={"requests": reqs}
            ).execute()
            print(f"    OK")
            return
        except Exception as e:
            err = str(e)
            if '429' in err:
                print(f"    Rate limited, waiting {delay}s (attempt {attempt+1}/5)...")
                time.sleep(delay)
                delay *= 2
            else:
                print(f"    ERROR: {err[:200]}")
                return
    print(f"    FAILED after 5 retries")


def read_all_tabs(service):
    """Read content and structure of all 6 tabs."""
    print("\n  READING ALL TABS...")
    meta = service.spreadsheets().get(spreadsheetId=MAP_ID, includeGridData=False).execute()

    tab_info = {}
    for sheet in meta['sheets']:
        p = sheet['properties']
        name = p['title']
        tab_info[name] = {
            'sheetId': p['sheetId'],
            'rows': p['gridProperties']['rowCount'],
            'cols': p['gridProperties']['columnCount'],
        }
        print(f"    {name}: sid={p['sheetId']}, {p['gridProperties']['rowCount']}r x {p['gridProperties']['columnCount']}c")

    tab_data = {}
    for name in tab_info:
        data = service.spreadsheets().values().get(
            spreadsheetId=MAP_ID,
            range=f"'{name}'!A1:AZ100",
            valueRenderOption="FORMATTED_VALUE"
        ).execute().get("values", [])
        tab_data[name] = data

        max_col = max((len(r) for r in data if r), default=0)
        max_row = max((i+1 for i, r in enumerate(data) if r), default=0)
        tab_info[name]['data_rows'] = max_row
        tab_info[name]['data_cols'] = max_col
        print(f"      Data: {max_row}r x {max_col}c")
        for i, row in enumerate(data[:4]):
            if row:
                print(f"      R{i+1}: {[str(c)[:25] for c in row[:5]]}")

    return tab_info, tab_data


def classify_row(val):
    """Classify a row by its first cell content."""
    v = val.strip().upper()
    if not v:
        return 'empty'

    # Section headers
    section_kw = ['KEY ASSUMPTION', 'PROJECTS', 'RETAINER', 'P&L', 'EXPENSES',
                  'MONTHLY BREAKDOWN', 'FIXED', 'VARIABLE', 'OVERHEAD',
                  'SERVICE', 'CATEGORY', 'TIER', 'PACKAGE', 'PRICING',
                  'DELIVERABLE', 'COGS', 'ARCHITECT', 'BUILDER', 'INTERIOR',
                  'EDITORIAL', 'STANDALONE', 'EXAMPLE', 'PIPELINE', 'SUMMARY']
    if any(kw in v for kw in section_kw) and 'TOTAL' not in v:
        # But not if it looks like a data label (has digits or $)
        if not any(c.isdigit() for c in v) or len(v) < 25:
            return 'section'

    # Quarter headers
    if any(q in v for q in ['Q1', 'Q2', 'Q3', 'Q4']) and len(v) < 30:
        return 'quarter'

    # Total rows
    if 'TOTAL' in v or 'ANNUAL' in v or 'GRAND' in v:
        if 'GRAND' in v or ('TOTAL' in v and 'PROJECT' not in v and 'RETAINER' not in v):
            return 'grand_total'
        return 'total'

    # Growth / YOY
    if 'YOY' in v or 'GROWTH' in v:
        return 'growth'

    # Percent rows
    if '% TO GOAL' in v or 'PERCENT' in v:
        return 'pct'

    # Cumulative
    if 'CUMUL' in v:
        return 'cumulative'

    return 'data'


def design_tab(sid, data, info, tab_name, accent=BLUE, total_color=BLUE, total_bg=TOTAL_BG,
               is_monthly=False, is_rocks=False):
    """
    Unified design function for any tab.
    Returns list of request batches (each batch is a list of requests).
    """
    NC = min(info['data_cols'], info['cols'])  # Never exceed grid
    NR = info['data_rows']
    TC = info['cols']  # Total columns in grid

    print(f"\n  {tab_name}: {NR} data rows x {NC} data cols (grid: {TC} cols)")

    # ── BATCH 1: Clear + base formatting ──
    b1 = []

    # Clear all formatting in data area + beyond
    b1.append(rc(sid, 0, min(NR+10, info['rows']), 0, TC, {"backgroundColor": WHITE}, F_BG))
    b1.append(clear_borders(sid, 0, min(NR+10, info['rows']), 0, TC))

    # Base font for entire sheet
    b1.append(rc(sid, 0, min(NR+10, info['rows']), 0, TC, {
        "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": DARK_TEXT},
        "verticalAlignment": "MIDDLE"
    }, f"{F_TF},{F_VA}"))

    # Column widths: gutter + labels + data
    b1.append(cws(sid, 0, 1, 20))   # Column A = gutter
    b1.append(cws(sid, 1, 2, 200))  # Column B = labels
    col_width = 75 if is_monthly else 100
    if NC > 2:
        b1.append(cws(sid, 2, NC, col_width))

    # Row heights: spacer/title/subtitle/spacer
    b1.append(rhs(sid, 0, 1, 8))    # spacer
    b1.append(rhs(sid, 1, 2, 44))   # title
    b1.append(rhs(sid, 2, 3, 22))   # subtitle
    b1.append(rhs(sid, 3, 4, 8))    # spacer

    # Title
    b1.append(rc(sid, 1, 2, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 20, "bold": True, "foregroundColor": CHARCOAL},
        "verticalAlignment": "MIDDLE"
    }, F_ALL))

    # Subtitle
    b1.append(rc(sid, 2, 3, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": SUBTITLE_C},
        "verticalAlignment": "TOP"
    }, F_ALL))

    # Set all data rows to 28px default
    if NR > 4:
        b1.append(rhs(sid, 4, NR, 28))

    # ── BATCH 2: Row-by-row formatting ──
    b2 = []

    # Detect header rows (month names or GOAL/ACT sub-headers)
    header_rows = []
    col_header_row = None

    for i, row in enumerate(data):
        if i < 4 or not row:
            continue
        row_text = ' '.join(str(c).upper() for c in row if c)

        # Monthly tracker: detect month header bars
        if is_monthly and ('JAN' in row_text and 'FEB' in row_text):
            header_rows.append(i)
            continue
        if is_monthly and ('GOAL' in row_text and 'ACT' in row_text and len(row) > 5):
            header_rows.append(i)
            continue

        # Rocks: detect column header rows
        if is_rocks and ('ROCK' in row_text and ('STATUS' in row_text or 'OWNER' in row_text)):
            header_rows.append(i)
            continue

        # Simple tabs: detect first column-header-like row
        if not is_monthly and not is_rocks and col_header_row is None and i >= 4:
            text_count = sum(1 for c in row if c and not str(c).startswith('$') and
                           not str(c).replace(',','').replace('.','').replace('-','').replace('$','').replace('%','').strip().isdigit())
            if text_count >= 2 and len(row) >= 2:
                val = str(row[0]).strip().upper()
                cls = classify_row(str(row[0]))
                if cls not in ['section', 'total', 'grand_total', 'data'] or text_count >= 3:
                    col_header_row = i
                    header_rows.append(i)

    if not header_rows and not is_monthly and not is_rocks:
        col_header_row = 4
        header_rows = [4]

    # Format header rows
    for hr in header_rows:
        b2.append(rhs(sid, hr, hr+1, 36))
        b2.append(rc(sid, hr, hr+1, 0, NC, {
            "backgroundColor": COL_HDR_BG,
            "textFormat": {"fontFamily": "Inter", "fontSize": 9, "bold": True, "foregroundColor": WHITE},
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE"
        }, F_ALL))
        b2.append(border_bottom(sid, hr, hr+1, 0, NC, COL_HDR_BG))

    # For monthly tracker with two header rows, second is smaller
    if is_monthly and len(header_rows) >= 2 and header_rows[1] == header_rows[0] + 1:
        b2.append(rhs(sid, header_rows[1], header_rows[1]+1, 28))
        b2.append(rc(sid, header_rows[1], header_rows[1]+1, 0, NC, {
            "backgroundColor": COL_HDR_BG,
            "textFormat": {"fontFamily": "Inter", "fontSize": 8, "bold": True, "foregroundColor": WHITE},
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE"
        }, F_ALL))

    # Process all other rows
    skip = set(header_rows + [0, 1, 2, 3])
    data_idx = 0

    for i in range(4, NR):
        if i in skip:
            continue
        if i >= len(data) or not data[i]:
            # Empty/spacer row
            b2.append(rhs(sid, i, i+1, 8))
            continue

        val = str(data[i][0]).strip() if data[i][0] else ""
        cls = classify_row(val)

        if cls == 'empty':
            b2.append(rhs(sid, i, i+1, 8))
            continue

        if cls == 'section':
            b2.append(rhs(sid, i, i+1, 32))
            b2.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": SECTION_BG,
                "textFormat": {"fontFamily": "Inter", "fontSize": 11, "bold": True, "foregroundColor": CHARCOAL},
                "verticalAlignment": "MIDDLE"
            }, F_ALL))
            if i > 4:
                b2.append(border_bottom(sid, i-1, i, 0, NC, BORDER_MED))
            continue

        if cls == 'quarter':
            b2.append(rhs(sid, i, i+1, 36))
            b2.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": CHARCOAL,
                "textFormat": {"fontFamily": "Inter", "fontSize": 12, "bold": True, "foregroundColor": WHITE},
                "verticalAlignment": "MIDDLE"
            }, F_ALL))
            continue

        if cls == 'grand_total':
            b2.append(rhs(sid, i, i+1, 32))
            b2.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": GRAND_BG,
                "textFormat": {"fontFamily": "Inter", "fontSize": 11, "bold": True, "foregroundColor": total_color},
                "verticalAlignment": "MIDDLE"
            }, F_ALL))
            b2.append(border_top(sid, i, i+1, 0, NC, accent, "SOLID_MEDIUM", 2))
            continue

        if cls == 'total':
            b2.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": total_bg,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "bold": True, "foregroundColor": total_color},
                "verticalAlignment": "MIDDLE"
            }, F_ALL))
            b2.append(border_top(sid, i, i+1, 0, NC, accent, "SOLID", 1))
            continue

        if cls == 'cumulative':
            b2.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": TOTAL_BG,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "bold": True, "foregroundColor": BLUE},
                "verticalAlignment": "MIDDLE"
            }, F_ALL))
            continue

        if cls == 'growth':
            b2.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": ZEBRA,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "bold": True, "foregroundColor": CHARCOAL},
                "verticalAlignment": "MIDDLE"
            }, F_ALL))
            continue

        if cls == 'pct':
            b2.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": PALE_BLUE,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "bold": True, "foregroundColor": BLUE},
                "verticalAlignment": "MIDDLE"
            }, F_ALL))
            b2.append(pct_fmt(sid, i, i+1, 2, NC))
            continue

        # Regular data row
        bg = ZEBRA if data_idx % 2 == 0 else WHITE
        data_idx += 1

        # Full row base
        b2.append(rc(sid, i, i+1, 0, NC, {
            "backgroundColor": bg,
            "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": DARK_TEXT},
            "verticalAlignment": "MIDDLE"
        }, F_ALL))

        # Numbers right-aligned (columns C onward)
        if NC > 2:
            b2.append(rc(sid, i, i+1, 2, NC, {
                "horizontalAlignment": "RIGHT"
            }, F_AL))

        # Monthly tracker: ACT columns get subtle blue tint
        if is_monthly and NC > 3:
            for c in range(2, NC, 2):  # Even-indexed data cols = ACT
                if c < NC:
                    b2.append(rc(sid, i, i+1, c, c+1, {
                        "backgroundColor": ACT_TINT if bg == WHITE else {"red": 0.961, "green": 0.965, "blue": 0.976}
                    }, F_BG))

        # Subtle bottom border
        b2.append(border_bottom(sid, i, i+1, 0, NC, BORDER_LIGHT))

        # Rocks: color status cells
        if is_rocks:
            for ci, cell in enumerate(data[i]):
                if ci >= NC:
                    break
                cv = str(cell).strip().upper() if cell else ""
                if cv in ['COMPLETE', 'DONE', 'ON TRACK']:
                    b2.append(rc(sid, i, i+1, ci, ci+1, {
                        "textFormat": {"fontFamily": "Inter", "fontSize": 10, "bold": True, "foregroundColor": GREEN}
                    }, F_TF))
                elif cv in ['IN PROGRESS', 'STARTED']:
                    b2.append(rc(sid, i, i+1, ci, ci+1, {
                        "textFormat": {"fontFamily": "Inter", "fontSize": 10, "bold": True, "foregroundColor": ORANGE}
                    }, F_TF))
                elif cv in ['AT RISK', 'BEHIND', 'NOT STARTED', 'BLOCKED']:
                    b2.append(rc(sid, i, i+1, ci, ci+1, {
                        "textFormat": {"fontFamily": "Inter", "fontSize": 10, "bold": True, "foregroundColor": RED}
                    }, F_TF))

    # ── BATCH 3: Final polish ──
    b3 = []

    # Freeze rows
    freeze_to = max(header_rows) + 1 if header_rows else 5
    b3.append(freeze_rows(sid, min(freeze_to, 8)))

    # Number format for data columns
    data_start = freeze_to if freeze_to < NR else 4
    if NC > 2 and NR > data_start:
        b3.append(number_fmt(sid, data_start, NR, 2, NC, "$#,##0"))

    # Rocks: wider label column
    if is_rocks:
        b3.append(cws(sid, 1, 2, 250))
        for c in range(2, min(NC, TC)):
            b3.append(cws(sid, c, c+1, 120))

    print(f"    Batches: {len(b1)}, {len(b2)}, {len(b3)} requests")
    return [b1, b2, b3]


def main():
    print("\n" + "=" * 70)
    print("  FINANCIAL MAP — PROFESSIONAL REDESIGN")
    print("=" * 70)

    service = get_sheets_service()
    tab_info, tab_data = read_all_tabs(service)

    print("\n" + "=" * 70)
    print("  APPLYING DESIGN")
    print("=" * 70)

    # ── Global: tab colors + gridlines ──
    global_reqs = []
    tab_colors = {
        'Dashboard': CHARCOAL, 'Monthly Tracker': BLUE, 'Project COGS': ORANGE,
        'Overhead': GREY_666, 'Pricing Guide': GREEN, 'Quarterly Rocks': PURPLE,
    }
    for name, info in tab_info.items():
        global_reqs.append(hide_gridlines(info['sheetId']))
        if name in tab_colors:
            global_reqs.append(set_tab_color(info['sheetId'], tab_colors[name]))

    execute_with_retry(service, global_reqs, "Global")
    time.sleep(3)

    # ── Tab configs ──
    configs = [
        ('Dashboard',       {'accent': BLUE, 'total_color': BLUE, 'total_bg': TOTAL_BG}),
        ('Monthly Tracker', {'accent': BLUE, 'total_color': GREEN, 'total_bg': TOTAL_BG, 'is_monthly': True}),
        ('Project COGS',    {'accent': ORANGE, 'total_color': ORANGE, 'total_bg': PALE_ORANGE}),
        ('Overhead',        {'accent': RED, 'total_color': RED, 'total_bg': PALE_RED}),
        ('Pricing Guide',   {'accent': GREEN, 'total_color': GREEN, 'total_bg': PALE_GREEN}),
        ('Quarterly Rocks', {'accent': PURPLE, 'total_color': PURPLE, 'total_bg': TOTAL_BG, 'is_rocks': True}),
    ]

    for tab_name, kwargs in configs:
        if tab_name not in tab_info:
            print(f"\n  SKIP: {tab_name} not found")
            continue

        batches = design_tab(
            tab_info[tab_name]['sheetId'],
            tab_data.get(tab_name, []),
            tab_info[tab_name],
            tab_name,
            **kwargs
        )

        for bi, batch in enumerate(batches):
            execute_with_retry(service, batch, f"{tab_name} batch {bi+1}")
            time.sleep(3)  # Respect rate limits between batches

    print("\n" + "=" * 70)
    print("  REDESIGN COMPLETE")
    print("=" * 70)
    print("""
  Applied:
  - Gridlines hidden, tab colors set
  - 20px left gutter, 8px spacer rows
  - Title: 20pt Inter bold #272c38
  - Subtitle: 10pt Inter #b3b7bd
  - Section headers: 11pt bold on #f0f1f3
  - Column headers: 9pt bold white on #272c38
  - Data rows: 28px, zebra #f8f9fa
  - Total rows: #f5f7ff + blue top border
  - Grand totals: #ebeefa + 2px blue border
  - Monthly Tracker: ACT columns subtle blue tint
  - Quarterly Rocks: status text coloring
  - No vertical borders, minimal horizontals
  - Currency: $#,##0 | Percentages: 0%
  - Frozen header rows, Inter font throughout
    """)


if __name__ == '__main__':
    main()
