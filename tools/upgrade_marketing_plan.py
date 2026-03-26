"""
Upgrade Marketing Plan & KPI Tracker with enhanced features.
Adds: conversion funnel, revenue progress, today's focus, weekly summaries,
      Monthly Review tab, Referral Tracker tab, award deadlines, overdue highlighting.

Usage:
    python3 tools/upgrade_marketing_plan.py
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from google_sheets_auth import get_sheets_service

# Brand colors
INK = {"red": 0.102, "green": 0.102, "blue": 0.094}
GOLD = {"red": 0.788, "green": 0.663, "blue": 0.431}
PAPER = {"red": 0.965, "green": 0.957, "blue": 0.941}
WHITE = {"red": 1, "green": 1, "blue": 1}
LIGHT_GOLD = {"red": 0.95, "green": 0.93, "blue": 0.88}
GREEN = {"red": 0.72, "green": 0.88, "blue": 0.73}
YELLOW = {"red": 1.0, "green": 0.95, "blue": 0.7}
RED_LIGHT = {"red": 1.0, "green": 0.82, "blue": 0.82}
BLUE_LIGHT = {"red": 0.85, "green": 0.92, "blue": 1.0}


def main():
    sheet_id = os.getenv("MARKETING_PLAN_SHEET_ID")
    if not sheet_id:
        print("ERROR: MARKETING_PLAN_SHEET_ID not found in .env")
        return

    sheets = get_sheets_service()

    # ════════════════════════════════════════════════════════════
    # STEP 1: ADD NEW TABS (skip if they already exist)
    # ════════════════════════════════════════════════════════════
    meta = sheets.spreadsheets().get(spreadsheetId=sheet_id).execute()
    existing_titles = {s["properties"]["title"] for s in meta["sheets"]}

    add_tabs_requests = []
    if "Monthly Review" not in existing_titles:
        add_tabs_requests.append({"addSheet": {"properties": {"title": "Monthly Review", "sheetId": 100, "gridProperties": {"frozenRowCount": 1}}}})
    if "Referral Tracker" not in existing_titles:
        add_tabs_requests.append({"addSheet": {"properties": {"title": "Referral Tracker", "sheetId": 101, "gridProperties": {"frozenRowCount": 1, "frozenColumnCount": 1}}}})

    if add_tabs_requests:
        sheets.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": add_tabs_requests}).execute()
        print("Added new tabs")
    else:
        print("Tabs already exist, skipping creation")

    # ════════════════════════════════════════════════════════════
    # STEP 2: REBUILD DAILY TRACKER WITH DAY COLUMN + WEEKLY SUMMARIES
    # ════════════════════════════════════════════════════════════

    # Clear old Daily Tracker data
    sheets.spreadsheets().values().clear(
        spreadsheetId=sheet_id,
        range="'Daily Tracker'!A1:P500"
    ).execute()

    tracker_headers = [
        "Date",                    # A
        "Day",                     # B
        "Cold Emails",             # C
        "Replies",                 # D
        "IG Posts",                # E
        "LI Posts",                # F
        "GBP Updates",             # G
        "Engagement",              # H - Comments, DMs, likes on target accounts
        "Referral Asks",           # I
        "New Leads",               # J
        "Google Reviews",          # K
        "Quotes Sent",             # L
        "Deals Won",               # M
        "Revenue Booked",          # N
        "Website Sessions",        # O
        "Notes",                   # P
    ]

    tracker_summary = [
        "YTD TOTALS", "",
        '=SUMPRODUCT((LEFT(A4:A600,1)<>"W")*ISNUMBER(C4:C600)*C4:C600)',
        '=SUMPRODUCT((LEFT(A4:A600,1)<>"W")*ISNUMBER(D4:D600)*D4:D600)',
        '=SUMPRODUCT((LEFT(A4:A600,1)<>"W")*ISNUMBER(E4:E600)*E4:E600)',
        '=SUMPRODUCT((LEFT(A4:A600,1)<>"W")*ISNUMBER(F4:F600)*F4:F600)',
        '=SUMPRODUCT((LEFT(A4:A600,1)<>"W")*ISNUMBER(G4:G600)*G4:G600)',
        '=SUMPRODUCT((LEFT(A4:A600,1)<>"W")*ISNUMBER(H4:H600)*H4:H600)',
        '=SUMPRODUCT((LEFT(A4:A600,1)<>"W")*ISNUMBER(I4:I600)*I4:I600)',
        '=SUMPRODUCT((LEFT(A4:A600,1)<>"W")*ISNUMBER(J4:J600)*J4:J600)',
        '=SUMPRODUCT((LEFT(A4:A600,1)<>"W")*ISNUMBER(K4:K600)*K4:K600)',
        '=SUMPRODUCT((LEFT(A4:A600,1)<>"W")*ISNUMBER(L4:L600)*L4:L600)',
        '=SUMPRODUCT((LEFT(A4:A600,1)<>"W")*ISNUMBER(M4:M600)*M4:M600)',
        '=SUMPRODUCT((LEFT(A4:A600,1)<>"W")*ISNUMBER(N4:N600)*N4:N600)',
        '=SUMPRODUCT((LEFT(A4:A600,1)<>"W")*ISNUMBER(O4:O600)*O4:O600)',
        "",
    ]

    # Daily targets row
    tracker_targets = [
        "DAILY TARGETS", "",
        "10", "", "~0.4", "~0.3", "", "3-5", "", "", "", "", "", "", "", "Use as reference"
    ]

    # Build rows with weekly summaries inserted
    start_date = datetime(2026, 3, 23)
    end_date = datetime(2026, 12, 31)
    current = start_date
    rows = []
    week_start_row = 4  # First data row (1-indexed in sheet, 0-indexed here offset by headers)
    days_in_week = 0
    current_row = 4  # Track actual sheet row number

    while current <= end_date:
        day_name = current.strftime("%a")
        rows.append([current.strftime("%Y-%m-%d"), day_name] + [""] * 14)
        days_in_week += 1
        current_row += 1

        # Insert weekly summary on Sunday night
        if current.weekday() == 6:  # Sunday
            week_num = current.isocalendar()[1]
            summary_row_num = current_row  # This is where the summary will be
            first_day_row = summary_row_num - days_in_week
            last_day_row = summary_row_num - 1

            weekly_summary = [
                f"WEEK {week_num} TOTAL", "",
            ]
            # Sum columns C through O for this week's daily rows
            for col_letter in ["C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O"]:
                weekly_summary.append(f'=SUM({col_letter}{first_day_row}:{col_letter}{last_day_row})')
            weekly_summary.append("")  # Notes column
            rows.append(weekly_summary)
            current_row += 1
            days_in_week = 0

        current += timedelta(days=1)

    # Final partial week summary if needed
    if days_in_week > 0:
        week_num = (current - timedelta(days=1)).isocalendar()[1]
        first_day_row = current_row - days_in_week
        last_day_row = current_row - 1
        weekly_summary = [f"WEEK {week_num} TOTAL", ""]
        for col_letter in ["C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O"]:
            weekly_summary.append(f'=SUM({col_letter}{first_day_row}:{col_letter}{last_day_row})')
        weekly_summary.append("")
        rows.append(weekly_summary)

    all_tracker_data = [tracker_headers, tracker_summary, tracker_targets] + rows

    sheets.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"'Daily Tracker'!A1:P{len(all_tracker_data)}",
        valueInputOption="USER_ENTERED",
        body={"values": all_tracker_data}
    ).execute()
    print(f"Rebuilt Daily Tracker with {len(rows)} rows (daily entries + weekly summaries)")

    # ════════════════════════════════════════════════════════════
    # STEP 3: UPGRADE DASHBOARD
    # ════════════════════════════════════════════════════════════

    # Clear and rewrite dashboard
    sheets.spreadsheets().values().clear(
        spreadsheetId=sheet_id,
        range="Dashboard!A1:H60"
    ).execute()

    dashboard_data = [
        ["MARKETING PLAN & KPI TRACKER", "", "", "", "", "", "", ""],
        ["Matt Anthony Photography | 2026", "", "", "", "", "", "", ""],
        [""],
        # --- REVENUE PROGRESS ---
        ["2026 REVENUE PROGRESS", "", "", "", "", "", "", ""],
        ["Target", "YTD Revenue", "% of Target", "Pace Required", "Monthly Avg Needed", "On Track?", "", ""],
        [
            "$125,000",
            '=SUMPRODUCT((LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!N4:N600)*\'Daily Tracker\'!N4:N600)',
            '=IFERROR(B6/125000,0)',
            '=125000*(DAYS(TODAY(),DATE(2026,1,1))/365)',
            '=IFERROR((125000-B6)/(12-MONTH(TODAY())+1),"")',
            '=IF(B6>=D6,"Ahead of Pace","Behind Pace")',
            "", "",
        ],
        [""],
        # --- CONVERSION FUNNEL ---
        ["CONVERSION FUNNEL (This Month)", "", "", "", "", "", "", ""],
        ["Stage", "Count", "Conversion Rate", "Benchmark", "Status", "", "", ""],
        [
            "Emails Sent",
            '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!C4:C600)*\'Daily Tracker\'!C4:C600)',
            "", "200/mo", '=IF(B10>=200,"Hit",IF(B10>=140,"On Track","Behind"))', "", "", "",
        ],
        [
            "Replies Received",
            '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!D4:D600)*\'Daily Tracker\'!D4:D600)',
            '=IFERROR(B11/B10,"")', "5%", '=IF(C11>=0.05,"Good",IF(C11>=0.03,"OK","Low"))', "", "", "",
        ],
        [
            "Meetings Booked",
            '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!J4:J600)*\'Daily Tracker\'!J4:J600)',
            '=IFERROR(B12/B11,"")', "30% of replies", '=IF(B12>=3,"Hit",IF(B12>=2,"On Track","Behind"))', "", "", "",
        ],
        [
            "Proposals Sent",
            '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!L4:L600)*\'Daily Tracker\'!L4:L600)',
            '=IFERROR(B13/B12,"")', "80% of meetings", "", "", "", "",
        ],
        [
            "Deals Won",
            '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!M4:M600)*\'Daily Tracker\'!M4:M600)',
            '=IFERROR(B14/B13,"")', "40% of proposals", "", "", "", "",
        ],
        [
            "Revenue",
            '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!N4:N600)*\'Daily Tracker\'!N4:N600)',
            "", "", "", "", "", "",
        ],
        [""],
        # --- TODAY'S FOCUS ---
        ["TODAY'S FOCUS", "", "", "", "", "", "", ""],
        ["Activity", "Target", "Done Today", "Remaining", "Status", "", "", ""],
        [
            "Cold Emails",
            "10",
            '=IFERROR(INDEX(\'Daily Tracker\'!C4:C600,MATCH(TODAY(),\'Daily Tracker\'!A4:A600,0)),0)',
            '=MAX(B19-C19,0)',
            '=IF(C19>=B19,"Done",IF(C19>0,"In Progress","Not Started"))',
            "", "", "",
        ],
        [
            "Engagement Actions",
            "3",
            '=IFERROR(INDEX(\'Daily Tracker\'!H4:H600,MATCH(TODAY(),\'Daily Tracker\'!A4:A600,0)),0)',
            '=MAX(B20-C20,0)',
            '=IF(C20>=B20,"Done",IF(C20>0,"In Progress","Not Started"))',
            "", "", "",
        ],
        [
            "IG Story",
            "1",
            "",
            "",
            '=IF(C21>=1,"Done","Not Done")',
            "", "", "",
        ],
        [
            "Check & Respond (DMs, comments)",
            "1",
            "",
            "",
            '=IF(C22>=1,"Done","Not Done")',
            "", "", "",
        ],
        [""],
        # --- THIS WEEK ---
        ["THIS WEEK", "", "", "", "", "", "", ""],
        ["Metric", "Target", "Actual", "% Hit", "Status", "vs Last Week", "", ""],
        [
            "Cold Emails Sent", "50",
            '=SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A4:A600,2)=WEEKNUM(TODAY(),2))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!C4:C600)*\'Daily Tracker\'!C4:C600)',
            '=IFERROR(C26/B26,"")',
            '=IF(D26="","",IF(D26>=1,"On Track",IF(D26>=0.7,"Behind","At Risk")))',
            '=IFERROR(C26-SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A4:A600,2)=WEEKNUM(TODAY(),2)-1)*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!C4:C600)*\'Daily Tracker\'!C4:C600),"")',
            "", "",
        ],
        [
            "Instagram Posts", "3",
            '=SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A4:A600,2)=WEEKNUM(TODAY(),2))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!E4:E600)*\'Daily Tracker\'!E4:E600)',
            '=IFERROR(C27/B27,"")',
            '=IF(D27="","",IF(D27>=1,"On Track",IF(D27>=0.7,"Behind","At Risk")))',
            '=IFERROR(C27-SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A4:A600,2)=WEEKNUM(TODAY(),2)-1)*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!E4:E600)*\'Daily Tracker\'!E4:E600),"")',
            "", "",
        ],
        [
            "LinkedIn Posts", "2",
            '=SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A4:A600,2)=WEEKNUM(TODAY(),2))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!F4:F600)*\'Daily Tracker\'!F4:F600)',
            '=IFERROR(C28/B28,"")',
            '=IF(D28="","",IF(D28>=1,"On Track",IF(D28>=0.7,"Behind","At Risk")))',
            '=IFERROR(C28-SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A4:A600,2)=WEEKNUM(TODAY(),2)-1)*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!F4:F600)*\'Daily Tracker\'!F4:F600),"")',
            "", "",
        ],
        [
            "GBP Updates", "1",
            '=SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A4:A600,2)=WEEKNUM(TODAY(),2))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!G4:G600)*\'Daily Tracker\'!G4:G600)',
            '=IFERROR(C29/B29,"")',
            '=IF(D29="","",IF(D29>=1,"On Track",IF(D29>=0.7,"Behind","At Risk")))',
            "",
            "", "",
        ],
        [
            "Engagement Actions", "15",
            '=SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A4:A600,2)=WEEKNUM(TODAY(),2))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!H4:H600)*\'Daily Tracker\'!H4:H600)',
            '=IFERROR(C30/B30,"")',
            '=IF(D30="","",IF(D30>=1,"On Track",IF(D30>=0.7,"Behind","At Risk")))',
            '=IFERROR(C30-SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A4:A600,2)=WEEKNUM(TODAY(),2)-1)*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!H4:H600)*\'Daily Tracker\'!H4:H600),"")',
            "", "",
        ],
        [
            "Referral Asks", "2",
            '=SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A4:A600,2)=WEEKNUM(TODAY(),2))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!I4:I600)*\'Daily Tracker\'!I4:I600)',
            '=IFERROR(C31/B31,"")',
            '=IF(D31="","",IF(D31>=1,"On Track",IF(D31>=0.7,"Behind","At Risk")))',
            "",
            "", "",
        ],
        [
            "New Leads", "",
            '=SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A4:A600,2)=WEEKNUM(TODAY(),2))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!J4:J600)*\'Daily Tracker\'!J4:J600)',
            "",
            "",
            '=IFERROR(C32-SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A4:A600,2)=WEEKNUM(TODAY(),2)-1)*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!J4:J600)*\'Daily Tracker\'!J4:J600),"")',
            "", "",
        ],
        [""],
        # --- THIS MONTH ---
        ["THIS MONTH", "", "", "", "", "", "", ""],
        ["Metric", "Target", "Actual", "% Hit", "Status", "vs Last Month", "", ""],
        [
            "Cold Emails Sent", "200",
            '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!C4:C600)*\'Daily Tracker\'!C4:C600)',
            '=IFERROR(C36/B36,"")',
            '=IF(D36="","",IF(D36>=1,"On Track",IF(D36>=0.7,"Behind","At Risk")))',
            '=IFERROR(C36-SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY())-1)*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!C4:C600)*\'Daily Tracker\'!C4:C600),"")',
            "", "",
        ],
        [
            "Replies", "",
            '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!D4:D600)*\'Daily Tracker\'!D4:D600)',
            "", "", "", "", "",
        ],
        [
            "Instagram Posts", "12",
            '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!E4:E600)*\'Daily Tracker\'!E4:E600)',
            '=IFERROR(C38/B38,"")',
            '=IF(D38="","",IF(D38>=1,"On Track",IF(D38>=0.7,"Behind","At Risk")))',
            '=IFERROR(C38-SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY())-1)*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!E4:E600)*\'Daily Tracker\'!E4:E600),"")',
            "", "",
        ],
        [
            "LinkedIn Posts", "8",
            '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!F4:F600)*\'Daily Tracker\'!F4:F600)',
            '=IFERROR(C39/B39,"")',
            '=IF(D39="","",IF(D39>=1,"On Track",IF(D39>=0.7,"Behind","At Risk")))',
            '=IFERROR(C39-SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY())-1)*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!F4:F600)*\'Daily Tracker\'!F4:F600),"")',
            "", "",
        ],
        [
            "Google Reviews", "2",
            '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!K4:K600)*\'Daily Tracker\'!K4:K600)',
            '=IFERROR(C40/B40,"")',
            '=IF(D40="","",IF(D40>=1,"On Track",IF(D40>=0.5,"Behind","At Risk")))',
            "", "", "",
        ],
        [
            "New Leads", "",
            '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!J4:J600)*\'Daily Tracker\'!J4:J600)',
            "", "", "", "", "",
        ],
        [
            "Quotes Sent", "",
            '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!L4:L600)*\'Daily Tracker\'!L4:L600)',
            "", "", "", "", "",
        ],
        [
            "Deals Won", "",
            '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!M4:M600)*\'Daily Tracker\'!M4:M600)',
            "", "", "", "", "",
        ],
        [
            "Revenue Booked", "",
            '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!N4:N600)*\'Daily Tracker\'!N4:N600)',
            "", "", "", "", "",
        ],
        [""],
        # --- CHANNEL HEALTH ---
        ["CHANNEL HEALTH (YTD)", "", "", "", "", "", "", ""],
        ["Channel", "Leads", "Revenue", "Cost", "ROI", "Cost/Lead", "Avg Deal", "Trend"],
        ["Cold Email", '=COUNTIF(\'Lead Attribution\'!D2:D500,"Cold Email")', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Cold Email")*(\'Lead Attribution\'!H2:H500))', '=SUMIF(\'Budget & ROI\'!A2:A100,"Cold Email",\'Budget & ROI\'!E2:E100)', '=IFERROR((C48-D48)/D48,"")', '=IFERROR(D48/B48,"")', '=IFERROR(C48/COUNTIFS(\'Lead Attribution\'!D2:D500,"Cold Email",\'Lead Attribution\'!F2:F500,"Won"),"")', ""],
        ["Instagram", '=COUNTIF(\'Lead Attribution\'!D2:D500,"Instagram")', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Instagram")*(\'Lead Attribution\'!H2:H500))', '=SUMIF(\'Budget & ROI\'!A2:A100,"Instagram",\'Budget & ROI\'!E2:E100)', '=IFERROR((C49-D49)/D49,"")', '=IFERROR(D49/B49,"")', '=IFERROR(C49/COUNTIFS(\'Lead Attribution\'!D2:D500,"Instagram",\'Lead Attribution\'!F2:F500,"Won"),"")', ""],
        ["LinkedIn", '=COUNTIF(\'Lead Attribution\'!D2:D500,"LinkedIn")', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="LinkedIn")*(\'Lead Attribution\'!H2:H500))', '=SUMIF(\'Budget & ROI\'!A2:A100,"LinkedIn",\'Budget & ROI\'!E2:E100)', '=IFERROR((C50-D50)/D50,"")', '=IFERROR(D50/B50,"")', '=IFERROR(C50/COUNTIFS(\'Lead Attribution\'!D2:D500,"LinkedIn",\'Lead Attribution\'!F2:F500,"Won"),"")', ""],
        ["Google/SEO", '=COUNTIF(\'Lead Attribution\'!D2:D500,"Google/SEO")', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Google/SEO")*(\'Lead Attribution\'!H2:H500))', '=SUMIF(\'Budget & ROI\'!A2:A100,"Google/SEO",\'Budget & ROI\'!E2:E100)', '=IFERROR((C51-D51)/D51,"")', '=IFERROR(D51/B51,"")', '=IFERROR(C51/COUNTIFS(\'Lead Attribution\'!D2:D500,"Google/SEO",\'Lead Attribution\'!F2:F500,"Won"),"")', ""],
        ["GBP", '=COUNTIF(\'Lead Attribution\'!D2:D500,"GBP")', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="GBP")*(\'Lead Attribution\'!H2:H500))', '=SUMIF(\'Budget & ROI\'!A2:A100,"GBP",\'Budget & ROI\'!E2:E100)', '=IFERROR((C52-D52)/D52,"")', '=IFERROR(D52/B52,"")', '=IFERROR(C52/COUNTIFS(\'Lead Attribution\'!D2:D500,"GBP",\'Lead Attribution\'!F2:F500,"Won"),"")', ""],
        ["Referral", '=COUNTIF(\'Lead Attribution\'!D2:D500,"Referral")', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Referral")*(\'Lead Attribution\'!H2:H500))', '=SUMIF(\'Budget & ROI\'!A2:A100,"Referral",\'Budget & ROI\'!E2:E100)', '=IFERROR((C53-D53)/D53,"")', '=IFERROR(D53/B53,"")', '=IFERROR(C53/COUNTIFS(\'Lead Attribution\'!D2:D500,"Referral",\'Lead Attribution\'!F2:F500,"Won"),"")', ""],
        ["Awards", '=COUNTIF(\'Lead Attribution\'!D2:D500,"Awards")', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Awards")*(\'Lead Attribution\'!H2:H500))', '=SUMIF(\'Budget & ROI\'!A2:A100,"Awards",\'Budget & ROI\'!E2:E100)', '=IFERROR((C54-D54)/D54,"")', '=IFERROR(D54/B54,"")', '=IFERROR(C54/COUNTIFS(\'Lead Attribution\'!D2:D500,"Awards",\'Lead Attribution\'!F2:F500,"Won"),"")', ""],
        ["Pricing Guide", '=COUNTIF(\'Lead Attribution\'!D2:D500,"Pricing Guide")', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Pricing Guide")*(\'Lead Attribution\'!H2:H500))', '=SUMIF(\'Budget & ROI\'!A2:A100,"Pricing Guide",\'Budget & ROI\'!E2:E100)', '=IFERROR((C55-D55)/D55,"")', '=IFERROR(D55/B55,"")', '=IFERROR(C55/COUNTIFS(\'Lead Attribution\'!D2:D500,"Pricing Guide",\'Lead Attribution\'!F2:F500,"Won"),"")', ""],
        ["TOTAL", '=SUM(B48:B55)', '=SUM(C48:C55)', '=SUM(D48:D55)', '=IFERROR((C56-D56)/D56,"")', '=IFERROR(D56/B56,"")', '=IFERROR(C56/SUMPRODUCT((\'Lead Attribution\'!F2:F500="Won")*1),"")', ""],
    ]

    sheets.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="Dashboard!A1:H56",
        valueInputOption="USER_ENTERED",
        body={"values": dashboard_data}
    ).execute()
    print("Upgraded Dashboard with revenue progress, funnel, today's focus, week-over-week")

    # ════════════════════════════════════════════════════════════
    # STEP 4: MONTHLY REVIEW TAB
    # ════════════════════════════════════════════════════════════
    months = ["March", "April", "May", "June", "July", "August",
              "September", "October", "November", "December"]
    month_nums = list(range(3, 13))

    monthly_review_data = [
        ["Month", "Emails Sent", "Replies", "IG Posts", "LI Posts", "Engagement", "New Leads",
         "Quotes Sent", "Deals Won", "Revenue", "Best Channel", "What Worked", "What to Improve", "Key Learning"],
    ]

    for i, month in enumerate(months):
        mn = month_nums[i]
        row = [
            month,
            f'=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)={mn})*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!C4:C600)*\'Daily Tracker\'!C4:C600)',
            f'=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)={mn})*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!D4:D600)*\'Daily Tracker\'!D4:D600)',
            f'=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)={mn})*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!E4:E600)*\'Daily Tracker\'!E4:E600)',
            f'=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)={mn})*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!F4:F600)*\'Daily Tracker\'!F4:F600)',
            f'=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)={mn})*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!H4:H600)*\'Daily Tracker\'!H4:H600)',
            f'=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)={mn})*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!J4:J600)*\'Daily Tracker\'!J4:J600)',
            f'=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)={mn})*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!L4:L600)*\'Daily Tracker\'!L4:L600)',
            f'=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)={mn})*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!M4:M600)*\'Daily Tracker\'!M4:M600)',
            f'=SUMPRODUCT((MONTH(\'Daily Tracker\'!A4:A600)={mn})*(YEAR(\'Daily Tracker\'!A4:A600)=2026)*(LEFT(\'Daily Tracker\'!A4:A600,1)<>"W")*ISNUMBER(\'Daily Tracker\'!N4:N600)*\'Daily Tracker\'!N4:N600)',
            "",  # Best Channel - manual
            "",  # What Worked - manual
            "",  # What to Improve - manual
            "",  # Key Learning - manual
        ]
        monthly_review_data.append(row)

    # Totals row
    monthly_review_data.append([
        "TOTAL",
        '=SUM(B2:B11)', '=SUM(C2:C11)', '=SUM(D2:D11)', '=SUM(E2:E11)',
        '=SUM(F2:F11)', '=SUM(G2:G11)', '=SUM(H2:H11)', '=SUM(I2:I11)',
        '=SUM(J2:J11)', "", "", "", "",
    ])

    # MoM change row
    monthly_review_data.append([""])
    monthly_review_data.append(["MONTH-OVER-MONTH CHANGE", "", "", "", "", "", "", "", "", "", "", "", "", ""])
    for i, month in enumerate(months):
        if i == 0:
            monthly_review_data.append([month, "—", "—", "—", "—", "—", "—", "—", "—", "—", "", "", "", ""])
        else:
            r = i + 2  # row of current month
            pr = r - 1  # row of previous month
            row = [month]
            for col in ["B", "C", "D", "E", "F", "G", "H", "I", "J"]:
                row.append(f'=IFERROR({col}{r}-{col}{pr},"")')
            row.extend(["", "", "", ""])
            monthly_review_data.append(row)

    sheets.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="'Monthly Review'!A1:N25",
        valueInputOption="USER_ENTERED",
        body={"values": monthly_review_data}
    ).execute()
    print("Created Monthly Review tab with auto-calculated metrics and MoM changes")

    # ════════════════════════════════════════════════════════════
    # STEP 5: REFERRAL TRACKER TAB
    # ════════════════════════════════════════════════════════════
    referral_data = [
        [
            "Date Asked",         # A
            "Referrer Name",      # B
            "Referrer Company",   # C
            "Relationship",       # D
            "Referred Lead",      # E
            "Referred Company",   # F
            "Lead ICP",           # G
            "Estimated Value",    # H
            "Stage",              # I
            "Revenue Won",        # J
            "Thank You Sent",     # K
            "Thank You Type",     # L
            "Notes",              # M
        ],
    ]

    sheets.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="'Referral Tracker'!A1:M1",
        valueInputOption="RAW",
        body={"values": referral_data}
    ).execute()
    print("Created Referral Tracker tab")

    # ════════════════════════════════════════════════════════════
    # STEP 6: UPDATE ROADMAP WITH AWARD DEADLINES
    # ════════════════════════════════════════════════════════════

    # Read existing roadmap to find where to append
    existing_roadmap = sheets.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range="'Q2-Q4 Roadmap'!A1:I30"
    ).execute()
    existing_rows = existing_roadmap.get("values", [])
    next_row = len(existing_rows) + 2  # +1 for blank row separator

    award_deadlines = [
        [""],
        ["AWARD & SUBMISSION DEADLINES", "", "", "", "", "", "", "", ""],
        ["Quarter", "Award / Publication", "Channel", "Entry Requirements", "Deadline", "Status", "Submitted", "Fee", "Notes"],
        ["Q2", "AIBC Architecture Awards", "Awards", "Professional photography of BC project", "2026-05-15", "Not Started", "", "$150", "Check exact deadline"],
        ["Q2", "Georgie Awards (CHBA BC)", "Awards", "Builder project photography", "2026-06-01", "Not Started", "", "$100", "Builder must co-submit"],
        ["Q3", "RAIC Awards", "Awards", "Architectural photography excellence", "2026-08-01", "Not Started", "", "$200", "National scope"],
        ["Q3", "Western Living Design Awards", "Awards", "Interior/architecture photography", "2026-07-15", "Not Started", "", "$75", "Publication opportunity"],
        ["Q4", "Canadian Architect Awards", "Awards", "Significant Canadian project", "2026-10-01", "Not Started", "", "$150", ""],
        ["Q4", "Azure Magazine", "Awards", "Design publication feature pitch", "Ongoing", "Not Started", "", "$0", "Pitch via email"],
    ]

    sheets.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"'Q2-Q4 Roadmap'!A{next_row}:I{next_row + len(award_deadlines)}",
        valueInputOption="USER_ENTERED",
        body={"values": award_deadlines}
    ).execute()
    print("Added award deadlines to Roadmap")

    # ════════════════════════════════════════════════════════════
    # STEP 7: ALL FORMATTING
    # ════════════════════════════════════════════════════════════
    fmt = []

    # Remove old banding from original creation
    for banding_id in [10, 20, 30, 40]:
        fmt.append({"deleteBanding": {"bandedRangeId": banding_id}})

    # ── DASHBOARD FORMATTING ──

    # Title
    fmt.append({"repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 8},
        "cell": {"userEnteredFormat": {"backgroundColor": INK, "textFormat": {"bold": True, "foregroundColor": GOLD, "fontSize": 16}}},
        "fields": "userEnteredFormat(backgroundColor,textFormat)"
    }})
    fmt.append({"mergeCells": {"range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 8}, "mergeType": "MERGE_ALL"}})

    # Subtitle
    fmt.append({"repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": 8},
        "cell": {"userEnteredFormat": {"backgroundColor": INK, "textFormat": {"foregroundColor": PAPER, "fontSize": 11}}},
        "fields": "userEnteredFormat(backgroundColor,textFormat)"
    }})
    fmt.append({"mergeCells": {"range": {"sheetId": 0, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": 8}, "mergeType": "MERGE_ALL"}})

    # Section title rows (dark ink background, gold text)
    section_title_rows = [3, 8, 17, 24, 34, 46]
    for row in section_title_rows:
        fmt.append({"repeatCell": {
            "range": {"sheetId": 0, "startRowIndex": row, "endRowIndex": row + 1, "startColumnIndex": 0, "endColumnIndex": 8},
            "cell": {"userEnteredFormat": {"backgroundColor": INK, "textFormat": {"bold": True, "foregroundColor": GOLD, "fontSize": 12}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }})
        fmt.append({"mergeCells": {"range": {"sheetId": 0, "startRowIndex": row, "endRowIndex": row + 1, "startColumnIndex": 0, "endColumnIndex": 8}, "mergeType": "MERGE_ALL"}})

    # Sub-header rows (light gold background)
    sub_header_rows = [4, 9, 18, 25, 35, 47]
    for row in sub_header_rows:
        fmt.append({"repeatCell": {
            "range": {"sheetId": 0, "startRowIndex": row, "endRowIndex": row + 1, "startColumnIndex": 0, "endColumnIndex": 8},
            "cell": {"userEnteredFormat": {"backgroundColor": LIGHT_GOLD, "textFormat": {"bold": True, "foregroundColor": INK, "fontSize": 10}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }})

    # Revenue progress row - big gold numbers
    fmt.append({"repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 5, "endRowIndex": 6, "startColumnIndex": 0, "endColumnIndex": 6},
        "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "fontSize": 13, "foregroundColor": INK}}},
        "fields": "userEnteredFormat.textFormat"
    }})

    # Revenue progress - currency formatting
    for col in [0, 1, 3, 4]:  # Target, YTD, Pace, Monthly needed
        fmt.append({"repeatCell": {
            "range": {"sheetId": 0, "startRowIndex": 5, "endRowIndex": 6, "startColumnIndex": col, "endColumnIndex": col + 1},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
            "fields": "userEnteredFormat.numberFormat"
        }})

    # Percentage for % of Target
    fmt.append({"repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 5, "endRowIndex": 6, "startColumnIndex": 2, "endColumnIndex": 3},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}}},
        "fields": "userEnteredFormat.numberFormat"
    }})

    # On Track/Behind conditional formatting for revenue pace
    for status, color in [("Ahead of Pace", GREEN), ("Behind Pace", RED_LIGHT)]:
        fmt.append({"addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": 0, "startRowIndex": 5, "endRowIndex": 6, "startColumnIndex": 5, "endColumnIndex": 6}],
                "booleanRule": {
                    "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": status}]},
                    "format": {"backgroundColor": color, "textFormat": {"bold": True}}
                }
            }, "index": 0
        }})

    # Funnel conversion rate formatting
    fmt.append({"repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 10, "endRowIndex": 15, "startColumnIndex": 2, "endColumnIndex": 3},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}}},
        "fields": "userEnteredFormat.numberFormat"
    }})

    # Funnel revenue currency
    fmt.append({"repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 15, "endRowIndex": 16, "startColumnIndex": 1, "endColumnIndex": 2},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
        "fields": "userEnteredFormat.numberFormat"
    }})

    # Status conditional formatting across all sections
    for start_row, end_row in [(10, 15), (19, 23), (26, 32), (36, 45)]:
        for status, color in [("On Track", GREEN), ("Hit", GREEN), ("Good", GREEN), ("Behind", YELLOW), ("OK", YELLOW), ("At Risk", RED_LIGHT), ("Low", RED_LIGHT)]:
            fmt.append({"addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": 0, "startRowIndex": start_row, "endRowIndex": end_row, "startColumnIndex": 4, "endColumnIndex": 5}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": status}]},
                        "format": {"backgroundColor": color, "textFormat": {"bold": True}}
                    }
                }, "index": 0
            }})

    # Today's Focus status formatting
    for status, color in [("Done", GREEN), ("In Progress", BLUE_LIGHT), ("Not Started", {"red": 0.93, "green": 0.93, "blue": 0.93}), ("Not Done", RED_LIGHT)]:
        fmt.append({"addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": 0, "startRowIndex": 18, "endRowIndex": 23, "startColumnIndex": 4, "endColumnIndex": 5}],
                "booleanRule": {
                    "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": status}]},
                    "format": {"backgroundColor": color, "textFormat": {"bold": True}}
                }
            }, "index": 0
        }})

    # Percentage format for weekly/monthly % Hit
    for start_row, end_row in [(25, 33), (35, 45)]:
        fmt.append({"repeatCell": {
            "range": {"sheetId": 0, "startRowIndex": start_row, "endRowIndex": end_row, "startColumnIndex": 3, "endColumnIndex": 4},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0%"}}},
            "fields": "userEnteredFormat.numberFormat"
        }})

    # Channel health currency + percentage
    fmt.append({"repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 47, "endRowIndex": 56, "startColumnIndex": 2, "endColumnIndex": 5},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
        "fields": "userEnteredFormat.numberFormat"
    }})
    fmt.append({"repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 47, "endRowIndex": 56, "startColumnIndex": 4, "endColumnIndex": 5},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0%"}}},
        "fields": "userEnteredFormat.numberFormat"
    }})
    fmt.append({"repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 47, "endRowIndex": 56, "startColumnIndex": 5, "endColumnIndex": 7},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
        "fields": "userEnteredFormat.numberFormat"
    }})

    # Totals row on channel health
    fmt.append({"repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 55, "endRowIndex": 56, "startColumnIndex": 0, "endColumnIndex": 8},
        "cell": {"userEnteredFormat": {"backgroundColor": INK, "textFormat": {"bold": True, "foregroundColor": GOLD}}},
        "fields": "userEnteredFormat(backgroundColor,textFormat)"
    }})

    # Dashboard column widths
    for col, width in {0: 220, 1: 100, 2: 100, 3: 100, 4: 110, 5: 120, 6: 100, 7: 100}.items():
        fmt.append({"updateDimensionProperties": {
            "range": {"sheetId": 0, "dimension": "COLUMNS", "startIndex": col, "endIndex": col + 1},
            "properties": {"pixelSize": width}, "fields": "pixelSize"
        }})

    # Monthly revenue currency
    for row in [43, 44]:
        fmt.append({"repeatCell": {
            "range": {"sheetId": 0, "startRowIndex": row, "endRowIndex": row + 1, "startColumnIndex": 2, "endColumnIndex": 3},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
            "fields": "userEnteredFormat.numberFormat"
        }})

    # ── DAILY TRACKER FORMATTING ──

    # Header row
    fmt.append({"repeatCell": {
        "range": {"sheetId": 1, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 16},
        "cell": {"userEnteredFormat": {
            "backgroundColor": INK, "textFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 10},
            "horizontalAlignment": "CENTER"
        }},
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
    }})

    # YTD Totals row
    fmt.append({"repeatCell": {
        "range": {"sheetId": 1, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": 16},
        "cell": {"userEnteredFormat": {
            "backgroundColor": INK, "textFormat": {"bold": True, "foregroundColor": GOLD, "fontSize": 10},
            "horizontalAlignment": "CENTER"
        }},
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
    }})

    # Daily targets row
    fmt.append({"repeatCell": {
        "range": {"sheetId": 1, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": 16},
        "cell": {"userEnteredFormat": {
            "backgroundColor": LIGHT_GOLD, "textFormat": {"bold": True, "foregroundColor": INK, "fontSize": 9, "italic": True},
            "horizontalAlignment": "CENTER"
        }},
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
    }})

    # Alternating rows
    fmt.append({"addBanding": {
        "bandedRange": {
            "bandedRangeId": 11,
            "range": {"sheetId": 1, "startRowIndex": 3, "endRowIndex": 500, "startColumnIndex": 0, "endColumnIndex": 16},
            "rowProperties": {"firstBandColor": WHITE, "secondBandColor": PAPER}
        }
    }})

    # Weekend highlighting
    fmt.append({"addConditionalFormatRule": {
        "rule": {
            "ranges": [{"sheetId": 1, "startRowIndex": 3, "endRowIndex": 500, "startColumnIndex": 0, "endColumnIndex": 16}],
            "booleanRule": {
                "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": '=AND(LEFT($A4,1)<>"W",OR(WEEKDAY(DATEVALUE($A4))=1,WEEKDAY(DATEVALUE($A4))=7))'}]},
                "format": {"backgroundColor": {"red": 0.92, "green": 0.92, "blue": 0.95}}
            }
        }, "index": 0
    }})

    # Weekly summary row highlighting
    fmt.append({"addConditionalFormatRule": {
        "rule": {
            "ranges": [{"sheetId": 1, "startRowIndex": 3, "endRowIndex": 500, "startColumnIndex": 0, "endColumnIndex": 16}],
            "booleanRule": {
                "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": '=LEFT($A4,4)="WEEK"'}]},
                "format": {"backgroundColor": INK, "textFormat": {"bold": True, "foregroundColor": GOLD}}
            }
        }, "index": 0
    }})

    # Highlight days where cold emails hit target (>=10)
    fmt.append({"addConditionalFormatRule": {
        "rule": {
            "ranges": [{"sheetId": 1, "startRowIndex": 3, "endRowIndex": 500, "startColumnIndex": 2, "endColumnIndex": 3}],
            "booleanRule": {
                "condition": {"type": "NUMBER_GREATER_THAN_EQ", "values": [{"userEnteredValue": "10"}]},
                "format": {"backgroundColor": GREEN}
            }
        }, "index": 0
    }})

    # Highlight days where engagement hit target (>=3)
    fmt.append({"addConditionalFormatRule": {
        "rule": {
            "ranges": [{"sheetId": 1, "startRowIndex": 3, "endRowIndex": 500, "startColumnIndex": 7, "endColumnIndex": 8}],
            "booleanRule": {
                "condition": {"type": "NUMBER_GREATER_THAN_EQ", "values": [{"userEnteredValue": "3"}]},
                "format": {"backgroundColor": GREEN}
            }
        }, "index": 0
    }})

    # Currency format for Revenue column (N)
    fmt.append({"repeatCell": {
        "range": {"sheetId": 1, "startRowIndex": 3, "endRowIndex": 500, "startColumnIndex": 13, "endColumnIndex": 14},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
        "fields": "userEnteredFormat.numberFormat"
    }})

    # Column widths
    tracker_widths = {0: 120, 1: 50, 2: 85, 3: 60, 4: 65, 5: 65, 6: 85, 7: 90, 8: 90, 9: 75, 10: 100, 11: 80, 12: 75, 13: 110, 14: 100, 15: 250}
    for col, width in tracker_widths.items():
        fmt.append({"updateDimensionProperties": {
            "range": {"sheetId": 1, "dimension": "COLUMNS", "startIndex": col, "endIndex": col + 1},
            "properties": {"pixelSize": width}, "fields": "pixelSize"
        }})

    # Update frozen rows for new header structure
    fmt.append({"updateSheetProperties": {
        "properties": {"sheetId": 1, "gridProperties": {"frozenRowCount": 3, "frozenColumnCount": 2}},
        "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"
    }})

    # ── MONTHLY REVIEW FORMATTING ──

    # Header row
    fmt.append({"repeatCell": {
        "range": {"sheetId": 100, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 14},
        "cell": {"userEnteredFormat": {
            "backgroundColor": INK, "textFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 10},
            "horizontalAlignment": "CENTER"
        }},
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
    }})

    # Totals row
    fmt.append({"repeatCell": {
        "range": {"sheetId": 100, "startRowIndex": 11, "endRowIndex": 12, "startColumnIndex": 0, "endColumnIndex": 14},
        "cell": {"userEnteredFormat": {
            "backgroundColor": INK, "textFormat": {"bold": True, "foregroundColor": GOLD, "fontSize": 10}
        }},
        "fields": "userEnteredFormat(backgroundColor,textFormat)"
    }})

    # MoM Change header
    fmt.append({"repeatCell": {
        "range": {"sheetId": 100, "startRowIndex": 13, "endRowIndex": 14, "startColumnIndex": 0, "endColumnIndex": 14},
        "cell": {"userEnteredFormat": {
            "backgroundColor": INK, "textFormat": {"bold": True, "foregroundColor": GOLD, "fontSize": 11}
        }},
        "fields": "userEnteredFormat(backgroundColor,textFormat)"
    }})
    fmt.append({"mergeCells": {"range": {"sheetId": 100, "startRowIndex": 13, "endRowIndex": 14, "startColumnIndex": 0, "endColumnIndex": 14}, "mergeType": "MERGE_ALL"}})

    # Alternating rows for data
    fmt.append({"addBanding": {
        "bandedRange": {
            "bandedRangeId": 50,
            "range": {"sheetId": 100, "startRowIndex": 0, "endRowIndex": 12, "startColumnIndex": 0, "endColumnIndex": 14},
            "rowProperties": {"headerColor": INK, "firstBandColor": WHITE, "secondBandColor": PAPER}
        }
    }})

    # Revenue column currency (J)
    fmt.append({"repeatCell": {
        "range": {"sheetId": 100, "startRowIndex": 1, "endRowIndex": 12, "startColumnIndex": 9, "endColumnIndex": 10},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
        "fields": "userEnteredFormat.numberFormat"
    }})

    # Conditional formatting for MoM changes - positive green, negative red
    fmt.append({"addConditionalFormatRule": {
        "rule": {
            "ranges": [{"sheetId": 100, "startRowIndex": 14, "endRowIndex": 25, "startColumnIndex": 1, "endColumnIndex": 10}],
            "booleanRule": {
                "condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "0"}]},
                "format": {"textFormat": {"foregroundColor": {"red": 0.13, "green": 0.55, "blue": 0.13}}}
            }
        }, "index": 0
    }})
    fmt.append({"addConditionalFormatRule": {
        "rule": {
            "ranges": [{"sheetId": 100, "startRowIndex": 14, "endRowIndex": 25, "startColumnIndex": 1, "endColumnIndex": 10}],
            "booleanRule": {
                "condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "0"}]},
                "format": {"textFormat": {"foregroundColor": {"red": 0.8, "green": 0.13, "blue": 0.13}}}
            }
        }, "index": 0
    }})

    # Monthly Review column widths
    for col, width in {0: 100, 1: 90, 2: 70, 3: 70, 4: 70, 5: 90, 6: 80, 7: 80, 8: 80, 9: 100, 10: 120, 11: 200, 12: 200, 13: 200}.items():
        fmt.append({"updateDimensionProperties": {
            "range": {"sheetId": 100, "dimension": "COLUMNS", "startIndex": col, "endIndex": col + 1},
            "properties": {"pixelSize": width}, "fields": "pixelSize"
        }})

    # ── REFERRAL TRACKER FORMATTING ──

    # Header row
    fmt.append({"repeatCell": {
        "range": {"sheetId": 101, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 13},
        "cell": {"userEnteredFormat": {
            "backgroundColor": INK, "textFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 10},
            "horizontalAlignment": "CENTER"
        }},
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
    }})

    # Alternating rows
    fmt.append({"addBanding": {
        "bandedRange": {
            "bandedRangeId": 60,
            "range": {"sheetId": 101, "startRowIndex": 0, "endRowIndex": 101, "startColumnIndex": 0, "endColumnIndex": 13},
            "rowProperties": {"headerColor": INK, "firstBandColor": WHITE, "secondBandColor": PAPER}
        }
    }})

    # Data validations for Referral Tracker
    # Relationship dropdown
    fmt.append({"setDataValidation": {
        "range": {"sheetId": 101, "startRowIndex": 1, "endRowIndex": 101, "startColumnIndex": 3, "endColumnIndex": 4},
        "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in ["Past Client", "Current Client", "Industry Contact", "Personal", "Other"]]}, "showCustomUi": True, "strict": False}
    }})

    # ICP dropdown
    fmt.append({"setDataValidation": {
        "range": {"sheetId": 101, "startRowIndex": 1, "endRowIndex": 101, "startColumnIndex": 6, "endColumnIndex": 7},
        "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in ["Architect", "Builder", "Interior Designer", "Developer", "Trades"]]}, "showCustomUi": True, "strict": False}
    }})

    # Stage dropdown
    fmt.append({"setDataValidation": {
        "range": {"sheetId": 101, "startRowIndex": 1, "endRowIndex": 101, "startColumnIndex": 8, "endColumnIndex": 9},
        "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in ["New Lead", "Discovery Booked", "Proposal Sent", "Won", "Lost", "Not Qualified"]]}, "showCustomUi": True, "strict": False}
    }})

    # Thank You Sent checkbox-style dropdown
    fmt.append({"setDataValidation": {
        "range": {"sheetId": 101, "startRowIndex": 1, "endRowIndex": 101, "startColumnIndex": 10, "endColumnIndex": 11},
        "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in ["Yes", "No", "Pending"]]}, "showCustomUi": True, "strict": False}
    }})

    # Thank You Type dropdown
    fmt.append({"setDataValidation": {
        "range": {"sheetId": 101, "startRowIndex": 1, "endRowIndex": 101, "startColumnIndex": 11, "endColumnIndex": 12},
        "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in ["Gift Card", "Bottle of Wine", "Handwritten Note", "Print/Photo", "Dinner", "Other"]]}, "showCustomUi": True, "strict": False}
    }})

    # Currency format for H, J (Estimated Value, Revenue Won)
    for col in [7, 9]:
        fmt.append({"repeatCell": {
            "range": {"sheetId": 101, "startRowIndex": 1, "endRowIndex": 101, "startColumnIndex": col, "endColumnIndex": col + 1},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
            "fields": "userEnteredFormat.numberFormat"
        }})

    # Stage conditional formatting
    for stage, color in [("Won", GREEN), ("Lost", RED_LIGHT), ("Proposal Sent", YELLOW)]:
        fmt.append({"addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": 101, "startRowIndex": 1, "endRowIndex": 101, "startColumnIndex": 8, "endColumnIndex": 9}],
                "booleanRule": {
                    "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": stage}]},
                    "format": {"backgroundColor": color}
                }
            }, "index": 0
        }})

    # Referral Tracker column widths
    for col, width in {0: 100, 1: 150, 2: 150, 3: 120, 4: 150, 5: 150, 6: 120, 7: 110, 8: 120, 9: 110, 10: 100, 11: 120, 12: 250}.items():
        fmt.append({"updateDimensionProperties": {
            "range": {"sheetId": 101, "dimension": "COLUMNS", "startIndex": col, "endIndex": col + 1},
            "properties": {"pixelSize": width}, "fields": "pixelSize"
        }})

    # ── ROADMAP - Overdue conditional formatting ──
    # Highlight rows where deadline has passed but status is not Complete
    fmt.append({"addConditionalFormatRule": {
        "rule": {
            "ranges": [{"sheetId": 5, "startRowIndex": 1, "endRowIndex": 40, "startColumnIndex": 0, "endColumnIndex": 9}],
            "booleanRule": {
                "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": '=AND($G2<>"",DATEVALUE($G2)<TODAY(),$F2<>"Complete")'}]},
                "format": {"backgroundColor": RED_LIGHT, "textFormat": {"bold": True}}
            }
        }, "index": 0
    }})

    # Award deadlines section header
    award_header_row = next_row  # 0-indexed for the API
    fmt.append({"repeatCell": {
        "range": {"sheetId": 5, "startRowIndex": award_header_row, "endRowIndex": award_header_row + 1, "startColumnIndex": 0, "endColumnIndex": 9},
        "cell": {"userEnteredFormat": {"backgroundColor": INK, "textFormat": {"bold": True, "foregroundColor": GOLD, "fontSize": 12}}},
        "fields": "userEnteredFormat(backgroundColor,textFormat)"
    }})
    fmt.append({"mergeCells": {"range": {"sheetId": 5, "startRowIndex": award_header_row, "endRowIndex": award_header_row + 1, "startColumnIndex": 0, "endColumnIndex": 9}, "mergeType": "MERGE_ALL"}})

    # Award sub-header row
    fmt.append({"repeatCell": {
        "range": {"sheetId": 5, "startRowIndex": award_header_row + 1, "endRowIndex": award_header_row + 2, "startColumnIndex": 0, "endColumnIndex": 9},
        "cell": {"userEnteredFormat": {"backgroundColor": LIGHT_GOLD, "textFormat": {"bold": True, "foregroundColor": INK}}},
        "fields": "userEnteredFormat(backgroundColor,textFormat)"
    }})

    # ════════════════════════════════════════════════════════════
    # EXECUTE ALL FORMATTING
    # ════════════════════════════════════════════════════════════
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": fmt}
    ).execute()
    print("Applied all formatting")

    print(f"\nUpgrade complete!")
    print(f"URL: https://docs.google.com/spreadsheets/d/{sheet_id}")
    print(f"\nNew features:")
    print(f"  Dashboard: Revenue progress ($125K tracker), conversion funnel, today's focus, week-over-week comparison")
    print(f"  Daily Tracker: Day column, weekly summary rows (gold), daily targets row, hit-target highlighting")
    print(f"  Monthly Review: Auto-calculated metrics per month, MoM change tracking, manual reflection columns")
    print(f"  Referral Tracker: Full referral network tracking with thank-you management")
    print(f"  Roadmap: Award submission deadlines, overdue row highlighting (red)")


if __name__ == "__main__":
    main()
