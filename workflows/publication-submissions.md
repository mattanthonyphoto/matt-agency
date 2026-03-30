# Publication & Editorial Submissions — Standard Operating Procedure

Submit completed projects to architecture and design publications for editorial features. This is the highest-leverage marketing activity in the business — one published project generates more credibility than 50 cold emails.

---

## Trigger

Matt says: "submit to publications", "publication workflow", "pitch a project", "ArchDaily submission", "Dezeen pitch", "editorial submission", "prep a submission package", "publication review", or "what should I submit"

---

## Tools

| Tool | Purpose |
|---|---|
| `tools/publication_tracker.py` | Google Sheet tracking: projects, submissions, awards, dashboard |
| `tools/prompts/write_publication_pitch.md` | Pitch email generation per publication |
| `tools/prompts/write_project_description.md` | Editorial project description (200-400 words) |
| `tools/prompts/write_client_publication_request.md` | Client permission + materials request |
| `tools/prompts/write_publication_announcement.md` | Post-publication announcements (email, IG, LinkedIn) |

---

## Quick Start Commands

### First-time setup
```bash
python tools/publication_tracker.py init
# → Creates Google Sheet, returns sheet ID
# → Add PUBLICATION_TRACKER_SHEET_ID=<id> to .env
```

### Add a project to track
```bash
python tools/publication_tracker.py add-project \
  --name "Summerhill Residence" \
  --firm "Summerhill Fine Homes" \
  --location "Squamish, BC" \
  --project-type "New build" \
  --completed "2025-09" \
  --merit 4 \
  --images 22
```

### Log a submission
```bash
python tools/publication_tracker.py add-submission \
  --project "Summerhill Residence" \
  --publication "ArchDaily"
```

### Update when you hear back
```bash
python tools/publication_tracker.py update-status \
  --project "Summerhill Residence" \
  --publication "ArchDaily" \
  --status "Published" \
  --url "https://archdaily.com/..."
```

### Quarterly review
```bash
python tools/publication_tracker.py review   # All projects + statuses
python tools/publication_tracker.py due      # What needs attention
```

---

## Full Submission Process (Step by Step)

When Matt says "submit [project] to publications" or "prep [project] for editorial":

### Step 1: Evaluate the Project

Rate design merit 1-5:
- **5** — Unique concept, strong site, Dezeen-worthy
- **4** — Well-designed, good story, Dwell/Western Living + ArchDaily
- **3** — Solid work, ArchDaily + Canadian publications
- **2** — Professional but not publication-ready
- **1** — Standard documentation, no editorial angle

Only proceed with 3+.

### Step 2: Get Client Permission

Use `tools/prompts/write_client_publication_request.md` to draft the request email. You need:
- Written approval to submit
- Floor plans or drawings
- Full credits list
- Project description or approval to draft one

### Step 3: Build the Submission Package

1. **Write project description** using `tools/prompts/write_project_description.md`
2. **Curate image set** — 15-25 selects, captioned, 2880px+
3. **Compile credits** — every firm involved
4. **Collect floor plans** — from architect
5. **Log the project** via `publication_tracker.py add-project`

### Step 4: Determine Submission Strategy

Follow the priority logic in the Publication Database section below. Key decision:
- Merit 5 → Pitch Dezeen first (exclusive), wait 3 weeks, then everywhere else
- Merit 4 → Pitch Dwell or Western Living first if lifestyle angle, ArchDaily simultaneously
- Merit 3 → ArchDaily + Canadian publications simultaneously

### Step 5: Send Pitches

Use `tools/prompts/write_publication_pitch.md` for each publication. Log each via `publication_tracker.py add-submission`.

### Step 6: Follow Up & Track

- 2 weeks: Check for responses
- 3 weeks: One follow-up to Dezeen/Dwell if no response
- 4 weeks: Mark as "No Response" and move on
- On acceptance: Update tracker, prep full package if not already sent
- On publication: Run the announcement workflow (Step 7)

### Step 7: Announce Publication

Use `tools/prompts/write_publication_announcement.md` to generate:
- Client congratulations email
- Instagram caption
- LinkedIn post

Then update: website press page, email signature, project page credits, proposals.

---

## Why This Matters

"Almost two-thirds of new commissions come from reputation." A private home gets 50 visitors. The same project on ArchDaily gets 10,000+. Photography IS the building's public life. No photographer in BC explicitly offers structured publication submission service — this is the competitive moat.

**The Flywheel:** Publication → Awards → Peer credibility → Referrals → Premium clients → Better projects → More publication.

---

## When to Run This Workflow

- After delivering final images for any project with strong design merit
- When a client's project wins or is shortlisted for an award
- When a client asks about getting published (upsell to retainer)
- Quarterly — batch-review all unsubmitted projects from the past 6 months
- Before awards deadlines — submissions and publications reinforce each other

---

## Publication Database

### Architecture Publications

| Publication | Tier | Exclusivity | Acceptance Rate | Turnaround | Best For |
|---|---|---|---|---|---|
| **Dezeen** | 1 — Global | Yes — pitch first, wait 2-3 weeks | Low (~5%) | 2-8 weeks | High-concept residential, unique material/site story |
| **ArchDaily** | 1 — Global | No | High (~40-60%) | 1-4 weeks | Everything — volume play, build your "published in" list |
| **Architectural Record** | 1 — Global | Soft yes | Very low | 4-12 weeks | Significant commissions, institutional |
| **Dwell** | 2 — Lifestyle | Soft yes | Low-medium | 4-8 weeks | Residential with lifestyle angle, who-lives-here story |
| **Wallpaper*** | 2 — Lifestyle | Yes | Very low | 6-12 weeks | Design-forward, material innovation |
| **Western Living** | 2 — Canadian/BC | No | Medium | 2-6 weeks | Any BC project with lifestyle angle, design homes |
| **Azure** | 2 — Canadian | No | Medium | 2-6 weeks | Canadian design-forward projects |
| **Canadian Architect** | 3 — Canadian | No | Medium-high | 2-4 weeks | Any Canadian project, aligns with awards cycle |
| **Canadian Interiors** | 3 — Canadian | No | Medium-high | 2-4 weeks | Interior-focused projects |

### Interior Design Publications

| Publication | Tier | Exclusivity | Best For |
|---|---|---|---|
| **AD (Architectural Digest)** | 1 — Global | Yes | High-end residential interiors |
| **Elle Decor** | 1 — Global | Yes | Lifestyle-forward interiors |
| **Interior Design Magazine** | 1 — Global | Yes | Commercial and high-end residential |
| **House Beautiful** | 2 — Lifestyle | Soft yes | Aspirational residential |
| **Luxe Interiors + Design** | 2 — Regional | No | Luxury residential, regional editions |
| **House & Home** | 3 — Canadian | No | Canadian residential interiors |

### Online-Only / High-Volume

| Publication | Notes |
|---|---|
| **Leibal** | Minimalist design, quick turnaround |
| **Designboom** | Architecture + design, accepts simultaneous |
| **Archinect** | Community-driven, good for emerging firms |
| **v2com newswire** | Canadian press distribution for design projects |

---

## Submission Priority Logic

**Always submit top-down with exclusivity management:**

```
1. Does the project warrant Dezeen/AD/Dwell?
   → YES: Pitch Dezeen (or AD for interiors) FIRST. Wait 2-3 weeks for response.
   → NO: Skip to step 3.

2. Dezeen responds?
   → ACCEPTED: Wait for publication. Then submit to non-exclusive outlets.
   → DECLINED or NO RESPONSE after 3 weeks: Move to step 3.

3. Submit simultaneously to ALL non-exclusive publications:
   - ArchDaily (always)
   - Western Living (if BC project)
   - Azure (if Canadian)
   - Canadian Architect (if Canadian)
   - Any other relevant non-exclusive outlet

4. After publication anywhere, share links when pitching remaining outlets.
```

**Rule:** Never let exclusivity requests stall a project for more than 3 weeks. If Dezeen doesn't reply, move on.

---

## The Submission Package

Every project needs a complete package prepared BEFORE pitching any editor. Incomplete submissions get ignored.

### Required Components

#### 1. Project Brief (1 page)

```
PROJECT NAME: [Full project name as the firm uses it]
LOCATION: [City, Province/State, Country]
PROJECT TYPE: [New build / Renovation / Addition / Adaptive reuse]
SIZE: [Square footage + lot size if relevant]
COMPLETION DATE: [Month Year]
BUDGET RANGE: [Only if the client approves sharing — "undisclosed" is fine]

CREDITS:
- Architecture: [Firm name, city]
- Interior Design: [Firm name, city]
- General Contractor: [Firm name, city]
- Landscape: [Firm name, city]
- Structural Engineering: [Firm name, city]
- Photography: Matt Anthony Photography, Squamish BC

PROJECT DESCRIPTION:
[200-400 words, third person, written for editors not clients]

Focus on:
- Design intent — what problem did the design solve?
- Site response — how does the building relate to its context?
- Material choices — why these materials, what do they achieve?
- Spatial experience — how does it feel to move through the space?
- Sustainability — any notable performance or environmental features?

Avoid:
- Marketing language ("stunning", "breathtaking", "world-class")
- Client testimonials
- Pricing or value statements
- Technical jargon without context
```

#### 2. Image Set

| Requirement | Specification |
|---|---|
| **Quantity** | 15-25 selects (ArchDaily requires 15+, Dezeen wants 20+) |
| **Resolution** | 2880px+ on long edge (safe for print at 300dpi) |
| **Format** | JPEG, sRGB, quality 10-12 |
| **File naming** | `[project-name]-[descriptor]-matt-anthony.jpg` |
| **Variety required** | Hero exterior, hero interior, 2-3 detail shots, context/site, twilight if available |
| **Captions** | Room name, key materials, orientation (e.g., "Living room facing south toward Howe Sound. Douglas fir ceiling, board-formed concrete fireplace.") |

**Image selection principles:**
- Lead with the strongest exterior — this is the thumbnail editors see first
- Include at least one twilight/dusk shot (dramatically increases selection odds)
- Show the building in its site context (drone or wide establishing shot)
- Detail shots should tell a material story, not just be pretty
- Include at least one "human scale" reference (furniture, a doorway, a stair detail)
- Avoid over-processed HDR, heavy vignettes, or replaced skies — editors reject these immediately
- Construction-phase images are a bonus (before/during/after narratives are strong)

#### 3. Floor Plans / Drawings (If Available)

- Ask the architect — most will provide plans for publication
- Site plan showing building in context
- Key floor plans (main level at minimum)
- A section drawing if the spatial story is vertical
- Format: High-res PDF or PNG, clean linework

#### 4. Exclusivity Tracker

Maintain a running log per project:

```
| Publication | Date Pitched | Exclusive? | Response | Published? | URL |
|---|---|---|---|---|---|
| Dezeen | 2026-04-15 | Yes | Declined 2026-05-01 | — | — |
| ArchDaily | 2026-05-02 | No | Accepted 2026-05-10 | Yes | [url] |
| Western Living | 2026-05-02 | No | Pending | — | — |
```

---

## Publication-Specific Submission Guides

### ArchDaily — The Volume Play

**Why start here:** Highest acceptance rate. Builds your "published in" credentials fast. Architects respect it. Every ArchDaily feature is a Google-indexed backlink to your name.

**How to submit:**
1. Go to archdaily.com → Submit a Project (requires free account)
2. Fill in all project metadata (location, typology, year, area, credits)
3. Upload 15-25 images at 2880px+ (their system processes them)
4. Paste project description (200-400 words)
5. Upload floor plans if available
6. Submit — editorial team reviews within 1-4 weeks
7. If accepted, they publish with full photographer credit

**What editors want:**
- Strong hero image (this becomes the thumbnail across the site)
- Complete credits (they cross-reference with the architect's profile)
- Clean, design-focused narrative — not marketing copy
- Floor plans significantly increase acceptance odds
- 15 images minimum, 25 is ideal

**What to avoid:**
- Real estate photography style (wide-angle everything, no composition)
- Incomplete credits
- Projects without clear design merit (renovations need a strong concept angle)

---

### Dezeen — The Prestige Play

**Why it matters:** Most-read architecture publication globally. A Dezeen feature changes careers. Architects will hire you specifically because you've been published in Dezeen.

**How to submit:**
1. Email: submissions@dezeen.com
2. Subject line: `[City, Country] [Project Name] by [Architect]`
3. Body: 2-3 sentence hook + 5-6 hero images (embedded or linked via Dropbox)
4. If interested, they request the full package (all images + description + plans)
5. Turnaround: 2-8 weeks. No response after 3 weeks = likely pass.

**What editors want:**
- Exclusivity — they want to be first to publish
- A design story, not just pretty photos — what's conceptually interesting?
- Strong site response (how does the building relate to landscape/context?)
- Material innovation or unusual construction methods
- Residential projects in dramatic natural settings (BC is an advantage here)
- Minimum 20 images, high resolution

**What to avoid:**
- Submitting projects already published on ArchDaily (kills exclusivity)
- Generic luxury homes without a design concept
- Overly styled/staged interiors (they prefer lived-in authenticity)
- Following up more than once — one polite check-in at 3 weeks is acceptable

---

### Dwell — The Lifestyle Play

**Why it matters:** Reaches design-conscious homeowners (your clients' clients). Strong Instagram presence. A Dwell feature helps architects and designers attract better clients.

**How to submit:**
1. Email: editorial@dwell.com (or use their online submission form)
2. Subject line: `Story Pitch: [Project Name], [City]`
3. Body: Lead with the human story — who lives here and how. Include 5-6 images.
4. They may want to interview the homeowner and architect separately.

**What editors want:**
- The human story — who lives here, what was their brief, how do they use the space?
- Lifestyle context — real life, not showroom staging
- Kitchen and bathroom shots (their highest-performing content)
- Before/after if it's a renovation
- Sustainability angle is strong (net-zero, passive house, adaptive reuse)
- BC mountain/ocean setting is a plus for their audience

**What to avoid:**
- Purely architectural language — Dwell is lifestyle-first
- Projects without a homeowner willing to be interviewed
- Over-styled interiors that feel magazine-set rather than lived-in

---

### Western Living — The BC Play

**Why it matters:** Dominant publication for BC design community. 25K print distribution. Every designer and architect in Western Canada reads it. The Design of the Year (DOTY) awards are the most prestigious in Western Canada.

**How to submit:**
1. Email the editor directly (check current masthead at westernliving.ca)
2. Subject: `Project Feature: [Project Name], [City BC]`
3. Include: Brief description + 8-10 hero images + credits
4. BC angle is essential — the location, the landscape response, local materials

**What editors want:**
- BC/Western Canadian projects (this is non-negotiable)
- Interior design focus with lifestyle context
- The "West Coast" aesthetic — natural materials, indoor-outdoor living, mountain/ocean views
- Strong kitchen, living room, and primary bedroom coverage
- Designer or architect willing to provide quotes
- Styling that feels elevated but approachable

**DOTY Awards (Separate process):**
- Early bird deadline: April 1 (~$150)
- Final deadline: varies
- Event: September 10
- Projects must be in Western Canada, completed within 2 years
- Winning = Western Living feature + trophy + gala recognition

---

### Canadian Architect — The Industry Play

**Why it matters:** Every architect in Canada reads this. Publication here = instant professional credibility. Their Photo Awards let you enter directly as a photographer.

**How to submit projects:**
1. Email editor with project brief + 10-15 images
2. Canadian projects only
3. Strong design narrative required — technical depth appreciated here
4. Include floor plans (almost expected for this publication)

**Photo Awards of Excellence (Enter directly as photographer):**
- Opens: ~August 1
- Deadline: ~September 12
- Fee: ~$75 CDN
- Submit: Best image of a Canadian building, no more than 2 years old
- Winners published in December issue + all digital platforms
- Photographer credited and featured prominently
- **This is the single highest-ROI submission Matt can make.** Win or shortlist = every architect in Canada sees your name.

---

### Azure Magazine — The Canadian Design Play

**How to submit:**
1. Email editorial team (check azuremagazine.com for current contacts)
2. Canadian design focus — architecture, interiors, product design
3. Include brief + 10-15 images + credits
4. Design-forward narrative required

---

## Quarterly Submission Review Process

Run this every quarter (January, April, July, October):

### Step 1: Audit Unsubmitted Projects

Review all projects delivered in the past 6 months. For each:

```
| Project | Delivered | Design Merit (1-5) | Submitted To | Status |
|---|---|---|---|---|
| [Name] | [Date] | [Score] | [Publications] | [Pending/Published/Declined] |
```

**Design merit scoring:**
- **5** — Unique concept, strong site, excellent design, Dezeen-worthy
- **4** — Well-designed, good story, suitable for Dwell/Western Living + ArchDaily
- **3** — Solid work, good for ArchDaily + Canadian publications
- **2** — Professional but not publication-ready (marketing use only)
- **1** — Standard documentation, no editorial angle

Only submit projects scoring 3+.

### Step 2: Prepare Missing Packages

For any 3+ project without a complete submission package, build one using the template above.

### Step 3: Submit in Priority Order

Follow the submission priority logic. Track everything in the exclusivity tracker.

### Step 4: Follow Up

- Dezeen: One polite follow-up at 3 weeks, then move on
- ArchDaily: No follow-up needed — their portal shows status
- Others: One follow-up at 2-3 weeks if no response

---

## Client Communication

### Getting Permission

Always get written approval before submitting a client's project. Use this template:

```
Subject: Publication opportunity — [Project Name]

Hi [Architect/Designer Name],

I'd like to submit [Project Name] to [Publication(s)] for editorial consideration.
The project photographs well and I think it has a strong shot.

Here's what I'd need from you:
- Approval to submit (the photos are ready to go)
- Floor plans or drawings if you're open to sharing them
- A brief project description or confirmation that I can draft one
- Any credits I should include beyond [list known credits]

There's no cost to you — I handle the submission process. If they publish,
you get a feature in [Publication] with full firm credit.

Let me know if you're interested and I'll prepare the package.

Matt
```

### After Publication

When a project gets published:

1. Email the client immediately with the link and congratulations
2. Share on your Instagram, LinkedIn, and website (tag the client)
3. Add the publication credit to the project page on your website
4. Update your press page
5. Use the publication as proof in future pitches ("I recently got [Firm]'s project into [Publication]")
6. If retainer client: include in their quarterly report

---

## Awards ↔ Publications Synergy

Awards and publications feed each other. Use this cycle:

```
Shoot project → Submit to publications → Win award using published images
                                        → Use award win to pitch more publications
                                        → Use publication + award credits in cold outreach
                                        → Architect sees ROI → Retainer conversion
```

### Key Awards That Drive Publications

| Award | Deadline | Fee | Publication Overlap |
|---|---|---|---|
| **Canadian Architect Photo Awards** | ~Sept 12 | $75 | Winners in December issue |
| **AFBC Awards of Excellence** | ~July 25 | Varies | Winners covered by Canadian Architect, Azure |
| **RAIC Governor General's Medals** | Dec 11, 2026 | ~$415 | National press coverage |
| **Western Living DOTY** | April 1 early bird | ~$150 | Feature in Western Living |
| **Georgie Awards** | Varies | Varies | Covered by local/trade press |
| **Wood Design & Building Awards** | June 27 | Free (BC) | Winners in Wood Design & Building magazine |
| **Architizer A+ Awards** | ~February | Varies | Global exposure on Architizer platform |

### Direct Photographer Entry

You can enter these directly (not through a client):
- **Canadian Architect Photo Awards** — $75, best single image, September deadline
- **Architizer A+ Awards** — Photography categories available
- **APA (Architectural Photography Awards)** — International, annual

---

## Building Editor Relationships

This is a long game. The goal is that editors recognize your name and associate it with quality.

### Month 1-3: Establish Presence
- Submit 2-3 strong projects to ArchDaily (build published portfolio)
- Enter Canadian Architect Photo Awards when submissions open
- Follow editors on Instagram and LinkedIn — engage genuinely with their content

### Month 4-6: Pitch Higher
- Use ArchDaily publications as credibility when pitching Dezeen, Dwell, Western Living
- Attend RAIC Conference (May 5-8, Vancouver) — editors attend these
- Share published work on LinkedIn tagging publications and firms

### Month 7-12: Become a Known Name
- Pitch Western Living with a BC project (your home turf advantage)
- Submit to Dezeen with the strongest project of the year
- Follow up on any shortlisted award entries — use those as press hooks
- Aim for 4-6 publications in year one across all tiers

### Ongoing
- Every published project gets shared across all channels
- Every new project gets evaluated for submission within 2 weeks of delivery
- Maintain relationships — share relevant content, congratulate editors on good features
- Add a "Press" or "Published In" section to your website as credits accumulate
- Update your email signature with publication credits
- Reference publications in cold emails and proposals

---

## Image Delivery Standards for Publication-Ready Work

When shooting any project, always deliver to these specs — even if the client hasn't asked about publications. This makes every project submission-ready by default.

| Parameter | Standard |
|---|---|
| Resolution | 2880px+ on long edge (6720 x 4480 native from Z7ii is fine) |
| Format | JPEG, sRGB, quality 10-12 in Lightroom |
| Color | Accurate white balance, no heavy color grading |
| Processing | Clean and natural — no heavy HDR, no sky replacements, no extreme perspective correction |
| Verticals | Corrected but not aggressively — buildings should look natural, not rendered |
| Composition | Intentional — every frame should communicate design intent, not just document a room |
| Variety | Minimum 15 selects per project: exteriors, interiors, details, context, twilight |
| Captions | Room + materials + orientation for each image |
| Metadata | IPTC fields populated: photographer, copyright, location, description |

---

## Tracking & Measurement

### Key Metrics

| Metric | Target (Year 1) | How to Track |
|---|---|---|
| Projects submitted | 6-8 | Exclusivity tracker |
| Publications achieved | 3-4 | Exclusivity tracker |
| Awards entered | 3-5 | Awards calendar |
| Awards shortlisted/won | 1-2 | Awards calendar |
| Retainer conversions from published work | 1 | Sales pipeline |
| Inbound leads mentioning publications | Any | GHL |

### Publication Credibility Milestones

```
[ ] First ArchDaily publication
[ ] Canadian Architect Photo Awards entry submitted
[ ] First Canadian publication (Western Living, Azure, or Canadian Architect)
[ ] First international publication (Dezeen, Dwell, or equivalent)
[ ] Photo Awards shortlist or win
[ ] Press page live on website with 3+ credits
[ ] "Published in" added to email signature
[ ] Client references your publication credits in a testimonial
[ ] First retainer client citing publications as reason for signing
```

---

## Common Mistakes to Avoid

1. **Waiting for the "perfect" project** — Submit good projects now. Don't wait for a masterpiece.
2. **Submitting everywhere simultaneously** — Respect exclusivity or you'll burn bridges with top-tier editors.
3. **Weak project descriptions** — Editors read hundreds of pitches. Lead with the design story, not adjectives.
4. **Not including floor plans** — This is the #1 easiest way to increase acceptance odds. Just ask the architect.
5. **Following up too aggressively** — One check-in is fine. Two is pushy. Three burns the relationship.
6. **Not tracking submissions** — Without a tracker you'll double-submit, miss follow-ups, and lose data.
7. **Ignoring ArchDaily because it's "easy"** — ArchDaily publications are legitimate credentials. Start there.
8. **Not telling clients about publications** — Every published project is a retention and upsell opportunity.
9. **Over-processing images** — Editorial standards are cleaner and more natural than commercial/marketing standards.
10. **Forgetting to update your own marketing** — Every publication should appear on your website, LinkedIn, and proposals within 48 hours.

---

## Retainer Upsell Path

Publications are the strongest conversion tool for retainer sales. Every publication is proof that your service delivers ROI beyond the photos themselves.

### The Conversation Arc

**After first publication together:**
> "Now that [Project] is published in [Publication], imagine if we did this systematically for every project you complete this year. That's what the Publication Partner retainer looks like."

**Pricing context** (from `business/sales/architect-retainer-model.md`):
- Portfolio Partner: $2,000/mo — 4 shoots/year + 1 awards package
- Publication Partner: $3,000/mo — 6 shoots/year + 2 publication submissions + social content

**Key stat to reference:** A la carte equivalent of the Publication Partner tier is $25,000-$35,000/year. The retainer costs $36,000 but includes ongoing relationship, priority scheduling, and cost-share coordination.

### When to Pitch

- Right after a publication goes live (highest emotional moment)
- During quarterly reviews with existing clients
- When a client mentions wanting more press/awards recognition
- After you've done 2+ projects with them (relationship established)

---

## Annual Calendar

| Month | Publications | Awards | Actions |
|---|---|---|---|
| **January** | — | RAIC Annual Awards deadline (Jan 9) | Quarterly review. Pitch architects on spring shoots for summer award deadlines. |
| **February** | — | Architizer A+ deadline | Submit to Architizer if entering. |
| **March** | — | — | Prepare packages for spring submissions. Western Living DOTY early bird prep. |
| **April** | Western Living pitches | WL DOTY early bird (Apr 1) | Submit DOTY entries. Pitch Western Living with BC projects. |
| **May** | ArchDaily batch | Wood Design opens, RAIC Conference (May 5-8), Georgie Awards (May 23) | Network at RAIC. Submit ArchDaily batch. Attend Georgie gala. |
| **June** | Dezeen pitches | Wood Design deadline (Jun 27) | Pitch strongest project to Dezeen. Submit Wood Design entries. |
| **July** | Continue ArchDaily | AFBC deadline (~Jul 25) | Submit AFBC entries. Continue ArchDaily submissions. |
| **August** | — | CA Photo Awards opens (~Aug 1) | Select best single image for Photo Awards. |
| **September** | Western Living follow-ups | CA Photo Awards deadline (~Sep 12), WL DOTY event (Sep 10) | Submit Photo Awards entry. Attend DOTY event if shortlisted. |
| **October** | Dwell pitches | — | Quarterly review. Pitch Dwell with lifestyle-angle projects. |
| **November** | Azure pitches | Architizer opens (~Nov) | Pitch Azure. Plan Architizer entries. |
| **December** | — | RAIC GG Medals deadline (Dec 11) | Submit GG entries. Year-end review. Plan next year's targets. |

---

## Appendix: File Naming Convention for Submission Assets

Store submission packages in Dropbox alongside project deliverables:

```
2026/Clients/Projects/[Project Name]/
  ├── Deliverables/          # Client delivery (existing)
  └── Publications/          # Submission assets
      ├── project-brief.pdf
      ├── description.txt
      ├── credits.txt
      ├── floor-plans/
      │   ├── main-level.pdf
      │   └── site-plan.pdf
      └── selects/
          ├── [project]-exterior-hero-matt-anthony.jpg
          ├── [project]-living-room-south-matt-anthony.jpg
          └── ...
```

This keeps everything organized and accessible when an editor requests the full package.
