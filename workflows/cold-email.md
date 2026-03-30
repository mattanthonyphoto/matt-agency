# Cold Email Pipeline — Standard Operating Procedure

Process prospect leads through verification, qualification, decision maker research, and 3-email sequence generation.

This SOP is the single source of truth for processing cold email leads. Reference it every time you process a prospect. The prompts in `tools/prompts/` handle the specific email generation rules — this document handles everything else.

---

## Prerequisites

- `.env` has `ICYPEAS_API_KEY`
- Google OAuth token valid (`credentials.json` / `token.json`)
- Input sheet: `1qaeT6nURloVQx48dPtJODUz55IrqQEyRJ5xmnJJjoVs`
- Output sheet: `1brgQYbtCZwH1fFS3vYjMaW9IGf8iK37qeDBY2l06r8A`

---

## Part 1 — Lead Verification (Before Qualification)

Every lead MUST be individually verified before qualification. Never batch-skip or batch-mark leads.

### 1a. Fetch Unprocessed Leads

```bash
python tools/cold_email.py fetch-leads --tab [Tab]
```

Returns JSON array of `{company, website}` not yet processed. If empty, stop.

### 1b. Verify Website Is Reachable

For each lead, attempt to load the website via **WebFetch**.

**If WebFetch fails (ECONNREFUSED, SSL, timeout):**
1. Retry with `http://www.` prefix (many small firms lack SSL)
2. Retry without `www.` prefix
3. If all URL variations fail, use **WebSearch** to find the company via directories (Houzz, BBB, LinkedIn, Yellow Pages)
4. Only mark as "SCRAPE FAILED" after exhausting all three fallbacks

**If the company appears to be permanently closed or the domain is parked/for sale:**
- Mark as `NOT QUALIFIED` with note "Business closed" or "Domain inactive"
- Skip to next lead

### 1c. Verify Business Is Active

Quick signals that a business is still operating:
- Website has recent projects (within 2 years)
- Active social media (posted within 6 months)
- Phone number answers or has a voicemail
- Listed in current directories

If uncertain, proceed with qualification — the scrape will reveal more.

---

## Part 2 — Prospect Research (Per Lead)

This is the most important step. The quality of research directly determines the quality of every email.

### 2a. Scrape Website (3 pages minimum attempt)

Use **WebFetch** to grab up to 3 pages:
1. **Homepage** — the website URL
2. **About page** — try in order: `/about`, `/about-us`, `/team`, `/our-team`, `/people`, `/leadership`, `/our-story`
3. **Projects/Portfolio page** — try: `/projects`, `/portfolio`, `/our-work`, `/work`, `/gallery`

If a page returns 404, try the next pattern. Minimum 1 page required.

**From each page, extract and note:**
- Company description and positioning
- Specific project names, locations, and details
- Team member names and roles
- Contact info (email, phone, address)
- Social media handles (especially Instagram)
- Founding year or years in business
- Awards, publications, press mentions
- Design philosophy or process language
- Client types and project scale

### 2b. Award Research (Mandatory)

**WebSearch** the prospect's award history before writing anything. Never assume zero awards.

Search queries:
- `"{company name}" award`
- `"{owner name}" award`
- Check relevant award databases for their ICP:
  - Builders: Georgie Awards, CHBA, HAVAN
  - Architects: AIBC, RAIC, Governor General's Medal, Architizer, Wood Design Awards
  - Designers: IDIBC, Western Living DOTY, NKBA
  - Trades: AWMAC, specific trade association awards

If awards are found, note them — they're strong outreach signals.

### 2c. Instagram Research

During scraping, capture the company's Instagram handle from:
- Website footer/header social links
- Input sheet Instagram column
- **WebSearch**: `"{company name}" {city} BC instagram`

Note: If the prospect has no Instagram presence, flag them as a Creative Partner retainer upsell opportunity (they need content help).

### 2d. Marketing Contact Research (Builders $1M-$5M)

For builder prospects, check who actually handles marketing. In the $1M-$5M range, the owner is usually on-site all day and the **spouse or office manager** handles website, social media, and award submissions. They are often the real decision-maker for photography.

**Where to look:**
- Company website "Team" or "About" page — titles like Office Manager, Marketing Coordinator, Co-Owner
- LinkedIn — search company, filter employees, look for non-construction titles
- Instagram — check who runs the account (posting style, bio mentions)
- Facebook — builder's profile often shows spouse who lists company in work history

**If found:** Note the marketing contact name, title, and channel (IG handle, email) in the Additional Notes field. This enables parallel outreach to the right person.

See `business/sales/spouse-office-manager-channel.md` for full targeting strategy.

### 2e. Clean HTML

```bash
python tools/cold_email.py clean-html --input .tmp/scraped.json
```

Returns cleaned text (1500 chars per page, max 5 pages). Save output to `.tmp/cleaned.json`.

---

## Part 3 — Qualification

### 3a. Run Qualification

Read the prompt from `tools/prompts/qualify_lead.md`. Replace placeholders:
- `{website_url}` — the lead's website
- `{website_content}` — the combined_content from cleaned output

Process the qualification inline. Parse the structured output to extract:
- `icp_tier`, `icp_category`, `qualification_score`
- `decision_maker_first_name`, `decision_maker_last_name`, `decision_maker_role`
- `email`, `email_tier`
- `fit_signals`, `documentation_gap`, `specific_detail_for_outreach`
- `outreach_type` (Cold or Warm Re-engagement)
- `additional_notes`

### 3b. Qualification Decision

**If Disqualified or Weak Fit:**
- Do NOT write to output sheet — only qualified leads go to output
- Mark in input sheet immediately:
```bash
python tools/cold_email.py mark-processed \
  --tab [Tab] --website "https://example.com" \
  --status "Yes" --qualified "NOT QUALIFIED"
```
- Skip to next lead

**If Moderate Fit or Strong Fit:** Continue to Part 4.

### 3c. ICP-Specific Qualification Notes

Each ICP has different qualification signals. Use these as guides:

**Builders:** Custom one-off projects, complex builds, architect involvement, long timelines. Disqualify: spec homes, production builders, renovation-only with no portfolio.

**Architects:** Completed built work (not just renders), design-led practice, awards/publications, credits collaborators. Disqualify: drafting services only, no built portfolio.

**Interior Designers:** Spatial design (not just decorating), high-end residential or commercial, craft and material focus. Disqualify: home staging, retail decor, no portfolio.

**Millwork & Cabinetry:** Custom/bespoke fabrication, architect-specified work, visible craftsmanship. Disqualify: big-box cabinet dealers, franchise operations.

**Windows & Doors:** Custom or high-performance fenestration, architect-designed integrations. Disqualify: basic replacement window companies, vinyl-only installers.

**Structural Fabrication:** Expressive, visible structural work (exposed steel, ornamental metal). Disqualify: hidden structural steel, pure industrial fabrication.

**Landscape Architecture:** Site-responsive design, photographable outdoor environments. Disqualify: lawn care only, maintenance-only companies.

**Lighting Design:** Spatial lighting systems, architectural experience. Disqualify: bulb retailers, basic electricians.

**Building Envelope:** Facades, cladding, exterior systems that define the building visually. Disqualify: basic insulation contractors, hidden waterproofing only.

**Flooring & Stone:** Premium materials, custom installations in high-end projects. Disqualify: discount flooring outlets, big-box retailers.

**Hardware & Fixtures:** Custom or artisan hardware, luxury fixtures visible in finished spaces. Disqualify: wholesale-only distributors, commodity hardware.

---

## Part 4 — Decision Maker Research

### 4a. Extract Decision Maker from Scrape

The qualification prompt extracts the decision maker. Check its output:
- If first AND last name found → proceed
- If partial name → flag for manual research but proceed
- If both "Not found" → go to 4b

### 4b. External Decision Maker Search

If the website didn't reveal a name:
1. **WebSearch**: `"{company name}" {city} owner founder principal`
2. **WebSearch**: `"{company name}" team leadership`
3. Check LinkedIn company page
4. Check Houzz profile (often lists the owner)

### 4c. Decision Maker Hierarchy

When the primary decision maker's email can't be found, go down the hierarchy:
1. Owner / Founder / Principal — always try first
2. General Manager / Operations Manager — next best
3. Project Manager / Construction Manager — still reaches leadership
4. Any named person with a direct email — better than generic inbox

### 4d. Email Discovery

**Email Priority (use highest tier found):**

| Tier | Type | Example | Action |
|------|------|---------|--------|
| 1 | Personal named email | jamie@firm.com | Use directly |
| 2 | Likely personal (initials match) | jm@firm.com | Use, flag as "likely personal" |
| 3 | Generic business email | info@, hello@ | Use as fallback, try Icypeas for personal |
| 4 | No email found | — | Check contact page, try Icypeas, WebSearch |

**Where to find emails — check ALL of these:**
- Contact page
- Footer
- Team/about page bios
- mailto: links in HTML
- Job listings (hiring contact emails)
- Press/media sections
- Social media profiles

### 4e. Icypeas Lookup (If Needed)

Only if: we have a first + last name but no personal email, AND we have a Tier 3 generic email as fallback.

```bash
python tools/cold_email.py icypeas-lookup \
  --first-name "Jamie" \
  --last-name "Morrison" \
  --domain "morrisonhomes.ca"
```

If Icypeas returns a deliverable email, use it. Otherwise keep the generic email.

**Important:** Icypeas costs credits. Only call when we have a name but no personal email. Never guess email patterns — pattern guesses have ~50% failure rate.

### 4f. Email Verification

Before deploying any email to Instantly, verify via Icypeas email-verification API:
- `DEBITED` = valid
- `DEBITED_NOT_FOUND` = email doesn't exist

For failed emails, try Icypeas email-search with name + domain as fallback. If both fail, revert to generic email.

---

## Part 5 — Email Generation

### 5a. ICP-Specific Angles

The offer is always the same: architectural photography of completed projects plus documentary-style video. What changes is the angle:

| ICP | What They Care About | Matt's Angle |
|-----|---------------------|--------------|
| Architect | Design intent gets misread, costing peer credibility and commissions | Photography that makes design thinking legible to juries, editors, and peers |
| Builder | Best work should win the next project without explaining it | Photography at milestones plus video that makes execution undeniable |
| Designer | Work gets misread as styling when it's spatial design | Photography that communicates thinking behind the space |
| Secondary ICP | Craft disappears into finished buildings without documentation | Photography showing their work in context, at the detail level it deserves |

### 5b. Case Study Selection

| ICP Category | Case Study | Link |
|---|---|---|
| Builder | Summerhill Fine Homes | mattanthonyphoto.com/summerhill-fine-homes |
| Builder (if prospect IS Summerhill) | Balmoral Construction | mattanthonyphoto.com/balmoral-construction |
| Architect | Sitelines Architecture | mattanthonyphoto.com/sitelines-architecture |
| Designer | LRD Studio | mattanthonyphoto.com/lrd-studio-interior-design |
| Secondary ICP | The Window Merchant | mattanthonyphoto.com/the-window-merchant |
| Generic | Main Portfolio | mattanthonyphoto.com |

**Competitor Guard:** If the prospect IS one of the case study clients, switch to the fallback. For Builder: Summerhill <> Balmoral. For others: use generic portfolio.

**Named descriptions:**
- Summerhill: "I photographed five luxury residences for Summerhill Fine Homes on the Sunshine Coast"
- Balmoral: "I photographed four custom homes for Balmoral Construction across Whistler and the Sea to Sky"
- Sitelines: "I documented two projects for Sitelines Architecture across residential and institutional scales"
- LRD: "I documented two major renovation projects for LRD Studio in Whistler"
- Window Merchant: "I run a monthly content retainer for The Window Merchant, covering project documentation, social media, and website imagery"

**Anonymous versions** (when competitor guard fires): replace client name with generic description.

### 5c. Journal Article Selection

| ICP Category | Article | Link |
|---|---|---|
| Builder | ROI of Professional Architectural Photography | mattanthonyphoto.com/journal/roi-professional-architectural-photography-builders |
| Architect | What Architects Should Look for When Hiring a Photographer | mattanthonyphoto.com/journal/what-architects-should-look-for-hiring-photographer |
| Designer | Documenting Design Intent | mattanthonyphoto.com/journal/documenting-design-intent-photography-before-build-finished |
| Secondary / Generic | Build a Visual Library | mattanthonyphoto.com/journal/build-visual-library-website-proposals-awards |

**Hooks:**
- Builder: "I wrote a piece on the ROI of professional photography for custom builders"
- Architect: "I wrote a piece on what to look for when hiring an architectural photographer"
- Designer: "I wrote a piece on documenting design intent and why timing matters"
- Secondary/Generic: "I wrote a piece on building a visual library that works across your website, proposals, and awards"

### 5d. Generate Intro Email

Read `tools/prompts/write_intro_email.md`. Replace all `{placeholders}` with lead data. Generate inline.

**Critical rules (from prompt + feedback):**
- 5 sentences total, 3 paragraphs + signature
- Opener must reference a specific project or detail from their site
- Detail must be architectural/visual (site, material, light, space) — never program stats
- No em dashes, semicolons, or superlatives anywhere
- Signature block: Matt / Architectural Photography + Documentary Video / mattanthonyphoto.com

### 5e. Generate Follow-Up Email

Read `tools/prompts/write_followup.md`. Replace placeholders including case study fields. Generate inline.

**Critical rules:**
- 4 sentences total, 3 paragraphs + signature
- Do NOT repeat the project name from the intro
- Portfolio link (mattanthonyphoto.com) in paragraph 2, sentence 1
- Case study link in paragraph 2, sentence 2
- Never use "case study" or "visual identity" in the email

### 5f. Generate Breakup Email

Read `tools/prompts/write_breakup.md`. Replace placeholders including journal article. Generate inline.

**Critical rules:**
- 2-3 sentences max + signature
- Do NOT reference previous emails
- Journal article link replaces portfolio link
- Frame as giving, not pitching

### 5g. Generate Instagram DM

Write a short DM (2-3 sentences max):
- Lead with value — reference a specific recent post or project
- Casual, peer-to-peer tone
- No pitch, no CTA beyond "check out my work"
- Link to mattanthonyphoto.com
- Written as Matt, not a business

### 5h. Generate Subject Lines

- **Intro**: 3-5 words, reference the project name or location. E.g. "Your Whistler project" or "Lands End"
- **Follow-up**: 2-4 words, casual. E.g. "quick follow up" or "one more thing"
- **Breakup**: 2-4 words, zero clickbait. E.g. "something useful" or "one last thing"

---

## Part 6 — Variety & Anti-Template Rules

This is critical. Matt flagged identical value prop sentences repeated 136x across a batch. That kills credibility.

### 6a. Variation Pools

Build pools of 10-13 variations for each structural sentence:
- Value prop sentence 1 (what Matt does)
- Value prop sentence 2 (what it gets them)
- Follow-up recap sentence
- Follow-up CTA
- Breakup opener
- Breakup closer

### 6b. Rotation Rules

- Use offset index rotation so adjacent leads in the same city get different combos
- Max acceptable repeat of any single sentence across a campaign: ~1 in 13 leads
- The opener (project reference) is already unique per lead
- After generating a batch, run a uniqueness check before writing to the sheet

### 6c. Per-ICP Language

Each ICP uses different vocabulary:

**Architects:** "Documenting" not "shooting." Reference materiality, spatial quality, site response. Never say "marketing" or "content." Prebooking angle for spring/summer.

**Builders:** Frame around build process, milestones. Finished result implied by sentence 2. Don't try to cover both timeframes in sentence 1.

**Designers:** Frame around spatial thinking, design intent. Distinguish from decorating/styling.

**Secondary ICP:** Frame around craft visibility, work in context, documentation before the next project covers it up.

---

## Part 7 — Quality Checks

Run these checks on EVERY email before writing to the sheet:

### 7a. Content Checks
- [ ] No banned words (superlatives, cliches, urgency language, vendor language)
- [ ] No em dashes (—), en dashes (–), or spaced hyphens
- [ ] No semicolons
- [ ] Correct sentence count (5 intro, 4 follow-up, 2-3 breakup)
- [ ] Signature block present and complete (all 3 lines)
- [ ] All links include full URLs with `https://`
- [ ] All proper nouns correctly capitalized
- [ ] No word appears more than twice in the whole email
- [ ] No sentence longer than 30 words
- [ ] No more than one "and" per sentence

### 7b. Structural Checks
- [ ] Opener starts with "I came across" and includes "on your site"
- [ ] Opener references specific project/detail from research (not generic)
- [ ] Detail is visual/architectural (would be visible in a photograph)
- [ ] Closing phrase follows one of three approved patterns
- [ ] CTA offers samples, not a call/meeting
- [ ] Follow-up does NOT repeat the project name from intro
- [ ] Follow-up includes both portfolio link AND case study link
- [ ] Breakup does NOT reference previous emails
- [ ] Breakup includes journal article link

### 7c. Compliance Checks (CASL)
- [ ] Recipient email was conspicuously published on their website
- [ ] Message is relevant to their business role
- [ ] Email will include sender identification + physical address + unsubscribe (handled by Instantly)

### 7d. Data Completeness
- [ ] Every field in the output sheet is filled (real data or "Not found" with reason)
- [ ] Decision maker name present (or flagged for manual research)
- [ ] Email present (personal, or generic as fallback)
- [ ] Instagram handle present (or flagged as missing)
- [ ] City confirmed
- [ ] Travel estimate included

If an email fails quality checks, regenerate once with explicit fix instructions.

---

## Part 8 — Write Result & Mark Processed

### 8a. Save Result

Save to `.tmp/result.json` with all fields matching output sheet columns (A:W):

```json
{
  "company_name": "",
  "website_url": "",
  "decision_maker_name": "",
  "role": "",
  "city": "",
  "email": "",
  "phone": "",
  "instagram": "",
  "icp_category": "",
  "outreach_type": "",
  "qualified": "",
  "intro_subject": "",
  "intro_email": "",
  "followup_subject": "",
  "followup_email": "",
  "breakup_subject": "",
  "breakup_email": "",
  "instagram_dm": "",
  "timeline": "Day 1: Intro email + IG DM | Day 4: Follow-up | Day 8: Breakup",
  "travel_est": "",
  "marketing_angle": "",
  "notes": ""
}
```

**Output sheet columns (A:W):** Company, Decision Maker, Role, City, Score, ICP, Email, Phone, Instagram, Website, Outreach, Status, Timeline, Intro Subject, Intro Email, Follow-Up Subject, Follow-Up Email, Breakup Subject, Breakup Email, Instagram DM, Travel Est., Marketing Angle, Notes

### 8b. Write to Output Sheet

```bash
python tools/cold_email.py write-result --json .tmp/result.json --tab [Tab]
```

### 8c. Mark Input Sheet

Immediately after writing to output:

```bash
python tools/cold_email.py mark-processed \
  --tab [Tab] --website "https://example.com" \
  --status "Yes" --qualified "QUALIFIED — Strong Fit"
```

Input sheet format (must match exactly):
- **Processed column:** `Yes`
- **Qualified column:** `QUALIFIED — Strong Fit`, `QUALIFIED — Moderate Fit`, or `NOT QUALIFIED`

---

## Part 9 — Contact Timeline

Standard cadence per lead:

| Day | Action | Channel |
|-----|--------|---------|
| Day 1 | Send intro email | Email |
| Day 1 | Send Instagram DM | Instagram |
| Day 4 | Send follow-up email | Email (reply-in-thread) |
| Day 8 | Send breakup email | Email (reply-in-thread) |
| Day 10+ | Phone call (if no response) | Phone |

Notes:
- Intro email and IG DM on the same day — different channels reinforce each other
- Follow-up at Day 4 gives a full business week cycle
- Breakup at Day 8 gives breathing room after follow-up
- Phone is last resort — only after all written touchpoints unanswered
- If prospect replies on ANY channel, pause all other channels immediately

---

## Part 10 — Batch Processing Summary

After processing a batch, print a summary:
- Total leads processed
- Qualified (Strong Fit / Moderate Fit) vs disqualified count
- Email addresses found: personal vs generic vs Icypeas vs none
- Instagram handles found vs missing
- Leads needing manual review (partial names, no email, scrape failed)
- Any errors encountered
- Sentence variation uniqueness report

---

## Part 11 — Export to Instantly

```bash
python tools/cold_email.py export-instantly
```

Exports qualified leads to `.tmp/instantly_import.csv`.

**Instantly sequence setup:**
- Step 1 (Day 1): Subject = `{{intro_subject}}`, Body = `{{intro_body}}`
- Step 2 (+3 day delay): Leave subject blank (reply-in-thread), Body = `{{followup_body}}`
- Step 3 (+4 day delay): Leave subject blank (reply-in-thread), Body = `{{breakup_body}}`

**Critical Instantly rules:**
- Send from secondary domains (e.g. `mattanthony.co`), never `mattanthonyphoto.com`
- Warm up accounts 3-4 weeks before launching (mandatory)
- Max 50 cold emails per inbox per day (30 campaign + 10-20 warmup)
- Keep warmup running alongside campaigns (never stop)
- Use fallbacks: `{{First Name|there}}` for missing data
- Monday-Friday sending only, 9:30am-11:30am prospect timezone
- Monitor: bounce <3%, spam complaints <0.1% — pause immediately if exceeded

**Email format rules (deliverability):**
- Plain text only — no HTML, no images, no logos
- Zero or one link maximum per email
- No spam trigger words (free, guaranteed, act now, limited time)
- Keep body under 100 words (50-80 ideal)
- Include unsubscribe link (handled by Instantly)

---

## Part 12 — Travel Cost Reference (from Squamish)

| Destination | Transport | Ferry RT | Overnight? | Total |
|---|---|---|---|---|
| Whistler | $31 | — | No | **$31** |
| Vancouver | $36 | — | No | **$36** |
| Pemberton | $48 | — | No | **$48** |
| Fraser Valley | $70-85 | — | No | **$70-85** |
| Nanaimo | $26 | $160 | No | **$186** |
| Sunshine Coast | $49 | $142 | No | **$191** |
| Kelowna | $234 | — | Yes (+$150-250) | **$385-485** |
| Victoria | $93 | $160 | Yes (+$150-250) | **$400-500** |
| Tofino | $111 | $160 | Yes (+$150-250) | **$420-510** |

**Strategy:** Batch 2-3 shoots per ferry trip to spread the $160 RT ferry cost. COGS budgets $125-150 for travel.

---

## Part 13 — Error Recovery

- **WebFetch fails for all pages:** Try HTTP fallback, then WebSearch. Only log as "SCRAPE FAILED" after exhausting all options.
- **Icypeas fails:** Keep the generic email, note in result, continue.
- **Sheets write fails:** Save result JSON to `.tmp/failed/` for retry.
- **Rate limit hit:** Pause 60 seconds, retry once. If still failing, save progress and stop.

---

## Part 14 — Key Performance Benchmarks

Target metrics for Matt's cold email campaigns:

| Metric | Target | Industry Avg |
|--------|--------|-------------|
| Open Rate | 50%+ | 27.7% |
| Reply Rate | 8-12% | 3.4% |
| Positive Reply Rate | 5%+ | 1-2% |
| Bounce Rate | <2% | 7-8% |
| Qualification Rate | 40-60% of leads | — |

---

## Processing Rules (Non-Negotiable)

1. **Process leads one at a time.** Never parallel process — maintains context for quality.
2. **Never batch-skip.** Every lead gets individually scraped and assessed. No exceptions.
3. **Never guess emails.** Pattern guesses have ~50% failure rate. Use Icypeas or keep generic.
4. **Always research awards.** WebSearch before writing. Never assume zero.
5. **Every field filled.** Real data or "Not found" with reason. No blank cells.
6. **Only qualified leads in output.** Disqualified leads marked in input only.
7. **Variety is mandatory.** 10-13 variation pools for structural sentences. No repeated value props.
8. **CTAs link to /discovery-call.** Never raw GHL widget URLs.
9. **No dashes in emails.** Use commas instead of em dashes, en dashes, or spaced hyphens.
10. **Complete all fields or stop.** If you can't finish a lead properly, leave it unprocessed for the next session rather than partially completing it.
