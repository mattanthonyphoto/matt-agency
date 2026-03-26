"""
Fix dark formatting artifacts on the Financial Map Dashboard tab.
Clears charcoal (#272c38) backgrounds from empty columns P-Z on rows 24-50,
and also blanks out any formatting from columns G-Z (beyond the data area)
to ensure a clean white appearance.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_sheets_service

SHEET_ID = '1nrzAfXzRiFIQpa85one6iuMXASIBbgPrwDoI6TwH9KU'
DASHBOARD_SHEET_ID = 378592626

WHITE = {"red": 1, "green": 1, "blue": 1}
NO_BORDER = {"style": "NONE"}

def gr(sr, er, sc, ec):
    return {"sheetId": DASHBOARD_SHEET_ID,
            "startRowIndex": sr, "endRowIndex": er,
            "startColumnIndex": sc, "endColumnIndex": ec}

def main():
    service = get_sheets_service()
    requests = []

    # 1. Clear ALL formatting from columns G-Z (indices 6-26) for rows 1-100
    #    This covers every possible artifact. Set white bg, no borders, default text.
    requests.append({
        "repeatCell": {
            "range": gr(0, 100, 6, 26),
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": WHITE,
                    "borders": {
                        "top": NO_BORDER,
                        "bottom": NO_BORDER,
                        "left": NO_BORDER,
                        "right": NO_BORDER,
                    },
                    "textFormat": {
                        "foregroundColor": WHITE,  # white text so nothing shows
                        "fontSize": 10,
                        "bold": False,
                    }
                }
            },
            "fields": "userEnteredFormat(backgroundColor,borders,textFormat)"
        }
    })

    # 2. Also clear rows 100-200 in those columns just to be safe
    requests.append({
        "repeatCell": {
            "range": gr(100, 200, 6, 26),
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": WHITE,
                    "borders": {
                        "top": NO_BORDER,
                        "bottom": NO_BORDER,
                        "left": NO_BORDER,
                        "right": NO_BORDER,
                    },
                }
            },
            "fields": "userEnteredFormat(backgroundColor,borders)"
        }
    })

    # 3. Clear any content that might exist in those columns
    requests.append({
        "repeatCell": {
            "range": gr(0, 200, 6, 26),
            "cell": {
                "userEnteredValue": {}
            },
            "fields": "userEnteredValue"
        }
    })

    print(f"Sending {len(requests)} batch update requests...")
    result = service.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"requests": requests}
    ).execute()
    print(f"Done. {result.get('totalUpdatedCells', 'N/A')} cells updated.")

    # Verify the fix
    time.sleep(2)
    print("\nVerifying fix...")

    verify = service.spreadsheets().get(
        spreadsheetId=SHEET_ID,
        ranges=["Dashboard!P24:Z50"],
        includeGridData=True
    ).execute()

    grid_data = verify['sheets'][0]['data'][0]
    dark_remaining = 0
    for ri, row in enumerate(grid_data.get('rowData', [])):
        for ci, cell in enumerate(row.get('values', [])):
            fmt = cell.get('userEnteredFormat', {}) or cell.get('effectiveFormat', {})
            bg = fmt.get('backgroundColor', {})
            r = bg.get('red', 1)
            g = bg.get('green', 1)
            b = bg.get('blue', 1)
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if lum < 0.35:
                dark_remaining += 1

    if dark_remaining == 0:
        print("SUCCESS: No dark cells remaining in columns P-Z, rows 24-50.")
    else:
        print(f"WARNING: {dark_remaining} dark cells still remain.")

if __name__ == '__main__':
    main()
