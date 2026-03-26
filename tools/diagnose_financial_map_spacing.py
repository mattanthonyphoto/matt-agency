"""
Full diagnostic of ALL 6 tabs on the Financial Map spreadsheet.
Prints row heights, column widths, cell contents, backgrounds, merges, freezes, gridlines, tab colors.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_sheets_service

MAP_ID = '1nrzAfXzRiFIQpa85one6iuMXASIBbgPrwDoI6TwH9KU'

def col_letter(idx):
    """Convert 0-based column index to letter(s)."""
    result = ""
    while True:
        result = chr(65 + idx % 26) + result
        idx = idx // 26 - 1
        if idx < 0:
            break
    return result

def color_str(c):
    """Format a color object as hex-ish string."""
    if not c:
        return "none"
    r = int(c.get("red", 0) * 255)
    g = int(c.get("green", 0) * 255)
    b = int(c.get("blue", 0) * 255)
    a = c.get("alpha", 1)
    return f"#{r:02x}{g:02x}{b:02x}"

def get_cell_value(cell):
    """Extract display value from cell."""
    if not cell:
        return ""
    ev = cell.get("effectiveValue", {})
    fv = cell.get("formattedValue", "")
    if fv:
        return fv[:50]
    if ev:
        for k in ("stringValue", "numberValue", "boolValue", "formulaValue"):
            if k in ev:
                return str(ev[k])[:50]
    return ""

def get_cell_bg(cell):
    """Get background color of cell."""
    if not cell:
        return "default"
    fmt = cell.get("effectiveFormat", {})
    bg = fmt.get("backgroundColor", fmt.get("backgroundColorStyle", {}).get("rgbColor", None))
    if bg:
        return color_str(bg)
    return "default"

def get_cell_valign(cell):
    if not cell:
        return ""
    fmt = cell.get("effectiveFormat", {})
    return fmt.get("verticalAlignment", "")

def main():
    service = get_sheets_service()

    print("Fetching spreadsheet with full grid data...")
    ss = service.spreadsheets().get(
        spreadsheetId=MAP_ID,
        includeGridData=True
    ).execute()

    sheets = ss.get("sheets", [])
    print(f"Found {len(sheets)} tabs\n")

    for sheet in sheets:
        props = sheet.get("properties", {})
        title = props.get("title", "???")
        sid = props.get("sheetId", 0)
        grid_props = props.get("gridProperties", {})
        tab_color = props.get("tabColor", props.get("tabColorStyle", {}).get("rgbColor", None))

        frozen_rows = grid_props.get("frozenRowCount", 0)
        frozen_cols = grid_props.get("frozenColumnCount", 0)
        hide_gridlines = grid_props.get("hideGridlines", False)
        row_count = grid_props.get("rowCount", 0)
        col_count = grid_props.get("columnCount", 0)

        print("=" * 90)
        print(f"TAB: {title} (sheetId={sid})")
        print(f"  Grid size: {row_count} rows x {col_count} cols")
        print(f"  Frozen rows: {frozen_rows}, Frozen cols: {frozen_cols}")
        print(f"  Gridlines hidden: {hide_gridlines}")
        print(f"  Tab color: {color_str(tab_color) if tab_color else 'none'}")

        # Merges
        merges = sheet.get("merges", [])
        if merges:
            print(f"  Merged ranges ({len(merges)}):")
            for m in merges:
                sr = m.get("startRowIndex", 0)
                er = m.get("endRowIndex", 0)
                sc = m.get("startColumnIndex", 0)
                ec = m.get("endColumnIndex", 0)
                print(f"    {col_letter(sc)}{sr+1}:{col_letter(ec-1)}{er} (rows {sr}-{er-1}, cols {sc}-{ec-1})")
        else:
            print("  No merged ranges")

        # Grid data
        grid_data_list = sheet.get("data", [])
        if not grid_data_list:
            print("  NO GRID DATA")
            continue

        gd = grid_data_list[0]
        row_data = gd.get("rowData", [])
        row_metadata = gd.get("rowMetadata", [])
        col_metadata = gd.get("columnMetadata", [])

        # Find last row with content
        last_content_row = 0
        for ri, rd in enumerate(row_data):
            cells = rd.get("values", [])
            for cell in cells:
                if get_cell_value(cell):
                    last_content_row = ri
                    break

        # Find last column with content
        last_content_col = 0
        for rd in row_data:
            cells = rd.get("values", [])
            for ci, cell in enumerate(cells):
                if get_cell_value(cell):
                    if ci > last_content_col:
                        last_content_col = ci

        diag_rows = min(last_content_row + 11, len(row_metadata))
        diag_cols = min(last_content_col + 6, len(col_metadata))

        print(f"\n  Last content row: {last_content_row + 1}, Last content col: {col_letter(last_content_col)}")
        print(f"  Diagnosing rows 1-{diag_rows}, cols A-{col_letter(diag_cols - 1)}")

        # Column widths
        print(f"\n  COLUMN WIDTHS:")
        for ci in range(diag_cols):
            if ci < len(col_metadata):
                cm = col_metadata[ci]
                px = cm.get("pixelSize", "?")
                hidden = cm.get("hiddenByUser", False)
                print(f"    {col_letter(ci)}: {px}px{' (HIDDEN)' if hidden else ''}")

        # Row details
        print(f"\n  ROW DETAILS:")
        for ri in range(diag_rows):
            # Row height
            if ri < len(row_metadata):
                rm = row_metadata[ri]
                height = rm.get("pixelSize", "?")
                hidden = rm.get("hiddenByUser", False)
            else:
                height = "?"
                hidden = False

            # Cell contents
            cells_str = []
            if ri < len(row_data):
                cells = row_data[ri].get("values", [])
                for ci in range(diag_cols):
                    if ci < len(cells):
                        val = get_cell_value(cells[ci])
                        bg = get_cell_bg(cells[ci])
                        if val or bg != "#ffffff":
                            cells_str.append(f"{col_letter(ci)}={val!r} bg={bg}")
                    # Skip empty white cells to keep output readable

            hidden_tag = " [HIDDEN]" if hidden else ""
            cells_info = " | ".join(cells_str) if cells_str else "(empty/white)"
            print(f"    Row {ri+1:3d}: {height:4}px{hidden_tag} — {cells_info}")

        print()

if __name__ == "__main__":
    main()
