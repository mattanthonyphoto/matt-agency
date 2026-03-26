"""
Software Audit Tool
Reads transactions from 2025 and 2026 Finance Tracker sheets,
identifies all software/subscription spending, and writes an audit report.
"""
import os
import sys
import re
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.google_sheets_auth import get_sheets_service

SHEET_2025 = "1TyX4sOIo6CxblxjNM9Yft5h5vZO_BGhQjHlgC0uzQtI"
SHEET_2026 = "1fPpOPnAYEnfCu33h1ki9NzFGTUOkpgd4mMSQX_sT9CY"

# Software vendor patterns - broad matching
SOFTWARE_PATTERNS = [
    # Exact known tools
    (r"Adobe", "Adobe Creative Cloud", "Photo/Video Editing"),
    (r"Dropbox", "Dropbox", "Cloud Storage"),
    (r"GOOGLE\s*\*?\s*Workspace", "Google Workspace", "Email & Productivity"),
    (r"GOOGLE\s*\*?\s*STORAGE", "Google Storage", "Cloud Storage"),
    (r"GOOGLE\s*\*?\s*One", "Google One", "Cloud Storage"),
    (r"GOOGLE\s*\*?\s*DOMAINS", "Google Domains", "Domain Registration"),
    (r"GOOGLE\s*\*?\s*Cloud", "Google Cloud", "Cloud Services"),
    (r"GOOGLE\s*\*?\s*ADs", "Google Ads", "Advertising"),
    (r"GOOGLE\s*\*?\s*YT", "YouTube Premium", "Media"),
    (r"HIGHLEVEL|GoHighLevel|GOHIGHLEVEL", "GoHighLevel", "CRM & Marketing"),
    (r"ANTHROPIC|Claude", "Anthropic (Claude)", "AI Assistant"),
    (r"OPENAI|CHATGPT", "ChatGPT Plus", "AI Assistant"),
    (r"OPENROUTER", "OpenRouter", "AI API Gateway"),
    (r"SQUARESPACE", "Squarespace", "Website Hosting"),
    (r"INSTANTLY", "Instantly", "Cold Email Platform"),
    (r"SPOTIFY", "Spotify", "Music Streaming"),
    (r"INTUIT.*QBooks|QUICKBOOKS|QBO", "QuickBooks Online", "Accounting"),
    (r"BUFFER", "Buffer", "Social Media Management"),
    (r"CLICKUP", "ClickUp", "Project Management"),
    (r"EpidemicSound|EPIDEMIC", "Epidemic Sound", "Music Licensing"),
    (r"Audible|AUDIBLE", "Audible", "Audiobooks/Learning"),
    (r"EXPRESSVPN|EXPRESS\s*VPN", "ExpressVPN", "VPN"),
    (r"LEADGENJAY", "LeadGenJay", "Lead Scraping"),
    (r"APIFY", "Apify", "Web Scraping"),
    (r"ICYPEAS", "IcyPeas", "Email Verification"),
    (r"APPLE\.COM|APPLE\s", "Apple (iCloud/Services)", "Cloud Storage / Services"),
    (r"AMAZON\s*PRIME|AMZN.*Prime", "Amazon Prime", "Shopping/Streaming"),
    (r"NETFLIX", "Netflix", "Streaming"),
    (r"CANVA", "Canva", "Design"),
    (r"NOTION", "Notion", "Productivity"),
    (r"SLACK", "Slack", "Communication"),
    (r"ZOOM", "Zoom", "Video Conferencing"),
    (r"MICROSOFT|MSFT", "Microsoft 365", "Productivity"),
    (r"GITHUB|GH\s", "GitHub", "Development"),
    (r"FIGMA", "Figma", "Design"),
    (r"MAILCHIMP", "Mailchimp", "Email Marketing"),
    (r"HOOTSUITE", "Hootsuite", "Social Media"),
    (r"SEMRUSH|AHREFS", "SEO Tool", "SEO"),
    (r"CLOUDFLARE", "Cloudflare", "Web Infrastructure"),
    (r"NAMECHEAP", "Namecheap", "Domain Registration"),
    (r"GODADDY", "GoDaddy", "Domain/Hosting"),
    (r"SHUTTERSTOCK|GETTYIMAGES|STOCK", "Stock Media", "Stock Photos/Video"),
    (r"GRAMMARLY", "Grammarly", "Writing"),
    (r"1PASSWORD|LASTPASS|BITWARDEN|DASHLANE", "Password Manager", "Security"),
    (r"AIRALO", "Airalo", "eSIM / Travel Data"),
    (r"N8N|n8n", "n8n", "Workflow Automation"),
    (r"LOOM", "Loom", "Video Messaging"),
    (r"CALENDLY", "Calendly", "Scheduling"),
    (r"MIRO", "Miro", "Whiteboarding"),
    (r"LINEAR", "Linear", "Project Management"),
    (r"VERCEL", "Vercel", "Web Hosting"),
    (r"NETLIFY", "Netlify", "Web Hosting"),
    (r"TYPEFORM", "Typeform", "Forms"),
    (r"STRIPE", "Stripe", "Payment Processing"),
    (r"PAYPAL", "PayPal", "Payment Processing"),
    (r"SHOWPASS", "Showpass", "Event Ticketing"),
    (r"WAVE\s*APP|WAVEAPPS", "Wave", "Accounting"),
    (r"FRESHBOOKS", "FreshBooks", "Accounting"),
    (r"HONEYBOOK", "HoneyBook", "Client Management"),
    (r"PIXIESET", "Pixieset", "Photo Delivery"),
    (r"SMUGMUG", "SmugMug", "Photo Hosting"),
    (r"ZENFOLIO", "Zenfolio", "Photo Hosting"),
    (r"PIC-TIME|PICTIME", "Pic-Time", "Photo Delivery"),
    (r"DARKROOM|LIGHTROOM", "Lightroom", "Photo Editing"),
    (r"CAPTURE\s*ONE", "Capture One", "Photo Editing"),
    (r"BACKBLAZE", "Backblaze", "Cloud Backup"),
    (r"TODOIST", "Todoist", "Task Management"),
    (r"TRELLO", "Trello", "Project Management"),
    (r"ASANA", "Asana", "Project Management"),
    (r"DESCRIPT", "Descript", "Video/Audio Editing"),
    (r"RIVERSIDE", "Riverside", "Podcast Recording"),
    (r"INVIDEO|INSHOT", "Video Tool", "Video Editing"),
    (r"MIDJOURNEY", "Midjourney", "AI Image Generation"),
    (r"PERPLEXITY", "Perplexity", "AI Search"),
    (r"CURSOR", "Cursor", "AI Code Editor"),
    (r"REPLIT", "Replit", "Development"),
    (r"HETZNER|DIGITALOCEAN|LINODE|VULTR|AWS", "Cloud Server", "Infrastructure"),
    (r"TWILIO|SENDGRID", "Communication API", "API Services"),
]

def get_transactions(service, sheet_id, tab_name="Transactions"):
    """Fetch all transactions from a sheet tab."""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"'{tab_name}'!A1:Z5000"
        ).execute()
        return result.get("values", [])
    except Exception as e:
        print(f"  Error reading {tab_name} from {sheet_id}: {e}")
        # Try common alternative names
        for alt in ["Transactions", "All Transactions", "transactions", "Sheet1"]:
            if alt != tab_name:
                try:
                    result = service.spreadsheets().values().get(
                        spreadsheetId=sheet_id,
                        range=f"'{alt}'!A1:Z5000"
                    ).execute()
                    print(f"  Found data in tab: {alt}")
                    return result.get("values", [])
                except:
                    continue
        return []


def get_sheet_tabs(service, sheet_id):
    """List all tab names in a sheet."""
    meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    return [(s['properties']['title'], s['properties']['sheetId']) for s in meta['sheets']]


def identify_software(description, category=""):
    """Check if a transaction is software/subscription related."""
    text = f"{description} {category}".upper()

    for pattern, name, cat in SOFTWARE_PATTERNS:
        if re.search(pattern, description, re.IGNORECASE):
            return name, cat

    # Also catch by category
    cat_lower = category.lower() if category else ""
    if any(kw in cat_lower for kw in ["software", "subscription", "saas", "8871"]):
        return description.strip(), "Software (from category)"

    return None, None


def parse_amount(val):
    """Parse a dollar amount string to float."""
    if not val:
        return 0.0
    val = str(val).replace("$", "").replace(",", "").replace(" ", "").strip()
    # Handle parentheses for negatives
    if val.startswith("(") and val.endswith(")"):
        val = "-" + val[1:-1]
    try:
        return float(val)
    except:
        return 0.0


def main():
    service = get_sheets_service()

    # First, discover tab names
    print("=== Discovering sheet structure ===")
    tabs_2025 = get_sheet_tabs(service, SHEET_2025)
    tabs_2026 = get_sheet_tabs(service, SHEET_2026)
    print(f"2025 tabs: {[t[0] for t in tabs_2025]}")
    print(f"2026 tabs: {[t[0] for t in tabs_2026]}")

    # Find transaction tabs
    all_software = defaultdict(lambda: {"charges": [], "total": 0, "category": "", "months": set()})

    for year, sheet_id, tabs in [("2025", SHEET_2025, tabs_2025), ("2026", SHEET_2026, tabs_2026)]:
        print(f"\n=== Processing {year} ===")

        # Try to find transaction-like tabs
        for tab_name, tab_id in tabs:
            print(f"\n  Reading tab: {tab_name}")
            rows = get_transactions(service, sheet_id, tab_name)
            if not rows:
                print(f"    No data found")
                continue

            # Print headers for debugging
            headers = rows[0] if rows else []
            print(f"    Headers: {headers[:10]}")
            print(f"    Total rows: {len(rows)}")

            # Find relevant columns
            header_lower = [h.lower().strip() for h in headers]

            # Look for date, description, amount, category columns
            date_col = None
            desc_col = None
            amount_col = None
            cat_col = None
            debit_col = None
            credit_col = None
            split_col = None

            for i, h in enumerate(header_lower):
                if h in ["date", "transaction date", "trans date"]:
                    date_col = i
                elif h in ["description", "desc", "vendor", "merchant", "transaction", "name", "memo"]:
                    desc_col = i
                elif h in ["amount", "total", "charge", "cost"]:
                    amount_col = i
                elif h in ["category", "cat", "type", "t2125 category", "cra category"]:
                    cat_col = i
                elif h in ["debit", "withdrawal"]:
                    debit_col = i
                elif h in ["credit", "deposit"]:
                    credit_col = i
                elif "split" in h or "%" in h:
                    split_col = i

            print(f"    Columns: date={date_col}, desc={desc_col}, amount={amount_col}, cat={cat_col}, debit={debit_col}")

            if desc_col is None:
                # Try matching more loosely
                for i, h in enumerate(header_lower):
                    if "desc" in h or "vendor" in h or "merchant" in h or "name" in h:
                        desc_col = i
                        break

            if desc_col is None:
                print(f"    Skipping - no description column found")
                continue

            # Process rows
            sw_count = 0
            for row in rows[1:]:
                if len(row) <= desc_col:
                    continue

                desc = row[desc_col] if desc_col < len(row) else ""
                category = row[cat_col] if cat_col is not None and cat_col < len(row) else ""

                name, sw_cat = identify_software(desc, category)
                if not name:
                    continue

                # Get amount
                amt = 0
                if amount_col is not None and amount_col < len(row):
                    amt = abs(parse_amount(row[amount_col]))
                elif debit_col is not None and debit_col < len(row):
                    amt = abs(parse_amount(row[debit_col]))

                # Apply split percentage if exists
                if split_col is not None and split_col < len(row):
                    split_val = row[split_col]
                    if split_val:
                        try:
                            pct = float(str(split_val).replace("%", "").strip())
                            if 0 < pct < 1:
                                amt = amt * pct
                            elif 1 < pct <= 100:
                                amt = amt * (pct / 100)
                        except:
                            pass

                if amt == 0:
                    continue

                # Get date for month tracking
                date_str = row[date_col] if date_col is not None and date_col < len(row) else ""
                month = ""
                if date_str:
                    try:
                        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"]:
                            try:
                                dt = __import__("datetime").datetime.strptime(date_str.strip(), fmt)
                                month = f"{year}-{dt.month:02d}"
                                break
                            except:
                                continue
                    except:
                        pass

                all_software[name]["charges"].append(amt)
                all_software[name]["total"] += amt
                all_software[name]["category"] = sw_cat
                if month:
                    all_software[name]["months"].add(month)
                sw_count += 1

            if sw_count > 0:
                print(f"    Found {sw_count} software transactions")

    # Calculate summary
    print("\n\n" + "=" * 80)
    print("SOFTWARE / SUBSCRIPTION AUDIT REPORT")
    print("=" * 80)

    # Sort by total spend descending
    sorted_tools = sorted(all_software.items(), key=lambda x: x[1]["total"], reverse=True)

    grand_total = sum(v["total"] for v in all_software.values())

    # Estimate monthly cost based on number of months observed
    report_data = []
    for name, data in sorted_tools:
        n_charges = len(data["charges"])
        total = data["total"]
        n_months = len(data["months"]) if data["months"] else n_charges

        if n_months > 0:
            monthly_est = total / max(n_months, 1)
        else:
            monthly_est = total

        # Annualize: if we only have partial year data, project forward
        annual_est = monthly_est * 12

        # Determine if essential
        essential = categorize_essential(name, data["category"])

        report_data.append({
            "name": name,
            "monthly": monthly_est,
            "annual": annual_est,
            "actual_spent": total,
            "n_charges": n_charges,
            "n_months": n_months,
            "category": data["category"],
            "essential": essential,
            "charges": data["charges"],
        })

        print(f"\n{name}")
        print(f"  Category: {data['category']}")
        print(f"  Total Spent: ${total:,.2f} across {n_charges} charges")
        print(f"  Est. Monthly: ${monthly_est:,.2f}")
        print(f"  Est. Annual: ${annual_est:,.2f}")
        print(f"  Assessment: {essential}")

    print(f"\n{'=' * 80}")
    print(f"TOTAL ACTUAL SPEND: ${grand_total:,.2f}")
    print(f"ESTIMATED ANNUAL RUN-RATE: ${sum(r['annual'] for r in report_data):,.2f}")

    # Flag overlaps
    print(f"\n{'=' * 80}")
    print("OVERLAP / REDUNDANCY FLAGS")
    print("=" * 80)
    overlaps = find_overlaps(report_data)
    for overlap in overlaps:
        print(f"  ⚠ {overlap}")

    # Write to Google Sheet
    print(f"\n{'=' * 80}")
    print("Writing audit to 2026 Finance Sheet...")
    write_audit_tab(service, SHEET_2026, report_data, grand_total, overlaps, tabs_2026)
    print("Done!")

    return report_data, grand_total


def categorize_essential(name, category):
    """Rate a tool as Essential / Nice-to-Have / Cut."""
    essential_tools = [
        "Adobe Creative Cloud", "Google Workspace", "Dropbox",
        "Squarespace", "QuickBooks Online",
    ]
    core_business = [
        "GoHighLevel", "Anthropic (Claude)", "Instantly",
        "Google Storage", "Google One", "n8n",
    ]
    nice_to_have = [
        "ChatGPT Plus", "OpenRouter", "Buffer", "Epidemic Sound",
        "ExpressVPN", "Audible", "Capture One",
    ]
    likely_cut = [
        "ClickUp", "LeadGenJay", "Apify", "IcyPeas",
        "Spotify", "Netflix", "Amazon Prime",
        "Showpass",
    ]

    if name in essential_tools:
        return "ESSENTIAL — Core to business operations"
    elif name in core_business:
        return "ESSENTIAL — Revenue-generating tool"
    elif name in nice_to_have:
        return "NICE-TO-HAVE — Useful but could downgrade/pause"
    elif name in likely_cut:
        return "CONSIDER CUTTING — Low ROI or redundant"
    else:
        return "REVIEW — Assess if still needed"


def find_overlaps(report_data):
    """Find overlapping/redundant tools."""
    overlaps = []

    categories = defaultdict(list)
    for r in report_data:
        categories[r["category"]].append(r["name"])

    # Check specific overlaps
    names = [r["name"] for r in report_data]

    if "Google One" in names and "Dropbox" in names:
        overlaps.append("Google One + Dropbox: Both are cloud storage. Could consolidate to one.")
    if "ChatGPT Plus" in names and "Anthropic (Claude)" in names:
        overlaps.append("ChatGPT + Claude: Two AI assistants. Consider keeping only your primary one.")
    if "ClickUp" in names and "Linear" in names:
        overlaps.append("ClickUp + Linear: Two project management tools. Pick one.")
    if "ClickUp" in names and "Notion" in names:
        overlaps.append("ClickUp + Notion: Overlapping project/note tools. Notion may cover both.")
    if "QuickBooks Online" in names and "Wave" in names:
        overlaps.append("QuickBooks + Wave: Two accounting tools. Wave is free.")
    if "LeadGenJay" in names and "Apify" in names:
        overlaps.append("LeadGenJay + Apify: Both scraping tools. May only need one.")
    if "LeadGenJay" in names and "IcyPeas" in names:
        overlaps.append("LeadGenJay + IcyPeas: LeadGenJay may include email finding.")
    if "Buffer" in names and "Hootsuite" in names:
        overlaps.append("Buffer + Hootsuite: Two social media tools. Keep only one.")
    if "Google Workspace" in names and "Microsoft 365" in names:
        overlaps.append("Google Workspace + Microsoft 365: Two productivity suites.")
    if "OpenRouter" in names and "ChatGPT Plus" in names and "Anthropic (Claude)" in names:
        overlaps.append("OpenRouter + ChatGPT + Claude: Three AI tools. OpenRouter gives access to multiple models — could replace subscriptions.")
    if "Capture One" in names and "Adobe Creative Cloud" in names:
        overlaps.append("Capture One + Adobe (Lightroom): Two photo editors. Adobe CC already includes Lightroom.")

    for cat, tools in categories.items():
        if len(tools) > 2 and cat not in ["Cloud Storage", "AI Assistant"]:
            overlaps.append(f"Multiple {cat} tools: {', '.join(tools)}")

    return overlaps


def write_audit_tab(service, sheet_id, report_data, grand_total, overlaps, existing_tabs):
    """Write the software audit to a new tab in the 2026 sheet."""

    # Check if tab already exists
    tab_exists = False
    old_tab_id = None
    for name, tid in existing_tabs:
        if name == "Software Audit":
            tab_exists = True
            old_tab_id = tid
            break

    requests = []

    if tab_exists:
        # Clear existing content
        requests.append({
            "updateCells": {
                "range": {"sheetId": old_tab_id},
                "fields": "userEnteredValue,userEnteredFormat"
            }
        })
        new_tab_id = old_tab_id
    else:
        new_tab_id = 9999
        requests.append({
            "addSheet": {
                "properties": {
                    "sheetId": new_tab_id,
                    "title": "Software Audit",
                    "gridProperties": {"rowCount": 100, "columnCount": 10},
                    "tabColor": {"red": 0.85, "green": 0.33, "blue": 0.31}
                }
            }
        })

    # Execute sheet creation first
    if requests:
        try:
            service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body={"requests": requests}
            ).execute()
        except Exception as e:
            if "already exists" in str(e).lower():
                # Find the existing tab id
                for name, tid in existing_tabs:
                    if name == "Software Audit":
                        new_tab_id = tid
                        break
            else:
                print(f"Error creating tab: {e}")
                return

    # Design system colors
    HEADER_BG = {"red": 0.153, "green": 0.173, "blue": 0.220}  # #272c38
    HEADER_FG = {"red": 1, "green": 1, "blue": 1}
    ZEBRA_LIGHT = {"red": 0.969, "green": 0.973, "blue": 0.980}  # #f7f8fa
    ZEBRA_WHITE = {"red": 1, "green": 1, "blue": 1}
    ESSENTIAL_BG = {"red": 0.85, "green": 0.95, "blue": 0.85}
    NICE_BG = {"red": 1, "green": 0.95, "blue": 0.8}
    CUT_BG = {"red": 1, "green": 0.85, "blue": 0.85}
    REVIEW_BG = {"red": 0.95, "green": 0.95, "blue": 0.95}

    def make_cell(val, bold=False, bg=None, fg=None, fmt=None, font_size=10, font_family="Inter"):
        cell = {
            "userEnteredValue": {},
            "userEnteredFormat": {
                "textFormat": {
                    "bold": bold,
                    "fontSize": font_size,
                    "fontFamily": font_family,
                },
                "verticalAlignment": "MIDDLE",
                "wrapStrategy": "WRAP",
            }
        }
        if isinstance(val, (int, float)):
            cell["userEnteredValue"]["numberValue"] = val
            if fmt == "currency":
                cell["userEnteredFormat"]["numberFormat"] = {
                    "type": "CURRENCY",
                    "pattern": "$#,##0.00"
                }
        else:
            cell["userEnteredValue"]["stringValue"] = str(val)

        if bg:
            cell["userEnteredFormat"]["backgroundColor"] = bg
        if fg:
            cell["userEnteredFormat"]["textFormat"]["foregroundColor"] = fg

        return cell

    rows_data = []

    # Title row
    rows_data.append({
        "values": [
            make_cell("SOFTWARE & SUBSCRIPTION AUDIT", bold=True, font_size=16, bg=HEADER_BG, fg=HEADER_FG),
            make_cell("", bg=HEADER_BG),
            make_cell("", bg=HEADER_BG),
            make_cell("", bg=HEADER_BG),
            make_cell("", bg=HEADER_BG),
            make_cell("", bg=HEADER_BG),
        ]
    })

    # Subtitle
    rows_data.append({
        "values": [
            make_cell(f"Generated March 2026 | Based on 2025-2026 transaction data", font_size=9, bg={"red": 0.95, "green": 0.95, "blue": 0.95}),
            make_cell("", bg={"red": 0.95, "green": 0.95, "blue": 0.95}),
            make_cell("", bg={"red": 0.95, "green": 0.95, "blue": 0.95}),
            make_cell("", bg={"red": 0.95, "green": 0.95, "blue": 0.95}),
            make_cell("", bg={"red": 0.95, "green": 0.95, "blue": 0.95}),
            make_cell("", bg={"red": 0.95, "green": 0.95, "blue": 0.95}),
        ]
    })

    # Blank row
    rows_data.append({"values": [make_cell("")]})

    # Headers
    headers = ["Tool", "Monthly Cost", "Annual Cost", "Category", "Assessment", "Notes"]
    rows_data.append({
        "values": [make_cell(h, bold=True, bg=HEADER_BG, fg=HEADER_FG, font_size=10) for h in headers]
    })

    # Data rows
    # Sort: Essential first, then Nice-to-Have, then Cut, by annual cost desc within each
    def sort_key(r):
        if "ESSENTIAL" in r["essential"]:
            return (0, -r["annual"])
        elif "NICE" in r["essential"]:
            return (1, -r["annual"])
        elif "CUT" in r["essential"]:
            return (2, -r["annual"])
        else:
            return (3, -r["annual"])

    sorted_report = sorted(report_data, key=sort_key)

    essential_total = 0
    nice_total = 0
    cut_total = 0
    review_total = 0

    for i, r in enumerate(sorted_report):
        if "ESSENTIAL" in r["essential"]:
            row_bg = ESSENTIAL_BG if i % 2 == 0 else {"red": 0.9, "green": 0.97, "blue": 0.9}
            essential_total += r["annual"]
        elif "NICE" in r["essential"]:
            row_bg = NICE_BG if i % 2 == 0 else {"red": 1, "green": 0.93, "blue": 0.77}
            nice_total += r["annual"]
        elif "CUT" in r["essential"]:
            row_bg = CUT_BG if i % 2 == 0 else {"red": 1, "green": 0.82, "blue": 0.82}
            cut_total += r["annual"]
        else:
            row_bg = REVIEW_BG if i % 2 == 0 else ZEBRA_WHITE
            review_total += r["annual"]

        # Build notes
        notes_parts = []
        notes_parts.append(f"{r['n_charges']} charges tracked")
        if r["actual_spent"] != r["annual"]:
            notes_parts.append(f"${r['actual_spent']:,.2f} actual spend")

        assessment_label = r["essential"].split("—")[0].strip() if "—" in r["essential"] else r["essential"]

        rows_data.append({
            "values": [
                make_cell(r["name"], bg=row_bg),
                make_cell(r["monthly"], fmt="currency", bg=row_bg),
                make_cell(r["annual"], fmt="currency", bg=row_bg),
                make_cell(r["category"], bg=row_bg),
                make_cell(assessment_label, bold=True, bg=row_bg),
                make_cell("; ".join(notes_parts), font_size=9, bg=row_bg),
            ]
        })

    # Blank row
    rows_data.append({"values": [make_cell("")]})

    # Summary section
    rows_data.append({
        "values": [
            make_cell("SUMMARY", bold=True, font_size=12, bg=HEADER_BG, fg=HEADER_FG),
            make_cell("", bg=HEADER_BG),
            make_cell("", bg=HEADER_BG),
            make_cell("", bg=HEADER_BG),
            make_cell("", bg=HEADER_BG),
            make_cell("", bg=HEADER_BG),
        ]
    })

    summary_rows = [
        ("Essential Tools (keep)", essential_total),
        ("Nice-to-Have (review)", nice_total),
        ("Consider Cutting", cut_total),
        ("Needs Review", review_total),
        ("", 0),
        ("TOTAL ESTIMATED ANNUAL", essential_total + nice_total + cut_total + review_total),
        ("POTENTIAL SAVINGS (Cut + 50% Nice-to-Have)", cut_total + (nice_total * 0.5)),
    ]

    for label, val in summary_rows:
        if not label:
            rows_data.append({"values": [make_cell("")]})
            continue
        is_total = "TOTAL" in label or "SAVINGS" in label
        bg = HEADER_BG if is_total else ZEBRA_LIGHT
        fg = HEADER_FG if is_total else None
        rows_data.append({
            "values": [
                make_cell(label, bold=is_total, bg=bg, fg=fg),
                make_cell("", bg=bg),
                make_cell(val, fmt="currency", bold=is_total, bg=bg, fg=fg),
                make_cell("", bg=bg),
                make_cell("", bg=bg),
                make_cell("", bg=bg),
            ]
        })

    # Blank row
    rows_data.append({"values": [make_cell("")]})

    # Overlaps section
    if overlaps:
        rows_data.append({
            "values": [
                make_cell("REDUNDANCY FLAGS", bold=True, font_size=12, bg={"red": 0.85, "green": 0.33, "blue": 0.31}, fg=HEADER_FG),
                make_cell("", bg={"red": 0.85, "green": 0.33, "blue": 0.31}),
                make_cell("", bg={"red": 0.85, "green": 0.33, "blue": 0.31}),
                make_cell("", bg={"red": 0.85, "green": 0.33, "blue": 0.31}),
                make_cell("", bg={"red": 0.85, "green": 0.33, "blue": 0.31}),
                make_cell("", bg={"red": 0.85, "green": 0.33, "blue": 0.31}),
            ]
        })
        for o in overlaps:
            rows_data.append({
                "values": [
                    make_cell(o, font_size=9),
                    make_cell(""),
                    make_cell(""),
                    make_cell(""),
                    make_cell(""),
                    make_cell(""),
                ]
            })

    # Write all data
    format_requests = [{
        "updateCells": {
            "rows": rows_data,
            "range": {
                "sheetId": new_tab_id,
                "startRowIndex": 0,
                "startColumnIndex": 0,
            },
            "fields": "userEnteredValue,userEnteredFormat"
        }
    }]

    # Column widths
    col_widths = [220, 110, 110, 180, 150, 280]
    for i, w in enumerate(col_widths):
        format_requests.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": new_tab_id,
                    "dimension": "COLUMNS",
                    "startIndex": i,
                    "endIndex": i + 1,
                },
                "properties": {"pixelSize": w},
                "fields": "pixelSize"
            }
        })

    # Merge title row
    format_requests.append({
        "mergeCells": {
            "range": {
                "sheetId": new_tab_id,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "mergeType": "MERGE_ALL"
        }
    })

    # Merge subtitle row
    format_requests.append({
        "mergeCells": {
            "range": {
                "sheetId": new_tab_id,
                "startRowIndex": 1,
                "endRowIndex": 2,
                "startColumnIndex": 0,
                "endColumnIndex": 6,
            },
            "mergeType": "MERGE_ALL"
        }
    })

    # Freeze header rows
    format_requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": new_tab_id,
                "gridProperties": {"frozenRowCount": 4}
            },
            "fields": "gridProperties.frozenRowCount"
        }
    })

    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": format_requests}
    ).execute()

    print(f"  Software Audit tab written with {len(sorted_report)} tools")


if __name__ == "__main__":
    main()
