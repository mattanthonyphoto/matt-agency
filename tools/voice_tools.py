"""Voice agent tool definitions and executors.

Defines 21 tools for Claude API tool_use and dispatches execution
to existing agent_utils functions, Google APIs, and subprocess calls.
"""

import os
import sys
import json
import subprocess
import base64
from pathlib import Path
from email.mime.text import MIMEText

# Add parent dir so we can import sibling modules
sys.path.insert(0, os.path.dirname(__file__))

from agent_utils import (
    send_telegram,
    get_ghl_contacts,
    get_ghl_opportunities,
    get_ghl_invoices,
    get_instantly_campaigns,
    get_instantly_replies,
    search_gmail,
    get_gmail_service,
    get_today_events,
    get_week_events,
)
from google_sheets_auth import get_sheets_service

PROJECT_ROOT = Path(__file__).parent.parent

# ─── Tool Definitions (Claude API tool_use schema) ────────────────────────

TOOLS = [
    # --- Calendar ---
    {
        "name": "get_today_schedule",
        "description": "Get today's calendar events. Returns event names, times, and locations.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_week_schedule",
        "description": "Get calendar events for the next 7 days.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    # --- Email ---
    {
        "name": "search_email",
        "description": "Search Gmail inbox. Use Gmail search syntax (e.g. 'from:marc', 'subject:invoice', 'newer_than:3d').",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Gmail search query",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Max emails to return (default 10)",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "draft_email",
        "description": "Create a Gmail draft (does NOT send). Matt will review and send manually.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject line"},
                "body": {"type": "string", "description": "Email body text"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    # --- CRM / Pipeline ---
    {
        "name": "get_pipeline",
        "description": "Get all open deals from GHL CRM. Returns deal names, values, stages, and contact info.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_contacts",
        "description": "Get contacts from GHL CRM.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max contacts to return (default 50)",
                    "default": 50,
                },
            },
            "required": [],
        },
    },
    {
        "name": "search_contacts",
        "description": "Search CRM contacts by name, company, or email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term (name, company, or email)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_invoices",
        "description": "Get all invoices from GHL with statuses and amounts.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    # --- Revenue / Finance ---
    {
        "name": "get_revenue_summary",
        "description": "Get revenue summary: YTD revenue, monthly breakdown, outstanding invoices.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    # --- Campaigns ---
    {
        "name": "get_campaigns",
        "description": "Get cold email campaigns from Instantly with statuses and stats.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_cold_email_replies",
        "description": "Get recent replies to cold email campaigns.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    # --- Agent Runs ---
    {
        "name": "run_morning_briefing",
        "description": "Run the Morning Command agent. Produces a full daily briefing (calendar, email, pipeline, campaigns). Also sends to Telegram.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "run_operator",
        "description": "Run The Operator agent. Modes: dm (Instagram DM prep), followup (draft follow-up emails), content (today's social content), leads (process raw leads), reviews (Google review requests).",
        "input_schema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["dm", "followup", "content", "leads", "reviews"],
                    "description": "Operator mode to run",
                },
            },
            "required": ["mode"],
        },
    },
    {
        "name": "run_accountant",
        "description": "Run The Accountant agent. Modes: invoices (chase overdue), expenses (track spending), tax (tax reminders).",
        "input_schema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["invoices", "expenses", "tax"],
                    "description": "Accountant mode to run",
                },
            },
            "required": ["mode"],
        },
    },
    {
        "name": "run_watchdog",
        "description": "Run The Watchdog agent. Modes: health (system health checks), gbp (Google Business Profile), domains (domain monitoring), retainer (retainer tracking).",
        "input_schema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["health", "gbp", "domains", "retainer"],
                    "description": "Watchdog mode to run",
                },
            },
            "required": ["mode"],
        },
    },
    {
        "name": "run_producer",
        "description": "Run The Producer agent. Modes: prep (shoot prep checklists), handoff (editor handoff), delivery (client delivery), costshare (cost-share opportunities).",
        "input_schema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["prep", "handoff", "delivery", "costshare"],
                    "description": "Producer mode to run",
                },
            },
            "required": ["mode"],
        },
    },
    {
        "name": "run_strategist",
        "description": "Run The Strategist agent. Modes: campaigns (campaign performance), winloss (win/loss analysis), competitors (competitor tracking), attribution (lead attribution).",
        "input_schema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["campaigns", "winloss", "competitors", "attribution"],
                    "description": "Strategist mode to run",
                },
            },
            "required": ["mode"],
        },
    },
    # --- Communication ---
    {
        "name": "send_telegram_message",
        "description": "Send a message to Matt's Telegram. Use for 'text me that', 'send me a summary', etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message text (HTML formatting supported: <b>, <i>, <code>)",
                },
            },
            "required": ["message"],
        },
    },
    # --- Utility ---
    {
        "name": "run_shell_command",
        "description": "Run a shell command on the local machine. For system tasks like disk space, listing files, git status, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute",
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a local file. For checking business docs, workflows, configs, markdown files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path (relative to project root or absolute)",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "get_business_context",
        "description": "Get a snapshot of the business: who Matt is, key clients, revenue targets, current priorities. Use for strategic or contextual questions.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ─── Tool Executors ───────────────────────────────────────────────────────

def _run_agent(script, mode=None):
    """Run a Python agent script via subprocess."""
    cmd = ["python3", str(PROJECT_ROOT / "tools" / script)]
    if mode:
        cmd.append(mode)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(PROJECT_ROOT),
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr[-500:]}"
        return output[:4000] if output else "Agent completed (no output captured)."
    except subprocess.TimeoutExpired:
        return "Agent timed out after 120 seconds."
    except Exception as e:
        return f"Error running agent: {e}"


def _exec_get_today_schedule(_params):
    events = get_today_events()
    if not events:
        return json.dumps({"events": [], "summary": "No events today."})
    formatted = []
    for e in events:
        start = e.get("start", {}).get("dateTime", e.get("start", {}).get("date", ""))
        formatted.append({
            "summary": e.get("summary", "Untitled"),
            "start": start,
            "location": e.get("location", ""),
            "description": (e.get("description", "") or "")[:200],
        })
    return json.dumps({"events": formatted, "count": len(formatted)})


def _exec_get_week_schedule(_params):
    events = get_week_events()
    if not events:
        return json.dumps({"events": [], "summary": "No events this week."})
    formatted = []
    for e in events:
        start = e.get("start", {}).get("dateTime", e.get("start", {}).get("date", ""))
        formatted.append({
            "summary": e.get("summary", "Untitled"),
            "start": start,
            "location": e.get("location", ""),
        })
    return json.dumps({"events": formatted, "count": len(formatted)})


def _exec_search_email(params):
    query = params.get("query", "")
    max_results = params.get("max_results", 10)
    messages = search_gmail(query, max_results)
    return json.dumps({"messages": messages, "count": len(messages)})


def _exec_draft_email(params):
    svc = get_gmail_service()
    message = MIMEText(params["body"])
    message["to"] = params["to"]
    message["subject"] = params["subject"]
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    draft = svc.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw}},
    ).execute()
    return json.dumps({
        "status": "Draft created",
        "draft_id": draft.get("id", ""),
        "to": params["to"],
        "subject": params["subject"],
    })


def _exec_get_pipeline(_params):
    data = get_ghl_opportunities()
    opportunities = data.get("opportunities", [])
    formatted = []
    for opp in opportunities[:20]:
        formatted.append({
            "name": opp.get("name", ""),
            "value": opp.get("monetaryValue", 0),
            "stage": opp.get("pipelineStageId", ""),
            "status": opp.get("status", ""),
            "contact": opp.get("contact", {}).get("name", ""),
            "email": opp.get("contact", {}).get("email", ""),
        })
    return json.dumps({"opportunities": formatted, "count": len(formatted)})


def _exec_get_contacts(params):
    limit = params.get("limit", 50)
    data = get_ghl_contacts(limit)
    contacts = data.get("contacts", [])
    formatted = []
    for c in contacts[:limit]:
        formatted.append({
            "name": f"{c.get('firstName', '')} {c.get('lastName', '')}".strip(),
            "email": c.get("email", ""),
            "phone": c.get("phone", ""),
            "company": c.get("companyName", ""),
        })
    return json.dumps({"contacts": formatted, "count": len(formatted)})


def _exec_search_contacts(params):
    query = params.get("query", "").lower()
    data = get_ghl_contacts(200)
    contacts = data.get("contacts", [])
    matches = []
    for c in contacts:
        name = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip()
        company = c.get("companyName", "")
        email = c.get("email", "")
        if query in name.lower() or query in company.lower() or query in email.lower():
            matches.append({
                "name": name,
                "email": email,
                "phone": c.get("phone", ""),
                "company": company,
            })
    return json.dumps({"matches": matches, "count": len(matches)})


def _exec_get_invoices(_params):
    data = get_ghl_invoices()
    invoices = data.get("invoices", [])
    formatted = []
    for inv in invoices[:30]:
        formatted.append({
            "name": inv.get("name", ""),
            "amount": inv.get("total", 0),
            "status": inv.get("status", ""),
            "due_date": inv.get("dueDate", ""),
            "contact": inv.get("contactName", ""),
        })
    return json.dumps({"invoices": formatted, "count": len(formatted)})


def _exec_get_revenue_summary(_params):
    # Get invoices for revenue calc
    data = get_ghl_invoices()
    invoices = data.get("invoices", [])

    total_paid = 0
    total_outstanding = 0
    for inv in invoices:
        amount = inv.get("total", 0) or 0
        if isinstance(amount, str):
            try:
                amount = float(amount)
            except ValueError:
                amount = 0
        status = inv.get("status", "").lower()
        if status == "paid":
            total_paid += amount
        elif status in ("sent", "viewed", "overdue"):
            total_outstanding += amount

    # Try to read finance sheet for more detail
    sheet_summary = ""
    try:
        sheet_id = os.getenv("FINANCE_SHEET_2026_ID")
        if sheet_id:
            sheets = get_sheets_service()
            result = sheets.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range="'Dashboard'!A1:F20",
            ).execute()
            rows = result.get("values", [])
            sheet_summary = json.dumps(rows[:10])
    except Exception:
        sheet_summary = "Finance sheet unavailable."

    return json.dumps({
        "total_paid": total_paid,
        "total_outstanding": total_outstanding,
        "invoice_count": len(invoices),
        "finance_sheet": sheet_summary,
    })


def _exec_get_campaigns(_params):
    data = get_instantly_campaigns()
    campaigns = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(campaigns, list):
        formatted = []
        for c in campaigns[:15]:
            formatted.append({
                "name": c.get("name", ""),
                "status": c.get("status", ""),
                "id": c.get("id", ""),
            })
        return json.dumps({"campaigns": formatted, "count": len(formatted)})
    return json.dumps({"raw": str(data)[:2000]})


def _exec_get_cold_email_replies(_params):
    data = get_instantly_replies()
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        formatted = []
        for r in items[:20]:
            formatted.append({
                "from": r.get("from_address_email", r.get("from", "")),
                "subject": r.get("subject", ""),
                "snippet": (r.get("body", {}).get("text", "") or "")[:300],
                "date": r.get("timestamp", ""),
            })
        return json.dumps({"replies": formatted, "count": len(formatted)})
    return json.dumps({"raw": str(data)[:2000]})


def _exec_run_morning_briefing(_params):
    return _run_agent("morning_command.py")


def _exec_run_operator(params):
    return _run_agent("the_operator.py", params.get("mode"))


def _exec_run_accountant(params):
    return _run_agent("the_accountant.py", params.get("mode"))


def _exec_run_watchdog(params):
    return _run_agent("the_watchdog.py", params.get("mode"))


def _exec_run_producer(params):
    return _run_agent("the_producer.py", params.get("mode"))


def _exec_run_strategist(params):
    return _run_agent("the_strategist.py", params.get("mode"))


def _exec_send_telegram(params):
    send_telegram(params.get("message", ""))
    return json.dumps({"status": "Message sent to Telegram."})


def _exec_run_shell(params):
    command = params.get("command", "")
    # Block dangerous commands
    dangerous = ["rm -rf", "mkfs", "dd if=", "> /dev/", "shutdown", "reboot"]
    if any(d in command for d in dangerous):
        return json.dumps({"error": "Blocked: potentially destructive command."})
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        output = result.stdout[:3000]
        if result.stderr:
            output += f"\n[stderr]: {result.stderr[:500]}"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def _exec_read_file(params):
    path = params.get("path", "")
    # Resolve relative paths against project root
    if not os.path.isabs(path):
        path = str(PROJECT_ROOT / path)
    try:
        with open(path, "r") as f:
            content = f.read(5000)
        if len(content) == 5000:
            content += "\n... (truncated at 5000 chars)"
        return content
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Error reading file: {e}"


def _exec_get_business_context(_params):
    return json.dumps({
        "business": "Matt Anthony Photography",
        "owner": "Matt Anthony (Matthew Fernandes)",
        "location": "Squamish, BC, Canada",
        "specialty": "Architectural and interior photography for custom home builders, architects, and designers",
        "key_clients": [
            "Balmoral Construction (Marc Harvey) - top client, Creative Partner retainer prospect",
            "Summerhill Fine Homes - active project work",
            "Hanson Land & Sea - newer client",
        ],
        "revenue_2025": "$105,237 across 89 invoices",
        "target_2026": "$150,000+",
        "pricing": "Day rate model, cost-share (90% success rate)",
        "sales_channels": [
            "Cold email via Instantly (builders, architects, designers)",
            "Instagram DM outreach",
            "Georgie Awards networking",
            "Architect referral flywheel",
        ],
        "key_systems": [
            "GHL CRM for pipeline and contacts",
            "Instantly for cold email campaigns",
            "Google Sheets for finance and data",
            "n8n for automation workflows",
            "Telegram bot for agent briefings",
            "8 automated agents running on cron",
        ],
        "current_priorities": [
            "Close retainer deals (Creative Partner model)",
            "Architect referral flywheel activation",
            "Georgie Awards 2026 networking",
            "Hit $150K revenue target",
        ],
    })


# ─── Dispatcher ───────────────────────────────────────────────────────────

EXECUTORS = {
    "get_today_schedule": _exec_get_today_schedule,
    "get_week_schedule": _exec_get_week_schedule,
    "search_email": _exec_search_email,
    "draft_email": _exec_draft_email,
    "get_pipeline": _exec_get_pipeline,
    "get_contacts": _exec_get_contacts,
    "search_contacts": _exec_search_contacts,
    "get_invoices": _exec_get_invoices,
    "get_revenue_summary": _exec_get_revenue_summary,
    "get_campaigns": _exec_get_campaigns,
    "get_cold_email_replies": _exec_get_cold_email_replies,
    "run_morning_briefing": _exec_run_morning_briefing,
    "run_operator": _exec_run_operator,
    "run_accountant": _exec_run_accountant,
    "run_watchdog": _exec_run_watchdog,
    "run_producer": _exec_run_producer,
    "run_strategist": _exec_run_strategist,
    "send_telegram_message": _exec_send_telegram,
    "run_shell_command": _exec_run_shell,
    "read_file": _exec_read_file,
    "get_business_context": _exec_get_business_context,
}


def execute_tool(name, params):
    """Execute a tool by name. Returns a string result."""
    executor = EXECUTORS.get(name)
    if not executor:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = executor(params)
        return result if isinstance(result, str) else json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"{name} failed: {e}"})
