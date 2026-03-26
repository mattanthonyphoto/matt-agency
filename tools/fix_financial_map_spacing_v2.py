"""
Fix spacing issues on all 6 tabs of the Financial Map spreadsheet.
Based on diagnostic findings:

Dashboard (378592626):
  - Col A = 251px (too wide, should match label column ~200px or less)
  - Frozen rows = 8 (freezes too far down; should freeze through headers only ~3)
  - Row heights mostly fine but need standardization

Monthly Tracker (845249983):
  - Rows 1-3 all 59px (WAY too tall — title should be 44px, subtitle 24px, spacer 12px)
  - Col A = 202px (a bit wide, bring to 180px)
  - Frozen rows = 7 (ok for this tab's layout, adjust to row 6 after spacer)

Project COGS (865779075):
  - Content in col A (no gutter). Structure is fine but col A = 24px is too narrow for labels.
  - Widen col A to hold labels properly (~200px)
  - Frozen rows = 8 (too many, should be ~4)

Overhead (7683076):
  - Col A = 24px but has long labels like "Paid Ads (Google/Meta)" — way too narrow
  - Widen A to ~250px for labels
  - Frozen rows = 6 (too many, ~3 is better)

Pricing Guide (655418673):
  - Col A = 24px but has labels — too narrow
  - Widen A to ~200px
  - Frozen rows = 7 (too many, ~4 is better)

Quarterly Rocks (1620953837):
  - Col A = 24px but has "Q1", "Q2" etc — too narrow
  - Widen A to ~50px (short labels)
  - Frozen rows = 5 (too many, ~3 is better)

Global fixes:
  - Standardize row heights: title 44px, subtitle 24px, headers 34px,
    section labels 32px, data 28px, spacers 12px, totals 32px
  - Remove consecutive spacer rows (keep max 1)
  - Vertical align everything MIDDLE
  - Ensure no content bleeds past data area
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_sheets_service

MAP_ID = '1nrzAfXzRiFIQpa85one6iuMXASIBbgPrwDoI6TwH9KU'

# ── Helpers ──────────────────────────────────────────────────────────────────
def gr(sid, sr, er, sc, ec):
    return {"sheetId": sid, "startRowIndex": sr, "endRowIndex": er,
            "startColumnIndex": sc, "endColumnIndex": ec}

def rhs(sid, r0, r1, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": r0, "endIndex": r1},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def cws(sid, c0, c1, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": c0, "endIndex": c1},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}

def valign_middle(sid, sr, er, sc, ec):
    return {"repeatCell": {
        "range": gr(sid, sr, er, sc, ec),
        "cell": {"userEnteredFormat": {"verticalAlignment": "MIDDLE"}},
        "fields": "userEnteredFormat.verticalAlignment"}}

def freeze(sid, rows=0, cols=0):
    props = {}
    fields = []
    if rows is not None:
        props["frozenRowCount"] = rows
        fields.append("gridProperties.frozenRowCount")
    if cols is not None:
        props["frozenColumnCount"] = cols
        fields.append("gridProperties.frozenColumnCount")
    return {"updateSheetProperties": {
        "properties": {"sheetId": sid, "gridProperties": props},
        "fields": ",".join(fields)}}

def execute_batch(service, reqs, label=""):
    if not reqs:
        print(f"  {label}: No requests")
        return True
    print(f"  {label}: {len(reqs)} requests...")
    delay = 5
    for attempt in range(5):
        try:
            service.spreadsheets().batchUpdate(
                spreadsheetId=MAP_ID,
                body={"requests": reqs}
            ).execute()
            print(f"    Done")
            return True
        except Exception as e:
            err = str(e)
            if '429' in err or 'Quota' in err:
                print(f"    Rate limited, waiting {delay}s...")
                time.sleep(delay)
                delay *= 2
            else:
                print(f"    ERROR: {err[:400]}")
                return False
    return False


def get_cell_value(cell):
    if not cell:
        return ""
    fv = cell.get("formattedValue", "")
    if fv:
        return fv
    ev = cell.get("effectiveValue", {})
    for k in ("stringValue", "numberValue", "boolValue"):
        if k in ev:
            return str(ev[k])
    return ""


def main():
    service = get_sheets_service()

    # Read full spreadsheet for analysis
    print("Reading spreadsheet...")
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
        row_count = grid_props.get("rowCount", 0)
        col_count = grid_props.get("columnCount", 0)

        gd = sheet.get("data", [{}])[0]
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

        print(f"=== Fixing: {title} (sid={sid}) ===")
        print(f"  Content: rows 0-{last_content_row}, cols 0-{last_content_col}")

        reqs = []

        # ── Classify each row ──
        # Look at row content to determine type
        for ri in range(last_content_row + 1):
            if ri >= len(row_data):
                break
            cells = row_data[ri].get("values", [])

            # Get all cell values for this row
            vals = []
            for ci, cell in enumerate(cells):
                vals.append(get_cell_value(cell))

            # Check if row is empty
            all_empty = all(not v.strip() for v in vals)
            first_val = vals[0].strip() if vals else ""

            # Current height
            current_height = row_metadata[ri].get("pixelSize", 21) if ri < len(row_metadata) else 21

            # Determine target height based on content
            target_height = None

            if all_empty:
                # Spacer row — should be 12px
                target_height = 12
            elif ri == 0:
                # Title row — 44px
                target_height = 44
            elif ri == 1 and title in ["Dashboard", "Monthly Tracker", "Project COGS", "Pricing Guide"]:
                # Subtitle row — 24px
                target_height = 24

            # Skip specific classification for data rows — we'll handle by tab below

            if target_height and target_height != current_height:
                reqs.append(rhs(sid, ri, ri + 1, target_height))

        # ── Tab-specific fixes ──
        if title == "Dashboard":
            # Col A = 251px → 220px (it holds labels, keep readable)
            reqs.append(cws(sid, 0, 1, 220))
            # Col B-F are data columns at 120px — good
            # Cols G-K are 24px padding — good, but make them match
            for ci in range(last_content_col + 1, min(last_content_col + 6, col_count)):
                reqs.append(cws(sid, ci, ci + 1, 20))

            # Freeze: title + subtitle + spacer + assumptions header = row 4
            reqs.append(freeze(sid, rows=3))

            # Row heights for data area
            # Row 0 = title (44px, handled above)
            # Row 1 = subtitle (24px, handled above)
            # Row 2 = spacer (12px, handled above)
            # Row 3 = section label "KEY ASSUMPTIONS" → 32px
            reqs.append(rhs(sid, 3, 4, 32))
            # Rows 4-10 = assumption data → 28px
            for r in range(4, 11):
                reqs.append(rhs(sid, r, r + 1, 28))
            # Row 11 = "Revenue Stream" header row → 34px
            reqs.append(rhs(sid, 11, 12, 34))
            # Rows 12-17 = revenue data → 28px
            for r in range(12, 18):
                reqs.append(rhs(sid, r, r + 1, 28))
            # Row 17 = "Total Project Revenue" → 32px (total row)
            reqs.append(rhs(sid, 17, 18, 32))
            # Row 19 = "RETAINER REVENUE" section → 32px
            reqs.append(rhs(sid, 19, 20, 32))
            # Rows 20-24 = retainer data → 28px
            for r in range(20, 25):
                reqs.append(rhs(sid, r, r + 1, 28))
            # Row 25 = "TOTAL 2026 REVENUE" → 32px
            reqs.append(rhs(sid, 25, 26, 32))
            # Row 27-28 = YOY/% → 28px
            reqs.append(rhs(sid, 27, 29, 28))
            # Row 30 = "PROFIT & LOSS" section → 32px
            reqs.append(rhs(sid, 30, 31, 32))
            # Row 31 = "Total Revenue" → 32px
            reqs.append(rhs(sid, 31, 32, 32))
            # Rows 33-44 = P&L data → 28px
            for r in range(33, 45):
                if r < len(row_data):
                    cells = row_data[r].get("values", [])
                    first = get_cell_value(cells[0]) if cells else ""
                    if "TOTAL" in first.upper() or "GROSS PROFIT" in first.upper() or "RETAINED" in first.upper() or "OPERATING" in first.upper():
                        reqs.append(rhs(sid, r, r + 1, 32))
                    elif not first.strip():
                        reqs.append(rhs(sid, r, r + 1, 12))
                    else:
                        reqs.append(rhs(sid, r, r + 1, 28))
            # Rows 45-67 remaining
            for r in range(45, last_content_row + 1):
                if r < len(row_data):
                    cells = row_data[r].get("values", [])
                    first = get_cell_value(cells[0]) if cells else ""
                    if not first.strip():
                        reqs.append(rhs(sid, r, r + 1, 12))
                    elif "TOTAL" in first.upper() or first.upper().startswith("WHAT") or "CAPACITY" in first.upper():
                        reqs.append(rhs(sid, r, r + 1, 32))
                    elif "Note:" in first or "COGS" in first:
                        reqs.append(rhs(sid, r, r + 1, 32))
                    else:
                        reqs.append(rhs(sid, r, r + 1, 28))

            # Vertical align all content
            reqs.append(valign_middle(sid, 0, last_content_row + 1, 0, last_content_col + 1))

        elif title == "Monthly Tracker":
            # Row 0 = title → 44px (currently 59px)
            reqs.append(rhs(sid, 0, 1, 44))
            # Row 1 = subtitle → 24px (currently 59px)
            reqs.append(rhs(sid, 1, 2, 24))
            # Row 2 = spacer → 12px (currently 59px)
            reqs.append(rhs(sid, 2, 3, 12))
            # Row 3 = GOAL/ACT header → 28px (currently 59px)
            reqs.append(rhs(sid, 3, 4, 28))
            # Row 4 = month names → 34px
            reqs.append(rhs(sid, 4, 5, 34))
            # Row 5 = spacer → 12px
            reqs.append(rhs(sid, 5, 6, 12))
            # Row 6 = PROJECTS section header → 32px
            reqs.append(rhs(sid, 6, 7, 32))
            # Row 7 = Projects Completed → 28px
            reqs.append(rhs(sid, 7, 8, 28))
            # Row 8 = spacer → 12px
            reqs.append(rhs(sid, 8, 9, 12))
            # Row 9 = Project Revenue total → 32px
            reqs.append(rhs(sid, 9, 10, 32))
            # Row 10 = spacer → 12px
            reqs.append(rhs(sid, 10, 11, 12))
            # Row 11 = RETAINERS section → 32px
            reqs.append(rhs(sid, 11, 12, 32))
            # Row 12 = Active Retainer → 28px
            reqs.append(rhs(sid, 12, 13, 28))
            # Row 13 = spacer → 12px
            reqs.append(rhs(sid, 13, 14, 12))
            # Row 14 = Retainer Revenue → 32px
            reqs.append(rhs(sid, 14, 15, 32))
            # Row 15 = Image Licensing → 28px
            reqs.append(rhs(sid, 15, 16, 28))
            # Row 16 = spacer → 12px
            reqs.append(rhs(sid, 16, 17, 12))
            # Row 17 = TOTALS section → 32px
            reqs.append(rhs(sid, 17, 18, 32))
            # Row 18 = Total Revenue → 32px
            reqs.append(rhs(sid, 18, 19, 32))
            # Row 19 = spacer → 12px
            reqs.append(rhs(sid, 19, 20, 12))
            # Rows 20-22 = cumulative data → 28px
            for r in range(20, 23):
                reqs.append(rhs(sid, r, r + 1, 28))
            # Row 23 = spacer → 12px
            reqs.append(rhs(sid, 23, 24, 12))
            # Row 24 = PIPELINE section → 32px
            reqs.append(rhs(sid, 24, 25, 32))
            # Rows 25-33 = pipeline data → 28px
            for r in range(25, min(34, last_content_row + 1)):
                if r < len(row_data):
                    cells = row_data[r].get("values", [])
                    first = get_cell_value(cells[0]) if cells else ""
                    if not first.strip():
                        reqs.append(rhs(sid, r, r + 1, 12))
                    elif "PROFIT" in first.upper() or "PIPELINE" in first.upper():
                        reqs.append(rhs(sid, r, r + 1, 32))
                    else:
                        reqs.append(rhs(sid, r, r + 1, 28))

            # Col A = 202px → 180px (label column)
            reqs.append(cws(sid, 0, 1, 180))
            # Freeze through row 6 (title, subtitle, spacer, goal/act, months, spacer)
            reqs.append(freeze(sid, rows=6))

            # Vertical align
            reqs.append(valign_middle(sid, 0, last_content_row + 1, 0, last_content_col + 1))

        elif title == "Project COGS":
            # Col A = 24px but holds full labels → 200px
            reqs.append(cws(sid, 0, 1, 200))
            # Cols B-F = 110px → fine for data

            # Freeze through row 4 (title, subtitle, spacer, headers)
            reqs.append(freeze(sid, rows=4))

            # Row 0 = title → 44px (currently 12px — way too small!)
            reqs.append(rhs(sid, 0, 1, 44))
            # Row 1 = subtitle → 24px (currently 48px)
            reqs.append(rhs(sid, 1, 2, 24))
            # Row 2 = spacer → 12px
            reqs.append(rhs(sid, 2, 3, 12))
            # Row 3 = headers → 34px
            reqs.append(rhs(sid, 3, 4, 34))
            # Rows 4-12 = data → 28px
            for r in range(4, 13):
                reqs.append(rhs(sid, r, r + 1, 28))
            # Row 12 = spacer already handled
            # Row 13 = TOTAL COGS → 32px
            reqs.append(rhs(sid, 13, 14, 32))
            # Row 14 = spacer → 12px
            # Row 15 = Project Price → 28px
            reqs.append(rhs(sid, 15, 16, 28))
            # Row 16 = spacer → 12px
            # Row 17 = Gross Profit → 32px
            reqs.append(rhs(sid, 17, 18, 32))
            # Row 18 = Gross Margin → 28px
            reqs.append(rhs(sid, 18, 19, 28))
            # Row 19 = spacer → 12px
            # Row 20 = AOS MARGIN CHECK section → 32px
            reqs.append(rhs(sid, 20, 21, 32))
            # Row 21 = Meets 40% → 32px (dark accent)
            reqs.append(rhs(sid, 21, 22, 32))
            # Row 22 = Meets 45% → 28px
            reqs.append(rhs(sid, 22, 23, 28))
            # Row 23 = spacer → 12px
            # Row 24 = CASH vs FOUNDER → 32px
            reqs.append(rhs(sid, 24, 25, 32))
            # Rows 25-28 = data → 28px
            for r in range(25, 29):
                if r < len(row_data):
                    cells = row_data[r].get("values", [])
                    first = get_cell_value(cells[0]) if cells else ""
                    if not first.strip():
                        pass  # spacer handled by generic
                    else:
                        reqs.append(rhs(sid, r, r + 1, 28))
            # Row 29 = COST-SHARE section → 32px
            reqs.append(rhs(sid, 29, 30, 32))
            # Rows 30-33 = data → 28px
            for r in range(30, min(34, last_content_row + 1)):
                if r < len(row_data):
                    cells = row_data[r].get("values", [])
                    first = get_cell_value(cells[0]) if cells else ""
                    if not first.strip():
                        pass
                    else:
                        reqs.append(rhs(sid, r, r + 1, 28))

            # Vertical align
            reqs.append(valign_middle(sid, 0, last_content_row + 1, 0, last_content_col + 1))

        elif title == "Overhead":
            # Col A = 24px but holds labels → 250px
            reqs.append(cws(sid, 0, 1, 250))
            # Cols B-C = 120px → fine

            # Freeze through row 3 (title, headers, spacer)
            reqs.append(freeze(sid, rows=3))

            # Row 0 = title → 44px (currently 12px)
            reqs.append(rhs(sid, 0, 1, 44))
            # Row 1 = headers (Category/Monthly/Annual) → 34px (currently 48px)
            reqs.append(rhs(sid, 1, 2, 34))
            # Row 2 = spacer → 12px
            reqs.append(rhs(sid, 2, 3, 12))

            # All remaining rows: section headers 32px, data 28px, spacers 12px, total 32px
            for r in range(3, last_content_row + 1):
                if r < len(row_data):
                    cells = row_data[r].get("values", [])
                    first = get_cell_value(cells[0]) if cells else ""
                    current_h = row_metadata[r].get("pixelSize", 21) if r < len(row_metadata) else 21

                    if not first.strip():
                        if current_h != 12:
                            reqs.append(rhs(sid, r, r + 1, 12))
                    elif "TOTAL" in first.upper():
                        reqs.append(rhs(sid, r, r + 1, 32))
                    elif first.upper() in ["MARKETING", "SOFTWARE & SUBSCRIPTIONS", "VEHICLE",
                                            "EQUIPMENT", "OFFICE", "INSURANCE", "ACCOUNTING & LEGAL",
                                            "RESERVES & DEVELOPMENT"]:
                        reqs.append(rhs(sid, r, r + 1, 32))
                    else:
                        reqs.append(rhs(sid, r, r + 1, 28))

            # Vertical align
            reqs.append(valign_middle(sid, 0, last_content_row + 1, 0, last_content_col + 1))

        elif title == "Pricing Guide":
            # Col A = 24px but holds labels → 200px
            reqs.append(cws(sid, 0, 1, 200))
            # Col B = 200px → keep (descriptions)
            # Cols C-E = 120px → keep

            # Freeze through row 5 (title, subtitle, spacer, headers, spacer)
            reqs.append(freeze(sid, rows=5))

            # Row 0 = title → 44px (currently 12px)
            reqs.append(rhs(sid, 0, 1, 44))
            # Row 1 = subtitle → 24px (currently 48px)
            reqs.append(rhs(sid, 1, 2, 24))
            # Row 2 = spacer → 12px
            reqs.append(rhs(sid, 2, 3, 12))
            # Row 3 = headers → 34px
            reqs.append(rhs(sid, 3, 4, 34))
            # Row 4 = spacer → 12px

            # All remaining rows
            for r in range(5, last_content_row + 1):
                if r < len(row_data):
                    cells = row_data[r].get("values", [])
                    first = get_cell_value(cells[0]) if cells else ""
                    current_h = row_metadata[r].get("pixelSize", 21) if r < len(row_metadata) else 21

                    if not first.strip():
                        if current_h != 12:
                            reqs.append(rhs(sid, r, r + 1, 12))
                    elif first.startswith("ICP #") or first == "STANDALONE (ALL ICPs)" or first == "ADD-ONS":
                        reqs.append(rhs(sid, r, r + 1, 32))
                    elif current_h == 36:
                        # Dark accent rows (like "Architectural Project") → 32px
                        reqs.append(rhs(sid, r, r + 1, 32))
                    else:
                        reqs.append(rhs(sid, r, r + 1, 28))

            # Vertical align
            reqs.append(valign_middle(sid, 0, last_content_row + 1, 0, last_content_col + 1))

        elif title == "Quarterly Rocks":
            # Col A = 24px → 50px (holds Q1/Q2/Q3/Q4)
            reqs.append(cws(sid, 0, 1, 50))
            # Col B = 300px → keep (rock descriptions)

            # Freeze through row 3 (title, spacer, headers)
            reqs.append(freeze(sid, rows=3))

            # Row 0 = title → 44px (currently 12px)
            reqs.append(rhs(sid, 0, 1, 44))
            # Row 1 = spacer → 12px
            reqs.append(rhs(sid, 1, 2, 12))
            # Row 2 = headers (QTR/ROCK/OWNER etc) → 34px
            reqs.append(rhs(sid, 2, 3, 34))

            # All remaining rows
            for r in range(3, last_content_row + 1):
                if r < len(row_data):
                    cells = row_data[r].get("values", [])
                    first = get_cell_value(cells[0]) if cells else ""

                    if not first.strip():
                        reqs.append(rhs(sid, r, r + 1, 12))
                    elif first.startswith("Q1:") or first.startswith("Q2:") or first.startswith("Q3:") or first.startswith("Q4:"):
                        # Quarter section headers → 32px
                        reqs.append(rhs(sid, r, r + 1, 32))
                    else:
                        # Data rows → 28px (currently 36px — too tall)
                        reqs.append(rhs(sid, r, r + 1, 28))

            # Vertical align
            reqs.append(valign_middle(sid, 0, last_content_row + 1, 0, last_content_col + 1))

        # ── Make trailing rows past content consistently 12px ──
        trailing_end = min(last_content_row + 11, len(row_metadata))
        for r in range(last_content_row + 1, trailing_end):
            reqs.append(rhs(sid, r, r + 1, 12))

        # Execute
        if reqs:
            success = execute_batch(service, reqs, label=title)
            if not success:
                print(f"  FAILED on {title}, continuing...")
        else:
            print(f"  No changes needed for {title}")

        time.sleep(1)  # Brief pause between tabs

    print("\n=== ALL TABS FIXED ===")


if __name__ == "__main__":
    main()
