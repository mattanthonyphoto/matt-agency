"""
Fix spacing for all 6 tabs of the Financial Map spreadsheet.
Reads current content, then applies spacious row heights, column widths,
inserts spacer rows between sections, and sets vertical alignment to MIDDLE.
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_sheets_service

MAP_ID = '1nrzAfXzRiFIQpa85one6iuMXASIBbgPrwDoI6TwH9KU'

WHITE = {"red": 1, "green": 1, "blue": 1}

# ── Helpers ──────────────────────────────────────────────────────────────────
def gr(sid, sr, er, sc, ec):
    return {"sheetId": sid, "startRowIndex": sr, "endRowIndex": er,
            "startColumnIndex": sc, "endColumnIndex": ec}

def rhs(sid, r0, r1, px):
    """Set row height."""
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": r0, "endIndex": r1},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def cws(sid, c0, c1, px):
    """Set column width."""
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": c0, "endIndex": c1},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def rc(sid, sr, er, sc, ec, fmt, fields):
    return {"repeatCell": {"range": gr(sid, sr, er, sc, ec),
            "cell": {"userEnteredFormat": fmt}, "fields": fields}}

def insert_rows(sid, row_idx, count=1):
    return {"insertDimension": {
        "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": row_idx, "endIndex": row_idx + count},
        "inheritFromBefore": False}}

def clear_borders(sid, sr, er, sc, ec):
    n = {"style": "NONE"}
    return {"updateBorders": {"range": gr(sid, sr, er, sc, ec),
            "top": n, "bottom": n, "left": n, "right": n,
            "innerHorizontal": n, "innerVertical": n}}

def execute_with_retry(service, reqs, label=""):
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
            return True
        except Exception as e:
            err = str(e)
            if '429' in err or 'Quota' in err:
                print(f"    Rate limited, waiting {delay}s (attempt {attempt+1}/5)...")
                time.sleep(delay)
                delay *= 2
            else:
                print(f"    ERROR: {err[:300]}")
                return False
    print(f"    FAILED after 5 retries")
    return False


# ── Read all tabs ────────────────────────────────────────────────────────────
def read_all_tabs(service):
    """Read content and grid data for all 6 tabs."""
    print("\n=== READING ALL TABS (with grid data) ===")

    # Get full spreadsheet with grid data
    meta = service.spreadsheets().get(
        spreadsheetId=MAP_ID,
        includeGridData=True
    ).execute()

    tabs = {}
    for sheet in meta['sheets']:
        p = sheet['properties']
        name = p['title']
        sid = p['sheetId']
        rows = p['gridProperties']['rowCount']
        cols = p['gridProperties']['columnCount']

        # Extract grid data
        grid_data = sheet.get('data', [{}])[0]
        row_metadata = grid_data.get('rowMetadata', [])
        col_metadata = grid_data.get('columnMetadata', [])
        row_data = grid_data.get('rowData', [])

        # Extract cell values
        cell_values = []
        for rd in row_data:
            row_vals = []
            for cell in rd.get('values', []):
                ev = cell.get('effectiveValue', {})
                fv = cell.get('formattedValue', '')
                row_vals.append(fv)
            cell_values.append(row_vals)

        # Extract row heights
        row_heights = [rm.get('pixelSize', 21) for rm in row_metadata]
        col_widths = [cm.get('pixelSize', 100) for cm in col_metadata]

        tabs[name] = {
            'sheetId': sid,
            'rows': rows,
            'cols': cols,
            'cell_values': cell_values,
            'row_heights': row_heights,
            'col_widths': col_widths,
            'row_data': row_data,  # Keep raw for formatting inspection
        }

        # Print summary
        data_rows = len(cell_values)
        max_col = max((len(r) for r in cell_values if r), default=0)
        print(f"\n  {name} (sid={sid}): {rows}r x {cols}c, data={data_rows}r x {max_col}c")
        print(f"    Row heights: {row_heights[:15]}...")
        print(f"    Col widths:  {col_widths[:15]}...")
        for i, row in enumerate(cell_values[:8]):
            if row and any(c for c in row):
                cells = [str(c)[:30] for c in row[:8]]
                print(f"    R{i+1}: {cells}")

    return tabs


# ── Classify rows ────────────────────────────────────────────────────────────
def classify_rows(cell_values, row_data):
    """Classify each row by type: title, subtitle, spacer, col_header, section_header, data, total, footer."""
    classifications = []
    for i, row in enumerate(cell_values):
        text = ' '.join(str(c) for c in row if c).strip()
        first_cell = str(row[0]).strip() if row and row[0] else ''

        # Check if row is empty
        if not text:
            classifications.append('spacer')
            continue

        # Check formatting from row_data
        bg_color = None
        text_fmt = None
        if i < len(row_data):
            rd = row_data[i]
            cells = rd.get('values', [])
            if cells:
                ef = cells[0].get('effectiveFormat', {})
                bg = ef.get('backgroundColor', {})
                bg_color = (bg.get('red', 1), bg.get('green', 1), bg.get('blue', 1))
                text_fmt = ef.get('textFormat', {})

        text_upper = text.upper()
        first_upper = first_cell.upper()

        # Title row: usually row 1-2, large bold text
        if i <= 1 and text_fmt and text_fmt.get('fontSize', 10) >= 16:
            classifications.append('title')
        elif i <= 2 and text_fmt and text_fmt.get('fontSize', 10) >= 11 and text_fmt.get('fontSize', 10) < 16:
            classifications.append('subtitle')
        # Column headers: dark background with white text
        elif bg_color and bg_color[0] < 0.3 and bg_color[1] < 0.3 and bg_color[2] < 0.4:
            classifications.append('col_header')
        # Section headers: check for known section names or bold text on tinted bg
        elif first_upper in ['PROJECTS', 'RETAINERS', 'TOTALS', 'PIPELINE', 'PROFIT-PER-PROJECT',
                             'REVENUE', 'COST OF GOODS SOLD', 'GROSS PROFIT', 'OVERHEAD',
                             'NET PROFIT', 'KEY ASSUMPTIONS', 'FIXED COSTS', 'VARIABLE COSTS',
                             'TOTAL OVERHEAD', 'PRICING', 'SERVICE TIERS', 'PROJECT TYPES',
                             'ROCK', 'Q1', 'Q2', 'Q3', 'Q4', 'QUARTERLY ROCKS',
                             'INCOME', 'EXPENSES', 'BUSINESS EXPENSES', 'TAX',
                             'PROJECT REVENUE', 'RETAINER REVENUE',
                             'KPI CARDS', 'SCORECARD', 'FINANCIAL SUMMARY']:
            classifications.append('section_header')
        elif bg_color and bg_color != (1, 1, 1) and text_fmt and text_fmt.get('bold', False) and not any(c in text for c in ['$', '%', ',']):
            # Bold text on non-white bg that doesn't look like data
            if bg_color[0] > 0.85 and bg_color[1] > 0.85 and bg_color[2] > 0.85:
                classifications.append('section_header')
            else:
                classifications.append('section_header')
        # Total rows
        elif 'TOTAL' in text_upper or 'GRAND' in text_upper or 'NET' in text_upper:
            if text_fmt and text_fmt.get('bold', False):
                classifications.append('total')
            else:
                classifications.append('data')
        else:
            classifications.append('data')

    return classifications


# ── Build spacing requests per tab ───────────────────────────────────────────

def build_dashboard_requests(tab):
    sid = tab['sheetId']
    rows = tab['rows']
    cols = tab['cols']
    cv = tab['cell_values']
    classifications = classify_rows(cv, tab['row_data'])

    reqs = []

    # Column widths
    col_specs = [
        (0, 1, 24),    # A: gutter
        (1, 2, 220),   # B: labels
        (2, 3, 120),   # C
        (3, 4, 120),   # D
        (4, 5, 120),   # E
        (5, 6, 120),   # F
    ]
    if cols > 6:
        col_specs.append((6, min(cols, 26), 24))  # Beyond F: narrow

    for c0, c1, px in col_specs:
        reqs.append(cws(sid, c0, c1, px))
        print(f"    Col {chr(65+c0)}-{chr(64+c1)}: {px}px")

    # Row heights based on classification
    for i, cls in enumerate(classifications):
        if i == 0:
            px = 12  # Top spacer
        elif cls == 'title':
            px = 48
        elif cls == 'subtitle':
            px = 28
        elif cls == 'col_header':
            px = 36
        elif cls == 'section_header':
            px = 34
        elif cls == 'total':
            px = 34
        elif cls == 'spacer':
            px = 14
        elif cls == 'data':
            px = 30
        else:
            px = 28
        reqs.append(rhs(sid, i, i+1, px))

    # Print row height summary
    for i, cls in enumerate(classifications[:20]):
        first_text = str(cv[i][0])[:25] if i < len(cv) and cv[i] and cv[i][0] else '(empty)'
        print(f"    Row {i+1} ({cls}): {first_text}")

    # Set vertical alignment MIDDLE for all content
    max_data_row = len(classifications)
    max_data_col = max((len(r) for r in cv if r), default=6)
    reqs.append(rc(sid, 0, max_data_row, 0, max_data_col,
        {"verticalAlignment": "MIDDLE"}, "userEnteredFormat.verticalAlignment"))

    # Set text wrapping to CLIP on data cells
    reqs.append(rc(sid, 0, max_data_row, 0, max_data_col,
        {"wrapStrategy": "CLIP"}, "userEnteredFormat.wrapStrategy"))

    # Clean spacer rows: white bg, no borders
    for i, cls in enumerate(classifications):
        if cls == 'spacer':
            reqs.append(rc(sid, i, i+1, 0, max_data_col,
                {"backgroundColor": WHITE}, "userEnteredFormat.backgroundColor"))
            reqs.append(clear_borders(sid, i, i+1, 0, max_data_col))

    return reqs


def build_monthly_tracker_requests(tab):
    sid = tab['sheetId']
    rows = tab['rows']
    cols = tab['cols']
    cv = tab['cell_values']
    classifications = classify_rows(cv, tab['row_data'])

    reqs = []

    # First understand the column layout
    print(f"    Analyzing column layout...")
    header_row = None
    for i, cls in enumerate(classifications):
        if cls == 'col_header':
            header_row = i
            break

    if header_row is not None and header_row < len(cv):
        hr = cv[header_row]
        print(f"    Header row {header_row+1}: {[str(c)[:15] for c in hr[:30]]}")

    # Column widths - Col A is gutter, B is labels, then month pairs
    reqs.append(cws(sid, 0, 1, 24))   # A: gutter
    reqs.append(cws(sid, 1, 2, 200))  # B: labels
    print(f"    Col A: 24px, Col B: 200px")

    # Determine how many data columns there are
    max_data_col = max((len(r) for r in cv if r), default=2)

    # Find the YR GOAL/YR ACT columns (usually the last 2 data cols)
    # Monthly columns are pairs: GOAL, ACT for each month (Jan-Dec = 24 cols)
    # Then YR GOAL, YR ACT
    # So: B=labels, C-Z = 24 month cols, AA-AB = yearly totals
    # That's col index 2 through max_data_col

    # Set month data columns (C onwards) to 80px each
    end_month_cols = min(max_data_col, 26)  # up to Z
    if end_month_cols > 2:
        reqs.append(cws(sid, 2, end_month_cols, 80))
        print(f"    Col C-{chr(64+end_month_cols)}: 80px each ({end_month_cols-2} cols)")

    # YR columns (last 2) to 90px
    if max_data_col > 26:
        reqs.append(cws(sid, 26, max_data_col, 90))
        print(f"    Col AA+: 90px ({max_data_col-26} cols)")

    # Beyond data: narrow
    if cols > max_data_col:
        reqs.append(cws(sid, max_data_col, min(cols, max_data_col + 10), 24))

    # Row heights
    for i, cls in enumerate(classifications):
        if i == 0:
            px = 12
        elif cls == 'title':
            px = 48
        elif cls == 'subtitle':
            px = 28
        elif cls == 'col_header':
            px = 36
        elif cls == 'section_header':
            px = 34
        elif cls == 'total':
            px = 34
        elif cls == 'spacer':
            px = 14
        elif cls == 'data':
            px = 30
        else:
            px = 28
        reqs.append(rhs(sid, i, i+1, px))

    for i, cls in enumerate(classifications[:25]):
        first_text = str(cv[i][0])[:25] if i < len(cv) and cv[i] and cv[i][0] else '(empty)'
        print(f"    Row {i+1} ({cls}): {first_text}")

    # Vertical alignment MIDDLE
    max_data_row = len(classifications)
    reqs.append(rc(sid, 0, max_data_row, 0, max_data_col,
        {"verticalAlignment": "MIDDLE"}, "userEnteredFormat.verticalAlignment"))
    reqs.append(rc(sid, 0, max_data_row, 0, max_data_col,
        {"wrapStrategy": "CLIP"}, "userEnteredFormat.wrapStrategy"))

    # Clean spacer rows
    for i, cls in enumerate(classifications):
        if cls == 'spacer':
            reqs.append(rc(sid, i, i+1, 0, max_data_col,
                {"backgroundColor": WHITE}, "userEnteredFormat.backgroundColor"))
            reqs.append(clear_borders(sid, i, i+1, 0, max_data_col))

    return reqs


def build_project_cogs_requests(tab):
    sid = tab['sheetId']
    rows = tab['rows']
    cols = tab['cols']
    cv = tab['cell_values']
    classifications = classify_rows(cv, tab['row_data'])

    reqs = []
    max_data_col = max((len(r) for r in cv if r), default=4)

    # Column widths
    reqs.append(cws(sid, 0, 1, 24))    # A: gutter
    reqs.append(cws(sid, 1, 2, 200))   # B: labels
    print(f"    Col A: 24px, Col B: 200px")
    if max_data_col > 2:
        reqs.append(cws(sid, 2, max_data_col, 110))
        print(f"    Col C-{chr(64+max_data_col)}: 110px each")
    if cols > max_data_col:
        reqs.append(cws(sid, max_data_col, min(cols, max_data_col + 10), 24))

    # Row heights
    for i, cls in enumerate(classifications):
        if i == 0:
            px = 12
        elif cls == 'title':
            px = 48
        elif cls == 'subtitle':
            px = 28
        elif cls == 'col_header':
            px = 36
        elif cls == 'section_header':
            px = 34
        elif cls == 'total':
            px = 34
        elif cls == 'spacer':
            px = 14
        elif cls == 'data':
            px = 30
        else:
            px = 28
        reqs.append(rhs(sid, i, i+1, px))

    for i, cls in enumerate(classifications[:20]):
        first_text = str(cv[i][0])[:25] if i < len(cv) and cv[i] and cv[i][0] else '(empty)'
        print(f"    Row {i+1} ({cls}): {first_text}")

    max_data_row = len(classifications)
    reqs.append(rc(sid, 0, max_data_row, 0, max_data_col,
        {"verticalAlignment": "MIDDLE"}, "userEnteredFormat.verticalAlignment"))
    reqs.append(rc(sid, 0, max_data_row, 0, max_data_col,
        {"wrapStrategy": "CLIP"}, "userEnteredFormat.wrapStrategy"))

    for i, cls in enumerate(classifications):
        if cls == 'spacer':
            reqs.append(rc(sid, i, i+1, 0, max_data_col,
                {"backgroundColor": WHITE}, "userEnteredFormat.backgroundColor"))
            reqs.append(clear_borders(sid, i, i+1, 0, max_data_col))

    return reqs


def build_overhead_requests(tab):
    sid = tab['sheetId']
    rows = tab['rows']
    cols = tab['cols']
    cv = tab['cell_values']
    classifications = classify_rows(cv, tab['row_data'])

    reqs = []
    max_data_col = max((len(r) for r in cv if r), default=4)

    # Column widths
    reqs.append(cws(sid, 0, 1, 24))    # A: gutter
    reqs.append(cws(sid, 1, 2, 250))   # B: expense names (long)
    print(f"    Col A: 24px, Col B: 250px")
    if max_data_col > 2:
        reqs.append(cws(sid, 2, max_data_col, 120))
        print(f"    Col C-{chr(64+max_data_col)}: 120px each")
    if cols > max_data_col:
        reqs.append(cws(sid, max_data_col, min(cols, max_data_col + 10), 24))

    # Row heights
    for i, cls in enumerate(classifications):
        if i == 0:
            px = 12
        elif cls == 'title':
            px = 48
        elif cls == 'subtitle':
            px = 28
        elif cls == 'col_header':
            px = 36
        elif cls == 'section_header':
            px = 34
        elif cls == 'total':
            px = 34
        elif cls == 'spacer':
            px = 14
        elif cls == 'data':
            px = 30
        else:
            px = 28
        reqs.append(rhs(sid, i, i+1, px))

    for i, cls in enumerate(classifications[:20]):
        first_text = str(cv[i][0])[:25] if i < len(cv) and cv[i] and cv[i][0] else '(empty)'
        print(f"    Row {i+1} ({cls}): {first_text}")

    max_data_row = len(classifications)
    reqs.append(rc(sid, 0, max_data_row, 0, max_data_col,
        {"verticalAlignment": "MIDDLE"}, "userEnteredFormat.verticalAlignment"))
    reqs.append(rc(sid, 0, max_data_row, 0, max_data_col,
        {"wrapStrategy": "CLIP"}, "userEnteredFormat.wrapStrategy"))

    for i, cls in enumerate(classifications):
        if cls == 'spacer':
            reqs.append(rc(sid, i, i+1, 0, max_data_col,
                {"backgroundColor": WHITE}, "userEnteredFormat.backgroundColor"))
            reqs.append(clear_borders(sid, i, i+1, 0, max_data_col))

    return reqs


def build_pricing_guide_requests(tab):
    sid = tab['sheetId']
    rows = tab['rows']
    cols = tab['cols']
    cv = tab['cell_values']
    classifications = classify_rows(cv, tab['row_data'])

    reqs = []
    max_data_col = max((len(r) for r in cv if r), default=6)

    # Column widths - need to figure out which are description cols
    reqs.append(cws(sid, 0, 1, 24))    # A: gutter
    print(f"    Col A: 24px")

    # Check header row for column names
    header_row = None
    for i, cls in enumerate(classifications):
        if cls == 'col_header':
            header_row = i
            break

    if header_row is not None and header_row < len(cv):
        headers = cv[header_row]
        for ci, h in enumerate(headers[:max_data_col]):
            h_str = str(h).upper()
            if ci == 0:
                continue  # already set gutter
            elif ci == 1:
                # Usually a label/name column
                reqs.append(cws(sid, ci, ci+1, 200))
                print(f"    Col {chr(65+ci)}: 200px (label)")
            elif 'DESC' in h_str or 'NOTE' in h_str or 'DETAIL' in h_str:
                reqs.append(cws(sid, ci, ci+1, 250))
                print(f"    Col {chr(65+ci)}: 250px (description)")
            else:
                reqs.append(cws(sid, ci, ci+1, 120))
                print(f"    Col {chr(65+ci)}: 120px")
    else:
        # Fallback: B=200, rest=120
        reqs.append(cws(sid, 1, 2, 200))
        if max_data_col > 2:
            reqs.append(cws(sid, 2, max_data_col, 120))
        print(f"    Col B: 200px, C+: 120px")

    if cols > max_data_col:
        reqs.append(cws(sid, max_data_col, min(cols, max_data_col + 10), 24))

    # Row heights
    for i, cls in enumerate(classifications):
        if i == 0:
            px = 12
        elif cls == 'title':
            px = 48
        elif cls == 'subtitle':
            px = 28
        elif cls == 'col_header':
            px = 36
        elif cls == 'section_header':
            px = 34
        elif cls == 'total':
            px = 34
        elif cls == 'spacer':
            px = 14
        elif cls == 'data':
            px = 30
        else:
            px = 28
        reqs.append(rhs(sid, i, i+1, px))

    for i, cls in enumerate(classifications[:20]):
        first_text = str(cv[i][0])[:25] if i < len(cv) and cv[i] and cv[i][0] else '(empty)'
        print(f"    Row {i+1} ({cls}): {first_text}")

    max_data_row = len(classifications)
    reqs.append(rc(sid, 0, max_data_row, 0, max_data_col,
        {"verticalAlignment": "MIDDLE"}, "userEnteredFormat.verticalAlignment"))
    reqs.append(rc(sid, 0, max_data_row, 0, max_data_col,
        {"wrapStrategy": "CLIP"}, "userEnteredFormat.wrapStrategy"))

    for i, cls in enumerate(classifications):
        if cls == 'spacer':
            reqs.append(rc(sid, i, i+1, 0, max_data_col,
                {"backgroundColor": WHITE}, "userEnteredFormat.backgroundColor"))
            reqs.append(clear_borders(sid, i, i+1, 0, max_data_col))

    return reqs


def build_quarterly_rocks_requests(tab):
    sid = tab['sheetId']
    rows = tab['rows']
    cols = tab['cols']
    cv = tab['cell_values']
    classifications = classify_rows(cv, tab['row_data'])

    reqs = []
    max_data_col = max((len(r) for r in cv if r), default=6)

    # Column widths
    reqs.append(cws(sid, 0, 1, 24))    # A: gutter
    reqs.append(cws(sid, 1, 2, 300))   # B: rock description (long)
    print(f"    Col A: 24px, Col B: 300px")
    if max_data_col > 2:
        reqs.append(cws(sid, 2, max_data_col, 110))
        print(f"    Col C-{chr(64+max_data_col)}: 110px each")
    if cols > max_data_col:
        reqs.append(cws(sid, max_data_col, min(cols, max_data_col + 10), 24))

    # Row heights
    for i, cls in enumerate(classifications):
        if i == 0:
            px = 12
        elif cls == 'title':
            px = 48
        elif cls == 'subtitle':
            px = 28
        elif cls == 'col_header':
            px = 36
        elif cls == 'section_header':
            px = 34
        elif cls == 'total':
            px = 34
        elif cls == 'spacer':
            px = 14
        elif cls == 'data':
            px = 30
        else:
            px = 28
        reqs.append(rhs(sid, i, i+1, px))

    for i, cls in enumerate(classifications[:20]):
        first_text = str(cv[i][0])[:25] if i < len(cv) and cv[i] and cv[i][0] else '(empty)'
        print(f"    Row {i+1} ({cls}): {first_text}")

    max_data_row = len(classifications)
    reqs.append(rc(sid, 0, max_data_row, 0, max_data_col,
        {"verticalAlignment": "MIDDLE"}, "userEnteredFormat.verticalAlignment"))
    reqs.append(rc(sid, 0, max_data_row, 0, max_data_col,
        {"wrapStrategy": "CLIP"}, "userEnteredFormat.wrapStrategy"))

    for i, cls in enumerate(classifications):
        if cls == 'spacer':
            reqs.append(rc(sid, i, i+1, 0, max_data_col,
                {"backgroundColor": WHITE}, "userEnteredFormat.backgroundColor"))
            reqs.append(clear_borders(sid, i, i+1, 0, max_data_col))

    return reqs


# ── Identify where spacer rows need inserting ────────────────────────────────
def find_missing_spacers(classifications, cell_values):
    """Find transitions between sections that lack a spacer row.
    Returns list of row indices (0-based) where a spacer should be inserted.
    We process bottom-to-top so insertions don't shift later indices."""

    insert_points = []

    for i in range(1, len(classifications)):
        prev = classifications[i-1]
        curr = classifications[i]

        # Transitions that need a spacer
        needs_spacer = False

        # After title/subtitle block, before col_header or section_header
        if prev in ('title', 'subtitle') and curr in ('col_header', 'section_header', 'data'):
            needs_spacer = True
        # Between section_header and previous section's data/total
        if prev in ('data', 'total') and curr in ('section_header',):
            needs_spacer = True
        # After a total row, before next section
        if prev == 'total' and curr in ('section_header', 'col_header', 'data'):
            needs_spacer = True

        if needs_spacer:
            # Check if there's already a spacer nearby (within 1 row)
            already_has = False
            if i >= 1 and classifications[i-1] == 'spacer':
                already_has = True
            if i < len(classifications) - 1 and classifications[i] == 'spacer':
                already_has = True

            if not already_has:
                insert_points.append(i)

    # Return in reverse order so we can insert bottom-to-top
    return sorted(insert_points, reverse=True)


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("FINANCIAL MAP — SPACING FIX")
    print("=" * 60)

    service = get_sheets_service()

    # Step 1: Read all tabs
    tabs = read_all_tabs(service)

    # Step 2: Insert missing spacer rows first (this changes row indices)
    print("\n\n=== STEP 2: INSERT MISSING SPACER ROWS ===")

    for tab_name, tab in tabs.items():
        cv = tab['cell_values']
        classifications = classify_rows(cv, tab['row_data'])
        missing = find_missing_spacers(classifications, cv)

        if missing:
            print(f"\n  {tab_name}: Inserting {len(missing)} spacer rows at indices: {[m+1 for m in missing]}")
            insert_reqs = []
            for idx in missing:  # already reverse sorted
                insert_reqs.append(insert_rows(tab['sheetId'], idx, 1))
            execute_with_retry(service, insert_reqs, f"{tab_name} inserts")
            time.sleep(2)  # Brief pause after inserts
        else:
            print(f"\n  {tab_name}: No spacer rows needed")

    # Step 3: Re-read all tabs after inserts
    print("\n\n=== STEP 3: RE-READ TABS AFTER INSERTS ===")
    tabs = read_all_tabs(service)

    # Step 4: Apply spacing to each tab
    print("\n\n=== STEP 4: APPLY SPACING ===")

    tab_builders = {
        'Dashboard': build_dashboard_requests,
        'Monthly Tracker': build_monthly_tracker_requests,
        'Project COGS': build_project_cogs_requests,
        'Overhead': build_overhead_requests,
        'Pricing Guide': build_pricing_guide_requests,
        'Quarterly Rocks': build_quarterly_rocks_requests,
    }

    for tab_name, builder in tab_builders.items():
        if tab_name not in tabs:
            print(f"\n  WARNING: Tab '{tab_name}' not found, skipping")
            continue

        print(f"\n--- {tab_name} ---")
        reqs = builder(tabs[tab_name])
        execute_with_retry(service, reqs, f"{tab_name} spacing")
        time.sleep(3)  # Pause between tabs to avoid rate limits

    print("\n\n" + "=" * 60)
    print("DONE — All 6 tabs updated with improved spacing")
    print("=" * 60)


if __name__ == "__main__":
    main()
