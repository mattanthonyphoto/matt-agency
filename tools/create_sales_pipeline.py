"""
Create the unified Sales Pipeline — the single central hub for all leads.

Every lead flows here regardless of source:
  - Cold email warm signals (Instantly replies/opens)
  - Website lead magnet (plan requests)
  - GHL inbound (intake forms)
  - Manual adds (referrals, networking, Instagram DMs)

Tabs:
  1. Pipeline — every lead, one row per company
  2. Dashboard — KPIs, stage breakdowns, revenue by source/ICP
  3. Monthly Summary — monthly funnel metrics
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from google_sheets_auth import get_sheets_service

# Brand colors
INK = {"red": 0.102, "green": 0.102, "blue": 0.094}      # #1A1A18
GOLD = {"red": 0.788, "green": 0.663, "blue": 0.431}      # #C9A96E
PAPER = {"red": 0.965, "green": 0.957, "blue": 0.941}      # #F6F4F0
WHITE = {"red": 1, "green": 1, "blue": 1}


def col_index(col_letter):
    result = 0
    for c in col_letter:
        result = result * 26 + (ord(c) - ord('A'))
    return result


def main():
    sheets = get_sheets_service()

    # Create spreadsheet with 3 tabs
    spreadsheet = sheets.spreadsheets().create(body={
        "properties": {"title": "Sales Pipeline"},
        "sheets": [
            {"properties": {"title": "Pipeline", "sheetId": 0,
                            "gridProperties": {"frozenRowCount": 1, "frozenColumnCount": 1}}},
            {"properties": {"title": "Dashboard", "sheetId": 1}},
            {"properties": {"title": "Monthly Summary", "sheetId": 2,
                            "gridProperties": {"frozenRowCount": 1}}},
        ]
    }).execute()

    spreadsheet_id = spreadsheet["spreadsheetId"]
    url = spreadsheet["spreadsheetUrl"]
    print(f"Created spreadsheet: {url}")
    print(f"Sheet ID: {spreadsheet_id}")

    # ══════════════════════════════════════════════════════════
    # TAB 1: PIPELINE — unified lead tracking
    # ══════════════════════════════════════════════════════════
    #
    # Column layout (A:T):
    #   A  Company           — company name (primary key)
    #   B  Contact           — decision maker name
    #   C  Email             — best email
    #   D  Phone             — phone number
    #   E  ICP               — Architect, Builder, Interior Designer, Trades
    #   F  Source            — how they entered the pipeline
    #   G  Stage             — unified lifecycle stage
    #   H  Date Added        — when lead entered pipeline
    #   I  Last Activity     — date of most recent touchpoint
    #   J  Signal            — engagement detail (e.g. "Replied Mar 25", "Opened 4x")
    #   K  Service Type      — what they'd buy
    #   L  Estimated Value   — deal value
    #   M  Plan Sent         — date marketing plan was sent
    #   N  Plan URL          — published plan link
    #   O  Days Since Plan   — formula: days since plan sent
    #   P  Next Action       — what to do next
    #   Q  Action Date       — when to do it
    #   R  Close Date        — when deal closed (won or lost)
    #   S  Loss Reason       — why we lost (if lost)
    #   T  Notes             — free text, engagement log

    pipeline_headers = [
        "Company", "Contact", "Email", "Phone", "ICP", "Source",
        "Stage", "Date Added", "Last Activity", "Signal",
        "Service Type", "Estimated Value",
        "Plan Sent", "Plan URL", "Days Since Plan",
        "Next Action", "Action Date",
        "Close Date", "Loss Reason", "Notes",
    ]

    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Pipeline!A1:T1",
        valueInputOption="RAW",
        body={"values": [pipeline_headers]}
    ).execute()

    # Formulas for rows 2-500
    formula_rows = []
    for r in range(2, 501):
        formula_rows.append([
            f'=IF(M{r}="","",TODAY()-M{r})',  # O: Days Since Plan
        ])

    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Pipeline!O2:O501",
        valueInputOption="USER_ENTERED",
        body={"values": formula_rows}
    ).execute()

    # Data validation
    validations = [
        ("E2:E501", ["Architect", "Builder", "Interior Designer", "Trades"]),
        ("F2:F501", ["Cold Email", "Lead Magnet", "Google", "Instagram", "Referral", "Networking", "Pricing Guide", "Reactivation", "Other"]),
        ("G2:G501", ["New Lead", "Engaged", "Discovery Booked", "Discovery Done", "Proposal Sent", "Won", "Lost", "Dormant", "Do Not Contact"]),
        ("K2:K501", ["Project Photography", "Award & Publication", "Build & Team", "Creative Partner", "Standalone"]),
        ("S2:S501", ["Price", "Timing", "Went with competitor", "No response", "Not ready", "Other"]),
    ]

    validation_requests = []
    for range_str, values in validations:
        parts = range_str.replace(":", " ").split()
        start_col = col_index(''.join(filter(str.isalpha, parts[0])))
        start_row = int(''.join(filter(str.isdigit, parts[0]))) - 1
        end_col = col_index(''.join(filter(str.isalpha, parts[1])))
        end_row = int(''.join(filter(str.isdigit, parts[1])))

        validation_requests.append({
            "setDataValidation": {
                "range": {
                    "sheetId": 0,
                    "startRowIndex": start_row,
                    "endRowIndex": end_row,
                    "startColumnIndex": start_col,
                    "endColumnIndex": end_col + 1,
                },
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": [{"userEnteredValue": v} for v in values],
                    },
                    "showCustomUi": True,
                    "strict": False,
                },
            }
        })

    # Date validation for H, I, M, Q, R
    for col_letter in ["H", "I", "M", "Q", "R"]:
        ci = col_index(col_letter)
        validation_requests.append({
            "setDataValidation": {
                "range": {
                    "sheetId": 0,
                    "startRowIndex": 1,
                    "endRowIndex": 501,
                    "startColumnIndex": ci,
                    "endColumnIndex": ci + 1,
                },
                "rule": {
                    "condition": {"type": "DATE_IS_VALID"},
                    "showCustomUi": True,
                    "strict": False,
                },
            }
        })

    # Currency format for L (Estimated Value)
    currency_requests = [{
        "repeatCell": {
            "range": {
                "sheetId": 0,
                "startRowIndex": 1,
                "endRowIndex": 501,
                "startColumnIndex": col_index("L"),
                "endColumnIndex": col_index("L") + 1,
            },
            "cell": {
                "userEnteredFormat": {
                    "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"},
                }
            },
            "fields": "userEnteredFormat.numberFormat",
        }
    }]

    # ══════════════════════════════════════════════════════════
    # TAB 2: DASHBOARD
    # ══════════════════════════════════════════════════════════
    P = "Pipeline"  # shorthand for formulas
    dashboard_data = [
        ["SALES PIPELINE DASHBOARD", "", "", ""],
        [""],
        ["PIPELINE OVERVIEW", "", "", ""],
        ["Total Leads", f'=COUNTA({P}!A2:A501)', "", ""],
        ["Active Pipeline Value",
         f'=SUMPRODUCT(({P}!G2:G501<>"Won")*({P}!G2:G501<>"Lost")*({P}!G2:G501<>"Dormant")*({P}!G2:G501<>"")*{P}!L2:L501)', "", ""],
        ["Won Revenue YTD",
         f'=SUMPRODUCT(({P}!G2:G501="Won")*{P}!L2:L501)', "", ""],
        ["Close Rate",
         f'=IFERROR(COUNTIF({P}!G2:G501,"Won")/(COUNTIF({P}!G2:G501,"Won")+COUNTIF({P}!G2:G501,"Lost")),"No data")', "", ""],
        ["Avg Deal Size (Won)",
         f'=IFERROR(AVERAGEIF({P}!G2:G501,"Won",{P}!L2:L501),"No data")', "", ""],
        ["Avg Days to Close",
         f'=IFERROR(AVERAGEIFS({P}!R2:R501-{P}!H2:H501,{P}!G2:G501,"Won"),"No data")', "", ""],
        [""],
        ["LEADS BY STAGE", "", "Count", "Pipeline Value"],
    ]

    stages = ["New Lead", "Engaged", "Discovery Booked", "Discovery Done", "Proposal Sent", "Won", "Lost", "Dormant"]
    for stage in stages:
        val_col = "L"
        dashboard_data.append([
            stage, "",
            f'=COUNTIF({P}!G2:G501,"{stage}")',
            f'=SUMPRODUCT(({P}!G2:G501="{stage}")*{P}!{val_col}2:{val_col}501)',
        ])

    dashboard_data.append([""])
    dashboard_data.append(["REVENUE BY SOURCE (Won)", "", "Deals", "Revenue"])

    sources = ["Cold Email", "Lead Magnet", "Google", "Instagram", "Referral", "Networking", "Pricing Guide", "Reactivation", "Other"]
    for source in sources:
        dashboard_data.append([
            source, "",
            f'=SUMPRODUCT(({P}!F2:F501="{source}")*({P}!G2:G501="Won"))',
            f'=SUMPRODUCT(({P}!F2:F501="{source}")*({P}!G2:G501="Won")*{P}!L2:L501)',
        ])

    dashboard_data.append([""])
    dashboard_data.append(["REVENUE BY ICP (Won)", "", "Deals", "Revenue"])

    icps = ["Architect", "Builder", "Interior Designer", "Trades"]
    for icp in icps:
        dashboard_data.append([
            icp, "",
            f'=SUMPRODUCT(({P}!E2:E501="{icp}")*({P}!G2:G501="Won"))',
            f'=SUMPRODUCT(({P}!E2:E501="{icp}")*({P}!G2:G501="Won")*{P}!L2:L501)',
        ])

    dashboard_data.append([""])
    dashboard_data.append(["LEADS BY SOURCE (All)", "", "Count", "% of Total"])

    for source in sources:
        row_num = len(dashboard_data) + 1
        dashboard_data.append([
            source, "",
            f'=COUNTIF({P}!F2:F501,"{source}")',
            f'=IFERROR(C{row_num}/B4,"")',
        ])

    dashboard_data.append([""])
    dashboard_data.append(["MONTHLY CLOSE RATE", "", "Won", "Lost", "Close Rate"])

    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    for i, month in enumerate(months, 1):
        row_num = len(dashboard_data) + 1
        dashboard_data.append([
            month, "",
            f'=SUMPRODUCT((MONTH({P}!R2:R501)={i})*(YEAR({P}!R2:R501)=YEAR(TODAY()))*({P}!G2:G501="Won"))',
            f'=SUMPRODUCT((MONTH({P}!R2:R501)={i})*(YEAR({P}!R2:R501)=YEAR(TODAY()))*({P}!G2:G501="Lost"))',
            f'=IFERROR(C{row_num}/(C{row_num}+D{row_num}),"")',
        ])

    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"Dashboard!A1:E{len(dashboard_data)}",
        valueInputOption="USER_ENTERED",
        body={"values": dashboard_data}
    ).execute()

    # ══════════════════════════════════════════════════════════
    # TAB 3: MONTHLY SUMMARY
    # ══════════════════════════════════════════════════════════
    monthly_headers = [
        "Month", "Leads In", "Discovery Calls", "Proposals Sent",
        "Won", "Lost", "Close Rate", "Revenue", "Avg Deal Size",
    ]

    monthly_data = [monthly_headers]
    for i, month in enumerate(months, 1):
        r = i + 1
        monthly_data.append([
            month,
            f'=SUMPRODUCT((MONTH({P}!H2:H501)={i})*(YEAR({P}!H2:H501)=YEAR(TODAY()))*({P}!A2:A501<>""))',
            f'=SUMPRODUCT((MONTH({P}!H2:H501)={i})*(YEAR({P}!H2:H501)=YEAR(TODAY()))*(({P}!G2:G501="Discovery Booked")+({P}!G2:G501="Discovery Done")+({P}!G2:G501="Proposal Sent")+({P}!G2:G501="Won")+({P}!G2:G501="Lost")))',
            f'=SUMPRODUCT((MONTH({P}!H2:H501)={i})*(YEAR({P}!H2:H501)=YEAR(TODAY()))*(({P}!G2:G501="Proposal Sent")+({P}!G2:G501="Won")+({P}!G2:G501="Lost")))',
            f'=SUMPRODUCT((MONTH({P}!R2:R501)={i})*(YEAR({P}!R2:R501)=YEAR(TODAY()))*({P}!G2:G501="Won"))',
            f'=SUMPRODUCT((MONTH({P}!R2:R501)={i})*(YEAR({P}!R2:R501)=YEAR(TODAY()))*({P}!G2:G501="Lost"))',
            f'=IFERROR(E{r}/(E{r}+F{r}),"")',
            f'=SUMPRODUCT((MONTH({P}!R2:R501)={i})*(YEAR({P}!R2:R501)=YEAR(TODAY()))*({P}!G2:G501="Won")*{P}!L2:L501)',
            f'=IFERROR(H{r}/E{r},"")',
        ])

    monthly_data.append([
        "TOTAL",
        '=SUM(B2:B13)', '=SUM(C2:C13)', '=SUM(D2:D13)',
        '=SUM(E2:E13)', '=SUM(F2:F13)',
        '=IFERROR(E14/(E14+F14),"")',
        '=SUM(H2:H13)', '=IFERROR(H14/E14,"")',
    ])

    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="'Monthly Summary'!A1:I14",
        valueInputOption="USER_ENTERED",
        body={"values": monthly_data}
    ).execute()

    # ══════════════════════════════════════════════════════════
    # FORMATTING
    # ══════════════════════════════════════════════════════════
    fmt_requests = []

    # --- Pipeline tab ---
    # Header row
    fmt_requests.append({
        "repeatCell": {
            "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1,
                      "startColumnIndex": 0, "endColumnIndex": 20},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": INK,
                    "textFormat": {"bold": True, "foregroundColor": GOLD, "fontSize": 10},
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE",
                    "padding": {"top": 6, "bottom": 6, "left": 4, "right": 4},
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,padding)",
        }
    })

    # Header row height
    fmt_requests.append({
        "updateDimensionProperties": {
            "range": {"sheetId": 0, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
            "properties": {"pixelSize": 40},
            "fields": "pixelSize",
        }
    })

    # Alternating rows
    fmt_requests.append({
        "addBanding": {
            "bandedRange": {
                "bandedRangeId": 1,
                "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 501,
                          "startColumnIndex": 0, "endColumnIndex": 20},
                "rowProperties": {
                    "headerColor": INK,
                    "firstBandColor": WHITE,
                    "secondBandColor": PAPER,
                },
            }
        }
    })

    # Tab color: gold
    fmt_requests.append({
        "updateSheetProperties": {
            "properties": {"sheetId": 0, "tabColorStyle": {"rgbColor": GOLD}},
            "fields": "tabColorStyle",
        }
    })

    # Column widths
    pipeline_widths = {
        0: 200, 1: 160, 2: 220, 3: 130, 4: 140, 5: 120,
        6: 140, 7: 100, 8: 110, 9: 200,
        10: 150, 11: 120,
        12: 100, 13: 280, 14: 100,
        15: 220, 16: 100,
        17: 100, 18: 160, 19: 300,
    }
    for col, width in pipeline_widths.items():
        fmt_requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": 0, "dimension": "COLUMNS",
                          "startIndex": col, "endIndex": col + 1},
                "properties": {"pixelSize": width},
                "fields": "pixelSize",
            }
        })

    # --- Dashboard tab ---
    # Title
    fmt_requests.append({
        "repeatCell": {
            "range": {"sheetId": 1, "startRowIndex": 0, "endRowIndex": 1,
                      "startColumnIndex": 0, "endColumnIndex": 5},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": INK,
                    "textFormat": {"bold": True, "foregroundColor": GOLD, "fontSize": 14},
                    "padding": {"top": 10, "bottom": 10, "left": 8},
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,padding)",
        }
    })

    fmt_requests.append({
        "mergeCells": {
            "range": {"sheetId": 1, "startRowIndex": 0, "endRowIndex": 1,
                      "startColumnIndex": 0, "endColumnIndex": 5},
            "mergeType": "MERGE_ALL",
        }
    })

    # Find section header row indices in dashboard_data
    section_rows = []
    for i, row in enumerate(dashboard_data):
        if row and row[0] in ("PIPELINE OVERVIEW", "LEADS BY STAGE",
                              "REVENUE BY SOURCE (Won)", "REVENUE BY ICP (Won)",
                              "LEADS BY SOURCE (All)", "MONTHLY CLOSE RATE"):
            section_rows.append(i)

    for row_idx in section_rows:
        fmt_requests.append({
            "repeatCell": {
                "range": {"sheetId": 1, "startRowIndex": row_idx, "endRowIndex": row_idx + 1,
                          "startColumnIndex": 0, "endColumnIndex": 5},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": INK,
                        "textFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 11},
                        "padding": {"top": 4, "bottom": 4, "left": 6},
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,padding)",
            }
        })

    # KPI values (B4:B9) — gold, large
    fmt_requests.append({
        "repeatCell": {
            "range": {"sheetId": 1, "startRowIndex": 3, "endRowIndex": 9,
                      "startColumnIndex": 1, "endColumnIndex": 2},
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {"bold": True, "foregroundColor": GOLD, "fontSize": 14},
                }
            },
            "fields": "userEnteredFormat.textFormat",
        }
    })

    # KPI labels bold
    fmt_requests.append({
        "repeatCell": {
            "range": {"sheetId": 1, "startRowIndex": 3, "endRowIndex": 9,
                      "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {
                "userEnteredFormat": {"textFormat": {"bold": True, "fontSize": 11}}
            },
            "fields": "userEnteredFormat.textFormat",
        }
    })

    # Currency/percent formatting for dashboard KPI cells
    for row_idx, fmt_type in [(4, "CURRENCY"), (5, "CURRENCY"), (6, "PERCENT"), (7, "CURRENCY")]:
        pattern = "$#,##0" if fmt_type == "CURRENCY" else "0%"
        fmt_requests.append({
            "repeatCell": {
                "range": {"sheetId": 1, "startRowIndex": row_idx, "endRowIndex": row_idx + 1,
                          "startColumnIndex": 1, "endColumnIndex": 2},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": fmt_type, "pattern": pattern}}},
                "fields": "userEnteredFormat.numberFormat",
            }
        })

    # Dashboard column widths
    for col, width in {0: 200, 1: 180, 2: 100, 3: 140, 4: 100}.items():
        fmt_requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": 1, "dimension": "COLUMNS",
                          "startIndex": col, "endIndex": col + 1},
                "properties": {"pixelSize": width},
                "fields": "pixelSize",
            }
        })

    # --- Monthly Summary tab ---
    fmt_requests.append({
        "repeatCell": {
            "range": {"sheetId": 2, "startRowIndex": 0, "endRowIndex": 1,
                      "startColumnIndex": 0, "endColumnIndex": 9},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": INK,
                    "textFormat": {"bold": True, "foregroundColor": GOLD, "fontSize": 10},
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE",
                    "padding": {"top": 6, "bottom": 6},
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,padding)",
        }
    })

    # Totals row
    fmt_requests.append({
        "repeatCell": {
            "range": {"sheetId": 2, "startRowIndex": 13, "endRowIndex": 14,
                      "startColumnIndex": 0, "endColumnIndex": 9},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": INK,
                    "textFormat": {"bold": True, "foregroundColor": GOLD, "fontSize": 10},
                    "horizontalAlignment": "CENTER",
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
        }
    })

    # Alternating rows
    fmt_requests.append({
        "addBanding": {
            "bandedRange": {
                "bandedRangeId": 2,
                "range": {"sheetId": 2, "startRowIndex": 0, "endRowIndex": 14,
                          "startColumnIndex": 0, "endColumnIndex": 9},
                "rowProperties": {
                    "headerColor": INK,
                    "firstBandColor": WHITE,
                    "secondBandColor": PAPER,
                },
            }
        }
    })

    # Close Rate (G) — percent
    fmt_requests.append({
        "repeatCell": {
            "range": {"sheetId": 2, "startRowIndex": 1, "endRowIndex": 14,
                      "startColumnIndex": 6, "endColumnIndex": 7},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0%"}}},
            "fields": "userEnteredFormat.numberFormat",
        }
    })

    # Revenue (H) + Avg Deal Size (I) — currency
    fmt_requests.append({
        "repeatCell": {
            "range": {"sheetId": 2, "startRowIndex": 1, "endRowIndex": 14,
                      "startColumnIndex": 7, "endColumnIndex": 9},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
            "fields": "userEnteredFormat.numberFormat",
        }
    })

    # Monthly Summary column widths
    for col, width in {0: 120, 1: 90, 2: 130, 3: 130, 4: 70, 5: 70, 6: 100, 7: 120, 8: 120}.items():
        fmt_requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": 2, "dimension": "COLUMNS",
                          "startIndex": col, "endIndex": col + 1},
                "properties": {"pixelSize": width},
                "fields": "pixelSize",
            }
        })

    # Apply all formatting
    all_requests = validation_requests + currency_requests + fmt_requests
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": all_requests}
    ).execute()

    print(f"\nSales Pipeline created successfully!")
    print(f"URL: {url}")
    print(f"\nTabs:")
    print(f"  1. Pipeline — unified lead tracking (A:T)")
    print(f"  2. Dashboard — KPIs, stage/source/ICP breakdowns")
    print(f"  3. Monthly Summary — funnel metrics by month")


if __name__ == "__main__":
    main()
