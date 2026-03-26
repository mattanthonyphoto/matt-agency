"""Google Sheets data layer — pulls finance and cold email data."""

import sys
import os
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.google_sheets_auth import get_sheets_service
from tools.dashboard.config import (
    FINANCE_2026_SHEET_ID, FINANCE_2025_SHEET_ID,
    COLD_EMAIL_INPUT_ID, COLD_EMAIL_OUTPUT_ID,
    FINANCE_RANGES_2026, FINANCE_RANGES_2025, MONTH_NAMES,
)

_sheets_service = None


def _get_service():
    global _sheets_service
    if _sheets_service is None:
        _sheets_service = get_sheets_service()
    return _sheets_service


def _safe_float(val):
    """Convert a cell value to float, returning 0.0 on failure."""
    if val is None or val == "" or val is False or val is True:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        # Strip currency symbols and commas
        try:
            return float(str(val).replace("$", "").replace(",", "").strip())
        except (ValueError, TypeError):
            return 0.0


def _safe_str(val):
    if val is None:
        return ""
    return str(val).strip()


def _batch_get(sheet_id, ranges_dict):
    """Fetch multiple ranges in one API call. Returns dict of label -> rows."""
    svc = _get_service()
    ranges = list(ranges_dict.values())
    labels = list(ranges_dict.keys())
    try:
        result = svc.spreadsheets().values().batchGet(
            spreadsheetId=sheet_id,
            ranges=ranges,
            valueRenderOption="UNFORMATTED_VALUE",
        ).execute()
        value_ranges = result.get("valueRanges", [])
        out = {}
        for i, label in enumerate(labels):
            if i < len(value_ranges):
                out[label] = value_ranges[i].get("values", [])
            else:
                out[label] = []
        return out
    except Exception as e:
        return {"error": str(e)}


def _parse_transactions(rows):
    """Parse transaction rows into income and expense lists.

    Transactions tab layout:
      Row 1-3: headers/labels
      Row 4-5: section header for income
      Row 6-141: income data
      Row 142-145: section header for expenses
      Row 146+: expense data

    Columns (0-indexed):
      A(0)=Date, B(1)=Vendor, C(2)=Description,
      D(3)=Amount, E(4)=Business flag, F(5)=Category,
      G(6)=Split multiplier, H(7)=GST, I(8)=Receipt,
      J(9)=Payment type, K(10)=Account, L(11)=Notes,
      M(12)=empty, N(13)=Month number
    """
    income = []
    expenses = []
    for i, row in enumerate(rows):
        if i < 5:  # skip headers (rows 1-5)
            continue
        if len(row) < 4:
            continue
        amount = _safe_float(row[3] if len(row) > 3 else 0)
        if amount == 0:
            continue
        entry = {
            "date": _safe_str(row[0] if len(row) > 0 else ""),
            "vendor": _safe_str(row[1] if len(row) > 1 else ""),
            "description": _safe_str(row[2] if len(row) > 2 else ""),
            "amount": amount,
            "is_business": bool(row[4]) if len(row) > 4 else False,
            "category": _safe_str(row[5] if len(row) > 5 else ""),
            "split_pct": _safe_float(row[6] if len(row) > 6 else 0),
            "gst": _safe_float(row[7] if len(row) > 7 else 0),
            "month": int(_safe_float(row[13] if len(row) > 13 else 0)),
        }
        if amount > 0:
            income.append(entry)
        else:
            expenses.append(entry)
    return income, expenses


def fetch_finance_2026():
    """Fetch 2026 finance data. Returns structured dict."""
    data = _batch_get(FINANCE_2026_SHEET_ID, FINANCE_RANGES_2026)
    if "error" in data:
        return {"error": data["error"]}

    # Parse transactions
    income, expenses = _parse_transactions(data.get("transactions", []))

    # Monthly revenue and expenses
    monthly = defaultdict(lambda: {"revenue": 0, "expenses": 0})
    for tx in income:
        if tx["is_business"] and tx["month"] > 0:
            monthly[tx["month"]]["revenue"] += tx["amount"]
    for tx in expenses:
        if tx["is_business"] and tx["month"] > 0:
            monthly[tx["month"]]["expenses"] += abs(tx["amount"])

    monthly_data = []
    for m in range(1, 13):
        monthly_data.append({
            "month": MONTH_NAMES[m - 1],
            "month_num": m,
            "revenue": round(monthly[m]["revenue"], 2),
            "expenses": round(monthly[m]["expenses"], 2),
            "net": round(monthly[m]["revenue"] - monthly[m]["expenses"], 2),
        })

    ytd_revenue = sum(m["revenue"] for m in monthly_data)
    ytd_expenses = sum(m["expenses"] for m in monthly_data)
    net_profit = ytd_revenue - ytd_expenses
    profit_margin = (net_profit / ytd_revenue * 100) if ytd_revenue > 0 else 0

    # Client breakdown (business income grouped by vendor)
    client_revenue = defaultdict(float)
    for tx in income:
        if tx["is_business"]:
            client_revenue[tx["vendor"]] += tx["amount"]
    top_clients = sorted(client_revenue.items(), key=lambda x: x[1], reverse=True)

    # Expense breakdown by category
    expense_categories = defaultdict(float)
    for tx in expenses:
        if tx["is_business"]:
            cat = tx["category"] or "Uncategorized"
            expense_categories[cat] += abs(tx["amount"])
    expense_breakdown = sorted(expense_categories.items(), key=lambda x: x[1], reverse=True)

    # Recurring vs project revenue
    recurring_keywords = ["retainer", "hosting", "seo", "web maintenance", "monthly"]
    recurring_revenue = 0
    project_revenue = 0
    for tx in income:
        if tx["is_business"]:
            search_text = (tx["vendor"] + " " + tx["description"] + " " + tx.get("category", "")).lower()
            if any(kw in search_text for kw in recurring_keywords):
                recurring_revenue += tx["amount"]
            else:
                project_revenue += tx["amount"]

    # Mileage
    mileage_rows = data.get("mileage", [])
    total_km = 0
    trip_count = 0
    for row in mileage_rows[3:]:  # skip headers
        if len(row) >= 5:
            km = _safe_float(row[4] if len(row) > 4 else 0)
            if km > 0:
                total_km += km
                trip_count += 1

    # GST
    gst_rows = data.get("gst", [])
    gst_collected = 0
    gst_itcs = 0
    if len(gst_rows) > 6:
        # Row 6 = GST collected, Row 7 = ITCs (0-indexed: 5, 6)
        for cell in gst_rows[5][2:7] if len(gst_rows) > 5 else []:
            gst_collected += _safe_float(cell)
        for cell in gst_rows[6][2:7] if len(gst_rows) > 6 else []:
            gst_itcs += _safe_float(cell)
    gst_owing = gst_collected + gst_itcs  # ITCs are negative

    # Equipment / CCA
    equipment_rows = data.get("equipment", [])
    total_cca = 0
    for row in equipment_rows:
        if len(row) >= 7 and "total" in _safe_str(row[0]).lower():
            total_cca = _safe_float(row[6])
            break

    return {
        "ytd_revenue": round(ytd_revenue, 2),
        "ytd_expenses": round(ytd_expenses, 2),
        "net_profit": round(net_profit, 2),
        "profit_margin": round(profit_margin, 1),
        "monthly": monthly_data,
        "top_clients": [{"name": n, "revenue": round(v, 2)} for n, v in top_clients[:15]],
        "expense_breakdown": [{"category": c, "amount": round(v, 2)} for c, v in expense_breakdown[:15]],
        "recurring_revenue": round(recurring_revenue, 2),
        "project_revenue": round(project_revenue, 2),
        "mileage_km": round(total_km, 1),
        "mileage_trips": trip_count,
        "gst_collected": round(gst_collected, 2),
        "gst_itcs": round(gst_itcs, 2),
        "gst_owing": round(gst_owing, 2),
        "total_cca": round(total_cca, 2),
    }


def fetch_finance_2025():
    """Fetch 2025 finance data for YoY comparison."""
    data = _batch_get(FINANCE_2025_SHEET_ID, FINANCE_RANGES_2025)
    if "error" in data:
        return {"error": data["error"]}

    income, expenses = _parse_transactions(data.get("transactions", []))

    monthly = defaultdict(lambda: {"revenue": 0, "expenses": 0})
    for tx in income:
        if tx["is_business"] and tx["month"] > 0:
            monthly[tx["month"]]["revenue"] += tx["amount"]
    for tx in expenses:
        if tx["is_business"] and tx["month"] > 0:
            monthly[tx["month"]]["expenses"] += abs(tx["amount"])

    monthly_data = []
    for m in range(1, 13):
        monthly_data.append({
            "month": MONTH_NAMES[m - 1],
            "month_num": m,
            "revenue": round(monthly[m]["revenue"], 2),
            "expenses": round(monthly[m]["expenses"], 2),
        })

    ytd_revenue = sum(m["revenue"] for m in monthly_data)

    return {
        "total_revenue": round(ytd_revenue, 2),
        "monthly": monthly_data,
    }


def fetch_cold_email_stats():
    """Fetch cold email pipeline statistics."""
    svc = _get_service()
    try:
        # Input sheet — count rows per tab
        input_tabs = ["Builders", "Architects", "Interior Designers", "Trades"]
        input_ranges = [f"'{tab}'!A:A" for tab in input_tabs]

        result = svc.spreadsheets().values().batchGet(
            spreadsheetId=COLD_EMAIL_INPUT_ID,
            ranges=input_ranges,
            valueRenderOption="UNFORMATTED_VALUE",
        ).execute()

        by_category = {}
        total_leads = 0
        for i, tab in enumerate(input_tabs):
            vr = result.get("valueRanges", [])
            rows = vr[i].get("values", []) if i < len(vr) else []
            count = max(0, len(rows) - 1)  # subtract header
            by_category[tab] = count
            total_leads += count

        # Output sheet — count qualified leads across all tabs
        output_tabs = ["Builders", "Architects", "Interior Designers", "Trades"]
        output_ranges = [f"'{tab}'!A:Z" for tab in output_tabs]
        output_result = svc.spreadsheets().values().batchGet(
            spreadsheetId=COLD_EMAIL_OUTPUT_ID,
            ranges=output_ranges,
            valueRenderOption="UNFORMATTED_VALUE",
        ).execute()
        output_rows = []
        for vr in output_result.get("valueRanges", []):
            rows = vr.get("values", [])
            if rows:
                output_rows.extend(rows[1:])  # skip header per tab
        qualified = len(output_rows)

        # Count how many have email addresses (check column for email)
        emails_found = 0
        for row in output_rows:
            for cell in row:
                if isinstance(cell, str) and "@" in cell:
                    emails_found += 1
                    break

        return {
            "total_leads": total_leads,
            "qualified": qualified,
            "emails_found": emails_found,
            "by_category": by_category,
        }
    except Exception as e:
        return {"error": str(e), "total_leads": 0, "qualified": 0, "emails_found": 0, "by_category": {}}


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    print("Fetching 2026 finance data...")
    data = fetch_finance_2026()
    if "error" in data:
        print(f"Error: {data['error']}")
    else:
        print(f"YTD Revenue: ${data['ytd_revenue']:,.2f}")
        print(f"YTD Expenses: ${data['ytd_expenses']:,.2f}")
        print(f"Net Profit: ${data['net_profit']:,.2f}")
        print(f"Margin: {data['profit_margin']}%")
        print(f"Top clients: {len(data['top_clients'])}")

    print("\nFetching cold email stats...")
    ce = fetch_cold_email_stats()
    print(f"Total leads: {ce['total_leads']}, Qualified: {ce['qualified']}")
