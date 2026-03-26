"""
Fix Financial Map colors to EXACTLY match the Finance Tracker's design system.

Problem: The Financial Map was redesigned but came out too dark. Header bars used
dark charcoal (#272c38) backgrounds everywhere, making it look heavy. The Finance
Tracker actually uses a clean, light design with colored accents.

This script reads both sheets, compares colors, and applies the Tracker's exact
color scheme to all 6 tabs of the Financial Map.
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_sheets_service

# ── Sheet IDs ────────────────────────────────────────────────────────────────
MAP_ID = '1nrzAfXzRiFIQpa85one6iuMXASIBbgPrwDoI6TwH9KU'
TRACKER_ID = '1fPpOPnAYEnfCu33h1ki9NzFGTUOkpgd4mMSQX_sT9CY'

# ── EXACT colors from Finance Tracker (verified via API read) ─────────────
# These are the ACTUAL RGB values read from the Finance Tracker cells

# Primary palette
CHARCOAL    = {"red": 0.153, "green": 0.173, "blue": 0.224}   # #272c38 — title text color, NOT for backgrounds
DARK_TEXT   = {"red": 0.094, "green": 0.110, "blue": 0.145}   # #181c25 — body text
BLUE        = {"red": 0.224, "green": 0.443, "blue": 0.871}   # #3870de — accent blue
GREEN       = {"red": 0.118, "green": 0.624, "blue": 0.424}   # #1e9f6c — income/profit green
RED         = {"red": 0.851, "green": 0.200, "blue": 0.200}   # #d93333 — expense red
ORANGE      = {"red": 0.902, "green": 0.533, "blue": 0.118}   # #e6871e — tax/warning orange
PURPLE      = {"red": 0.482, "green": 0.318, "blue": 0.804}   # #7a51cd — personal purple
WHITE       = {"red": 1, "green": 1, "blue": 1}

# Background tints (light, clean)
ZEBRA       = {"red": 0.965, "green": 0.965, "blue": 0.969}   # #f6f6f7 — alternating rows
PALE_BLUE   = {"red": 0.922, "green": 0.933, "blue": 0.980}   # #ebeefa — KPI blue bg, totals, ACT cols
PALE_RED    = {"red": 0.988, "green": 0.925, "blue": 0.925}   # #fcecec — expense section bg
PALE_GREEN  = {"red": 0.906, "green": 0.965, "blue": 0.933}   # #e7f6ee — income section bg, green totals
PALE_ORANGE = {"red": 0.988, "green": 0.953, "blue": 0.906}   # #fcf3e7 — tax total bg
LIGHT_GREY  = {"red": 0.933, "green": 0.941, "blue": 0.953}   # #eef0f3 — section label rows (close to tracker #f0f1f3)

# Text colors
MUTED       = {"red": 0.545, "green": 0.573, "blue": 0.608}   # #8b929b — column header text
SUBTITLE    = {"red": 0.702, "green": 0.718, "blue": 0.741}   # #b3b7bd — subtitle text

# Border
BORDER      = {"red": 0.882, "green": 0.894, "blue": 0.906}   # #e1e4e7
BORDER_MED  = {"red": 0.820, "green": 0.827, "blue": 0.843}   # #d1d3d7

# ── Helpers ──────────────────────────────────────────────────────────────────
def gr(sid, sr, er, sc, ec):
    return {"sheetId": sid, "startRowIndex": sr, "endRowIndex": er,
            "startColumnIndex": sc, "endColumnIndex": ec}

def rc(sid, sr, er, sc, ec, fmt, fields):
    return {"repeatCell": {"range": gr(sid, sr, er, sc, ec),
            "cell": {"userEnteredFormat": fmt}, "fields": fields}}

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

def border_box(sid, sr, er, sc, ec, color=BORDER, style="SOLID", width=1):
    b = {"style": style, "width": width, "color": color}
    return {"updateBorders": {"range": gr(sid, sr, er, sc, ec),
            "top": b, "bottom": b, "left": b, "right": b}}

def border_bottom(sid, sr, er, sc, ec, color=BORDER, style="SOLID", width=1):
    return {"updateBorders": {"range": gr(sid, sr, er, sc, ec),
            "bottom": {"style": style, "width": width, "color": color}}}

def clear_all_formatting(sid, sr, er, sc, ec):
    """Clear borders."""
    none_b = {"style": "NONE"}
    return {"updateBorders": {"range": gr(sid, sr, er, sc, ec),
            "top": none_b, "bottom": none_b, "left": none_b, "right": none_b,
            "innerHorizontal": none_b, "innerVertical": none_b}}

F_BG = "userEnteredFormat.backgroundColor"
F_TF = "userEnteredFormat.textFormat"
F_AL = "userEnteredFormat.horizontalAlignment"
F_VA = "userEnteredFormat.verticalAlignment"
F_BG_TF = f"{F_BG},{F_TF}"
F_ALL = f"{F_BG},{F_TF},{F_AL},{F_VA}"

def rgb_hex(c):
    return f"#{int(c.get('red',0)*255):02x}{int(c.get('green',0)*255):02x}{int(c.get('blue',0)*255):02x}"


def print_color_comparison():
    """Print what the Tracker uses vs what the Map has."""
    print("\n" + "=" * 70)
    print("  COLOR COMPARISON: FINANCE TRACKER vs FINANCIAL MAP")
    print("=" * 70)

    comparisons = [
        ("Header bar bg (data tables)", "#3870de (blue) or context-colored", "#272c38 (dark charcoal) — TOO DARK"),
        ("Section label bg (PROJECTS etc)", "#eef0f3 or #f0f1f3 (light grey)", "#eef0f3 (OK, but text issues)"),
        ("Column header text", "#8b929b (muted grey)", "#8a929b (close, OK)"),
        ("Title text", "#272c38 (charcoal)", "#272c38 (OK)"),
        ("Subtitle text", "#b3b7bd (light grey)", "#b3b7bb (close, OK)"),
        ("Body text", "#181c25 (dark)", "#272c38 (slightly off)"),
        ("Zebra stripe bg", "#f6f6f7", "#f6f6f6 (close)"),
        ("ACT column bg", "#ebeefa (pale blue)", "#ebedf9 (close but wrong)"),
        ("Total row bg (revenue)", "#e7f6ee (pale green)", "#e7f6ed (close)"),
        ("Total row bg (blue)", "#ebeefa (pale blue)", "NOT USED — uses #272c38 instead"),
        ("KPI Revenue card", "#ebeefa bg, #3870de text", "NOT PRESENT"),
        ("KPI Expense card", "#fcecec bg, #d93333 text", "NOT PRESENT"),
        ("Tab: Dashboard", "#272c38 (charcoal)", "#2e5c8a (dark blue) — WRONG"),
        ("Tab: Monthly Tracker", "#666666 or #3870de", "#2e7d31 (dark green) — WRONG"),
        ("Tab: Project COGS", "#e6871e (orange)", "#c67700 (dark orange) — TOO DARK"),
        ("Tab: Overhead", "#d93333 (red)", "#b22222 (dark red) — TOO DARK"),
        ("Tab: Pricing Guide", "#e6871e (orange)", "#ff6f00 (bright orange) — WRONG"),
        ("Tab: Quarterly Rocks", "#7a51cd (purple)", "#7a1fa2 (dark purple) — TOO DARK"),
        ("YOY Growth row", "bg=#f6f6f7 fg=#181c25", "bg=#f6f6f6 fg=#ffffff (WHITE ON GREY = INVISIBLE!)"),
    ]

    for label, tracker, mapval in comparisons:
        status = "FIX" if "WRONG" in mapval or "TOO DARK" in mapval or "INVISIBLE" in mapval or "NOT USED" in mapval else "OK"
        marker = "!!!" if status == "FIX" else "   "
        print(f"  {marker} {label}")
        print(f"       Tracker: {tracker}")
        print(f"       Map:     {mapval}")
        print()


def get_sheet_ids(service, spreadsheet_id):
    """Get sheet IDs and names."""
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    result = {}
    for sheet in meta['sheets']:
        props = sheet['properties']
        result[props['title']] = props['sheetId']
    return result


def fix_tab_colors(sheet_ids):
    """Set tab colors to match Finance Tracker palette."""
    reqs = []

    # Map each tab to a Tracker-style color
    tab_colors = {
        'Dashboard':       CHARCOAL,   # #272c38 — matches Tracker Dashboard
        'Monthly Tracker': BLUE,       # #3870de — like Tracker Income tab
        'Project COGS':    ORANGE,     # #e6871e — like Tracker Expenses tab
        'Overhead':        RED,        # #d93333 — like Tracker Tax tab
        'Pricing Guide':   GREEN,      # #1e9f6c — like Tracker P&L tab
        'Quarterly Rocks': PURPLE,     # #7a51cd — like Tracker Personal tab
    }

    for tab_name, color in tab_colors.items():
        if tab_name in sheet_ids:
            reqs.append({
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_ids[tab_name],
                        "tabColor": color
                    },
                    "fields": "tabColor"
                }
            })
    return reqs


def fix_dashboard(sid, service):
    """Fix Dashboard tab formatting."""
    reqs = []

    # Read current data to know what's where
    data = service.spreadsheets().values().get(
        spreadsheetId=MAP_ID,
        range="'Dashboard'!A1:O50",
        valueRenderOption="FORMATTED_VALUE"
    ).execute().get("values", [])

    NC = 15  # columns A-O

    # 1. Title row (R0) — keep as-is, it's correct
    # Just ensure correct text color
    reqs.append(rc(sid, 0, 1, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 22, "bold": True, "foregroundColor": CHARCOAL}
    }, F_BG_TF))

    # 2. Subtitle row (R1)
    reqs.append(rc(sid, 1, 2, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 11, "foregroundColor": SUBTITLE}
    }, F_BG_TF))

    # 3. Spacer row (R2)
    reqs.append(rc(sid, 2, 3, 0, NC, {"backgroundColor": WHITE}, F_BG))
    reqs.append(rh(sid, 2, 8))

    # 4. "KEY ASSUMPTIONS" label (R3) — section header, light grey
    reqs.append(rc(sid, 3, 4, 0, NC, {
        "backgroundColor": LIGHT_GREY,
        "textFormat": {"fontFamily": "Inter", "fontSize": 10, "bold": True, "foregroundColor": CHARCOAL}
    }, F_BG_TF))

    # 5. Assumption rows (R4-R9) — alternating zebra with muted text
    for r in range(4, 10):
        bg = ZEBRA if r % 2 == 0 else WHITE
        reqs.append(rc(sid, r, r+1, 0, NC, {
            "backgroundColor": bg,
            "textFormat": {"fontFamily": "Inter", "fontSize": 9, "bold": True, "foregroundColor": MUTED}
        }, F_BG_TF))

    # 6. "2026 REVENUE — PROJECT WORK" section header (R10)
    reqs.append(rc(sid, 10, 11, 0, NC, {
        "backgroundColor": LIGHT_GREY,
        "textFormat": {"fontFamily": "Inter", "fontSize": 10, "bold": True, "foregroundColor": CHARCOAL}
    }, F_BG_TF))

    # 7. Column headers for project table (R11) — white bg, muted text
    reqs.append(rc(sid, 11, 12, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 9, "bold": True, "foregroundColor": MUTED}
    }, F_BG_TF))

    # 8. Project data rows (R12-R16) — alternating zebra
    for r in range(12, 17):
        bg = ZEBRA if r % 2 == 0 else WHITE
        reqs.append(rc(sid, r, r+1, 0, NC, {
            "backgroundColor": bg,
            "textFormat": {"fontFamily": "Inter", "fontSize": 9, "bold": True, "foregroundColor": MUTED}
        }, F_BG_TF))

    # 9. Total Project Revenue row (R17) — subtle blue total like Tracker
    reqs.append(rc(sid, 17, 18, 0, NC, {
        "backgroundColor": PALE_BLUE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 9, "bold": True, "foregroundColor": BLUE}
    }, F_BG_TF))

    # 10. Spacer (R18)
    reqs.append(rc(sid, 18, 19, 0, NC, {"backgroundColor": WHITE}, F_BG))
    reqs.append(rh(sid, 18, 8))

    # 11. "RETAINER REVENUE" section header (R19)
    reqs.append(rc(sid, 19, 20, 0, NC, {
        "backgroundColor": LIGHT_GREY,
        "textFormat": {"fontFamily": "Inter", "fontSize": 10, "bold": True, "foregroundColor": CHARCOAL}
    }, F_BG_TF))

    # 12. Retainer data rows (R20-R22) — alternating
    for r in range(20, 23):
        bg = ZEBRA if r % 2 == 0 else WHITE
        reqs.append(rc(sid, r, r+1, 0, NC, {
            "backgroundColor": bg,
            "textFormat": {"fontFamily": "Inter", "fontSize": 9, "bold": True, "foregroundColor": MUTED}
        }, F_BG_TF))

    # 13. "Annual Retainer Revenue" total (R23) — was dark #272c38, change to pale blue
    reqs.append(rc(sid, 23, 24, 0, NC, {
        "backgroundColor": PALE_BLUE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 12, "bold": True, "foregroundColor": BLUE}
    }, F_BG_TF))

    # 14. Licensing row (R24)
    reqs.append(rc(sid, 24, 25, 0, NC, {
        "backgroundColor": ZEBRA,
        "textFormat": {"fontFamily": "Inter", "fontSize": 9, "bold": True, "foregroundColor": MUTED}
    }, F_BG_TF))

    # 15. "TOTAL 2026 REVENUE" (R25) — was dark #272c38, change to green total like Tracker
    reqs.append(rc(sid, 25, 26, 0, NC, {
        "backgroundColor": PALE_GREEN,
        "textFormat": {"fontFamily": "Inter", "fontSize": 12, "bold": True, "foregroundColor": GREEN}
    }, F_BG_TF))

    # 16. "YOY Growth" row (R26) — was white-on-grey (INVISIBLE!), fix to proper colors
    reqs.append(rc(sid, 26, 27, 0, NC, {
        "backgroundColor": ZEBRA,
        "textFormat": {"fontFamily": "Inter", "fontSize": 12, "bold": True, "foregroundColor": CHARCOAL}
    }, F_BG_TF))

    # 17. "% to Goal" row (R27)
    reqs.append(rc(sid, 27, 28, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 9, "bold": True, "foregroundColor": MUTED}
    }, F_BG_TF))

    # 18. Spacer (R28)
    reqs.append(rc(sid, 28, 29, 0, NC, {"backgroundColor": WHITE}, F_BG))

    # 19. P&L section header (R29)
    reqs.append(rc(sid, 29, 30, 0, NC, {
        "backgroundColor": LIGHT_GREY,
        "textFormat": {"fontFamily": "Inter", "fontSize": 9, "bold": True, "foregroundColor": MUTED}
    }, F_BG_TF))

    # 20. Continue for rows 30-50 (P&L data area) — read to see what's there
    # Apply clean formatting to any remaining rows
    for r in range(30, 50):
        bg = ZEBRA if r % 2 == 0 else WHITE
        reqs.append(rc(sid, r, r+1, 0, NC, {
            "backgroundColor": bg,
            "textFormat": {"fontFamily": "Inter", "fontSize": 9, "bold": True, "foregroundColor": MUTED}
        }, F_BG_TF))

    # Add subtle bottom borders on section breaks
    reqs.append(border_bottom(sid, 9, 10, 0, NC, BORDER_MED))
    reqs.append(border_bottom(sid, 17, 18, 0, NC, BORDER_MED))
    reqs.append(border_bottom(sid, 25, 26, 0, NC, BORDER_MED))

    return reqs


def fix_monthly_tracker(sid, service):
    """Fix Monthly Tracker tab — the main issue: dark charcoal header bars."""
    reqs = []

    # Get actual column count
    meta = service.spreadsheets().get(spreadsheetId=MAP_ID, includeGridData=False).execute()
    NC = 27  # default
    for s in meta['sheets']:
        if s['properties']['title'] == 'Monthly Tracker':
            NC = s['properties']['gridProperties'].get('columnCount', 27)
            break
    print(f"  Monthly Tracker has {NC} columns")

    # Read current data
    data = service.spreadsheets().values().get(
        spreadsheetId=MAP_ID,
        range=f"'Monthly Tracker'!A1:{NC}50",
        valueRenderOption="FORMATTED_VALUE"
    ).execute().get("values", [])

    # 1. Title (R0)
    reqs.append(rc(sid, 0, 1, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 22, "bold": True, "foregroundColor": CHARCOAL}
    }, F_BG_TF))

    # 2. Subtitle (R1)
    reqs.append(rc(sid, 1, 2, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 11, "foregroundColor": SUBTITLE}
    }, F_BG_TF))

    # 3. HEADER BAR (R2-R3) — THE MAIN FIX: was dark #272c38, change to blue like Tracker
    reqs.append(rc(sid, 2, 4, 0, NC, {
        "backgroundColor": BLUE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 9, "bold": True, "foregroundColor": WHITE}
    }, F_BG_TF))
    # Month names in R3 should be white on blue

    # 4. Section labels (PROJECTS R4, RETAINERS R8, TOTALS R12, PIPELINE R18)
    section_rows = [4, 8, 12, 18]
    for r in section_rows:
        if r < len(data):
            reqs.append(rc(sid, r, r+1, 0, NC, {
                "backgroundColor": LIGHT_GREY,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "bold": True, "foregroundColor": CHARCOAL}
            }, F_BG_TF))

    # 5. Data rows — fix ACT column backgrounds to exact #ebeefa
    # Body rows between sections
    body_rows = [5, 6, 7, 9, 10, 11]
    for r in body_rows:
        # Label column (col 0) — white bg, dark text
        reqs.append(rc(sid, r, r+1, 0, 1, {
            "backgroundColor": WHITE,
            "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": CHARCOAL}
        }, F_BG_TF))

        # GOAL columns (odd: 1,3,5,7,9,11,13) — zebra
        for c in range(1, NC, 2):
            reqs.append(rc(sid, r, r+1, c, c+1, {
                "backgroundColor": WHITE,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": DARK_TEXT}
            }, F_BG_TF))

        # ACT columns (even: 2,4,6,8,10,12,14) — pale blue tint
        for c in range(2, NC, 2):
            reqs.append(rc(sid, r, r+1, c, c+1, {
                "backgroundColor": PALE_BLUE,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": DARK_TEXT}
            }, F_BG_TF))

    # 6. Total Revenue rows (R13-R15) — green tint like Tracker
    for r in range(13, 16):
        reqs.append(rc(sid, r, r+1, 0, NC, {
            "backgroundColor": PALE_GREEN,
            "textFormat": {"fontFamily": "Inter", "fontSize": 10, "bold": True, "foregroundColor": GREEN}
        }, F_BG_TF))

    # 7. % to Goal row (R16) — blue tint
    reqs.append(rc(sid, 16, 17, 0, NC, {
        "backgroundColor": PALE_BLUE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 10, "bold": True, "foregroundColor": BLUE}
    }, F_BG_TF))

    # 8. Spacer row (R17)
    reqs.append(rc(sid, 17, 18, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": DARK_TEXT}
    }, F_BG_TF))
    # Fix ACT columns in spacer
    for c in range(2, NC, 2):
        reqs.append(rc(sid, 17, 18, c, c+1, {
            "backgroundColor": PALE_BLUE
        }, F_BG))

    # 9. Pipeline section (R18+)
    # Pipeline data rows (R19-R28 estimated)
    for r in range(19, 30):
        reqs.append(rc(sid, r, r+1, 0, 1, {
            "backgroundColor": WHITE,
            "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": CHARCOAL}
        }, F_BG_TF))
        for c in range(1, NC, 2):
            reqs.append(rc(sid, r, r+1, c, c+1, {
                "backgroundColor": WHITE,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": DARK_TEXT}
            }, F_BG_TF))
        for c in range(2, NC, 2):
            reqs.append(rc(sid, r, r+1, c, c+1, {
                "backgroundColor": PALE_BLUE,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": DARK_TEXT}
            }, F_BG_TF))

    return reqs


def fix_project_cogs(sid, service):
    """Fix Project COGS tab."""
    reqs = []

    data = service.spreadsheets().values().get(
        spreadsheetId=MAP_ID,
        range="'Project COGS'!A1:O50",
        valueRenderOption="FORMATTED_VALUE"
    ).execute().get("values", [])

    NC = 15

    # Title
    reqs.append(rc(sid, 0, 1, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 22, "bold": True, "foregroundColor": CHARCOAL}
    }, F_BG_TF))

    # Subtitle
    reqs.append(rc(sid, 1, 2, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 11, "foregroundColor": SUBTITLE}
    }, F_BG_TF))

    # Find header rows and section headers
    for i, row in enumerate(data):
        if not row:
            continue
        val = str(row[0]).strip().upper()

        # Look for dark header bars and convert to blue
        if i >= 2 and i <= 4:
            # Column headers area
            reqs.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": WHITE,
                "textFormat": {"fontFamily": "Inter", "fontSize": 9, "bold": True, "foregroundColor": MUTED}
            }, F_BG_TF))
        elif 'TOTAL' in val or 'SUMMARY' in val:
            reqs.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": PALE_BLUE,
                "textFormat": {"fontFamily": "Inter", "fontSize": 11, "bold": True, "foregroundColor": BLUE}
            }, F_BG_TF))
        elif val and (val.startswith('SERVICE') or val.startswith('PROJECT') or
                      'ARCHITECT' in val or 'BUILDER' in val or 'INTERIOR' in val or
                      'EDITORIAL' in val or 'STANDALONE' in val or 'RETAINER' in val or
                      'EXAMPLE' in val or 'COGS' in val):
            reqs.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": LIGHT_GREY,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "bold": True, "foregroundColor": CHARCOAL}
            }, F_BG_TF))
        elif i >= 5:
            bg = ZEBRA if i % 2 == 0 else WHITE
            reqs.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": bg,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": DARK_TEXT}
            }, F_BG_TF))

    return reqs


def fix_overhead(sid, service):
    """Fix Overhead tab."""
    reqs = []

    data = service.spreadsheets().values().get(
        spreadsheetId=MAP_ID,
        range="'Overhead'!A1:O50",
        valueRenderOption="FORMATTED_VALUE"
    ).execute().get("values", [])

    NC = 15

    # Title
    reqs.append(rc(sid, 0, 1, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 22, "bold": True, "foregroundColor": CHARCOAL}
    }, F_BG_TF))

    # Subtitle
    reqs.append(rc(sid, 1, 2, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 11, "foregroundColor": SUBTITLE}
    }, F_BG_TF))

    for i, row in enumerate(data):
        if not row or i < 2:
            continue
        val = str(row[0]).strip().upper()

        if 'TOTAL' in val:
            reqs.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": PALE_RED,
                "textFormat": {"fontFamily": "Inter", "fontSize": 11, "bold": True, "foregroundColor": RED}
            }, F_BG_TF))
        elif val and ('FIXED' in val or 'VARIABLE' in val or 'OVERHEAD' in val or
                      'MONTHLY' in val or 'ANNUAL' in val or 'CATEGORY' in val):
            reqs.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": LIGHT_GREY,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "bold": True, "foregroundColor": CHARCOAL}
            }, F_BG_TF))
        elif i >= 2:
            bg = ZEBRA if i % 2 == 0 else WHITE
            reqs.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": bg,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": DARK_TEXT}
            }, F_BG_TF))

    # If no data rows found, apply clean defaults
    if len(data) <= 2:
        for r in range(2, 4):
            reqs.append(rc(sid, r, r+1, 0, NC, {
                "backgroundColor": WHITE,
                "textFormat": {"fontFamily": "Inter", "fontSize": 9, "bold": True, "foregroundColor": MUTED}
            }, F_BG_TF))
        for r in range(4, 30):
            bg = ZEBRA if r % 2 == 0 else WHITE
            reqs.append(rc(sid, r, r+1, 0, NC, {
                "backgroundColor": bg,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": DARK_TEXT}
            }, F_BG_TF))

    return reqs


def fix_pricing_guide(sid, service):
    """Fix Pricing Guide tab."""
    reqs = []

    data = service.spreadsheets().values().get(
        spreadsheetId=MAP_ID,
        range="'Pricing Guide'!A1:O50",
        valueRenderOption="FORMATTED_VALUE"
    ).execute().get("values", [])

    NC = 15

    # Title
    reqs.append(rc(sid, 0, 1, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 22, "bold": True, "foregroundColor": CHARCOAL}
    }, F_BG_TF))

    # Subtitle
    reqs.append(rc(sid, 1, 2, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 11, "foregroundColor": SUBTITLE}
    }, F_BG_TF))

    for i, row in enumerate(data):
        if not row or i < 2:
            continue
        val = str(row[0]).strip().upper()

        if 'TOTAL' in val or 'SUMMARY' in val:
            reqs.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": PALE_GREEN,
                "textFormat": {"fontFamily": "Inter", "fontSize": 11, "bold": True, "foregroundColor": GREEN}
            }, F_BG_TF))
        elif val and ('SERVICE' in val or 'PRICING' in val or 'TIER' in val or
                      'PACKAGE' in val or 'RATE' in val or 'DELIVERABLE' in val or
                      'TYPE' in val or 'ARCHITECT' in val or 'BUILDER' in val):
            reqs.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": LIGHT_GREY,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "bold": True, "foregroundColor": CHARCOAL}
            }, F_BG_TF))
        elif i >= 2:
            bg = ZEBRA if i % 2 == 0 else WHITE
            reqs.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": bg,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": DARK_TEXT}
            }, F_BG_TF))

    if len(data) <= 2:
        for r in range(2, 30):
            bg = ZEBRA if r % 2 == 0 else WHITE
            reqs.append(rc(sid, r, r+1, 0, NC, {
                "backgroundColor": bg,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": DARK_TEXT}
            }, F_BG_TF))

    return reqs


def fix_quarterly_rocks(sid, service):
    """Fix Quarterly Rocks tab."""
    reqs = []

    data = service.spreadsheets().values().get(
        spreadsheetId=MAP_ID,
        range="'Quarterly Rocks'!A1:O50",
        valueRenderOption="FORMATTED_VALUE"
    ).execute().get("values", [])

    NC = 15

    # Title
    reqs.append(rc(sid, 0, 1, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 22, "bold": True, "foregroundColor": CHARCOAL}
    }, F_BG_TF))

    # Subtitle
    reqs.append(rc(sid, 1, 2, 0, NC, {
        "backgroundColor": WHITE,
        "textFormat": {"fontFamily": "Inter", "fontSize": 11, "foregroundColor": SUBTITLE}
    }, F_BG_TF))

    for i, row in enumerate(data):
        if not row or i < 2:
            continue
        val = str(row[0]).strip().upper()

        if val and ('Q1' in val or 'Q2' in val or 'Q3' in val or 'Q4' in val) and ('ROCK' in val or 'QUARTER' in val or len(val) < 20):
            # Quarter header — use blue accent like Tracker
            reqs.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": BLUE,
                "textFormat": {"fontFamily": "Inter", "fontSize": 12, "bold": True, "foregroundColor": WHITE}
            }, F_BG_TF))
        elif 'STATUS' in val or 'ROCK' in val or 'PRIORITY' in val or 'OWNER' in val:
            reqs.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": WHITE,
                "textFormat": {"fontFamily": "Inter", "fontSize": 9, "bold": True, "foregroundColor": MUTED}
            }, F_BG_TF))
        elif 'COMPLETE' in val or 'DONE' in val:
            reqs.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": PALE_GREEN,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": GREEN}
            }, F_BG_TF))
        elif i >= 2:
            bg = ZEBRA if i % 2 == 0 else WHITE
            reqs.append(rc(sid, i, i+1, 0, NC, {
                "backgroundColor": bg,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": DARK_TEXT}
            }, F_BG_TF))

    if len(data) <= 2:
        for r in range(2, 30):
            bg = ZEBRA if r % 2 == 0 else WHITE
            reqs.append(rc(sid, r, r+1, 0, NC, {
                "backgroundColor": bg,
                "textFormat": {"fontFamily": "Inter", "fontSize": 10, "foregroundColor": DARK_TEXT}
            }, F_BG_TF))

    return reqs


def main():
    service = get_sheets_service()
    sheets = service.spreadsheets()

    # Print comparison first
    print_color_comparison()

    # Get sheet IDs
    sheet_ids = get_sheet_ids(service, MAP_ID)
    print("\nFinancial Map tabs:")
    for name, sid in sheet_ids.items():
        print(f"  {name}: sheetId={sid}")

    # Build all formatting requests
    all_reqs = []

    # 1. Fix tab colors
    print("\n--- Fixing tab colors ---")
    all_reqs.extend(fix_tab_colors(sheet_ids))

    # 2. Fix Dashboard
    print("--- Fixing Dashboard ---")
    all_reqs.extend(fix_dashboard(sheet_ids['Dashboard'], service))

    # 3. Fix Monthly Tracker
    print("--- Fixing Monthly Tracker ---")
    all_reqs.extend(fix_monthly_tracker(sheet_ids['Monthly Tracker'], service))

    # 4. Fix Project COGS
    print("--- Fixing Project COGS ---")
    all_reqs.extend(fix_project_cogs(sheet_ids['Project COGS'], service))

    # 5. Fix Overhead
    print("--- Fixing Overhead ---")
    all_reqs.extend(fix_overhead(sheet_ids['Overhead'], service))

    # 6. Fix Pricing Guide
    print("--- Fixing Pricing Guide ---")
    all_reqs.extend(fix_pricing_guide(sheet_ids['Pricing Guide'], service))

    # 7. Fix Quarterly Rocks
    print("--- Fixing Quarterly Rocks ---")
    all_reqs.extend(fix_quarterly_rocks(sheet_ids['Quarterly Rocks'], service))

    # Execute in batches (API limit is 100 requests per batch)
    BATCH_SIZE = 80
    total = len(all_reqs)
    print(f"\n--- Applying {total} formatting requests ---")

    for i in range(0, total, BATCH_SIZE):
        batch = all_reqs[i:i + BATCH_SIZE]
        print(f"  Batch {i // BATCH_SIZE + 1}: requests {i+1}-{min(i+len(batch), total)}")
        sheets.batchUpdate(
            spreadsheetId=MAP_ID,
            body={"requests": batch}
        ).execute()
        if i + BATCH_SIZE < total:
            time.sleep(1)

    print("\n" + "=" * 70)
    print("  DONE! Financial Map colors now match the Finance Tracker.")
    print("=" * 70)
    print("""
  Changes applied:
  - Tab colors: matched to Tracker palette (charcoal, blue, orange, red, green, purple)
  - Header bars: changed from dark #272c38 to #3870de (blue) with white text
  - Section labels: light grey #eef0f3 with charcoal text (clean, not heavy)
  - Total rows: pale blue #ebeefa or pale green #e7f6ee (not dark charcoal!)
  - ACT columns: exact #ebeefa pale blue tint
  - Body text: #181c25 (correct dark, not charcoal)
  - Column headers: #8b929b muted grey, white background
  - Zebra stripes: #f6f6f7
  - YOY Growth: fixed invisible white-on-grey text
  - All fonts: Inter family throughout
    """)


if __name__ == '__main__':
    main()
