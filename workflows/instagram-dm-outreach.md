# Instagram DM Outreach System

## Trigger
Matt says: "run my IG outreach", "DM queue", "who should I DM today", or "Instagram prospecting"

---

## Overview

Two-channel Instagram outreach system:
1. **Manual DM Outreach** — Warm-up engagement → personalized DM → follow-up sequence → pipeline
2. **Comment-to-DM Funnel** — Content CTA → ManyChat automation → lead magnet delivery → pipeline

Both channels feed into the Unified Sales Pipeline via the IG DM Tracker sheet.

---

## Channel 1: Manual DM Outreach

### Daily Routine (15-20 min)

#### Step 1: Pull today's queue (1 min)
```bash
python3 tools/ig_dm_tracker.py get-queue
```
Returns three lists:
- **Warm-up:** New prospects — start engaging with their content
- **Ready to DM:** Warmed for 2+ days — send the first DM today
- **Follow-ups due:** Previous DMs that need a follow-up

#### Step 2: Warm-up engagement (5 min)
For each prospect in the warm-up list:
1. Go to their Instagram profile
2. Like 2-3 of their recent posts (space these out, not all at once)
3. React to their most recent Story (use a relevant emoji, not just 🔥)
4. If they posted a project, leave a genuine comment about a specific detail
5. Mark as warming:
```bash
python3 tools/ig_dm_tracker.py update-status "@handle" --status "Warming"
```

**Rules:**
- Maximum 10 warm-ups per day
- Engage with their content, not their ads or reposts
- Comments must reference something specific ("That CLT beam detail is incredible" not "Great work!")
- Never warm up and DM on the same day

#### Step 3: Send DMs (10 min)
For each prospect in the ready-to-DM list (max 15-20/day):
1. Open the DM templates reference below — pick the right one for their ICP
2. Customize the opening line to reference something specific from their recent content
3. Send the DM manually from the Instagram app
4. Log it:
```bash
python3 tools/ig_dm_tracker.py log-dm "@handle" \
  --template "builder-craft-01" \
  --message "The actual message you sent"
```

**Rules:**
- Never copy-paste the exact template — always personalize the opener
- Keep DMs under 150 words
- End with a question, not a pitch
- No links in the first DM
- Send from the Instagram app (not desktop) — looks more natural
- Best times: Tuesday-Thursday, 9-11am or 1-3pm Pacific

#### Step 4: Handle follow-ups (3 min)
```bash
python3 tools/ig_dm_tracker.py get-follow-ups
```
For each follow-up:
- **4 days after first DM, no reply:** Send a light follow-up (different angle, not "just checking in")
- **5 days after follow-up 1, no reply:** Final touch — share something valuable (article, case study) with no ask
- **7 days after follow-up 2, no reply:** Mark as No Response
- **If they replied:** Update status and continue the conversation naturally
```bash
python3 tools/ig_dm_tracker.py update-status "@handle" --status "Replied" --notes "Interested in spring shoot"
```

#### Step 5: Weekly stats (Friday)
```bash
python3 tools/ig_dm_tracker.py stats
```

---

### DM Templates

#### Builder Templates

**builder-craft-01 (Craft Recognition)**
> Hey [Name], I came across [specific project/detail from their feed]. The [specific craft element — timber detailing, concrete work, joinery] really caught my eye.
>
> I photograph architectural projects in the Sea-to-Sky and Van — always curious when I see work at this level. Are you wrapping up anything else this spring?

**builder-awards-01 (Awards Angle)**
> Hey [Name], that [project name/location] is Georgie-worthy. Have you entered it?
>
> I've shot for a few builders prepping their submissions — the photography requirement catches a lot of people off guard. When's your next completion?

**builder-legacy-01 (Legacy Framing)**
> Hey [Name], been following your work for a bit — [specific project] is the kind of build that should be properly documented.
>
> Curious, do you typically photograph your completed projects or does it end up on the back burner?

#### Architect Templates

**architect-intent-01 (Design Intent)**
> Hey [Name], I was looking at [project name/detail] — the way you handled [light/material/spatial sequence] is really compelling.
>
> I focus on architectural photography specifically because I think the design intent usually gets lost in standard real estate shoots. Would love to hear more about this project sometime.

**architect-publish-01 (Publication Angle)**
> Hey [Name], I noticed [project or award]. Have you submitted it to [ArchDaily/Dezeen/Canadian Architect/Western Living]?
>
> I've worked with [Sitelines/other firm] on publication-ready shoots — the editorial requirements are pretty specific. Is that something you've explored?

**architect-collab-01 (Collaboration)**
> Hey [Name], your work on [project] is great. I'm curious about [specific design decision — material choice, massing, site response].
>
> I shoot exclusively in the architectural space — always looking to connect with studios doing interesting work in the corridor. What are you working on right now?

#### Interior Designer Templates

**designer-credit-01 (Credit Attribution)**
> Hey [Name], saw your work on [project/space]. The [specific element — material palette, lighting, spatial composition] is beautiful.
>
> I find designers' contributions often get overshadowed in project photography — the builder or architect gets the spotlight. Do you find that's an issue when it comes to your portfolio?

**designer-content-01 (Content Pipeline)**
> Hey [Name], your feed is gorgeous. How do you handle photography for your projects — do you coordinate with the builder's photographer or arrange your own?
>
> I ask because I work with a few designers in the area and the cost-share model has been a game changer for them.

**designer-awards-01 (Awards)**
> Hey [Name], is [project] entering Western Living DOTY or IDIBC Awards this year? It should be.
>
> The photography requirements for awards are pretty specific — I've helped a few designers nail their submissions. What's your timeline looking like?

#### Trades Templates

**trades-invisible-01 (Invisible Craft)**
> Hey [Name], I was looking at [specific product/project]. Your [windows/millwork/fabrication/etc.] in that context is stunning.
>
> I find that trades companies have this problem where their work looks incredible installed but their portfolio is all warehouse shots. Is that something you deal with?

---

## Channel 2: Comment-to-DM Funnel (ManyChat)

### The Lead Magnet: Free Personalized Marketing Plan

The comment-to-DM funnel drives toward one thing: a **free, personalized marketing plan** for the prospect's business. This is a 17-section, fully custom analysis generated from their website — covering their online presence, content strategy, awards positioning, competitor landscape, and a 6-month roadmap.

No photographer offers this. It positions Matt as a creative partner and marketing strategist, not a vendor with a camera. The plan naturally reveals every gap that professional photography would fill — without ever making a direct pitch.

**Why it works:**
- It's genuinely valuable. Even if they never hire you, the plan helps their business.
- It takes you ~5 minutes to generate (fully automated pipeline), but feels like hours of consulting.
- It creates reciprocity. They feel like they owe you a conversation.
- It demonstrates expertise. You're not selling photography — you're diagnosing their marketing.
- It surfaces the photography need organically. Every gap the plan identifies points back to visual content.

### Setup (One-Time)

Three automated funnels, each triggered by a keyword comment. All roads lead to the marketing plan.

#### Funnel 1: "PLAN" — Free Marketing Plan
**Trigger:** User comments "PLAN" on an educational post or case study
**ManyChat flow:**
1. Instant DM: "Hey! I'd love to put one together for you. Quick question — are you a builder, architect, or designer?"
2. Wait for reply → Tag by ICP type
3. "Perfect. Drop your website URL and I'll build out a custom marketing plan for your firm — completely free."
4. Wait for URL → Store in Website URL custom field
5. "Got it. I'll have the plan ready within 24 hours and send it right here. What's the best name for your company?"
6. Store Company Name → Tag as `plan-requested` → Notify Matt
7. **Matt runs:** `python3 tools/warm_lead_plan.py --company "X" --owner "Y" --website "Z"`
8. Plan generated → ManyChat sends plan link → Tag as `plan-sent`

#### Funnel 2: "AUDIT" — Quick Visual Audit
**Trigger:** User comments "AUDIT" on a before/after or portfolio post
**ManyChat flow:**
1. Instant DM: "I'll take a look! Drop your website URL and I'll give you a quick audit of your visual presence — what's working and where the gaps are."
2. Wait for URL → Store in Website URL custom field
3. "Got it. Are you a builder, architect, or designer?"
4. Wait for reply → Tag by ICP type + `plan-requested` → Notify Matt
5. **Matt runs the full plan pipeline** (the "audit" is actually the marketing plan — they get more than they asked for)
6. Send plan link via DM → Tag as `plan-sent`

#### Funnel 3: "BOOK" — Discovery Call
**Trigger:** User comments "BOOK" on a CTA or testimonial post
**ManyChat flow:**
1. Instant DM: "Here's my calendar to grab 15 minutes: mattanthonyphoto.com/discovery-call. Before we chat — what kind of project are you working on?"
2. Wait for reply → Tag as `engaged-booking` (hottest intent) → Notify Matt

### Content Posts That Drive Comments

Each week, at least one post should include a comment-to-DM CTA:

- **Reels (case study or educational):** "Comment PLAN and I'll build a free marketing plan for your firm"
- **Carousels (before/after or audit-style):** Last slide: "Comment AUDIT and I'll review your online presence for free"
- **Testimonial or CTA posts:** "Comment BOOK to grab 15 minutes on my calendar"

**The hook that works best:** Show the Balmoral marketing plan as an example (blur sensitive details). "I built this for a builder in Squamish. Comment PLAN and I'll make one for your firm — free."

### ManyChat Configuration

**Keyword triggers to set up in ManyChat:**
| Keyword | Flow | Tag |
|---------|------|-----|
| PLAN | Marketing Plan Delivery | plan-requested |
| AUDIT | Visual Audit (delivers full plan) | plan-requested |
| BOOK | Discovery Call Booking | engaged-booking |

**Custom fields (already configured):**
| Field | ID | Purpose |
|-------|-----|---------|
| Website URL | 14418207 | Captured in DM flow |
| Company Name | 14418208 | Captured in DM flow |
| Plan URL | 14418209 | Set after plan is generated |
| Plan Status | 14418210 | requested / generating / sent |

**Tags (already configured):**
| Tag | ID | Purpose |
|-----|-----|---------|
| builder-lead | 84044070 | ICP identification |
| plan-requested | 84044071 | Entered the funnel |
| plan-sent | 84044072 | Plan delivered |
| replied | 84044073 | Responded after plan delivery |
| converted | 84044074 | Booked a call or hired |

### Plan Generation Pipeline

When a prospect provides their website URL via ManyChat:

```bash
python3 tools/warm_lead_plan.py \
  --company "Company Name" --owner "Contact Name" \
  --website "https://their-site.com" --email "" \
  --location "City BC"
```

This automatically:
1. Crawls their website (site audit)
2. Builds a personalized marketing plan config
3. Generates a full HTML plan (17 sections)
4. Publishes to GitHub Pages
5. Updates the Pipeline tab
6. Returns a URL to send back via DM

**Turnaround target:** Under 24 hours. Most can be generated in 5-10 minutes.

---

## Pipeline Integration

### When a prospect moves to "Replied" or "In Conversation":
1. Add them to the Unified Sales Pipeline:
   - Source: "Instagram"
   - Stage: "Engaged"
   - Fill Company, Contact, ICP, Email (if provided)
2. Mark `Pipeline Synced = Yes` in the tracker

### When a prospect is ready for a marketing plan:
```bash
python3 tools/warm_lead_plan.py \
  --company "Company Name" --owner "Contact Name" \
  --website "https://their-site.com" --email "email@company.com" \
  --location "City BC"
```
Then send the plan URL via Instagram DM.

### When a prospect books a discovery call:
- Update Pipeline stage to "Discovery Booked"
- Update tracker status to "Call Booked"

---

## Prospect Sourcing

### Where to find prospects to add:

1. **Cold email input sheet** — All 11 ICP tabs have company names and websites. Cross-reference with Instagram search.
2. **Instagram Explore** — Search location tags (Squamish, Whistler, Vancouver) + hashtags (#bcbuilder, #vancouverarchitect, #interiordesignvancouver)
3. **Competitor followers** — Check who follows/engages with @ema_peter_photography, @andrew.fyfe, @kyle_r_graham
4. **Award nominees** — Georgie Awards, AIBC Awards, Western Living DOTY nominee lists
5. **Client followers** — Who follows @balmoralconstruction, @summerhillfinehomes, @sitelines_architecture
6. **Tagged accounts** — When you post a project and tag collaborators, check who engages with those tags

### Adding prospects:
```bash
python3 tools/ig_dm_tracker.py add-prospect \
  --company "Company Name" \
  --contact "Owner Name" \
  --ig-handle "their_handle" \
  --icp-type "Builder" \
  --region "Sea-to-Sky" \
  --website "https://their-site.com" \
  --source "Cold email list"
```

---

## Metrics & Targets

| Metric | Weekly Target | Monthly Target |
|--------|--------------|----------------|
| Warm-ups started | 10 | 40 |
| DMs sent | 15-20 | 60-80 |
| Reply rate | 15%+ | 15%+ |
| Conversations started | 3-4 | 12-15 |
| Calls booked | 1 | 3-4 |
| Plans sent | 1 | 3-4 |

---

## Edge Cases

**Prospect has no Instagram:**
- Skip DM outreach. They may still be in the cold email pipeline.

**Prospect follows you but hasn't engaged:**
- Start with warm-up engagement on their content. Higher chance of a reply.

**They reply but go cold:**
- Wait 7 days, then share a relevant piece of content (case study, journal article) with no ask.
- If still no reply after 14 days, mark as "No Response" and move on.

**They're already in the cold email pipeline:**
- Check before DMing. If they've received an email in the last 7 days, wait. Don't hit them from two channels simultaneously.
- If they opened the email 3+ times but didn't reply, an Instagram DM is a great follow-up (different channel, warmer medium).

**Competitor follows your approach:**
- Don't DM prospects who work exclusively with a competitor. Focus on those who are underserved or between photographers.

---

## Tools Reference

| Command | What it does |
|---------|-------------|
| `python3 tools/ig_dm_tracker.py create-sheet` | Create the tracker Google Sheet |
| `python3 tools/ig_dm_tracker.py add-prospect --company X --contact Y --ig-handle Z --icp-type Builder` | Add a prospect |
| `python3 tools/ig_dm_tracker.py update-status "@handle" --status "Warming"` | Update status |
| `python3 tools/ig_dm_tracker.py log-dm "@handle" --template "builder-craft-01"` | Log a sent DM |
| `python3 tools/ig_dm_tracker.py get-queue` | Get today's outreach queue |
| `python3 tools/ig_dm_tracker.py get-follow-ups` | Get follow-ups due today |
| `python3 tools/ig_dm_tracker.py stats` | Show outreach stats |
