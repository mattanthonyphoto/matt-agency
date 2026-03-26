"""
Create the Matt Anthony Photography Agency Operating System Manual
as a fully formatted Google Document with table of contents, branded styling,
and all operational content.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]

# Brand colors
INK = {"red": 0.102, "green": 0.102, "blue": 0.094}  # #1A1A18
PAPER = {"red": 0.965, "green": 0.957, "blue": 0.941}  # #F6F4F0
GOLD = {"red": 0.788, "green": 0.663, "blue": 0.431}  # #C9A96E
STONE = {"red": 0.541, "green": 0.522, "blue": 0.475}  # #8A8579
WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}
BLACK = {"red": 0.0, "green": 0.0, "blue": 0.0}
LIGHT_GOLD_BG = {"red": 0.976, "green": 0.961, "blue": 0.929}  # subtle gold tint for table headers


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds


def pt_to_pixels(pt):
    """Convert points to pixels (Google Docs uses points internally)."""
    return pt


class AOSManualBuilder:
    def __init__(self):
        self.creds = get_credentials()
        self.docs_service = build("docs", "v1", credentials=self.creds)
        self.drive_service = build("drive", "v3", credentials=self.creds)
        self.requests = []
        self.index = 1  # current insertion index

    def create_document(self):
        doc = self.docs_service.documents().create(
            body={"title": "Matt Anthony Photography — Agency Operating System"}
        ).execute()
        self.doc_id = doc["documentId"]
        print(f"Document created: https://docs.google.com/document/d/{self.doc_id}/edit")
        return self.doc_id

    def _insert_text(self, text, style_name=None):
        """Insert text and optionally apply a named style."""
        start = self.index
        self.requests.append({
            "insertText": {"location": {"index": start}, "text": text}
        })
        end = start + len(text)
        self.index = end
        if style_name:
            self.requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": end - 1},
                    "paragraphStyle": {"namedStyleType": style_name},
                    "fields": "namedStyleType"
                }
            })
        return start, end

    def _style_text(self, start, end, bold=False, italic=False, font_size=None,
                    color=None, font_family=None, underline=False):
        if end <= start:
            return
        style = {}
        fields = []
        if bold:
            style["bold"] = True
            fields.append("bold")
        if italic:
            style["italic"] = True
            fields.append("italic")
        if underline:
            style["underline"] = True
            fields.append("underline")
        if font_size:
            style["fontSize"] = {"magnitude": font_size, "unit": "PT"}
            fields.append("fontSize")
        if color:
            style["foregroundColor"] = {"color": {"rgbColor": color}}
            fields.append("foregroundColor")
        if font_family:
            style["weightedFontFamily"] = {"fontFamily": font_family}
            fields.append("weightedFontFamily")
        if fields:
            self.requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "textStyle": style,
                    "fields": ",".join(fields)
                }
            })

    def _set_paragraph_alignment(self, start, end, alignment="CENTER"):
        if end <= start:
            return
        self.requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end},
                "paragraphStyle": {"alignment": alignment},
                "fields": "alignment"
            }
        })

    def _set_paragraph_spacing(self, start, end, before=0, after=0):
        if end <= start:
            return
        style = {}
        fields = []
        if before:
            style["spaceAbove"] = {"magnitude": before, "unit": "PT"}
            fields.append("spaceAbove")
        if after:
            style["spaceBelow"] = {"magnitude": after, "unit": "PT"}
            fields.append("spaceBelow")
        if fields:
            self.requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "paragraphStyle": style,
                    "fields": ",".join(fields)
                }
            })

    def _insert_page_break(self):
        self.requests.append({
            "insertText": {"location": {"index": self.index}, "text": "\n"}
        })
        self.index += 1
        self.requests.append({
            "insertPageBreak": {"location": {"index": self.index}}
        })
        self.index += 1

    def _add_horizontal_rule(self):
        """Add a gold-colored divider line using underscores."""
        start = self.index
        text = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        self._insert_text(text)
        self._style_text(start, start + len(text) - 1, color=GOLD, font_size=8)
        self._set_paragraph_alignment(start, start + len(text) - 1, "CENTER")

    def _add_heading(self, text, level=1):
        """Add a heading with brand styling."""
        style_map = {1: "HEADING_1", 2: "HEADING_2", 3: "HEADING_3"}
        start, end = self._insert_text(text + "\n", style_map.get(level, "HEADING_1"))
        if level == 1:
            self._style_text(start, end - 1, font_family="Cormorant Garamond",
                           font_size=28, color=INK, bold=False)
            self._set_paragraph_spacing(start, end - 1, before=24, after=8)
        elif level == 2:
            self._style_text(start, end - 1, font_family="Cormorant Garamond",
                           font_size=20, color=INK, bold=False)
            self._set_paragraph_spacing(start, end - 1, before=18, after=6)
        elif level == 3:
            self._style_text(start, end - 1, font_family="DM Sans",
                           font_size=13, color=GOLD, bold=True)
            self._set_paragraph_spacing(start, end - 1, before=12, after=4)

    def _add_body(self, text):
        """Add body text."""
        start, end = self._insert_text(text + "\n", "NORMAL_TEXT")
        self._style_text(start, end - 1, font_family="DM Sans", font_size=10.5, color=INK)
        self._set_paragraph_spacing(start, end - 1, after=6)

    def _add_body_bold(self, text):
        start, end = self._insert_text(text + "\n", "NORMAL_TEXT")
        self._style_text(start, end - 1, font_family="DM Sans", font_size=10.5,
                        color=INK, bold=True)
        self._set_paragraph_spacing(start, end - 1, after=6)

    def _add_callout(self, text):
        """Add a callout/highlight block."""
        start, end = self._insert_text("▎ " + text + "\n", "NORMAL_TEXT")
        self._style_text(start, end - 1, font_family="DM Sans", font_size=10.5,
                        color=GOLD, italic=True)
        self._set_paragraph_spacing(start, end - 1, before=8, after=8)

    def _add_bullet(self, text):
        """Add a bullet point."""
        start, end = self._insert_text(text + "\n", "NORMAL_TEXT")
        self._style_text(start, end - 1, font_family="DM Sans", font_size=10.5, color=INK)
        self.requests.append({
            "createParagraphBullets": {
                "range": {"startIndex": start, "endIndex": end},
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
            }
        })

    def _add_numbered(self, text):
        """Add a numbered list item."""
        start, end = self._insert_text(text + "\n", "NORMAL_TEXT")
        self._style_text(start, end - 1, font_family="DM Sans", font_size=10.5, color=INK)
        self.requests.append({
            "createParagraphBullets": {
                "range": {"startIndex": start, "endIndex": end},
                "bulletPreset": "NUMBERED_DECIMAL_NESTED"
            }
        })

    def _add_table(self, headers, rows):
        """Insert a formatted table."""
        num_rows = len(rows) + 1
        num_cols = len(headers)
        self.requests.append({
            "insertTable": {
                "location": {"index": self.index},
                "rows": num_rows,
                "columns": num_cols
            }
        })
        # We need to flush requests to get the table index, then populate
        # Instead, we'll track the table and populate after
        self._pending_tables = getattr(self, '_pending_tables', [])
        self._pending_tables.append({
            "insert_index": self.index,
            "headers": headers,
            "rows": rows
        })
        # Estimate index advancement for table
        # Each cell has \n, plus table structure
        # Rough estimate: (num_rows * num_cols * 2) + 4
        self.index += (num_rows * num_cols * 2) + num_rows + 2

    def _add_spacer(self):
        start, end = self._insert_text("\n", "NORMAL_TEXT")
        self._set_paragraph_spacing(start, end - 1, before=2, after=2)
        self._style_text(start, end - 1, font_size=4)

    # =========================================================================
    # DOCUMENT SECTIONS
    # =========================================================================

    def build_cover_page(self):
        """Create the cover page."""
        # Add some spacing
        for _ in range(6):
            self._add_spacer()

        # Title
        start, end = self._insert_text("MATT ANTHONY PHOTOGRAPHY\n", "HEADING_1")
        self._style_text(start, end - 1, font_family="Josefin Sans", font_size=14,
                        color=GOLD, bold=False)
        self._set_paragraph_alignment(start, end - 1, "CENTER")
        self._set_paragraph_spacing(start, end - 1, after=8)

        # Main title
        start, end = self._insert_text("Agency Operating System\n", "HEADING_1")
        self._style_text(start, end - 1, font_family="Cormorant Garamond", font_size=42,
                        color=INK, bold=False)
        self._set_paragraph_alignment(start, end - 1, "CENTER")
        self._set_paragraph_spacing(start, end - 1, after=4)

        self._add_horizontal_rule()

        # Subtitle
        start, end = self._insert_text("The Complete Operational Manual\n", "NORMAL_TEXT")
        self._style_text(start, end - 1, font_family="DM Sans", font_size=14,
                        color=STONE)
        self._set_paragraph_alignment(start, end - 1, "CENTER")
        self._set_paragraph_spacing(start, end - 1, after=40)

        # Details
        for line in [
            "Version 1.0  —  March 2026",
            "Squamish, British Columbia",
            "mattanthonyphoto.com",
            "info@mattanthonyphoto.com  |  604.765.9270",
        ]:
            start, end = self._insert_text(line + "\n", "NORMAL_TEXT")
            self._style_text(start, end - 1, font_family="DM Sans", font_size=10,
                            color=STONE)
            self._set_paragraph_alignment(start, end - 1, "CENTER")

        for _ in range(4):
            self._add_spacer()

        # Confidentiality notice
        start, end = self._insert_text(
            "CONFIDENTIAL — This document contains proprietary business information.\n",
            "NORMAL_TEXT"
        )
        self._style_text(start, end - 1, font_family="DM Sans", font_size=8,
                        color=STONE, italic=True)
        self._set_paragraph_alignment(start, end - 1, "CENTER")

        self._insert_page_break()

    def build_toc(self):
        """Build manual table of contents."""
        self._add_heading("Table of Contents")
        self._add_horizontal_rule()
        self._add_spacer()

        chapters = [
            ("01", "Company Overview"),
            ("02", "Brand Identity & Voice"),
            ("03", "Ideal Client Profiles"),
            ("04", "Service Offerings"),
            ("05", "Pricing & Rate Card"),
            ("06", "Financial Framework"),
            ("07", "Sales Process"),
            ("08", "Operations"),
            ("09", "Team Standards"),
            ("10", "Marketing & Content Strategy"),
            ("11", "Lead Generation & Pipeline"),
            ("12", "Technology Stack"),
            ("13", "Competitive Landscape"),
            ("14", "Growth Plan & Quarterly Rocks"),
            ("15", "AOS Rules & Governance"),
        ]
        for num, title in chapters:
            start, end = self._insert_text(f"{num}    {title}\n", "NORMAL_TEXT")
            self._style_text(start, start + len(num), font_family="Josefin Sans",
                           font_size=11, color=GOLD, bold=True)
            self._style_text(start + len(num), end - 1, font_family="Cormorant Garamond",
                           font_size=13, color=INK)
            self._set_paragraph_spacing(start, end - 1, before=6, after=6)

        self._insert_page_break()

    def build_chapter_01(self):
        """Company Overview."""
        self._add_chapter_header("01", "Company Overview")

        self._add_body("Matt Anthony Photography is a professional architectural and interiors photography business serving the construction and design industry across British Columbia. Based in Squamish, BC, the business operates as a creative partner — not a vendor — for architects, custom home builders, interior designers, and construction firms.")
        self._add_spacer()
        self._add_body("The brand philosophy centers on documenting design intent: clarity, accuracy, and intention over spectacle. The business is building toward a scalable, retainer-based media service model with plans to expand beyond solo shooting.")

        self._add_heading("Business Details", 2)
        for item in [
            "Owner: Matt Anthony",
            "Location: Squamish, British Columbia, Canada",
            "Website: mattanthonyphoto.com (Squarespace)",
            "Email: info@mattanthonyphoto.com",
            "Phone: 604.765.9270",
            "Instagram: @mattanthonyphoto",
            "LinkedIn: /in/mattanthonyphoto/",
            "Certification: Transport Canada Advanced Drone Pilot",
        ]:
            self._add_bullet(item)

        self._add_heading("Service Areas", 2)
        for area in [
            "Sea-to-Sky Corridor — Squamish, Whistler, Pemberton (home base, no travel fee)",
            "Sunshine Coast — Sechelt, Gibsons, Roberts Creek, Sandy Hook, Gambier Island",
            "Metro Vancouver — Vancouver, North Vancouver, West Vancouver",
            "Fraser Valley — Langley, Abbotsford, Chilliwack, Maple Ridge",
            "Okanagan — Kelowna, Vernon, Penticton (accommodation required)",
        ]:
            self._add_bullet(area)

        self._add_heading("Year 1 Baseline (2025)", 2)
        self._add_body("Total revenue: $105,237 across 89 invoices. Top 2 clients (Balmoral Construction and Window Merchant) represented 49% of revenue. Year 1 was reactive — no formal systems, no AOS. Year 2 (2026) builds the foundation to prove the model works so 2027 can be the acceleration year.")

        self._insert_page_break()

    def build_chapter_02(self):
        """Brand Identity & Voice."""
        self._add_chapter_header("02", "Brand Identity & Voice")

        self._add_heading("Brand Position", 2)
        self._add_body("Matt Anthony Photography positions as a creative partner for the construction and design industry. The work is natural, precise, and intentional — not flashy or stylized. The brand lets the architecture be the subject, presenting it clearly without reinterpretation.")
        self._add_callout("\"Your work defines the space. Let me show the world its full potential.\"")

        self._add_heading("Brand Voice", 2)
        for item in [
            "Professional but warm — consultative, never pushy",
            "Calm, structured, intentional",
            "First person singular (\"I\") on project pages and bio",
            "First person plural (\"We\") on homepage philosophy and service pages",
            "Avoids superlatives and hype — lets the work speak",
            "No brand-speak or marketing jargon",
        ]:
            self._add_bullet(item)

        self._add_heading("Visual Design System", 2)

        self._add_heading("Typography", 3)
        for item in [
            "Josefin Sans (700) — Display titles, navigation, uppercase tags and labels",
            "Cormorant Garamond (300, 400) — Headlines, testimonial quotes, project names",
            "DM Sans (300, 400, 500) — Body text, buttons, labels, meta text",
        ]:
            self._add_bullet(item)

        self._add_heading("Color Palette", 3)
        colors = [
            ("Ink #1A1A18", "Primary dark background, text color"),
            ("Paper #F6F4F0", "Light background, hero text"),
            ("Gold #C9A96E", "Accent color, CTAs, labels, highlights"),
            ("Warm Muted #B8975A", "Secondary gold, labels"),
            ("Stone #8A8579", "Muted body text, meta information"),
            ("Light Stone #D9D5CD", "Borders, light text, location labels"),
            ("Off White #EEECE6", "Quote backgrounds, alternating sections"),
        ]
        for name, usage in colors:
            self._add_bullet(f"{name} — {usage}")

        self._add_heading("Design Principles", 3)
        for item in [
            "Dark backgrounds (#1A1A18) for hero sections, CTAs, footers, and project showcases",
            "Light backgrounds (#F6F4F0) for content and text sections",
            "Gold accent (#C9A96E) for labels, buttons, dividers, and interactive elements",
            "Generous whitespace — content sections padded with 5–6rem vertical, 5vw horizontal",
            "Natural, slightly desaturated image treatment — true to materials",
            "No heavy color grading, film presets, or trendy looks — timeless aesthetic",
        ]:
            self._add_bullet(item)

        self._insert_page_break()

    def build_chapter_03(self):
        """Ideal Client Profiles."""
        self._add_chapter_header("03", "Ideal Client Profiles")

        self._add_heading("Primary Tier", 2)

        self._add_heading("ICP #1 — Architects", 3)
        self._add_body("Design-intent documentation, award submissions (Georgie, AIBC, RAIC), publication features (Dwell, Dezeen, Western Living). These clients value precision, editorial quality, and the ability to capture design narrative. Typically engaged for completed projects and award deadlines.")
        self._add_body_bold("Case study reference: Sitelines Architecture ($6,720 in 2025, 2 projects)")

        self._add_heading("ICP #2 — Custom Home Builders", 3)
        self._add_body("Portfolio imagery for websites, proposals, and social media. Builders need consistent documentation of completed projects to win new business. Highest retainer potential — they have ongoing project flow and need a reliable visual partner. Primary cold email target.")
        self._add_body_bold("Case study reference: Summerhill Fine Homes, Balmoral Construction")

        self._add_heading("ICP #3 — Interior Designers", 3)
        self._add_body("Portfolio building, editorial features, award submissions. Often involved as a second party on architect/builder projects, making them ideal cost-share candidates. Feature-ready photography for publication in shelter magazines.")
        self._add_body_bold("Case study reference: LRD Studio ($3,150 in 2025)")

        self._add_heading("Secondary Tier", 2)
        for item in [
            "Millwork shops and trades — Project documentation, marketing imagery",
            "Construction firms — Team content, progression documentation",
            "Window/glazing companies — Product-in-context photography",
            "Fabricators and specialty trades — Detail documentation for portfolios",
        ]:
            self._add_bullet(item)
        self._add_callout("Secondary ICP clients are often the cost-share opportunity on primary ICP projects. Always ask about additional parties on every discovery call.")

        self._insert_page_break()

    def build_chapter_04(self):
        """Service Offerings."""
        self._add_chapter_header("04", "Service Offerings")

        # Service 01
        self._add_heading("Service 01: Project Photography", 2)
        self._add_body("Completed project documentation — the core service. Full-day shoot capturing the finished space with architectural precision. Includes photography, drone aerials, and short-form video.")
        self._add_heading("Deliverables", 3)
        for item in [
            "20–30 edited images (web + print resolution)",
            "60-second walkthrough video",
            "Drone/aerial coverage",
            "Social media reel",
            "Unlimited license for business use",
        ]:
            self._add_bullet(item)

        # Service 02
        self._add_heading("Service 02: Award & Publication Imagery", 2)
        self._add_body("Submission-ready photography for industry awards (Georgie Awards, CHBA, AIBC, HAVAN) and publications (Dwell, Dezeen, Western Living, Azure). Higher image count, editorial quality, includes twilight coverage.")
        self._add_heading("Deliverables", 3)
        for item in [
            "30–40 edited images (editorial quality)",
            "Drone/aerial coverage",
            "Twilight/blue hour session",
            "2–3 minute architectural film",
            "Social media reel",
            "Publication-resolution exports per submission specs",
        ]:
            self._add_bullet(item)

        # Service 03
        self._add_heading("Service 03: Build & Team Content", 2)
        self._add_body("In-progress construction documentation and crew content. Shows the process, the team, the craft. Used for social media, proposals, recruitment, and client updates.")
        self._add_heading("Deliverables", 3)
        for item in [
            "10–15 images per session (half-day)",
            "Progress documentation (wide + detail)",
            "Team at work (candid, not posed)",
            "Material close-ups (texture, craft)",
            "Site context (signage, equipment, environment)",
        ]:
            self._add_bullet(item)

        # Service 04
        self._add_heading("Service 04: Creative Partner", 2)
        self._add_body("Ongoing embedded creative department for firms with consistent visual needs. Renamed from \"Visual Partner Retainer\" in March 2026 to reflect the expanded scope. Matt functions as the client's creative arm — not just a photographer on retainer.")
        self._add_heading("Scope Includes", 3)
        for item in [
            "Photography (project, award, lifestyle, team) — 1 shoot/month",
            "Marketing strategy and campaign planning",
            "Website development & management (Squarespace)",
            "Content creation (social media, editorial, proposals)",
            "Brand strategy and visual identity",
            "Priority booking and dedicated availability",
        ]:
            self._add_bullet(item)
        self._add_callout("Proof case: Balmoral Construction — 1+ year on retainer, Matt manages photography, video, website (42-page rebuild), drone, and all things related to their business marketing.")

        # Additional services
        self._add_heading("Additional Services", 2)
        for item in [
            "Website design & build (Squarespace) — full custom builds with code block architecture",
            "Social media management — content creation, scheduling, strategy",
            "Standalone project sessions — photography only, half-day rate",
        ]:
            self._add_bullet(item)

        self._insert_page_break()

    def build_chapter_05(self):
        """Pricing & Rate Card."""
        self._add_chapter_header("05", "Pricing & Rate Card")
        self._add_body("Last reviewed: March 2026. Next review: June 2026.")
        self._add_callout("AOS Rule: No discounts. No rate matching. No free add-ons. Price changes only by changing scope.")

        self._add_heading("Project Pricing by ICP", 2)

        self._add_heading("Architects", 3)
        for item in [
            "Architectural Project: $3,500 (48.1% margin) — Full day, 20–30 images + 60s video + drone + social reel",
            "Award-Ready: $5,500 (56.8% margin) — Full day, 30–40 images + drone + twilight + 2–3 min film",
            "Curated Portfolio Edit: $4,000–$6,000 (~54–70% margin) — 8–15 images, maximum restraint",
            "Multi-Phase Documentation: $12,000–$20,000 (~55% margin) — 3–5 visits, 40–75 images",
        ]:
            self._add_bullet(item)

        self._add_heading("Builders", 3)
        for item in [
            "Completed Project: $3,500 (57.1% margin) — Full day, 25–30 images + 60s video + drone + social reel",
            "Signature Project: $5,500 (56.8% margin) — Full day, 30–40 images + drone + twilight + film + team/lifestyle",
            "Pilot Retainer (3 mo): $2,500/mo (~44–56% margin) — 1 shoot/mo, 12–15 images, priority",
            "Full Retainer (12 mo): $3,000/mo (~50–60% margin) — 1 shoot/mo, 15–20 images, priority",
            "Construction Progress: $1,000–$1,500 (~54–69% margin) — 2–4 hrs, 10–15 images",
        ]:
            self._add_bullet(item)

        self._add_heading("Interior Designers", 3)
        for item in [
            "Residential Interior: $3,000 (56.0% margin) — Full day, 25–30 images + walkthrough + social reel",
            "Feature-Ready: $4,500 (47.2% margin) — Full day, 30–40 images + editorial film",
            "Project Session: $2,000 (58.75% margin) — Full day, 20–25 images, photography only",
            "Cost-Share: +30% of project fee (~100% margin) — Licensing fee when designer on another project",
        ]:
            self._add_bullet(item)

        self._add_heading("Editorial / Award Submissions", 3)
        self._add_bullet("Editorial Package: $4,500 (47.2% margin) — Full day, 30–40 images + drone + twilight + film")

        self._add_heading("Standalone (All ICPs)", 3)
        self._add_bullet("Project Session: $2,000 (58.75% margin) — Full day, 20–25 images, photography only")

        self._add_heading("Add-Ons", 2)
        for item in [
            "Drone / Aerial: $350–$600 per session",
            "Twilight / Blue Hour: $500–$800 (separate visit, high-impact)",
            "Before & After (Interior): $400–$600 (interior designer add-on)",
            "Video (60–90s film): $3,000–$4,500 (for tiers without video)",
            "Cost-Share (+1 party): +30% of fee (pure margin, $0 COGS)",
            "Image Licensing (trades/suppliers): $500–$1,500/party (zero COGS)",
        ]:
            self._add_bullet(item)

        self._add_heading("COGS Breakdown", 2)
        self._add_body("All COGS calculated at founder effective rate of $75/hr (not quoted to clients).")
        for item in [
            "Architect $3,500 project: $1,815 COGS → $1,685 gross profit (48.1%)",
            "Builder $3,500 project: $1,500 COGS → $2,000 gross profit (57.1%)",
            "Interior $3,000 project: $1,320 COGS → $1,680 gross profit (56.0%)",
            "Editorial $4,500 project: $2,375 COGS → $2,125 gross profit (47.2%)",
            "Session $2,000 project: $825 COGS → $1,175 gross profit (58.75%)",
        ]:
            self._add_bullet(item)

        self._add_heading("Cost Components", 3)
        self._add_body("Pre-production (research, shot list, scheduling) → Travel (fuel, time) → Production (on-site shooting) → Assistant / 2nd Shooter → Post-production direction → Editor (contracted) → Equipment / consumables → Client management / delivery.")

        self._add_heading("Travel Fees", 2)
        for item in [
            "Sea-to-Sky (Squamish, Whistler, Pemberton): Included",
            "Sunshine Coast: ~$85–$125",
            "Vancouver / Fraser Valley: ~$125–$150",
            "Okanagan: ~$125 + accommodation",
        ]:
            self._add_bullet(item)

        self._add_heading("Monthly Fixed Overhead: $4,717/mo ($56,604/yr)", 2)
        for item in [
            "Marketing: $540/mo (Ads $300, Instantly $140, Print $100)",
            "Software & Subscriptions: $457/mo (Adobe $80, Dropbox $40, Google $50, GHL $150, AI $85, Hosting $17, Spotify $15, QuickBooks $20)",
            "Vehicle: $950/mo (Lease $750, Insurance $150, Maintenance $50)",
            "Equipment: $500/mo (Depreciation $400, Maintenance $100)",
            "Office: $1,260/mo (Phone $110, Supplies $50, Home Office $1,100)",
            "Insurance: $80/mo (Liability $60, Gear $20)",
            "Accounting & Legal: $230/mo (Bookkeeping $80, Filings $100, Bank $20, LOC $30)",
        ]:
            self._add_bullet(item)

        self._insert_page_break()

    def build_chapter_06(self):
        """Financial Framework."""
        self._add_chapter_header("06", "Financial Framework")

        self._add_heading("2026 Revenue Target: $172,900", 2)

        self._add_heading("Revenue Streams", 3)
        for item in [
            "Project Photography (31 projects): $103,500",
            "  — Architect Projects: 11 × $3,500 = $38,500",
            "  — Builder Projects: 8 × $3,500 = $28,000",
            "  — Interior Design: 3 × $3,000 = $9,000",
            "  — Editorial / Award: 4 × $4,500 = $18,000",
            "  — Standalone Sessions: 5 × $2,000 = $10,000",
            "Retainer Revenue (3 clients, ramp): $57,000",
            "Image Licensing (~31 projects × $400 avg): $12,400",
        ]:
            self._add_bullet(item)

        self._add_heading("Key Financial Metrics", 3)
        for item in [
            "Monthly overhead: $4,717",
            "Break-even: ~$150,000/year",
            "Owner draw target: $3,000/month",
            "Annual overhead: $56,604",
            "Required monthly revenue: ~$14,408 ($172,900 ÷ 12)",
        ]:
            self._add_bullet(item)

        self._add_heading("2025 Baseline Performance", 2)
        self._add_body("Total 2025 revenue: $105,237 across 89 invoices. The 2026 target represents a 64% increase.")

        self._add_heading("Revenue by Category (2025)", 3)
        for item in [
            "Project Photography: $42,829 (40.7%)",
            "Retainers (Balmoral + Window Merchant): $44,541 (42.3%)",
            "Licensing / Cost-Share: $7,822 (7.4%)",
            "Hosting / Subscriptions: $3,570 (3.4%)",
            "Other: $6,475 (6.2%)",
        ]:
            self._add_bullet(item)

        self._add_heading("Active Recurring Revenue", 2)
        self._add_body("Current MRR: $1,417.50/month ($17,010 annualized):")
        for item in [
            "Balmoral web retainer: $367.50/mo",
            "Balmoral SEO retainer: $892.50/mo",
            "Shala Yoga hosting: $105/mo",
            "Carmen Chornell hosting: $52.50/mo",
        ]:
            self._add_bullet(item)
        self._add_callout("Window Merchant retainer ($2,100/mo) is PAUSED — creates an $18K+ gap that must be replaced in 2026.")

        self._add_heading("Cost-Share & Licensing Strategy", 2)
        self._add_body("30% licensing fee per additional party involved in a project. Ask on every discovery call. Near-100% margin. 2025 licensing revenue was $7,822 — validates the model. If 1/3 of 2026 projects include cost-share, that's ~$10K–$13K added revenue.")

        self._add_heading("Tax Position", 2)
        self._add_body("2025 gross revenue: ~$103K. Total T2125 expenses: ~$70K (including CCA $12,816 + Home Office $4,350 + Mileage $13,500). Final tax + CPP: ~$6,566. Tax optimization saved $7,143 from original estimate.")
        self._add_heading("2026 Tax Action Items", 3)
        for item in [
            "Open FHSA before Dec 31, 2026 ($8,000 deduction)",
            "RRSP contribution before Mar 1, 2027",
            "Elect GST Quick Method for 2027",
            "Consider incorporation at $173K revenue target",
            "Continue mileage log (Mileage tab in finance sheet)",
        ]:
            self._add_bullet(item)

        self._insert_page_break()

    def build_chapter_07(self):
        """Sales Process."""
        self._add_chapter_header("07", "Sales Process")

        self._add_heading("Pipeline Stages", 2)
        self._add_body("Managed in GoHighLevel CRM (LeadConnector). Pipeline: Marketing & Sales → Production → Post-Production → Cost Sharing.")

        self._add_heading("Lead Sources", 3)
        for item in [
            "Inbound: Google search, website contact form, pricing guide downloads",
            "Outbound: Cold email (Instantly), social DMs, networking",
            "Referral: Existing clients, industry connections",
            "Events: Georgie Gala, HAVAN events, industry mixers",
        ]:
            self._add_bullet(item)

        self._add_heading("Discovery Call Framework", 2)
        for i, item in enumerate([
            "Understand the project — What are they building/designing? Where? Timeline?",
            "Understand the need — Why now? Award deadline? Website launch? New business pitch?",
            "Qualify — Does this fit our ICP? Is the project visually compelling? Budget aligned?",
            "Scope the work — Which service tier? Any add-ons? Cost-share opportunities?",
            "Set expectations — Pricing, timeline, process, deliverables",
            "Always ask about cost-share — Who else was involved in this project? Any designers, trades, or suppliers who might want images?",
        ], 1):
            self._add_numbered(item)

        self._add_heading("Deposit Policy", 2)
        self._add_callout("AOS Rule: 50% deposit before scheduling. No exceptions. This is non-negotiable.")
        self._add_body("Deposit is required to hold the date. Remaining 50% invoiced upon gallery delivery. Net 30 payment terms. Late payment: 2% monthly interest after 30 days.")

        self._add_heading("Proposal Process", 2)
        for i, item in enumerate([
            "Discovery call completed and scope confirmed",
            "Proposal drafted using template (business/marketing/proposal-template.html)",
            "Proposal sent with follow-up email (see Email Templates)",
            "If accepted: service agreement sent, contract signed, deposit invoiced",
            "Deposit received → shoot date scheduled → onboarding begins",
        ], 1):
            self._add_numbered(item)

        self._add_heading("Objection Handling", 2)

        objections = [
            ("\"We already have a photographer.\"",
             "That's great — having someone you trust matters. What I'd ask is whether they specialize in architectural and interiors work specifically. General photographers and real estate shooters approach a space very differently than someone focused on documenting design intent. I'm happy to show you the difference side by side if you're ever curious."),
            ("\"It's too expensive.\"",
             "I understand — photography is a real investment. The way I think about it: one strong image set can land you an award, anchor your website for years, close your next client, and give you content for months of social media. The cost of not having those images is invisible, but it's real. I'm also happy to scope something that fits your budget as a starting point."),
            ("\"We'll just use our phones.\"",
             "For progress shots and social stories, absolutely — phone photos are great for that. But for your portfolio, website, and especially award submissions, the difference is dramatic. Judges and prospective clients notice. Your work deserves to be seen the way you designed it — with proper light, composition, and intention."),
            ("\"We don't have any projects ready.\"",
             "That's the best time to plan. I can scout a project in progress so we're ready the moment it's done. Or if you have older projects that were never properly documented, those are often worth revisiting. Happy to do a quick call to see what makes sense."),
            ("\"Can you just do a quick shoot?\"",
             "I offer half-day rates for smaller scopes. That said, there's a minimum investment required to do the work properly — showing up, setting up, and capturing a space with intention takes time regardless of size. Happy to scope it and find the right fit."),
            ("\"We'll reach out when we have a project.\"",
             "Of course. One thing to consider: my retainer clients get priority booking, which matters during peak construction season (May–October in the Sea to Sky). If you've got 3–4 projects a year, the retainer usually saves money and guarantees availability. No pressure — just worth knowing."),
            ("\"We had a bad experience with a photographer.\"",
             "I hear that more than you'd think. Usually it comes down to communication — unclear expectations, no shot list, rushed turnaround. My process is built around pre-production planning and clear scope upfront so there are no surprises. I'm happy to walk you through exactly how a project works before you commit to anything."),
        ]
        for objection, response in objections:
            self._add_body_bold(objection)
            self._add_body(response)
            self._add_spacer()

        self._insert_page_break()

    def build_chapter_08(self):
        """Operations."""
        self._add_chapter_header("08", "Operations")

        # Onboarding
        self._add_heading("Client Onboarding Checklist", 2)
        self._add_body("Repeatable checklist from closed deal to shoot-ready.")

        self._add_heading("Pre-Contract", 3)
        for item in [
            "Discovery call completed",
            "Scope confirmed (service type, deliverables, timeline)",
            "Proposal sent",
            "Proposal accepted",
        ]:
            self._add_bullet(item)

        self._add_heading("Contract & Payment", 3)
        for item in [
            "Service agreement sent (see Service Agreement Terms)",
            "Contract signed",
            "Deposit invoice sent",
            "Deposit received",
        ]:
            self._add_bullet(item)

        self._add_heading("Pre-Production", 3)
        for item in [
            "Client added to project management",
            "Dropbox delivery folder created: Client Name / Project Name / YYYY-MM",
            "Site visit / scout scheduled (if applicable)",
            "Site visit completed — notes captured",
            "Shoot date confirmed with client",
            "Staging coordination discussed (furniture, landscaping, cleaning)",
            "Shot list drafted based on project type",
            "Pre-shoot brief sent to client (what to expect, how to prepare)",
        ]:
            self._add_bullet(item)

        self._add_heading("Gear & Logistics", 3)
        for item in [
            "Gear checklist reviewed (see Shoot Day Protocol)",
            "Drone flight plan confirmed (airspace, weather, TC compliance)",
            "Travel / accommodation booked (if outside Sea-to-Sky)",
            "Weather backup date discussed",
            "Calendar event created with all details",
        ]:
            self._add_bullet(item)

        # Shoot Day
        self._add_heading("Shoot Day Protocol", 2)

        self._add_heading("Camera Gear Check", 3)
        for item in [
            "Primary body — charged, card formatted",
            "Backup body — charged, card formatted",
            "Wide angle lens (16–35mm or equivalent)",
            "Standard zoom (24–70mm)",
            "Tilt-shift lens (if architectural)",
            "Spare batteries (×3 minimum)",
            "Spare memory cards (×3 minimum)",
            "Tripod + L-bracket",
        ]:
            self._add_bullet(item)

        self._add_heading("Drone Gear Check", 3)
        for item in [
            "Drone body inspected, batteries charged (×3 minimum)",
            "Controller charged, ND filters packed",
            "Transport Canada pilot certificate accessible",
            "Airspace checked (NRC Drone Site Selection Tool)",
            "NOTAM check completed",
        ]:
            self._add_bullet(item)

        self._add_heading("Lighting & Accessories", 3)
        for item in [
            "Speedlights / strobes (if interior)",
            "Light stands, color checker / gray card",
            "Lens cloths + blower, step stool, gaffer tape",
        ]:
            self._add_bullet(item)

        self._add_heading("On-Site Protocol", 3)
        self._add_body("Arrive 30 minutes before shoot. Walk the full space — assess natural light direction and quality. Identify hero compositions. Note staging issues to flag with client. Plan shooting sequence (chase the light).")

        self._add_heading("Shot Framework by Project Type", 3)
        self._add_body_bold("Completed Project:")
        for item in [
            "Hero exterior (2–3 angles, include context/landscape)",
            "Key interior spaces (living, kitchen, primary suite, bathrooms)",
            "Architectural details (millwork, stairs, materiality)",
            "Environmental context (views, setting, streetscape)",
            "Twilight exterior + drone aerials (if scheduled)",
        ]:
            self._add_bullet(item)

        self._add_body_bold("Award & Publication:")
        for item in [
            "Every room, every angle — overshoot",
            "Straight verticals, zero distortion",
            "Clean sightlines — no personal items unless intentional",
            "Details showing design intent (joinery, hardware, lighting design)",
            "Context shots that tell the project story",
        ]:
            self._add_bullet(item)

        # Post-Production
        self._add_heading("Post-Production & Delivery", 2)

        self._add_heading("Import & Backup", 3)
        for item in [
            "Import all cards to Lightroom catalog",
            "Backup raw files to external drive",
            "Create project folder: YYYY-MM — Client Name — Project Name",
        ]:
            self._add_numbered(item)

        self._add_heading("Culling", 3)
        for item in [
            "First pass: reject obvious misses (focus, exposure, duplicates)",
            "Second pass: select hero shots + supporting images per room/space",
            "Target delivery count per package tier",
        ]:
            self._add_bullet(item)

        self._add_heading("Export Specifications", 3)
        for item in [
            "Web / portfolio: JPEG, 2400px long edge, 85% quality, sRGB",
            "Print / publication: TIFF, full resolution, uncompressed, Adobe RGB",
            "Social media (feed): JPEG, 1080×1350, 90% quality, sRGB",
            "Social media (story): JPEG, 1080×1920, 90% quality, sRGB",
            "Award submission: per spec, full resolution, 95% quality, sRGB",
        ]:
            self._add_bullet(item)

        self._add_heading("Delivery", 3)
        for item in [
            "Upload to Dropbox client folder (Final / [Web] and Final / [Print])",
            "Send delivery notification email",
            "Share Dropbox link with client",
        ]:
            self._add_numbered(item)

        self._add_heading("Post-Delivery Follow-Up", 3)
        for item in [
            "Day 0: Gallery delivered — send notification",
            "Day 3: Check in — any questions or feedback?",
            "Week 2: Request testimonial / Google review",
            "Month 1: Ask about case study (if strong project)",
            "Month 3: Check in — new projects? Retainer pitch if repeat client",
        ]:
            self._add_bullet(item)

        # Service Agreement Terms
        self._add_heading("Service Agreement Terms", 2)

        self._add_heading("Usage Rights & Licensing", 3)
        for item in [
            "Client receives a perpetual, non-exclusive license for business use (website, social, print, proposals, awards, publications)",
            "Matt Anthony Photography retains copyright and portfolio/marketing usage rights",
            "Images may not be resold, sublicensed, or used for stock photography",
            "Credit required: \"Photo: Matt Anthony Photography\" or \"@mattanthonyphoto\"",
            "Extended licensing (advertising, billboards, national campaigns) available at additional cost",
        ]:
            self._add_bullet(item)

        self._add_heading("Cancellation Policy", 3)
        for item in [
            "7+ days out: Full deposit refund",
            "3–6 days out: 50% deposit retained",
            "Less than 3 days: Full deposit retained",
            "Weather cancellation: Reschedule at no cost (mutual agreement)",
            "Photographer cancellation: Full refund or reschedule at client's choice",
        ]:
            self._add_bullet(item)

        self._add_heading("Delivery Timelines", 3)
        for item in [
            "Project Photography: 15 business days",
            "Award & Publication: 10 business days",
            "Build & Team Content: 10 business days",
            "Creative Partner Retainer: 10 business days per shoot",
            "Rush delivery: 48 hours (add-on fee applies)",
        ]:
            self._add_bullet(item)

        self._add_heading("Revisions", 3)
        for item in [
            "2 rounds of minor edits included (crop, exposure, white balance)",
            "Additional edits or retouching beyond scope: $50/image",
            "Major reshoots billed as new session",
            "Scope changes require written change orders (per AOS)",
        ]:
            self._add_bullet(item)

        self._insert_page_break()

    def build_chapter_09(self):
        """Team Standards."""
        self._add_chapter_header("09", "Team Standards")

        self._add_heading("Editing & Visual Style Guide", 2)
        self._add_body("Standards for anyone editing images under the Matt Anthony Photography brand.")

        self._add_heading("Philosophy", 3)
        self._add_callout("Document the space as the designer intended it. Natural, honest, intentional. The architecture is the subject — our job is to present it clearly, not reinterpret it.")

        self._add_heading("Color & Tone", 3)
        for item in [
            "Natural color grading — true to materials. Wood looks like wood, concrete like concrete.",
            "Slightly desaturated — pull back vibrancy ~10–15%. Avoid oversaturation in greens and blues.",
            "Warm neutral — lean warm but never orange. Natural skin tones if present.",
            "No heavy color grading, film presets, or trendy looks. Timeless aesthetic.",
        ]:
            self._add_bullet(item)

        self._add_heading("Exposure & Light", 3)
        for item in [
            "Expose for the room — natural light is primary, flash/strobe is supplemental",
            "Lift shadows moderately — show detail without going flat",
            "Protect highlights — preserve window views (window pulls if needed)",
            "No HDR look. Exposure blending should be invisible.",
        ]:
            self._add_bullet(item)

        self._add_heading("Composition & Geometry", 3)
        for item in [
            "Verticals must be straight — non-negotiable",
            "No barrel distortion — correct in post",
            "Clean sightlines — eye travels through the space naturally",
            "Shoot at standing eye height (~5ft) for interiors unless reason not to",
            "Two-point perspective preferred for interiors (camera level, two vanishing points)",
        ]:
            self._add_bullet(item)

        self._add_heading("Retouching Standards", 3)
        self._add_body_bold("Remove:")
        for item in [
            "Construction debris, tools left behind",
            "Visible cables and cords (unless architectural)",
            "Staging imperfections (crooked cushions, visible price tags)",
            "Photographer's reflection in glass/mirrors",
            "Temporary signage, dumpsters, port-a-potties in exteriors",
        ]:
            self._add_bullet(item)

        self._add_body_bold("Keep:")
        for item in [
            "Material texture and grain (wood, stone, concrete, metal)",
            "Natural light patterns and shadows",
            "Intentional design elements (even if they look \"imperfect\")",
            "Landscape and environment as-is (don't composite skies)",
        ]:
            self._add_bullet(item)

        self._add_heading("File Naming Convention", 3)
        self._add_body("Format: YYYY-MM_ClientName_ProjectName_###.ext")
        self._add_body("Example: 2026-03_Balmoral_WarblerWay_001.jpg")

        # Contractor Brief
        self._add_heading("Contractor / Second Shooter Brief", 2)

        self._add_heading("On-Set Standards", 3)
        for item in [
            "Arrive 15 minutes early — no exceptions",
            "Dress: clean, dark, neutral clothing. Closed-toe shoes. No logos or bright colors.",
            "Let Matt lead all client communication unless asked otherwise",
            "Don't make promises about deliverables or timelines",
            "Phone on silent — no personal phone use on set",
            "Move quietly through the space — often shooting in occupied or staged homes",
        ]:
            self._add_bullet(item)

        self._add_heading("Equipment (Contractor Brings)", 3)
        for item in [
            "Camera body (full frame preferred), wide angle (16–35mm), standard zoom (24–70mm)",
            "Tripod, spare batteries + cards",
            "Laptop for on-site backup (if requested)",
        ]:
            self._add_bullet(item)

        self._add_heading("Image Handling", 3)
        for item in [
            "Memory cards stay with Matt at end of shoot",
            "All raw files are property of Matt Anthony Photography",
            "Editing handled by Matt unless explicitly delegated",
            "No posting, sharing, or using shoot images without written permission",
        ]:
            self._add_bullet(item)

        self._add_heading("Confidentiality", 3)
        self._add_body("Client details, locations, and project information are confidential. Do not share addresses, client names, or project details with anyone outside the team. Some projects may be under NDA — Matt will flag these in advance.")

        self._insert_page_break()

    def build_chapter_10(self):
        """Marketing & Content Strategy."""
        self._add_chapter_header("10", "Marketing & Content Strategy")

        self._add_heading("Content Pillars", 2)

        pillars = [
            ("1. Project Showcases", "The portfolio in motion. Final images from completed shoots presented as reveals. Instagram carousels (8–10 images), LinkedIn posts with project story, journal posts (long-form behind the scenes)."),
            ("2. Process & Behind the Scenes", "Show how the work gets made. Builds trust and differentiates. Setup shots, gear in the field, before/after staging. Stories and Reels from shoot days. \"How I shot this\" breakdowns."),
            ("3. Client Spotlights", "Elevate the people you work with — the retainer pitch in action. Tag clients, share their wins (awards, completions). Testimonial graphics. Case study summaries."),
            ("4. Educational", "Position as the authority on architectural photography in BC. Why professional photos matter. How to prepare for a shoot. Award submission tips. Seasonal shooting considerations."),
            ("5. Personal / Brand", "Let people know who's behind the camera. Squamish lifestyle, why this work matters. Milestone posts. Keep rare — max 1–2/month."),
        ]
        for title, desc in pillars:
            self._add_heading(title, 3)
            self._add_body(desc)

        self._add_heading("Platform Strategy", 2)

        self._add_heading("Instagram", 3)
        for item in [
            "Grid aesthetic matters — alternate between wide/detail, light/dark",
            "Carousels outperform single images for engagement",
            "Reels: 15–30 seconds, process-focused, no talking head required",
            "Stories: shoot day BTS, polls, casual content",
            "Post 3–4×/week",
        ]:
            self._add_bullet(item)

        self._add_heading("LinkedIn", 3)
        for item in [
            "Longer captions, B2B angle",
            "Tag client companies and collaborators",
            "Share insights, not just images",
            "Post 2–3×/week",
        ]:
            self._add_bullet(item)

        self._add_heading("Website Journal", 3)
        for item in [
            "1–2 posts/month, SEO-focused",
            "Target keywords builders and architects search",
            "Link to relevant service pages and project pages",
            "800–1,500 words per post",
        ]:
            self._add_bullet(item)

        self._add_heading("Content Repurposing Chain", 2)
        self._add_body("Shoot → Final Images → Instagram carousel (immediate) → LinkedIn post (same week, different angle) → Journal post (2–4 weeks later) → Case study (if strong project) → Proposal insert (ongoing) → Award submission collateral (seasonal).")
        self._add_callout("One shoot feeds content for months. Maximize every project.")

        self._add_heading("Seasonal Strategy", 2)
        for item in [
            "Jan–Mar: Award submissions (Georgie deadlines), planning content, educational posts",
            "Apr–May: Construction season ramp-up, retainer pitches, drone content",
            "Jun–Aug: Peak shooting season, heavy project reveals, BTS content",
            "Sep–Oct: Fall light content, wrap-up projects, Okanagan/Sunshine Coast",
            "Nov–Dec: Year-in-review, testimonial collection, planning for next year",
        ]:
            self._add_bullet(item)

        self._add_heading("Email Templates", 2)
        self._add_body("Standard email templates for common touchpoints. All written in Matt's voice — professional but warm, consultative, never pushy.")

        templates = [
            ("Post-Discovery Call Follow-Up", "Subject: Great connecting, [FIRST NAME]\n\nPersonalized follow-up referencing specific project/goal discussed. Confirm service type fit. Promise proposal by specific date. Include link to relevant portfolio work."),
            ("Proposal Send", "Subject: Your proposal — [PROJECT NAME]\n\nDirect, clean. Link to proposal document. Offer to walk through on call."),
            ("Post-Shoot Thank You", "Subject: Great shoot today\n\nThank client, note delivery timeline, set expectations for Dropbox link."),
            ("Gallery Delivery", "Subject: Your images are ready — [PROJECT NAME]\n\nDropbox link with organized deliverables. Encourage immediate use. Offer adjustments."),
            ("Testimonial Request (2 weeks post-delivery)", "Subject: Quick favour?\n\nLow-pressure ask for Google review. Direct link included. \"No pressure\" tone."),
            ("Re-Engagement (Dormant Lead)", "Subject: Any new projects on the horizon?\n\nWarm check-in. Reference their area/market. Link to recent work."),
            ("Retainer Pitch (Repeat Client)", "Subject: An idea for [COMPANY]\n\nReference past projects together. Introduce Creative Partner concept. Priority booking angle. No pressure."),
        ]
        for title, desc in templates:
            self._add_heading(title, 3)
            self._add_body(desc)

        self._insert_page_break()

    def build_chapter_11(self):
        """Lead Generation & Pipeline."""
        self._add_chapter_header("11", "Lead Generation & Pipeline")

        self._add_heading("Cold Email System", 2)
        self._add_body("Automated prospecting pipeline targeting builders, architects, interior designers, and trades across BC. Two system versions exist:")

        self._add_heading("Version 1: n8n Workflow", 3)
        self._add_body("Pipeline: Google Maps data → n8n enrichment/qualification → Output Google Sheet → Instantly for sending.")
        for item in [
            "Trigger: Google Sheets poll (every 3 minutes) on input sheet tabs",
            "Scrape: Apify Website Content Crawler (Cheerio, 3 pages max, depth 1)",
            "Qualify: Claude Opus via OpenRouter — 4,500-word ICP classification prompt",
            "Email Generation: 3 sequential AI agents (Intro → Follow-Up → Breakup)",
            "Email Verify: Icypeas → AI Email Finder fallback",
            "Output: Google Sheet with all 3 email drafts ready for Instantly import",
        ]:
            self._add_bullet(item)

        self._add_heading("Version 2: Claude Code Pipeline", 3)
        self._add_body("Direct replacement built March 2026. More reliable, higher quality output.")
        for item in [
            "279 Builders scraped and qualified (85 qualified, 192 not qualified)",
            "75 in output sheet with full 3-email sequences",
            "68 ready for Instantly deployment (have email + intro)",
            "6 missing email addresses (contact-form-only sites)",
            "32 missing decision maker names (emails use \"Hi there\")",
        ]:
            self._add_bullet(item)

        self._add_heading("Email Copy Strategy", 3)
        for item in [
            "Subject lines: \"[project name], from a photographer\" — all lowercase, 3–5 words",
            "Tone: Selective and affirming (\"your work is why I reached out\"), never critical",
            "Intro: Personalized opener (project detail from their site), ICP-specific value prop, low-pressure CTA",
            "Follow-Up: Recap + prebooking spring/summer angle, portfolio link, case study link",
            "Breakup: Graceful close + ICP-matched journal article link",
            "Follow-up/breakup: Reply-in-thread in Instantly (no separate subject lines)",
        ]:
            self._add_bullet(item)

        self._add_heading("Case Study Mapping for Cold Email", 3)
        for item in [
            "Builder → Summerhill Fine Homes (fallback: Balmoral Construction)",
            "Architect → Sitelines Architecture",
            "Designer → LRD Studio",
            "Trades → The Window Merchant",
            "Competitor guard: if prospect IS the case study company, use anonymous alternate",
        ]:
            self._add_bullet(item)

        self._add_heading("Sending Platform: Instantly", 2)
        self._add_body("Instantly.ai ($140/mo) handles warm-up, sending schedule, domain rotation. 4 warmed accounts ready, send from secondary domain.")
        self._add_body("Data flow: Claude generates copy → CSV export → Instantly sends sequences → Replies flow to GoHighLevel → Qualified leads tracked in Notion Pipeline.")

        self._add_heading("CRM: GoHighLevel (LeadConnector)", 2)
        self._add_body("All contacts, opportunities, and invoicing managed through GoHighLevel.")

        self._add_heading("Pipelines", 3)
        for item in [
            "1. Marketing & Sales — Lead to closed deal",
            "0.3 Production — Active project management",
            "2. Production (Post) — Post-production tracking",
            "05. Cost Sharing — Multi-party licensing tracking",
        ]:
            self._add_bullet(item)

        self._add_heading("Key Custom Fields", 3)
        for item in [
            "Contact Form fields: Timeline, Project Location, Service Interest, Project Details, Referral Source",
            "Discovery Call fields: Estimated Deal Value, Lead Temperature, Fit Score, Retainer Potential, Follow Up Action",
            "Project Intake fields: Project Name, Address, Value, Sq Footage, Architect, Builder, Designer, Awards, Status, Preferred Shoot Date",
        ]:
            self._add_bullet(item)

        self._insert_page_break()

    def build_chapter_12(self):
        """Technology Stack."""
        self._add_chapter_header("12", "Technology Stack")

        self._add_heading("Production & Editing", 2)
        for item in [
            "Adobe Creative Cloud ($80/mo) — Lightroom, Photoshop, Premiere Pro",
            "Dropbox ($40/mo) — Client file delivery and persistent storage",
        ]:
            self._add_bullet(item)

        self._add_heading("Business & CRM", 2)
        for item in [
            "GoHighLevel / LeadConnector ($150/mo) — CRM, invoicing, pipeline, booking",
            "Google Workspace ($50/mo) — Email, Drive, Sheets, Docs",
            "QuickBooks ($20/mo) — Bookkeeping",
        ]:
            self._add_bullet(item)

        self._add_heading("Website", 2)
        for item in [
            "Squarespace — Custom code block architecture, 72 pages",
            "Web Hosting & Domain ($17/mo)",
        ]:
            self._add_bullet(item)

        self._add_heading("Marketing & Outreach", 2)
        for item in [
            "Instantly.ai ($140/mo) — Cold email sending, warm-up, domain rotation",
            "Google/Meta Ads ($300/mo) — Paid advertising",
            "Print / Brochures ($100/mo)",
        ]:
            self._add_bullet(item)

        self._add_heading("AI & Automation", 2)
        for item in [
            "Claude Code / Anthropic ($85/mo) — AI assistant, content generation, automation scripts",
            "n8n (self-hosted) — Workflow automation (contact form processing, cold email pipeline)",
            "OpenRouter — LLM API access for n8n workflows",
            "Apify — Website scraping for lead qualification",
            "Icypeas — Email verification and finding",
        ]:
            self._add_bullet(item)

        self._add_heading("Finance Tracking", 2)
        self._add_body("Custom Google Sheets system tracking all bank accounts (Personal Visa, Chequing, Business Visa, Business Chequing). Tabs: Dashboard, Transactions, Income, Expenses, P&L, Mileage, GST, Equipment, Tax, Insights. Python import tools for bank CSV processing.")

        self._add_heading("Other", 2)
        for item in [
            "Notion — Project pipeline, client database, content planning",
            "Spotify ($15/mo) — Music for video content",
            "Transport Canada RPAS — Advanced Operations Certificate for drone",
        ]:
            self._add_bullet(item)

        self._insert_page_break()

    def build_chapter_13(self):
        """Competitive Landscape."""
        self._add_chapter_header("13", "Competitive Landscape")

        self._add_callout("Matt's competitors are other architectural photographers, NOT builders. Builders are clients.")

        self._add_heading("Direct Competitors", 2)

        competitors = [
            ("Ema Peter — HIGH THREAT", "Top-tier, internationally recognized. Architizer top 5 globally. Clients include Kengo Kuma, BIG, Omar Gandhi. Published in AD, Dwell, Azure. 20+ years. North Vancouver. Premium pricing, institutional/commercial focus.", "Matt's edge: Accessible to regional builders/designers, retainer model, full-service creative partner offering."),
            ("Andrew Fyfe — HIGH THREAT", "Most direct overlap. Vancouver-based. Drone certified. $1,200–$10K pricing. Good Houzz presence.", "Matt's edge: Specialist focus (not generalist), retainer model, video storytelling, embedded creative partner positioning."),
            ("Kyle Graham — MEDIUM", "Covers Vancouver Island + Vancouver + Sea-to-Sky. Fine art approach.", "Matt's edge: Deeply embedded in one region rather than spread across three."),
            ("Martin Knowles — MEDIUM", "Vancouver. Founded 2007. 40+ award-winning projects. ArchDaily, Georgie Awards.", "Matt's edge: Modern website, full-service offering (video, drone, social), retainer model vs. traditional shoot-and-deliver."),
            ("Luke Potter — LOW", "North Vancouver. 10+ years. Clean portfolio but smaller presence.", "Matt's edge: Drone certified, video capability, broader service offering."),
            ("RAEF — LOW", "Vancouver/Calgary/Atlanta. 20+ years, 8K video, helicopter aerials.", "Matt's edge: Design-intent focus vs. commercial/volume approach."),
        ]
        for name, desc, edge in competitors:
            self._add_heading(name, 3)
            self._add_body(desc)
            self._add_body_bold(edge)

        self._add_heading("The Real Competition", 2)
        self._add_body("Most prospects have never hired an architectural photographer. The actual competition is:")
        for item in [
            "Inaction — \"We'll get to it later\"",
            "iPhone photos — \"Good enough\"",
            "Real estate photographers — $300 for 25 photos (volume over quality)",
        ]:
            self._add_bullet(item)

        self._add_heading("Positioning Strategy", 3)
        for item in [
            "Against Ema Peter: \"Same design intention, accessible model and pricing\"",
            "Against Fyfe/Knowles: \"We specialize exclusively in architecture, plus retainers\"",
            "Against inaction: Lead with education — show the ROI of proper imagery",
            "Against real estate photographers: \"Your $3M home deserves better than a $300 shoot\"",
        ]:
            self._add_bullet(item)

        self._insert_page_break()

    def build_chapter_14(self):
        """Growth Plan & Quarterly Rocks."""
        self._add_chapter_header("14", "Growth Plan & Quarterly Rocks")

        self._add_heading("2026 Quarterly Themes", 2)

        quarters = [
            ("Q1: Build the Machine (Jan–Mar)", [
                "Rebuild website (72 pages — COMPLETED)",
                "Build finance tracking system — COMPLETED",
                "Build cold email pipeline — COMPLETED (75 qualified leads)",
                "Process Builders tab (279 leads) — COMPLETED",
                "Establish AOS rules and pricing framework — COMPLETED",
            ]),
            ("Q2: Launch the Engine (Apr–Jun)", [
                "6 location pages live on website (target: May 2)",
                "4 client-type pages live on website (target: May 16)",
                "Attend Georgie Gala (May 23–25)",
                "Sign retainer client #1 (target: May 31) — top candidate: Balmoral photography retainer ($2,500/mo pilot)",
                "Deploy cold email campaign via Instantly",
                "Deploy Balmoral website rebuild",
            ]),
            ("Q3: Produce & Prove (Jul–Sep)", [
                "Peak shooting season — target 8–10 projects completed",
                "Prove retainer model works with at least 1 active retainer client",
                "Build case studies from Q2/Q3 projects",
                "Process Architects, Interior Designers, and Trades tabs for cold email",
            ]),
            ("Q4: Solidify & Plan (Oct–Dec)", [
                "Sign retainer client #2 and #3",
                "Year-end financials and tax preparation",
                "Build 2027 strategic plan based on 2026 learnings",
                "Evaluate incorporation if revenue target hit",
                "Open FHSA before Dec 31 ($8K deduction)",
            ]),
        ]
        for title, items in quarters:
            self._add_heading(title, 3)
            for item in items:
                self._add_bullet(item)

        self._add_heading("Critical Reactivation Targets", 2)
        for item in [
            "Balmoral Construction — Photography retainer pitch ($2,500/mo pilot). Fitzsimmons North under construction. Layer on existing $1,260/mo relationship. Target: April 1.",
            "Sitelines Architecture — Jordan Maddox. Expanding to BC Interior 2026. $6,720 in 2025. Warm.",
            "Koze Homes — Jason Craig. $3,415 in 2025. Warm.",
            "Michel Laflamme — Already buying licenses ($735 Jan 2026).",
            "Black Point — Chris McKenzie. Licensing $882 Mar 2026.",
        ]:
            self._add_bullet(item)

        self._add_heading("Key Milestones", 2)
        for item in [
            "First $10K month in 2026 → validates pipeline is working",
            "First retainer signed → proves model for 2027 expansion",
            "30 projects completed → on track for $103.5K project revenue",
            "3 active retainer clients → $57K annual retainer revenue",
            "$150K revenue → break-even crossed, owner draw secured",
            "$172.9K revenue → full target hit, 2027 acceleration unlocked",
        ]:
            self._add_bullet(item)

        self._insert_page_break()

    def build_chapter_15(self):
        """AOS Rules & Governance."""
        self._add_chapter_header("15", "AOS Rules & Governance")

        self._add_callout("The Agency Operating System (AOS) governs all pricing, qualification, and operational decisions. These rules take precedence over any other guidance.")

        self._add_heading("Margin Rules", 2)
        for item in [
            "Floor (Minimum): 40% — Projects below this are NOT accepted",
            "Target (Healthy): 45–55% — Normal operating range",
            "Stretch (Ideal): 60–70% — Low-friction, high-alignment work",
        ]:
            self._add_bullet(item)
        self._add_body("All current service offerings pass the 40% floor. Cash margins (excluding founder time) range from 78.9% to 86.3%.")

        self._add_heading("Pricing Rules", 2)
        for item in [
            "No discounts — ever",
            "No rate matching — we don't compete on price",
            "No free add-ons — value is priced into every deliverable",
            "Price changes only by changing scope — if a client wants a lower price, reduce the scope",
            "Founder rate ($75/hr) is for internal COGS calculations only — never quoted to clients",
        ]:
            self._add_bullet(item)

        self._add_heading("Deposit Rule", 2)
        self._add_body_bold("50% deposit before scheduling. No exceptions.")
        self._add_body("This is non-negotiable. The deposit holds the date. No deposit = no calendar hold = no shoot.")

        self._add_heading("Cost-Share Rule", 2)
        self._add_body_bold("Ask about cost-share on every single discovery call.")
        self._add_body("\"Who else was involved in this project?\" — If there's a designer, trades company, or supplier, that's a 30% licensing fee per party. Near-100% margin. This single question can add $10K–$13K in annual revenue.")

        self._add_heading("Capacity Rule", 2)
        self._add_body("Every Friday, count active projects:")
        for item in [
            "≥3 active projects → Intake PAUSES. No new bookings until capacity frees up.",
            "2 active + complex inbound → Slow the pipeline. Don't overcommit.",
            "≤2 active → Pipeline is open. Actively pursue leads.",
        ]:
            self._add_bullet(item)

        self._add_heading("Scope Change Rule", 2)
        self._add_body("All scope changes require a written change order. No verbal agreements for additional work. If a client asks for more on set, document it and price it. Scope creep is the #1 margin killer.")

        self._add_heading("Qualification Rule", 2)
        self._add_body("Before accepting any project, confirm:")
        for item in [
            "Does this client fit our ICP? (Architect, Builder, Interior Designer, or Trades)",
            "Is the project visually compelling enough for our portfolio?",
            "Is the budget aligned with our pricing? (No projects below $2,000)",
            "Will this project pass the 40% margin floor after COGS?",
            "Is there cost-share potential? (Multiple parties involved)",
        ]:
            self._add_bullet(item)

        self._add_spacer()
        self._add_spacer()
        self._add_horizontal_rule()

        # Final page
        start, end = self._insert_text("\n\nMATT ANTHONY PHOTOGRAPHY\n", "NORMAL_TEXT")
        self._style_text(start + 2, end - 1, font_family="Josefin Sans", font_size=11,
                        color=GOLD, bold=False)
        self._set_paragraph_alignment(start + 2, end - 1, "CENTER")

        start, end = self._insert_text("Agency Operating System — Version 1.0\n", "NORMAL_TEXT")
        self._style_text(start, end - 1, font_family="DM Sans", font_size=9, color=STONE)
        self._set_paragraph_alignment(start, end - 1, "CENTER")

        start, end = self._insert_text("Squamish, BC — March 2026\n", "NORMAL_TEXT")
        self._style_text(start, end - 1, font_family="DM Sans", font_size=9, color=STONE)
        self._set_paragraph_alignment(start, end - 1, "CENTER")

        start, end = self._insert_text("mattanthonyphoto.com\n", "NORMAL_TEXT")
        self._style_text(start, end - 1, font_family="DM Sans", font_size=9, color=GOLD)
        self._set_paragraph_alignment(start, end - 1, "CENTER")

    def _add_chapter_header(self, number, title):
        """Add a styled chapter header."""
        # Chapter number
        start, end = self._insert_text(f"CHAPTER {number}\n", "NORMAL_TEXT")
        self._style_text(start, end - 1, font_family="Josefin Sans", font_size=11,
                        color=GOLD, bold=False)
        self._set_paragraph_spacing(start, end - 1, before=0, after=4)

        # Chapter title
        self._add_heading(title)
        self._add_horizontal_rule()
        self._add_spacer()

    def build_document(self):
        """Build the complete AOS manual."""
        self.create_document()

        # Set default document styling
        self.requests.append({
            "updateDocumentStyle": {
                "documentStyle": {
                    "marginTop": {"magnitude": 72, "unit": "PT"},
                    "marginBottom": {"magnitude": 72, "unit": "PT"},
                    "marginLeft": {"magnitude": 72, "unit": "PT"},
                    "marginRight": {"magnitude": 72, "unit": "PT"},
                },
                "fields": "marginTop,marginBottom,marginLeft,marginRight"
            }
        })

        # Build all sections
        print("Building cover page...")
        self.build_cover_page()
        print("Building table of contents...")
        self.build_toc()
        print("Building Chapter 01: Company Overview...")
        self.build_chapter_01()
        print("Building Chapter 02: Brand Identity & Voice...")
        self.build_chapter_02()
        print("Building Chapter 03: Ideal Client Profiles...")
        self.build_chapter_03()
        print("Building Chapter 04: Service Offerings...")
        self.build_chapter_04()
        print("Building Chapter 05: Pricing & Rate Card...")
        self.build_chapter_05()
        print("Building Chapter 06: Financial Framework...")
        self.build_chapter_06()
        print("Building Chapter 07: Sales Process...")
        self.build_chapter_07()
        print("Building Chapter 08: Operations...")
        self.build_chapter_08()
        print("Building Chapter 09: Team Standards...")
        self.build_chapter_09()
        print("Building Chapter 10: Marketing & Content Strategy...")
        self.build_chapter_10()
        print("Building Chapter 11: Lead Generation & Pipeline...")
        self.build_chapter_11()
        print("Building Chapter 12: Technology Stack...")
        self.build_chapter_12()
        print("Building Chapter 13: Competitive Landscape...")
        self.build_chapter_13()
        print("Building Chapter 14: Growth Plan & Quarterly Rocks...")
        self.build_chapter_14()
        print("Building Chapter 15: AOS Rules & Governance...")
        self.build_chapter_15()

        # Execute all requests in batches (API limit is ~200 requests per batch)
        print(f"\nApplying {len(self.requests)} formatting requests...")
        batch_size = 200
        for i in range(0, len(self.requests), batch_size):
            batch = self.requests[i:i + batch_size]
            try:
                self.docs_service.documents().batchUpdate(
                    documentId=self.doc_id,
                    body={"requests": batch}
                ).execute()
                print(f"  Batch {i // batch_size + 1} applied ({len(batch)} requests)")
            except Exception as e:
                print(f"  Error in batch {i // batch_size + 1}: {e}")
                # Try individual requests to find the problem
                for j, req in enumerate(batch):
                    try:
                        self.docs_service.documents().batchUpdate(
                            documentId=self.doc_id,
                            body={"requests": [req]}
                        ).execute()
                    except Exception as e2:
                        print(f"    Failed request {i + j}: {list(req.keys())[0]} - {e2}")
                        break
                break

        print(f"\nDone! Document URL:")
        print(f"https://docs.google.com/document/d/{self.doc_id}/edit")
        return self.doc_id


if __name__ == "__main__":
    builder = AOSManualBuilder()
    builder.build_document()
