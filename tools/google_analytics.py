"""Google Analytics 4 Data API tool.
Pulls reports from GA4 using OAuth credentials (shared with Sheets/Drive).
"""
import sys
import os
import json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_credentials

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Dimension,
    Metric,
    OrderBy,
)

PROPERTY_ID = "349457616"


def get_analytics_client():
    """Return an authenticated GA4 BetaAnalyticsDataClient."""
    creds = get_credentials()
    return BetaAnalyticsDataClient(credentials=creds)


def run_report(
    dimensions: list[str],
    metrics: list[str],
    start_date: str = "30daysAgo",
    end_date: str = "today",
    limit: int = 25,
    order_by_metric: str = None,
    descending: bool = True,
):
    """Run a GA4 report and return rows as list of dicts.

    Args:
        dimensions: e.g. ["pagePath", "sessionSource"]
        metrics: e.g. ["sessions", "totalUsers", "screenPageViews"]
        start_date: "30daysAgo", "7daysAgo", "2026-01-01", etc.
        end_date: "today", "yesterday", "2026-03-30", etc.
        limit: max rows to return
        order_by_metric: metric name to sort by (defaults to first metric)
        descending: sort direction
    """
    client = get_analytics_client()

    if order_by_metric is None:
        order_by_metric = metrics[0]

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        order_bys=[
            OrderBy(
                metric=OrderBy.MetricOrderBy(metric_name=order_by_metric),
                desc=descending,
            )
        ],
        limit=limit,
    )

    response = client.run_report(request)

    rows = []
    for row in response.rows:
        entry = {}
        for i, dim in enumerate(dimensions):
            entry[dim] = row.dimension_values[i].value
        for i, met in enumerate(metrics):
            entry[met] = row.metric_values[i].value
        rows.append(entry)

    return rows


def traffic_overview(start_date="30daysAgo", end_date="today"):
    """High-level traffic overview: users, sessions, pageviews, bounce rate, avg duration."""
    client = get_analytics_client()

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        metrics=[
            Metric(name="totalUsers"),
            Metric(name="sessions"),
            Metric(name="screenPageViews"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
            Metric(name="newUsers"),
        ],
    )

    response = client.run_report(request)

    if response.rows:
        row = response.rows[0]
        return {
            "period": f"{start_date} to {end_date}",
            "total_users": row.metric_values[0].value,
            "sessions": row.metric_values[1].value,
            "pageviews": row.metric_values[2].value,
            "bounce_rate": f"{float(row.metric_values[3].value):.1%}",
            "avg_session_duration_sec": f"{float(row.metric_values[4].value):.0f}",
            "new_users": row.metric_values[5].value,
        }
    return {}


def top_pages(start_date="30daysAgo", end_date="today", limit=25):
    """Top pages by pageviews."""
    return run_report(
        dimensions=["pagePath"],
        metrics=["screenPageViews", "totalUsers", "averageSessionDuration"],
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        order_by_metric="screenPageViews",
    )


def traffic_sources(start_date="30daysAgo", end_date="today", limit=15):
    """Traffic by source/medium."""
    return run_report(
        dimensions=["sessionSource", "sessionMedium"],
        metrics=["sessions", "totalUsers", "bounceRate"],
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        order_by_metric="sessions",
    )


def daily_traffic(start_date="30daysAgo", end_date="today"):
    """Daily traffic trend."""
    return run_report(
        dimensions=["date"],
        metrics=["totalUsers", "sessions", "screenPageViews"],
        start_date=start_date,
        end_date=end_date,
        limit=90,
        order_by_metric="totalUsers",
        descending=False,
    )


def geo_report(start_date="30daysAgo", end_date="today", limit=15):
    """Traffic by city."""
    return run_report(
        dimensions=["city", "country"],
        metrics=["sessions", "totalUsers"],
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        order_by_metric="sessions",
    )


def device_report(start_date="30daysAgo", end_date="today"):
    """Traffic by device category."""
    return run_report(
        dimensions=["deviceCategory"],
        metrics=["sessions", "totalUsers", "bounceRate"],
        start_date=start_date,
        end_date=end_date,
        limit=10,
        order_by_metric="sessions",
    )


def print_report(title, data):
    """Pretty print a report."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    if isinstance(data, dict):
        for k, v in data.items():
            print(f"  {k:30s} {v}")
    elif isinstance(data, list):
        if data:
            headers = list(data[0].keys())
            print("  " + " | ".join(f"{h:>20s}" for h in headers))
            print("  " + "-" * (23 * len(headers)))
            for row in data:
                print("  " + " | ".join(f"{str(v):>20s}" for v in row.values()))
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pull GA4 reports")
    parser.add_argument("--report", default="all",
                        choices=["all", "overview", "pages", "sources", "daily", "geo", "devices"],
                        help="Which report to run")
    parser.add_argument("--start", default="30daysAgo", help="Start date")
    parser.add_argument("--end", default="today", help="End date")
    parser.add_argument("--limit", type=int, default=25, help="Max rows")
    args = parser.parse_args()

    reports = {
        "overview": ("Traffic Overview", lambda: traffic_overview(args.start, args.end)),
        "pages": ("Top Pages", lambda: top_pages(args.start, args.end, args.limit)),
        "sources": ("Traffic Sources", lambda: traffic_sources(args.start, args.end, args.limit)),
        "daily": ("Daily Traffic", lambda: daily_traffic(args.start, args.end)),
        "geo": ("Geography", lambda: geo_report(args.start, args.end, args.limit)),
        "devices": ("Devices", lambda: device_report(args.start, args.end)),
    }

    if args.report == "all":
        for name, (title, fn) in reports.items():
            print_report(title, fn())
    else:
        title, fn = reports[args.report]
        print_report(title, fn())
