#!/usr/bin/env python3
"""Live Business Dashboard v3 — Light theme, expanded data, premium design. localhost:8888"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
from agent_utils import (
    get_ghl_opportunities, get_ghl_contacts, get_ghl_invoices,
    get_instantly_campaigns, get_instantly_replies,
    search_gmail, _calendar_api_call, get_google_creds,
    INSTANTLY_HEADERS
)
import requests

PORT = 8888

AGENTS = [
    {"name": "Morning Command", "schedule": "Daily 7 AM", "pillar": "REPORT", "log": "/tmp/morning_command.log", "icon": "☀️", "desc": "Calendar, email, pipeline, campaigns, actions"},
    {"name": "Reply Classifier", "schedule": "Every 2hrs", "pillar": "WATCH", "log": "/tmp/reply_classifier.log", "icon": "📨", "desc": "Classify cold email replies, create GHL contacts"},
    {"name": "DM Prep", "schedule": "Daily 6 AM", "pillar": "WORK", "log": "/tmp/operator_dm.log", "icon": "📱", "desc": "10 personalized IG DMs ready to send"},
    {"name": "Follow-Up Drafter", "schedule": "Tue/Thu 8 AM", "pillar": "WORK", "log": "/tmp/operator_followup.log", "icon": "📝", "desc": "Gmail drafts for stale pipeline deals"},
    {"name": "Content Operator", "schedule": "MWF 6:30 AM", "pillar": "WORK", "log": "/tmp/operator_content.log", "icon": "📸", "desc": "IG + LinkedIn + Pinterest captions"},
    {"name": "Lead Processor", "schedule": "Sat 10 AM", "pillar": "WORK", "log": "/tmp/operator_leads.log", "icon": "🔄", "desc": "Process 50 secondary ICP leads"},
    {"name": "Review Harvester", "schedule": "Wed 10 AM", "pillar": "WORK", "log": "/tmp/operator_reviews.log", "icon": "⭐", "desc": "Google review request drafts"},
    {"name": "Health Check", "schedule": "Every 4hrs", "pillar": "WATCH", "log": "/tmp/watchdog_health.log", "icon": "🏥", "desc": "Website, n8n, GHL, Instantly uptime"},
    {"name": "GBP Monitor", "schedule": "Daily 6 PM", "pillar": "WATCH", "log": "/tmp/watchdog_gbp.log", "icon": "📍", "desc": "Google Business reviews & questions"},
    {"name": "Domain Check", "schedule": "Daily 9 AM", "pillar": "WATCH", "log": "/tmp/watchdog_domains.log", "icon": "📡", "desc": "Instantly sending domain health"},
    {"name": "Retainer Tracker", "schedule": "1st of month", "pillar": "WATCH", "log": "/tmp/watchdog_retainer.log", "icon": "📋", "desc": "Balmoral monthly deliverables"},
    {"name": "Invoice Chaser", "schedule": "Wed/Fri 9 AM", "pillar": "FINANCE", "log": "/tmp/accountant_invoices.log", "icon": "💳", "desc": "Chase overdue invoices >14 days"},
    {"name": "Expense Tracker", "schedule": "Mon 9 AM", "pillar": "FINANCE", "log": "/tmp/accountant_expenses.log", "icon": "🧾", "desc": "Weekly charge & receipt summary"},
    {"name": "Tax Reminders", "schedule": "1st + 15th", "pillar": "FINANCE", "log": "/tmp/accountant_tax.log", "icon": "📊", "desc": "FHSA, installments, GST, LOC"},
    {"name": "Shoot Prep", "schedule": "Daily 8 PM", "pillar": "PRODUCE", "log": "/tmp/producer_prep.log", "icon": "📷", "desc": "Tomorrow's shoot checklist"},
    {"name": "Editor Handoff", "schedule": "Mon/Thu 9 AM", "pillar": "PRODUCE", "log": "/tmp/producer_handoff.log", "icon": "🎬", "desc": "Cull selects → Alena → deadline"},
    {"name": "Delivery Tracker", "schedule": "Daily 5 PM", "pillar": "PRODUCE", "log": "/tmp/producer_delivery.log", "icon": "📦", "desc": "Flag projects 5/7/10+ days"},
    {"name": "Cost-Share", "schedule": "Fri 2 PM", "pillar": "PRODUCE", "log": "/tmp/producer_costshare.log", "icon": "💰", "desc": "30% licensing after delivery"},
    {"name": "Campaign Analysis", "schedule": "Mon/Thu 10 AM", "pillar": "STRATEGY", "log": "/tmp/strategist_campaigns.log", "icon": "📊", "desc": "Open/reply/bounce by ICP"},
    {"name": "Win/Loss", "schedule": "1st of month", "pillar": "STRATEGY", "log": "/tmp/strategist_winloss.log", "icon": "📈", "desc": "Close rate & deal patterns"},
    {"name": "Competitor Watch", "schedule": "1st + 15th", "pillar": "STRATEGY", "log": "/tmp/strategist_competitors.log", "icon": "🔍", "desc": "Peter, Knowles, Fyfe activity"},
    {"name": "Attribution", "schedule": "Sun 6 PM", "pillar": "STRATEGY", "log": "/tmp/strategist_attribution.log", "icon": "🔗", "desc": "Lead source breakdown"},
    {"name": "Sunday Command", "schedule": "Sun 7 PM", "pillar": "ANALYZE", "log": "/tmp/sunday_command.log", "icon": "📊", "desc": "Full weekly business review"},
]

PILLAR_META = {
    "REPORT": {"color": "#2563eb", "bg": "#eff6ff", "label": "Report"},
    "WATCH":  {"color": "#7c3aed", "bg": "#f5f3ff", "label": "Watch"},
    "WORK":   {"color": "#059669", "bg": "#ecfdf5", "label": "Work"},
    "FINANCE":{"color": "#ea580c", "bg": "#fff7ed", "label": "Finance"},
    "PRODUCE":{"color": "#0891b2", "bg": "#ecfeff", "label": "Produce"},
    "STRATEGY":{"color": "#ca8a04", "bg": "#fefce8", "label": "Strategy"},
    "ANALYZE":{"color": "#db2777", "bg": "#fdf2f8", "label": "Analyze"},
}

def agent_status(agent):
    log = agent["log"]
    if not os.path.exists(log):
        return {"last_run": None, "status": "pending", "output": ""}
    try:
        mtime = os.path.getmtime(log)
        last_run = datetime.fromtimestamp(mtime)
        with open(log) as f:
            lines = [l.strip() for l in f.readlines()[-5:] if l.strip()]
            output = lines[-1] if lines else ""
        if "✅" in output or "healthy" in output.lower(): status = "ok"
        elif "error" in output.lower() or "failed" in output.lower() or "Traceback" in output: status = "error"
        elif "No " in output or "no " in output.lower(): status = "idle"
        else: status = "ok"
        return {"last_run": last_run, "status": status, "output": output[:60]}
    except:
        return {"last_run": None, "status": "unknown", "output": ""}

def fetch_all():
    d = {}
    now = datetime.now()
    try:
        s = now.replace(hour=0,minute=0,second=0).isoformat()+"-07:00"
        e = now.replace(hour=23,minute=59,second=59).isoformat()+"-07:00"
        d["cal"] = _calendar_api_call(s, e)
    except: d["cal"] = []
    try: d["mail"] = search_gmail("newer_than:1d -category:promotions -category:social -category:updates", 15)
    except: d["mail"] = []
    try: d["opps"] = get_ghl_opportunities().get("opportunities", [])
    except: d["opps"] = []
    try: d["inv"] = get_ghl_invoices().get("invoices", get_ghl_invoices().get("data", []))
    except: d["inv"] = []
    try:
        c = get_instantly_campaigns()
        d["camps"] = c if isinstance(c,list) else c.get("items",c.get("data",[]))
    except: d["camps"] = []
    try:
        r = get_instantly_replies()
        d["replies"] = r if isinstance(r,list) else r.get("data",r.get("items",[]))
    except: d["replies"] = []
    try: d["contacts"] = get_ghl_contacts(100).get("contacts",[])
    except: d["contacts"] = []
    return d

def render(data):
    now = datetime.now()
    today_str = now.strftime("%A, %B %d, %Y")
    time_str = now.strftime("%-I:%M %p")

    # === CRUNCH NUMBERS ===
    inv = data.get("inv",[])
    ytd_rev = 0; mo_rev = 0; outs = []
    for i in inv:
        amt = i.get("amount",i.get("total",0)) or 0
        if amt > 10000: amt /= 100
        st = i.get("status","").lower()
        nm = i.get("name",i.get("title",i.get("contactName","?")))
        cr = i.get("createdAt",i.get("created_at",""))
        if st in ["paid","completed"] and "2026" in str(cr):
            ytd_rev += amt
            if now.strftime("%Y-%m") in str(cr): mo_rev += amt
        elif st in ["sent","viewed","overdue","unpaid"] and amt > 0:
            age=0
            try: age=(now-datetime.fromisoformat(cr.replace("Z","+00:00")).replace(tzinfo=None)).days
            except: pass
            outs.append({"n":nm,"a":amt,"d":age})
    rec = 1417.50
    ytd = ytd_rev + rec*now.month
    tgt = 125000; pct = ytd/tgt*100; gap = tgt-ytd
    ml = 12-now.month; pace = gap/ml if ml>0 else gap
    tot_out = sum(o["a"] for o in outs)

    opps = data.get("opps",[])
    hot=[]; warm=[]; stale=[]
    pv = 0
    for o in opps:
        if o.get("status")!="open": continue
        nm=o.get("name","?"); v=o.get("monetaryValue",0) or 0; pv+=v
        try: age=(now-datetime.fromisoformat(o.get("lastStageChangeAt",o.get("updatedAt","")).replace("Z","+00:00")).replace(tzinfo=None)).days
        except: age=99
        d={"n":nm,"v":v,"d":age}
        if age<=3: hot.append(d)
        elif age<=7: warm.append(d)
        else: stale.append(d)

    cal = data.get("cal",[])
    mail = data.get("mail",[])
    inbox = [m for m in mail if "INBOX" in m.get("labels",[]) or "UNREAD" in m.get("labels",[])]
    drafts = [m for m in mail if "DRAFT" in m.get("labels",[]) and "SENT" not in m.get("labels",[])]
    camps = data.get("camps",[])
    reps = data.get("replies",[]) or []
    contacts = data.get("contacts",[])

    # Agent statuses
    agents = [{**a, **agent_status(a)} for a in AGENTS]
    ok_ct = sum(1 for a in agents if a["status"]=="ok")
    err_ct = sum(1 for a in agents if a["status"]=="error")
    idle_ct = sum(1 for a in agents if a["status"]=="idle")
    pend_ct = sum(1 for a in agents if a["status"]=="pending")

    # Health
    hlth = []
    for sn,url in [("mattanthonyphoto.com","https://mattanthonyphoto.com"),("n8n","https://n8n.srv1277163.hstgr.cloud/healthz")]:
        try:
            r=requests.get(url,timeout=5); ms=int(r.elapsed.total_seconds()*1000)
            hlth.append({"n":sn,"ok":r.status_code==200,"ms":ms})
        except: hlth.append({"n":sn,"ok":False,"ms":0})

    # Contact stats
    tagged_leads = sum(1 for c in contacts if "warm-lead" in (c.get("tags") or []))
    total_contacts = len(contacts)

    # === HELPERS ===
    def kpi(label, value, sub, color="#1a1a2e", accent=""):
        ac = f'style="color:{accent}"' if accent else ""
        return f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value" {ac}>{value}</div><div class="kpi-sub">{sub}</div></div>'

    def rows(items, empty="Nothing to show"):
        if not items: return f'<div class="empty">{empty}</div>'
        return "".join(items)

    def deal_html(deals, empty):
        if not deals: return f'<div class="empty">{empty}</div>'
        h=""
        for d in deals[:6]:
            vs = f'<span class="rv">${d["v"]:,.0f}</span>' if d["v"] else ""
            h+=f'<div class="item"><span class="item-text">{d["n"]}</span>{vs}<span class="item-meta">{d["d"]}d</span></div>'
        return h

    bar_pct = min(pct,100)
    bar_col = "#16a34a" if pct>=50 else "#ca8a04" if pct>=25 else "#dc2626"

    # Events
    ev_html = ""
    for e in cal:
        s = e.get("start",{}).get("dateTime","")
        sm = e.get("summary","Untitled")
        loc = e.get("location","")
        try: t = datetime.fromisoformat(s.replace("Z","+00:00")).strftime("%-I:%M %p")
        except: t=""
        ev_html += f'<div class="item"><span class="item-time">{t}</span><span class="item-text">{sm}</span></div>'
        if loc: ev_html += f'<div class="item-loc">📍 {loc}</div>'
    if not ev_html: ev_html = '<div class="empty">No events — open day for deep work</div>'

    # Emails
    em_html = ""
    for m in inbox[:10]:
        fr = m.get("from","").split("<")[0].strip().strip('"')[:25]
        su = m.get("subject","")[:50]
        un = " unread" if "UNREAD" in m.get("labels",[]) else ""
        em_html += f'<div class="item{un}"><span class="item-from">{fr}</span><span class="item-text">{su}</span></div>'
    if not em_html: em_html = '<div class="empty">Inbox clear</div>'

    # Campaigns
    cp_html = ""
    for c in camps:
        n = c.get("name","?")
        active = c.get("status",0)==1
        tag = '<span class="tag green">Live</span>' if active else '<span class="tag amber">Paused</span>'
        cp_html += f'<div class="item"><span class="item-text">{n}</span>{tag}</div>'
    if not cp_html: cp_html = '<div class="empty">No campaign data</div>'

    # Outstanding
    ou_html = ""
    for o in sorted(outs,key=lambda x:x["d"],reverse=True)[:5]:
        crit = " crit" if o["d"]>30 else ""
        ou_html += f'<div class="item{crit}"><span class="item-text">{o["n"]}</span><span class="rv warn">${o["a"]:,.0f}</span><span class="item-meta">{o["d"]}d</span></div>'
    if not ou_html: ou_html = '<div class="empty">All invoices paid</div>'

    # Agent fleet
    pillars_order = ["REPORT","WATCH","WORK","FINANCE","PRODUCE","STRATEGY","ANALYZE"]
    fleet_html = ""
    for pname in pillars_order:
        pa = [a for a in agents if a["pillar"]==pname]
        if not pa: continue
        pm = PILLAR_META[pname]
        fleet_html += f'<div class="pillar"><div class="pillar-head"><span class="pillar-badge" style="background:{pm["bg"]};color:{pm["color"]}">{pm["label"]}</span><span class="pillar-count">{len(pa)} agents</span></div><div class="pillar-grid">'
        for a in pa:
            st = a["status"]
            if st=="ok": dot="dot-ok"; stxt="Running"
            elif st=="error": dot="dot-err"; stxt="Error"
            elif st=="idle": dot="dot-idle"; stxt="Idle"
            else: dot="dot-pend"; stxt="Pending"
            ago=""
            if a["last_run"]:
                mins=int((now-a["last_run"]).total_seconds()/60)
                if mins<60: ago=f"{mins}m ago"
                elif mins<1440: ago=f"{mins//60}h ago"
                else: ago=f"{mins//1440}d ago"
            else: ago="—"
            out = a.get("output","")
            if out and len(out)>40: out=out[:40]+"…"
            fleet_html += f'''<div class="agent">
                <div class="agent-top">
                    <span class="agent-dot {dot}"></span>
                    <span class="agent-icon">{a["icon"]}</span>
                    <span class="agent-name">{a["name"]}</span>
                    <span class="agent-status-tag {dot}">{stxt}</span>
                </div>
                <div class="agent-mid">{a["desc"]}</div>
                <div class="agent-bot">
                    <span>🕐 {a["schedule"]}</span>
                    <span>Last: {ago}</span>
                </div>
                {f'<div class="agent-output">{out}</div>' if out else ''}
            </div>'''
        fleet_html += '</div></div>'

    # Timeline
    timeline = [
        ("6:00 AM","📱 DM Prep","Work"),("6:30 AM","📸 Content (MWF)","Work"),
        ("7:00 AM","☀️ Morning Command","Report"),("8:00 AM","📝 Follow-ups (T/Th)","Work"),
        ("8:00 AM","📨 Reply Classifier","Watch"),("9:00 AM","📡 Domain Check","Watch"),
        ("9:00 AM","💳 Invoices (W/F)","Finance"),("10:00 AM","📊 Campaigns (M/Th)","Strategy"),
        ("10:00 AM","⭐ Reviews (Wed)","Work"),("12:00 PM","📨 Reply Classifier","Watch"),
        ("2:00 PM","📨 Reply Classifier","Watch"),("2:00 PM","💰 Cost-Share (Fri)","Produce"),
        ("4:00 PM","📨 Reply Classifier","Watch"),("5:00 PM","📦 Delivery Tracker","Produce"),
        ("6:00 PM","📍 GBP Monitor","Watch"),("6:00 PM","📨 Reply Classifier","Watch"),
        ("8:00 PM","📷 Shoot Prep","Produce"),
    ]
    # Highlight current hour
    cur_h = now.hour
    tl_html = ""
    for t,name,pil in timeline:
        pm = PILLAR_META.get(pil.upper(), PILLAR_META["WORK"])
        try:
            th = int(t.split(":")[0])
            if "PM" in t and th!=12: th+=12
            if "AM" in t and th==12: th=0
        except: th=-1
        active = " tl-active" if th==cur_h else " tl-past" if th<cur_h else ""
        tl_html += f'<div class="tl-row{active}"><span class="tl-time">{t}</span><span class="tl-dot" style="background:{pm["color"]}"></span><span class="tl-name">{name}</span></div>'

    return f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta http-equiv="refresh" content="300">
<title>Dashboard — Matt Anthony Photography</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html{{font-size:14px}}
body{{
    background:#f8f9fb;color:#1a1a2e;
    font-family:'Inter',-apple-system,system-ui,sans-serif;
    line-height:1.5;padding:28px 36px;min-height:100vh;
}}

/* HEADER */
.hdr{{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:28px;padding-bottom:20px;border-bottom:2px solid #e5e7eb}}
.hdr h1{{font-size:22px;font-weight:900;letter-spacing:-0.03em;color:#0f172a}}
.hdr-sub{{color:#64748b;font-size:13px;margin-top:2px}}
.hdr-right{{text-align:right}}
.hdr-time{{font-size:24px;font-weight:800;color:#0f172a}}
.hdr-date{{font-size:12px;color:#64748b}}
.live{{display:inline-flex;align-items:center;gap:6px;background:#ecfdf5;color:#059669;font-size:11px;font-weight:600;padding:4px 12px;border-radius:20px;margin-top:6px}}
.live-dot{{width:6px;height:6px;border-radius:50%;background:#059669;animation:pulse 2s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}

/* KPIS */
.kpis{{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin-bottom:24px}}
.kpi{{background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:18px 20px}}
.kpi-label{{font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:#94a3b8;font-weight:600;margin-bottom:4px}}
.kpi-value{{font-size:28px;font-weight:900;letter-spacing:-.03em;line-height:1.1;color:#0f172a}}
.kpi-sub{{font-size:11px;color:#94a3b8;margin-top:3px}}
.bar{{width:100%;height:6px;background:#e5e7eb;border-radius:3px;margin-top:10px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:3px;transition:width .5s}}

/* GRID */
.g3{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px}}
.g2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px}}
.g-fleet{{display:grid;grid-template-columns:280px 1fr;gap:20px;margin-bottom:20px}}
.card{{background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:22px;overflow:hidden}}
.card-t{{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:#94a3b8;font-weight:600;margin-bottom:14px;display:flex;align-items:center;gap:8px}}
.badge{{background:#f1f5f9;padding:2px 10px;border-radius:20px;font-size:10px;color:#475569;font-weight:600}}
.sect{{font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:#94a3b8;font-weight:600;padding:10px 0 4px;margin-top:6px}}

/* ITEMS */
.item{{display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid #f1f5f9;font-size:13px}}
.item:last-child{{border-bottom:none}}
.item-time{{font-weight:700;color:#2563eb;min-width:76px;font-size:12px}}
.item-from{{font-weight:600;color:#0f172a;min-width:100px;white-space:nowrap}}
.item-text{{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#334155}}
.item-meta{{color:#94a3b8;font-size:11px;min-width:32px;text-align:right}}
.item-loc{{font-size:11px;color:#94a3b8;padding:0 0 6px 86px}}
.rv{{font-weight:700;color:#059669;white-space:nowrap}}
.rv.warn{{color:#ea580c}}
.item.unread .item-from{{color:#2563eb}}
.item.unread .item-text{{color:#0f172a;font-weight:500}}
.item.crit{{color:#dc2626}}
.item.crit .rv{{color:#dc2626}}
.tag{{font-size:10px;padding:2px 10px;border-radius:20px;font-weight:600;white-space:nowrap}}
.tag.green{{background:#ecfdf5;color:#059669}}
.tag.amber{{background:#fefce8;color:#ca8a04}}
.tag.red{{background:#fef2f2;color:#dc2626}}
.empty{{color:#94a3b8;font-size:13px;padding:10px 0;font-style:italic}}

/* HEALTH */
.hlth{{display:flex;align-items:center;gap:8px;padding:5px 0;font-size:13px}}
.hlth-dot{{width:8px;height:8px;border-radius:50%}}
.hlth-ok{{background:#22c55e;box-shadow:0 0 6px rgba(34,197,94,.4)}}
.hlth-dn{{background:#ef4444;box-shadow:0 0 6px rgba(239,68,68,.4)}}
.hlth-ms{{margin-left:auto;color:#94a3b8;font-size:11px}}

/* TIMELINE */
.tl-card{{background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:22px;overflow-y:auto;max-height:600px}}
.tl-title{{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:#94a3b8;font-weight:600;margin-bottom:14px}}
.tl-row{{display:flex;align-items:center;gap:10px;padding:6px 0;font-size:12px;color:#64748b;border-left:2px solid #e5e7eb;margin-left:6px;padding-left:14px;position:relative}}
.tl-row.tl-active{{border-left-color:#2563eb;color:#0f172a;font-weight:600}}
.tl-row.tl-past{{opacity:.4}}
.tl-time{{min-width:64px;font-weight:600;font-size:11px}}
.tl-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.tl-name{{flex:1}}
.tl-row.tl-active .tl-dot{{box-shadow:0 0 8px rgba(37,99,235,.5)}}

/* AGENTS */
.pillar{{margin-bottom:16px}}
.pillar-head{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
.pillar-badge{{font-size:11px;font-weight:700;padding:4px 14px;border-radius:8px;text-transform:uppercase;letter-spacing:.06em}}
.pillar-count{{font-size:11px;color:#94a3b8}}
.pillar-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}}
.agent{{background:#f8f9fb;border:1px solid #e5e7eb;border-radius:12px;padding:14px 16px;transition:all .15s}}
.agent:hover{{background:#f1f5f9;border-color:#cbd5e1;transform:translateY(-1px);box-shadow:0 2px 8px rgba(0,0,0,.04)}}
.agent-top{{display:flex;align-items:center;gap:8px;font-size:13px}}
.agent-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.dot-ok{{background:#22c55e;box-shadow:0 0 6px rgba(34,197,94,.4)}}
.dot-err{{background:#ef4444;box-shadow:0 0 6px rgba(239,68,68,.4)}}
.dot-idle{{background:#3b82f6;box-shadow:0 0 6px rgba(59,130,246,.3)}}
.dot-pend{{background:#cbd5e1}}
.agent-icon{{font-size:15px}}
.agent-name{{font-weight:600;flex:1;color:#0f172a}}
.agent-status-tag{{font-size:9px;padding:2px 8px;border-radius:6px;font-weight:600;text-transform:uppercase;letter-spacing:.06em}}
.agent-status-tag.dot-ok{{background:#ecfdf5;color:#059669}}
.agent-status-tag.dot-err{{background:#fef2f2;color:#dc2626}}
.agent-status-tag.dot-idle{{background:#eff6ff;color:#2563eb}}
.agent-status-tag.dot-pend{{background:#f1f5f9;color:#94a3b8}}
.agent-mid{{font-size:12px;color:#64748b;padding:4px 0 4px 32px}}
.agent-bot{{display:flex;justify-content:space-between;font-size:11px;color:#94a3b8;padding-left:32px}}
.agent-output{{font-size:10px;color:#94a3b8;padding:4px 0 0 32px;font-family:monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}

/* FOOTER */
.ftr{{text-align:center;color:#94a3b8;font-size:11px;margin-top:28px;padding-top:20px;border-top:1px solid #e5e7eb}}

/* RESPONSIVE */
@media(max-width:1400px){{.kpis{{grid-template-columns:repeat(3,1fr)}}.g-fleet{{grid-template-columns:1fr}}}}
@media(max-width:1000px){{.g3{{grid-template-columns:1fr}}.g2{{grid-template-columns:1fr}}.kpis{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:600px){{body{{padding:16px}}.kpis{{grid-template-columns:1fr}}}}
</style></head>
<body>

<div class="hdr">
    <div>
        <h1>Matt Anthony Photography</h1>
        <div class="hdr-sub">Business Command Center &middot; 23 Agents Active</div>
    </div>
    <div class="hdr-right">
        <div class="hdr-time">{time_str}</div>
        <div class="hdr-date">{today_str}</div>
        <div class="live"><span class="live-dot"></span>Live &middot; Refreshes 5m</div>
    </div>
</div>

<div class="kpis">
    {kpi("Revenue YTD", f"${ytd:,.0f}", f"{pct:.1f}% of $125K")}
    {kpi("Pipeline", f"${pv:,.0f}", f"{len(hot)+len(warm)+len(stale)} deals", accent="#2563eb")}
    {kpi("Monthly Target", f"${pace:,.0f}", f"{ml} months left")}
    {kpi("Outstanding", f"${tot_out:,.0f}", f"{len(outs)} unpaid", accent="#ea580c" if tot_out>500 else "")}
    {kpi("Contacts", f"{total_contacts}", f"{tagged_leads} warm leads", accent="#7c3aed")}
    {kpi("Agents", f"{ok_ct}/{len(AGENTS)}", f"{'All clear' if err_ct==0 else f'{err_ct} errors'}", accent="#059669" if err_ct==0 else "#dc2626")}
</div>

<div style="margin-bottom:16px">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px">
        <span style="font-size:12px;font-weight:600;color:#64748b">Revenue Progress</span>
        <span style="font-size:11px;color:#94a3b8">${ytd:,.0f} / $125,000</span>
    </div>
    <div class="bar"><div class="bar-fill" style="width:{bar_pct}%;background:{bar_col}"></div></div>
</div>

<div class="g3">
    <div class="card">
        <div class="card-t">📅 Today's Schedule <span class="badge">{len(cal)}</span></div>
        {ev_html}
    </div>
    <div class="card">
        <div class="card-t">🎯 Pipeline <span class="badge">${pv:,.0f}</span></div>
        <div class="sect" style="color:#059669">Hot &middot; 0-3 days</div>
        {deal_html(hot,"No hot deals")}
        <div class="sect" style="color:#ca8a04">Warm &middot; 4-7 days</div>
        {deal_html(warm,"No warm deals")}
        <div class="sect" style="color:#dc2626">Stale &middot; 7+ days</div>
        {deal_html(stale,"No stale deals")}
    </div>
    <div class="card">
        <div class="card-t">📧 Email <span class="badge">{len(inbox)} inbox &middot; {len(drafts)} drafts</span></div>
        {em_html}
    </div>
</div>

<div class="g3">
    <div class="card">
        <div class="card-t">📡 Campaigns <span class="badge">{len(reps)} replies</span></div>
        {cp_html}
    </div>
    <div class="card">
        <div class="card-t">💳 Outstanding Invoices <span class="badge">${tot_out:,.0f}</span></div>
        {ou_html}
    </div>
    <div class="card">
        <div class="card-t">⚡ Quick Stats</div>
        {"".join('<div class="hlth"><span class="hlth-dot ' + ("hlth-ok" if h["ok"] else "hlth-dn") + '"></span>' + h["n"] + '<span class="hlth-ms">' + str(h["ms"]) + 'ms</span></div>' for h in hlth)}
        <div style="margin-top:14px;padding-top:14px;border-top:1px solid #f1f5f9">
            <div class="sect">Recurring Revenue</div>
            <div style="font-size:20px;font-weight:800;color:#0f172a">$1,417<span style="font-size:14px;color:#94a3b8">.50/mo</span></div>
            <div style="font-size:11px;color:#94a3b8;margin-top:4px">Balmoral $1,260 &middot; Shala $105 &middot; Carmen $52.50</div>
        </div>
        <div style="margin-top:14px;padding-top:14px;border-top:1px solid #f1f5f9">
            <div class="sect">Monthly Burn</div>
            <div style="font-size:20px;font-weight:800;color:#ea580c">$7,200</div>
            <div style="font-size:11px;color:#94a3b8;margin-top:4px">Personal $6,580 &middot; Software ~$600</div>
        </div>
    </div>
</div>

<div class="g-fleet">
    <div class="tl-card">
        <div class="tl-title">⏰ Today's Agent Timeline</div>
        {tl_html}
    </div>
    <div class="card" style="overflow-y:auto;max-height:620px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
            <div class="card-t" style="margin-bottom:0">🤖 Agent Fleet</div>
            <div style="display:flex;gap:12px;font-size:11px;color:#94a3b8">
                <span style="display:flex;align-items:center;gap:4px"><span class="agent-dot dot-ok" style="width:6px;height:6px"></span>{ok_ct}</span>
                <span style="display:flex;align-items:center;gap:4px"><span class="agent-dot dot-idle" style="width:6px;height:6px"></span>{idle_ct}</span>
                <span style="display:flex;align-items:center;gap:4px"><span class="agent-dot dot-err" style="width:6px;height:6px"></span>{err_ct}</span>
                <span style="display:flex;align-items:center;gap:4px"><span class="agent-dot dot-pend" style="width:6px;height:6px"></span>{pend_ct}</span>
            </div>
        </div>
        {fleet_html}
    </div>
</div>

<div class="ftr">
    LOC: $16,574 at 8.94% &middot; FHSA: Open before Dec 31 &middot; Target: $125,000 &middot; Gap: ${gap:,.0f} &middot; Mac must be awake for cron
</div>

</body></html>'''


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ["/","dashboard"]:
            h = render(fetch_all())
            self.send_response(200)
            self.send_header("Content-Type","text/html;charset=utf-8")
            self.end_headers()
            self.wfile.write(h.encode())
        else:
            self.send_response(404);self.end_headers()
    def log_message(self,*a): pass

if __name__=="__main__":
    s=HTTPServer(("0.0.0.0",PORT),H)
    print(f"🖥️  Dashboard → http://localhost:{PORT}")
    try: s.serve_forever()
    except KeyboardInterrupt: s.server_close()
