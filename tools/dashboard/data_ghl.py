"""GoHighLevel data layer — pulls invoices, contacts, and opportunities."""

import os
from collections import defaultdict
from datetime import datetime

import requests

from tools.dashboard.config import GHL_BASE_URL, GHL_API_VERSION, GHL_PAGE_SIZE


def _headers():
    api_key = os.getenv("GHL_API_KEY")
    if not api_key:
        return None
    return {
        "Authorization": f"Bearer {api_key}",
        "Version": GHL_API_VERSION,
        "Accept": "application/json",
    }


def _location_id():
    return os.getenv("GHL_LOCATION_ID", "")


def _extract_amount(invoice):
    amount = invoice.get("total", invoice.get("amount", invoice.get("amountDue", 0)))
    return float(amount) if amount else 0.0


def _extract_date(invoice):
    date_str = invoice.get("issueDate", invoice.get("createdAt", invoice.get("dueDate", "")))
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return str(date_str)[:10]


def _extract_client_name(invoice):
    contact = invoice.get("contactDetails", invoice.get("contact", {}))
    if isinstance(contact, dict):
        name = contact.get("name", "")
        if not name:
            first = contact.get("firstName", "")
            last = contact.get("lastName", "")
            name = f"{first} {last}".strip()
        return name or "Unknown"
    return "Unknown"


def fetch_invoices():
    """Fetch all invoices from GHL. Returns structured summary."""
    hdrs = _headers()
    if not hdrs:
        return {"error": "GHL_API_KEY not set", "invoices": [], "total_count": 0}

    loc = _location_id()
    all_invoices = []
    offset = 0

    while True:
        try:
            resp = requests.get(
                f"{GHL_BASE_URL}/invoices/",
                headers=hdrs,
                params={
                    "altType": "location",
                    "altId": loc,
                    "limit": GHL_PAGE_SIZE,
                    "offset": offset,
                    "status": "all",
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            invoices = data.get("invoices", data.get("data", []))
            if not invoices:
                break
            all_invoices.extend(invoices)
            offset += GHL_PAGE_SIZE
            if len(invoices) < GHL_PAGE_SIZE:
                break
        except Exception as e:
            if all_invoices:
                break  # return what we have
            return {"error": str(e), "invoices": [], "total_count": 0}

    # Process invoices
    total_revenue = 0
    outstanding_total = 0
    outstanding = []
    by_status = defaultdict(lambda: {"count": 0, "amount": 0})
    by_client = defaultdict(float)
    recent = []

    for inv in all_invoices:
        amount = _extract_amount(inv)
        status = inv.get("status", "unknown").lower()
        client = _extract_client_name(inv)
        date = _extract_date(inv)
        inv_num = inv.get("invoiceNumber", inv.get("number", ""))

        by_status[status]["count"] += 1
        by_status[status]["amount"] += amount
        by_client[client] += amount

        if status == "paid":
            total_revenue += amount
        elif status in ("sent", "viewed", "overdue"):
            outstanding_total += amount
            outstanding.append({
                "number": inv_num,
                "client": client,
                "amount": round(amount, 2),
                "date": date,
                "status": status,
            })

        recent.append({
            "number": inv_num,
            "client": client,
            "amount": round(amount, 2),
            "date": date,
            "status": status,
        })

    # Sort recent by date descending
    recent.sort(key=lambda x: x["date"], reverse=True)

    # Sort clients by revenue
    top_clients = sorted(by_client.items(), key=lambda x: x[1], reverse=True)

    return {
        "total_count": len(all_invoices),
        "total_revenue": round(total_revenue, 2),
        "outstanding_total": round(outstanding_total, 2),
        "outstanding": outstanding,
        "by_status": {k: {"count": v["count"], "amount": round(v["amount"], 2)} for k, v in by_status.items()},
        "by_client": [{"name": n, "amount": round(a, 2)} for n, a in top_clients[:15]],
        "recent": recent[:10],
    }


def fetch_contacts():
    """Fetch contact count and recent contacts from GHL."""
    hdrs = _headers()
    if not hdrs:
        return {"error": "GHL_API_KEY not set", "total": 0}

    loc = _location_id()
    try:
        resp = requests.get(
            f"{GHL_BASE_URL}/contacts/",
            headers=hdrs,
            params={"locationId": loc, "limit": 20},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        contacts = data.get("contacts", [])
        total = data.get("meta", {}).get("total", len(contacts))
        return {
            "total": total,
            "recent": [
                {
                    "name": f"{c.get('firstName', '')} {c.get('lastName', '')}".strip(),
                    "email": c.get("email", ""),
                    "date_added": c.get("dateAdded", ""),
                }
                for c in contacts[:5]
            ],
        }
    except Exception as e:
        return {"error": str(e), "total": 0, "recent": []}


def fetch_opportunities():
    """Fetch pipeline opportunities from GHL."""
    hdrs = _headers()
    if not hdrs:
        return {"error": "GHL_API_KEY not set", "stages": {}, "total_value": 0}

    loc = _location_id()

    # First get pipelines
    try:
        resp = requests.get(
            f"{GHL_BASE_URL}/opportunities/pipelines",
            headers=hdrs,
            params={"locationId": loc},
            timeout=15,
        )
        resp.raise_for_status()
        pipelines = resp.json().get("pipelines", [])
    except Exception:
        pipelines = []

    if not pipelines:
        return {"stages": {}, "total_value": 0, "count": 0}

    # Fetch opportunities from first pipeline
    pipeline = pipelines[0]
    pipeline_id = pipeline.get("id", "")
    stage_map = {s["id"]: s["name"] for s in pipeline.get("stages", [])}

    try:
        resp = requests.get(
            f"{GHL_BASE_URL}/opportunities/search",
            headers=hdrs,
            params={"location_id": loc, "pipeline_id": pipeline_id},
            timeout=15,
        )
        resp.raise_for_status()
        opps = resp.json().get("opportunities", [])
    except Exception:
        opps = []

    stages = defaultdict(lambda: {"count": 0, "value": 0, "opportunities": []})
    total_value = 0

    for opp in opps:
        stage_id = opp.get("pipelineStageId", "")
        stage_name = stage_map.get(stage_id, "Unknown")
        value = float(opp.get("monetaryValue", 0) or 0)
        name = opp.get("name", opp.get("contactName", "Unknown"))

        stages[stage_name]["count"] += 1
        stages[stage_name]["value"] += value
        stages[stage_name]["opportunities"].append({
            "name": name,
            "value": round(value, 2),
            "status": opp.get("status", ""),
        })
        total_value += value

    return {
        "pipeline_name": pipeline.get("name", "Pipeline"),
        "stages": {k: {"count": v["count"], "value": round(v["value"], 2), "opportunities": v["opportunities"]}
                   for k, v in stages.items()},
        "total_value": round(total_value, 2),
        "count": len(opps),
    }
