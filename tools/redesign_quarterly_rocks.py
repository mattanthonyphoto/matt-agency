from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/spreadsheets'])
service = build('sheets', 'v4', credentials=creds)
SHEET_ID = '1nrzAfXzRiFIQpa85one6iuMXASIBbgPrwDoI6TwH9KU'
SID = 1620953837

def rgb(h):
    h = h.lstrip('#')
    return {'red': int(h[0:2],16)/255, 'green': int(h[2:4],16)/255, 'blue': int(h[4:6],16)/255}

WHITE = rgb('#ffffff')
CHARCOAL = rgb('#272c38')
BODY = rgb('#3a3f47')
MUTED = rgb('#8b929b')
BLUE = rgb('#3870de')
GREEN = rgb('#1e9f6c')
ORANGE = rgb('#e6871e')
RED = rgb('#d93333')
PURPLE = rgb('#7a51cd')
ZEBRA = rgb('#f8f9fa')
LIGHT_GREY = rgb('#f0f1f3')
BORDER_LIGHT = rgb('#e1e4e7')
BORDER_MED = rgb('#d1d3d7')

# Quarter accent colors
Q_COLORS = {
    'Q1': BLUE,
    'Q2': GREEN, 
    'Q3': ORANGE,
    'Q4': PURPLE
}
Q_BG = {
    'Q1': rgb('#ebeefa'),  # pale blue
    'Q2': rgb('#e7f6ee'),  # pale green
    'Q3': rgb('#fef3e5'),  # pale orange
    'Q4': rgb('#f3eefa'),  # pale purple
}

# Status colors
STATUS_BG = {
    'Not Started': rgb('#f0f1f3'),
    'In Progress': rgb('#ebeefa'),
    'Complete': rgb('#e7f6ee'),
    'Done': rgb('#e7f6ee'),
    'At Risk': rgb('#fcecec'),
    'Behind': rgb('#fcecec'),
    'On Track': rgb('#e7f6ee'),
}
STATUS_TEXT = {
    'Not Started': MUTED,
    'In Progress': BLUE,
    'Complete': GREEN,
    'Done': GREEN,
    'At Risk': RED,
    'Behind': RED,
    'On Track': GREEN,
}

requests = []

# ============================================================
# COLUMN WIDTHS — wider, more breathing room
# ============================================================
col_widths = {0: 55, 1: 380, 2: 80, 3: 90, 4: 110, 5: 80}
for c, w in col_widths.items():
    requests.append({
        'updateDimensionProperties': {
            'range': {'sheetId': SID, 'dimension': 'COLUMNS', 'startIndex': c, 'endIndex': c+1},
            'properties': {'pixelSize': w},
            'fields': 'pixelSize'
        }
    })

# ============================================================
# ROW 1 — Title (bigger, bolder)
# ============================================================
requests.append({
    'updateDimensionProperties': {
        'range': {'sheetId': SID, 'dimension': 'ROWS', 'startIndex': 0, 'endIndex': 1},
        'properties': {'pixelSize': 52},
        'fields': 'pixelSize'
    }
})
requests.append({
    'repeatCell': {
        'range': {'sheetId': SID, 'startRowIndex': 0, 'endRowIndex': 1, 'startColumnIndex': 0, 'endColumnIndex': 6},
        'cell': {'userEnteredFormat': {
            'backgroundColor': WHITE,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 18, 'bold': True, 'foregroundColor': CHARCOAL},
            'verticalAlignment': 'MIDDLE'
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment)'
    }
})

# ============================================================
# ROW 2 — Spacer (16px)
# ============================================================
requests.append({
    'updateDimensionProperties': {
        'range': {'sheetId': SID, 'dimension': 'ROWS', 'startIndex': 1, 'endIndex': 2},
        'properties': {'pixelSize': 16},
        'fields': 'pixelSize'
    }
})

# ============================================================
# ROW 3 — Column Headers (strong, visible!)
# ============================================================
requests.append({
    'updateDimensionProperties': {
        'range': {'sheetId': SID, 'dimension': 'ROWS', 'startIndex': 2, 'endIndex': 3},
        'properties': {'pixelSize': 36},
        'fields': 'pixelSize'
    }
})
requests.append({
    'repeatCell': {
        'range': {'sheetId': SID, 'startRowIndex': 2, 'endRowIndex': 3, 'startColumnIndex': 0, 'endColumnIndex': 6},
        'cell': {'userEnteredFormat': {
            'backgroundColor': CHARCOAL,
            'textFormat': {'fontFamily': 'Inter', 'fontSize': 9, 'bold': True, 'foregroundColor': WHITE},
            'verticalAlignment': 'MIDDLE',
            'borders': {
                'bottom': {'style': 'SOLID_MEDIUM', 'color': CHARCOAL}
            }
        }},
        'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment,borders)'
    }
})

# ============================================================
# QUARTER SECTIONS — each gets a container treatment
# ============================================================
# Structure: quarter_header_row, data_rows, spacer_row
quarters = [
    {'name': 'Q1', 'header': 3, 'data': list(range(4, 12)), 'spacer': 12},
    {'name': 'Q2', 'header': 13, 'data': list(range(14, 22)), 'spacer': 22},
    {'name': 'Q3', 'header': 23, 'data': list(range(24, 31)), 'spacer': 31},
    {'name': 'Q4', 'header': 32, 'data': list(range(33, 39)), 'spacer': 39},
]

for q in quarters:
    qname = q['name']
    accent = Q_COLORS[qname]
    qbg = Q_BG[qname]
    
    # --- Quarter Header Row ---
    requests.append({
        'updateDimensionProperties': {
            'range': {'sheetId': SID, 'dimension': 'ROWS', 'startIndex': q['header'], 'endIndex': q['header']+1},
            'properties': {'pixelSize': 40},
            'fields': 'pixelSize'
        }
    })
    requests.append({
        'repeatCell': {
            'range': {'sheetId': SID, 'startRowIndex': q['header'], 'endRowIndex': q['header']+1, 'startColumnIndex': 0, 'endColumnIndex': 6},
            'cell': {'userEnteredFormat': {
                'backgroundColor': qbg,
                'textFormat': {'fontFamily': 'Inter', 'fontSize': 12, 'bold': True, 'foregroundColor': CHARCOAL},
                'verticalAlignment': 'MIDDLE',
                'borders': {
                    'left': {'style': 'SOLID_MEDIUM', 'color': accent, 'width': 3},
                    'top': {'style': 'SOLID', 'color': BORDER_LIGHT},
                    'bottom': {'style': 'SOLID', 'color': BORDER_LIGHT},
                    'right': {'style': 'SOLID', 'color': BORDER_LIGHT},
                }
            }},
            'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment,borders)'
        }
    })
    # Thicker left accent on col A only
    requests.append({
        'repeatCell': {
            'range': {'sheetId': SID, 'startRowIndex': q['header'], 'endRowIndex': q['header']+1, 'startColumnIndex': 0, 'endColumnIndex': 1},
            'cell': {'userEnteredFormat': {
                'borders': {
                    'left': {'style': 'SOLID_THICK', 'color': accent},
                    'top': {'style': 'SOLID', 'color': BORDER_LIGHT},
                    'bottom': {'style': 'SOLID', 'color': BORDER_LIGHT},
                }
            }},
            'fields': 'userEnteredFormat(borders)'
        }
    })
    
    # --- Data Rows ---
    for i, r in enumerate(q['data']):
        bg = ZEBRA if i % 2 == 0 else WHITE
        
        requests.append({
            'updateDimensionProperties': {
                'range': {'sheetId': SID, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
                'properties': {'pixelSize': 34},
                'fields': 'pixelSize'
            }
        })
        
        # All columns except Status (E) and % Done (F)
        for c in [0, 1, 2, 3]:
            requests.append({
                'repeatCell': {
                    'range': {'sheetId': SID, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': c, 'endColumnIndex': c+1},
                    'cell': {'userEnteredFormat': {
                        'backgroundColor': bg,
                        'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'bold': False, 'foregroundColor': BODY},
                        'verticalAlignment': 'MIDDLE',
                        'borders': {
                            'left': {'style': 'SOLID_THICK' if c == 0 else 'NONE', 'color': accent if c == 0 else BORDER_LIGHT},
                            'bottom': {'style': 'SOLID', 'color': BORDER_LIGHT},
                            'right': {'style': 'SOLID' if c == 5 else 'NONE', 'color': BORDER_LIGHT},
                        }
                    }},
                    'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment,borders)'
                }
            })
        
        # % Done column (F, index 5) — same base style + right border to close container
        requests.append({
            'repeatCell': {
                'range': {'sheetId': SID, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 5, 'endColumnIndex': 6},
                'cell': {'userEnteredFormat': {
                    'backgroundColor': bg,
                    'textFormat': {'fontFamily': 'Inter', 'fontSize': 10, 'bold': True, 'foregroundColor': MUTED},
                    'verticalAlignment': 'MIDDLE',
                    'numberFormat': {'type': 'PERCENT', 'pattern': '0%'},
                    'horizontalAlignment': 'CENTER',
                    'borders': {
                        'bottom': {'style': 'SOLID', 'color': BORDER_LIGHT},
                        'right': {'style': 'SOLID', 'color': BORDER_LIGHT},
                    }
                }},
                'fields': 'userEnteredFormat(backgroundColor,textFormat,verticalAlignment,numberFormat,horizontalAlignment,borders)'
            }
        })
    
    # Left accent border on all data rows (col A)
    requests.append({
        'repeatCell': {
            'range': {'sheetId': SID, 'startRowIndex': q['data'][0], 'endRowIndex': q['data'][-1]+1, 'startColumnIndex': 0, 'endColumnIndex': 1},
            'cell': {'userEnteredFormat': {
                'borders': {
                    'left': {'style': 'SOLID_THICK', 'color': accent},
                    'bottom': {'style': 'SOLID', 'color': BORDER_LIGHT},
                }
            }},
            'fields': 'userEnteredFormat(borders)'
        }
    })
    
    # Right border on all data rows (col F) to close container
    requests.append({
        'repeatCell': {
            'range': {'sheetId': SID, 'startRowIndex': q['data'][0], 'endRowIndex': q['data'][-1]+1, 'startColumnIndex': 5, 'endColumnIndex': 6},
            'cell': {'userEnteredFormat': {
                'borders': {
                    'right': {'style': 'SOLID', 'color': BORDER_LIGHT},
                    'bottom': {'style': 'SOLID', 'color': BORDER_LIGHT},
                }
            }},
            'fields': 'userEnteredFormat(borders)'
        }
    })
    
    # Bottom border on last data row (closes the container box)
    last_data = q['data'][-1]
    requests.append({
        'repeatCell': {
            'range': {'sheetId': SID, 'startRowIndex': last_data, 'endRowIndex': last_data+1, 'startColumnIndex': 0, 'endColumnIndex': 6},
            'cell': {'userEnteredFormat': {
                'borders': {
                    'left': {'style': 'SOLID_THICK', 'color': accent},
                    'bottom': {'style': 'SOLID_MEDIUM', 'color': BORDER_MED},
                    'right': {'style': 'SOLID', 'color': BORDER_LIGHT},
                }
            }},
            'fields': 'userEnteredFormat(borders)'
        }
    })
    
    # --- Spacer Row ---
    requests.append({
        'updateDimensionProperties': {
            'range': {'sheetId': SID, 'dimension': 'ROWS', 'startIndex': q['spacer'], 'endIndex': q['spacer']+1},
            'properties': {'pixelSize': 18},
            'fields': 'pixelSize'
        }
    })
    requests.append({
        'repeatCell': {
            'range': {'sheetId': SID, 'startRowIndex': q['spacer'], 'endRowIndex': q['spacer']+1, 'startColumnIndex': 0, 'endColumnIndex': 6},
            'cell': {'userEnteredFormat': {
                'backgroundColor': WHITE,
                'borders': {'top': {'style': 'NONE'}, 'bottom': {'style': 'NONE'}, 'left': {'style': 'NONE'}, 'right': {'style': 'NONE'}}
            }},
            'fields': 'userEnteredFormat(backgroundColor,borders)'
        }
    })

# ============================================================
# STATUS COLUMN (E) — color-coded chips per status value
# Need to read actual values first, then apply per-cell
# ============================================================
print("Reading status values...")
result = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='Quarterly Rocks!E1:E45'
).execute()
status_values = result.get('values', [])

for r in range(len(status_values)):
    if r < 3:  # skip title, spacer, header
        continue
    val = status_values[r][0] if status_values[r] else ''
    if val in STATUS_BG:
        bg = STATUS_BG[val]
        tc = STATUS_TEXT[val]
        requests.append({
            'repeatCell': {
                'range': {'sheetId': SID, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 4, 'endColumnIndex': 5},
                'cell': {'userEnteredFormat': {
                    'backgroundColor': bg,
                    'textFormat': {'fontFamily': 'Inter', 'fontSize': 9, 'bold': True, 'foregroundColor': tc},
                    'horizontalAlignment': 'CENTER',
                    'verticalAlignment': 'MIDDLE',
                    'borders': {
                        'top': {'style': 'SOLID', 'color': BORDER_LIGHT},
                        'bottom': {'style': 'SOLID', 'color': BORDER_LIGHT},
                        'left': {'style': 'SOLID', 'color': BORDER_LIGHT},
                        'right': {'style': 'SOLID', 'color': BORDER_LIGHT},
                    }
                }},
                'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,borders)'
            }
        })

# ============================================================
# FIX % DONE VALUES — they show "$0" because of currency format
# Clear and rewrite as proper numbers
# ============================================================
print("Fixing % Done values...")
# Read current values
pct_result = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range='Quarterly Rocks!F1:F45'
).execute()
pct_values = pct_result.get('values', [])

# The quarter header rows also have "$0" — those should show aggregate %
# Data rows showing "$0" should be "0"
fix_ranges = []
fix_values = []
for r in range(len(pct_values)):
    val = pct_values[r][0] if pct_values[r] else ''
    if val == '$0' or val == '$0.00':
        fix_ranges.append(f'Quarterly Rocks!F{r+1}')
        fix_values.append([[0]])

# Batch update values
for i, rng in enumerate(fix_ranges):
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=rng,
        valueInputOption='RAW',
        body={'values': fix_values[i]}
    ).execute()

# ============================================================
# TRAILING ROWS — collapse
# ============================================================
for r in range(40, 55):
    requests.append({
        'updateDimensionProperties': {
            'range': {'sheetId': SID, 'dimension': 'ROWS', 'startIndex': r, 'endIndex': r+1},
            'properties': {'pixelSize': 4},
            'fields': 'pixelSize'
        }
    })
    requests.append({
        'repeatCell': {
            'range': {'sheetId': SID, 'startRowIndex': r, 'endRowIndex': r+1, 'startColumnIndex': 0, 'endColumnIndex': 6},
            'cell': {'userEnteredFormat': {'backgroundColor': WHITE, 'borders': {
                'top': {'style': 'NONE'}, 'bottom': {'style': 'NONE'}, 'left': {'style': 'NONE'}, 'right': {'style': 'NONE'}
            }}},
            'fields': 'userEnteredFormat(backgroundColor,borders)'
        }
    })

# Collapse extra columns
requests.append({
    'updateDimensionProperties': {
        'range': {'sheetId': SID, 'dimension': 'COLUMNS', 'startIndex': 6, 'endIndex': 26},
        'properties': {'pixelSize': 12},
        'fields': 'pixelSize'
    }
})

# ============================================================
# FREEZE header rows
# ============================================================
requests.append({
    'updateSheetProperties': {
        'properties': {
            'sheetId': SID,
            'gridProperties': {'frozenRowCount': 3}
        },
        'fields': 'gridProperties.frozenRowCount'
    }
})

# ============================================================
# EXECUTE
# ============================================================
print(f"Sending {len(requests)} formatting requests...")
service.spreadsheets().batchUpdate(
    spreadsheetId=SHEET_ID,
    body={'requests': requests}
).execute()
print("Done! Quarterly Rocks redesigned.")
