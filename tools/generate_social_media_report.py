"""
Generate Social Media System PDF report for Matt Anthony Photography.
Uses the same brand styling as the site audit PDF.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable
import os
from datetime import datetime


# Brand colors
INK = HexColor("#1A1A18")
PAPER = HexColor("#F6F4F0")
GOLD = HexColor("#C9A96E")
STONE = HexColor("#8A8579")
LIGHT_STONE = HexColor("#D9D5CD")
OFF_WHITE = HexColor("#EEECE6")
WARM_MUTED = HexColor("#B8975A")
GREEN = HexColor("#27864A")
BLUE = HexColor("#2C5F8A")


class GoldLine(Flowable):
    """A thin gold horizontal line."""
    def __init__(self, width, thickness=1):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness

    def draw(self):
        self.canv.setStrokeColor(GOLD)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    usable_width = letter[0] - 1.5 * inch

    # Custom styles
    s_cover_title = ParagraphStyle(
        "CoverTitle", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=28, leading=34,
        textColor=INK, alignment=TA_LEFT, spaceAfter=6,
    )
    s_cover_sub = ParagraphStyle(
        "CoverSub", parent=styles["Normal"],
        fontName="Helvetica", fontSize=13, leading=18,
        textColor=STONE, alignment=TA_LEFT, spaceAfter=4,
    )
    s_h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"],
        fontName="Helvetica-Bold", fontSize=20, leading=26,
        textColor=INK, spaceBefore=24, spaceAfter=10,
    )
    s_h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=14, leading=19,
        textColor=INK, spaceBefore=16, spaceAfter=6,
    )
    s_h3 = ParagraphStyle(
        "H3", parent=styles["Heading3"],
        fontName="Helvetica-Bold", fontSize=11, leading=15,
        textColor=WARM_MUTED, spaceBefore=12, spaceAfter=4,
    )
    s_body = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9.5, leading=14,
        textColor=INK, spaceAfter=6,
    )
    s_body_bold = ParagraphStyle(
        "BodyBold", parent=s_body,
        fontName="Helvetica-Bold",
    )
    s_bullet = ParagraphStyle(
        "Bullet", parent=s_body,
        leftIndent=18, bulletIndent=6,
        spaceAfter=3,
    )
    s_small = ParagraphStyle(
        "Small", parent=s_body,
        fontSize=8, leading=11, textColor=STONE,
    )
    s_gold_label = ParagraphStyle(
        "GoldLabel", parent=s_body,
        fontName="Helvetica-Bold", fontSize=9, textColor=GOLD,
        spaceBefore=10, spaceAfter=2,
    )
    s_table_header = ParagraphStyle(
        "TableHeader", parent=s_body,
        fontName="Helvetica-Bold", fontSize=8.5, leading=11,
        textColor=white,
    )
    s_table_cell = ParagraphStyle(
        "TableCell", parent=s_body,
        fontSize=8.5, leading=11, textColor=INK,
    )
    s_table_cell_bold = ParagraphStyle(
        "TableCellBold", parent=s_table_cell,
        fontName="Helvetica-Bold",
    )
    s_code = ParagraphStyle(
        "Code", parent=s_body,
        fontName="Courier", fontSize=8, leading=11,
        textColor=INK, leftIndent=12, backColor=OFF_WHITE,
        spaceBefore=4, spaceAfter=4,
    )

    def make_table(headers, rows, col_widths=None):
        """Build a styled table."""
        header_cells = [Paragraph(h, s_table_header) for h in headers]
        data = [header_cells]
        for row in rows:
            data.append([Paragraph(str(c), s_table_cell) for c in row])

        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INK),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8.5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, OFF_WHITE]),
            ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_STONE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ]))
        return t

    story = []

    # ── COVER PAGE ──────────────────────────────────────────

    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("Social Media<br/>Management System", s_cover_title))
    story.append(Spacer(1, 8))
    story.append(GoldLine(usable_width * 0.4, 2))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Matt Anthony Photography", s_cover_sub))
    story.append(Paragraph("System Report &amp; Activation Guide", s_cover_sub))
    story.append(Paragraph(f"Prepared {datetime.now().strftime('%B %d, %Y')}", s_cover_sub))
    story.append(Spacer(1, 1.5 * inch))

    story.append(Paragraph("What's Inside", s_h3))
    toc_items = [
        "1. System Overview — What was built and why",
        "2. Architecture — How all the pieces connect",
        "3. Strategy Layer — Content pillars, platforms, and positioning",
        "4. Operations Layer — Workflows, SOPs, and daily routines",
        "5. Tools Layer — Caption generator, image pipeline, automation",
        "6. Activation Guide — Step-by-step setup and testing",
        "7. Monthly Operating Playbook — Ongoing cadence and costs",
        "8. File Reference — Complete inventory of all deliverables",
    ]
    for item in toc_items:
        story.append(Paragraph(item, s_bullet, bulletText="→"))

    story.append(PageBreak())

    # ── 1. SYSTEM OVERVIEW ──────────────────────────────────

    story.append(Paragraph("1. System Overview", s_h1))
    story.append(GoldLine(usable_width, 1))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "This document covers a complete social media management system built for Matt Anthony Photography. "
        "It spans strategy, operations, and automation — designed to turn every completed photo shoot into "
        "3-6 months of content across Instagram, LinkedIn, Pinterest, and the website journal.",
        s_body
    ))

    story.append(Paragraph("The Problem", s_h3))
    story.append(Paragraph(
        "You had solid strategy foundations (content pillars, basic caption templates, a repurposing chain concept) "
        "but lacked the execution layer — no automation, no scheduling integration, no expanded hooks, no video scripts, "
        "no LinkedIn acquisition playbook, and no Pinterest presence. Every post required starting from scratch.",
        s_body
    ))

    story.append(Paragraph("What Was Built", s_h3))
    story.append(make_table(
        ["Layer", "Files", "Purpose"],
        [
            ["Strategy", "8 documents", "What to post, how to write it, where to put it"],
            ["Operations", "3 workflows", "SOPs for daily/weekly/monthly execution"],
            ["Tools", "2 Python scripts", "Caption generation (Claude API) + image resizing"],
            ["Automation", "1 n8n spec", "End-to-end pipeline from sheet to scheduled post"],
        ],
        col_widths=[1.2 * inch, 1.2 * inch, usable_width - 2.4 * inch],
    ))

    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Total: 14 files, ~3,600 lines of documentation and code.</b>",
        s_body_bold
    ))

    story.append(Paragraph("Key Strategic Shifts", s_h3))
    shifts = [
        "<b>LinkedIn is now the #1 B2B channel</b> — with a full acquisition playbook, not an afterthought",
        "<b>Pinterest launched from zero</b> — 11 boards, SEO-optimized pins, passive traffic engine",
        "<b>Hooks are designed to stop scrolling</b> — curiosity gaps and story entries replace announcement-style openers",
        "<b>Every shoot produces 15-25 content pieces</b> across 4 platforms instead of 3-4 posts",
        "<b>Video/Reels have a real strategy</b> — 8 specific formats with timing and shot structure",
        "<b>Automation removes manual work</b> — Claude generates captions, Postiz schedules posts, n8n orchestrates",
    ]
    for s in shifts:
        story.append(Paragraph(s, s_bullet, bulletText="•"))

    story.append(PageBreak())

    # ── 2. ARCHITECTURE ─────────────────────────────────────

    story.append(Paragraph("2. Architecture", s_h1))
    story.append(GoldLine(usable_width, 1))
    story.append(Spacer(1, 8))

    story.append(Paragraph("How Everything Connects", s_h3))
    story.append(Paragraph(
        "The system follows the WAT framework (Workflows, Agents, Tools). Strategy documents define what to do. "
        "Workflows define how to do it. Tools execute the deterministic work.",
        s_body
    ))

    story.append(Paragraph("End-to-End Content Flow", s_h2))
    flow_steps = [
        "<b>1. Shoot delivered</b> → Images land in Dropbox delivery folder",
        "<b>2. Image pipeline</b> → resize_images.py creates crops for all 6 platforms",
        "<b>3. Caption generation</b> → generate_captions.py produces platform-specific captions via Claude API",
        "<b>4. Review &amp; edit</b> → You refine the AI-generated captions (the 80/20 handoff)",
        "<b>5. Schedule</b> → Posts loaded into Postiz (or content calendar sheet) with dates",
        "<b>6. Publish</b> → Postiz pushes to Instagram, LinkedIn, Pinterest on schedule",
        "<b>7. Engage</b> → Daily 10-minute routine: respond, comment, connect",
        "<b>8. Measure</b> → Monthly analytics review using the dashboard template",
        "<b>9. Adjust</b> → Update content mix based on what's working",
    ]
    for step in flow_steps:
        story.append(Paragraph(step, s_bullet, bulletText="→"))

    story.append(Spacer(1, 8))
    story.append(Paragraph("File Reference Map", s_h2))
    story.append(Paragraph(
        "When you're working, here's what to open for what:",
        s_body
    ))
    story.append(make_table(
        ["You Need To...", "Open This File"],
        [
            ["Pick a hook for a post", "hooks-scripts-library.md"],
            ["Write a caption", "caption-templates.md"],
            ["Grab hashtags", "hashtag-system.md"],
            ["Write a LinkedIn post", "linkedin-b2b-playbook.md"],
            ["Optimize a Pinterest pin", "pinterest-playbook.md"],
            ["Batch content from a shoot", "workflows/content-batching.md"],
            ["Check the weekly schedule", "workflows/social-media-management.md"],
            ["Pull monthly analytics", "analytics-dashboard.md"],
            ["Resize images", "python3 tools/resize_images.py"],
            ["Generate captions", "python3 tools/generate_captions.py"],
            ["Set up n8n automation", "workflows/social-media-automation.md"],
        ],
        col_widths=[2.5 * inch, usable_width - 2.5 * inch],
    ))

    story.append(PageBreak())

    # ── 3. STRATEGY LAYER ───────────────────────────────────

    story.append(Paragraph("3. Strategy Layer", s_h1))
    story.append(GoldLine(usable_width, 1))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Content Pillars", s_h2))
    story.append(make_table(
        ["Pillar", "What It Covers", "Frequency"],
        [
            ["1. Project Showcases", "Final images, project reveals, portfolio in motion", "2-3x/week"],
            ["2. Process &amp; BTS", "Shoot day footage, gear, lighting, retouching timelapses", "1-2x/week"],
            ["3. Client Spotlights", "Testimonials, collaboration stories, client wins", "1x/week"],
            ["4. Educational", "Tips for builders, award submission advice, industry insights", "1-2x/week"],
            ["5. Personal / Brand", "Squamish life, career reflections, milestones", "1-2x/month"],
        ],
        col_widths=[1.5 * inch, 3.2 * inch, usable_width - 4.7 * inch],
    ))

    story.append(Paragraph("Platform Strategy", s_h2))
    story.append(make_table(
        ["Platform", "Role", "Cadence", "Key Insight"],
        [
            ["Instagram", "Portfolio + reach", "4-5x/week", "Carousels get 10% engagement vs 7% for singles. 4:5 vertical."],
            ["LinkedIn", "B2B client acquisition", "4x/week", "Personal profile gets 561% more reach. No links in post body."],
            ["Pinterest", "Passive traffic engine", "3-5 pins/day", "5x more website traffic. Pins gain value over months, not hours."],
            ["Journal", "SEO + long-form", "1-2x/month", "Each post feeds 3-5 Pinterest pins. Target builder search terms."],
        ],
        col_widths=[1 * inch, 1.5 * inch, 1.1 * inch, usable_width - 3.6 * inch],
    ))

    story.append(Paragraph("Hooks Library Summary", s_h2))
    story.append(Paragraph(
        "The hooks library contains <b>53 proven hooks</b> organized by content pillar, plus <b>6 universal hook formulas</b> "
        "(Curiosity Gap, Problem-Solution, Pattern Interrupt, Contrarian Take, Story Entry, Data/Proof) that can generate "
        "unlimited variations. Every hook is designed to work in the first 1-2 lines where the scroll-stop decision happens.",
        s_body
    ))

    story.append(Paragraph("Sample Hooks by Pillar", s_h3))
    hooks = [
        ["Showcase", "\"Every angle in this project fights for your attention. Swipe.\""],
        ["BTS", "\"POV: You're photographing a $3M house and the sun disappears.\""],
        ["Client", "\"When a builder's standards are this high, the photos take care of themselves.\""],
        ["Educational", "\"Builders spend $500K on a kitchen and $0 on photographing it.\""],
        ["Personal", "\"I didn't plan on becoming an architectural photographer.\""],
    ]
    story.append(make_table(
        ["Pillar", "Example Hook"],
        hooks,
        col_widths=[1.2 * inch, usable_width - 1.2 * inch],
    ))

    story.append(Paragraph("Hashtag System", s_h2))
    story.append(Paragraph(
        "5-tier system with 80+ hashtags and 10 pre-built copy-paste rotation groups. "
        "Tiers: High Volume (broad reach), Medium/Niche (your sweet spot), Location-Specific (always include), "
        "Industry/B2B (targets clients), Photography Craft (professional community). "
        "Rotate between Set A and Set B per content type to avoid algorithmic suppression.",
        s_body
    ))

    story.append(PageBreak())

    # ── 4. OPERATIONS LAYER ─────────────────────────────────

    story.append(Paragraph("4. Operations Layer", s_h1))
    story.append(GoldLine(usable_width, 1))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Weekly Posting Schedule", s_h2))
    story.append(make_table(
        ["Day", "Instagram", "LinkedIn", "Pinterest"],
        [
            ["Monday", "Carousel (Project Reveal)", "Document carousel (Project Story)", "3-5 pins"],
            ["Tuesday", "Reel (BTS / Before-After)", "Text post (Industry Insight)", "3-5 pins"],
            ["Wednesday", "—", "—", "3-5 pins"],
            ["Thursday", "Carousel (Educational)", "Client Spotlight / Educational", "3-5 pins"],
            ["Friday", "Reel (Process / Reveal)", "Personal / Contrarian take", "3-5 pins"],
            ["Saturday", "Single image / throwback", "—", "3-5 pins"],
            ["Sunday", "—", "—", "3-5 pins"],
        ],
        col_widths=[1 * inch, 2 * inch, 2.2 * inch, usable_width - 5.2 * inch],
    ))

    story.append(Paragraph("Content Batching Process", s_h2))
    story.append(Paragraph(
        "One shoot → 15-25 content pieces → 2.5 hours of work. Here's the breakdown:",
        s_body
    ))
    story.append(make_table(
        ["Step", "Time", "What You Do"],
        [
            ["1. Prepare assets", "30 min", "Select images, run resize_images.py for all platform crops"],
            ["2. Generate captions", "5 min", "Run generate_captions.py — AI produces 7 platform-specific captions"],
            ["3. Edit captions", "60 min", "Review AI output, add your voice, write BTS and personal pieces"],
            ["4. Schedule", "30 min", "Load into Postiz or calendar, map to weekly schedule"],
            ["5. Quality check", "10 min", "Run through the checklist (tags, hashtags, links, variety)"],
        ],
        col_widths=[1.3 * inch, 0.7 * inch, usable_width - 2 * inch],
    ))

    story.append(Paragraph("Repurposing Chain", s_h2))
    story.append(Paragraph(
        "Every project generates content over a 3-6 month arc:",
        s_body
    ))
    chain = [
        ["Week 1", "IG hero carousel, LinkedIn doc carousel, BTS Reel, 5-8 Pinterest pins, Stories"],
        ["Week 2", "Client tag post, educational post, detail shots, 5 more Pinterest pins"],
        ["Week 3-4", "Journal post (SEO), journal-derived Pinterest pins, testimonial graphic"],
        ["Month 3-6", "Throwback re-share, case study, award submission collateral"],
    ]
    story.append(make_table(
        ["Timing", "Content"],
        chain,
        col_widths=[1 * inch, usable_width - 1 * inch],
    ))

    story.append(Paragraph("Daily Engagement Routine (10 min/day)", s_h2))
    routines = [
        "<b>2 min</b> — Respond to all comments on your posts",
        "<b>5 min</b> — Comment on 3-5 posts from architects, builders, developers (meaningful, not generic)",
        "<b>2 min</b> — Post Instagram Stories if you have casual content",
        "<b>1 min</b> — Send 2-3 LinkedIn connection requests with personalized notes",
    ]
    for r in routines:
        story.append(Paragraph(r, s_bullet, bulletText="•"))

    story.append(PageBreak())

    # ── 5. TOOLS LAYER ──────────────────────────────────────

    story.append(Paragraph("5. Tools Layer", s_h1))
    story.append(GoldLine(usable_width, 1))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Caption Generator — generate_captions.py", s_h2))
    story.append(Paragraph(
        "Uses the Claude API (Sonnet) to produce platform-specific captions from project metadata. "
        "Brand voice, platform rules, and format specs are baked into the system prompt so every output "
        "matches your tone: professional but warm, no hype, design-focused.",
        s_body
    ))

    story.append(Paragraph("Three Modes", s_h3))
    modes = [
        ["generate", "Feed project metadata → get all 7 platform captions at once"],
        ["single", "Generate one specific caption (e.g., just a LinkedIn insight)"],
        ["batch", "Point at a Google Sheet → generate captions for every project row"],
    ]
    story.append(make_table(
        ["Mode", "What It Does"],
        modes,
        col_widths=[1.2 * inch, usable_width - 1.2 * inch],
    ))

    story.append(Paragraph("Output per project:", s_h3))
    outputs = [
        "Instagram Carousel caption",
        "Instagram Reel caption",
        "Instagram Detail/Single caption",
        "Instagram BTS caption",
        "LinkedIn Project Story post",
        "LinkedIn Industry Insight post",
        "Pinterest Pin (title + description + alt text)",
    ]
    for o in outputs:
        story.append(Paragraph(o, s_bullet, bulletText="•"))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Image Resize Pipeline — resize_images.py", s_h2))
    story.append(Paragraph(
        "Center-weighted smart cropping that produces all 6 platform dimensions from a single source image. "
        "Supports SEO-friendly filename prefixes for Pinterest and Google image search.",
        s_body
    ))

    story.append(Paragraph("Platform Crops", s_h3))
    story.append(make_table(
        ["Platform", "Dimensions", "Aspect Ratio"],
        [
            ["Instagram Feed", "1080 × 1350px", "4:5 portrait"],
            ["Instagram Story / Reel", "1080 × 1920px", "9:16 portrait"],
            ["LinkedIn Image", "1200 × 628px", "1.91:1 landscape"],
            ["LinkedIn Doc Carousel", "1080 × 1350px", "4:5 portrait"],
            ["Pinterest Pin", "1000 × 1500px", "2:3 portrait"],
            ["Website / Journal", "1600 × 900px", "16:9 landscape"],
        ],
        col_widths=[1.8 * inch, 1.5 * inch, usable_width - 3.3 * inch],
    ))

    story.append(Spacer(1, 8))
    story.append(Paragraph("n8n Automation Pipeline", s_h2))
    story.append(Paragraph(
        "Three n8n workflows that automate the end-to-end pipeline once everything is tested manually:",
        s_body
    ))
    story.append(make_table(
        ["Workflow", "Trigger", "What It Does"],
        [
            ["1. Caption Generation", "New row in Content Calendar sheet", "Claude API generates captions → writes back to sheet for review"],
            ["2. Post Publishing", "Row marked 'Approved' + scheduled date", "Postiz schedules posts to IG, LinkedIn, Pinterest"],
            ["3. Analytics Pull", "Weekly cron (Monday 9am)", "Instagram Insights API → writes engagement data to sheet"],
        ],
        col_widths=[1.5 * inch, 1.8 * inch, usable_width - 3.3 * inch],
    ))

    story.append(PageBreak())

    # ── 6. ACTIVATION GUIDE ─────────────────────────────────

    story.append(Paragraph("6. Activation Guide", s_h1))
    story.append(GoldLine(usable_width, 1))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "9 steps to get fully operational. Steps 1-4 can be done today. Step 5 happens on your next project delivery. "
        "Steps 7-9 are for when you're ready to automate.",
        s_body
    ))

    steps = [
        ["1", "Test image resize tool", "5 min", "None — works now",
         "Run: python3 tools/resize_images.py resize --input /path/to/photo.jpg --output-dir .tmp/test/"],
        ["2", "Set up caption generator", "10 min", "Anthropic API key",
         "Add ANTHROPIC_API_KEY to .env, then run: python3 tools/generate_captions.py generate --project \"Test\" --client \"Test\" --location \"Squamish\""],
        ["3", "Set up Pinterest", "20 min", "Manual",
         "Convert to business account. Claim website. Create 11 boards from pinterest-playbook.md. Pin first 20-30 images."],
        ["4", "Optimize LinkedIn profile", "15 min", "Manual",
         "Update headline, banner, about section, featured items using linkedin-b2b-playbook.md checklist. Request 3 recommendations."],
        ["5", "First full content batch", "2.5 hrs", "Steps 1-2 done",
         "Follow content-batching.md step by step on your most recent project delivery."],
        ["6", "Daily engagement routine", "10 min/day", "None",
         "Start tomorrow. Respond to comments, engage on LinkedIn, send connection requests."],
        ["7", "Set up Postiz", "30 min", "Docker hosting",
         "Deploy Postiz via Docker. Connect IG, LinkedIn, Pinterest. Add MCP to Claude Code. Free."],
        ["8", "Content calendar sheet", "20 min", "Google Sheet",
         "Create sheet with the 19-column structure from social-media-automation.md. Test batch caption generation."],
        ["9", "Build n8n workflows", "2-3 hrs", "All above stable",
         "Deploy 3 workflows on n8n instance. Test each with one project."],
    ]
    story.append(make_table(
        ["#", "Step", "Time", "Requires", "How"],
        steps,
        col_widths=[0.3 * inch, 1.4 * inch, 0.7 * inch, 1.1 * inch, usable_width - 3.5 * inch],
    ))

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "<b>Total setup time: ~4-5 hours spread across a few days.</b> "
        "Ongoing: ~10 min/day engagement + 2.5 hours per project batch.",
        s_body_bold
    ))

    story.append(PageBreak())

    # ── 7. MONTHLY OPERATING PLAYBOOK ───────────────────────

    story.append(Paragraph("7. Monthly Operating Playbook", s_h1))
    story.append(GoldLine(usable_width, 1))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Target Metrics", s_h2))
    story.append(make_table(
        ["Platform", "Metric", "Target", "Why"],
        [
            ["Instagram", "Engagement rate", "5%+", "Content quality signal"],
            ["Instagram", "Saves per post", "10+", "Strongest quality signal"],
            ["Instagram", "Shares/sends per post", "5+", "#1 algorithm signal for new reach"],
            ["LinkedIn", "Profile views/week", "100+", "Visibility to decision-makers"],
            ["LinkedIn", "Post impressions/week", "2,000+", "Content reach"],
            ["LinkedIn", "Inbound inquiries/quarter", "2-3", "Revenue attribution"],
            ["Pinterest", "Monthly impressions", "10K+ (month 3)", "Content discovery"],
            ["Pinterest", "Website clicks/month", "50+", "Traffic driven"],
        ],
        col_widths=[1 * inch, 1.8 * inch, 1.3 * inch, usable_width - 4.1 * inch],
    ))

    story.append(Paragraph("Monthly Review Process", s_h2))
    story.append(Paragraph(
        "First Monday of each month. ~1 hour. Use the template in analytics-dashboard.md:",
        s_body
    ))
    review_steps = [
        "Pull metrics from all platforms (Instagram Insights, LinkedIn Analytics, Pinterest Analytics)",
        "Compare to targets — what's on track, what's behind?",
        "Identify top 3 performing posts — what hook/format/topic worked?",
        "Identify bottom 3 — what fell flat and why?",
        "Adjust next month's content mix based on findings",
        "Update hashtag rotation if any sets are underperforming",
        "Plan seasonal or event-tied content for the month ahead",
    ]
    for i, step in enumerate(review_steps, 1):
        story.append(Paragraph(f"<b>{i}.</b> {step}", s_bullet, bulletText=""))

    story.append(Paragraph("Quarterly Deep Review (add every 3 months)", s_h3))
    quarterly = [
        "Platform ROI ranking — which platform generates the most inquiries per hour invested?",
        "Content pillar performance — rank all 5 pillars by engagement, shift mix toward what works",
        "Follower quality audit — are you attracting builders/architects or just other photographers?",
        "Competitor check — what are Ema Peter, Kyle Graham, Fyfe doing differently?",
        "Service alignment — is social driving inquiries for retainers and project photography, or the wrong services?",
    ]
    for q in quarterly:
        story.append(Paragraph(q, s_bullet, bulletText="•"))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Monthly Operating Cost", s_h2))
    story.append(make_table(
        ["Service", "Cost", "Notes"],
        [
            ["Postiz (self-hosted)", "$0", "Instagram + LinkedIn + Pinterest scheduling"],
            ["Claude API (Sonnet)", "$5-10/mo", "~50 caption batches/month"],
            ["n8n", "$0", "Existing instance"],
            ["Google Sheets", "$0", "Content calendar"],
            ["Pinterest", "$0", "Business account is free"],
            ["<b>Total</b>", "<b>$5-10/mo</b>", ""],
        ],
        col_widths=[2.5 * inch, 1 * inch, usable_width - 3.5 * inch],
    ))

    story.append(PageBreak())

    # ── 8. FILE REFERENCE ───────────────────────────────────

    story.append(Paragraph("8. File Reference", s_h1))
    story.append(GoldLine(usable_width, 1))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Strategy Documents — business/marketing/", s_h2))
    story.append(make_table(
        ["File", "Lines", "Description"],
        [
            ["content-strategy.md", "186", "Master strategy — pillars, platform rules, repurposing chain, video, metrics"],
            ["caption-templates.md", "296", "Fill-in-the-blank captions for every post type and platform"],
            ["hooks-scripts-library.md", "342", "53 hooks, 6 universal formulas, full scripts by pillar"],
            ["linkedin-b2b-playbook.md", "260", "Profile optimization, content schedule, client acquisition playbook"],
            ["pinterest-playbook.md", "265", "Account setup, 11 boards, pin SEO, posting cadence, growth timeline"],
            ["hashtag-system.md", "198", "5-tier system, 80+ hashtags, 10 copy-paste rotation groups"],
            ["analytics-dashboard.md", "221", "KPIs, benchmarks, monthly review template, revenue attribution"],
        ],
        col_widths=[2.2 * inch, 0.5 * inch, usable_width - 2.7 * inch],
    ))

    story.append(Paragraph("Workflow SOPs — workflows/", s_h2))
    story.append(make_table(
        ["File", "Lines", "Description"],
        [
            ["social-media-management.md", "223", "Master SOP — weekly schedule, daily/weekly/monthly routines"],
            ["content-batching.md", "246", "One shoot → 15-25 pieces in 2.5 hours, step by step"],
            ["social-media-automation.md", "389", "n8n workflow spec — captions, scheduling, analytics"],
            ["social-media-activation.md", "300", "This activation report in markdown form"],
        ],
        col_widths=[2.5 * inch, 0.5 * inch, usable_width - 3 * inch],
    ))

    story.append(Paragraph("Tools — tools/", s_h2))
    story.append(make_table(
        ["File", "Lines", "Description"],
        [
            ["generate_captions.py", "318", "Claude API caption generator — single, multi-platform, batch"],
            ["resize_images.py", "234", "Smart-crop images for all 6 platform dimensions"],
            ["google_sheets_auth.py", "52", "Shared Google OAuth helper (pre-existing)"],
        ],
        col_widths=[2.2 * inch, 0.5 * inch, usable_width - 2.7 * inch],
    ))

    story.append(Spacer(1, 24))
    story.append(GoldLine(usable_width * 0.3, 2))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"Generated {datetime.now().strftime('%B %d, %Y')} — Matt Anthony Photography",
        s_small
    ))
    story.append(Paragraph(
        "mattanthonyphoto.com | @mattanthonyphoto | info@mattanthonyphoto.com",
        s_small
    ))

    # Build
    doc.build(story)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    output = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".tmp",
        "social-media-system-report.pdf",
    )
    os.makedirs(os.path.dirname(output), exist_ok=True)
    build_pdf(output)
