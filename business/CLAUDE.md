# Matt Anthony Photography

Architectural and interiors photography business serving the construction and design industry across British Columbia.

## Business Profile

- **Owner:** Matt Anthony
- **Structure:** Sole proprietorship (incorporation planned at $150K+ net income)
- **GST#:** 79115 0261 RT0001
- **Location:** Squamish, British Columbia
- **Website:** mattanthonyphoto.com (Squarespace)
- **Email:** info@mattanthonyphoto.com
- **Phone:** 604.765.9270
- **Instagram:** @mattanthonyphoto (2,427 followers)
- **LinkedIn:** /in/mattanthonyphoto/
- **Booking:** GHL discovery call widget on website pages
- **Certification:** Transport Canada certified Advanced Drone Pilot

## Positioning

Creative partner (not vendor) for architects, custom home builders, interior designers, and construction firms. Philosophy centers on "documenting design intent" — clarity, accuracy, and intention over spectacle. Building toward a scalable, retainer-based media service model with a full-time second shooter by 2027.

## Services

1. **Project Photography** — Completed project documentation
2. **Award & Publication Imagery** — Submission-ready photography for Georgie Awards, publications, etc.
3. **Build & Team Content** — In-progress construction and crew documentation
4. **Creative Partner** — Ongoing embedded creative arm for firms (formerly "Visual Partner Retainer")

Also delivers **website design/build** (Squarespace) and **social media management** for clients.

## Target Clients (ICP)

**Primary:** Architects, custom home builders, interior designers
**Secondary:** Millwork shops, trades/fabricators, construction firms, window/glazing companies

## Service Areas

- Sea-to-Sky Corridor (Squamish, Whistler, Pemberton)
- Sunshine Coast (Sechelt, Gibsons, Roberts Creek, Sandy Hook, Gambier Island)
- Vancouver
- Fraser Valley
- Okanagan

## Revenue Targets (2026)

- **Revised target:** $125,000 (21 projects + 2 retainers) — adjusted March 21 after Q1 travel
- **Original AOS target:** $172,900 (31 projects + 3 retainers) — the full-scale model
- **Q1 actual:** $5,701.50
- **Recurring base:** $1,417.50/mo ($17,010 annualized)
- **Cost-share hit rate:** 90% of projects (AOS modeled 33% — actual is much higher)

## Financial Position

- **LOC:** $16,574 balance / $35K limit / 8.94%
- **TFSA:** $43,472 (Questrade)
- **Monthly overhead:** $4,717 (see operations/pricing.md)
- **Owner draw target:** $3,000/mo
- **Rent:** $1,150/mo all-in (50% home office deduction)

## Brand Voice

- Professional but warm
- Calm, structured, intentional
- First person singular ("I") on project pages and bio
- First person plural ("We") on homepage philosophy and service pages
- Avoids superlatives and hype — lets the work speak

## Production

- **Editing:** Lightroom + Photoshop, self-edited (contracted editor lined up for scale)
- **Second shooter:** Sebastian Canon ($200-300/day, brings own gear, as needed)
- **Turnaround:** ~1 week average (SOP says 10-15 business days)
- **Delivery:** Dropbox — `2026/Clients/Projects/[Project Name]/Deliverables`

## Sales Process

- **Discovery:** GHL booking widget → pre-call form → discovery call → proposal within hours
- **Proposals:** Sent through GHL, same day as discovery call
- **Close rate:** Not formally tracked (gap to fix)
- **Cost-share:** Ask on every call — 90% hit rate, near-100% margin

## Tech Stack

| Tool | Cost/mo | Purpose |
|------|---------|---------|
| GHL | $150 | CRM, invoicing, booking, pipelines |
| Adobe CC | $80 | Lightroom + Photoshop |
| Google Workspace | $50 | Email, Drive, Sheets |
| Dropbox | $40 | Client delivery + storage |
| Instantly | $140 | Cold email sending |
| Claude/AI | $85 | Agent, automation, content |
| Squarespace | $17 | Website hosting |
| Spotify | $15 | Music |
| n8n | hosted | Self-hosted on Hostinger |

## Website Architecture

- **Platform:** Squarespace with custom code block embeds
- **No DOCTYPE/html/head/body wrappers** — breaks mobile rendering
- **No reveal/scroll animations** (opacity:0 + IntersectionObserver) — causes invisible text
- Each code block is self-contained with its own `<style>` and HTML
- Footer included within each code block
- CloudFlare email protection mangles mailto links — always use clean `mailto:`

### CSS Prefix System

| Prefix | Page Type |
|--------|-----------|
| `tp-` | Project pages |
| `hp-` | Homepage |
| `proj-` | Projects listing |
| `sh-` | Summerhill case study |
| `bc-` | Balmoral case study |
| `sl-` | Sitelines case study |
| `wm-` | Window Merchant case study |
| `sv-` | Service pages |
| `bio-` | Bio page |
| `ct-` | Contact page |
| `jn-` | Journal landing |
| `bl-` | Blog posts / award guides |

### Design System

**Typography:** Josefin Sans (display), Cormorant Garamond (headlines), DM Sans (body)

**Colors:**
| Name | Hex | Usage |
|------|-----|-------|
| Ink | #1A1A18 | Primary dark bg, text |
| Paper | #F6F4F0 | Light bg, hero text |
| Gold | #C9A96E | Accent, CTAs, labels |
| Warm Muted | #B8975A | Secondary gold |
| Stone | #8A8579 | Muted body text |
| Light Stone | #D9D5CD | Borders, light text |
| Off White | #EEECE6 | Quote bgs, alt sections |

## Portfolio

19 projects across BC — full list and metadata in brand bible.

**Case Studies:** Summerhill Fine Homes, Balmoral Construction, Sitelines Architecture, The Window Merchant

## Key References

- **Brand Bible:** `/Users/matthewfernandes/Documents/Documents/brand-bible.md`
- **Site Audit (March 2026):** `/Users/matthewfernandes/Documents/Documents/mattanthonyphoto-site-audit-march2026.md`
- **Website Standards:** `/Users/matthewfernandes/Documents/Documents/website-standards-guidelines.docx`

## Automation (n8n — 7 active workflows)

- **Contact Form → GHL + Email + Slack + Sheet** — Working (Mar 21)
- **Pricing Guide Form → GHL + Emails + Sheet** — Working (Mar 20)
- **Project Brief Generator → GitHub Pages** — Working (Mar 14)
- **Cold Email System** — Working (Mar 20), 70 nodes
- **Find Decision Makers Email** — ERRORING (3 failures Mar 23)
- **Web Crawler - Find Decision Makers Name** — ERRORING (Mar 22)
- **Personalized Outreach Message** — Active but unused, should deactivate

## Known Issues (March 2026)

- `/construction-team-content` serving Visual Partner Retainer content instead of Build & Team Content
- FAQ typos ("architects" instead of "photographers", "reach back" instead of "reach out")
- Fitzsimmons project missing JSON-LD
- Duplicate FAQ schema on some pages
- 2 n8n workflows actively erroring (Decision Makers Email + Web Crawler)
- Instagram dormant since October 2025
- Google Business Profile likely not set up — highest priority marketing gap
- $300/mo ad budget allocated but not being spent

## 2027 Vision

- Hit $170K+ revenue
- Incorporate the business
- Full-time second shooter on payroll
- Move upmarket to larger, design-intensive custom homes
- Published in one architectural magazine + Western Living feature
