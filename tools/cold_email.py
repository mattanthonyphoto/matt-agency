"""Cold email pipeline tool — Sheets I/O, HTML cleaning, Icypeas lookup.

Subcommands:
  fetch-leads   Read unprocessed leads from input sheet
  clean-html    Strip HTML to clean text for qualification
  icypeas-lookup  Find personal email via Icypeas API
  write-result  Append processed lead to output sheet
"""
import argparse
import json
import os
import re
import sys
import time

from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.google_sheets_auth import get_sheets_service

load_dotenv(PROJECT_ROOT / ".env")

INPUT_SHEET_ID = "1qaeT6nURloVQx48dPtJODUz55IrqQEyRJ5xmnJJjoVs"
OUTPUT_SHEET_ID = "1brgQYbtCZwH1fFS3vYjMaW9IGf8iK37qeDBY2l06r8A"

TAB_MAP = {
    "Builders": "Builders",
    "Architects": "Architects",
    "Designers": "Interior Designers",
    "Millwork": "Millwork & Cabinetry",
    "Windows": "Windows & Doors",
    "Steel": "Structural Fabrication",
    "Landscape": "Landscape Architecture",
    "Lighting": "Lighting Design",
    "Flooring": "Flooring & Stone",
    "Hardware": "Hardware & Fixtures",
    "Envelope": "Building Envelope",
}


# ── fetch-leads ──────────────────────────────────────────────

def fetch_leads(args):
    """Read input sheet, subtract already-processed URLs, return JSON."""
    tab = TAB_MAP.get(args.tab)
    if not tab:
        print(f"ERROR: Unknown tab '{args.tab}'. Options: {', '.join(TAB_MAP.keys())}")
        return 1

    sheets = get_sheets_service()

    # Read input leads
    result = sheets.spreadsheets().values().get(
        spreadsheetId=INPUT_SHEET_ID,
        range=f"'{tab}'!A:G",
    ).execute()
    input_rows = result.get("values", [])

    if len(input_rows) < 2:
        print(json.dumps([]))
        return 0

    headers = [h.strip().lower() for h in input_rows[0]]
    col_idx = {}
    for i, h in enumerate(headers):
        if h in ("company name", "company"):
            col_idx["company"] = i
        elif h in ("website url", "website", "url"):
            col_idx["website"] = i
        elif h == "city":
            col_idx["city"] = i
        elif h == "email":
            col_idx["email"] = i
        elif h == "processed":
            col_idx["processed"] = i

    company_col = col_idx.get("company", 0)
    url_col = col_idx.get("website", 1)
    city_col = col_idx.get("city")
    email_col = col_idx.get("email")
    processed_col = col_idx.get("processed")

    leads = []
    for row in input_rows[1:]:
        # Skip rows marked as processed
        if processed_col is not None and len(row) > processed_col:
            if row[processed_col].strip().upper() in ("YES", "TRUE", "DONE", "1"):
                continue

        company = row[company_col].strip() if len(row) > company_col else ""
        url = row[url_col].strip() if len(row) > url_col else ""
        city = row[city_col].strip() if city_col is not None and len(row) > city_col else ""
        email = row[email_col].strip() if email_col is not None and len(row) > email_col else ""
        if url:
            lead = {"company": company, "website": url}
            if city:
                lead["city"] = city
            if email:
                lead["email"] = email
            leads.append(lead)

    # Read already-processed URLs from output sheet (Website is col J)
    try:
        out_result = sheets.spreadsheets().values().get(
            spreadsheetId=OUTPUT_SHEET_ID,
            range=f"'{tab}'!J:J",
        ).execute()
        processed_urls = set()
        for row in out_result.get("values", [])[1:]:
            if row:
                processed_urls.add(row[0].strip().lower().rstrip("/"))
    except Exception:
        processed_urls = set()

    # Filter unprocessed
    unprocessed = [
        lead for lead in leads
        if lead["website"].lower().rstrip("/") not in processed_urls
    ]

    print(json.dumps(unprocessed, indent=2))
    return 0


# ── clean-html ───────────────────────────────────────────────

def clean_html(args):
    """Strip HTML to plain text suitable for AI qualification."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: File not found: {args.input}")
        return 1

    with open(input_path) as f:
        data = json.load(f)

    # data is either a list of {url, html} or a single {url, html}
    pages = data if isinstance(data, list) else [data]

    cleaned_pages = []
    for page in pages[:5]:
        url = page.get("url", "")
        html = page.get("html", "")

        text = _strip_html(html)
        # Truncate to 1500 chars per page
        if len(text) > 1500:
            text = text[:1500] + "..."

        cleaned_pages.append({"url": url, "content": text})

    # Combined content for the qualifier
    combined = "\n\n---\n\n".join(
        f"PAGE: {p['url']}\n{p['content']}" for p in cleaned_pages
    )

    output = {
        "pages": cleaned_pages,
        "combined_content": combined,
    }

    print(json.dumps(output, indent=2))
    return 0


def _strip_html(html):
    """Remove HTML tags, scripts, styles, nav, footer, and boilerplate."""
    if not html:
        return ""

    # Remove script and style blocks
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove nav and footer blocks
    text = re.sub(r"<nav[^>]*>.*?</nav>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<footer[^>]*>.*?</footer>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<header[^>]*>.*?</header>", " ", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove all HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Decode common HTML entities
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    text = text.replace("&nbsp;", " ")
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"&\w+;", " ", text)

    # Remove cookie/privacy boilerplate patterns
    boilerplate_patterns = [
        r"(?i)we use cookies.*?(?:accept|dismiss|close|learn more)[.\s]*",
        r"(?i)this (website|site) uses cookies.*?(?:\.|$)",
        r"(?i)privacy policy.*?(?:\.|$)",
        r"(?i)cookie (policy|settings|preferences).*?(?:\.|$)",
        r"(?i)by (continuing|using) (this|our) (site|website).*?(?:\.|$)",
        r"(?i)accept all cookies",
        r"(?i)manage (cookie )?preferences",
    ]
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, " ", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ── icypeas-lookup ───────────────────────────────────────────

def icypeas_lookup(args):
    """Search for personal email via Icypeas API."""
    import requests

    api_key = os.getenv("ICYPEAS_API_KEY")
    if not api_key:
        print("ERROR: ICYPEAS_API_KEY not set in .env")
        return 1

    # Step 1: Submit search
    search_payload = {
        "firstname": args.first_name,
        "lastname": args.last_name,
        "domainOrCompany": args.domain,
    }

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(
            "https://app.icypeas.com/api/email-search",
            headers=headers,
            json=search_payload,
            timeout=30,
        )
        resp.raise_for_status()
        search_result = resp.json()
    except Exception as e:
        print(json.dumps({"email": "", "error": str(e)}))
        return 1

    # Get the search ID
    item = search_result.get("item", {})
    search_id = item.get("_id", "")

    if not search_id:
        print(json.dumps({"email": "", "error": "No search ID returned"}))
        return 1

    # Step 2: Wait for processing
    print(f"Icypeas search submitted (ID: {search_id}), waiting 10s...", file=sys.stderr)
    time.sleep(10)

    # Step 3: Fetch result
    try:
        resp = requests.post(
            "https://app.icypeas.com/api/bulk-single-searchs/read",
            headers=headers,
            json={"id": search_id},
            timeout=30,
        )
        resp.raise_for_status()
        fetch_result = resp.json()
    except Exception as e:
        print(json.dumps({"email": "", "error": str(e)}))
        return 1

    # Step 4: Extract best email
    items = fetch_result.get("items", [])
    result = items[0] if items else {}
    emails = result.get("emails", [])

    certainty_rank = {
        "ultra_sure": 4,
        "very_sure": 3,
        "probable": 2,
        "not_found": 0,
        "undeliverable": -1,
    }

    best_email = ""
    best_certainty = "not_found"
    best_score = -1

    for e in emails:
        score = certainty_rank.get(e.get("certainty", ""), 0)
        if score > best_score:
            best_score = score
            best_email = e.get("email", "")
            best_certainty = e.get("certainty", "not_found")

    is_deliverable = best_certainty in ("very_sure", "ultra_sure", "probable")

    output = {
        "email": best_email if is_deliverable else "",
        "certainty": best_certainty,
        "deliverable": is_deliverable,
        "all_emails": [e.get("email", "") for e in emails],
    }

    print(json.dumps(output, indent=2))
    return 0


# ── write-result ─────────────────────────────────────────────

def write_result(args):
    """Append or update a row in the output sheet.

    Output sheet columns (A:W):
    A=Company  B=Decision Maker  C=Role  D=City  E=Score  F=ICP
    G=Email  H=Phone  I=Instagram  J=Website  K=Outreach  L=Status
    M=Timeline  N=Intro Subject  O=Intro Email  P=Follow-Up Subject
    Q=Follow-Up Email  R=Breakup Subject  S=Breakup Email
    T=Instagram DM  U=Travel Est.  V=Marketing Angle  W=Notes
    """
    input_path = Path(args.json)
    if not input_path.exists():
        print(f"ERROR: File not found: {args.json}")
        return 1

    with open(input_path) as f:
        data = json.load(f)

    sheets = get_sheets_service()

    # Prefix URLs for Sheets auto-linking
    def prefix_url(body):
        if not body or not isinstance(body, str):
            return ""
        return re.sub(
            r"(?<!/)(?<!\w)(mattanthonyphoto\.com(?:/[^\s,;:!?)\"'>]*)?)",
            lambda m: "https://" + m.group(0).rstrip(".,;:!?)"),
            body,
        )

    # Force text for values that Sheets might interpret as formulas
    def safe_text(val):
        if not val:
            return ""
        val = str(val)
        if val.startswith(("+", "=", "-")) and not val.startswith(("https://", "http://")):
            return "'" + val
        return val

    # Match exact output sheet column order (A:W)
    row = [
        data.get("company_name", ""),           # A: Company
        data.get("decision_maker_name", ""),     # B: Decision Maker
        data.get("role", ""),                    # C: Role
        data.get("city", ""),                    # D: City
        data.get("qualified", ""),               # E: Score
        data.get("icp_category", ""),            # F: ICP
        data.get("email", ""),                   # G: Email
        safe_text(data.get("phone", "")),          # H: Phone
        data.get("instagram", ""),               # I: Instagram
        data.get("website_url", ""),             # J: Website
        data.get("outreach_type", ""),           # K: Outreach
        "",                                      # L: Status (blank — set manually)
        data.get("timeline", ""),                # M: Timeline
        data.get("intro_subject", ""),           # N: Intro Subject
        prefix_url(data.get("intro_email", "")), # O: Intro Email
        data.get("followup_subject", ""),        # P: Follow-Up Subject
        prefix_url(data.get("followup_email", "")),  # Q: Follow-Up Email
        data.get("breakup_subject", ""),         # R: Breakup Subject
        prefix_url(data.get("breakup_email", "")),   # S: Breakup Email
        data.get("instagram_dm", ""),            # T: Instagram DM
        data.get("travel_est", ""),              # U: Travel Est.
        data.get("marketing_angle", ""),         # V: Marketing Angle
        data.get("notes", ""),                   # W: Notes
    ]

    # Determine output tab
    output_tab = TAB_MAP.get(args.tab, "Builders")

    # Check if website URL already exists in output sheet col J
    website_url = data.get("website_url", "")
    existing_row = None

    try:
        out_result = sheets.spreadsheets().values().get(
            spreadsheetId=OUTPUT_SHEET_ID,
            range=f"'{output_tab}'!J:J",
        ).execute()
        for i, r in enumerate(out_result.get("values", [])):
            if r and r[0].strip().lower().rstrip("/") == website_url.lower().rstrip("/"):
                existing_row = i + 1  # 1-indexed
                break
    except Exception:
        pass

    if existing_row:
        # Update existing row
        range_str = f"'{output_tab}'!A{existing_row}:W{existing_row}"
        sheets.spreadsheets().values().update(
            spreadsheetId=OUTPUT_SHEET_ID,
            range=range_str,
            valueInputOption="USER_ENTERED",
            body={"values": [row]},
        ).execute()
        print(f"Updated row {existing_row} for {data.get('company_name', 'unknown')}")
    else:
        # Append new row
        sheets.spreadsheets().values().append(
            spreadsheetId=OUTPUT_SHEET_ID,
            range=f"'{output_tab}'!A:W",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()
        print(f"Appended row for {data.get('company_name', 'unknown')}")

    return 0


# ── mark-processed ────────────────────────────────────────────

def mark_processed(args):
    """Mark a lead as processed in the input sheet.

    Updates the Processed (col G) and Qualified (col H) columns
    for the row matching the given website URL.
    """
    sheets = get_sheets_service()
    tab = TAB_MAP.get(args.tab)
    if not tab:
        print(f"ERROR: Unknown tab '{args.tab}'. Options: {', '.join(TAB_MAP.keys())}")
        return 1

    # Read all rows to find the matching URL
    result = sheets.spreadsheets().values().get(
        spreadsheetId=INPUT_SHEET_ID,
        range=f"'{tab}'!A:H",
    ).execute()
    rows = result.get("values", [])

    if len(rows) < 2:
        print("ERROR: No data rows in sheet")
        return 1

    headers = [h.strip().lower() for h in rows[0]]
    url_col = None
    processed_col = None
    qualified_col = None

    for i, h in enumerate(headers):
        if h in ("website url", "website", "url"):
            url_col = i
        elif h == "processed":
            processed_col = i
        elif h == "qualified":
            qualified_col = i

    if url_col is None:
        print("ERROR: No website column found in headers")
        return 1

    target_url = args.website.lower().rstrip("/")
    # Normalize: strip UTM params, protocol, www prefix for matching
    target_clean = re.sub(r"\?.*$", "", target_url)
    target_norm = re.sub(r"^https?://(www\.)?", "", target_clean).rstrip("/")

    for row_idx, row in enumerate(rows[1:], start=2):  # 1-indexed, skip header
        if len(row) <= url_col:
            continue
        row_url = row[url_col].strip().lower().rstrip("/")
        row_clean = re.sub(r"\?.*$", "", row_url)
        row_norm = re.sub(r"^https?://(www\.)?", "", row_clean).rstrip("/")
        if row_norm == target_norm or row_clean == target_clean or row_url == target_url:
            updates = []
            if processed_col is not None:
                cell = f"'{tab}'!{chr(65 + processed_col)}{row_idx}"
                updates.append({"range": cell, "values": [[args.status]]})
            if qualified_col is not None and args.qualified:
                cell = f"'{tab}'!{chr(65 + qualified_col)}{row_idx}"
                updates.append({"range": cell, "values": [[args.qualified]]})

            if updates:
                sheets.spreadsheets().values().batchUpdate(
                    spreadsheetId=INPUT_SHEET_ID,
                    body={"valueInputOption": "USER_ENTERED", "data": updates},
                ).execute()
                print(f"Marked row {row_idx} as processed: {args.status}")
            return 0

    print(f"WARNING: URL not found in {tab} tab: {args.website}")
    return 1


# ── export-instantly ──────────────────────────────────────────

def export_instantly(args):
    """Export qualified leads as Instantly-compatible CSV for import."""
    import csv

    sheets = get_sheets_service()

    # Read output sheet
    output_tab = TAB_MAP.get(args.tab, "Builders")
    result = sheets.spreadsheets().values().get(
        spreadsheetId=OUTPUT_SHEET_ID,
        range=f"'{output_tab}'!A:T",
    ).execute()
    rows = result.get("values", [])

    if len(rows) < 2:
        print("No leads to export")
        return 1

    header = rows[0]
    data = rows[1:]

    # Map output sheet columns (A:W) to Instantly fields
    # Output layout: A=Company B=Decision Maker C=Role D=City E=Score
    # F=ICP G=Email H=Phone I=Instagram J=Website K=Outreach
    # L=Status M=Timeline N=Intro Subject O=Intro Email
    # P=FU Subject Q=FU Email R=Breakup Subject S=Breakup Email
    # T=Instagram DM U=Travel Est V=Marketing Angle W=Notes
    output_path = Path(args.output) if args.output else PROJECT_ROOT / ".tmp" / "instantly_import.csv"

    instantly_rows = []
    for row in data:
        while len(row) < 23:
            row.append("")

        email = row[6]   # G: Email
        if not email or "N/A" in email:
            continue

        # Split decision maker name into first/last
        dm_name = row[1].strip()  # B: Decision Maker
        name_parts = dm_name.split(" ", 1) if dm_name else ["", ""]
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        instantly_row = {
            "Email": email,
            "First Name": first_name,
            "Last Name": last_name,
            "Company Name": row[0],   # A: Company
            "Phone": row[7],          # H: Phone
            "Website": row[9],        # J: Website
            "Location": row[3],       # D: City
            "intro_subject": row[13], # N: Intro Subject
            "intro_body": row[14],    # O: Intro Email
            "followup_body": row[16], # Q: Follow-Up Email
            "breakup_body": row[18],  # S: Breakup Email
            "ig_handle": row[8],      # I: Instagram
            "ig_dm": row[19],         # T: Instagram DM
        }
        instantly_rows.append(instantly_row)

    if not instantly_rows:
        print("No leads with emails to export")
        return 1

    # Write CSV
    fieldnames = list(instantly_rows[0].keys())
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(instantly_rows)

    print(f"Exported {len(instantly_rows)} leads to {output_path}")
    print(f"Columns: {', '.join(fieldnames)}")
    print(f"\nInstantly setup:")
    print(f"  1. Import this CSV into Instantly (Email column auto-detected)")
    print(f"  2. Predefined fields auto-map: First Name, Last Name, Company Name, Phone, Website, Location")
    print(f"  3. Create 3-step sequence:")
    print(f"     Step 1 (Day 1): Subject={{{{intro_subject}}}} Body={{{{intro_body}}}}")
    print(f"     Step 2 (+3 days): LEAVE SUBJECT BLANK (reply-in-thread) Body={{{{followup_body}}}}")
    print(f"     Step 3 (+4 days): LEAVE SUBJECT BLANK (reply-in-thread) Body={{{{breakup_body}}}}")
    print(f"  4. Reply-in-thread sends follow-ups as replies to Step 1 — higher open rates")
    print(f"  5. Use fallbacks: {{{{First Name|there}}}} in case any name is missing")
    print(f"  6. IMPORTANT: Send from secondary domain (not mattanthonyphoto.com)")
    print(f"     Warm up accounts 2-3 weeks before launching")
    return 0


# ── CLI ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Cold email pipeline tool")
    sub = parser.add_subparsers(dest="command")

    # fetch-leads
    fl = sub.add_parser("fetch-leads", help="Get unprocessed leads from input sheet")
    fl.add_argument("--tab", required=True, choices=list(TAB_MAP.keys()),
                     help="Which ICP tab to read")

    # clean-html
    ch = sub.add_parser("clean-html", help="Strip HTML to clean text")
    ch.add_argument("--input", required=True, help="Path to JSON file with scraped HTML")

    # icypeas-lookup
    il = sub.add_parser("icypeas-lookup", help="Find email via Icypeas")
    il.add_argument("--first-name", required=True)
    il.add_argument("--last-name", required=True)
    il.add_argument("--domain", required=True)

    # write-result
    wr = sub.add_parser("write-result", help="Write result to output sheet")
    wr.add_argument("--json", required=True, help="Path to JSON file with result data")
    wr.add_argument("--tab", required=False, choices=list(TAB_MAP.keys()),
                     default="Builders", help="Which output tab to write to")

    # mark-processed
    mp = sub.add_parser("mark-processed", help="Mark lead as processed in input sheet")
    mp.add_argument("--tab", required=True, choices=list(TAB_MAP.keys()),
                     help="Which ICP tab")
    mp.add_argument("--website", required=True, help="Website URL to match")
    mp.add_argument("--status", default="Yes", help="Value for Processed column")
    mp.add_argument("--qualified", default="NOT QUALIFIED",
                     help="Value for Qualified column (e.g. 'QUALIFIED — Strong Fit')")

    # export-instantly
    ei = sub.add_parser("export-instantly", help="Export leads as Instantly CSV")
    ei.add_argument("--tab", required=False, choices=list(TAB_MAP.keys()),
                     default="Builders", help="Which output tab to export")
    ei.add_argument("--output", required=False, help="Output CSV path (default: .tmp/instantly_import.csv)")

    args = parser.parse_args()

    if args.command == "fetch-leads":
        return fetch_leads(args)
    elif args.command == "clean-html":
        return clean_html(args)
    elif args.command == "icypeas-lookup":
        return icypeas_lookup(args)
    elif args.command == "write-result":
        return write_result(args)
    elif args.command == "mark-processed":
        return mark_processed(args)
    elif args.command == "export-instantly":
        return export_instantly(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
