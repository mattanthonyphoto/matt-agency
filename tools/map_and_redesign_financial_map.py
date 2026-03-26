"""
Map revenue data from Finance Tracker → Financial Map Monthly Tracker,
then redesign ALL 6 tabs of the Financial Map to match the Finance Tracker design system.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_sheets_service

# ── Sheet IDs ────────────────────────────────────────────────────────────────
SOURCE_ID = '1fPpOPnAYEnfCu33h1ki9NzFGTUOkpgd4mMSQX_sT9CY'  # Finance Tracker
TARGET_ID = '1nrzAfXzRiFIQpa85one6iuMXASIBbgPrwDoI6TwH9KU'  # Financial Map

# ── Design Tokens (Finance Tracker system) ───────────────────────────────────
CHARCOAL   = {"red": 0.153, "green": 0.173, "blue": 0.224}   # #272c38
BLUE       = {"red": 0.224, "green": 0.443, "blue": 0.871}   # #3870de
GREEN      = {"red": 0.118, "green": 0.624, "blue": 0.424}   # #1e9f6c
RED        = {"red": 0.851, "green": 0.200, "blue": 0.200}   # #d93333
ORANGE     = {"red": 0.902, "green": 0.533, "blue": 0.118}   # #e6871e
WHITE      = {"red": 1, "green": 1, "blue": 1}
ZEBRA      = {"red": 0.965, "green": 0.965, "blue": 0.969}   # #f6f6f7
BORDER     = {"red": 0.882, "green": 0.894, "blue": 0.906}   # #e1e4e7
BORDER_MED = {"red": 0.820, "green": 0.827, "blue": 0.843}   # #d1d3d7
MUTED      = {"red": 0.545, "green": 0.573, "blue": 0.608}   # #8b929b
SUBTITLE   = {"red": 0.702, "green": 0.718, "blue": 0.741}   # #b3b7bd
LIGHT_GREY = {"red": 0.941, "green": 0.945, "blue": 0.953}   # #f0f1f3 section headers
PALE_BLUE  = {"red": 0.922, "green": 0.933, "blue": 0.980}   # #ebeefa ACT columns
WARM_INPUT = {"red": 1.0, "green": 0.973, "blue": 0.882}     # #fff8e1 inputs
GREEN_TOTAL= {"red": 0.906, "green": 0.965, "blue": 0.933}   # #e7f6ee totals

# ── Helpers ──────────────────────────────────────────────────────────────────
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

def clear_borders(sid, sr, er, sc, ec):
    none_b = {"style": "NONE"}
    return {"updateBorders": {"range": gr(sid, sr, er, sc, ec),
            "top": none_b, "bottom": none_b, "left": none_b, "right": none_b,
            "innerHorizontal": none_b, "innerVertical": none_b}}

F_BG = "userEnteredFormat.backgroundColor"
F_TF = "userEnteredFormat.textFormat"
F_NF = "userEnteredFormat.numberFormat"
F_AL = "userEnteredFormat.horizontalAlignment"
F_VA = "userEnteredFormat.verticalAlignment"
F_BG_TF = f"{F_BG},{F_TF}"
F_ALL = f"{F_BG},{F_TF},{F_AL},{F_VA}"
F_BG_TF_AL = f"{F_BG},{F_TF},{F_AL}"


# ═══════════════════════════════════════════════════════════════════════════════
# TASK 1: MAP DATA
# ═══════════════════════════════════════════════════════════════════════════════

def map_data(service):
    """Read monthly revenue from Finance Tracker, write to Financial Map."""
    print("\n══════════════════════════════════════════════════")
    print("  TASK 1: MAP DATA")
    print("══════════════════════════════════════════════════")

    sheets = service.spreadsheets()

    # ── Read source data ─────────────────────────────────────────────────────
    # Try Dashboard Monthly Breakdown first
    print("\n→ Reading Finance Tracker Dashboard...")
    dash_data = sheets.values().get(
        spreadsheetId=SOURCE_ID,
        range="Dashboard!A1:Z100",
        valueRenderOption="UNFORMATTED_VALUE"
    ).execute().get("values", [])

    # Find the Monthly Breakdown section
    monthly_revenue = {}
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    month_short = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    for i, row in enumerate(dash_data):
        if not row:
            continue
        cell = str(row[0]).strip().lower()
        # Look for "monthly breakdown" or month names in a table
        if "monthly" in cell and "breakdown" in cell:
            print(f"  Found Monthly Breakdown at row {i+1}")
            # Read subsequent rows for month data
            for j in range(i+1, min(i+20, len(dash_data))):
                if j >= len(dash_data) or not dash_data[j]:
                    continue
                r = dash_data[j]
                month_cell = str(r[0]).strip()
                for mi, mn in enumerate(month_names):
                    if month_cell.lower().startswith(mn.lower()[:3]):
                        # Revenue is typically in column B (index 1)
                        if len(r) > 1 and r[1] is not None:
                            try:
                                val = float(r[1])
                                monthly_revenue[mi] = val
                                print(f"  {month_short[mi]}: ${val:,.2f}")
                            except (ValueError, TypeError):
                                pass
                        break
            break

    # If Dashboard didn't work, try P&L tab
    if not monthly_revenue:
        print("  Dashboard monthly breakdown not found, trying P&L tab...")
        try:
            pl_data = sheets.values().get(
                spreadsheetId=SOURCE_ID,
                range="P&L!A1:Z50",
                valueRenderOption="UNFORMATTED_VALUE"
            ).execute().get("values", [])
            for i, row in enumerate(pl_data):
                if not row:
                    continue
                cell = str(row[0]).strip().lower()
                for mi, mn in enumerate(month_names):
                    if cell.startswith(mn.lower()[:3]):
                        if len(row) > 1 and row[1] is not None:
                            try:
                                val = float(row[1])
                                monthly_revenue[mi] = val
                                print(f"  {month_short[mi]}: ${val:,.2f}")
                            except (ValueError, TypeError):
                                pass
                        break
        except Exception as e:
            print(f"  P&L read error: {e}")

    # Also try Income tab
    if not monthly_revenue:
        print("  Trying Income tab...")
        try:
            inc_data = sheets.values().get(
                spreadsheetId=SOURCE_ID,
                range="Income!A1:Z100",
                valueRenderOption="UNFORMATTED_VALUE"
            ).execute().get("values", [])
            # Print first few rows to understand structure
            for i, row in enumerate(inc_data[:5]):
                print(f"  Income row {i+1}: {row[:10]}")
            # Find Total Revenue row
            for i, row in enumerate(inc_data):
                if not row:
                    continue
                cell = str(row[0]).strip().lower()
                if "total" in cell and "revenue" in cell:
                    print(f"  Found Total Revenue at row {i+1}: {row}")
                    # Monthly values should be in subsequent columns
                    for mi in range(12):
                        col_idx = mi + 1  # assuming col B onwards
                        if len(row) > col_idx and row[col_idx] is not None:
                            try:
                                val = float(row[col_idx])
                                monthly_revenue[mi] = val
                                print(f"  {month_short[mi]}: ${val:,.2f}")
                            except (ValueError, TypeError):
                                pass
                    break
        except Exception as e:
            print(f"  Income read error: {e}")

    if not monthly_revenue:
        print("\n  ⚠ Could not find monthly revenue data. Dumping source tabs for debugging...")
        # Last resort: dump first rows of all tabs to find the data
        for tab in ["Dashboard", "Income", "P&L"]:
            try:
                data = sheets.values().get(
                    spreadsheetId=SOURCE_ID,
                    range=f"{tab}!A1:F20",
                    valueRenderOption="UNFORMATTED_VALUE"
                ).execute().get("values", [])
                print(f"\n  --- {tab} (first 20 rows) ---")
                for i, row in enumerate(data):
                    print(f"  Row {i+1}: {row}")
            except Exception as e:
                print(f"  Error reading {tab}: {e}")
        return

    # ── Read existing GOAL values from Financial Map ────────────────────────
    print("\n→ Reading Financial Map goals...")
    # GOAL columns: B(Jan), D(Feb), F(Mar), H(Apr), J(May), L(Jun), N(Jul), P(Aug), R(Sep), T(Oct), V(Nov), X(Dec), Z(YR GOAL)
    # ACT columns:  C(Jan), E(Feb), G(Mar), I(Apr), K(May), M(Jun), O(Jul), Q(Aug), S(Sep), U(Oct), W(Nov), Y(Dec), AA(YR ACT)
    goal_data = sheets.values().get(
        spreadsheetId=TARGET_ID,
        range="Monthly Tracker!A1:AB30",
        valueRenderOption="UNFORMATTED_VALUE"
    ).execute().get("values", [])

    print("  Current Monthly Tracker structure:")
    for i, row in enumerate(goal_data[:20]):
        if row:
            print(f"  Row {i+1}: {row[:8]}...")

    # Read cumulative GOAL values from row 15 (index 14)
    cum_goals = {}
    if len(goal_data) > 14:
        goal_row = goal_data[14]  # Row 15 = Cumulative Goal
        # GOAL columns are B=1, D=3, F=5, H=7, J=9, L=11, N=13, P=15, R=17, T=19, V=21, X=23
        goal_cols = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]
        for mi, ci in enumerate(goal_cols):
            if len(goal_row) > ci and goal_row[ci] is not None:
                try:
                    cum_goals[mi] = float(goal_row[ci])
                except (ValueError, TypeError):
                    pass
        print(f"  Cumulative goals found: {cum_goals}")

    # ── Write ACT values to Financial Map ───────────────────────────────────
    print("\n→ Writing actuals to Monthly Tracker...")

    # ACT column letters: C, E, G, I, K, M, O, Q, S, U, W, Y, AA
    act_cols = ['C', 'E', 'G', 'I', 'K', 'M', 'O', 'Q', 'S', 'U', 'W', 'Y']

    updates = []
    cumulative = 0

    for mi in range(12):
        rev = monthly_revenue.get(mi, 0)
        col = act_cols[mi]
        cumulative += rev

        # Row 7: Project Revenue ACT
        updates.append({
            'range': f"Monthly Tracker!{col}7",
            'values': [[rev]]
        })

        # Row 14: Total Revenue ACT (same as project revenue for now)
        updates.append({
            'range': f"Monthly Tracker!{col}14",
            'values': [[rev]]
        })

        # Row 16: Cumulative Actual
        updates.append({
            'range': f"Monthly Tracker!{col}16",
            'values': [[cumulative]]
        })

        # Row 17: % to Goal
        cum_goal = cum_goals.get(mi, 0)
        pct = cumulative / cum_goal if cum_goal > 0 else 0
        updates.append({
            'range': f"Monthly Tracker!{col}17",
            'values': [[pct]]
        })

    # YR ACT (column AA)
    annual_total = sum(monthly_revenue.get(mi, 0) for mi in range(12))
    updates.append({'range': "Monthly Tracker!AA7", 'values': [[annual_total]]})
    updates.append({'range': "Monthly Tracker!AA14", 'values': [[annual_total]]})
    updates.append({'range': "Monthly Tracker!AA16", 'values': [[cumulative]]})

    # Write all at once
    body = {'valueInputOption': 'USER_ENTERED', 'data': updates}
    result = sheets.values().batchUpdate(spreadsheetId=TARGET_ID, body=body).execute()
    print(f"  Updated {result.get('totalUpdatedCells', 0)} cells")
    print(f"  Annual total: ${annual_total:,.2f}")

    return monthly_revenue


# ═══════════════════════════════════════════════════════════════════════════════
# TASK 2: REDESIGN ALL TABS
# ═══════════════════════════════════════════════════════════════════════════════

def get_tab_ids(service):
    """Get sheet IDs for all tabs."""
    meta = service.spreadsheets().get(spreadsheetId=TARGET_ID).execute()
    tabs = {}
    for sheet in meta['sheets']:
        props = sheet['properties']
        tabs[props['title']] = props['sheetId']
        print(f"  Tab: {props['title']} (id={props['sheetId']}, "
              f"{props['gridProperties']['rowCount']}r x {props['gridProperties']['columnCount']}c)")
    return tabs, meta


def redesign_all_tabs(service):
    """Apply Finance Tracker design system to all 6 tabs."""
    print("\n══════════════════════════════════════════════════")
    print("  TASK 2: REDESIGN ALL TABS")
    print("══════════════════════════════════════════════════")

    sheets = service.spreadsheets()
    tabs, meta = get_tab_ids(service)

    # Read existing data from each tab to understand structure
    tab_data = {}
    for tab_name in tabs:
        try:
            data = sheets.values().get(
                spreadsheetId=TARGET_ID,
                range=f"'{tab_name}'!A1:AE50",
                valueRenderOption="FORMATTED_VALUE"
            ).execute().get("values", [])
            tab_data[tab_name] = data
            print(f"\n  {tab_name} ({len(data)} rows):")
            for i, row in enumerate(data[:8]):
                if row:
                    print(f"    Row {i+1}: {row[:6]}...")
        except Exception as e:
            print(f"  Error reading {tab_name}: {e}")
            tab_data[tab_name] = []

    # ── Build formatting requests ────────────────────────────────────────────
    reqs = []

    for tab_name, sid in tabs.items():
        print(f"\n→ Redesigning: {tab_name}")
        data = tab_data.get(tab_name, [])
        num_rows = len(data) + 5  # Padding
        if num_rows < 30:
            num_rows = 30

        # Determine number of columns from metadata
        for sheet in meta['sheets']:
            if sheet['properties']['title'] == tab_name:
                num_cols = sheet['properties']['gridProperties']['columnCount']
                break
        else:
            num_cols = 28

        # ── Global: Set all cells to Inter font ──────────────────────────────
        reqs.append(rc(sid, 0, num_rows, 0, num_cols,
            {"textFormat": {"fontFamily": "Inter", "fontSize": 10}},
            F_TF))

        # ── Global: Set all backgrounds to white first ───────────────────────
        reqs.append(rc(sid, 0, num_rows, 0, num_cols,
            {"backgroundColor": WHITE}, F_BG))

        # ── Global: Clear all borders then apply light grey ──────────────────
        reqs.append(clear_borders(sid, 0, num_rows, 0, num_cols))

        # ── Tab-specific formatting ──────────────────────────────────────────
        if tab_name == "Monthly Tracker":
            _format_monthly_tracker(reqs, sid, data, num_rows, num_cols)
        elif tab_name == "Dashboard":
            _format_dashboard(reqs, sid, data, num_rows, num_cols)
        elif tab_name == "Project COGS":
            _format_generic_tab(reqs, sid, data, num_rows, num_cols, "Project COGS")
        elif tab_name == "Overhead":
            _format_generic_tab(reqs, sid, data, num_rows, num_cols, "Overhead")
        elif tab_name == "Pricing Guide":
            _format_generic_tab(reqs, sid, data, num_rows, num_cols, "Pricing Guide")
        elif tab_name == "Quarterly Rocks":
            _format_generic_tab(reqs, sid, data, num_rows, num_cols, "Quarterly Rocks")

    # ── Execute in batches ───────────────────────────────────────────────────
    print(f"\n→ Applying {len(reqs)} formatting requests...")
    batch_size = 200
    for i in range(0, len(reqs), batch_size):
        batch = reqs[i:i+batch_size]
        sheets.batchUpdate(spreadsheetId=TARGET_ID, body={"requests": batch}).execute()
        print(f"  Batch {i//batch_size + 1}: {len(batch)} requests applied")
        if i + batch_size < len(reqs):
            time.sleep(1)

    print("\n  Redesign complete!")


def _format_monthly_tracker(reqs, sid, data, num_rows, num_cols):
    """Format the Monthly Tracker tab."""
    # Row 0: spacer
    reqs.append(rh(sid, 0, 16))

    # Row 1: Title - "Monthly Tracker"
    reqs.append(rh(sid, 0, 50))
    reqs.append(rc(sid, 0, 1, 0, num_cols,
        {"backgroundColor": WHITE,
         "textFormat": tf(bold=True, sz=22, color=CHARCOAL),
         "verticalAlignment": "MIDDLE"}, F_ALL))

    # Row 2: Subtitle
    if len(data) > 1:
        reqs.append(rh(sid, 1, 24))
        reqs.append(rc(sid, 1, 2, 0, num_cols,
            {"backgroundColor": WHITE,
             "textFormat": tf(sz=11, color=SUBTITLE)}, F_BG_TF))

    # Find header rows and section rows by scanning data
    # Row 3 (index 2) typically has month names
    # Row 4 (index 3) typically has GOAL/ACT labels

    # Month header row (row 3, index 2): dark charcoal bar with white text
    reqs.append(rh(sid, 2, 32))
    reqs.append(rc(sid, 2, 3, 0, num_cols,
        {"backgroundColor": CHARCOAL,
         "textFormat": tf(bold=True, sz=9, color=WHITE),
         "horizontalAlignment": "CENTER",
         "verticalAlignment": "MIDDLE"}, F_ALL))

    # GOAL/ACT label row (row 4, index 3)
    reqs.append(rh(sid, 3, 24))
    reqs.append(rc(sid, 3, 4, 0, num_cols,
        {"backgroundColor": CHARCOAL,
         "textFormat": tf(bold=True, sz=9, color=MUTED),
         "horizontalAlignment": "CENTER",
         "verticalAlignment": "MIDDLE"}, F_ALL))

    # Section header rows: identify them (rows with section titles like "Revenue", "Pipeline")
    section_rows = []
    data_rows = []
    total_rows = []
    pct_rows = []

    for i, row in enumerate(data):
        if i < 4:
            continue  # Skip headers
        if not row or not row[0]:
            continue
        label = str(row[0]).strip().lower()
        if any(s in label for s in ["revenue", "pipeline", "metrics", "section", "kpi"]):
            if len(label) < 20:  # Short labels are likely section headers
                section_rows.append(i)
        elif "total" in label or "cumulative" in label:
            total_rows.append(i)
        elif "%" in label or "rate" in label:
            pct_rows.append(i)
        else:
            data_rows.append(i)

    # Known rows from the spec:
    # Row 5 (idx 4): section header "Revenue" area
    # Row 6 (idx 5): Projects Completed
    # Row 7 (idx 6): Project Revenue
    # Row 10 (idx 9): Active Retainer Clients
    # Row 11 (idx 10): Retainer Revenue
    # Row 12 (idx 11): Image Licensing Revenue
    # Row 14 (idx 13): Total Revenue
    # Row 15 (idx 14): Cumulative Goal
    # Row 16 (idx 15): Cumulative Actual
    # Row 17 (idx 16): % to Goal
    # Row 20 (idx 19): Qualified Leads
    # Row 26 (idx 25): Avg Revenue/Project

    # Section headers - light grey background
    known_sections = [4, 8, 18, 24]  # Approximate section header row indices
    for ri in known_sections:
        if ri < num_rows:
            reqs.append(rh(sid, ri, 32))
            reqs.append(rc(sid, ri, ri+1, 0, num_cols,
                {"backgroundColor": LIGHT_GREY,
                 "textFormat": tf(bold=True, sz=14, color=CHARCOAL),
                 "verticalAlignment": "MIDDLE"}, F_ALL))
            reqs.append(border_side(sid, ri, ri+1, 0, num_cols, "bottom",
                color=BORDER_MED, style="SOLID", width=1))

    # Also check actual data for section rows
    for i, row in enumerate(data):
        if i < 4:
            continue
        if not row:
            continue
        label = str(row[0]).strip() if row[0] else ""
        # Section headers are usually in col A with no data in other columns
        has_data_cols = any(str(c).strip() for c in row[1:4]) if len(row) > 1 else False
        if label and not has_data_cols and len(label) < 25:
            if i not in known_sections:
                reqs.append(rh(sid, i, 32))
                reqs.append(rc(sid, i, i+1, 0, num_cols,
                    {"backgroundColor": LIGHT_GREY,
                     "textFormat": tf(bold=True, sz=14, color=CHARCOAL),
                     "verticalAlignment": "MIDDLE"}, F_ALL))

    # Total rows - green total background
    known_totals = [13, 14, 15]  # Rows 14, 15, 16 (Total Revenue, Cumulative Goal/Actual)
    for ri in known_totals:
        if ri < num_rows:
            reqs.append(rc(sid, ri, ri+1, 0, num_cols,
                {"backgroundColor": GREEN_TOTAL,
                 "textFormat": tf(bold=True, sz=10, color=CHARCOAL)}, F_BG_TF))
            reqs.append(border_side(sid, ri, ri+1, 0, num_cols, "top",
                color=GREEN, style="SOLID", width=2))

    # % to Goal row (row 17, idx 16)
    if 16 < num_rows:
        reqs.append(rc(sid, 16, 17, 0, num_cols,
            {"backgroundColor": PALE_BLUE,
             "textFormat": tf(bold=True, sz=10, color=BLUE)}, F_BG_TF))

    # ACT columns get pale blue background for data rows
    # ACT column indices: C=2, E=4, G=6, I=8, K=10, M=12, O=14, Q=16, S=18, U=20, W=22, Y=24, AA=26
    act_col_indices = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26]
    for ci in act_col_indices:
        if ci < num_cols:
            # Apply pale blue to data area (rows 5-27 ish)
            for ri in range(4, min(28, num_rows)):
                if ri not in known_sections and ri not in known_totals and ri != 16:
                    reqs.append(rc(sid, ri, ri+1, ci, ci+1,
                        {"backgroundColor": PALE_BLUE}, F_BG))

    # Zebra striping on non-section data rows
    data_row_indices = [5, 6, 9, 10, 11, 19, 20, 21, 22, 25, 26]
    for idx, ri in enumerate(data_row_indices):
        if ri < num_rows and idx % 2 == 1:
            # Apply zebra to GOAL columns only (ACT already has pale blue)
            goal_col_indices = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]
            for ci in goal_col_indices:
                if ci < num_cols:
                    reqs.append(rc(sid, ri, ri+1, ci, ci+1,
                        {"backgroundColor": ZEBRA}, F_BG))

    # Column A: labels - left aligned, muted color
    reqs.append(rc(sid, 4, num_rows, 0, 1,
        {"textFormat": tf(sz=10, color=CHARCOAL),
         "horizontalAlignment": "LEFT"}, f"{F_TF},{F_AL}"))

    # Light grid borders on data area
    reqs.append(border_box(sid, 2, min(28, num_rows), 0, min(27, num_cols),
        color=BORDER, style="SOLID", width=1))

    # Column A width
    reqs.append(cw(sid, 0, 180))

    # Set data column widths (narrower for GOAL/ACT pairs)
    for ci in range(1, min(27, num_cols)):
        reqs.append(cw(sid, ci, 75))

    print(f"  Monthly Tracker: {len(reqs)} format requests")


def _format_dashboard(reqs, sid, data, num_rows, num_cols):
    """Format the Dashboard tab."""
    # Row 0: Title row
    reqs.append(rh(sid, 0, 50))
    reqs.append(rc(sid, 0, 1, 0, num_cols,
        {"backgroundColor": WHITE,
         "textFormat": tf(bold=True, sz=22, color=CHARCOAL),
         "verticalAlignment": "MIDDLE"}, F_ALL))

    # Row 1: subtitle
    if len(data) > 1:
        reqs.append(rh(sid, 1, 24))
        reqs.append(rc(sid, 1, 2, 0, num_cols,
            {"textFormat": tf(sz=11, color=SUBTITLE)}, F_TF))

    # Scan for section headers, KPI blocks, tables
    for i, row in enumerate(data):
        if i < 2 or not row:
            continue
        label = str(row[0]).strip() if row[0] else ""

        # Detect header-like rows
        if label and len(label) < 30:
            has_data = any(str(c).strip() for c in row[1:3]) if len(row) > 1 else False
            if not has_data and label[0].isupper():
                # Likely a section header
                reqs.append(rh(sid, i, 36))
                reqs.append(rc(sid, i, i+1, 0, num_cols,
                    {"backgroundColor": CHARCOAL,
                     "textFormat": tf(bold=True, sz=12, color=WHITE),
                     "verticalAlignment": "MIDDLE"}, F_ALL))
                continue

        # Table column headers (short labels with peers)
        if label and has_peers(row):
            # Could be a table header row
            reqs.append(rc(sid, i, i+1, 0, num_cols,
                {"backgroundColor": WHITE,
                 "textFormat": tf(bold=True, sz=9, color=MUTED)}, F_BG_TF))
            reqs.append(border_side(sid, i, i+1, 0, num_cols, "bottom",
                color=BORDER, style="SOLID", width=2))

    # Zebra striping on data rows
    in_table = False
    for i, row in enumerate(data):
        if i < 2:
            continue
        if not row or not row[0]:
            in_table = False
            continue
        label = str(row[0]).strip()
        if has_peers(row) and is_data_row(row):
            if in_table and i % 2 == 0:
                reqs.append(rc(sid, i, i+1, 0, num_cols,
                    {"backgroundColor": ZEBRA}, F_BG))
            in_table = True

    # Column widths
    reqs.append(cw(sid, 0, 200))
    for ci in range(1, min(8, num_cols)):
        reqs.append(cw(sid, ci, 120))

    print(f"  Dashboard: formatted")


def _format_generic_tab(reqs, sid, data, num_rows, num_cols, tab_name):
    """Format a generic tab with the design system."""
    # Row 0: Title
    reqs.append(rh(sid, 0, 50))
    reqs.append(rc(sid, 0, 1, 0, num_cols,
        {"backgroundColor": WHITE,
         "textFormat": tf(bold=True, sz=22, color=CHARCOAL),
         "verticalAlignment": "MIDDLE"}, F_ALL))

    # Row 1: subtitle if exists
    if len(data) > 1:
        reqs.append(rh(sid, 1, 24))
        reqs.append(rc(sid, 1, 2, 0, num_cols,
            {"textFormat": tf(sz=11, color=SUBTITLE)}, F_TF))

    # Scan rows
    header_row_found = False
    data_start = 2
    for i, row in enumerate(data):
        if i < 1 or not row:
            continue
        label = str(row[0]).strip() if row[0] else ""

        # Detect section headers (text in col A only, all caps or title case)
        has_data = has_peers(row)

        if label and not has_data and len(label) < 35 and i > 0:
            # Section header - dark charcoal bar
            reqs.append(rh(sid, i, 36))
            reqs.append(rc(sid, i, i+1, 0, num_cols,
                {"backgroundColor": CHARCOAL,
                 "textFormat": tf(bold=True, sz=12, color=WHITE),
                 "verticalAlignment": "MIDDLE"}, F_ALL))
            continue

        # Column headers (row with multiple short labels)
        if has_data and not header_row_found and i < 5:
            # This might be column headers
            all_short = all(len(str(c).strip()) < 20 for c in row if c)
            if all_short:
                header_row_found = True
                data_start = i + 1
                reqs.append(rh(sid, i, 32))
                reqs.append(rc(sid, i, i+1, 0, num_cols,
                    {"backgroundColor": CHARCOAL,
                     "textFormat": tf(bold=True, sz=9, color=WHITE),
                     "horizontalAlignment": "CENTER",
                     "verticalAlignment": "MIDDLE"}, F_ALL))
                continue

        # Data rows - check for totals
        if label:
            label_lower = label.lower()
            if "total" in label_lower or "sum" in label_lower:
                reqs.append(rc(sid, i, i+1, 0, num_cols,
                    {"backgroundColor": GREEN_TOTAL,
                     "textFormat": tf(bold=True, sz=10, color=CHARCOAL)}, F_BG_TF))
                reqs.append(border_side(sid, i, i+1, 0, num_cols, "top",
                    color=GREEN, style="SOLID", width=2))
            elif has_data and i >= data_start:
                # Zebra striping
                if (i - data_start) % 2 == 1:
                    reqs.append(rc(sid, i, i+1, 0, num_cols,
                        {"backgroundColor": ZEBRA}, F_BG))

    # Light grid on all data
    if len(data) > 2:
        reqs.append(border_box(sid, 1, min(len(data)+1, num_rows), 0, min(num_cols, 15),
            color=BORDER, style="SOLID", width=1))

    # Column widths
    reqs.append(cw(sid, 0, 200))
    for ci in range(1, min(10, num_cols)):
        reqs.append(cw(sid, ci, 120))

    print(f"  {tab_name}: formatted")


def has_peers(row):
    """Check if a row has multiple non-empty cells (indicates data, not a header)."""
    non_empty = sum(1 for c in row if c and str(c).strip())
    return non_empty >= 2


def is_data_row(row):
    """Check if a row looks like data (has numbers)."""
    for c in row[1:]:
        if c is None:
            continue
        try:
            float(str(c).replace('$', '').replace(',', '').replace('%', ''))
            return True
        except (ValueError, TypeError):
            continue
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("╔══════════════════════════════════════════════════╗")
    print("║  FINANCIAL MAP: DATA MAPPING & REDESIGN         ║")
    print("╚══════════════════════════════════════════════════╝")

    service = get_sheets_service()

    # Task 1: Map data from Finance Tracker → Financial Map
    monthly_revenue = map_data(service)

    # Task 2: Redesign all tabs
    redesign_all_tabs(service)

    print("\n✓ All done!")

if __name__ == "__main__":
    main()
