"""
Diagnose dark formatting artifacts on the Financial Map Dashboard tab.
Reads full grid data and reports any cells with dark backgrounds or borders
beyond the expected data area.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_sheets_service

SHEET_ID = '1nrzAfXzRiFIQpa85one6iuMXASIBbgPrwDoI6TwH9KU'

def color_to_hex(c):
    """Convert API color dict to hex string."""
    if not c:
        return None
    r = int(c.get('red', 0) * 255)
    g = int(c.get('green', 0) * 255)
    b = int(c.get('blue', 0) * 255)
    return f"#{r:02x}{g:02x}{b:02x}"

def is_dark(c):
    """Check if a color is dark (luminance < 0.3)."""
    if not c:
        return False
    r = c.get('red', 0)
    g = c.get('green', 0)
    b = c.get('blue', 0)
    # If all zeros and no keys, it's black by default
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return lum < 0.35

def col_letter(idx):
    """Convert 0-based column index to letter."""
    result = ""
    idx += 1
    while idx > 0:
        idx -= 1
        result = chr(65 + idx % 26) + result
        idx //= 26
    return result

def main():
    service = get_sheets_service()

    # First, get sheet metadata to find Dashboard tab's sheetId
    meta = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    dashboard_sheet = None
    for s in meta['sheets']:
        props = s['properties']
        print(f"  Tab: {props['title']} (id={props['sheetId']}, "
              f"rows={props.get('gridProperties',{}).get('rowCount','?')}, "
              f"cols={props.get('gridProperties',{}).get('columnCount','?')})")
        if props['title'].lower() == 'dashboard':
            dashboard_sheet = props

    if not dashboard_sheet:
        print("ERROR: No 'Dashboard' tab found!")
        return

    sheet_id = dashboard_sheet['sheetId']
    total_rows = dashboard_sheet['gridProperties']['rowCount']
    total_cols = dashboard_sheet['gridProperties']['columnCount']
    print(f"\nDashboard: {total_rows} rows x {total_cols} cols (sheetId={sheet_id})")

    # Read grid data for the full sheet
    # Use ranges to get all data including formatting
    end_col = col_letter(min(total_cols - 1, 51))  # up to AZ
    range_str = f"Dashboard!A1:{end_col}{min(total_rows, 200)}"
    print(f"Reading range: {range_str}")

    result = service.spreadsheets().get(
        spreadsheetId=SHEET_ID,
        ranges=[range_str],
        includeGridData=True
    ).execute()

    grid_data = result['sheets'][0]['data'][0]

    dark_cells = []
    dark_border_cells = []
    all_formatted = []

    for ri, row in enumerate(grid_data.get('rowData', [])):
        for ci, cell in enumerate(row.get('values', [])):
            fmt = cell.get('userEnteredFormat', {}) or cell.get('effectiveFormat', {})
            if not fmt:
                continue

            # Check background color
            bg = fmt.get('backgroundColor') or fmt.get('backgroundColorStyle', {}).get('rgbColor')
            if bg and is_dark(bg):
                val = cell.get('userEnteredValue', cell.get('effectiveValue', {}))
                val_str = str(val) if val else ""
                hex_color = color_to_hex(bg)
                dark_cells.append({
                    'row': ri + 1,
                    'col': col_letter(ci),
                    'col_idx': ci,
                    'color': hex_color,
                    'value': val_str[:50]
                })

            # Check borders for dark colors
            borders = fmt.get('borders', {})
            for side in ['top', 'bottom', 'left', 'right']:
                border = borders.get(side, {})
                bc = border.get('color') or border.get('colorStyle', {}).get('rgbColor')
                if bc and is_dark(bc) and border.get('style', 'NONE') != 'NONE':
                    dark_border_cells.append({
                        'row': ri + 1,
                        'col': col_letter(ci),
                        'col_idx': ci,
                        'side': side,
                        'color': color_to_hex(bc),
                        'style': border.get('style', '?')
                    })

    # Report findings
    print(f"\n{'='*70}")
    print(f"DARK BACKGROUND CELLS: {len(dark_cells)}")
    print(f"{'='*70}")

    # Group by column
    by_col = {}
    for c in dark_cells:
        by_col.setdefault(c['col'], []).append(c)

    for col in sorted(by_col.keys(), key=lambda x: (len(x), x)):
        cells = by_col[col]
        rows = [c['row'] for c in cells]
        color = cells[0]['color']
        has_value = any(c['value'] and c['value'] != '{}' for c in cells)
        print(f"  Column {col} (idx {cells[0]['col_idx']}): {len(cells)} dark cells, "
              f"rows {min(rows)}-{max(rows)}, color={color}, has_values={has_value}")
        # Show a sample
        for c in cells[:3]:
            print(f"    Row {c['row']}: bg={c['color']} val={c['value']}")
        if len(cells) > 3:
            print(f"    ... and {len(cells)-3} more")

    print(f"\n{'='*70}")
    print(f"DARK BORDER CELLS: {len(dark_border_cells)}")
    print(f"{'='*70}")

    # Group border cells by column
    border_by_col = {}
    for c in dark_border_cells:
        border_by_col.setdefault(c['col'], []).append(c)

    for col in sorted(border_by_col.keys(), key=lambda x: (len(x), x)):
        cells = border_by_col[col]
        rows = sorted(set(c['row'] for c in cells))
        print(f"  Column {col} (idx {cells[0]['col_idx']}): {len(cells)} dark borders, "
              f"rows {min(rows)}-{max(rows)}")

    # Identify columns beyond expected data area (F = col 5) that have dark formatting
    print(f"\n{'='*70}")
    print("COLUMNS BEYOND F (col index > 5) WITH DARK FORMATTING:")
    print(f"{'='*70}")

    problem_cols = set()
    for c in dark_cells:
        if c['col_idx'] > 5:  # Beyond column F
            has_val = c['value'] and c['value'] != '{}'
            if not has_val:
                problem_cols.add(c['col_idx'])
                print(f"  PROBLEM: {c['col']}{c['row']} - dark bg {c['color']} (empty cell)")

    for c in dark_border_cells:
        if c['col_idx'] > 5:
            problem_cols.add(c['col_idx'])

    if problem_cols:
        print(f"\nProblem columns (0-indexed): {sorted(problem_cols)}")
        print(f"Problem columns (letters): {[col_letter(i) for i in sorted(problem_cols)]}")
    else:
        print("  None found beyond column F")

    # Also check: what's the rightmost column with ANY content?
    max_content_col = 0
    for ri, row in enumerate(grid_data.get('rowData', [])):
        for ci, cell in enumerate(row.get('values', [])):
            val = cell.get('userEnteredValue') or cell.get('effectiveValue')
            if val and str(val) != '{}':
                max_content_col = max(max_content_col, ci)

    print(f"\nRightmost column with actual content: {col_letter(max_content_col)} (index {max_content_col})")
    print(f"Total grid columns: {total_cols}")

    # Save full findings for the fix script
    findings = {
        'sheet_id': sheet_id,
        'total_rows': total_rows,
        'total_cols': total_cols,
        'max_content_col': max_content_col,
        'dark_cells': dark_cells,
        'dark_border_cells': dark_border_cells,
        'problem_cols': sorted(problem_cols)
    }

    findings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  '.tmp', 'dashboard_dark_findings.json')
    os.makedirs(os.path.dirname(findings_path), exist_ok=True)
    with open(findings_path, 'w') as f:
        json.dump(findings, f, indent=2)
    print(f"\nFindings saved to {findings_path}")

if __name__ == '__main__':
    main()
