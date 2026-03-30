"""Publication submission tracker — Google Sheets I/O for managing editorial submissions.

Subcommands:
  init            Create the tracking sheet with proper structure
  add-project     Add a new project to the tracker
  add-submission  Log a submission to a publication
  update-status   Update submission status (pending/accepted/declined/published)
  review          Show all projects and their submission status
  due             Show upcoming deadlines and unsubmitted projects
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.google_sheets_auth import get_sheets_service

load_dotenv(PROJECT_ROOT / ".env")

TRACKER_SHEET_ID = os.getenv("PUBLICATION_TRACKER_SHEET_ID", "")

# ── Sheet structure ──────────────────────────────────────────

PROJECTS_HEADERS = [
    "Project Name", "Client Firm", "Client Contact", "Location",
    "Project Type", "Completion Date", "Design Merit (1-5)",
    "Package Ready", "Floor Plans", "Description Ready",
    "Image Count", "Date Added", "Notes"
]

SUBMISSIONS_HEADERS = [
    "Project Name", "Publication", "Tier", "Exclusive",
    "Date Pitched", "Contact/Email", "Status",
    "Response Date", "Published Date", "Published URL", "Notes"
]

AWARDS_HEADERS = [
    "Award Name", "Project Name", "Deadline", "Fee",
    "Date Submitted", "Status", "Result", "Notes"
]

PUBLICATIONS_DB = {
    "ArchDaily": {"tier": 1, "exclusive": "No", "contact": "archdaily.com/submit", "type": "portal"},
    "Dezeen": {"tier": 1, "exclusive": "Yes", "contact": "submissions@dezeen.com", "type": "email"},
    "Dwell": {"tier": 2, "exclusive": "Soft", "contact": "editorial@dwell.com", "type": "email"},
    "Western Living": {"tier": 2, "exclusive": "No", "contact": "editor (check masthead)", "type": "email"},
    "Azure": {"tier": 2, "exclusive": "No", "contact": "editorial (check azuremagazine.com)", "type": "email"},
    "Canadian Architect": {"tier": 3, "exclusive": "No", "contact": "editor (check canadianarchitect.com)", "type": "email"},
    "Canadian Interiors": {"tier": 3, "exclusive": "No", "contact": "editor (check website)", "type": "email"},
    "AD": {"tier": 1, "exclusive": "Yes", "contact": "pitch via PR or direct", "type": "email"},
    "House & Home": {"tier": 3, "exclusive": "No", "contact": "editor (check houseandhome.com)", "type": "email"},
    "Designboom": {"tier": 2, "exclusive": "No", "contact": "submit@designboom.com", "type": "email"},
    "Leibal": {"tier": 2, "exclusive": "No", "contact": "submissions@leibal.com", "type": "email"},
}


# ── init ─────────────────────────────────────────────────────

def init_tracker(args):
    """Create the tracking sheet with Projects, Submissions, and Awards tabs."""
    sheets = get_sheets_service()

    body = {
        "properties": {"title": "Publication Tracker — Matt Anthony Photography"},
        "sheets": [
            {
                "properties": {"title": "Projects", "index": 0},
                "data": [{"rowData": [{"values": [
                    {"userEnteredValue": {"stringValue": h},
                     "userEnteredFormat": {"backgroundColor": {"red": 0.1, "green": 0.1, "blue": 0.1},
                                          "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True}}}
                    for h in PROJECTS_HEADERS
                ]}]}]
            },
            {
                "properties": {"title": "Submissions", "index": 1},
                "data": [{"rowData": [{"values": [
                    {"userEnteredValue": {"stringValue": h},
                     "userEnteredFormat": {"backgroundColor": {"red": 0.1, "green": 0.1, "blue": 0.1},
                                          "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True}}}
                    for h in SUBMISSIONS_HEADERS
                ]}]}]
            },
            {
                "properties": {"title": "Awards", "index": 2},
                "data": [{"rowData": [{"values": [
                    {"userEnteredValue": {"stringValue": h},
                     "userEnteredFormat": {"backgroundColor": {"red": 0.1, "green": 0.1, "blue": 0.1},
                                          "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True}}}
                    for h in AWARDS_HEADERS
                ]}]}]
            },
            {
                "properties": {"title": "Dashboard", "index": 3},
            },
        ],
    }

    result = sheets.spreadsheets().create(body=body).execute()
    sheet_id = result["spreadsheetId"]
    sheet_url = result["spreadsheetUrl"]

    # Get actual sheet IDs assigned by Google (they're NOT 0, 1, 2)
    tab_ids = {}
    for s in result.get("sheets", []):
        title = s["properties"]["title"]
        tab_ids[title] = s["properties"]["sheetId"]

    projects_id = tab_ids["Projects"]
    submissions_id = tab_ids["Submissions"]

    # Set column widths for readability
    requests = []
    for gid, widths in [
        (projects_id, [200, 180, 150, 120, 100, 110, 100, 90, 90, 100, 80, 100, 250]),
        (submissions_id, [200, 140, 50, 70, 100, 200, 90, 100, 100, 250, 250]),
        (tab_ids["Awards"], [200, 200, 100, 60, 100, 90, 90, 250]),
    ]:
        for col_i, w in enumerate(widths):
            requests.append({
                "updateDimensionProperties": {
                    "range": {"sheetId": gid, "dimension": "COLUMNS",
                              "startIndex": col_i, "endIndex": col_i + 1},
                    "properties": {"pixelSize": w},
                    "fields": "pixelSize"
                }
            })

    # Add data validation for Status column in Submissions
    requests.append({
        "setDataValidation": {
            "range": {"sheetId": submissions_id, "startRowIndex": 1, "startColumnIndex": 6, "endColumnIndex": 7},
            "rule": {
                "condition": {"type": "ONE_OF_LIST",
                              "values": [{"userEnteredValue": v} for v in
                                         ["Pending", "Accepted", "Declined", "Published", "No Response"]]},
                "showCustomUi": True, "strict": False
            }
        }
    })

    # Add data validation for Design Merit
    requests.append({
        "setDataValidation": {
            "range": {"sheetId": projects_id, "startRowIndex": 1, "startColumnIndex": 6, "endColumnIndex": 7},
            "rule": {
                "condition": {"type": "ONE_OF_LIST",
                              "values": [{"userEnteredValue": str(v)} for v in [1, 2, 3, 4, 5]]},
                "showCustomUi": True, "strict": False
            }
        }
    })

    # Add data validation for Package Ready / Floor Plans / Description Ready
    for col in [7, 8, 9]:
        requests.append({
            "setDataValidation": {
                "range": {"sheetId": projects_id, "startRowIndex": 1, "startColumnIndex": col, "endColumnIndex": col + 1},
                "rule": {
                    "condition": {"type": "ONE_OF_LIST",
                                  "values": [{"userEnteredValue": v} for v in ["Yes", "No", "Requested"]]},
                    "showCustomUi": True, "strict": False
                }
            }
        })

    if requests:
        sheets.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id, body={"requests": requests}
        ).execute()

    # Build dashboard formulas
    dashboard_data = [
        ["PUBLICATION TRACKER DASHBOARD"],
        [""],
        ["PROJECTS"],
        ["Total Projects", '=COUNTA(Projects!A2:A)'],
        ["Publication-Ready (Merit 3+)", '=COUNTIF(Projects!G2:G,">=3")'],
        ["Packages Complete", '=COUNTIF(Projects!H2:H,"Yes")'],
        [""],
        ["SUBMISSIONS"],
        ["Total Submitted", '=COUNTA(Submissions!A2:A)'],
        ["Pending", '=COUNTIF(Submissions!G2:G,"Pending")'],
        ["Accepted", '=COUNTIF(Submissions!G2:G,"Accepted")'],
        ["Published", '=COUNTIF(Submissions!G2:G,"Published")'],
        ["Declined", '=COUNTIF(Submissions!G2:G,"Declined")'],
        ["No Response", '=COUNTIF(Submissions!G2:G,"No Response")'],
        [""],
        ["AWARDS"],
        ["Entries Submitted", '=COUNTA(Awards!A2:A)'],
        [""],
        ["YEAR 1 TARGETS"],
        ["Projects submitted target: 6-8"],
        ["Publications achieved target: 3-4"],
        ["Awards entered target: 3-5"],
    ]

    sheets.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="Dashboard!A1",
        valueInputOption="USER_ENTERED",
        body={"values": dashboard_data}
    ).execute()

    print(json.dumps({
        "sheet_id": sheet_id,
        "url": sheet_url,
        "status": "created",
        "tabs": ["Projects", "Submissions", "Awards", "Dashboard"]
    }, indent=2))
    return 0


# ── add-project ──────────────────────────────────────────────

def add_project(args):
    """Add a project to the Projects tab."""
    if not TRACKER_SHEET_ID:
        print("ERROR: Set PUBLICATION_TRACKER_SHEET_ID in .env first (run 'init' to create)")
        return 1

    sheets = get_sheets_service()
    row = [
        args.name,
        args.firm,
        args.contact or "",
        args.location or "",
        args.project_type or "",
        args.completed or "",
        str(args.merit) if args.merit else "",
        "No",  # Package Ready
        "No",  # Floor Plans
        "No",  # Description Ready
        str(args.images) if args.images else "",
        datetime.now().strftime("%Y-%m-%d"),
        args.notes or "",
    ]

    sheets.spreadsheets().values().append(
        spreadsheetId=TRACKER_SHEET_ID,
        range="Projects!A:M",
        valueInputOption="USER_ENTERED",
        body={"values": [row]}
    ).execute()

    print(json.dumps({"status": "added", "project": args.name}))
    return 0


# ── add-submission ───────────────────────────────────────────

def add_submission(args):
    """Log a submission to the Submissions tab."""
    if not TRACKER_SHEET_ID:
        print("ERROR: Set PUBLICATION_TRACKER_SHEET_ID in .env first")
        return 1

    pub_info = PUBLICATIONS_DB.get(args.publication, {})
    sheets = get_sheets_service()

    row = [
        args.project,
        args.publication,
        str(pub_info.get("tier", "")),
        pub_info.get("exclusive", args.exclusive or ""),
        args.date or datetime.now().strftime("%Y-%m-%d"),
        args.contact or pub_info.get("contact", ""),
        "Pending",
        "",  # Response Date
        "",  # Published Date
        "",  # Published URL
        args.notes or "",
    ]

    sheets.spreadsheets().values().append(
        spreadsheetId=TRACKER_SHEET_ID,
        range="Submissions!A:K",
        valueInputOption="USER_ENTERED",
        body={"values": [row]}
    ).execute()

    print(json.dumps({
        "status": "logged",
        "project": args.project,
        "publication": args.publication,
        "exclusive": pub_info.get("exclusive", "Unknown")
    }))
    return 0


# ── update-status ────────────────────────────────────────────

def update_status(args):
    """Update the status of a submission."""
    if not TRACKER_SHEET_ID:
        print("ERROR: Set PUBLICATION_TRACKER_SHEET_ID in .env first")
        return 1

    sheets = get_sheets_service()
    result = sheets.spreadsheets().values().get(
        spreadsheetId=TRACKER_SHEET_ID,
        range="Submissions!A:K",
    ).execute()
    rows = result.get("values", [])

    updated = False
    for i, row in enumerate(rows[1:], start=2):
        if (len(row) > 1 and
                row[0].lower() == args.project.lower() and
                row[1].lower() == args.publication.lower()):
            # Update status (col G = index 6)
            sheets.spreadsheets().values().update(
                spreadsheetId=TRACKER_SHEET_ID,
                range=f"Submissions!G{i}",
                valueInputOption="USER_ENTERED",
                body={"values": [[args.status]]}
            ).execute()

            # Update response date
            today = datetime.now().strftime("%Y-%m-%d")
            if args.status in ("Accepted", "Declined", "No Response"):
                sheets.spreadsheets().values().update(
                    spreadsheetId=TRACKER_SHEET_ID,
                    range=f"Submissions!H{i}",
                    valueInputOption="USER_ENTERED",
                    body={"values": [[today]]}
                ).execute()

            # Update published date and URL
            if args.status == "Published":
                sheets.spreadsheets().values().update(
                    spreadsheetId=TRACKER_SHEET_ID,
                    range=f"Submissions!I{i}:J{i}",
                    valueInputOption="USER_ENTERED",
                    body={"values": [[today, args.url or ""]]}
                ).execute()

            updated = True
            print(json.dumps({
                "status": "updated",
                "project": args.project,
                "publication": args.publication,
                "new_status": args.status
            }))
            break

    if not updated:
        print(f"ERROR: No submission found for '{args.project}' → '{args.publication}'")
        return 1
    return 0


# ── review ───────────────────────────────────────────────────

def review(args):
    """Show all projects and their submission status."""
    if not TRACKER_SHEET_ID:
        print("ERROR: Set PUBLICATION_TRACKER_SHEET_ID in .env first")
        return 1

    sheets = get_sheets_service()

    projects = sheets.spreadsheets().values().get(
        spreadsheetId=TRACKER_SHEET_ID, range="Projects!A:M"
    ).execute().get("values", [])

    submissions = sheets.spreadsheets().values().get(
        spreadsheetId=TRACKER_SHEET_ID, range="Submissions!A:K"
    ).execute().get("values", [])

    # Build submission map
    sub_map = {}
    for row in submissions[1:] if len(submissions) > 1 else []:
        name = row[0] if row else ""
        if name not in sub_map:
            sub_map[name] = []
        sub_map[name].append({
            "publication": row[1] if len(row) > 1 else "",
            "status": row[6] if len(row) > 6 else "",
            "date": row[4] if len(row) > 4 else "",
        })

    output = {"projects": []}
    for row in projects[1:] if len(projects) > 1 else []:
        name = row[0] if row else ""
        output["projects"].append({
            "name": name,
            "firm": row[1] if len(row) > 1 else "",
            "merit": row[6] if len(row) > 6 else "",
            "package_ready": row[7] if len(row) > 7 else "",
            "submissions": sub_map.get(name, [])
        })

    print(json.dumps(output, indent=2))
    return 0


# ── due ──────────────────────────────────────────────────────

def due(args):
    """Show projects that need attention: unsubmitted, pending follow-ups, upcoming deadlines."""
    if not TRACKER_SHEET_ID:
        print("ERROR: Set PUBLICATION_TRACKER_SHEET_ID in .env first")
        return 1

    sheets = get_sheets_service()

    projects = sheets.spreadsheets().values().get(
        spreadsheetId=TRACKER_SHEET_ID, range="Projects!A:M"
    ).execute().get("values", [])

    submissions = sheets.spreadsheets().values().get(
        spreadsheetId=TRACKER_SHEET_ID, range="Submissions!A:K"
    ).execute().get("values", [])

    awards = sheets.spreadsheets().values().get(
        spreadsheetId=TRACKER_SHEET_ID, range="Awards!A:H"
    ).execute().get("values", [])

    submitted_projects = set()
    pending_followups = []
    today = datetime.now()

    for row in submissions[1:] if len(submissions) > 1 else []:
        if row:
            submitted_projects.add(row[0])
        if len(row) > 6 and row[6] == "Pending" and len(row) > 4 and row[4]:
            try:
                pitched = datetime.strptime(row[4], "%Y-%m-%d")
                days_ago = (today - pitched).days
                if days_ago >= 14:
                    pending_followups.append({
                        "project": row[0],
                        "publication": row[1] if len(row) > 1 else "",
                        "days_pending": days_ago,
                        "action": "Follow up" if days_ago < 28 else "Mark as No Response"
                    })
            except ValueError:
                pass

    # Unsubmitted projects with merit 3+
    unsubmitted = []
    for row in projects[1:] if len(projects) > 1 else []:
        if not row:
            continue
        name = row[0]
        merit = row[6] if len(row) > 6 else ""
        if name not in submitted_projects and merit and int(merit) >= 3:
            unsubmitted.append({
                "project": name,
                "firm": row[1] if len(row) > 1 else "",
                "merit": merit,
                "package_ready": row[7] if len(row) > 7 else "No"
            })

    # Upcoming award deadlines
    upcoming_awards = []
    for row in awards[1:] if len(awards) > 1 else []:
        if len(row) > 2 and row[2]:
            try:
                deadline = datetime.strptime(row[2], "%Y-%m-%d")
                days_until = (deadline - today).days
                if 0 <= days_until <= 60:
                    upcoming_awards.append({
                        "award": row[0],
                        "project": row[1] if len(row) > 1 else "",
                        "deadline": row[2],
                        "days_until": days_until
                    })
            except ValueError:
                pass

    print(json.dumps({
        "unsubmitted_projects": unsubmitted,
        "pending_followups": pending_followups,
        "upcoming_deadlines": upcoming_awards,
    }, indent=2))
    return 0


# ── CLI ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Publication submission tracker")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="Create the tracking Google Sheet")

    p_add = sub.add_parser("add-project", help="Add a project to track")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--firm", required=True)
    p_add.add_argument("--contact", default="")
    p_add.add_argument("--location", default="")
    p_add.add_argument("--project-type", default="")
    p_add.add_argument("--completed", default="")
    p_add.add_argument("--merit", type=int, choices=[1, 2, 3, 4, 5])
    p_add.add_argument("--images", type=int)
    p_add.add_argument("--notes", default="")

    p_sub = sub.add_parser("add-submission", help="Log a submission")
    p_sub.add_argument("--project", required=True)
    p_sub.add_argument("--publication", required=True)
    p_sub.add_argument("--date", default="")
    p_sub.add_argument("--contact", default="")
    p_sub.add_argument("--exclusive", default="")
    p_sub.add_argument("--notes", default="")

    p_up = sub.add_parser("update-status", help="Update submission status")
    p_up.add_argument("--project", required=True)
    p_up.add_argument("--publication", required=True)
    p_up.add_argument("--status", required=True,
                      choices=["Pending", "Accepted", "Declined", "Published", "No Response"])
    p_up.add_argument("--url", default="")

    sub.add_parser("review", help="Show all projects and submissions")
    sub.add_parser("due", help="Show what needs attention")

    args = parser.parse_args()

    commands = {
        "init": init_tracker,
        "add-project": add_project,
        "add-submission": add_submission,
        "update-status": update_status,
        "review": review,
        "due": due,
    }

    if args.command in commands:
        return commands[args.command](args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
