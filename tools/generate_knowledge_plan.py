#!/usr/bin/env python3
"""Generate the Business Knowledge Completion Plan PDF."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime

INK = HexColor("#1A1A18")
PAPER = HexColor("#F6F4F0")
GOLD = HexColor("#C9A96E")
STONE = HexColor("#8A8579")
LIGHT_STONE = HexColor("#D9D5CD")
OFF_WHITE = HexColor("#EEECE6")
WHITE = HexColor("#FFFFFF")
GREEN = HexColor("#2D6A4F")
BLUE = HexColor("#1B4965")
RED = HexColor("#9B2226")

output_path = "/Users/matthewfernandes/Downloads/Business Knowledge Completion Plan.pdf"

doc = SimpleDocTemplate(
    output_path,
    pagesize=letter,
    topMargin=0.75*inch,
    bottomMargin=0.75*inch,
    leftMargin=0.85*inch,
    rightMargin=0.85*inch,
)

styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    'CustomTitle', parent=styles['Title'],
    fontName='Helvetica-Bold', fontSize=26, textColor=INK,
    spaceAfter=4, spaceBefore=0, leading=30
)
subtitle_style = ParagraphStyle(
    'Subtitle', parent=styles['Normal'],
    fontName='Helvetica', fontSize=11, textColor=STONE,
    spaceAfter=20, spaceBefore=2
)
section_style = ParagraphStyle(
    'Section', parent=styles['Heading1'],
    fontName='Helvetica-Bold', fontSize=16, textColor=INK,
    spaceBefore=24, spaceAfter=8, leading=20
)
milestone_style = ParagraphStyle(
    'Milestone', parent=styles['Heading2'],
    fontName='Helvetica-Bold', fontSize=13, textColor=BLUE,
    spaceBefore=18, spaceAfter=6, leading=16
)
body_style = ParagraphStyle(
    'Body', parent=styles['Normal'],
    fontName='Helvetica', fontSize=9.5, textColor=INK,
    spaceAfter=6, spaceBefore=2, leading=13
)
body_bold = ParagraphStyle(
    'BodyBold', parent=body_style,
    fontName='Helvetica-Bold'
)
bullet_style = ParagraphStyle(
    'Bullet', parent=body_style,
    leftIndent=18, bulletIndent=6, spaceAfter=3
)
sub_bullet_style = ParagraphStyle(
    'SubBullet', parent=body_style,
    leftIndent=36, bulletIndent=22, spaceAfter=2, fontSize=9
)
tag_ask = ParagraphStyle(
    'TagAsk', parent=body_style,
    fontName='Helvetica-Bold', fontSize=8, textColor=RED
)
tag_audit = ParagraphStyle(
    'TagAudit', parent=body_style,
    fontName='Helvetica-Bold', fontSize=8, textColor=GREEN
)
tag_synth = ParagraphStyle(
    'TagSynth', parent=body_style,
    fontName='Helvetica-Bold', fontSize=8, textColor=BLUE
)
footer_style = ParagraphStyle(
    'Footer', parent=styles['Normal'],
    fontName='Helvetica', fontSize=8, textColor=STONE,
    alignment=TA_CENTER
)
label_style = ParagraphStyle(
    'Label', parent=body_style,
    fontName='Helvetica-Bold', fontSize=9, textColor=GOLD,
    spaceBefore=10, spaceAfter=2
)
pct_style = ParagraphStyle(
    'Pct', parent=body_style,
    fontName='Helvetica-Bold', fontSize=11, textColor=GREEN,
    spaceBefore=0, spaceAfter=0
)

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=LIGHT_STONE, spaceBefore=6, spaceAfter=6)

def tag(text, style):
    return Paragraph(text, style)

def bullet(text, style=bullet_style):
    return Paragraph(f"• {text}", style)

def sub_bullet(text):
    return Paragraph(f"◦ {text}", sub_bullet_style)

elements = []

# ── COVER ──
elements.append(Spacer(1, 1.5*inch))
elements.append(Paragraph("Business Knowledge<br/>Completion Plan", title_style))
elements.append(Paragraph("Matt Anthony Photography — Full Operational Understanding", subtitle_style))
elements.append(hr())
elements.append(Spacer(1, 0.3*inch))

# Summary box
summary_data = [
    [Paragraph("<b>Current Coverage</b>", body_style), Paragraph("<b>Target</b>", body_style), Paragraph("<b>Milestones</b>", body_style), Paragraph("<b>Est. Sessions</b>", body_style)],
    [Paragraph("~70%", pct_style), Paragraph("100%", pct_style), Paragraph("6", pct_style), Paragraph("3–4", pct_style)],
]
summary_table = Table(summary_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
summary_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), OFF_WHITE),
    ('BACKGROUND', (0, 1), (-1, 1), WHITE),
    ('GRID', (0, 0), (-1, -1), 0.5, LIGHT_STONE),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
]))
elements.append(summary_table)

elements.append(Spacer(1, 0.4*inch))
elements.append(Paragraph("Prepared: March 23, 2026", body_style))
elements.append(Paragraph("By: Claude (WAT Framework Agent)", body_style))

elements.append(PageBreak())

# ── PAGE 2: WHAT I ALREADY KNOW ──
elements.append(Paragraph("What I Already Know", section_style))
elements.append(Paragraph("These areas are well-documented in memory and local files. No further input needed unless something has changed.", body_style))
elements.append(hr())

known_areas = [
    ("Strategy & AOS", "95%", "Pricing tiers, margin floors, quarterly rocks, capacity rules, deposit policy, discount policy, AOS rules"),
    ("Financial System", "90%", "2025 actuals ($105K), 2026 YTD ($5.7K), tax optimization ($7K saved), CCA schedules, 4 bank accounts, Google Sheets system, import tools"),
    ("Client Roster & Pipeline", "85%", "Full client list with 2025 revenue, pipeline leads (MODA, Summerhill, Noven, Stowe), reactivation targets, contact details"),
    ("Website Architecture", "95%", "72-page Squarespace rebuild, CSS prefix system, code block architecture, all gotchas documented, deployment guide, SEO roadmap"),
    ("Cold Email Pipeline", "85%", "279 builders scraped, 75 qualified, 68 Instantly-ready, email sequences, ICP routing, subject line strategy"),
    ("Marketing Strategy", "90%", "Content pillars, platform rules (IG/LinkedIn/Pinterest/Journal), hooks library, caption templates, hashtag system, repurposing chain, video strategy"),
    ("Operations Docs", "85%", "Pricing rate card, shoot checklist, delivery workflow, onboarding checklist, service agreements, contractor brief, style guide"),
    ("Competitive Landscape", "80%", "6 BC architectural photographers mapped (Ema Peter, Fyfe, Graham, Knowles, Potter, RAEF), positioning strategy"),
    ("Brand Identity", "90%", "Design system (typography, colors, CSS variables), brand voice rules, 19 portfolio projects, case study template"),
    ("Notion Structure", "80%", "Database IDs, data sources, workspace layout, client pipeline, project tracker, recovery plan structure"),
]

for area, pct, detail in known_areas:
    elements.append(bullet(f"<b>{area}</b> — <font color='#2D6A4F'>{pct}</font>", bullet_style))
    elements.append(sub_bullet(detail))

elements.append(PageBreak())

# ── PAGE 3: WHAT'S MISSING ──
elements.append(Paragraph("What's Missing", section_style))
elements.append(Paragraph("Six milestones organized from foundational (must-know) to strategic (synthesis). Each task is tagged by method:", body_style))
elements.append(Spacer(1, 4))

legend_data = [
    [Paragraph("<b><font color='#9B2226'>ASK MATT</font></b> — Only you can answer this", body_style),
     Paragraph("<b><font color='#2D6A4F'>AUDIT</font></b> — I can investigate independently", body_style),
     Paragraph("<b><font color='#1B4965'>SYNTHESIZE</font></b> — I combine info into docs", body_style)],
]
legend_table = Table(legend_data, colWidths=[2.2*inch, 2.2*inch, 2.2*inch])
legend_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), OFF_WHITE),
    ('BOX', (0, 0), (-1, -1), 0.5, LIGHT_STONE),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
]))
elements.append(legend_table)
elements.append(Spacer(1, 10))

# ── MILESTONE 1 ──
elements.append(Paragraph("Milestone 1: Business Foundation & Legal", milestone_style))
elements.append(Paragraph("The basics I need to understand your entity, liability, and compliance.", body_style))
elements.append(hr())

m1_tasks = [
    ("ASK", "Business registration — Sole proprietorship or incorporated? Business number, GST registration number, registration date"),
    ("ASK", "Accountant relationship — Who files your taxes? What do they handle vs. what you do yourself? Cost?"),
    ("ASK", "Insurance details — Business liability carrier, coverage amount, gear insurance carrier, policy renewal dates"),
    ("ASK", "Banking setup — Why 4 accounts? Any line of credit details (limit, rate, balance)? Business credit card limit?"),
    ("ASK", "Vehicle — Make, model, year, lease vs. own, monthly payment, insurance carrier"),
    ("ASK", "Personal financial position — Emergency fund/runway, any debt beyond LOC, RRSP/TFSA/FHSA balances"),
    ("ASK", "Home office — Renting a room in a shared house? Lease terms? Landlord relationship for CRA purposes"),
    ("SYNTHESIZE", "Update memory files with all foundation details → single reference document"),
]

for method, task in m1_tasks:
    color = '#9B2226' if method == 'ASK' else '#1B4965' if method == 'SYNTHESIZE' else '#2D6A4F'
    elements.append(bullet(f"<font color='{color}'>[{method}]</font> {task}"))

# ── MILESTONE 2 ──
elements.append(Spacer(1, 6))
elements.append(Paragraph("Milestone 2: Production & Equipment", milestone_style))
elements.append(Paragraph("How the actual photography work gets done — gear, workflow, team.", body_style))
elements.append(hr())

m2_tasks = [
    ("ASK", "Equipment inventory — Camera bodies (make/model), lenses (full list), drone model, lighting kit, tripod/heads, accessories"),
    ("ASK", "Gear purchase history — What was bought in 2024/2025? (Feeds CCA schedule accuracy)"),
    ("ASK", "Post-production workflow — Lightroom vs. Capture One? Presets or manual? Catalog structure?"),
    ("ASK", "Editor/contractor — Do you currently use a contracted editor? Name, rate, turnaround, quality? Or all self-edited?"),
    ("ASK", "Second shooters — Who have you used? Day rates? How often? Reliable pool?"),
    ("ASK", "Delivery specifics — Dropbox folder structure, how clients access files, any delivery platform beyond Dropbox?"),
    ("ASK", "Typical shoot day (real, not template) — What time do you arrive? How long on average? What's the actual flow?"),
    ("ASK", "Turnaround reality — Do you actually hit the 10-15 day timelines? What's the real average?"),
    ("AUDIT", "Cross-reference CCA schedule against actual gear list to verify asset tracking"),
    ("SYNTHESIZE", "Create complete equipment registry in memory + update CCA records if needed"),
]

for method, task in m2_tasks:
    color = '#9B2226' if method == 'ASK' else '#1B4965' if method == 'SYNTHESIZE' else '#2D6A4F'
    elements.append(bullet(f"<font color='{color}'>[{method}]</font> {task}"))

elements.append(PageBreak())

# ── MILESTONE 3 ──
elements.append(Paragraph("Milestone 3: Systems & Automation", milestone_style))
elements.append(Paragraph("Complete map of every tool, automation, and integration running the business.", body_style))
elements.append(hr())

m3_tasks = [
    ("AUDIT", "Full software stack audit — Map all ~35 tools with cost, purpose, usage frequency, and whether each is essential"),
    ("AUDIT", "n8n workflows — What's actually running vs. dormant? Contact form flow, any other active automations?"),
    ("AUDIT", "GHL automations — What pipelines are active? What triggers exist? Email sequences running?"),
    ("ASK", "Google Workspace usage — What's in Drive beyond finance sheets? Any shared drives with clients?"),
    ("ASK", "Dropbox structure — Folder hierarchy, shared folders with clients, storage usage, any sync issues?"),
    ("ASK", "Scheduling/calendar — How do you manage your calendar? GHL booking widget? Manual? iCal?"),
    ("ASK", "Invoicing workflow — GHL invoices → where? QuickBooks connected? How do you track payments?"),
    ("ASK", "Client communication flow — What actually happens when a lead fills out the contact form? Step by step."),
    ("AUDIT", "LeadConnector/GHL — Map all active automations, booking flows, and pipeline stages with real data"),
    ("SYNTHESIZE", "Create systems map document — every tool, every integration, every data flow"),
]

for method, task in m3_tasks:
    color = '#9B2226' if method == 'ASK' else '#1B4965' if method == 'SYNTHESIZE' else '#2D6A4F'
    elements.append(bullet(f"<font color='{color}'>[{method}]</font> {task}"))

# ── MILESTONE 4 ──
elements.append(Spacer(1, 6))
elements.append(Paragraph("Milestone 4: Marketing & Brand Presence", milestone_style))
elements.append(Paragraph("Current state of all public-facing channels and marketing performance.", body_style))
elements.append(hr())

m4_tasks = [
    ("AUDIT", "Instagram audit — Current followers, engagement rate, posting frequency, top-performing posts, last post date"),
    ("AUDIT", "LinkedIn audit — Connections, profile completeness, posting frequency, any content performance data"),
    ("ASK", "Pinterest status — Is the account active? Any boards set up? Or still planning?"),
    ("AUDIT", "Google Business Profile — Current reviews, star rating, photos uploaded, categories, posting activity"),
    ("ASK", "Paid ads — Are you currently running Google or Meta ads? Budget, targeting, results? Or paused?"),
    ("ASK", "SEO current state — Any analytics access? Google Search Console set up? Current organic traffic volume?"),
    ("ASK", "Referral tracking — Where do your clients actually come from? (Google, word of mouth, Instagram, cold email, other?)"),
    ("ASK", "Email list — Do you have a mailing list beyond cold email? Newsletter? How many subscribers?"),
    ("AUDIT", "Website performance — Run current Lighthouse/PageSpeed scores, check indexed pages in Google"),
    ("SYNTHESIZE", "Create marketing scorecard — all channels with current metrics and health status"),
]

for method, task in m4_tasks:
    color = '#9B2226' if method == 'ASK' else '#1B4965' if method == 'SYNTHESIZE' else '#2D6A4F'
    elements.append(bullet(f"<font color='{color}'>[{method}]</font> {task}"))

elements.append(PageBreak())

# ── MILESTONE 5 ──
elements.append(Paragraph("Milestone 5: Sales Process & Client Experience", milestone_style))
elements.append(Paragraph("How deals actually close and clients actually experience your service.", body_style))
elements.append(hr())

m5_tasks = [
    ("ASK", "Discovery call flow — What do you actually ask? How long? Phone or video? Any script or just conversational?"),
    ("ASK", "Proposal process — Do you use GHL proposals? A PDF? How long from call to proposal sent?"),
    ("ASK", "Close rate — Of the last 10-20 leads, how many became paying clients? Biggest reasons for losing deals?"),
    ("ASK", "Client feedback — Any formal feedback process? NPS? Or just informal conversation?"),
    ("ASK", "Repeat client patterns — What triggers a client to come back? How many are repeat vs. one-time?"),
    ("ASK", "Award submissions — Which awards have you entered? Results? Who handles submissions — you or clients?"),
    ("ASK", "Georgie Awards May 23-25 — What's your plan? Attending? Entering work? Networking strategy?"),
    ("ASK", "Cost-share reality — How often do you actually close cost-share deals? Any examples of it working?"),
    ("ASK", "Balmoral retainer details — What exactly do you deliver monthly for the $367.50 web + $892.50 SEO retainers?"),
    ("SYNTHESIZE", "Document the real sales funnel with conversion rates at each stage"),
]

for method, task in m5_tasks:
    color = '#9B2226' if method == 'ASK' else '#1B4965' if method == 'SYNTHESIZE' else '#2D6A4F'
    elements.append(bullet(f"<font color='{color}'>[{method}]</font> {task}"))

# ── MILESTONE 6 ──
elements.append(Spacer(1, 6))
elements.append(Paragraph("Milestone 6: Strategic Reconciliation & Living Document", milestone_style))
elements.append(Paragraph("Sync all information, resolve conflicts, and create a single source of truth.", body_style))
elements.append(hr())

m6_tasks = [
    ("ASK", "Revenue target — Notion shows $125K (revised March 21) but AOS docs show $172.9K. Which is the real target? What changed?"),
    ("AUDIT", "Read the full March 21 Recovery Game Plan in Notion — understand the revised strategy"),
    ("AUDIT", "Read Q2/Q3/Q4 rocks pages in Notion — compare against AOS quarterly themes"),
    ("AUDIT", "Reconcile Notion client pipeline against memory records — find any mismatches"),
    ("ASK", "Biggest current worry — What keeps you up at night about the business right now?"),
    ("ASK", "2027 vision — Where do you want to be in 12 months? Hire? Incorporate? Revenue target?"),
    ("SYNTHESIZE", "Update all memory files with corrected/current information"),
    ("SYNTHESIZE", "Create 'Business Bible' master page in Notion — single source of truth linking every system"),
    ("SYNTHESIZE", "Update CLAUDE.md with any new operational rules or context discovered"),
]

for method, task in m6_tasks:
    color = '#9B2226' if method == 'ASK' else '#1B4965' if method == 'SYNTHESIZE' else '#2D6A4F'
    elements.append(bullet(f"<font color='{color}'>[{method}]</font> {task}"))

elements.append(PageBreak())

# ── EXECUTION PLAN ──
elements.append(Paragraph("Execution Plan", section_style))
elements.append(Paragraph("How we get from 70% to 100% in 3-4 focused sessions.", body_style))
elements.append(hr())

sessions = [
    ("Session 1: Foundation + Production", "~45 min conversation",
     "Milestones 1 & 2. I'll ask you 15-18 questions about your business entity, equipment, and production workflow. Bring: gear list if you have one, insurance policy details, accountant contact info."),
    ("Session 2: Systems + Marketing", "~30 min conversation + independent audit",
     "Milestone 3 & 4. Quick Q&A on tools and marketing channels, then I run independent audits on your social profiles, GBP, website performance, GHL, and n8n. You can leave me to work."),
    ("Session 3: Sales + Strategic Sync", "~45 min conversation",
     "Milestones 5 & 6. Deep dive on your real sales process, client experience, and strategic direction. We reconcile the $125K vs $172.9K target and align on 2027 vision."),
    ("Session 4: Synthesis & Delivery", "Independent — no input needed",
     "I compile everything into updated memory files, build the Business Bible in Notion, update CLAUDE.md, and verify 100% coverage. You review and confirm."),
]

for name, duration, desc in sessions:
    elements.append(Paragraph(f"<b>{name}</b>  <font color='#8A8579'>({duration})</font>", body_bold))
    elements.append(Paragraph(desc, body_style))
    elements.append(Spacer(1, 6))

elements.append(hr())
elements.append(Spacer(1, 8))

# Summary table
elements.append(Paragraph("Milestone Summary", label_style))
summary_data2 = [
    [Paragraph("<b>Milestone</b>", body_style), Paragraph("<b>Tasks</b>", body_style), Paragraph("<b>Ask Matt</b>", body_style), Paragraph("<b>Audit</b>", body_style), Paragraph("<b>Synthesize</b>", body_style), Paragraph("<b>Session</b>", body_style)],
    [Paragraph("1. Foundation & Legal", body_style), Paragraph("8", body_style), Paragraph("7", body_style), Paragraph("0", body_style), Paragraph("1", body_style), Paragraph("1", body_style)],
    [Paragraph("2. Production & Equipment", body_style), Paragraph("10", body_style), Paragraph("8", body_style), Paragraph("1", body_style), Paragraph("1", body_style), Paragraph("1", body_style)],
    [Paragraph("3. Systems & Automation", body_style), Paragraph("10", body_style), Paragraph("4", body_style), Paragraph("4", body_style), Paragraph("2", body_style), Paragraph("2", body_style)],
    [Paragraph("4. Marketing & Brand", body_style), Paragraph("10", body_style), Paragraph("4", body_style), Paragraph("4", body_style), Paragraph("2", body_style), Paragraph("2", body_style)],
    [Paragraph("5. Sales & Client Exp.", body_style), Paragraph("10", body_style), Paragraph("9", body_style), Paragraph("0", body_style), Paragraph("1", body_style), Paragraph("3", body_style)],
    [Paragraph("6. Strategic Reconciliation", body_style), Paragraph("9", body_style), Paragraph("3", body_style), Paragraph("3", body_style), Paragraph("3", body_style), Paragraph("3+4", body_style)],
    [Paragraph("<b>TOTAL</b>", body_bold), Paragraph("<b>57</b>", body_bold), Paragraph("<b>35</b>", body_bold), Paragraph("<b>12</b>", body_bold), Paragraph("<b>10</b>", body_bold), Paragraph("", body_style)],
]
summary_table2 = Table(summary_data2, colWidths=[2.0*inch, 0.7*inch, 0.9*inch, 0.7*inch, 0.9*inch, 0.8*inch])
summary_table2.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), INK),
    ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
    ('BACKGROUND', (0, -1), (-1, -1), OFF_WHITE),
    ('GRID', (0, 0), (-1, -1), 0.5, LIGHT_STONE),
    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('LEFTPADDING', (0, 0), (0, -1), 8),
    ('ROWBACKGROUNDS', (0, 1), (-1, -2), [WHITE, OFF_WHITE]),
]))
elements.append(summary_table2)

elements.append(Spacer(1, 0.4*inch))
elements.append(Paragraph("After all 4 sessions, every aspect of Matt Anthony Photography — entity, production, systems, marketing, sales, and strategy — will be fully documented in Claude's memory system with live links to Notion, Google Sheets, and all operational tools.", body_style))

elements.append(Spacer(1, 0.5*inch))
elements.append(hr())
elements.append(Paragraph("Prepared by Claude (WAT Framework) for Matt Anthony Photography", footer_style))
elements.append(Paragraph(f"Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))

doc.build(elements)
print(f"PDF saved to: {output_path}")
