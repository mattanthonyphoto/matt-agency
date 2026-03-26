from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import string

creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/spreadsheets'])
service = build('sheets', 'v4', credentials=creds)
SHEET_ID = '1nrzAfXzRiFIQpa85one6iuMXASIBbgPrwDoI6TwH9KU'

def rgb(hex_color):
    h = hex_color.lstrip('#')
    return {'red': int(h[0:2],16)/255, 'green': int(h[2:4],16)/255, 'blue': int(h[4:6],16)/255}

WHITE = rgb('#ffffff')
ZEBRA = rgb('#f8f9fa')
SECTION_BG = rgb('#f0f1f3')
TOTAL_BG = rgb('#ebeefa')
HEADER_BG = rgb('#272c38')
CHARCOAL = rgb('#272c38')
BODY_TEXT = rgb('#3a3f47')
MUTED = rgb('#8b929b')
SUBTLE_BLUE = rgb('#f5f7ff')

requests = []

# ============================================================
# 1. QUARTERLY ROCKS (gid=1620953837) — biggest problem
# Every data row is dark charcoal. Fix all to proper alternating.
# ============================================================
sid = 1620953837
print("Fixing Quarterly Rocks...")

# Row 1: title (44px) - keep
# Row 2: spacer (12px -> 10px)  
# Row 3: column headers (34px) - keep dark header
# Row 4: Q1 quarter header (32px) - make section header style
# Rows 5-12: Q1 data - alternate white/zebra
# Row 13: spacer
# Row 14: Q2 quarter header - section header
# Rows 15-22: Q2 data
# Row 23: spacer
# Row 24: Q3 quarter header
# Rows 25-31: Q3 data
# Row 32: spacer
# Row 33: Q4 quarter header
# Rows 34-39: Q4 data

quarter_headers = [3, 13, 23, 32]  # 0-indexed (rows 4, 14, 24, 33)
spacer_rows = [1, 12, 22, 31, 39]  # 0-indexed
header_row = 2  # row 3, keep dark

# Fix quarter header rows — light section style
for r in quarter_headers:
    requests.append({
        'repeatCell': {
            'range': {'sheetId': sid, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 0, 'endColumnIndex': 6},
            'cell': {'userEnteredFormat': {
                'backgroundColor': SECTION_BG,
                'textFormat': {'fontFamily': 'Inter', 'fontSize': 11, 'bold': True, 'foregroundColor': CHARCOAL}
            }},
            'fields': 'userEnteredFormat(backgroundColor,textFormat)'
        }
    })

# Fix ALL data rows — alternate white/zebra
data_rows = list(range(4, 12)) + list(range(14, 22)) + list(range(24, 31)) + list(range(33, 39))
for i, r in enumerate(data_rows):
    bg = ZEBRA if i % 2 == 0 else WHITE
    requests.append({
        'repeatCell': {
            'range': {'sheetId': sid, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 0, 'endColumnIndex': 6},
            'cell': {'userEnteredFormat': {
                'backgroundColor': bg,
                'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'bold': False, 'foregroundColor': BODY_TEXT}
            }},
            'fields': 'userEnteredFormat(backgroundColor,textFormat)'
        }
    })

# Row heights for Quarterly Rocks
row_heights_qr = {0: 44, 1: 10, 2: 34}
for r in quarter_headers:
    row_heights_qr[r] = 32
for r in spacer_rows:
    row_heights_qr[r] = 10
for r in data_rows:
    row_heights_qr[r] = 30

for r, h in row_heights_qr.items():
    requests.append({
        'updateDimensionProperties': {
            'range': {'sheetId': sid, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
            'properties': {'pixelSize': h},
            'fields': 'pixelSize'
        }
    })

# Spacer rows — clear formatting
for r in spacer_rows:
    requests.append({
        'repeatCell': {
            'range': {'sheetId': sid, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 0, 'endColumnIndex': 6},
            'cell': {'userEnteredFormat': {'backgroundColor': WHITE}},
            'fields': 'userEnteredFormat(backgroundColor)'
        }
    })

# Collapse extra columns (G onward)
requests.append({
    'updateDimensionProperties': {
        'range': {'sheetId': sid, 'dimension': 'COLUMNS', 'startIndex': 6, 'endIndex': 26},
        'properties': {'pixelSize': 20},
        'fields': 'pixelSize'
    }
})

# ============================================================
# 2. MONTHLY TRACKER (gid=845249983) — inverted row heights
# ============================================================
sid_mt = 845249983
print("Fixing Monthly Tracker...")

# The problem: section headers are 12px, spacers are 28-34px
# Fix row heights based on content:
mt_heights = {
    0: 44,   # title
    1: 24,   # subtitle
    2: 24,   # GOAL/ACT labels (was 12px!)
    3: 30,   # Month names (was 28px)
    4: 10,   # spacer (was 34px!)
    5: 30,   # PROJECTS section header (was 12px!)
    6: 28,   # Projects Completed
    7: 10,   # spacer (was 28px!)
    8: 28,   # Project Revenue (was 21px!)
    9: 10,   # spacer (was 32px!)
    10: 30,  # RETAINERS section header (was 12px!)
    11: 28,  # Active Retainer Clients
    12: 10,  # spacer (was 28px!)
    13: 28,  # Retainer Revenue (was 22px!)
    14: 28,  # Image Licensing Revenue
    15: 10,  # spacer (was 28px!)
    16: 30,  # TOTALS section header (was 12px!)
    17: 30,  # Total Revenue
    18: 10,  # spacer (was 32px!)
    19: 28,  # Cumulative Goal (was 12px!)
    20: 28,  # Cumulative Actual
    21: 28,  # % to Goal
    22: 10,  # spacer (was 28px!)
    23: 30,  # PIPELINE section header (was 12px!)
    24: 28,  # Qualified Leads
    25: 28,  # Discovery Calls
    26: 28,  # Proposals Sent
    27: 28,  # Close Rate
    28: 28,  # Cost-Share
    29: 30,  # PROFIT-PER-PROJECT section header
    30: 28,  # Avg Revenue
    31: 28,  # Licensing Deals
}

for r, h in mt_heights.items():
    requests.append({
        'updateDimensionProperties': {
            'range': {'sheetId': sid_mt, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
            'properties': {'pixelSize': h},
            'fields': 'pixelSize'
        }
    })

# Spacer rows in Monthly Tracker — clear to white
mt_spacers = [4, 7, 9, 12, 15, 18, 22]
for r in mt_spacers:
    requests.append({
        'repeatCell': {
            'range': {'sheetId': sid_mt, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 0, 'endColumnIndex': 27},
            'cell': {'userEnteredFormat': {'backgroundColor': WHITE, 'borders': {
                'top': {'style': 'NONE'}, 'bottom': {'style': 'NONE'},
                'left': {'style': 'NONE'}, 'right': {'style': 'NONE'}
            }}},
            'fields': 'userEnteredFormat(backgroundColor,borders)'
        }
    })

# Collapse trailing empty rows in Monthly Tracker
for r in range(32, 50):
    requests.append({
        'updateDimensionProperties': {
            'range': {'sheetId': sid_mt, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
            'properties': {'pixelSize': 6},
            'fields': 'pixelSize'
        }
    })

# ============================================================
# 3. OVERHEAD (gid=7683076) — Row 6 dark charcoal fix
# ============================================================
sid_oh = 7683076
print("Fixing Overhead...")

# Row 6 (index 5) "Instantly" has dark bg — fix to white (it's an odd row, no zebra)
requests.append({
    'repeatCell': {
        'range': {'sheetId': sid_oh, 'startRowIndex': 5, 'endRowIndex': 6, 'startColumnIndex': 0, 'endColumnIndex': 3},
        'cell': {'userEnteredFormat': {
            'backgroundColor': WHITE,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'bold': False, 'foregroundColor': BODY_TEXT}
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat)'
    }
})

# Fix column B width (250 is too wide for just dollar amounts)
requests.append({
    'updateDimensionProperties': {
        'range': {'sheetId': sid_oh, 'dimension': 'COLUMNS', 'startIndex': 1, 'endIndex': 2},
        'properties': {'pixelSize': 120},
        'fields': 'pixelSize'
    }
})

# Collapse extra columns D onward
requests.append({
    'updateDimensionProperties': {
        'range': {'sheetId': sid_oh, 'dimension': 'COLUMNS', 'startIndex': 3, 'endIndex': 26},
        'properties': {'pixelSize': 20},
        'fields': 'pixelSize'
    }
})

# Collapse trailing empty rows
for r in range(47, 55):
    requests.append({
        'updateDimensionProperties': {
            'range': {'sheetId': sid_oh, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
            'properties': {'pixelSize': 6},
            'fields': 'pixelSize'
        }
    })

# ============================================================
# 4. PRICING GUIDE (gid=655418673) — Row 7 dark charcoal
# ============================================================
sid_pg = 655418673
print("Fixing Pricing Guide...")

# Row 7 (index 6) "Architectural Project" has dark bg — fix to zebra
requests.append({
    'repeatCell': {
        'range': {'sheetId': sid_pg, 'startRowIndex': 6, 'endRowIndex': 7, 'startColumnIndex': 0, 'endColumnIndex': 5},
        'cell': {'userEnteredFormat': {
            'backgroundColor': ZEBRA,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'bold': False, 'foregroundColor': BODY_TEXT}
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat)'
    }
})

# Collapse extra columns F onward
requests.append({
    'updateDimensionProperties': {
        'range': {'sheetId': sid_pg, 'dimension': 'COLUMNS', 'startIndex': 5, 'endIndex': 26},
        'properties': {'pixelSize': 20},
        'fields': 'pixelSize'
    }
})

# Collapse trailing empty rows
for r in range(34, 55):
    requests.append({
        'updateDimensionProperties': {
            'range': {'sheetId': sid_pg, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
            'properties': {'pixelSize': 6},
            'fields': 'pixelSize'
        }
    })

# ============================================================
# 5. PROJECT COGS (gid=865779075) — collapse extra columns
# ============================================================
sid_cogs = 865779075
print("Fixing Project COGS...")

requests.append({
    'updateDimensionProperties': {
        'range': {'sheetId': sid_cogs, 'dimension': 'COLUMNS', 'startIndex': 6, 'endIndex': 26},
        'properties': {'pixelSize': 20},
        'fields': 'pixelSize'
    }
})

# Collapse trailing empty rows
for r in range(34, 55):
    requests.append({
        'updateDimensionProperties': {
            'range': {'sheetId': sid_cogs, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
            'properties': {'pixelSize': 6},
            'fields': 'pixelSize'
        }
    })

# ============================================================
# 6. DASHBOARD (gid=378592626) — collapse extras, fix spacing
# ============================================================
sid_dash = 378592626
print("Fixing Dashboard...")

# Collapse extra columns G onward (already 20px but some might not be)
requests.append({
    'updateDimensionProperties': {
        'range': {'sheetId': sid_dash, 'dimension': 'COLUMNS', 'startIndex': 6, 'endIndex': 26},
        'properties': {'pixelSize': 20},
        'fields': 'pixelSize'
    }
})

# Spacer rows (3, 19, 27, 30, 33, 37, 45, 50) — make them 10px
dash_spacers = [2, 18, 26, 29, 32, 36, 44, 49]
for r in dash_spacers:
    requests.append({
        'updateDimensionProperties': {
            'range': {'sheetId': sid_dash, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
            'properties': {'pixelSize': 10},
            'fields': 'pixelSize'
        }
    })

# ============================================================
# EXECUTE
# ============================================================
print(f"Sending {len(requests)} requests...")
service.spreadsheets().batchUpdate(
    spreadsheetId=SHEET_ID,
    body={'requests': requests}
).execute()
print("Done!")
