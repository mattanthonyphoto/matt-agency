from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/spreadsheets'])
service = build('sheets', 'v4', credentials=creds)
SHEET_ID = '1nrzAfXzRiFIQpa85one6iuMXASIBbgPrwDoI6TwH9KU'

def rgb(h):
    h = h.lstrip('#')
    return {'red': int(h[0:2],16)/255, 'green': int(h[2:4],16)/255, 'blue': int(h[4:6],16)/255}

WHITE = rgb('#ffffff')
CHARCOAL = rgb('#272c38')
BODY = rgb('#3a3f47')
MUTED = rgb('#8b929b')
ZEBRA = rgb('#f8f9fa')
BORDER_LIGHT = rgb('#e1e4e7')
BORDER_MED = rgb('#d1d3d7')

BLUE = rgb('#3870de')
GREEN = rgb('#1e9f6c')
ORANGE = rgb('#e6871e')
RED = rgb('#d93333')
PURPLE = rgb('#7a51cd')

BLUE_BG = rgb('#ebeefa')
GREEN_BG = rgb('#e7f6ee')
ORANGE_BG = rgb('#fef3e5')
RED_BG = rgb('#fcecec')
PURPLE_BG = rgb('#f3eefa')

requests = []

def add_title(sid, row, height=52):
    """Title row — 18pt bold charcoal"""
    requests.append({'updateDimensionProperties': {
        'range': {'sheetId': sid, 'dimension': 'ROWS', 'startIndex': row, 'endIndex': row+1},
        'properties': {'pixelSize': height}, 'fields': 'pixelSize'
    }})

def add_subtitle(sid, row, cols, height=28):
    requests.append({'updateDimensionProperties': {
        'range': {'sheetId': sid, 'dimension': 'ROWS', 'startIndex': row, 'endIndex': row+1},
        'properties': {'pixelSize': height}, 'fields': 'pixelSize'
    }})
    requests.append({'repeatCell': {
        'range': {'sheetId': sid, 'startRowIndex': row, 'endRowIndex': row+1, 'startColumnIndex': 0, 'endColumnIndex': cols},
        'cell': {'userEnteredFormat': {
            'backgroundColor': WHITE,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'foregroundColor': MUTED},
            'verticalAlignment': 'MIDDLE'
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment)'
    }})

def add_spacer(sid, row, cols, height=16):
    requests.append({'updateDimensionProperties': {
        'range': {'sheetId': sid, 'dimension': 'ROWS', 'startIndex': row, 'endIndex': row+1},
        'properties': {'pixelSize': height}, 'fields': 'pixelSize'
    }})
    requests.append({'repeatCell': {
        'range': {'sheetId': sid, 'startRowIndex': row, 'endRowIndex': row+1, 'startColumnIndex': 0, 'endColumnIndex': cols},
        'cell': {'userEnteredFormat': {
            'backgroundColor': WHITE,
            'borders': {'top': {'style': 'NONE'}, 'bottom': {'style': 'NONE'}, 'left': {'style': 'NONE'}, 'right': {'style': 'NONE'}}
        }},
        'fields': 'userEnteredFormat(backgroundColor,borders)'
    }})

def add_col_header(sid, row, cols, height=36):
    requests.append({'updateDimensionProperties': {
        'range': {'sheetId': sid, 'dimension': 'ROWS', 'startIndex': row, 'endIndex': row+1},
        'properties': {'pixelSize': height}, 'fields': 'pixelSize'
    }})
    requests.append({'repeatCell': {
        'range': {'sheetId': sid, 'startRowIndex': row, 'endRowIndex': row+1, 'startColumnIndex': 0, 'endColumnIndex': cols},
        'cell': {'userEnteredFormat': {
            'backgroundColor': CHARCOAL,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 9, 'bold': True, 'foregroundColor': WHITE},
            'verticalAlignment': 'MIDDLE',
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment)'
    }})

def add_container(sid, section_header_row, data_rows, cols, accent, accent_bg):
    """Apply the Quarterly Rocks container pattern to a section"""
    # Section header
    requests.append({'updateDimensionProperties': {
        'range': {'sheetId': sid, 'dimension': 'ROWS', 'startIndex': section_header_row, 'endIndex': section_header_row+1},
        'properties': {'pixelSize': 38}, 'fields': 'pixelSize'
    }})
    requests.append({'repeatCell': {
        'range': {'sheetId': sid, 'startRowIndex': section_header_row, 'endRowIndex': section_header_row+1, 'startColumnIndex': 0, 'endColumnIndex': cols},
        'cell': {'userEnteredFormat': {
            'backgroundColor': accent_bg,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 11, 'bold': True, 'foregroundColor': CHARCOAL},
            'verticalAlignment': 'MIDDLE',
            'borders': {
                'left': {'style': 'SOLID_THICK', 'color': accent},
                'top': {'style': 'SOLID', 'color': BORDER_LIGHT},
                'bottom': {'style': 'SOLID', 'color': BORDER_LIGHT},
                'right': {'style': 'SOLID', 'color': BORDER_LIGHT},
            }
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment,borders)'
    }})
    
    # Data rows
    for i, r in enumerate(data_rows):
        bg = ZEBRA if i % 2 == 0 else WHITE
        requests.append({'updateDimensionProperties': {
            'range': {'sheetId': sid, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
            'properties': {'pixelSize': 34}, 'fields': 'pixelSize'
        }})
        requests.append({'repeatCell': {
            'range': {'sheetId': sid, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 0, 'endColumnIndex': cols},
            'cell': {'userEnteredFormat': {
                'backgroundColor': bg,
                'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'bold': False, 'foregroundColor': BODY},
                'verticalAlignment': 'MIDDLE',
                'borders': {
                    'left': {'style': 'SOLID_THICK', 'color': accent},
                    'bottom': {'style': 'SOLID', 'color': BORDER_LIGHT},
                    'right': {'style': 'SOLID', 'color': BORDER_LIGHT},
                }
            }},
            'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment,borders)'
        }})
    
    # Close container — heavier bottom border on last row
    if data_rows:
        last = data_rows[-1]
        requests.append({'repeatCell': {
            'range': {'sheetId': sid, 'startRowIndex': last, 'endRowIndex': last+1, 'startColumnIndex': 0, 'endColumnIndex': cols},
            'cell': {'userEnteredFormat': {
                'borders': {
                    'left': {'style': 'SOLID_THICK', 'color': accent},
                    'bottom': {'style': 'SOLID_MEDIUM', 'color': BORDER_MED},
                    'right': {'style': 'SOLID', 'color': BORDER_LIGHT},
                }
            }},
            'fields': 'userEnteredFormat(borders)'
        }})

def add_total_row(sid, row, cols, accent):
    """Styled total/summary row"""
    requests.append({'updateDimensionProperties': {
        'range': {'sheetId': sid, 'dimension': 'ROWS', 'startIndex': row, 'endIndex': row+1},
        'properties': {'pixelSize': 36}, 'fields': 'pixelSize'
    }})
    requests.append({'repeatCell': {
        'range': {'sheetId': sid, 'startRowIndex': row, 'endRowIndex': row+1, 'startColumnIndex': 0, 'endColumnIndex': cols},
        'cell': {'userEnteredFormat': {
            'backgroundColor': WHITE,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 11, 'bold': True, 'foregroundColor': CHARCOAL},
            'verticalAlignment': 'MIDDLE',
            'borders': {
                'left': {'style': 'SOLID_THICK', 'color': accent},
                'top': {'style': 'SOLID_MEDIUM', 'color': accent},
                'bottom': {'style': 'SOLID_MEDIUM', 'color': accent},
                'right': {'style': 'SOLID', 'color': BORDER_LIGHT},
            }
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment,borders)'
    }})

# ============================================================
# DASHBOARD (gid=378592626) — 6 columns (A-F)
# ============================================================
print("Dashboard...")
D = 378592626
DCOLS = 6

add_title(D, 0)
add_subtitle(D, 1, DCOLS)
# Row 3 (idx 2) KEY ASSUMPTIONS section header
add_container(D, 2, [3,4,5,6,7,8], DCOLS, BLUE, BLUE_BG)
add_spacer(D, 9, DCOLS)
# Row 10 (idx 9) -> actually row 10 is "2026 REVENUE" label, row 11 is col header
# Sections: Revenue project work
add_container(D, 9, [], DCOLS, BLUE, BLUE_BG)  # just the section header for "2026 REVENUE"
add_col_header(D, 10, DCOLS)  # Revenue Stream | # Projects...
# Data rows 12-16 (idx 11-15)
for i, r in enumerate(range(11, 16)):
    bg = ZEBRA if i % 2 == 0 else WHITE
    requests.append({'updateDimensionProperties': {
        'range': {'sheetId': D, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
        'properties': {'pixelSize': 34}, 'fields': 'pixelSize'
    }})
    requests.append({'repeatCell': {
        'range': {'sheetId': D, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 0, 'endColumnIndex': DCOLS},
        'cell': {'userEnteredFormat': {
            'backgroundColor': bg,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'bold': False, 'foregroundColor': BODY},
            'verticalAlignment': 'MIDDLE',
            'borders': {
                'left': {'style': 'SOLID_THICK', 'color': BLUE},
                'bottom': {'style': 'SOLID', 'color': BORDER_LIGHT},
                'right': {'style': 'SOLID', 'color': BORDER_LIGHT},
            }
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment,borders)'
    }})
add_total_row(D, 16, DCOLS, BLUE)  # Total Project Revenue
add_spacer(D, 17, DCOLS)

# RETAINER REVENUE (row 19 idx 18)
add_container(D, 18, [19,20,21,22,23], DCOLS, GREEN, GREEN_BG)
add_spacer(D, 17, DCOLS)

# TOTAL 2026 REVENUE (row 25 idx 24)
add_total_row(D, 24, DCOLS, GREEN)
add_spacer(D, 25, DCOLS)

# YOY Growth + % to Goal (rows 27-28, idx 26-27)
for i, r in enumerate([26, 27]):
    bg = ZEBRA if i % 2 == 0 else WHITE
    requests.append({'updateDimensionProperties': {
        'range': {'sheetId': D, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
        'properties': {'pixelSize': 30}, 'fields': 'pixelSize'
    }})
    requests.append({'repeatCell': {
        'range': {'sheetId': D, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 0, 'endColumnIndex': DCOLS},
        'cell': {'userEnteredFormat': {
            'backgroundColor': bg,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'foregroundColor': MUTED},
            'verticalAlignment': 'MIDDLE',
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment)'
    }})
add_spacer(D, 28, DCOLS)

# P&L section (row 30 idx 29)
add_container(D, 29, [], DCOLS, ORANGE, ORANGE_BG)  # section header
add_total_row(D, 30, DCOLS, ORANGE)  # Total Revenue
add_spacer(D, 31, DCOLS)
# COGS rows (33-34 idx 32-33)
for i, r in enumerate([32, 33]):
    bg = ZEBRA if i % 2 == 0 else WHITE
    requests.append({'updateDimensionProperties': {
        'range': {'sheetId': D, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
        'properties': {'pixelSize': 34}, 'fields': 'pixelSize'
    }})
    requests.append({'repeatCell': {
        'range': {'sheetId': D, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 0, 'endColumnIndex': DCOLS},
        'cell': {'userEnteredFormat': {
            'backgroundColor': bg,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'foregroundColor': BODY},
            'verticalAlignment': 'MIDDLE',
            'borders': {
                'left': {'style': 'SOLID_THICK', 'color': ORANGE},
                'bottom': {'style': 'SOLID', 'color': BORDER_LIGHT},
                'right': {'style': 'SOLID', 'color': BORDER_LIGHT},
            }
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment,borders)'
    }})
add_total_row(D, 34, DCOLS, ORANGE)  # Total COGS
add_spacer(D, 35, DCOLS)

# GROSS PROFIT (row 37 idx 36)
add_total_row(D, 36, DCOLS, GREEN)
# Margin, Overhead, Draw (rows 38-40 idx 37-39)
for i, r in enumerate([37, 38, 39]):
    bg = ZEBRA if i % 2 == 0 else WHITE
    requests.append({'updateDimensionProperties': {
        'range': {'sheetId': D, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
        'properties': {'pixelSize': 34}, 'fields': 'pixelSize'
    }})
    requests.append({'repeatCell': {
        'range': {'sheetId': D, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 0, 'endColumnIndex': DCOLS},
        'cell': {'userEnteredFormat': {
            'backgroundColor': bg,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'foregroundColor': BODY},
            'verticalAlignment': 'MIDDLE',
            'borders': {
                'left': {'style': 'SOLID_THICK', 'color': GREEN},
                'bottom': {'style': 'SOLID', 'color': BORDER_LIGHT},
                'right': {'style': 'SOLID', 'color': BORDER_LIGHT},
            }
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment,borders)'
    }})

# Operating Income, Tax Reserve, Retained Earnings (rows 41-43 idx 40-42)
add_total_row(D, 40, DCOLS, ORANGE)  # Operating Income
add_total_row(D, 41, DCOLS, RED)     # Tax Reserve
add_total_row(D, 42, DCOLS, GREEN)   # Retained Earnings
add_spacer(D, 43, DCOLS)

# TAKE HOME (row 45 idx 44)
add_container(D, 44, [45, 46], DCOLS, PURPLE, PURPLE_BG)
add_total_row(D, 47, DCOLS, PURPLE)  # Total Value to Owner
add_spacer(D, 48, DCOLS)

# Monthly breakdown (rows 50-51 idx 49-50)
for i, r in enumerate([49, 50]):
    bg = ZEBRA if i % 2 == 0 else WHITE
    requests.append({'updateDimensionProperties': {
        'range': {'sheetId': D, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
        'properties': {'pixelSize': 30}, 'fields': 'pixelSize'
    }})
    requests.append({'repeatCell': {
        'range': {'sheetId': D, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 0, 'endColumnIndex': DCOLS},
        'cell': {'userEnteredFormat': {
            'backgroundColor': bg,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'foregroundColor': MUTED},
            'verticalAlignment': 'MIDDLE',
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment)'
    }})
add_spacer(D, 51, DCOLS)

# Capacity check (row 53 idx 52)
add_container(D, 52, [53], DCOLS, BLUE, BLUE_BG)

# Collapse trailing
for r in range(54, 60):
    add_spacer(D, r, DCOLS, 4)

# ============================================================
# MONTHLY TRACKER (gid=845249983) — 27 columns (A-AA)
# ============================================================
print("Monthly Tracker...")
MT = 845249983
MCOLS = 27

add_title(MT, 0)
add_subtitle(MT, 1, MCOLS, 24)

# GOAL/ACT row (idx 2) and Month names (idx 3)
requests.append({'updateDimensionProperties': {
    'range': {'sheetId': MT, 'dimension': 'ROWS', 'startIndex': 2, 'endIndex': 3},
    'properties': {'pixelSize': 24}, 'fields': 'pixelSize'
}})
requests.append({'repeatCell': {
    'range': {'sheetId': MT, 'startRowIndex': 2, 'endRowIndex': 3, 'startColumnIndex': 0, 'endColumnIndex': MCOLS},
    'cell': {'userEnteredFormat': {
        'textFormat': {'fontFamily': 'Inter', 'fontSize': 8, 'bold': True, 'foregroundColor': MUTED},
        'verticalAlignment': 'MIDDLE', 'horizontalAlignment': 'CENTER'
    }},
    'fields': 'userEnteredFormat(textFormat,verticalAlignment,horizontalAlignment)'
}})
add_col_header(MT, 3, MCOLS, 32)  # Month names row

add_spacer(MT, 4, MCOLS, 12)

# PROJECTS
add_container(MT, 5, [6], MCOLS, BLUE, BLUE_BG)
add_spacer(MT, 7, MCOLS, 8)
# Project Revenue (single row, not in container — just styled)
requests.append({'updateDimensionProperties': {
    'range': {'sheetId': MT, 'dimension': 'ROWS', 'startIndex': 8, 'endIndex': 9},
    'properties': {'pixelSize': 34}, 'fields': 'pixelSize'
}})
requests.append({'repeatCell': {
    'range': {'sheetId': MT, 'startRowIndex': 8, 'endRowIndex': 9, 'startColumnIndex': 0, 'endColumnIndex': MCOLS},
    'cell': {'userEnteredFormat': {
        'backgroundColor': ZEBRA,
        'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'foregroundColor': BODY},
        'verticalAlignment': 'MIDDLE',
        'borders': {'left': {'style': 'SOLID_THICK', 'color': BLUE}, 'bottom': {'style': 'SOLID_MEDIUM', 'color': BORDER_MED}, 'right': {'style': 'SOLID', 'color': BORDER_LIGHT}}
    }},
    'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment,borders)'
}})
add_spacer(MT, 9, MCOLS, 12)

# RETAINERS
add_container(MT, 10, [11], MCOLS, GREEN, GREEN_BG)
add_spacer(MT, 12, MCOLS, 8)
# Retainer Revenue + Licensing (two data rows)
for i, r in enumerate([13, 14]):
    bg = ZEBRA if i % 2 == 0 else WHITE
    requests.append({'updateDimensionProperties': {
        'range': {'sheetId': MT, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
        'properties': {'pixelSize': 34}, 'fields': 'pixelSize'
    }})
    requests.append({'repeatCell': {
        'range': {'sheetId': MT, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 0, 'endColumnIndex': MCOLS},
        'cell': {'userEnteredFormat': {
            'backgroundColor': bg,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'foregroundColor': BODY},
            'verticalAlignment': 'MIDDLE',
            'borders': {'left': {'style': 'SOLID_THICK', 'color': GREEN}, 'bottom': {'style': 'SOLID', 'color': BORDER_LIGHT}, 'right': {'style': 'SOLID', 'color': BORDER_LIGHT}}
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment,borders)'
    }})
requests.append({'repeatCell': {
    'range': {'sheetId': MT, 'startRowIndex': 14, 'endRowIndex': 15, 'startColumnIndex': 0, 'endColumnIndex': MCOLS},
    'cell': {'userEnteredFormat': {'borders': {'bottom': {'style': 'SOLID_MEDIUM', 'color': BORDER_MED}}}},
    'fields': 'userEnteredFormat(borders)'
}})
add_spacer(MT, 15, MCOLS, 12)

# TOTALS
add_container(MT, 16, [17], MCOLS, ORANGE, ORANGE_BG)
add_spacer(MT, 18, MCOLS, 8)
# Cumulative + % rows
for i, r in enumerate([19, 20, 21]):
    bg = ZEBRA if i % 2 == 0 else WHITE
    requests.append({'updateDimensionProperties': {
        'range': {'sheetId': MT, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
        'properties': {'pixelSize': 34}, 'fields': 'pixelSize'
    }})
    requests.append({'repeatCell': {
        'range': {'sheetId': MT, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 0, 'endColumnIndex': MCOLS},
        'cell': {'userEnteredFormat': {
            'backgroundColor': bg,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'bold': r == 21, 'foregroundColor': BODY},
            'verticalAlignment': 'MIDDLE',
            'borders': {'left': {'style': 'SOLID_THICK', 'color': ORANGE}, 'bottom': {'style': 'SOLID', 'color': BORDER_LIGHT}, 'right': {'style': 'SOLID', 'color': BORDER_LIGHT}}
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment,borders)'
    }})
add_spacer(MT, 22, MCOLS, 12)

# PIPELINE
add_container(MT, 23, [24,25,26,27,28], MCOLS, PURPLE, PURPLE_BG)

# PROFIT-PER-PROJECT
add_container(MT, 29, [30,31], MCOLS, BLUE, BLUE_BG)

# Collapse trailing
for r in range(32, 50):
    add_spacer(MT, r, MCOLS, 4)

# ============================================================
# PROJECT COGS (gid=865779075) — 6 columns
# ============================================================
print("Project COGS...")
PC = 865779075
PCOLS = 6

add_title(PC, 0)
add_subtitle(PC, 1, PCOLS)
add_spacer(PC, 2, PCOLS)
add_col_header(PC, 3, PCOLS)

# Cost breakdown rows 5-12 (idx 4-11)
for i, r in enumerate(range(4, 12)):
    bg = ZEBRA if i % 2 == 0 else WHITE
    requests.append({'updateDimensionProperties': {
        'range': {'sheetId': PC, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
        'properties': {'pixelSize': 34}, 'fields': 'pixelSize'
    }})
    requests.append({'repeatCell': {
        'range': {'sheetId': PC, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 0, 'endColumnIndex': PCOLS},
        'cell': {'userEnteredFormat': {
            'backgroundColor': bg,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'foregroundColor': BODY},
            'verticalAlignment': 'MIDDLE',
            'borders': {'left': {'style': 'SOLID_THICK', 'color': BLUE}, 'bottom': {'style': 'SOLID', 'color': BORDER_LIGHT}, 'right': {'style': 'SOLID', 'color': BORDER_LIGHT}}
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment,borders)'
    }})
add_spacer(PC, 12, PCOLS, 8)
add_total_row(PC, 13, PCOLS, BLUE)  # TOTAL COGS
add_spacer(PC, 14, PCOLS)

# Price + Gross Profit + Margin
for i, r in enumerate([15, 17, 18]):
    bg = ZEBRA if i % 2 == 0 else WHITE
    requests.append({'updateDimensionProperties': {
        'range': {'sheetId': PC, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
        'properties': {'pixelSize': 34}, 'fields': 'pixelSize'
    }})
    requests.append({'repeatCell': {
        'range': {'sheetId': PC, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 0, 'endColumnIndex': PCOLS},
        'cell': {'userEnteredFormat': {
            'backgroundColor': bg,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'bold': r == 17, 'foregroundColor': BODY if r != 17 else GREEN},
            'verticalAlignment': 'MIDDLE',
            'borders': {'left': {'style': 'SOLID_THICK', 'color': GREEN}, 'bottom': {'style': 'SOLID', 'color': BORDER_LIGHT}, 'right': {'style': 'SOLID', 'color': BORDER_LIGHT}}
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment,borders)'
    }})
add_spacer(PC, 16, PCOLS, 8)
add_spacer(PC, 19, PCOLS)

# AOS MARGIN CHECK
add_container(PC, 20, [21, 22], PCOLS, GREEN, GREEN_BG)
add_spacer(PC, 23, PCOLS)

# CASH vs FOUNDER TIME
add_container(PC, 24, [25, 26, 27], PCOLS, ORANGE, ORANGE_BG)
add_spacer(PC, 28, PCOLS)

# COST-SHARE OPPORTUNITY
add_container(PC, 29, [30, 31, 32], PCOLS, PURPLE, PURPLE_BG)

for r in range(33, 50):
    add_spacer(PC, r, PCOLS, 4)

# ============================================================
# OVERHEAD (gid=7683076) — 3 columns
# ============================================================
print("Overhead...")
OH = 7683076
OCOLS = 3

add_title(OH, 0)
add_col_header(OH, 1, OCOLS)
add_spacer(OH, 2, OCOLS)

# Sections with their data rows
oh_sections = [
    {'name': 'MARKETING', 'header': 3, 'data': [4,5,6], 'accent': BLUE, 'bg': BLUE_BG},
    {'name': 'SOFTWARE', 'header': 8, 'data': [9,10,11,12,13,14,15,16], 'accent': BLUE, 'bg': BLUE_BG},
    {'name': 'VEHICLE', 'header': 18, 'data': [19,20,21], 'accent': ORANGE, 'bg': ORANGE_BG},
    {'name': 'EQUIPMENT', 'header': 23, 'data': [24,25], 'accent': ORANGE, 'bg': ORANGE_BG},
    {'name': 'OFFICE', 'header': 27, 'data': [28,29,30], 'accent': GREEN, 'bg': GREEN_BG},
    {'name': 'INSURANCE', 'header': 32, 'data': [33,34], 'accent': GREEN, 'bg': GREEN_BG},
    {'name': 'ACCT & LEGAL', 'header': 36, 'data': [37,38,39,40], 'accent': PURPLE, 'bg': PURPLE_BG},
    {'name': 'RESERVES', 'header': 42, 'data': [43,44], 'accent': PURPLE, 'bg': PURPLE_BG},
]

for s in oh_sections:
    add_container(OH, s['header'], s['data'], OCOLS, s['accent'], s['bg'])
    spacer_row = s['data'][-1] + 1
    if spacer_row in [7, 17, 22, 26, 31, 35, 41]:
        add_spacer(OH, spacer_row, OCOLS, 14)

add_spacer(OH, 7, OCOLS, 14)
add_spacer(OH, 17, OCOLS, 14)
add_spacer(OH, 22, OCOLS, 14)
add_spacer(OH, 26, OCOLS, 14)
add_spacer(OH, 31, OCOLS, 14)
add_spacer(OH, 35, OCOLS, 14)
add_spacer(OH, 41, OCOLS, 14)

# TOTAL row
add_total_row(OH, 45, OCOLS, BLUE)

for r in range(46, 55):
    add_spacer(OH, r, OCOLS, 4)

# ============================================================
# PRICING GUIDE (gid=655418673) — 5 columns
# ============================================================
print("Pricing Guide...")
PG = 655418673
PGCOLS = 5

add_title(PG, 0)
add_subtitle(PG, 1, PGCOLS)
add_spacer(PG, 2, PGCOLS)
add_col_header(PG, 3, PGCOLS)
add_spacer(PG, 4, PGCOLS, 10)

pg_sections = [
    {'header': 5, 'data': [6,7,8,9], 'accent': BLUE, 'bg': BLUE_BG},       # Architects
    {'header': 11, 'data': [12,13,14,15], 'accent': ORANGE, 'bg': ORANGE_BG}, # Builders
    {'header': 17, 'data': [18,19,20], 'accent': GREEN, 'bg': GREEN_BG},      # Interior
    {'header': 22, 'data': [23,24], 'accent': PURPLE, 'bg': PURPLE_BG},       # Standalone
    {'header': 26, 'data': [27,28,29,30,31,32], 'accent': MUTED, 'bg': ZEBRA}, # Add-ons
]

for s in pg_sections:
    add_container(PG, s['header'], s['data'], PGCOLS, s['accent'], s['bg'])
    spacer = s['data'][-1] + 1
    add_spacer(PG, spacer, PGCOLS, 14)

for r in range(33, 50):
    add_spacer(PG, r, PGCOLS, 4)

# Column widths
requests.append({'updateDimensionProperties': {
    'range': {'sheetId': PG, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 1},
    'properties': {'pixelSize': 200}, 'fields': 'pixelSize'
}})
requests.append({'updateDimensionProperties': {
    'range': {'sheetId': PG, 'dimension': 'COLUMNS', 'startIndex': 1, 'endIndex': 2},
    'properties': {'pixelSize': 300}, 'fields': 'pixelSize'
}})
requests.append({'updateDimensionProperties': {
    'range': {'sheetId': PG, 'dimension': 'COLUMNS', 'startIndex': 2, 'endIndex': 3},
    'properties': {'pixelSize': 120}, 'fields': 'pixelSize'
}})
requests.append({'updateDimensionProperties': {
    'range': {'sheetId': PG, 'dimension': 'COLUMNS', 'startIndex': 3, 'endIndex': 4},
    'properties': {'pixelSize': 130}, 'fields': 'pixelSize'
}})
requests.append({'updateDimensionProperties': {
    'range': {'sheetId': PG, 'dimension': 'COLUMNS', 'startIndex': 4, 'endIndex': 5},
    'properties': {'pixelSize': 280}, 'fields': 'pixelSize'
}})

# ============================================================
# FREEZE + COLUMN WIDTHS cleanup
# ============================================================
# Dashboard col A
requests.append({'updateDimensionProperties': {
    'range': {'sheetId': D, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 1},
    'properties': {'pixelSize': 300}, 'fields': 'pixelSize'
}})

# Freeze rows
for sid, fr in [(D, 2), (MT, 4), (PC, 4), (OH, 2), (PG, 4)]:
    requests.append({'updateSheetProperties': {
        'properties': {'sheetId': sid, 'gridProperties': {'frozenRowCount': fr}},
        'fields': 'gridProperties.frozenRowCount'
    }})

# ============================================================
print(f"Sending {len(requests)} requests...")
service.spreadsheets().batchUpdate(
    spreadsheetId=SHEET_ID,
    body={'requests': requests}
).execute()
print("Done! All tabs redesigned with container pattern.")
