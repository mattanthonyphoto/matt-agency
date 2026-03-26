"""
Create Marketing Plan & KPI Tracker for Matt Anthony Photography.
Uses Google Sheets API to build a fully formatted, formula-driven spreadsheet.

6 tabs: Dashboard, Daily Tracker, Channel Plans, Lead Attribution, Budget & ROI, Q2-Q4 Roadmap

Usage:
    python tools/create_marketing_plan.py
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_sheets_service, get_drive_service

# Brand colors (matching existing tools)
INK = {"red": 0.102, "green": 0.102, "blue": 0.094}
GOLD = {"red": 0.788, "green": 0.663, "blue": 0.431}
PAPER = {"red": 0.965, "green": 0.957, "blue": 0.941}
WHITE = {"red": 1, "green": 1, "blue": 1}
LIGHT_GOLD = {"red": 0.95, "green": 0.93, "blue": 0.88}
GREEN = {"red": 0.72, "green": 0.88, "blue": 0.73}
YELLOW = {"red": 1.0, "green": 0.95, "blue": 0.7}
RED_LIGHT = {"red": 1.0, "green": 0.82, "blue": 0.82}


def col_index(col_letter):
    result = 0
    for c in col_letter:
        result = result * 26 + (ord(c) - ord('A'))
    return result


def main():
    sheets = get_sheets_service()

    # ════════════════════════════════════════════════════════════
    # CREATE SPREADSHEET WITH 6 TABS
    # ════════════════════════════════════════════════════════════
    spreadsheet = sheets.spreadsheets().create(body={
        "properties": {"title": "Marketing Plan & KPI Tracker 2026"},
        "sheets": [
            {"properties": {"title": "Dashboard", "sheetId": 0}},
            {"properties": {"title": "Daily Tracker", "sheetId": 1, "gridProperties": {"frozenRowCount": 2, "frozenColumnCount": 1}}},
            {"properties": {"title": "Channel Plans", "sheetId": 2, "gridProperties": {"frozenRowCount": 1}}},
            {"properties": {"title": "Lead Attribution", "sheetId": 3, "gridProperties": {"frozenRowCount": 1, "frozenColumnCount": 1}}},
            {"properties": {"title": "Budget & ROI", "sheetId": 4, "gridProperties": {"frozenRowCount": 1}}},
            {"properties": {"title": "Q2-Q4 Roadmap", "sheetId": 5, "gridProperties": {"frozenRowCount": 1}}},
        ]
    }).execute()

    spreadsheet_id = spreadsheet["spreadsheetId"]
    url = spreadsheet["spreadsheetUrl"]
    print(f"Created spreadsheet: {url}")

    # ════════════════════════════════════════════════════════════
    # TAB 1: DASHBOARD
    # ════════════════════════════════════════════════════════════
    dashboard_data = [
        ["MARKETING PLAN & KPI TRACKER", "", "", "", "", ""],
        ["Matt Anthony Photography | 2026", "", "", "", "", ""],
        [""],
        # --- THIS WEEK snapshot ---
        ["THIS WEEK AT A GLANCE", "", "", "", "", ""],
        ["Metric", "Target", "Actual", "% Hit", "Status", "Notes"],
        ["Cold Emails Sent", "50", '=SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A3:A367)=WEEKNUM(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!C4:C600)', '=IFERROR(C6/B6,"")', '=IF(D6="","",IF(D6>=1,"On Track",IF(D6>=0.7,"Behind","At Risk")))', ""],
        ["Instagram Posts", "3", '=SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A3:A367)=WEEKNUM(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!E4:E600)', '=IFERROR(C7/B7,"")', '=IF(D7="","",IF(D7>=1,"On Track",IF(D7>=0.7,"Behind","At Risk")))', ""],
        ["LinkedIn Posts", "2", '=SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A3:A367)=WEEKNUM(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!F4:F600)', '=IFERROR(C8/B8,"")', '=IF(D8="","",IF(D8>=1,"On Track",IF(D8>=0.7,"Behind","At Risk")))', ""],
        ["GBP Posts/Updates", "1", '=SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A3:A367)=WEEKNUM(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!G4:G600)', '=IFERROR(C9/B9,"")', '=IF(D9="","",IF(D9>=1,"On Track",IF(D9>=0.7,"Behind","At Risk")))', ""],
        ["Engagement Actions", "15", '=SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A3:A367)=WEEKNUM(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!H4:H600)', '=IFERROR(C10/B10,"")', '=IF(D10="","",IF(D10>=1,"On Track",IF(D10>=0.7,"Behind","At Risk")))', ""],
        ["Referral Asks", "2", '=SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A3:A367)=WEEKNUM(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!I4:I600)', '=IFERROR(C11/B11,"")', '=IF(D11="","",IF(D11>=1,"On Track",IF(D11>=0.7,"Behind","At Risk")))', ""],
        ["New Leads (all sources)", "", '=SUMPRODUCT((WEEKNUM(\'Daily Tracker\'!A3:A367)=WEEKNUM(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!J4:J600)', "", "", ""],
        [""],
        # --- MONTHLY ROLLUP ---
        ["THIS MONTH", "", "", "", "", ""],
        ["Metric", "Target", "Actual", "% Hit", "Status", ""],
        ["Cold Emails Sent", "200", '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A3:A367)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!C4:C600)', '=IFERROR(C17/B17,"")', '=IF(D17="","",IF(D17>=1,"On Track",IF(D17>=0.7,"Behind","At Risk")))', ""],
        ["Responses/Replies", "", '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A3:A367)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!C3:C367)', "", "", ""],
        ["Instagram Posts", "12", '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A3:A367)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!E4:E600)', '=IFERROR(C19/B19,"")', '=IF(D19="","",IF(D19>=1,"On Track",IF(D19>=0.7,"Behind","At Risk")))', ""],
        ["LinkedIn Posts", "8", '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A3:A367)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!F4:F600)', '=IFERROR(C20/B20,"")', '=IF(D20="","",IF(D20>=1,"On Track",IF(D20>=0.7,"Behind","At Risk")))', ""],
        ["Google Reviews Collected", "2", '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A3:A367)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!K4:K600)', '=IFERROR(C21/B21,"")', '=IF(D21="","",IF(D21>=1,"On Track",IF(D21>=0.7,"Behind","At Risk")))', ""],
        ["New Leads", "", '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A3:A367)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!J4:J600)', "", "", ""],
        ["Quotes Sent", "", '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A3:A367)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!L4:L600)', "", "", ""],
        ["Deals Won", "", '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A3:A367)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!M4:M600)', "", "", ""],
        ["Revenue Booked", "", '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A3:A367)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!N4:N600)', "", "", ""],
        [""],
        # --- STREAK TRACKER ---
        ["CONSISTENCY STREAKS", "", "", "", "", ""],
        ["Activity", "Current Streak", "Best Streak", "Last Done", "", ""],
        ["Daily Engagement", '=IF(\'Daily Tracker\'!G2="","0 days",\'Daily Tracker\'!G2)', "", "", "", ""],
        ["Cold Email (weekdays)", '=IF(\'Daily Tracker\'!B2="","0 days",\'Daily Tracker\'!B2)', "", "", "", ""],
        ["Social Posting", '=IF(\'Daily Tracker\'!D2="","0 days",\'Daily Tracker\'!D2)', "", "", "", ""],
        [""],
        # --- CHANNEL HEALTH ---
        ["CHANNEL HEALTH (Q-T-D)", "", "", "", "", ""],
        ["Channel", "Leads", "Revenue", "Cost", "ROI", "Trend"],
        ["Cold Email", '=COUNTIF(\'Lead Attribution\'!D2:D500,"Cold Email")', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Cold Email")*(\'Lead Attribution\'!H2:H500))', '=SUMIF(\'Budget & ROI\'!A2:A100,"Cold Email",\'Budget & ROI\'!D2:D100)', '=IFERROR((C35-D35)/D35,"")', ""],
        ["Instagram", '=COUNTIF(\'Lead Attribution\'!D2:D500,"Instagram")', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Instagram")*(\'Lead Attribution\'!H2:H500))', '=SUMIF(\'Budget & ROI\'!A2:A100,"Instagram",\'Budget & ROI\'!D2:D100)', '=IFERROR((C36-D36)/D36,"")', ""],
        ["LinkedIn", '=COUNTIF(\'Lead Attribution\'!D2:D500,"LinkedIn")', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="LinkedIn")*(\'Lead Attribution\'!H2:H500))', '=SUMIF(\'Budget & ROI\'!A2:A100,"LinkedIn",\'Budget & ROI\'!D2:D100)', '=IFERROR((C37-D37)/D37,"")', ""],
        ["Google/SEO", '=COUNTIF(\'Lead Attribution\'!D2:D500,"Google/SEO")', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Google/SEO")*(\'Lead Attribution\'!H2:H500))', '=SUMIF(\'Budget & ROI\'!A2:A100,"Google/SEO",\'Budget & ROI\'!D2:D100)', '=IFERROR((C38-D38)/D38,"")', ""],
        ["GBP", '=COUNTIF(\'Lead Attribution\'!D2:D500,"GBP")', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="GBP")*(\'Lead Attribution\'!H2:H500))', '=SUMIF(\'Budget & ROI\'!A2:A100,"GBP",\'Budget & ROI\'!D2:D100)', '=IFERROR((C39-D39)/D39,"")', ""],
        ["Referral", '=COUNTIF(\'Lead Attribution\'!D2:D500,"Referral")', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Referral")*(\'Lead Attribution\'!H2:H500))', '=SUMIF(\'Budget & ROI\'!A2:A100,"Referral",\'Budget & ROI\'!D2:D100)', '=IFERROR((C40-D40)/D40,"")', ""],
        ["Awards", '=COUNTIF(\'Lead Attribution\'!D2:D500,"Awards")', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Awards")*(\'Lead Attribution\'!H2:H500))', '=SUMIF(\'Budget & ROI\'!A2:A100,"Awards",\'Budget & ROI\'!D2:D100)', '=IFERROR((C41-D41)/D41,"")', ""],
        ["Pricing Guide", '=COUNTIF(\'Lead Attribution\'!D2:D500,"Pricing Guide")', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Pricing Guide")*(\'Lead Attribution\'!H2:H500))', '=SUMIF(\'Budget & ROI\'!A2:A100,"Pricing Guide",\'Budget & ROI\'!D2:D100)', '=IFERROR((C42-D42)/D42,"")', ""],
        ["TOTAL", '=SUM(B35:B42)', '=SUM(C35:C42)', '=SUM(D35:D42)', '=IFERROR((C43-D43)/D43,"")', ""],
    ]

    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="Dashboard!A1:F43",
        valueInputOption="USER_ENTERED",
        body={"values": dashboard_data}
    ).execute()

    # ════════════════════════════════════════════════════════════
    # TAB 2: DAILY TRACKER
    # ════════════════════════════════════════════════════════════
    # Row 1: Category headers
    # Row 2: Streak/summary row (auto-calculated)
    # Row 3+: Daily entries

    tracker_header_row1 = [
        "Date",                    # A
        "Cold Email",              # B - Emails Sent
        "Replies",                 # C - Email Replies
        "IG Posts",                # D
        "LI Posts",                # E
        "GBP Updates",             # F
        "Engagement Actions",      # G - Comments, DMs, likes on target accounts
        "Referral Asks",           # H
        "New Leads",               # I
        "Google Reviews",          # J
        "Quotes Sent",             # K
        "Deals Won",               # L
        "Revenue Booked",          # M
        "Website Sessions",        # N
        "Notes",                   # O
    ]

    # Row 2: Summary/streak row
    tracker_summary = [
        "STREAKS / TOTALS",
        # Streak formulas - count consecutive days with activity going backward from today
        '=ARRAYFORMULA(IF(COUNTA(B3:B367)=0,"0 days",COUNTA(B3:B367)&" logged"))',
        '=SUM(C3:C367)',
        '=ARRAYFORMULA(IF(COUNTA(D3:D367)=0,"0 days",COUNTA(D3:D367)&" logged"))',
        '=SUM(E3:E367)',
        '=SUM(F3:F367)',
        '=ARRAYFORMULA(IF(COUNTA(G3:G367)=0,"0 days",COUNTA(G3:G367)&" logged"))',
        '=SUM(H3:H367)',
        '=SUM(I3:I367)',
        '=SUM(J3:J367)',
        '=SUM(K3:K367)',
        '=SUM(L3:L367)',
        '=SUM(M3:M367)',
        '=SUM(N3:N367)',
        "",
    ]

    # Pre-populate dates for rest of 2026 (March 23 - Dec 31)
    tracker_dates = []
    start_date = datetime(2026, 3, 23)
    end_date = datetime(2026, 12, 31)
    current = start_date
    while current <= end_date:
        day_name = current.strftime("%a")
        tracker_dates.append([current.strftime("%Y-%m-%d")] + [""] * 14)
        current += timedelta(days=1)

    tracker_data = [tracker_header_row1, tracker_summary] + tracker_dates

    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="'Daily Tracker'!A1:O367",
        valueInputOption="USER_ENTERED",
        body={"values": tracker_data}
    ).execute()

    # ════════════════════════════════════════════════════════════
    # TAB 3: CHANNEL PLANS
    # ════════════════════════════════════════════════════════════
    channel_data = [
        ["CHANNEL PLANS & TARGETS", "", "", "", "", "", "", ""],
        [""],
        ["COLD EMAIL", "", "", "", "", "", "", ""],
        ["Metric", "Daily", "Weekly", "Monthly", "Quarterly", "Current", "Gap", "Notes"],
        ["Emails Sent", "10", "50", "200", "600", '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A3:A367)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!C4:C600)', '=F5-D5', "Mon-Fri cadence"],
        ["Response Rate", "", "", "5%", "5%", "", "", "Target: 5% minimum"],
        ["Positive Replies", "", "2-3", "10", "30", "", "", "Interested or booking call"],
        ["Meetings Booked", "", "1", "3-4", "10", "", "", "Discovery calls from cold"],
        ["Deals Closed", "", "", "1", "3", "", "", "$3,500-5,500 avg"],
        [""],
        ["INSTAGRAM", "", "", "", "", "", "", ""],
        ["Metric", "Daily", "Weekly", "Monthly", "Quarterly", "Current", "Gap", "Notes"],
        ["Posts Published", "", "3", "12", "36", '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A3:A367)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!E4:E600)', '=F13-D13', "Mix: carousel, reel, single"],
        ["Stories", "1-2", "7-10", "30", "90", "", "", "BTS, site visits, process"],
        ["Engagement Actions", "3-5", "15", "60", "180", '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A3:A367)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!H4:H600)', '=F15-D15', "Comment on target accounts"],
        ["Follower Growth", "", "", "50", "150", "", "", "Organic growth target"],
        ["DM Conversations", "", "2-3", "10", "30", "", "", "Warm outreach to prospects"],
        [""],
        ["LINKEDIN", "", "", "", "", "", "", ""],
        ["Metric", "Daily", "Weekly", "Monthly", "Quarterly", "Current", "Gap", "Notes"],
        ["Posts Published", "", "2", "8", "24", '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A3:A367)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!F4:F600)', '=F21-D21', "Industry insight + project stories"],
        ["Connections Added", "", "5", "20", "60", "", "", "Architects, builders, designers"],
        ["Impressions", "", "", "2000", "6000", "", "", "Track in analytics"],
        ["Engagement Rate", "", "", "3%", "3%", "", "", "Likes + comments / impressions"],
        [""],
        ["GOOGLE BUSINESS PROFILE", "", "", "", "", "", "", ""],
        ["Metric", "Daily", "Weekly", "Monthly", "Quarterly", "Current", "Gap", "Notes"],
        ["Posts/Updates", "", "1", "4", "12", '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A3:A367)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!G4:G600)', '=F27-D27', "Project photos + updates"],
        ["Reviews Collected", "", "", "2", "10", '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A3:A367)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!K4:K600)', '=F28-D28', "Ask after every delivery"],
        ["Total Reviews (cumulative)", "", "", "", "10 by Q4", "", "", "Q2 rock: 10 Google reviews"],
        [""],
        ["SEO / WEBSITE", "", "", "", "", "", "", ""],
        ["Metric", "Daily", "Weekly", "Monthly", "Quarterly", "Current", "Gap", "Notes"],
        ["Blog/Case Studies Published", "", "", "1-2", "4-6", "", "", "Project stories, process posts"],
        ["Location Pages", "", "", "", "6 indexed", "", "", "Q2 rock: 6 location pages"],
        ["Organic Sessions", "", "", "500", "1500", "", "", "Track in GA4"],
        ["Contact Form Submissions", "", "", "3-5", "12-15", "", "", "From organic traffic"],
        [""],
        ["REFERRALS & NETWORKING", "", "", "", "", "", "", ""],
        ["Metric", "Daily", "Weekly", "Monthly", "Quarterly", "Current", "Gap", "Notes"],
        ["Referral Asks", "", "2", "8", "24", '=SUMPRODUCT((MONTH(\'Daily Tracker\'!A3:A367)=MONTH(TODAY()))*(YEAR(\'Daily Tracker\'!A3:A367)=2026)*\'Daily Tracker\'!I4:I600)', '=F39-D39', "After project delivery + past clients"],
        ["Coffee Meetings", "", "", "2", "6", "", "", "In-person networking"],
        ["Event Attendance", "", "", "1", "3", "", "", "Industry events, openings"],
        ["Referral Leads", "", "", "2", "6", "", "", "Leads from referral asks"],
        [""],
        ["AWARDS & PUBLICATIONS", "", "", "", "", "", "", ""],
        ["Metric", "Daily", "Weekly", "Monthly", "Quarterly", "Current", "Gap", "Notes"],
        ["Submissions Made", "", "", "1-2", "4-6", "", "", "Track deadlines in Roadmap"],
        ["Awards Won", "", "", "", "1-2", "", "", "AIBC, Georgie, RAIC, etc."],
        ["Publications/Features", "", "", "", "1-2", "", "", "Pitch to design publications"],
    ]

    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="'Channel Plans'!A1:H100",
        valueInputOption="USER_ENTERED",
        body={"values": channel_data}
    ).execute()

    # ════════════════════════════════════════════════════════════
    # TAB 4: LEAD ATTRIBUTION
    # ════════════════════════════════════════════════════════════
    attribution_headers = [
        "Date",           # A
        "Lead Name",      # B
        "Company",        # C
        "Source",         # D
        "ICP",            # E
        "Stage",          # F
        "Estimated Value",# G
        "Closed Revenue", # H
        "Cost-Share",     # I
        "Days to Close",  # J
        "Notes",          # K
    ]

    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="'Lead Attribution'!A1:K1",
        valueInputOption="RAW",
        body={"values": [attribution_headers]}
    ).execute()

    # Formulas for J column (days to close)
    attr_formulas = []
    for r in range(2, 201):
        attr_formulas.append([
            f'=IF(OR(F{r}="Won",F{r}="Lost"),IF(A{r}="","",TODAY()-A{r}),"")',
        ])

    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="'Lead Attribution'!J2:J201",
        valueInputOption="USER_ENTERED",
        body={"values": attr_formulas}
    ).execute()

    # ════════════════════════════════════════════════════════════
    # TAB 5: BUDGET & ROI
    # ════════════════════════════════════════════════════════════
    budget_data = [
        ["Channel", "Item", "Frequency", "Monthly Cost", "Quarterly Cost", "Annual Cost", "Revenue Attributed", "ROI", "Notes"],
        ["Cold Email", "Instantly subscription", "Monthly", "97", '=D2*3', '=D2*12', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Cold Email")*(\'Lead Attribution\'!H2:H500))', '=IFERROR((G2-E2)/E2,"")', ""],
        ["Cold Email", "Apollo/lead data", "Monthly", "50", '=D3*3', '=D3*12', "", "", ""],
        ["Cold Email", "Sending domains", "Annual", '=15', '=D4*3', '=D4*12', "", "", "Mailreach warmup included"],
        ["Instagram", "Time investment (hrs)", "Weekly", "", "", "", '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Instagram")*(\'Lead Attribution\'!H2:H500))', "", "Organic only for now"],
        ["LinkedIn", "Premium subscription", "Monthly", "0", '=D6*3', '=D6*12', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="LinkedIn")*(\'Lead Attribution\'!H2:H500))', '=IFERROR((G6-E6)/E6,"")', "Free tier currently"],
        ["Google/SEO", "Squarespace plan", "Monthly", "33", '=D7*3', '=D7*12', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Google/SEO")*(\'Lead Attribution\'!H2:H500))', '=IFERROR((G7-E7)/E7,"")', ""],
        ["Google/SEO", "SEO tools", "Monthly", "0", '=D8*3', '=D8*12', "", "", ""],
        ["GBP", "Setup & maintenance", "Monthly", "0", '=D9*3', '=D9*12', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="GBP")*(\'Lead Attribution\'!H2:H500))', '=IFERROR((G9-E9)/E9,"")', "Free channel"],
        ["Referral", "Client gifts/thank you", "Per referral", "25", '=D10*3', '=D10*12', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Referral")*(\'Lead Attribution\'!H2:H500))', '=IFERROR((G10-E10)/E10,"")', "$25 avg per thank you"],
        ["Awards", "Submission fees", "Per submission", "75", '=D11*3', '=D11*12', '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Awards")*(\'Lead Attribution\'!H2:H500))', '=IFERROR((G11-E11)/E11,"")', "Avg $75 per submission"],
        ["Pricing Guide", "Design/hosting", "One-time", "0", "0", "0", '=SUMPRODUCT((\'Lead Attribution\'!D2:D500="Pricing Guide")*(\'Lead Attribution\'!H2:H500))', "", "Already built"],
        ["", "", "", "", "", "", "", "", ""],
        ["TOTALS", "", "", '=SUM(D2:D12)', '=SUM(E2:E12)', '=SUM(F2:F12)', '=SUM(G2:G12)', '=IFERROR((G14-E14)/E14,"")', ""],
    ]

    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="'Budget & ROI'!A1:I14",
        valueInputOption="USER_ENTERED",
        body={"values": budget_data}
    ).execute()

    # ════════════════════════════════════════════════════════════
    # TAB 6: Q2-Q4 ROADMAP
    # ════════════════════════════════════════════════════════════
    roadmap_data = [
        ["Quarter", "Rock / Initiative", "Channel", "Key Activities", "KPI Target", "Status", "Deadline", "Owner", "Notes"],
        # Q2 Rocks (from 2026 strategy)
        ["Q2", "Sign Balmoral retainer", "Referral", "Deliver proof case, pitch retainer", "1 retainer signed", "Not Started", "2026-06-30", "Matt", "Creative Partner service"],
        ["Q2", "Close 3 projects", "Multi-channel", "Cold email + referral + inbound pipeline", "3 projects closed", "Not Started", "2026-06-30", "Matt", "$3,500-5,500 each"],
        ["Q2", "Launch cold email campaign", "Cold Email", "Activate Instantly, monitor responses, iterate", "200 emails/month, 3 meetings booked", "In Progress", "2026-04-15", "Matt", "316 builders loaded"],
        ["Q2", "Pitch 2nd retainer", "Multi-channel", "Identify target, pitch Creative Partner", "1 retainer pitched", "Not Started", "2026-06-30", "Matt", ""],
        ["Q2", "Collect 10 Google reviews", "GBP", "Ask after every delivery, follow up past clients", "10 reviews total", "Not Started", "2026-06-30", "Matt", "Currently at 0"],
        ["Q2", "Index 6 location pages", "SEO", "Build and submit location pages to GSC", "6 pages indexed", "Not Started", "2026-06-30", "Matt", "Part of website rebuild"],
        ["Q2", "Restart Instagram", "Instagram", "3 posts/week, daily stories, engagement", "12 posts/month, 50 followers/month", "Not Started", "2026-04-07", "Matt", "Dormant 5+ months"],
        ["Q2", "Launch LinkedIn presence", "LinkedIn", "2 posts/week, connect with ICPs", "8 posts/month, 20 connections/month", "Not Started", "2026-04-14", "Matt", ""],
        ["Q2", "Submit 2 award entries", "Awards", "AIBC, Georgie Awards", "2 submissions", "Not Started", "2026-06-30", "Matt", "Check deadlines"],
        [""],
        # Q3
        ["Q3", "Scale cold email to warm pipeline", "Cold Email", "Iterate copy, add architect ICP", "4 meetings/month", "Not Started", "2026-09-30", "Matt", ""],
        ["Q3", "Close 5 projects", "Multi-channel", "Full pipeline working", "5 projects closed", "Not Started", "2026-09-30", "Matt", ""],
        ["Q3", "Sign 2nd retainer", "Multi-channel", "Convert pitched retainer", "2 active retainers", "Not Started", "2026-09-30", "Matt", ""],
        ["Q3", "Publish 3 case studies", "SEO", "Write up completed projects", "3 published, indexed in GSC", "Not Started", "2026-09-30", "Matt", ""],
        ["Q3", "Pinterest launch", "Pinterest", "Pin project galleries, link to website", "20 pins/month", "Not Started", "2026-07-15", "Matt", ""],
        ["Q3", "Reach 20 Google reviews", "GBP", "Continue asking, follow up", "20 total reviews", "Not Started", "2026-09-30", "Matt", ""],
        [""],
        # Q4
        ["Q4", "Close 5+ projects", "Multi-channel", "Year-end push, construction season", "5+ projects closed", "Not Started", "2026-12-31", "Matt", ""],
        ["Q4", "Pitch 3rd retainer", "Multi-channel", "Expand Creative Partner service", "3 active retainers", "Not Started", "2026-12-31", "Matt", ""],
        ["Q4", "Submit 3+ award entries", "Awards", "AIBC, Georgie, RAIC, publications", "3+ submissions", "Not Started", "2026-12-31", "Matt", ""],
        ["Q4", "Hit $125K revenue target", "Multi-channel", "All channels contributing", "$125,000 total 2026 revenue", "Not Started", "2026-12-31", "Matt", "Revised target"],
        ["Q4", "Year-end review & 2027 plan", "All", "Analyze ROI per channel, plan 2027", "Completed review doc", "Not Started", "2026-12-31", "Matt", ""],
    ]

    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="'Q2-Q4 Roadmap'!A1:I23",
        valueInputOption="USER_ENTERED",
        body={"values": roadmap_data}
    ).execute()

    # ════════════════════════════════════════════════════════════
    # FORMATTING
    # ════════════════════════════════════════════════════════════
    format_requests = []

    # ── DASHBOARD FORMATTING ──

    # Title row
    format_requests.append({
        "repeatCell": {
            "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 6},
            "cell": {"userEnteredFormat": {"backgroundColor": INK, "textFormat": {"bold": True, "foregroundColor": GOLD, "fontSize": 16}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    })
    format_requests.append({
        "mergeCells": {"range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 6}, "mergeType": "MERGE_ALL"}
    })

    # Subtitle row
    format_requests.append({
        "repeatCell": {
            "range": {"sheetId": 0, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": 6},
            "cell": {"userEnteredFormat": {"backgroundColor": INK, "textFormat": {"foregroundColor": PAPER, "fontSize": 11}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    })
    format_requests.append({
        "mergeCells": {"range": {"sheetId": 0, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": 6}, "mergeType": "MERGE_ALL"}
    })

    # Section headers on Dashboard
    dashboard_section_rows = [3, 4, 14, 15, 27, 28, 33, 34]
    for row in dashboard_section_rows:
        is_title = row in [3, 14, 27, 33]
        format_requests.append({
            "repeatCell": {
                "range": {"sheetId": 0, "startRowIndex": row, "endRowIndex": row + 1, "startColumnIndex": 0, "endColumnIndex": 6},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": INK if is_title else LIGHT_GOLD,
                    "textFormat": {"bold": True, "foregroundColor": GOLD if is_title else INK, "fontSize": 12 if is_title else 10},
                }},
                "fields": "userEnteredFormat(backgroundColor,textFormat)"
            }
        })

    # Conditional formatting for Status column (E6:E12, E17:E25) - On Track/Behind/At Risk
    for start_row, end_row in [(5, 12), (16, 25)]:
        for status, status_color in [("On Track", GREEN), ("Behind", YELLOW), ("At Risk", RED_LIGHT)]:
            format_requests.append({
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{"sheetId": 0, "startRowIndex": start_row, "endRowIndex": end_row, "startColumnIndex": 4, "endColumnIndex": 5}],
                        "booleanRule": {
                            "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": status}]},
                            "format": {"backgroundColor": status_color, "textFormat": {"bold": True}}
                        }
                    },
                    "index": 0
                }
            })

    # Dashboard column widths
    for col, width in {0: 200, 1: 100, 2: 100, 3: 80, 4: 100, 5: 200}.items():
        format_requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": 0, "dimension": "COLUMNS", "startIndex": col, "endIndex": col + 1},
                "properties": {"pixelSize": width}, "fields": "pixelSize"
            }
        })

    # Currency format for Dashboard revenue cells
    for row in [25, 26]:  # Revenue Booked rows
        format_requests.append({
            "repeatCell": {
                "range": {"sheetId": 0, "startRowIndex": row - 1, "endRowIndex": row, "startColumnIndex": 2, "endColumnIndex": 3},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        })

    # Channel health currency formatting (C35:D43)
    format_requests.append({
        "repeatCell": {
            "range": {"sheetId": 0, "startRowIndex": 34, "endRowIndex": 43, "startColumnIndex": 2, "endColumnIndex": 5},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
            "fields": "userEnteredFormat.numberFormat"
        }
    })

    # Channel health ROI percentage formatting (E35:E43)
    format_requests.append({
        "repeatCell": {
            "range": {"sheetId": 0, "startRowIndex": 34, "endRowIndex": 43, "startColumnIndex": 4, "endColumnIndex": 5},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0%"}}},
            "fields": "userEnteredFormat.numberFormat"
        }
    })

    # Percentage format for % Hit column on Dashboard (D6:D12, D17:D25)
    for start_row, end_row in [(5, 12), (16, 25)]:
        format_requests.append({
            "repeatCell": {
                "range": {"sheetId": 0, "startRowIndex": start_row, "endRowIndex": end_row, "startColumnIndex": 3, "endColumnIndex": 4},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0%"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        })

    # ── DAILY TRACKER FORMATTING ──

    # Header rows
    for row in range(2):
        bg = INK if row == 0 else LIGHT_GOLD
        fg = WHITE if row == 0 else INK
        format_requests.append({
            "repeatCell": {
                "range": {"sheetId": 1, "startRowIndex": row, "endRowIndex": row + 1, "startColumnIndex": 0, "endColumnIndex": 15},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": bg,
                    "textFormat": {"bold": True, "foregroundColor": fg, "fontSize": 10},
                    "horizontalAlignment": "CENTER"
                }},
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        })

    # Alternating rows on Daily Tracker
    format_requests.append({
        "addBanding": {
            "bandedRange": {
                "bandedRangeId": 10,
                "range": {"sheetId": 1, "startRowIndex": 2, "endRowIndex": 367, "startColumnIndex": 0, "endColumnIndex": 15},
                "rowProperties": {"firstBandColor": WHITE, "secondBandColor": PAPER}
            }
        }
    })

    # Weekend highlighting - conditional formatting for Sat/Sun
    format_requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": 1, "startRowIndex": 2, "endRowIndex": 367, "startColumnIndex": 0, "endColumnIndex": 15}],
                "booleanRule": {
                    "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=OR(WEEKDAY($A3)=1,WEEKDAY($A3)=7)"}]},
                    "format": {"backgroundColor": {"red": 0.93, "green": 0.93, "blue": 0.95}}
                }
            },
            "index": 0
        }
    })

    # Currency format for Revenue Booked column (M)
    format_requests.append({
        "repeatCell": {
            "range": {"sheetId": 1, "startRowIndex": 2, "endRowIndex": 367, "startColumnIndex": 12, "endColumnIndex": 13},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
            "fields": "userEnteredFormat.numberFormat"
        }
    })

    # Daily Tracker column widths
    tracker_widths = {0: 100, 1: 90, 2: 70, 3: 70, 4: 70, 5: 90, 6: 130, 7: 90, 8: 80, 9: 100, 10: 80, 11: 80, 12: 110, 13: 110, 14: 250}
    for col, width in tracker_widths.items():
        format_requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": 1, "dimension": "COLUMNS", "startIndex": col, "endIndex": col + 1},
                "properties": {"pixelSize": width}, "fields": "pixelSize"
            }
        })

    # ── CHANNEL PLANS FORMATTING ──

    # Title row
    format_requests.append({
        "repeatCell": {
            "range": {"sheetId": 2, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 8},
            "cell": {"userEnteredFormat": {"backgroundColor": INK, "textFormat": {"bold": True, "foregroundColor": GOLD, "fontSize": 14}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    })
    format_requests.append({
        "mergeCells": {"range": {"sheetId": 2, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 8}, "mergeType": "MERGE_ALL"}
    })

    # Channel section headers (the channel name rows)
    channel_title_rows = [2, 10, 18, 25, 31, 37, 43]
    for row in channel_title_rows:
        format_requests.append({
            "repeatCell": {
                "range": {"sheetId": 2, "startRowIndex": row, "endRowIndex": row + 1, "startColumnIndex": 0, "endColumnIndex": 8},
                "cell": {"userEnteredFormat": {"backgroundColor": INK, "textFormat": {"bold": True, "foregroundColor": GOLD, "fontSize": 11}}},
                "fields": "userEnteredFormat(backgroundColor,textFormat)"
            }
        })
        format_requests.append({
            "mergeCells": {"range": {"sheetId": 2, "startRowIndex": row, "endRowIndex": row + 1, "startColumnIndex": 0, "endColumnIndex": 8}, "mergeType": "MERGE_ALL"}
        })

    # Channel sub-headers (Metric, Daily, Weekly, etc.)
    channel_subheader_rows = [3, 11, 19, 26, 32, 38, 44]
    for row in channel_subheader_rows:
        format_requests.append({
            "repeatCell": {
                "range": {"sheetId": 2, "startRowIndex": row, "endRowIndex": row + 1, "startColumnIndex": 0, "endColumnIndex": 8},
                "cell": {"userEnteredFormat": {"backgroundColor": LIGHT_GOLD, "textFormat": {"bold": True, "foregroundColor": INK, "fontSize": 10}}},
                "fields": "userEnteredFormat(backgroundColor,textFormat)"
            }
        })

    # Channel Plans column widths
    for col, width in {0: 200, 1: 80, 2: 80, 3: 80, 4: 80, 5: 80, 6: 80, 7: 250}.items():
        format_requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": 2, "dimension": "COLUMNS", "startIndex": col, "endIndex": col + 1},
                "properties": {"pixelSize": width}, "fields": "pixelSize"
            }
        })

    # ── LEAD ATTRIBUTION FORMATTING ──

    # Header row
    format_requests.append({
        "repeatCell": {
            "range": {"sheetId": 3, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 11},
            "cell": {"userEnteredFormat": {
                "backgroundColor": INK,
                "textFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 10},
                "horizontalAlignment": "CENTER"
            }},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
        }
    })

    # Alternating rows
    format_requests.append({
        "addBanding": {
            "bandedRange": {
                "bandedRangeId": 20,
                "range": {"sheetId": 3, "startRowIndex": 0, "endRowIndex": 201, "startColumnIndex": 0, "endColumnIndex": 11},
                "rowProperties": {"headerColor": INK, "firstBandColor": WHITE, "secondBandColor": PAPER}
            }
        }
    })

    # Data validation for Lead Attribution
    attr_validations = [
        (3, ["Cold Email", "Instagram", "LinkedIn", "Google/SEO", "GBP", "Referral", "Awards", "Pricing Guide", "Networking", "Other"]),
        (4, ["Architect", "Builder", "Interior Designer", "Developer", "Trades"]),
        (5, ["New Lead", "Discovery Booked", "Discovery Done", "Proposal Sent", "Won", "Lost", "Dormant"]),
    ]
    for col_idx, values in attr_validations:
        format_requests.append({
            "setDataValidation": {
                "range": {"sheetId": 3, "startRowIndex": 1, "endRowIndex": 201, "startColumnIndex": col_idx, "endColumnIndex": col_idx + 1},
                "rule": {
                    "condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in values]},
                    "showCustomUi": True, "strict": False
                }
            }
        })

    # Currency format for G, H columns (Estimated Value, Closed Revenue)
    for col_idx in [6, 7]:
        format_requests.append({
            "repeatCell": {
                "range": {"sheetId": 3, "startRowIndex": 1, "endRowIndex": 201, "startColumnIndex": col_idx, "endColumnIndex": col_idx + 1},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        })

    # Cost-Share dropdown
    format_requests.append({
        "setDataValidation": {
            "range": {"sheetId": 3, "startRowIndex": 1, "endRowIndex": 201, "startColumnIndex": 8, "endColumnIndex": 9},
            "rule": {
                "condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in ["Yes", "No", "TBD"]]},
                "showCustomUi": True, "strict": False
            }
        }
    })

    # Conditional formatting for Lead Stage
    stage_colors = {
        "Won": GREEN,
        "Lost": RED_LIGHT,
        "Proposal Sent": YELLOW,
        "Dormant": {"red": 0.9, "green": 0.9, "blue": 0.9},
    }
    for stage, stage_color in stage_colors.items():
        format_requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": 3, "startRowIndex": 1, "endRowIndex": 201, "startColumnIndex": 5, "endColumnIndex": 6}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": stage}]},
                        "format": {"backgroundColor": stage_color}
                    }
                },
                "index": 0
            }
        })

    # Lead Attribution column widths
    for col, width in {0: 100, 1: 160, 2: 160, 3: 110, 4: 130, 5: 130, 6: 120, 7: 120, 8: 80, 9: 100, 10: 250}.items():
        format_requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": 3, "dimension": "COLUMNS", "startIndex": col, "endIndex": col + 1},
                "properties": {"pixelSize": width}, "fields": "pixelSize"
            }
        })

    # ── BUDGET & ROI FORMATTING ──

    # Header row
    format_requests.append({
        "repeatCell": {
            "range": {"sheetId": 4, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 9},
            "cell": {"userEnteredFormat": {
                "backgroundColor": INK,
                "textFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 10},
                "horizontalAlignment": "CENTER"
            }},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
        }
    })

    # Totals row
    format_requests.append({
        "repeatCell": {
            "range": {"sheetId": 4, "startRowIndex": 13, "endRowIndex": 14, "startColumnIndex": 0, "endColumnIndex": 9},
            "cell": {"userEnteredFormat": {
                "backgroundColor": INK,
                "textFormat": {"bold": True, "foregroundColor": GOLD, "fontSize": 10}
            }},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    })

    # Alternating rows
    format_requests.append({
        "addBanding": {
            "bandedRange": {
                "bandedRangeId": 30,
                "range": {"sheetId": 4, "startRowIndex": 0, "endRowIndex": 13, "startColumnIndex": 0, "endColumnIndex": 9},
                "rowProperties": {"headerColor": INK, "firstBandColor": WHITE, "secondBandColor": PAPER}
            }
        }
    })

    # Currency format for D-G columns (costs and revenue)
    for col_idx in range(3, 7):
        format_requests.append({
            "repeatCell": {
                "range": {"sheetId": 4, "startRowIndex": 1, "endRowIndex": 14, "startColumnIndex": col_idx, "endColumnIndex": col_idx + 1},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        })

    # ROI percentage format (H column)
    format_requests.append({
        "repeatCell": {
            "range": {"sheetId": 4, "startRowIndex": 1, "endRowIndex": 14, "startColumnIndex": 7, "endColumnIndex": 8},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0%"}}},
            "fields": "userEnteredFormat.numberFormat"
        }
    })

    # Budget column widths
    for col, width in {0: 120, 1: 180, 2: 100, 3: 100, 4: 120, 5: 110, 6: 140, 7: 80, 8: 200}.items():
        format_requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": 4, "dimension": "COLUMNS", "startIndex": col, "endIndex": col + 1},
                "properties": {"pixelSize": width}, "fields": "pixelSize"
            }
        })

    # ── Q2-Q4 ROADMAP FORMATTING ──

    # Header row
    format_requests.append({
        "repeatCell": {
            "range": {"sheetId": 5, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 9},
            "cell": {"userEnteredFormat": {
                "backgroundColor": INK,
                "textFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 10},
                "horizontalAlignment": "CENTER"
            }},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
        }
    })

    # Alternating rows
    format_requests.append({
        "addBanding": {
            "bandedRange": {
                "bandedRangeId": 40,
                "range": {"sheetId": 5, "startRowIndex": 0, "endRowIndex": 23, "startColumnIndex": 0, "endColumnIndex": 9},
                "rowProperties": {"headerColor": INK, "firstBandColor": WHITE, "secondBandColor": PAPER}
            }
        }
    })

    # Data validation for Status column on Roadmap
    format_requests.append({
        "setDataValidation": {
            "range": {"sheetId": 5, "startRowIndex": 1, "endRowIndex": 23, "startColumnIndex": 5, "endColumnIndex": 6},
            "rule": {
                "condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in ["Not Started", "In Progress", "On Hold", "Complete", "At Risk"]]},
                "showCustomUi": True, "strict": False
            }
        }
    })

    # Conditional formatting for Roadmap status
    roadmap_status_colors = {
        "Complete": GREEN,
        "In Progress": {"red": 0.85, "green": 0.92, "blue": 1.0},
        "At Risk": RED_LIGHT,
        "On Hold": YELLOW,
        "Not Started": {"red": 0.93, "green": 0.93, "blue": 0.93},
    }
    for status, status_color in roadmap_status_colors.items():
        format_requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": 5, "startRowIndex": 1, "endRowIndex": 23, "startColumnIndex": 5, "endColumnIndex": 6}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": status}]},
                        "format": {"backgroundColor": status_color, "textFormat": {"bold": True}}
                    }
                },
                "index": 0
            }
        })

    # Quarter column conditional formatting (Q2=blue, Q3=gold, Q4=green)
    quarter_colors = {
        "Q2": {"red": 0.85, "green": 0.92, "blue": 1.0},
        "Q3": LIGHT_GOLD,
        "Q4": {"red": 0.85, "green": 0.95, "blue": 0.85},
    }
    for quarter, q_color in quarter_colors.items():
        format_requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": 5, "startRowIndex": 1, "endRowIndex": 23, "startColumnIndex": 0, "endColumnIndex": 1}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": quarter}]},
                        "format": {"backgroundColor": q_color, "textFormat": {"bold": True}}
                    }
                },
                "index": 0
            }
        })

    # Roadmap column widths
    for col, width in {0: 70, 1: 220, 2: 110, 3: 280, 4: 200, 5: 100, 6: 100, 7: 70, 8: 250}.items():
        format_requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": 5, "dimension": "COLUMNS", "startIndex": col, "endIndex": col + 1},
                "properties": {"pixelSize": width}, "fields": "pixelSize"
            }
        })

    # ════════════════════════════════════════════════════════════
    # EXECUTE ALL FORMATTING
    # ════════════════════════════════════════════════════════════
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": format_requests}
    ).execute()

    print(f"\nMarketing Plan & KPI Tracker created successfully!")
    print(f"URL: {url}")
    print(f"\nTabs created:")
    print(f"  1. Dashboard — Weekly/monthly KPIs, consistency streaks, channel health")
    print(f"  2. Daily Tracker — Log daily activity, auto-rolls into weekly/monthly")
    print(f"  3. Channel Plans — Per-channel targets (daily/weekly/monthly/quarterly)")
    print(f"  4. Lead Attribution — Track every lead by source through to close")
    print(f"  5. Budget & ROI — Cost per channel vs revenue attributed")
    print(f"  6. Q2-Q4 Roadmap — Quarterly rocks mapped to marketing activities")
    print(f"\nAdd to .env:")
    print(f"  MARKETING_PLAN_SHEET_ID={spreadsheet_id}")


if __name__ == "__main__":
    main()
