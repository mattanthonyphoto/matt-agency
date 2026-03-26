#!/usr/bin/env python3
"""Generate the SEO Meta Audit & Fix Checklist PDF for mattanthonyphoto.com."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime

# Brand colors
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
LIGHT_RED = HexColor("#F2E0E0")
LIGHT_GREEN = HexColor("#E0F0E8")
LIGHT_GOLD = HexColor("#F5EFE0")

output_path = "/Users/matthewfernandes/Downloads/SEO Meta Audit - mattanthonyphoto.com.pdf"

doc = SimpleDocTemplate(
    output_path,
    pagesize=letter,
    topMargin=0.75*inch,
    bottomMargin=0.75*inch,
    leftMargin=0.75*inch,
    rightMargin=0.75*inch,
)

styles = getSampleStyleSheet()
usable = letter[0] - 1.5*inch

# Styles
title_style = ParagraphStyle(
    'CustomTitle', parent=styles['Title'],
    fontName='Helvetica-Bold', fontSize=24, textColor=INK,
    spaceAfter=4, spaceBefore=0, leading=28
)
subtitle_style = ParagraphStyle(
    'Subtitle', parent=styles['Normal'],
    fontName='Helvetica', fontSize=11, textColor=STONE,
    spaceAfter=6, spaceBefore=2
)
section_style = ParagraphStyle(
    'Section', parent=styles['Heading1'],
    fontName='Helvetica-Bold', fontSize=16, textColor=INK,
    spaceBefore=20, spaceAfter=8, leading=20
)
subsection_style = ParagraphStyle(
    'Subsection', parent=styles['Heading2'],
    fontName='Helvetica-Bold', fontSize=12, textColor=BLUE,
    spaceBefore=14, spaceAfter=6, leading=15
)
body_style = ParagraphStyle(
    'Body', parent=styles['Normal'],
    fontName='Helvetica', fontSize=9, textColor=INK,
    spaceAfter=4, spaceBefore=2, leading=12
)
body_bold = ParagraphStyle(
    'BodyBold', parent=body_style,
    fontName='Helvetica-Bold'
)
small_style = ParagraphStyle(
    'Small', parent=body_style,
    fontSize=8, textColor=STONE, leading=10
)
label_style = ParagraphStyle(
    'Label', parent=body_style,
    fontName='Helvetica-Bold', fontSize=8, textColor=STONE,
    spaceAfter=1, spaceBefore=6
)
code_style = ParagraphStyle(
    'Code', parent=body_style,
    fontName='Courier', fontSize=8, textColor=INK,
    backColor=OFF_WHITE, leading=11, spaceBefore=2, spaceAfter=2,
    leftIndent=6, rightIndent=6
)
tag_critical = ParagraphStyle(
    'TagCritical', parent=body_style,
    fontName='Helvetica-Bold', fontSize=8, textColor=RED
)
tag_done = ParagraphStyle(
    'TagDone', parent=body_style,
    fontName='Helvetica-Bold', fontSize=8, textColor=GREEN
)
checkbox_style = ParagraphStyle(
    'Checkbox', parent=body_style,
    fontName='Helvetica', fontSize=9, textColor=INK,
    leftIndent=18, spaceBefore=1, spaceAfter=1
)

elements = []


def add_hr(color=GOLD, width=1):
    elements.append(HRFlowable(width="100%", thickness=width, color=color, spaceAfter=8, spaceBefore=8))


def add_spacer(h=8):
    elements.append(Spacer(1, h))


def page_block(slug, current_title, new_title, current_desc, new_desc, priority="fix", notes=None):
    """Generate a single page audit block with checkbox."""
    rows = []

    # Page URL with checkbox
    checkbox = "\u2610"  # empty checkbox
    rows.append(Paragraph(f"<b>{checkbox}  /{slug}</b>", body_bold))

    if priority == "critical":
        rows.append(Paragraph("CRITICAL", tag_critical))

    # Title
    if new_title:
        rows.append(Paragraph("TITLE", label_style))
        if current_title:
            rows.append(Paragraph(f"<font color='#9B2226'><strike>{current_title}</strike></font>", small_style))
        rows.append(Paragraph(f"<font color='#2D6A4F'>{new_title}</font>", code_style))

    # Meta description
    if new_desc:
        rows.append(Paragraph("META DESCRIPTION", label_style))
        if current_desc and current_desc != "MISSING" and len(current_desc) > 20:
            rows.append(Paragraph(f"<font color='#9B2226'><strike>{current_desc}</strike></font>", small_style))
        elif current_desc == "MISSING":
            rows.append(Paragraph("<font color='#9B2226'>Currently: MISSING</font>", small_style))
        rows.append(Paragraph(f"<font color='#2D6A4F'>{new_desc}</font>", code_style))

    if notes:
        rows.append(Paragraph(f"<i>{notes}</i>", small_style))

    add_spacer(2)
    elements.append(KeepTogether(rows))
    add_spacer(6)
    elements.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_STONE, spaceAfter=4, spaceBefore=0))


# ============================================================
# COVER PAGE
# ============================================================
add_spacer(100)
elements.append(Paragraph("SEO Meta Audit", title_style))
elements.append(Paragraph("& Fix Checklist", title_style))
add_spacer(8)
add_hr(GOLD, 2)
add_spacer(8)
elements.append(Paragraph("mattanthonyphoto.com", ParagraphStyle(
    'URL', parent=subtitle_style, fontSize=14, textColor=GOLD
)))
elements.append(Paragraph(f"Generated {datetime.now().strftime('%B %d, %Y')}", subtitle_style))
add_spacer(30)

# Summary stats
summary_data = [
    ["76", "Pages Audited"],
    ["38", "Missing Meta Descriptions"],
    ["7", "Missing/Wrong Titles"],
    ["11", "Critical Fixes"],
    ["2", "Pages to Delete/Noindex"],
]
for val, label in summary_data:
    elements.append(Paragraph(f"<b>{val}</b>  {label}", ParagraphStyle(
        'Stat', parent=body_style, fontSize=12, spaceBefore=6, spaceAfter=2
    )))

add_spacer(40)
elements.append(Paragraph("Work through each section in order. Check off each page as you update it in Squarespace.", body_style))
elements.append(Paragraph("Pages are grouped by priority: critical fixes first, then by section.", body_style))

elements.append(PageBreak())


# ============================================================
# SECTION 1: CRITICAL FIXES
# ============================================================
elements.append(Paragraph("1. Critical Fixes", section_style))
elements.append(Paragraph("These are actively hurting your SEO right now. Fix these first.", body_style))
add_hr()

page_block(
    "okanagan-architectural-photographer",
    "Architectural Photographer in Pemberton, BC | Matt Anthony",
    "Architectural Photographer in the Okanagan | Matt Anthony",
    "MISSING",
    "Architectural and interior photography for custom homes across the Okanagan. Kelowna, Vernon, Penticton, and beyond. Book a discovery call with Matt Anthony.",
    priority="critical",
    notes="Title currently says PEMBERTON instead of Okanagan. Copy-paste error."
)

page_block(
    "journal/georgie-awards-guide",
    "How to Build a Visual Library for Your Business",
    "The Complete Guide to the Georgie Awards",
    "MISSING",
    "Everything you need to know about entering the Georgie Awards -- categories, deadlines, judging criteria, and how to prepare photography that wins.",
    priority="critical",
    notes="Title is duplicated from the visual library post. Wrong page entirely."
)

page_block(
    "journal/roi-professional-architectural-photography-builders",
    None,
    "The ROI of Architectural Photography for Builders",
    "MISSING",
    "How professional architectural photography drives leads, wins awards, and builds brand equity for custom home builders. A breakdown of the real return.",
    priority="critical",
    notes="Title tag is completely missing. Google is auto-generating."
)

page_block(
    "journal/documenting-design-intent-photography-before-build-finished",
    None,
    "Why Great Photography Starts Before the Build Finishes",
    "MISSING",
    "The best architectural photography captures design intent throughout construction -- not just the final reveal. How to plan shoots that tell the full story.",
    priority="critical",
    notes="Title tag is completely missing."
)

page_block(
    "journal/construction-lifestyle-photography-best-social-media-investment-builders",
    None,
    "Construction Lifestyle Photography for Builders",
    "MISSING",
    "Why construction lifestyle photography is the highest-ROI social media investment for custom builders. Real content that builds trust and attracts clients.",
    priority="critical",
    notes="Title tag is completely missing."
)

page_block(
    "journal/aibc-awards-guide",
    None,
    "AIBC Architectural Awards of Excellence | Guide",
    "MISSING",
    "A complete guide to the AIBC Awards of Excellence -- eligibility, submission requirements, judging criteria, and tips for preparing standout photography.",
    priority="critical",
    notes="Title tag is completely missing."
)

page_block(
    "journal/chba-national-awards-guide",
    None,
    "CHBA National Awards for Housing Excellence | Guide",
    "MISSING",
    "Everything you need to enter the CHBA National Awards -- categories, deadlines, and how to prepare project photography that meets national judging standards.",
    priority="critical",
    notes="Title tag is completely missing."
)

page_block(
    "journal/havan-awards-guide",
    None,
    "The Complete Guide to the HAVAN Awards",
    "MISSING",
    "A full breakdown of the HAVAN Awards -- eligibility, categories, submission tips, and how professional photography can strengthen your entry.",
    priority="critical",
    notes="Title tag is completely missing."
)

page_block(
    "gallery-1",
    "Gallery",
    "Architectural Photography Gallery | Matt Anthony",
    "MISSING",
    "Browse architectural, interior, and construction photography across British Columbia. Custom homes, commercial builds, and renovations by Matt Anthony.",
    priority="critical",
    notes="Title is a single generic word. Meta description completely missing."
)

page_block(
    "services",
    "Services | Discover Expert Photography Services",
    "Architectural Photography Services | Matt Anthony",
    None,
    "Full-scope architectural photography for builders, architects, and designers in BC. Project shoots, construction content, team headshots, and creative retainers.",
    priority="critical",
    notes="Title is generic template text. Doesn't mention 'architectural'."
)

elements.append(Paragraph("\u2610  Delete /services/project-one-f5w4d-absrg", body_bold))
elements.append(Paragraph("Squarespace placeholder page with junk URL slug. Remove or set to noindex.", small_style))
add_spacer(8)
elements.append(Paragraph("\u2610  Noindex /pricing-guide-thank-you", body_bold))
elements.append(Paragraph("Thank-you pages should not appear in search results. Set to 'Hide from search' in Squarespace.", small_style))

elements.append(PageBreak())

# ============================================================
# SECTION 2: LOCATION PAGES
# ============================================================
elements.append(Paragraph("2. Location Pages", section_style))
elements.append(Paragraph("All 7 location pages are missing meta descriptions. These are your local SEO workhorses.", body_style))
add_hr()

page_block(
    "squamish-architectural-photography",
    None,
    None,
    "MISSING",
    "Architectural and interior photography based in Squamish. Documenting custom homes, renovations, and commercial builds in the Sea-to-Sky corridor. Book a call.",
    notes="Title is good. Just add the meta description."
)

page_block(
    "whistler-architectural-photography",
    None,
    None,
    "MISSING",
    "Architectural photography for Whistler's custom homes, ski chalets, and alpine builds. Experienced with mountain light, snow conditions, and resort timelines.",
    notes="Title is good. Just add the meta description."
)

page_block(
    "vancouver-architectural-photographer",
    None,
    None,
    "MISSING",
    "Architectural and interior photography for Vancouver builders, architects, and designers. Modern homes, commercial spaces, and renovations. Book a discovery call.",
    notes="Title is good. Just add the meta description. Most competitive market."
)

page_block(
    "sunshine-coast-photography",
    "Architectural Photographer -- Sunshine Coast BC | Matt Anthony",
    "Architectural Photographer in Sunshine Coast, BC | Matt Anthony",
    "MISSING",
    "Architectural photography for the Sunshine Coast -- Sechelt, Gibsons, Roberts Creek, and Powell River. Custom homes, waterfront builds, and coastal retreats.",
    notes="Also standardize the title separator from em dash to 'in'."
)

page_block(
    "pemberton-photography",
    None,
    None,
    "MISSING",
    "Architectural photography in Pemberton and the Lillooet Valley. Custom homes framed by Mount Currie and the Coast Mountains. Book a shoot with Matt Anthony.",
    notes="Title is good. Just add the meta description."
)

page_block(
    "fraser-valley-photography",
    "Architectural Photographer -- Fraser Valley BC | Matt Anthony",
    "Architectural Photographer in Fraser Valley, BC | Matt Anthony",
    "MISSING",
    "Architectural and interior photography across the Fraser Valley -- Langley, Abbotsford, Chilliwack, and Mission. Custom homes, commercial, and multi-family builds.",
    notes="Also standardize the title separator from em dash to 'in'."
)

elements.append(PageBreak())

# ============================================================
# SECTION 3: JOURNAL PAGES
# ============================================================
elements.append(Paragraph("3. Journal Pages", section_style))
elements.append(Paragraph("All 23 journal pages are missing meta descriptions. The ones with title fixes are in the critical section above.", body_style))
add_hr()

journal_pages = [
    ("journal/how-to-photograph-your-project-for-award-submissions",
     None, None,
     "A guide to planning architectural photography specifically for award submissions -- timing, styling, shot lists, and what judges actually look for."),

    ("journal/what-architects-should-look-for-hiring-photographer",
     "What Architects Should Look for in a Photographer",
     "What Architects Should Look for in an Architectural Photographer",
     "How to evaluate and hire an architectural photographer -- portfolio red flags, questions to ask, pricing models, and what separates project photography from real estate."),

    ("journal/architectural-photography-whistler-mountain-projects",
     None, None,
     "What makes Whistler architectural photography unique -- mountain light, snow loads, alpine access, seasonal timing, and how to get the best results from your shoot."),

    ("journal/summerhill-fine-homes-visual-brand-ongoing-photography",
     "Summerhill Fine Homes: Building a Visual Brand",
     "Summerhill Fine Homes: Building a Visual Brand Through Photography",
     "How Summerhill Fine Homes built a cohesive visual brand through ongoing architectural photography -- from project shoots to team content and award submissions."),

    ("journal/why-your-award-submission-photos-arent-working",
     None, None,
     "Common mistakes in award submission photography -- wrong angles, bad staging, poor lighting, and missing context. How to fix your images before the next deadline."),

    ("journal/how-to-prepare-project-architectural-photo-shoot",
     "How to Prepare Your Project for a Photo Shoot - Matt Anthony Photography",
     "How to Prepare Your Project for an Architectural Photo Shoot",
     "A step-by-step checklist for preparing your build for an architectural photo shoot -- staging, cleaning, landscaping, lighting, and timing for the best results."),

    ("journal/project-photography-vs-real-estate-photography",
     None, None,
     "Why project photography and real estate photography are fundamentally different -- approach, equipment, intent, and the results each delivers for your business."),

    ("journal/seasonal-considerations-architectural-photography-bc",
     None, None,
     "How BC's seasons affect architectural photography -- optimal windows for exteriors, snow considerations, golden hour shifts, and when to schedule your shoot."),

    ("journal/behind-the-shoot-the-perch-sunshine-coast",
     None, None,
     "A behind-the-scenes look at photographing The Perch -- a contemporary Sunshine Coast home by Michel Laflamme Architect and Summerhill Fine Homes."),

    ("journal/5-details-make-or-break-architectural-interior-photography",
     "5 Details That Make or Break Interior Photography",
     "5 Details That Make or Break Architectural Interior Photography",
     "The small details that separate good interior photography from great -- reflections, sight lines, colour casts, styling, and natural vs artificial light."),

    ("journal/what-georgie-award-judges-look-for-submission-photography",
     None, None,
     "What Georgie Award judges actually evaluate in submission photography -- composition, context, consistency, and the specific shots that strengthen your entry."),

    ("journal/how-to-build-visual-library-website-proposals-awards",
     "How to Build a Visual Library for Your Business",
     "How to Build a Visual Library for Your Website, Proposals, and Awards",
     "A strategy for building a visual library that works across your website, proposals, and award submissions -- so every project you shoot keeps working for you."),

    ("journal/dezeen-submissions-guide",
     "How to Get Published on Dezeen | Submission Guide for Architects",
     "How to Get Published on Dezeen | Guide for Architects",
     "A practical guide to getting your project published on Dezeen -- what editors look for, photography standards, submission process, and common mistakes to avoid."),

    ("journal/dwell-submissions-guide",
     None, None,
     "How to submit your project to Dwell Magazine -- editorial preferences, photography requirements, and tips for making your submission stand out from the pile."),

    ("journal/raic-awards-guide",
     None, None,
     "A guide to the RAIC Awards and Governor General's Medals in Architecture -- eligibility, categories, submission tips, and photography that supports your entry."),

    ("journal/western-living-submissions",
     None, None,
     "How to get your project into Western Living Magazine -- what editors look for, photography standards, and how to pitch residential and interior design projects."),
]

for slug, old_title, new_title, new_desc in journal_pages:
    page_block(slug, old_title, new_title, "MISSING", new_desc)

elements.append(PageBreak())

# ============================================================
# SECTION 4: PROJECT PAGES - STUB FIXES
# ============================================================
elements.append(Paragraph("4. Project Pages -- Stub Descriptions", section_style))
elements.append(Paragraph("These 3 project pages have placeholder meta descriptions under 60 characters.", body_style))
add_hr()

page_block(
    "sitelines-architecture",
    "Sitelines Architecture | Photography Case Study - Matt Anthony Photography",
    "Sitelines Architecture | Fraser Valley Photography Case Study",
    "Documenting Sitelines Architecture",
    "Ongoing architectural photography for Sitelines Architecture -- documenting residential and commercial projects across the Fraser Valley and Abbotsford, BC.",
)

page_block(
    "the-window-merchant",
    "The Window Merchant | Content Retainer Case Study",
    "The Window Merchant | Content Retainer Case Study | Matt Anthony",
    "How a creative retainer transformed The Window Merchant",
    "How a creative photography retainer transformed The Window Merchant's brand -- ongoing product, lifestyle, and team content that drives sales and builds trust.",
)

page_block(
    "eagle-residence",
    None,
    None,
    "5,000 sq ft insulated concrete home in Pemberton",
    "5,000 sq ft insulated concrete home in Pemberton by Balmoral Construction. Mountain views, clean lines, and durable alpine design photographed inside and out.",
)

elements.append(PageBreak())

# ============================================================
# SECTION 5: CORE PAGES
# ============================================================
elements.append(Paragraph("5. Core Pages -- Trims & Fixes", section_style))
elements.append(Paragraph("These pages mostly need meta descriptions trimmed to 150-160 characters or minor title fixes.", body_style))
add_hr()

page_block(
    "home",
    "Architectural Photographer in Vancouver, Squamish, Whistler  & BC",
    "Architectural Photographer in Vancouver, Squamish, Whistler & BC",
    None,
    "Architectural and interior photography for architects, builders, and designers across British Columbia. Honest imagery that honours design intent. Book a call.",
    notes="Fix double space before '&' in title. Trim description to 160 chars."
)

page_block(
    "bio",
    None, None, None,
    "Meet Matt Anthony -- BC architectural photographer and certified drone pilot. Documenting custom homes, interiors, and commercial spaces across the Sea-to-Sky.",
    notes="Trim description from 176 to 160 chars."
)

page_block(
    "faqs",
    None, None, None,
    "Answers to common questions about architectural photography -- scheduling, staging, drone coverage, turnaround, pricing, and service areas across BC.",
    notes="Trim description from 166 to under 160."
)

page_block(
    "projects",
    None, None, None,
    "Architectural and interior photography projects across Whistler, Pemberton, Sunshine Coast, and Vancouver. Custom homes, commercial builds, and award-winning work.",
    notes="Trim description. Remove hardcoded '19 projects' which will go stale."
)

page_block(
    "process",
    None, None, None,
    "A structured photography process from discovery call to gallery delivery. Learn how we plan, shoot, and deliver architectural imagery that serves your goals.",
    notes="Trim from 167 to under 160."
)

page_block(
    "award-publication-imagery",
    "Award Submission Photography | Georgie & CHBA Ready - Matt Anthony Photography",
    "Award Submission Photography | Georgie & CHBA Ready",
    None, None,
    notes="Title is 78 chars. Trim by removing ' - Matt Anthony Photography'. Description is fine at 159."
)

page_block(
    "project-intake-form",
    "Project Intake Form",
    "Project Intake Form | Matt Anthony Photography",
    "Project Intake Form",
    "Submit your architectural photography project details. Service areas include Whistler, Squamish, Vancouver, Sunshine Coast, and across British Columbia.",
    notes="All metadata is a bare placeholder."
)

page_block(
    "pricing-guide-landing",
    "Pricing Guide",
    "Architectural Photography Pricing Guide | Matt Anthony",
    "Pricing Guide",
    "Download the architectural photography pricing guide. Transparent rates for project shoots, creative retainers, and award-ready imagery across BC.",
    notes="All metadata is a bare placeholder."
)

page_block(
    "project-photography",
    None, None, None,
    "Complete visual documentation of your finished build -- exteriors, interiors, aerial, and twilight. Serving architects and builders across British Columbia.",
    notes="Add location reference to existing description."
)

page_block(
    "construction-team-content",
    "Construction Lifestyle Photography for Builders - Matt Anthony Photography",
    "Construction Team Content for Builders | Matt Anthony",
    None,
    "Behind-the-scenes construction content, team portraits, and jobsite storytelling for builders across BC. Build your brand with authentic visual content.",
    notes="Title too long (74 chars). Description is currently the title copy-pasted."
)

page_block(
    "architectural-photography-for-publications",
    "Architectural Photography for Awards & Publications",
    "Architectural Photography for Awards & Publications | Matt Anthony",
    "Architectural Photography for Awards & Publications",
    "Photography composed for editorial features, design publications, and award submissions. Meeting the visual standards of Dezeen, Dwell, Western Living, and more.",
    notes="All 5 meta fields are currently identical text. Add brand to title, write real description."
)

elements.append(PageBreak())

# ============================================================
# SECTION 6: SERVICE SUBPAGES
# ============================================================
elements.append(Paragraph("6. Service Subpages -- Trim Descriptions", section_style))
elements.append(Paragraph("These pages have good content but meta descriptions are 170-180 chars. Trim to 160.", body_style))
add_hr()

page_block(
    "services/architectural-interiors-photography",
    None, None, None,
    "Architectural and interior photography across BC. Residential, commercial, and high-end design spaces documented with precision. Book a shoot with Matt Anthony.",
    notes="Trim from 177 to 160."
)

page_block(
    "services/construction-lifestyle-photography",
    None, None, None,
    "Construction and lifestyle photography across BC. On-site progress, team dynamics, and built environments captured with creative storytelling. Matt Anthony.",
    notes="Trim from 175 to 160."
)

page_block(
    "services/jobsite-progression-photography",
    None, None, None,
    "Jobsite progression photography across BC. Documenting construction milestones, safety compliance, and team progress from foundation to finishing. Matt Anthony.",
    notes="Trim from 180 to 160."
)

page_block(
    "services/team-headshots-photography",
    None, None, None,
    "Team and headshot photography across BC. Polished corporate portraits and authentic workplace branding with expert lighting. Book with Matt Anthony.",
    notes="Trim from 175 to 160."
)

elements.append(PageBreak())

# ============================================================
# SECTION 7: SITEMAP CLEANUP
# ============================================================
elements.append(Paragraph("7. Sitemap & Housekeeping", section_style))
add_hr()

housekeeping = [
    "\u2610  Update sitemap: replace /pitt-meadows-residence with /osprey (301 redirect is live)",
    "\u2610  Remove /services/project-one-f5w4d-absrg from sitemap after deleting",
    "\u2610  Remove /pricing-guide-thank-you from sitemap after noindexing",
    "\u2610  Resubmit sitemap in Google Search Console after all changes",
    "\u2610  Check Google Search Console in 7 days to verify new pages indexing",
]
for item in housekeeping:
    elements.append(Paragraph(item, checkbox_style))
    add_spacer(4)

add_spacer(20)

# Quick reference: what good looks like
elements.append(Paragraph("Quick Reference", subsection_style))
add_spacer(4)

ref_data = [
    ["Element", "Target", "Example"],
    ["Title tag", "Under 60 chars", "Architectural Photographer in Whistler, BC | Matt Anthony"],
    ["Meta description", "150-160 chars", "Architectural photography for Whistler's custom homes..."],
    ["Separator", "Use | consistently", "Page Name | Matt Anthony"],
    ["H1 tag", "Include primary keyword", "Architectural Photography in Whistler, BC"],
    ["og:title", "Match title tag", "(Squarespace auto-fills from SEO title)"],
    ["og:description", "Match meta desc", "(Squarespace auto-fills from SEO description)"],
]

ref_table = Table(ref_data, colWidths=[usable*0.18, usable*0.22, usable*0.60])
ref_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), GOLD),
    ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('BACKGROUND', (0, 1), (-1, -1), OFF_WHITE),
    ('GRID', (0, 0), (-1, -1), 0.5, LIGHT_STONE),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [OFF_WHITE, WHITE]),
]))
elements.append(ref_table)

add_spacer(30)
add_hr(GOLD, 2)
add_spacer(8)
elements.append(Paragraph("Generated by Claude Code for Matt Anthony Photography", ParagraphStyle(
    'Footer', parent=small_style, alignment=TA_CENTER, textColor=STONE
)))
elements.append(Paragraph(f"{datetime.now().strftime('%B %d, %Y')}", ParagraphStyle(
    'FooterDate', parent=small_style, alignment=TA_CENTER, textColor=LIGHT_STONE
)))


# Build
doc.build(elements)
print(f"PDF generated: {output_path}")
