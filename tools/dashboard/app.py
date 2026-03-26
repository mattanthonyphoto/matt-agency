"""
Matt Anthony Photography — Business Dashboard
Run: python -m tools.dashboard.app
"""

import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from flask import Flask, render_template, jsonify

from tools.dashboard.config import REVENUE_TARGET_2026, RECURRING_MONTHLY, CAPACITY_PAUSE_THRESHOLD
from tools.dashboard.data_sheets import fetch_finance_2026, fetch_finance_2025, fetch_cold_email_stats
from tools.dashboard.data_ghl import fetch_invoices, fetch_contacts, fetch_opportunities

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates",
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/all")
def api_all():
    """Combined endpoint — all dashboard data in one call."""
    finance_2026 = fetch_finance_2026()
    finance_2025 = fetch_finance_2025()
    cold_email = fetch_cold_email_stats()
    ghl_invoices = fetch_invoices()
    ghl_pipeline = fetch_opportunities()
    ghl_contacts = fetch_contacts()

    # Build revenue section
    ytd_revenue = finance_2026.get("ytd_revenue", 0)
    day_of_year = (datetime.now() - datetime(2026, 1, 1)).days
    pace_target = (REVENUE_TARGET_2026 * day_of_year) / 365 if day_of_year > 0 else 0

    revenue = {
        "ytd": ytd_revenue,
        "target": REVENUE_TARGET_2026,
        "pace_target": round(pace_target, 2),
        "on_track": ytd_revenue >= pace_target,
        "monthly": finance_2026.get("monthly", []),
        "monthly_2025": finance_2025.get("monthly", []),
        "total_2025": finance_2025.get("total_revenue", 0),
        "recurring": finance_2026.get("recurring_revenue", 0),
        "project": finance_2026.get("project_revenue", 0),
        "recurring_monthly_base": RECURRING_MONTHLY,
    }

    # Build pipeline section
    pipeline = {
        "opportunities": ghl_pipeline,
        "cold_email": cold_email,
        "contacts_total": ghl_contacts.get("total", 0),
    }

    # Build clients section
    clients = {
        "top_clients": finance_2026.get("top_clients", []),
        "ghl_clients": ghl_invoices.get("by_client", []),
    }

    # Build financial section
    financial = {
        "ytd_expenses": finance_2026.get("ytd_expenses", 0),
        "net_profit": finance_2026.get("net_profit", 0),
        "profit_margin": finance_2026.get("profit_margin", 0),
        "expense_breakdown": finance_2026.get("expense_breakdown", []),
    }

    # Build quick stats
    stats = {
        "mileage_km": finance_2026.get("mileage_km", 0),
        "mileage_trips": finance_2026.get("mileage_trips", 0),
        "gst_collected": finance_2026.get("gst_collected", 0),
        "gst_itcs": finance_2026.get("gst_itcs", 0),
        "gst_owing": finance_2026.get("gst_owing", 0),
        "total_cca": finance_2026.get("total_cca", 0),
        "outstanding_invoices": ghl_invoices.get("outstanding_total", 0),
        "outstanding_list": ghl_invoices.get("outstanding", []),
        "recent_invoices": ghl_invoices.get("recent", []),
        "capacity_threshold": CAPACITY_PAUSE_THRESHOLD,
    }

    return jsonify({
        "revenue": revenue,
        "pipeline": pipeline,
        "clients": clients,
        "financial": financial,
        "stats": stats,
        "updated_at": datetime.now().isoformat(),
    })


@app.route("/api/revenue")
def api_revenue():
    finance = fetch_finance_2026()
    return jsonify({
        "ytd": finance.get("ytd_revenue", 0),
        "target": REVENUE_TARGET_2026,
        "monthly": finance.get("monthly", []),
        "recurring": finance.get("recurring_revenue", 0),
        "project": finance.get("project_revenue", 0),
    })


@app.route("/api/pipeline")
def api_pipeline():
    return jsonify({
        "opportunities": fetch_opportunities(),
        "cold_email": fetch_cold_email_stats(),
    })


@app.route("/api/clients")
def api_clients():
    finance = fetch_finance_2026()
    invoices = fetch_invoices()
    return jsonify({
        "top_clients": finance.get("top_clients", []),
        "ghl_clients": invoices.get("by_client", []),
    })


@app.route("/api/financial")
def api_financial():
    finance = fetch_finance_2026()
    return jsonify({
        "ytd_expenses": finance.get("ytd_expenses", 0),
        "net_profit": finance.get("net_profit", 0),
        "profit_margin": finance.get("profit_margin", 0),
        "expense_breakdown": finance.get("expense_breakdown", []),
    })


@app.route("/api/stats")
def api_stats():
    finance = fetch_finance_2026()
    invoices = fetch_invoices()
    return jsonify({
        "mileage_km": finance.get("mileage_km", 0),
        "gst_owing": finance.get("gst_owing", 0),
        "total_cca": finance.get("total_cca", 0),
        "outstanding_invoices": invoices.get("outstanding_total", 0),
    })


if __name__ == "__main__":
    print("\n  Matt Anthony Photography — Business Dashboard")
    print("  http://127.0.0.1:5050\n")
    app.run(host="127.0.0.1", port=5050, debug=True)
