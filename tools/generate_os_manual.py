#!/usr/bin/env python3
"""
Agency OS Manual PDF Generator
Generates a binder-ready, branded PDF manual from structured content.
Brand: Matt Anthony Photography
Colors: Ink #1A1A18, Paper #F6F4F0, Gold #C9A96E, Stone #8A8579
Fonts: Josefin Sans (display), Cormorant Garamond (headlines), DM Sans (body)
Format: 8.5x11 Letter, wide left margin for 3-hole punch
"""

import json
import os
import re
import textwrap
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, Frame, PageTemplate, BaseDocTemplate, NextPageTemplate,
    Flowable, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, Line, String
from reportlab.graphics import renderPDF

# ── Brand Colors ──────────────────────────────────────────
INK = HexColor("#1A1A18")
PAPER = HexColor("#F6F4F0")
GOLD = HexColor("#C9A96E")
WARM_MUTED = HexColor("#B8975A")
STONE = HexColor("#8A8579")
LIGHT_STONE = HexColor("#D9D5CD")
OFF_WHITE = HexColor("#EEECE6")

# ── Paths ─────────────────────────────────────────────────
FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".tmp", "fonts")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".tmp")
CONTENT_FILE = os.path.join(OUTPUT_DIR, "os_manual_content.json")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Agency_OS_Manual.pdf")

# ── Page dimensions ───────────────────────────────────────
PAGE_W, PAGE_H = letter  # 8.5 x 11 inches
LEFT_MARGIN = 1.25 * inch   # Extra wide for 3-hole punch
RIGHT_MARGIN = 0.75 * inch
TOP_MARGIN = 0.75 * inch
BOTTOM_MARGIN = 0.85 * inch


def register_fonts():
    """Register brand fonts with reportlab."""
    font_map = {
        "JosefinSans": "JosefinSans-Regular.ttf",
        "JosefinSans-Bold": "JosefinSans-Bold.ttf",
        "Cormorant": "CormorantGaramond-Regular.ttf",
        "Cormorant-Light": "CormorantGaramond-Light.ttf",
        "Cormorant-Bold": "CormorantGaramond-Bold.ttf",
        "DMSans": "DMSans-Regular.ttf",
        "DMSans-Medium": "DMSans-Medium.ttf",
        "DMSans-Bold": "DMSans-Bold.ttf",
        "DMSans-Light": "DMSans-Light.ttf",
        "DMSans-Italic": "DMSans-Italic.ttf",
    }
    for name, filename in font_map.items():
        path = os.path.join(FONT_DIR, filename)
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
            except Exception as e:
                print(f"Warning: Could not register {name}: {e}")
        else:
            print(f"Warning: Font file not found: {path}")

    # Register font families for bold/italic mapping
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    try:
        registerFontFamily(
            'DMSans',
            normal='DMSans',
            bold='DMSans-Bold',
            italic='DMSans-Italic',
            boldItalic='DMSans-Bold'
        )
        registerFontFamily(
            'Cormorant',
            normal='Cormorant',
            bold='Cormorant-Bold',
            italic='Cormorant-Light',
            boldItalic='Cormorant-Bold'
        )
    except Exception:
        pass


def build_styles():
    """Create all paragraph styles for the manual."""
    styles = {}

    # Cover page styles
    styles['cover_title'] = ParagraphStyle(
        'cover_title',
        fontName='Cormorant-Light',
        fontSize=42,
        leading=50,
        textColor=PAPER,
        alignment=TA_CENTER,
    )
    styles['cover_subtitle'] = ParagraphStyle(
        'cover_subtitle',
        fontName='JosefinSans',
        fontSize=11,
        leading=16,
        textColor=GOLD,
        alignment=TA_CENTER,
        spaceAfter=6,
        textTransform='uppercase',
    )
    styles['cover_meta'] = ParagraphStyle(
        'cover_meta',
        fontName='DMSans',
        fontSize=9,
        leading=14,
        textColor=LIGHT_STONE,
        alignment=TA_CENTER,
    )

    # Section divider styles
    styles['section_number'] = ParagraphStyle(
        'section_number',
        fontName='JosefinSans-Bold',
        fontSize=72,
        leading=80,
        textColor=GOLD,
        alignment=TA_LEFT,
    )
    styles['section_title'] = ParagraphStyle(
        'section_title',
        fontName='Cormorant',
        fontSize=36,
        leading=42,
        textColor=INK,
        alignment=TA_LEFT,
        spaceAfter=12,
    )
    styles['section_desc'] = ParagraphStyle(
        'section_desc',
        fontName='DMSans-Light',
        fontSize=11,
        leading=18,
        textColor=STONE,
        alignment=TA_LEFT,
        spaceAfter=6,
    )

    # TOC styles
    styles['toc_section'] = ParagraphStyle(
        'toc_section',
        fontName='JosefinSans-Bold',
        fontSize=11,
        leading=20,
        textColor=INK,
        leftIndent=0,
        spaceBefore=14,
        spaceAfter=2,
    )
    styles['toc_item'] = ParagraphStyle(
        'toc_item',
        fontName='DMSans',
        fontSize=9.5,
        leading=16,
        textColor=STONE,
        leftIndent=16,
    )

    # Content heading styles
    styles['h1'] = ParagraphStyle(
        'h1',
        fontName='Cormorant-Bold',
        fontSize=22,
        leading=28,
        textColor=INK,
        spaceBefore=24,
        spaceAfter=10,
        borderPadding=(0, 0, 4, 0),
    )
    styles['h2'] = ParagraphStyle(
        'h2',
        fontName='JosefinSans-Bold',
        fontSize=13,
        leading=18,
        textColor=INK,
        spaceBefore=18,
        spaceAfter=8,
    )
    styles['h3'] = ParagraphStyle(
        'h3',
        fontName='DMSans-Bold',
        fontSize=11,
        leading=16,
        textColor=INK,
        spaceBefore=14,
        spaceAfter=6,
    )

    # Body text
    styles['body'] = ParagraphStyle(
        'body',
        fontName='DMSans',
        fontSize=9.5,
        leading=15,
        textColor=INK,
        alignment=TA_LEFT,
        spaceAfter=6,
    )
    styles['body_bold'] = ParagraphStyle(
        'body_bold',
        parent=styles['body'],
        fontName='DMSans-Bold',
    )

    # Callout / blockquote
    styles['callout'] = ParagraphStyle(
        'callout',
        fontName='DMSans',
        fontSize=9,
        leading=14,
        textColor=STONE,
        leftIndent=16,
        borderPadding=(8, 12, 8, 12),
        spaceAfter=10,
        spaceBefore=6,
    )
    styles['callout_important'] = ParagraphStyle(
        'callout_important',
        fontName='DMSans-Medium',
        fontSize=9.5,
        leading=15,
        textColor=INK,
        leftIndent=16,
        borderPadding=(8, 12, 8, 12),
        backColor=OFF_WHITE,
        spaceAfter=10,
        spaceBefore=6,
    )

    # Bullet points
    styles['bullet'] = ParagraphStyle(
        'bullet',
        fontName='DMSans',
        fontSize=9.5,
        leading=15,
        textColor=INK,
        leftIndent=28,
        firstLineIndent=-14,
        spaceAfter=3,
    )
    styles['bullet_sub'] = ParagraphStyle(
        'bullet_sub',
        parent=styles['bullet'],
        leftIndent=42,
        fontSize=9,
        textColor=STONE,
    )

    # Table styles
    styles['table_header'] = ParagraphStyle(
        'table_header',
        fontName='JosefinSans-Bold',
        fontSize=8,
        leading=12,
        textColor=INK,
    )
    styles['table_cell'] = ParagraphStyle(
        'table_cell',
        fontName='DMSans',
        fontSize=8.5,
        leading=13,
        textColor=INK,
    )

    # Page header/footer
    styles['page_header'] = ParagraphStyle(
        'page_header',
        fontName='JosefinSans',
        fontSize=7,
        leading=10,
        textColor=STONE,
    )
    styles['page_number'] = ParagraphStyle(
        'page_number',
        fontName='DMSans',
        fontSize=8,
        leading=10,
        textColor=STONE,
        alignment=TA_RIGHT,
    )

    # Horizontal rule
    styles['rule_text'] = ParagraphStyle(
        'rule_text',
        fontName='DMSans',
        fontSize=2,
        leading=2,
        spaceAfter=8,
        spaceBefore=8,
    )

    return styles


class GoldRule(Flowable):
    """A horizontal gold rule line."""
    def __init__(self, width, thickness=0.5, color=GOLD):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.color = color
        self.height = thickness + 4

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 2, self.width, 2)


class LightRule(Flowable):
    """A thin light stone rule for separating content."""
    def __init__(self, width):
        Flowable.__init__(self)
        self.width = width
        self.height = 8

    def draw(self):
        self.canv.setStrokeColor(LIGHT_STONE)
        self.canv.setLineWidth(0.25)
        self.canv.line(0, 4, self.width, 4)


class CalloutBox(Flowable):
    """A styled callout box with left gold border."""
    def __init__(self, content, width, styles, important=False):
        Flowable.__init__(self)
        self.content_text = content
        self.full_width = width
        self.styles = styles
        self.important = important
        # Pre-calculate height
        style = styles['callout_important'] if important else styles['callout']
        p = Paragraph(content, style)
        w, h = p.wrap(width - 24, 1000)
        self.para = p
        self.height = h + 16
        self.width = width

    def draw(self):
        # Background
        if self.important:
            self.canv.setFillColor(OFF_WHITE)
        else:
            self.canv.setFillColor(HexColor("#FAFAF8"))
        self.canv.roundRect(0, 0, self.full_width, self.height, 2, fill=1, stroke=0)

        # Left border
        self.canv.setFillColor(GOLD if self.important else LIGHT_STONE)
        self.canv.rect(0, 0, 3, self.height, fill=1, stroke=0)

        # Text
        self.para.wrapOn(self.canv, self.full_width - 24, self.height)
        self.para.drawOn(self.canv, 16, self.height - self.para.height - 8)


class SectionDividerPage(Flowable):
    """Full-page section divider with number, title, and description."""
    def __init__(self, number, title, description, styles):
        Flowable.__init__(self)
        self.number = number
        self.title = title
        self.description = description
        self.styles = styles
        self.width = PAGE_W - LEFT_MARGIN - RIGHT_MARGIN
        self.height = PAGE_H - TOP_MARGIN - BOTTOM_MARGIN

    def draw(self):
        c = self.canv
        w = self.width
        h = self.height

        # Large section number
        num_text = f"{self.number:02d}"
        c.setFont("JosefinSans-Bold", 96)
        c.setFillColor(GOLD)
        c.drawString(0, h - 120, num_text)

        # Gold rule under number
        c.setStrokeColor(GOLD)
        c.setLineWidth(2)
        c.line(0, h - 135, 80, h - 135)

        # Section title
        c.setFont("Cormorant", 36)
        c.setFillColor(INK)
        c.drawString(0, h - 190, self.title)

        # Description
        if self.description:
            style = self.styles['section_desc']
            p = Paragraph(self.description, style)
            p.wrapOn(c, w * 0.7, 200)
            p.drawOn(c, 0, h - 230)

        # Bottom-right section label (for binder tab reference)
        c.setFont("JosefinSans", 8)
        c.setFillColor(STONE)
        c.drawRightString(w, 10, f"SECTION {self.number:02d}")


class ManualDocTemplate(BaseDocTemplate):
    """Custom document template with headers, footers, and page numbers."""

    def __init__(self, filename, styles, sections, **kwargs):
        self.manual_styles = styles
        self.sections = sections
        self.current_section = ""
        self.current_section_num = 0
        BaseDocTemplate.__init__(self, filename, **kwargs)

        # Define frames
        content_frame = Frame(
            LEFT_MARGIN, BOTTOM_MARGIN,
            PAGE_W - LEFT_MARGIN - RIGHT_MARGIN,
            PAGE_H - TOP_MARGIN - BOTTOM_MARGIN,
            id='content',
            leftPadding=0, rightPadding=0,
            topPadding=0, bottomPadding=0,
        )

        # Cover page frame (centered, no header/footer)
        cover_frame = Frame(
            0.75 * inch, 0.75 * inch,
            PAGE_W - 1.5 * inch, PAGE_H - 1.5 * inch,
            id='cover',
        )

        self.addPageTemplates([
            PageTemplate(id='cover', frames=cover_frame, onPage=self._cover_page),
            PageTemplate(id='content', frames=content_frame, onPage=self._content_page),
            PageTemplate(id='divider', frames=content_frame, onPage=self._divider_page),
            PageTemplate(id='toc', frames=content_frame, onPage=self._toc_page),
        ])

    def _cover_page(self, canvas, doc):
        """Draw the cover page background."""
        canvas.saveState()
        # Full dark background
        canvas.setFillColor(INK)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

        # Gold accent line at top
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(3)
        canvas.line(0.75 * inch, PAGE_H - 0.6 * inch, PAGE_W - 0.75 * inch, PAGE_H - 0.6 * inch)

        # Gold accent line at bottom
        canvas.line(0.75 * inch, 0.6 * inch, PAGE_W - 0.75 * inch, 0.6 * inch)

        canvas.restoreState()

    def _toc_page(self, canvas, doc):
        """TOC page with minimal header."""
        canvas.saveState()
        # Header line
        canvas.setStrokeColor(LIGHT_STONE)
        canvas.setLineWidth(0.25)
        canvas.line(LEFT_MARGIN, PAGE_H - TOP_MARGIN + 10, PAGE_W - RIGHT_MARGIN, PAGE_H - TOP_MARGIN + 10)

        # Footer
        canvas.setFont("DMSans", 8)
        canvas.setFillColor(STONE)
        canvas.drawRightString(PAGE_W - RIGHT_MARGIN, BOTTOM_MARGIN - 20, f"{doc.page}")
        canvas.drawString(LEFT_MARGIN, BOTTOM_MARGIN - 20, "AGENCY OS MANUAL")
        canvas.restoreState()

    def _divider_page(self, canvas, doc):
        """Section divider page - minimal chrome."""
        canvas.saveState()
        # Thin top gold line
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(0.5)
        canvas.line(LEFT_MARGIN, PAGE_H - TOP_MARGIN + 10, PAGE_W - RIGHT_MARGIN, PAGE_H - TOP_MARGIN + 10)

        # Footer with page number
        canvas.setFont("DMSans", 8)
        canvas.setFillColor(STONE)
        canvas.drawRightString(PAGE_W - RIGHT_MARGIN, BOTTOM_MARGIN - 20, f"{doc.page}")
        canvas.restoreState()

    def _content_page(self, canvas, doc):
        """Standard content page with header and footer."""
        canvas.saveState()

        # Header: section name on left, gold rule
        canvas.setFont("JosefinSans", 7)
        canvas.setFillColor(STONE)
        header_text = self.current_section.upper() if self.current_section else "AGENCY OS"
        canvas.drawString(LEFT_MARGIN, PAGE_H - TOP_MARGIN + 14, header_text)

        # Header rule
        canvas.setStrokeColor(LIGHT_STONE)
        canvas.setLineWidth(0.25)
        canvas.line(LEFT_MARGIN, PAGE_H - TOP_MARGIN + 10, PAGE_W - RIGHT_MARGIN, PAGE_H - TOP_MARGIN + 10)

        # Footer: manual name left, page number right
        canvas.setFont("DMSans", 8)
        canvas.setFillColor(STONE)
        canvas.drawString(LEFT_MARGIN, BOTTOM_MARGIN - 20, "Matt Anthony Photography  |  Agency OS v2.0")

        # Footer rule
        canvas.line(LEFT_MARGIN, BOTTOM_MARGIN - 8, PAGE_W - RIGHT_MARGIN, BOTTOM_MARGIN - 8)

        # Page number
        canvas.drawRightString(PAGE_W - RIGHT_MARGIN, BOTTOM_MARGIN - 20, f"{doc.page}")

        # Three-hole punch guides (very faint)
        canvas.setStrokeColor(HexColor("#E8E6E0"))
        canvas.setLineWidth(0.15)
        punch_x = 0.5 * inch
        for y_pos in [PAGE_H / 2, PAGE_H / 2 + 3.5 * inch, PAGE_H / 2 - 3.5 * inch]:
            canvas.circle(punch_x, y_pos, 4, stroke=1, fill=0)

        canvas.restoreState()


def clean_markdown(text):
    """Convert Notion markdown to reportlab-safe XML."""
    if not text:
        return ""

    # Remove Notion-specific tags
    text = re.sub(r'<page url="[^"]*">(.*?)</page>', r'\1', text)
    text = re.sub(r'</?ancestor-path>.*?</ancestor-path>', '', text, flags=re.DOTALL)
    text = re.sub(r'</?properties>.*?</properties>', '', text, flags=re.DOTALL)
    text = re.sub(r'</?content>', '', text)
    text = re.sub(r'</?page[^>]*>', '', text)

    # Convert markdown bold/italic to reportlab XML
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<b><i>\1</i></b>', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)

    # Convert markdown links
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)

    # Escape XML special chars (but not our tags)
    text = text.replace('&', '&amp;')
    text = text.replace('<b>', '§BOLD§').replace('</b>', '§/BOLD§')
    text = text.replace('<i>', '§ITAL§').replace('</i>', '§/ITAL§')
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('§BOLD§', '<b>').replace('§/BOLD§', '</b>')
    text = text.replace('§ITAL§', '<i>').replace('§/ITAL§', '</i>')

    return text.strip()


def parse_content_to_flowables(text, styles, content_width):
    """Parse markdown-ish content into reportlab flowables."""
    flowables = []
    lines = text.split('\n')
    i = 0
    in_table = False
    table_rows = []
    has_header = False

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Horizontal rule
        if line == '---' or line == '***':
            flowables.append(Spacer(1, 4))
            flowables.append(LightRule(content_width))
            flowables.append(Spacer(1, 4))
            i += 1
            continue

        # Headers
        if line.startswith('#### '):
            text_content = clean_markdown(line[5:])
            flowables.append(Paragraph(text_content, styles['h3']))
            i += 1
            continue
        if line.startswith('### '):
            text_content = clean_markdown(line[4:])
            flowables.append(Paragraph(text_content, styles['h3']))
            i += 1
            continue
        if line.startswith('## '):
            text_content = clean_markdown(line[3:])
            flowables.append(Paragraph(text_content, styles['h2']))
            i += 1
            continue
        if line.startswith('# '):
            text_content = clean_markdown(line[2:])
            flowables.append(Paragraph(text_content, styles['h1']))
            flowables.append(GoldRule(min(content_width * 0.3, 120)))
            i += 1
            continue

        # Blockquote / callout
        if line.startswith('> '):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('> '):
                quote_lines.append(lines[i].strip()[2:])
                i += 1
            quote_text = clean_markdown(' '.join(quote_lines))
            is_important = any(kw in quote_text.lower() for kw in ['important', 'rule', 'warning', 'do not', 'critical', 'red flag'])
            try:
                flowables.append(CalloutBox(quote_text, content_width, styles, important=is_important))
            except Exception:
                style = styles['callout_important'] if is_important else styles['callout']
                flowables.append(Paragraph(quote_text, style))
            continue

        # Table detection (Notion format)
        if line.startswith('<table') or line.startswith('|'):
            # Skip Notion XML tables - convert to simple text
            if line.startswith('<table'):
                table_lines = []
                while i < len(lines) and '</table>' not in lines[i]:
                    table_lines.append(lines[i])
                    i += 1
                i += 1  # skip closing tag
                # Parse table rows
                rows = []
                current_row = []
                is_header_row = 'header-row' in table_lines[0] if table_lines else False
                for tl in table_lines:
                    tl = tl.strip()
                    if tl.startswith('<td>'):
                        cell_content = re.sub(r'</?td>', '', tl).strip()
                        cell_content = clean_markdown(cell_content)
                        current_row.append(cell_content)
                    elif tl == '</tr>' and current_row:
                        rows.append(current_row)
                        current_row = []

                if rows:
                    flowables.extend(build_table(rows, styles, content_width, is_header_row))
                continue

            # Markdown pipe tables
            if line.startswith('|'):
                table_lines_md = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines_md.append(lines[i].strip())
                    i += 1
                rows = []
                for tl in table_lines_md:
                    if '---' in tl:
                        continue
                    cells = [c.strip() for c in tl.split('|')[1:-1]]
                    if cells:
                        rows.append([clean_markdown(c) for c in cells])
                if rows:
                    flowables.extend(build_table(rows, styles, content_width, True))
                continue

        # Bullet points
        if line.startswith('- ') or line.startswith('* '):
            bullet_text = clean_markdown(line[2:])
            flowables.append(Paragraph(f"•  {bullet_text}", styles['bullet']))
            i += 1
            continue

        # Sub-bullets
        if line.startswith('  - ') or line.startswith('  * ') or line.startswith('\t- '):
            bullet_text = clean_markdown(line.lstrip(' \t')[2:])
            flowables.append(Paragraph(f"–  {bullet_text}", styles['bullet_sub']))
            i += 1
            continue

        # Numbered lists
        num_match = re.match(r'^(\d+)\.\s+(.*)', line)
        if num_match:
            num = num_match.group(1)
            text_content = clean_markdown(num_match.group(2))
            flowables.append(Paragraph(f"{num}.  {text_content}", styles['bullet']))
            i += 1
            continue

        # Regular paragraph
        para_lines = [line]
        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            if (not next_line or next_line.startswith('#') or next_line.startswith('>')
                or next_line.startswith('-') or next_line.startswith('*')
                or next_line.startswith('|') or next_line.startswith('<table')
                or next_line == '---'):
                break
            para_lines.append(next_line)
            i += 1

        para_text = clean_markdown(' '.join(para_lines))
        if para_text:
            flowables.append(Paragraph(para_text, styles['body']))

    return flowables


def build_table(rows, styles, content_width, has_header=True):
    """Build a styled reportlab table from rows."""
    flowables = []
    if not rows:
        return flowables

    # Convert to Paragraph objects
    num_cols = max(len(r) for r in rows)
    col_width = (content_width - 8) / num_cols if num_cols else content_width

    table_data = []
    for ri, row in enumerate(rows):
        table_row = []
        for ci, cell in enumerate(row):
            style = styles['table_header'] if (ri == 0 and has_header) else styles['table_cell']
            try:
                table_row.append(Paragraph(cell, style))
            except Exception:
                table_row.append(Paragraph(cell.replace('<', '&lt;').replace('>', '&gt;'), style))
        # Pad if needed
        while len(table_row) < num_cols:
            table_row.append(Paragraph("", styles['table_cell']))
        table_data.append(table_row)

    if not table_data:
        return flowables

    col_widths = [col_width] * num_cols
    t = Table(table_data, colWidths=col_widths, repeatRows=1 if has_header else 0)

    style_commands = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.25, LIGHT_STONE),
        ('LINEBELOW', (0, 0), (-1, 0), 1, GOLD),
    ]

    if has_header:
        style_commands.append(('BACKGROUND', (0, 0), (-1, 0), OFF_WHITE))

    # Alternate row colors
    for ri in range(1, len(table_data)):
        if ri % 2 == 0:
            style_commands.append(('BACKGROUND', (0, ri), (-1, ri), HexColor("#FCFCFA")))

    t.setStyle(TableStyle(style_commands))
    flowables.append(Spacer(1, 6))
    flowables.append(t)
    flowables.append(Spacer(1, 8))

    return flowables


def build_cover_page(styles):
    """Build the cover page flowables."""
    flowables = []
    flowables.append(Spacer(1, 2.5 * inch))
    flowables.append(Paragraph("Agency<br/>Operating System", styles['cover_title']))
    flowables.append(Spacer(1, 0.3 * inch))
    flowables.append(Paragraph("MATT ANTHONY PHOTOGRAPHY", styles['cover_subtitle']))
    flowables.append(Spacer(1, 0.15 * inch))
    flowables.append(Paragraph(
        "Documenting design intent for those who build with purpose",
        ParagraphStyle('cover_tagline', parent=styles['cover_meta'], fontName='Cormorant-Light', fontSize=12, textColor=LIGHT_STONE)
    ))
    flowables.append(Spacer(1, 1.5 * inch))
    flowables.append(Paragraph("Version 2.0  •  Effective January 9, 2026", styles['cover_meta']))
    flowables.append(Spacer(1, 0.1 * inch))
    flowables.append(Paragraph("Squamish, British Columbia", styles['cover_meta']))
    flowables.append(Spacer(1, 0.8 * inch))
    flowables.append(Paragraph(
        "CONFIDENTIAL — FOR INTERNAL USE ONLY",
        ParagraphStyle('cover_conf', parent=styles['cover_meta'], fontName='JosefinSans', fontSize=7, textColor=WARM_MUTED)
    ))
    return flowables


def build_toc(sections, styles, content_width):
    """Build the table of contents."""
    flowables = []
    flowables.append(Spacer(1, 0.3 * inch))
    flowables.append(Paragraph("Table of Contents", ParagraphStyle(
        'toc_title', fontName='Cormorant', fontSize=28, leading=34, textColor=INK, spaceAfter=8
    )))
    flowables.append(GoldRule(content_width * 0.25))
    flowables.append(Spacer(1, 0.2 * inch))

    for section in sections:
        num = section['number']
        title = section['title']
        flowables.append(Paragraph(
            f"<b>{num:02d}</b>&nbsp;&nbsp;&nbsp;{title}",
            styles['toc_section']
        ))
        for sub in section.get('sub_pages', []):
            flowables.append(Paragraph(f"→  {sub['title']}", styles['toc_item']))

    flowables.append(Spacer(1, 0.5 * inch))
    flowables.append(LightRule(content_width))
    flowables.append(Spacer(1, 0.15 * inch))
    flowables.append(Paragraph(
        "Do not decide from memory. Do not decide from instinct. Decide from the OS.",
        ParagraphStyle('toc_quote', fontName='Cormorant-Light', fontSize=13, leading=18, textColor=STONE, alignment=TA_CENTER)
    ))

    return flowables


def build_manual(content_data):
    """Build the complete manual PDF."""
    register_fonts()
    styles = build_styles()
    content_width = PAGE_W - LEFT_MARGIN - RIGHT_MARGIN

    sections = content_data['sections']
    story = []

    # ── Cover Page ────────────────────────────────────────
    story.append(NextPageTemplate('cover'))
    story.extend(build_cover_page(styles))
    story.append(PageBreak())

    # ── Table of Contents ─────────────────────────────────
    story.append(NextPageTemplate('toc'))
    story.extend(build_toc(sections, styles, content_width))
    story.append(PageBreak())

    # ── OS Index By Situation ─────────────────────────────
    story.append(NextPageTemplate('content'))
    if content_data.get('os_index'):
        story.append(Paragraph("OS Index By Situation", styles['h1']))
        story.append(GoldRule(content_width * 0.25))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "Something happened and you're not sure what to do? Find your situation below. Each one points to exactly one authoritative document.",
            styles['section_desc']
        ))
        story.append(Spacer(1, 8))
        index_flowables = parse_content_to_flowables(content_data['os_index'], styles, content_width)
        story.extend(index_flowables)
        story.append(PageBreak())

    # ── Sections ──────────────────────────────────────────
    for section in sections:
        num = section['number']
        title = section['title']
        desc = section.get('description', '')

        # Section divider page
        story.append(NextPageTemplate('divider'))
        story.append(SectionDividerPage(num, title, desc, styles))
        story.append(PageBreak())
        story.append(NextPageTemplate('content'))

        # Sub-pages
        for sub in section.get('sub_pages', []):
            sub_title = sub['title']
            sub_content = sub.get('content', '')

            # Update current section for header
            # (handled via doc template)

            # Sub-page title
            story.append(Paragraph(sub_title, styles['h1']))
            story.append(GoldRule(content_width * 0.25))
            story.append(Spacer(1, 8))

            # Parse and add content
            if sub_content:
                flowables = parse_content_to_flowables(sub_content, styles, content_width)
                story.extend(flowables)

            story.append(Spacer(1, 12))
            story.append(LightRule(content_width))
            story.append(PageBreak())

    # ── Build PDF ─────────────────────────────────────────
    doc = ManualDocTemplate(
        OUTPUT_FILE,
        styles,
        sections,
        pagesize=letter,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="Agency Operating System — Matt Anthony Photography",
        author="Matt Anthony",
        subject="Agency OS v2.0 Manual",
    )

    # Custom build to track section names in headers
    class SectionTracker:
        def __init__(self, doc_template, sections):
            self.doc = doc_template
            self.sections = sections

    doc.build(story)
    print(f"✓ Manual generated: {OUTPUT_FILE}")
    print(f"  Pages: {doc.page}")
    return OUTPUT_FILE


if __name__ == "__main__":
    if not os.path.exists(CONTENT_FILE):
        print(f"Content file not found: {CONTENT_FILE}")
        print("Run the content extraction step first.")
        exit(1)

    with open(CONTENT_FILE, 'r') as f:
        content_data = json.load(f)

    build_manual(content_data)
