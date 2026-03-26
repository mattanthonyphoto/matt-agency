"""
Generate site audit PDF report for mattanthonyphoto.com
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
CRITICAL_RED = HexColor("#C0392B")
HIGH_ORANGE = HexColor("#D4731A")
MEDIUM_YELLOW = HexColor("#B8860B")
LOW_GREEN = HexColor("#27864A")


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
    pw = doc.width

    # Custom styles
    styles.add(ParagraphStyle(
        'CoverTitle', fontName='Helvetica-Bold', fontSize=28,
        textColor=INK, leading=34, spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        'CoverSub', fontName='Helvetica', fontSize=12,
        textColor=STONE, leading=16, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        'GoldLabel', fontName='Helvetica-Bold', fontSize=8,
        textColor=GOLD, leading=12, spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        'SectionTitle', fontName='Helvetica-Bold', fontSize=16,
        textColor=INK, leading=20, spaceBefore=16, spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        'SubSection', fontName='Helvetica-Bold', fontSize=11,
        textColor=INK, leading=14, spaceBefore=10, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        'Body', fontName='Helvetica', fontSize=9,
        textColor=INK, leading=13, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        'BodyBold', fontName='Helvetica-Bold', fontSize=9,
        textColor=INK, leading=13, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        'Small', fontName='Helvetica', fontSize=8,
        textColor=STONE, leading=11, spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        'TableHeader', fontName='Helvetica-Bold', fontSize=8,
        textColor=white, leading=11
    ))
    styles.add(ParagraphStyle(
        'TableCell', fontName='Helvetica', fontSize=8,
        textColor=INK, leading=11
    ))
    styles.add(ParagraphStyle(
        'TableCellBold', fontName='Helvetica-Bold', fontSize=8,
        textColor=INK, leading=11
    ))
    styles.add(ParagraphStyle(
        'Footer', fontName='Helvetica', fontSize=7,
        textColor=STONE, leading=10, alignment=TA_CENTER
    ))

    story = []

    def gold_rule():
        story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=8, spaceBefore=4))

    def dark_rule():
        story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_STONE, spaceAfter=6, spaceBefore=6))

    def make_table(headers, rows, col_widths=None):
        header_row = [Paragraph(h, styles['TableHeader']) for h in headers]
        data = [header_row]
        for row in rows:
            data.append([Paragraph(str(c), styles['TableCell']) for c in row])

        if col_widths is None:
            col_widths = [pw / len(headers)] * len(headers)

        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), INK),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, OFF_WHITE]),
            ('GRID', (0, 0), (-1, -1), 0.5, LIGHT_STONE),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]))
        return t

    # =====================
    # COVER PAGE
    # =====================
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("MATT ANTHONY PHOTOGRAPHY", styles['GoldLabel']))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Website Rebuild", styles['CoverTitle']))
    story.append(Paragraph("Action Plan", styles['CoverTitle']))
    story.append(Spacer(1, 12))
    gold_rule()
    story.append(Spacer(1, 8))
    story.append(Paragraph("mattanthonyphoto.com — Full Site Audit &amp; Rebuild Specification", styles['CoverSub']))
    story.append(Paragraph("Prepared: March 19, 2026", styles['CoverSub']))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(
        "Based on comprehensive audit of 69 live URLs, ~740 images,<br/>"
        "structured data, technical SEO, Google indexing, and content review.",
        styles['Small']
    ))

    story.append(PageBreak())

    # =====================
    # EXECUTIVE SUMMARY
    # =====================
    story.append(Paragraph("1. EXECUTIVE SUMMARY", styles['SectionTitle']))
    gold_rule()

    story.append(Paragraph(
        "The site has grown to 69 URLs including 7 new location landing pages, a pricing guide funnel, "
        "and a 5th case study (LRD Studio). However, <b>Google has indexed only 2 pages</b> out of 69. "
        "Critical technical SEO issues — missing meta descriptions, broken structured data URLs, "
        "duplicate content signals, and a placeholder analytics tag — are undermining the site's "
        "ability to generate organic traffic. Additionally, Service 04 is being rebranded from "
        "\"Visual Partner Retainer\" to <b>\"Creative Partner\"</b> to reflect the full scope of services delivered.",
        styles['Body']
    ))
    story.append(Spacer(1, 8))

    summary_data = [
        ["Total pages in sitemap", "69"],
        ["Pages indexed by Google", "2 (CRITICAL)"],
        ["Total images audited", "~740"],
        ["Images missing alt text", "~80"],
        ["Images with useless alt text", "~120"],
        ["Images with lazy loading", "0"],
        ["Pages missing meta descriptions", "All"],
        ["Pages missing canonical tags", "Most"],
        ["Pages missing OG tags", "Most"],
    ]
    story.append(make_table(
        ["Metric", "Current State"],
        summary_data,
        col_widths=[pw * 0.55, pw * 0.45]
    ))

    story.append(PageBreak())

    # =====================
    # CRITICAL FIXES
    # =====================
    story.append(Paragraph("2. CRITICAL FIXES", styles['SectionTitle']))
    gold_rule()
    story.append(Paragraph(
        "These must be addressed before or during the rebuild. Each one is actively harming SEO or user experience.",
        styles['Small']
    ))
    story.append(Spacer(1, 8))

    critical_items = [
        ["CRITICAL", "#C0392B", "Google indexing — only 2 of 69 pages indexed",
         "Submit sitemap to Google Search Console. Request indexing for all priority pages. Add canonical tags. Fix duplicate URL signals (/home vs /, /projects vs /projects-1)."],
        ["CRITICAL", "#C0392B", "Placeholder GA4 tag (G-XXXXXXXXXX)",
         "Remove the placeholder Google Analytics script from the custom header. The real tag (G-MS06FRZ7L7) is already working. The placeholder fires errors on every page load."],
        ["HIGH", "#D4731A", "JSON-LD service URLs point to wrong paths",
         "Structured data lists services at /services/project-photography etc. Actual URLs are /project-photography (no /services/ prefix). Update all 4 service URLs in the sitewide JSON-LD OfferCatalog."],
        ["HIGH", "#D4731A", "/construction-team-content serving wrong content",
         "Page shows Visual Partner Retainer content instead of Build &amp; Team Content. Title tag is correct but H1 and body are wrong. Rebuild with correct content. Broken since at least March 16."],
        ["HIGH", "#D4731A", "Missing meta descriptions — ALL pages",
         "No page on the site has a meta description. Add unique, keyword-rich descriptions to every page. Priority: homepage, service pages, location pages, case studies, projects, journal."],
        ["HIGH", "#D4731A", "Rename Service 04: Visual Partner Retainer to Creative Partner",
         "Update everywhere: navigation, service page, case study cross-links, JSON-LD, footer. Rewrite page content to reflect expanded scope (marketing, strategy, website dev, content creation). Change URL slug with 301 redirect."],
    ]

    for item in critical_items:
        sev, color, title, desc = item
        story.append(KeepTogether([
            Paragraph(f'<font color="{color}">[{sev}]</font> <b>{title}</b>', styles['Body']),
            Paragraph(desc, styles['Small']),
            Spacer(1, 6),
        ]))

    story.append(PageBreak())

    # =====================
    # SEO FIXES
    # =====================
    story.append(Paragraph("3. SEO &amp; TECHNICAL FIXES", styles['SectionTitle']))
    gold_rule()

    seo_items = [
        ["MEDIUM", "#B8860B", "Missing OG tags on service pages",
         "Add og:title, og:description, og:image to each service page code block."],
        ["MEDIUM", "#B8860B", "Missing canonical tags",
         "Add link rel=\"canonical\" to all custom code block pages."],
        ["MEDIUM", "#B8860B", "Duplicate WebSite schema on every page",
         "Squarespace auto-generates a WebSite schema with empty description alongside the custom one. Suppress or align."],
        ["MEDIUM", "#B8860B", "Sitemap URL mismatches",
         "Sitemap has /projects but nav links /projects-1. Sitemap has /home but root is /. Fix nav links and set up 301 redirects."],
        ["MEDIUM", "#B8860B", "Stale /services/ sub-pages in sitemap",
         "Remove or redirect: /services/jobsite-progression-photography (Jul 2025), /services/team-headshots-photography (Jul 2025), /services/architectural-interiors-photography (Jul 2025), /services/project-one-f5w4d-absrg (duplicate)."],
        ["MEDIUM", "#B8860B", "Inconsistent location page URL slugs",
         "5 pages use -photography, 2 use -photographer. Standardize all to one pattern with 301 redirects."],
        ["MEDIUM", "#B8860B", "FAQ schema incomplete",
         "Only 10 of 17+ visible FAQ questions are in the FAQPage JSON-LD. Add all questions."],
        ["MEDIUM", "#B8860B", "Summerhill case study missing Article schema",
         "All other case studies have Article + Review schemas. Add to Summerhill."],
        ["LOW", "#27864A", "Inconsistent title tag separators",
         "Mix of | and - separators. Standardize across all pages."],
        ["LOW", "#27864A", "Process page missing HowTo schema",
         "5-step process is perfect for Google's HowTo rich results."],
        ["LOW", "#27864A", "Multiple H1 tags on /bio and /journal",
         "Each page should have a single H1 element."],
        ["LOW", "#27864A", "No-index utility pages",
         "/project-intake-form and /pricing-guide-thank-you should not be indexed."],
    ]

    for item in seo_items:
        sev, color, title, desc = item
        story.append(KeepTogether([
            Paragraph(f'<font color="{color}">[{sev}]</font> <b>{title}</b>', styles['Body']),
            Paragraph(desc, styles['Small']),
            Spacer(1, 4),
        ]))

    story.append(PageBreak())

    # =====================
    # CONTENT FIXES
    # =====================
    story.append(Paragraph("4. CONTENT FIXES", styles['SectionTitle']))
    gold_rule()

    content_items = [
        ["HIGH", "#D4731A", "FAQ typo: \"other architects\"",
         "/faqs — \"What makes your approach different from other architects?\" should be \"other photographers.\""],
        ["HIGH", "#D4731A", "FAQ typo: \"Reach back\"",
         "/faqs — \"Reach back and I'll get back within 24 hours\" should be \"Reach out.\""],
        ["MEDIUM", "#B8860B", "Warbler grammar issue",
         "/warbler-whistler — \"that balancing form and function\" is grammatically incorrect."],
        ["MEDIUM", "#B8860B", "SDA next-project typo",
         "/seventh-day-adventist-bc-headquarters — \"Pit Meadows\" should be \"Pitt Meadows\" in next-project link."],
        ["MEDIUM", "#B8860B", "Brand voice inconsistency (I vs We)",
         "Homepage uses We/Our, bio/process/contact use I/My. Unify per brand bible: I on project pages and bio, We on homepage and service pages."],
        ["LOW", "#27864A", "Truncated footer HTML",
         "/project-photography — LinkedIn link rel attribute is cut off in the code block."],
    ]

    for item in content_items:
        sev, color, title, desc = item
        story.append(KeepTogether([
            Paragraph(f'<font color="{color}">[{sev}]</font> <b>{title}</b>', styles['Body']),
            Paragraph(desc, styles['Small']),
            Spacer(1, 4),
        ]))

    story.append(PageBreak())

    # =====================
    # ALT TEXT AUDIT
    # =====================
    story.append(Paragraph("5. IMAGE ALT TEXT AUDIT", styles['SectionTitle']))
    gold_rule()

    story.append(Paragraph(
        "~740 images were audited across all pages. Zero images use lazy loading. "
        "The following pages require alt text fixes, ranked by SEO impact.",
        styles['Body']
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Tier 1: No Alt Text (entire page missing)", styles['SubSection']))
    alt_tier1 = [
        ["/journal", "17", "17 (100%)", "Every blog thumbnail missing — these drive organic traffic"],
        ["/squamish-architectural-photography", "11", "11 (100%)", "SEO landing page — worst page to have no alt text"],
        ["/whistler-architectural-photography", "10", "8 (80%)", "SEO landing page — only 2 hero images have alt"],
        ["/the-window-merchant", "11", "7 (64%)", "Case study with majority missing"],
    ]
    story.append(make_table(
        ["Page", "Images", "Missing", "Notes"],
        alt_tier1,
        col_widths=[pw * 0.28, pw * 0.08, pw * 0.12, pw * 0.52]
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Tier 2: Alt Text Present But Useless (generic or numbered)", styles['SubSection']))
    alt_tier2 = [
        ["/fitzsimmons-whistler", "27", "23 images all say just \"Fitzsimmons\" — no room, no location, no keywords"],
        ["/west-10th-vancouver", "57", "55 images use numbered alt (\"West 10th Vancouver 1\", \"...2\", etc.)"],
        ["/balsam-way", "41", "36 images use numbered alt (\"Balsam Way Whistler 1\", \"...2\", etc.)"],
        ["/sunset-beach", "23", "19 images use numbered alt (\"Sunset Beach Vancouver penthouse 1\", etc.)"],
    ]
    story.append(make_table(
        ["Page", "Images", "Issue"],
        alt_tier2,
        col_widths=[pw * 0.25, pw * 0.08, pw * 0.67]
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Tier 3: Sitewide Recurring Issues", styles['SubSection']))
    alt_tier3 = [
        ["Header hero image (warbler...jpg-22.jpg)", "~15+ pages", "Always MISSING alt — fix once in sitewide header code block"],
        ["Logo (matt-anthony-photography.png)", "Multiple", "MISSING alt — add alt=\"Matt Anthony Photography\""],
        ["CTA background images", "Homepage", "2 instances with EMPTY alt=\"\""],
        ["Generic \"Architectural photography\" alt", "3 pages", "Balmoral, Sitelines, Window Merchant — last gallery image"],
    ]
    story.append(make_table(
        ["Issue", "Pages", "Fix"],
        alt_tier3,
        col_widths=[pw * 0.35, pw * 0.12, pw * 0.53]
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Best Practice Alt Text Pattern (from your best pages)", styles['SubSection']))
    story.append(Paragraph(
        "<b>Format:</b> [Project Name] [Location] [room/feature] [photography type]<br/><br/>"
        "<b>Good examples (The Perch):</b><br/>"
        "- \"The Perch Sunshine Coast suspended fireplace interior detail\"<br/>"
        "- \"The Perch Sunshine Coast aerial drone architectural photography\"<br/>"
        "- \"The Perch Sunshine Coast bedroom with forest and ocean view\"<br/><br/>"
        "<b>Needs fixing:</b><br/>"
        "- \"Fitzsimmons\" (no detail)<br/>"
        "- \"West 10th Vancouver 14\" (numbered, useless)<br/>"
        "- \"Architectural photography\" (generic)",
        styles['Body']
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Performance: Lazy Loading", styles['SubSection']))
    story.append(Paragraph(
        "<b>Zero images across ~740 use loading=\"lazy\".</b> Pages like West 10th (57 images), "
        "Silver Star (44 images), and Wakefield (43 images) load every image eagerly. "
        "Add loading=\"lazy\" to all below-the-fold images in every code block during the rebuild.",
        styles['Body']
    ))

    story.append(PageBreak())

    # =====================
    # SERVICE ARCHITECTURE UPDATE
    # =====================
    story.append(Paragraph("6. SERVICE ARCHITECTURE UPDATE", styles['SectionTitle']))
    gold_rule()

    story.append(Paragraph("Updated Service Ladder", styles['SubSection']))
    service_data = [
        ["01", "Project Photography", "/project-photography", "Keep — no changes to scope"],
        ["02", "Award &amp; Publication Imagery", "/award-publication-imagery", "Keep — no changes to scope"],
        ["03", "Build &amp; Team Content", "/construction-team-content", "REBUILD — currently serving wrong content"],
        ["04", "Creative Partner", "/creative-partner (new)", "REBRAND + REBUILD — was \"Visual Partner Retainer\""],
    ]
    story.append(make_table(
        ["#", "Service Name", "URL", "Status"],
        service_data,
        col_widths=[pw * 0.05, pw * 0.22, pw * 0.28, pw * 0.45]
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Creative Partner — New Scope", styles['SubSection']))
    story.append(Paragraph(
        "This is no longer just a photography retainer. It is a full embedded creative department:<br/><br/>"
        "- <b>Photography</b> — project, award, lifestyle, team<br/>"
        "- <b>Marketing strategy</b><br/>"
        "- <b>Website development &amp; management</b><br/>"
        "- <b>Content creation</b> — social, editorial, proposals<br/>"
        "- <b>Brand strategy and visual identity</b><br/><br/>"
        "\"Retainer\" used in body copy to explain billing structure, not in the service name.<br/><br/>"
        "<b>Anchor case study:</b> Balmoral Construction — 1+ year on retainer, managing website and "
        "all creative services for the business. Best existing proof of the Creative Partner model.",
        styles['Body']
    ))

    story.append(PageBreak())

    # =====================
    # PAGE-BY-PAGE REBUILD CHECKLIST
    # =====================
    story.append(Paragraph("7. PAGE-BY-PAGE REBUILD CHECKLIST", styles['SectionTitle']))
    gold_rule()
    story.append(Paragraph(
        "Every page rebuilt must include: meta description, canonical tag, OG tags, "
        "proper alt text on all images, loading=\"lazy\" on below-fold images, single H1, "
        "and correct JSON-LD structured data.",
        styles['Body']
    ))
    story.append(Spacer(1, 6))

    pages_checklist = [
        ["Sitewide Header", "Remove G-XXXXXXXXXX GA4 tag. Fix JSON-LD service URLs (/services/X to /X). Add alt to header hero image and logo. Update nav: \"Visual Partner Retainer\" to \"Creative Partner\". Fix /projects-1 to /projects link."],
        ["Homepage /", "Add meta description. Add OG tags. Fix 2 empty alt CTA images. Rename Service 04 in services section. Update service link to /creative-partner."],
        ["/project-photography", "Add meta description, canonical, OG tags. Fix truncated footer LinkedIn HTML. Add lazy loading to gallery images."],
        ["/award-publication-imagery", "Add meta description, canonical, OG tags. Fix 1 missing hero alt text. Add lazy loading."],
        ["/construction-team-content", "FULL REBUILD — currently shows wrong content. Write and deploy actual Build &amp; Team Content page."],
        ["/creative-partner (new)", "FULL REBUILD — new URL slug, new expanded content covering full creative services scope. 301 redirect from /visual-partner-retainer."],
        ["/bio", "Fix dual H1 tags. Add meta description, OG tags. Fix 2 missing alt texts."],
        ["/process", "Add meta description, OG tags. Add HowTo JSON-LD schema. Fix 1 missing hero alt."],
        ["/faqs", "Fix \"architects\" to \"photographers\" typo. Fix \"reach back\" to \"reach out\". Expand FAQ schema to all 17+ questions."],
        ["/contact", "Add meta description, OG tags. Fix 1 missing image alt."],
        ["/projects", "Fix nav links from /projects-1 to /projects. Add meta description. Add body copy for SEO. Add CollectionPage schema."],
        ["/journal", "Fix dual H1. Add meta description, OG tags. Add alt text to ALL 17 blog thumbnails."],
        ["/summerhill-fine-homes", "Add Article + Review schema (missing). Fix 2 missing alt texts."],
        ["/balmoral-construction", "Update to reflect Creative Partner scope. Fix Review author type (Organization to Person)."],
        ["/sitelines-architecture", "Fix testimonial coded as H2. Fix 1 missing alt, 1 generic alt."],
        ["/the-window-merchant", "Fix 7 missing alt texts. Fix title tag (missing brand name). Fix 1 generic alt."],
        ["/lrd-studio-interior-design", "Fix 2 missing alt, 1 empty alt."],
        ["/fitzsimmons-whistler", "Add page-specific JSON-LD (confirmed missing). Rewrite all 23 \"Fitzsimmons\" alt texts with descriptive content."],
        ["/west-10th-vancouver", "Rewrite all 55 numbered alt texts with descriptive content. Add lazy loading (57 images)."],
        ["/balsam-way", "Rewrite all 36 numbered alt texts. Fix 2 missing alts. Add lazy loading."],
        ["/sunset-beach", "Rewrite all 19 numbered alt texts. Fix 1 missing alt. Add lazy loading."],
        ["/seventh-day-adventist-bc-hq", "Fix \"Pit Meadows\" to \"Pitt Meadows\" typo. Replace generic meta description with project-specific."],
        ["/warbler-whistler", "Fix \"that balancing\" grammar issue in body copy."],
        ["7 Location Pages", "Fix /squamish (all 11 alt missing). Fix /whistler (8/10 missing). Standardize URL slugs. Add meta descriptions to all."],
        ["Utility Pages", "No-index: /project-intake-form, /pricing-guide-thank-you. Fix /free-guide title tag."],
        ["Sitemap Cleanup", "Remove stale /services/ sub-pages. Fix /home to /. Fix /projects vs /projects-1. Submit to Google Search Console."],
    ]

    for page, tasks in pages_checklist:
        story.append(KeepTogether([
            Paragraph(f'<b>{page}</b>', styles['BodyBold']),
            Paragraph(tasks, styles['Small']),
            Spacer(1, 4),
        ]))

    story.append(PageBreak())

    # =====================
    # IMPLEMENTATION PRIORITY
    # =====================
    story.append(Paragraph("8. IMPLEMENTATION PRIORITY", styles['SectionTitle']))
    gold_rule()

    story.append(Paragraph("Phase 1: Immediate (5-minute fixes)", styles['SubSection']))
    phase1 = [
        ["1", "Remove placeholder GA4 tag (G-XXXXXXXXXX)", "5 min"],
        ["2", "Fix FAQ typos (architects to photographers, reach back to reach out)", "5 min"],
        ["3", "Fix \"Pit Meadows\" to \"Pitt Meadows\" typo", "2 min"],
        ["4", "Fix Warbler \"that balancing\" grammar", "2 min"],
    ]
    story.append(make_table(["#", "Task", "Est."], phase1, col_widths=[pw * 0.05, pw * 0.8, pw * 0.15]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Phase 2: Same Day", styles['SubSection']))
    phase2 = [
        ["5", "Fix JSON-LD service URLs (/services/X to /X)", "10 min"],
        ["6", "Update nav links: /projects-1 to /projects, rename Service 04", "10 min"],
        ["7", "Submit sitemap to Google Search Console", "15 min"],
    ]
    story.append(make_table(["#", "Task", "Est."], phase2, col_widths=[pw * 0.05, pw * 0.8, pw * 0.15]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Phase 3: This Week — SEO Foundation", styles['SubSection']))
    phase3 = [
        ["8", "Add meta descriptions to all pages (homepage, services, locations first)"],
        ["9", "Add canonical tags to all custom code block pages"],
        ["10", "Add OG tags to all pages"],
        ["11", "Fix /construction-team-content — build correct page content"],
        ["12", "Build /creative-partner page with new expanded scope content"],
        ["13", "Set up 301 redirect from /visual-partner-retainer to /creative-partner"],
        ["14", "Fix dual H1 tags on /bio and /journal"],
        ["15", "No-index utility pages (/project-intake-form, /pricing-guide-thank-you)"],
        ["16", "Clean up sitemap (remove stale URLs, fix /home, fix /projects)"],
    ]
    story.append(make_table(["#", "Task"], phase3, col_widths=[pw * 0.05, pw * 0.95]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Phase 4: This Week / Next — Alt Text &amp; Performance", styles['SubSection']))
    phase4 = [
        ["17", "Fix sitewide header hero image alt (fixes ~15 pages at once)"],
        ["18", "Add alt text to /journal (17 thumbnails)"],
        ["19", "Add alt text to /squamish-architectural-photography (11 images)"],
        ["20", "Add alt text to /whistler-architectural-photography (8 images)"],
        ["21", "Fix /the-window-merchant alt text (7 missing)"],
        ["22", "Rewrite /fitzsimmons-whistler alt text (23 images saying just \"Fitzsimmons\")"],
        ["23", "Rewrite /west-10th-vancouver numbered alt text (55 images)"],
        ["24", "Rewrite /balsam-way numbered alt text (36 images)"],
        ["25", "Rewrite /sunset-beach numbered alt text (19 images)"],
        ["26", "Add loading=\"lazy\" to all below-fold images across all code blocks"],
    ]
    story.append(make_table(["#", "Task"], phase4, col_widths=[pw * 0.05, pw * 0.95]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Phase 5: Ongoing — Schema &amp; Polish", styles['SubSection']))
    phase5 = [
        ["27", "Add Fitzsimmons page-specific JSON-LD (confirmed missing)"],
        ["28", "Add Summerhill Article + Review schema"],
        ["29", "Expand FAQ schema to all 17+ questions"],
        ["30", "Add HowTo schema to /process page"],
        ["31", "Standardize location page URL slugs + 301 redirects"],
        ["32", "Standardize title tag format (separator, brand name)"],
        ["33", "Unify brand voice (I vs We) per brand bible"],
        ["34", "Fix remaining scattered missing alt text (bio, contact, LRD, etc.)"],
        ["35", "Monitor Google Search Console indexing progress"],
    ]
    story.append(make_table(["#", "Task"], phase5, col_widths=[pw * 0.05, pw * 0.95]))

    story.append(Spacer(1, 0.3 * inch))
    dark_rule()
    story.append(Paragraph(
        "mattanthonyphoto.com Website Rebuild Action Plan — March 19, 2026<br/>"
        "35 action items across 5 phases.",
        styles['Footer']
    ))

    # Build
    doc.build(story)
    return output_path


if __name__ == "__main__":
    output = os.path.expanduser(
        "~/Documents/Claude/business/website/mattanthonyphoto-website-rebuild-action-plan.pdf"
    )
    result = build_pdf(output)
    print(f"PDF generated: {result}")
