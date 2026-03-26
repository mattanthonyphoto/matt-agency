# Cold Email Pipeline

Process prospect leads through qualification, decision maker research, and 3-email sequence generation.

## Trigger

User says: "process cold email leads from the [Tab] tab"

Supported tabs: **Builders**, **Architects**, **Designers**, **Trades**

## Prerequisites

- `.env` has `ICYPEAS_API_KEY`
- Google OAuth token valid (`credentials.json` / `token.json`)
- Input sheet: `1d5z2ph5FDztS4CQBTQwvnV8lBhkWe0Cll2q-nRYpp3s`
- Output sheet: `1xyug1GkKKLX3htiI8bHJ9oM4O-ymTfHteCIospcDKrs`

## Pipeline Flow

### Step 1 — Fetch Unprocessed Leads

```bash
python tools/cold_email.py fetch-leads --tab [Tab]
```

Returns JSON array of `{company, website}` not yet in output sheet. If empty, stop.

### Step 2 — Process Each Lead

For each lead in the array:

#### 2a. Scrape Website

Use **WebFetch** to grab up to 3 pages:
1. Homepage (the website URL)
2. About page — try: `/about`, `/about-us`, `/team`, `/our-team`, `/people`, `/leadership`
3. Projects page — try: `/projects`, `/portfolio`, `/our-work`, `/work`, `/gallery`

Save results to `.tmp/scraped.json` as:
```json
[
  {"url": "https://example.com", "html": "<html>..."},
  {"url": "https://example.com/about", "html": "<html>..."},
  {"url": "https://example.com/projects", "html": "<html>..."}
]
```

If a page returns 404, skip it and try the next pattern. Minimum 1 page required.

#### 2b. Clean HTML

```bash
python tools/cold_email.py clean-html --input .tmp/scraped.json
```

Returns cleaned text (1500 chars per page, max 5 pages). Save output to `.tmp/cleaned.json`.

#### 2c. Qualify Lead

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

#### 2d. Check Qualification

If qualification score is **Disqualified** or **Weak Fit**:
- Do NOT write to output sheet — only qualified leads go to output
- Mark in input sheet immediately:
```bash
python tools/cold_email.py mark-processed \
  --tab Builders --website "https://example.com" \
  --status "Yes" --qualified "NOT QUALIFIED"
```
- Skip to next lead

If **Moderate Fit** or **Strong Fit**: continue.

**IMPORTANT:** After writing each qualified lead to the output sheet, immediately mark it in the input sheet:
```bash
python tools/cold_email.py mark-processed \
  --tab Builders --website "https://example.com" \
  --status "Yes" --qualified "QUALIFIED — Strong Fit"
```

Input sheet format (must match exactly):
- **Processed column:** `Yes`
- **Qualified column:** `QUALIFIED — Strong Fit`, `QUALIFIED — Moderate Fit`, or `NOT QUALIFIED`

#### 2e. Decision Maker Research (if needed)

If decision maker first name AND last name are both "Not found":
- Use **WebSearch**: `"{company name}" {city if known} owner founder principal`
- Parse results for name, role, email
- Update decision maker fields

#### 2f. Classify Email

Check the email tier from qualification:
- **Tier 1 or Tier 2**: Personal email found — use it directly
- **Tier 3**: Generic email (info@, hello@, etc.) — proceed to Icypeas lookup, but **always keep the generic email as fallback**
- **Tier 4**: No email found on site — check the website contact page directly, then try Icypeas if name is known. Every qualified lead MUST have at least a business email in the output.

#### 2g. Icypeas Lookup (if needed)

Only if: we have a first name + last name but no personal email.

```bash
python tools/cold_email.py icypeas-lookup \
  --first-name "Jamie" \
  --last-name "Morrison" \
  --domain "morrisonhomes.ca"
```

If Icypeas returns a deliverable email, use it. Otherwise keep the generic email.

**Important:** Icypeas costs credits. Only call when we have a name but no personal email.

#### 2h. Generate Intro Email

Read `tools/prompts/write_intro_email.md`. Replace all `{placeholders}` with lead data from qualification. Generate the email inline.

Extract the email body text (the full email including greeting and signature).

#### 2i. Select Case Study + Generate Follow-Up Email

**Case Study Selection Logic:**

| ICP Category | Case Study | Link |
|---|---|---|
| Builder | Summerhill Fine Homes | mattanthonyphoto.com/summerhill-fine-homes |
| Builder (if prospect IS Summerhill) | Balmoral Construction | mattanthonyphoto.com/balmoral-construction |
| Architect | Sitelines Architecture | mattanthonyphoto.com/sitelines-architecture |
| Designer | LRD Studio | mattanthonyphoto.com/lrd-studio-interior-design |
| Secondary ICP | The Window Merchant | mattanthonyphoto.com/the-window-merchant |
| Generic | Main Portfolio | mattanthonyphoto.com |

**Competitor Guard:** If the prospect IS one of the case study clients (check company name and URL), switch to the fallback. For Builder: Summerhill ↔ Balmoral. For others: use generic portfolio.

**Case Study Descriptions (named):**
- Summerhill: "I photographed five luxury residences for Summerhill Fine Homes on the Sunshine Coast"
- Balmoral: "I photographed four custom homes for Balmoral Construction across Whistler and the Sea to Sky"
- Sitelines: "I documented two projects for Sitelines Architecture across residential and institutional scales"
- LRD: "I documented two major renovation projects for LRD Studio in Whistler"
- Window Merchant: "I run a monthly content retainer for The Window Merchant — project documentation, social media, and website imagery"

**Anonymous versions** (when competitor guard fires): replace client name with generic description ("a builder", "a firm", "a design studio", "a premium glazing supplier").

**Client Named:** Set to `true` unless competitor guard fired, then `false`.

Read `tools/prompts/write_followup.md`. Replace placeholders including case study fields. Generate inline.

#### 2j. Select Journal Article + Generate Breakup Email

**Journal Article Selection:**

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

Read `tools/prompts/write_breakup.md`. Replace placeholders including journal article fields. Generate inline.

#### 2k. Generate Instagram DM

During scraping, also capture the company's Instagram handle from:
- Website footer/header social links
- Input sheet Instagram column
- WebSearch: `"{company name}" Victoria BC instagram`

Write a short Instagram DM (2-3 sentences max). Rules:
- Lead with value — reference a specific recent post or project
- Casual, peer-to-peer tone (Instagram is informal)
- No pitch, no CTA beyond "check out my work"
- Link to mattanthonyphoto.com
- Written as Matt, not a business

#### 2l. Generate Subject Lines

Every email needs a subject line:
- **Intro**: 3-5 words, reference the project name or location. E.g. "Your Whistler project" or "Lands End"
- **Follow-up**: 2-4 words, casual. E.g. "quick follow up" or "one more thing"
- **Breakup**: 2-4 words, zero clickbait. E.g. "something useful" or "one last thing"

#### 2m. Write Result

Save result to `.tmp/result.json` with all fields matching the output sheet columns (A:W):
```json
{
  "company_name": "Example Homes",
  "website_url": "https://examplehomes.ca",
  "decision_maker_name": "Jamie Morrison",
  "role": "Owner",
  "city": "Whistler",
  "email": "jamie@examplehomes.ca",
  "phone": "250-555-1234",
  "instagram": "@examplehomes",
  "icp_category": "Builder",
  "outreach_type": "Cold",
  "qualified": "Strong Fit",
  "intro_subject": "The Whistler project",
  "intro_email": "Hi Jamie,...",
  "followup_subject": "quick follow up",
  "followup_email": "Hi Jamie,...",
  "breakup_subject": "something useful",
  "breakup_email": "Hi Jamie,...",
  "instagram_dm": "Hey Jamie, been following...",
  "timeline": "Day 1: Intro email + IG DM | Day 4: Follow-up | Day 8: Breakup"
}
```

**Output sheet columns (A:W):** Company, Decision Maker, Role, City, Score, ICP, Email, Phone, Instagram, Website, Outreach, Status, Timeline, Intro Subject, Intro Email, Follow-Up Subject, Follow-Up Email, Breakup Subject, Breakup Email, Instagram DM, Travel Est., Marketing Angle, Notes

```bash
python tools/cold_email.py write-result --json .tmp/result.json
```

**Then immediately mark the input sheet:**
```bash
python tools/cold_email.py mark-processed \
  --tab Builders --website "https://examplehomes.ca" \
  --status "Yes" --qualified "QUALIFIED — Strong Fit"
```

### Step 3 — Contact Timeline

Standard cadence per lead:

| Day | Action | Channel |
|-----|--------|---------|
| Day 1 | Send intro email | Email |
| Day 1 | Send Instagram DM | Instagram |
| Day 4 | Send follow-up email | Email |
| Day 8 | Send breakup email | Email |
| Day 10+ | Phone call (if no response to any touchpoint) | Phone |

Notes:
- Send intro email and IG DM on the same day — different channels reinforce each other
- Follow-up at Day 4 (not Day 3) gives them a full business week cycle
- Breakup at Day 8 gives breathing room after the follow-up
- Phone is the last resort — only after all written touchpoints have gone unanswered

### Step 4 — Summary

After all leads are processed, print a summary:
- Total leads processed
- Qualified vs disqualified
- Email addresses found (personal vs generic vs Icypeas vs none)
- Instagram handles found vs missing
- Any errors or leads needing manual review

## Error Recovery

- **WebFetch fails for all pages:** Log the error, write result with `qualified: "SCRAPE FAILED"`, continue to next lead
- **Icypeas fails:** Keep the generic email, note in result, continue
- **Sheets write fails:** Save result JSON to `.tmp/failed/` for retry

## Quality Checks

After each email is generated, verify:
- No banned words from the prompt files
- Correct sentence count (5 for intro, 4 for follow-up, 2-3 for breakup)
- Signature block present
- All links include full URLs with `https://`
- No em dashes or semicolons

If an email fails quality checks, regenerate once with explicit fix instructions.

## Step 5 — Export to Instantly

```bash
python tools/cold_email.py export-instantly
```

Exports all qualified leads to `.tmp/instantly_import.csv` for direct import into Instantly.ai.

**Instantly sequence setup:**
- Step 1 (Day 1): Subject = `{{intro_subject}}`, Body = `{{intro_body}}`
- Step 2 (+3 day delay): **Leave subject blank** (reply-in-thread), Body = `{{followup_body}}`
- Step 3 (+4 day delay): **Leave subject blank** (reply-in-thread), Body = `{{breakup_body}}`

**Reply-in-thread** sends follow-ups as replies to the intro email — significantly higher open rates.

**Critical Instantly rules:**
- Send from secondary domains (e.g. `mattanthony.co`), never `mattanthonyphoto.com`
- Warm up accounts 2-3 weeks before launching
- 30 campaign emails + 10 warmup per account per day
- Use fallbacks: `{{First Name|there}}` for missing data
- Keep warmup running alongside campaigns
- Monday-Friday sending only, 8am-12pm prospect time zone

## Travel Cost Reference (from Squamish)

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

**Strategy:** Batch 2-3 shoots per ferry trip to spread the $160 RT ferry cost. Your COGS budgets $125-150 for travel — Victoria trips run 2-3x over that baseline.

## Notes

- Process leads one at a time, not in parallel — maintains conversation context for quality
- Each lead takes ~30-60 seconds for scraping + qualification + 3 emails
- Icypeas lookup adds ~12 seconds when needed
- The prompts in `tools/prompts/` are the source of truth for email generation rules
- Leads without Instagram are flagged as Creative Partner retainer upsell opportunities
