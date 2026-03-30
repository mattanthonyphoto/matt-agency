"""Generate a live GA4 analytics dashboard as a self-refreshing HTML file.
Pulls data from GA4 API and renders an executive-level dashboard.
"""
import sys
import os
import json
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from google_analytics import (
    traffic_overview,
    top_pages,
    traffic_sources,
    daily_traffic,
    geo_report,
    device_report,
    run_report,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, "dist", "ga-dashboard.html")


def get_landing_pages():
    return run_report(
        dimensions=["landingPage"],
        metrics=["sessions", "bounceRate", "averageSessionDuration", "totalUsers"],
        start_date="30daysAgo",
        end_date="today",
        limit=15,
        order_by_metric="sessions",
    )


def build_dashboard():
    print("Pulling GA4 data...")
    overview = traffic_overview()
    pages = top_pages(limit=15)
    sources = traffic_sources(limit=12)
    daily = daily_traffic()
    geo = geo_report(limit=12)
    devices = device_report()
    landings = get_landing_pages()

    # Sort daily by date
    daily.sort(key=lambda x: x["date"])

    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # Build chart data
    daily_labels = json.dumps([d["date"][4:6] + "/" + d["date"][6:] for d in daily])
    daily_users = json.dumps([int(d["totalUsers"]) for d in daily])
    daily_sessions = json.dumps([int(d["sessions"]) for d in daily])
    daily_pageviews = json.dumps([int(d["screenPageViews"]) for d in daily])

    # Device chart data
    device_labels = json.dumps([d["deviceCategory"].title() for d in devices])
    device_values = json.dumps([int(d["sessions"]) for d in devices])

    # Source chart data
    source_labels = json.dumps([s["sessionSource"][:20] for s in sources[:8]])
    source_values = json.dumps([int(s["sessions"]) for s in sources[:8]])

    # Page table rows
    page_rows = ""
    for p in pages:
        dur = float(p["averageSessionDuration"])
        mins = int(dur // 60)
        secs = int(dur % 60)
        page_rows += f"""<tr>
            <td class="page-path">{p['pagePath']}</td>
            <td>{p['screenPageViews']}</td>
            <td>{p['totalUsers']}</td>
            <td>{mins}:{secs:02d}</td>
        </tr>"""

    # Landing page rows
    landing_rows = ""
    for l in landings:
        bounce = float(l["bounceRate"])
        dur = float(l["averageSessionDuration"])
        mins = int(dur // 60)
        secs = int(dur % 60)
        bounce_class = "good" if bounce < 0.4 else ("warn" if bounce < 0.6 else "bad")
        landing_rows += f"""<tr>
            <td class="page-path">{l['landingPage']}</td>
            <td>{l['sessions']}</td>
            <td><span class="badge {bounce_class}">{bounce:.0%}</span></td>
            <td>{mins}:{secs:02d}</td>
            <td>{l['totalUsers']}</td>
        </tr>"""

    # Source rows
    source_rows = ""
    for s in sources:
        bounce = float(s["bounceRate"])
        bounce_class = "good" if bounce < 0.4 else ("warn" if bounce < 0.6 else "bad")
        source_rows += f"""<tr>
            <td>{s['sessionSource']}</td>
            <td>{s['sessionMedium']}</td>
            <td>{s['sessions']}</td>
            <td>{s['totalUsers']}</td>
            <td><span class="badge {bounce_class}">{bounce:.0%}</span></td>
        </tr>"""

    # Geo rows
    geo_rows = ""
    for g in geo:
        geo_rows += f"""<tr>
            <td>{g['city']}</td>
            <td>{g['country']}</td>
            <td>{g['sessions']}</td>
            <td>{g['totalUsers']}</td>
        </tr>"""

    # Avg session duration formatted
    avg_dur = float(overview.get("avg_session_duration_sec", "0"))
    avg_mins = int(avg_dur // 60)
    avg_secs = int(avg_dur % 60)

    # Insights engine
    insights = generate_insights(overview, pages, sources, landings, devices, geo, daily)
    insights_html = "\n".join(
        f'<div class="insight {i["type"]}"><span class="insight-icon">{i["icon"]}</span><div><strong>{i["title"]}</strong><p>{i["text"]}</p></div></div>'
        for i in insights
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Matt Anthony Photo — Analytics Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
:root {{
    --bg: #ffffff;
    --card: #f9fafb;
    --card-border: #e5e7eb;
    --text: #1f2937;
    --muted: #6b7280;
    --accent: #7c3aed;
    --green: #16a34a;
    --yellow: #ca8a04;
    --red: #dc2626;
    --blue: #2563eb;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
    padding: 24px;
    max-width: 1400px;
    margin: 0 auto;
}}
.header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 32px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--card-border);
}}
.header h1 {{
    font-size: 22px;
    font-weight: 600;
    letter-spacing: -0.02em;
}}
.header .updated {{
    font-size: 13px;
    color: var(--muted);
}}
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin-bottom: 32px;
}}
.kpi {{
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 20px;
}}
.kpi .label {{
    font-size: 12px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
}}
.kpi .value {{
    font-size: 32px;
    font-weight: 700;
    letter-spacing: -0.03em;
}}
.kpi .sub {{
    font-size: 12px;
    color: var(--muted);
    margin-top: 2px;
}}
.grid-2 {{
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 16px;
    margin-bottom: 24px;
}}
.grid-3 {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px;
    margin-bottom: 24px;
}}
.card {{
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 20px;
}}
.card h2 {{
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 16px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}}
th {{
    text-align: left;
    color: var(--muted);
    font-weight: 500;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 8px 12px;
    border-bottom: 1px solid var(--card-border);
}}
td {{
    padding: 8px 12px;
    border-bottom: 1px solid rgba(0,0,0,0.05);
}}
tr:hover td {{
    background: rgba(0,0,0,0.02);
}}
.page-path {{
    font-family: 'SF Mono', monospace;
    font-size: 12px;
    color: var(--accent);
    max-width: 280px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}
.badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
}}
.badge.good {{ background: rgba(34,197,94,0.15); color: var(--green); }}
.badge.warn {{ background: rgba(234,179,8,0.15); color: var(--yellow); }}
.badge.bad {{ background: rgba(239,68,68,0.15); color: var(--red); }}

.insights {{
    margin-bottom: 24px;
}}
.insights h2 {{
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 16px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
.insight {{
    display: flex;
    gap: 12px;
    padding: 14px 16px;
    border-radius: 10px;
    margin-bottom: 8px;
    font-size: 13px;
}}
.insight strong {{
    display: block;
    margin-bottom: 2px;
    font-size: 13px;
}}
.insight p {{
    color: var(--muted);
    font-size: 12px;
    line-height: 1.5;
}}
.insight-icon {{
    font-size: 18px;
    flex-shrink: 0;
    margin-top: 2px;
}}
.insight.win {{ background: rgba(22,163,74,0.06); border: 1px solid rgba(22,163,74,0.2); }}
.insight.fix {{ background: rgba(220,38,38,0.06); border: 1px solid rgba(220,38,38,0.2); }}
.insight.idea {{ background: rgba(37,99,235,0.06); border: 1px solid rgba(37,99,235,0.2); }}
.insight.info {{ background: rgba(124,58,237,0.06); border: 1px solid rgba(124,58,237,0.2); }}

canvas {{
    max-height: 280px;
}}

@media (max-width: 900px) {{
    .grid-2, .grid-3 {{ grid-template-columns: 1fr; }}
    .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}
</style>
</head>
<body>

<div class="header">
    <h1>Matt Anthony Photo — Analytics</h1>
    <span class="updated">Last 30 days &middot; Updated {now}</span>
</div>

<div class="kpi-grid">
    <div class="kpi">
        <div class="label">Total Users</div>
        <div class="value">{overview.get('total_users', '0')}</div>
        <div class="sub">{overview.get('new_users', '0')} new</div>
    </div>
    <div class="kpi">
        <div class="label">Sessions</div>
        <div class="value">{overview.get('sessions', '0')}</div>
        <div class="sub">{float(int(overview.get('sessions','0')))/max(int(overview.get('total_users','1')),1):.1f} per user</div>
    </div>
    <div class="kpi">
        <div class="label">Pageviews</div>
        <div class="value">{overview.get('pageviews', '0')}</div>
        <div class="sub">{float(int(overview.get('pageviews','0')))/max(int(overview.get('sessions','1')),1):.1f} per session</div>
    </div>
    <div class="kpi">
        <div class="label">Bounce Rate</div>
        <div class="value">{overview.get('bounce_rate', '0%')}</div>
        <div class="sub">{'Good' if float(overview.get('bounce_rate','0%').strip('%'))/100 < 0.45 else 'Needs work'}</div>
    </div>
    <div class="kpi">
        <div class="label">Avg Session</div>
        <div class="value">{avg_mins}:{avg_secs:02d}</div>
        <div class="sub">minutes</div>
    </div>
    <div class="kpi">
        <div class="label">Pages / Session</div>
        <div class="value">{float(int(overview.get('pageviews','0')))/max(int(overview.get('sessions','1')),1):.1f}</div>
        <div class="sub">depth</div>
    </div>
</div>

<div class="insights">
    <h2>Insights &amp; Recommendations</h2>
    {insights_html}
</div>

<div class="grid-2">
    <div class="card">
        <h2>Daily Traffic (30 days)</h2>
        <canvas id="dailyChart"></canvas>
    </div>
    <div class="card">
        <h2>Devices</h2>
        <canvas id="deviceChart"></canvas>
    </div>
</div>

<div class="grid-2">
    <div class="card">
        <h2>Top Pages</h2>
        <div style="max-height: 420px; overflow-y: auto;">
        <table>
            <thead><tr><th>Page</th><th>Views</th><th>Users</th><th>Avg Time</th></tr></thead>
            <tbody>{page_rows}</tbody>
        </table>
        </div>
    </div>
    <div class="card">
        <h2>Traffic Sources</h2>
        <canvas id="sourceChart" style="margin-bottom: 16px;"></canvas>
        <div style="max-height: 260px; overflow-y: auto;">
        <table>
            <thead><tr><th>Source</th><th>Medium</th><th>Sessions</th><th>Users</th><th>Bounce</th></tr></thead>
            <tbody>{source_rows}</tbody>
        </table>
        </div>
    </div>
</div>

<div class="grid-2">
    <div class="card">
        <h2>Landing Pages</h2>
        <div style="max-height: 420px; overflow-y: auto;">
        <table>
            <thead><tr><th>Landing Page</th><th>Sessions</th><th>Bounce</th><th>Avg Time</th><th>Users</th></tr></thead>
            <tbody>{landing_rows}</tbody>
        </table>
        </div>
    </div>
    <div class="card">
        <h2>Geography</h2>
        <div style="max-height: 420px; overflow-y: auto;">
        <table>
            <thead><tr><th>City</th><th>Country</th><th>Sessions</th><th>Users</th></tr></thead>
            <tbody>{geo_rows}</tbody>
        </table>
        </div>
    </div>
</div>

<script>
const chartDefaults = {{
    color: '#6b7280',
    borderColor: 'rgba(0,0,0,0.08)',
}};
Chart.defaults.color = chartDefaults.color;

// Daily traffic
new Chart(document.getElementById('dailyChart'), {{
    type: 'line',
    data: {{
        labels: {daily_labels},
        datasets: [
            {{
                label: 'Users',
                data: {daily_users},
                borderColor: '#7c3aed',
                backgroundColor: 'rgba(124,58,237,0.1)',
                fill: true,
                tension: 0.3,
                borderWidth: 2,
                pointRadius: 3,
            }},
            {{
                label: 'Sessions',
                data: {daily_sessions},
                borderColor: '#2563eb',
                backgroundColor: 'transparent',
                tension: 0.3,
                borderWidth: 2,
                pointRadius: 2,
            }},
            {{
                label: 'Pageviews',
                data: {daily_pageviews},
                borderColor: '#16a34a',
                backgroundColor: 'transparent',
                tension: 0.3,
                borderWidth: 1.5,
                pointRadius: 1,
                borderDash: [4, 2],
            }},
        ]
    }},
    options: {{
        responsive: true,
        plugins: {{ legend: {{ position: 'top', labels: {{ boxWidth: 12, padding: 16 }} }} }},
        scales: {{
            x: {{ grid: {{ color: 'rgba(0,0,0,0.06)' }} }},
            y: {{ grid: {{ color: 'rgba(0,0,0,0.06)' }}, beginAtZero: true }}
        }}
    }}
}});

// Device chart
new Chart(document.getElementById('deviceChart'), {{
    type: 'doughnut',
    data: {{
        labels: {device_labels},
        datasets: [{{
            data: {device_values},
            backgroundColor: ['#7c3aed', '#2563eb', '#16a34a'],
            borderWidth: 0,
            spacing: 4,
        }}]
    }},
    options: {{
        responsive: true,
        cutout: '65%',
        plugins: {{ legend: {{ position: 'bottom', labels: {{ padding: 20, boxWidth: 12 }} }} }}
    }}
}});

// Source chart
new Chart(document.getElementById('sourceChart'), {{
    type: 'bar',
    data: {{
        labels: {source_labels},
        datasets: [{{
            label: 'Sessions',
            data: {source_values},
            backgroundColor: 'rgba(124,58,237,0.15)',
            borderColor: '#7c3aed',
            borderWidth: 1,
            borderRadius: 4,
        }}]
    }},
    options: {{
        responsive: true,
        indexAxis: 'y',
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
            x: {{ grid: {{ color: 'rgba(0,0,0,0.06)' }}, beginAtZero: true }},
            y: {{ grid: {{ display: false }} }}
        }}
    }}
}});
</script>

</body>
</html>"""

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write(html)
    print(f"Dashboard saved to {OUTPUT_PATH}")


def generate_insights(overview, pages, sources, landings, devices, geo, daily):
    insights = []
    total_users = int(overview.get("total_users", 0))
    sessions = int(overview.get("sessions", 0))
    pageviews = int(overview.get("pageviews", 0))
    bounce_str = overview.get("bounce_rate", "0%").strip("%")
    bounce = float(bounce_str) / 100 if float(bounce_str) > 1 else float(bounce_str)
    avg_dur = float(overview.get("avg_session_duration_sec", 0))
    pages_per_session = pageviews / max(sessions, 1)

    # 1. Session depth
    if pages_per_session > 4:
        insights.append({
            "type": "win",
            "icon": "&#9650;",
            "title": f"{pages_per_session:.1f} pages per session is excellent",
            "text": "Visitors are deeply exploring your portfolio. This signals strong interest and high-quality content.",
        })

    # 2. Session duration
    if avg_dur > 300:
        insights.append({
            "type": "win",
            "icon": "&#9650;",
            "title": f"{int(avg_dur//60)}+ minute average sessions",
            "text": "People are spending serious time on your site. For a photographer, this means they're studying your work — exactly what you want before a discovery call.",
        })

    # 3. Bounce rate
    if bounce > 0.5:
        insights.append({
            "type": "fix",
            "icon": "&#9660;",
            "title": f"Bounce rate at {bounce:.0%} — needs attention",
            "text": "Over half of visitors leave after one page. Add stronger CTAs, internal links to project pages, and consider a sticky nav with portfolio highlights.",
        })
    elif bounce < 0.45:
        insights.append({
            "type": "win",
            "icon": "&#9650;",
            "title": f"Bounce rate at {bounce:.0%} — solid engagement",
            "text": "Most visitors click through to additional pages. Your site structure is working.",
        })

    # 4. Direct traffic dominance
    direct_pct = 0
    organic_pct = 0
    for s in sources:
        if s["sessionSource"] == "(direct)":
            direct_pct = int(s["sessions"]) / max(sessions, 1)
        if s["sessionMedium"] == "organic":
            organic_pct += int(s["sessions"]) / max(sessions, 1)

    if direct_pct > 0.6:
        insights.append({
            "type": "fix",
            "icon": "&#9888;",
            "title": f"{direct_pct:.0%} of traffic is direct — you're dependent on people who already know you",
            "text": "Almost no discovery traffic. SEO and social need to become real channels. Target 'architectural photographer [city]' keywords, publish case studies as blog posts, and build backlinks from builder/architect websites.",
        })

    if organic_pct > 0 and organic_pct < 0.3:
        insights.append({
            "type": "idea",
            "icon": "&#10148;",
            "title": f"Organic search is only {organic_pct:.0%} of traffic",
            "text": "Huge growth opportunity. Each project page should target '[builder name] + [city] + photography'. Add schema markup, alt text on all images, and a blog with case studies to capture long-tail searches.",
        })

    # 5. Discovery call funnel
    disco_views = 0
    disco_form_views = 0
    for p in pages:
        if p["pagePath"] == "/discovery-call":
            disco_views = int(p["screenPageViews"])
        if "discovery-call-form" in p["pagePath"]:
            disco_form_views += int(p["screenPageViews"])

    if disco_views > 0:
        insights.append({
            "type": "info",
            "icon": "&#9679;",
            "title": f"Discovery call page: {disco_views} views, form: {disco_form_views} views",
            "text": f"Roughly {disco_form_views}/{disco_views} visitors ({disco_form_views/max(disco_views,1)*100:.0f}%) who hit the discovery page engage with the form. Consider adding social proof (testimonials) and reducing form fields to boost conversion.",
        })

    # 6. Pricing page engagement
    pricing_views = 0
    pricing_dur = 0
    for p in pages:
        if "pricing" in p["pagePath"]:
            pricing_views += int(p["screenPageViews"])
            pricing_dur = max(pricing_dur, float(p["averageSessionDuration"]))

    if pricing_views > 0:
        insights.append({
            "type": "info",
            "icon": "&#9679;",
            "title": f"Pricing pages: {pricing_views} total views, up to {int(pricing_dur//60)}:{int(pricing_dur%60):02d} avg time",
            "text": "People are seriously evaluating your pricing. This is high-intent traffic. Make sure pricing pages have clear next steps and a prominent CTA to book a call.",
        })

    # 7. Mobile experience
    for d in devices:
        if d["deviceCategory"] == "mobile":
            mobile_bounce = float(d["bounceRate"])
            mobile_sessions = int(d["sessions"])
            mobile_pct = mobile_sessions / max(sessions, 1)
            if mobile_bounce > 0.5:
                insights.append({
                    "type": "fix",
                    "icon": "&#9660;",
                    "title": f"Mobile bounce rate is {mobile_bounce:.0%} ({mobile_pct:.0%} of traffic)",
                    "text": "Mobile visitors bounce more. Check page speed on mobile, ensure images are optimized (WebP, lazy load), and verify the mobile nav is easy to use.",
                })
            else:
                insights.append({
                    "type": "win",
                    "icon": "&#9650;",
                    "title": f"Mobile bounce rate at {mobile_bounce:.0%} — well optimized",
                    "text": f"Mobile makes up {mobile_pct:.0%} of traffic and engagement is healthy.",
                })

    # 8. Top project pages
    project_pages = [p for p in pages if p["pagePath"] not in
                     ["/", "/projects", "/bio", "/contact", "/home", "/journal", "/process",
                      "/faqs", "/digital-business-card", "/discovery-call", "/project-photography",
                      "/creative-partner"] and "pricing" not in p["pagePath"]
                     and "discovery" not in p["pagePath"] and "form" not in p["pagePath"]
                     and "squamish" not in p["pagePath"] and "pemberton" not in p["pagePath"]
                     and "construction-team" not in p["pagePath"]]
    if project_pages:
        top3 = project_pages[:3]
        names = ", ".join(p["pagePath"].strip("/").replace("-", " ").title() for p in top3)
        insights.append({
            "type": "idea",
            "icon": "&#10148;",
            "title": f"Most viewed projects: {names}",
            "text": "These are your strongest portfolio pieces by traffic. Feature them prominently on the homepage, use them in cold emails, and create case study content around them.",
        })

    # 9. Geo insight
    local_sessions = 0
    for g in geo:
        if g["city"] in ["Squamish", "Vancouver", "North Vancouver", "West Vancouver", "Whistler", "Pemberton"]:
            local_sessions += int(g["sessions"])
    local_pct = local_sessions / max(sessions, 1)
    if local_pct > 0:
        insights.append({
            "type": "info",
            "icon": "&#9679;",
            "title": f"{local_pct:.0%} of traffic from Sea-to-Sky / Metro Vancouver",
            "text": f"{local_sessions} sessions from your core market. The Squamish concentration ({geo[0]['sessions']} sessions) suggests repeat visits from a small group — likely existing clients or close network.",
        })

    # 10. Social referral
    social_sessions = 0
    for s in sources:
        if any(x in s["sessionSource"] for x in ["instagram", "facebook", "linkedin", "pinterest"]):
            social_sessions += int(s["sessions"])
    social_pct = social_sessions / max(sessions, 1)
    if social_pct < 0.1:
        insights.append({
            "type": "fix",
            "icon": "&#9888;",
            "title": f"Social media drives only {social_pct:.0%} of traffic ({social_sessions} sessions)",
            "text": "Your Instagram and LinkedIn presence isn't converting to site visits. Add link-in-bio with UTM tracking, post carousel content that drives to specific project pages, and use Stories with 'link' stickers.",
        })

    return insights


if __name__ == "__main__":
    build_dashboard()
