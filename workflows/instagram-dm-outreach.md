# Instagram DM Outreach System

## Trigger
Matt says: "run my IG outreach", "DM queue", "who should I DM today", "prep my DMs", or "Instagram prospecting"

---

## Architecture

Four-layer system. Claude handles research and writing. Matt handles sending.

| Layer | Who | What | Time |
|-------|-----|------|------|
| **1. Daily Prep** | Claude | Research prospects, write personalized DMs, queue in sheet | 2-5 min (Claude) |
| **2. Matt Sends** | Matt | Open phone, copy-paste pre-written DMs, send | 10-15 min |
| **3. Comment Funnel** | ManyChat | Auto-respond to comment triggers, collect info, notify Matt | Automated |
| **4. Plan Closer** | Claude | Generate full marketing plan for warm, qualified prospects | On demand |

---

## Layer 1: Daily Prep (Claude)

This is the engine. When Matt says "run my IG outreach", follow these steps exactly.

### Step 1: Pull the queue

```bash
python3 tools/ig_dm_tracker.py batch-prep
```

This returns three lists:
- `needs_dm_written` — Prospects with no message prepped yet (Claude writes these)
- `ready_to_send` — Prospects with pre-written DMs ready for Matt to copy-paste
- `needs_follow_up` — Prospects due for follow-up messages

### Step 2: Research each prospect that needs a DM

For every prospect in `needs_dm_written`, do ALL of the following:

1. **Visit their website** — Use WebFetch on their website URL. Note:
   - What kind of projects they do (residential, commercial, luxury, custom)
   - Any featured projects with names or locations
   - Their service area
   - Any awards or publications mentioned
   - Their team size and key people
   - Quality of their current photography (this is the gap you're exploiting)

2. **Search for recent activity** — Use WebSearch for `"[company name]" + [city]`. Note:
   - Recent projects completed or in progress
   - Award wins or nominations
   - News coverage or press mentions
   - Social media presence

3. **Check cold email overlap** — If the prospect has an email, check if they're in the Instantly pipeline. If they've received a cold email in the last 7 days, SKIP them (don't double-tap). If they've opened an email 3+ times with no reply, they're a HIGH priority for IG DM (different channel breaks through).

4. **Find the hook** — Identify the single most specific, personal thing to reference:
   - A specific project name + detail ("the timber frame on the Whistler build")
   - An award they won or could enter ("that's Georgie-worthy")
   - A material or design choice visible in their work
   - A recent completion or milestone

### Step 3: Write personalized DMs

For each researched prospect, write a completely unique DM. **Do not use templates.** Each message must:

- Open with something specific to THEM (project name, material, design choice)
- Be under 120 words
- End with a question (not a pitch)
- Contain zero links
- Sound like a human who genuinely noticed their work, not a salesperson
- Use ICP-appropriate language:
  - **Builders:** "craft", "document", "portfolio", "legacy", "Georgie"
  - **Architects:** "design intent", "material", "light", "spatial", "publication"
  - **Designers:** "materiality", "palette", "curation", "credit", "cost-share"

**DM angle selection by ICP:**

| ICP | Best Angles | Trigger Moments |
|-----|------------|-----------------|
| Builder | Craft recognition, awards prep, legacy | Post-completion, pre-Georgie (May), post-Georgie gala |
| Architect | Design intent, publication, collaboration | Award deadlines, project completions, new website |
| Designer | Credit attribution, cost-share, content pipeline | Pre-WL DOTY, pre-IDIBC, post-project install |
| Trades | Invisible craft, in-situ vs warehouse | After seeing their work in a completed project |

### Step 4: Store prepped DMs in the tracker

For each DM written:

```bash
python3 tools/ig_dm_tracker.py prep-dm "@handle" \
  --message "The full personalized DM text" \
  --angle "craft-recognition" \
  --notes "Key research: Built the Cypress Point residence in Whistler, won Georgie 2024 for Best Custom Home. Current website photos are iPhone quality. High-value target."
```

### Step 5: Write follow-up messages

For each prospect in `needs_follow_up`:

- **First follow-up (day 4):** Different angle from the original DM. Never say "just following up." Share something relevant — a case study link, a journal article, a project that's similar to theirs. End with a softer question.
- **Second follow-up (day 9):** Pure value, zero ask. Share something useful with no CTA. "Saw this and thought of your [project]."
- **Final follow-up (day 14+):** Mark as "No Response" if still silent.

Store follow-ups the same way:
```bash
python3 tools/ig_dm_tracker.py prep-dm "@handle" \
  --message "The follow-up message" \
  --angle "follow-up-1"
```

### Step 6: Present the queue to Matt

After all research and writing is done, present a clean summary:

```
## Today's IG Outreach Queue

### Ready to Send (copy-paste these)
1. @handle — Company Name (Builder, Sea-to-Sky)
   > The full DM message here

2. @handle — Company Name (Architect, Vancouver)
   > The full DM message here

### Warm-Up Today (engage with their content, DM in 2 days)
1. @handle — Company Name — like 2-3 posts, react to Story

### Follow-Ups Due
1. @handle — Company Name — send follow-up message:
   > The follow-up message here

### Stats
- X prospects in pipeline
- X DMs sent this week
- X replies received
```

Matt opens his phone and sends. No research, no writing, no thinking about what to say.

---

## Layer 2: Matt Sends (Manual, 10-15 min)

### Sending DMs
1. Open Instagram on phone
2. For each "Ready to Send" prospect:
   - Go to their profile
   - Copy-paste the pre-written DM from the queue
   - Send
3. Tell Claude: "sent all DMs" or "sent DMs to @handle1, @handle2"
4. Claude logs them:
```bash
python3 tools/ig_dm_tracker.py log-dm "@handle" --message "the message"
```

### Warm-up engagement
For each "Warm-Up Today" prospect:
1. Like 2-3 of their recent posts (not all at once)
2. React to their most recent Story
3. If they posted a project, leave a genuine comment about a specific detail
4. Don't DM them yet — they'll be in "Ready to Send" in 2 days

### Handling replies
When someone replies:
1. Tell Claude the reply context
2. Claude updates the tracker and advises on next move
3. If qualified → Claude generates a marketing plan (Layer 4)
4. If they want a call → Send discovery link (mattanthonyphoto.com/discovery-call)

**Rules:**
- Send from the Instagram app (not desktop)
- Best times: Tuesday-Thursday, 9-11am or 1-3pm Pacific
- Max 20 DMs per day (stay under Instagram's radar)
- Never warm up and DM on the same day

---

## Layer 3: Comment-to-DM Funnel (ManyChat)

Light and fast. No heavy plan generation for random commenters.

### Trigger: AUDIT
**Post type:** Before/after Reel, portfolio comparison, case study carousel
**CTA on post:** "Comment AUDIT and I'll review your online presence for free"
**ManyChat flow:**
1. Instant DM: "Hey! I'd love to take a look. Are you a builder, architect, or designer?"
2. Wait for reply → Tag by ICP type
3. "Here's what I put together for a builder in Squamish — [Balmoral case study link]. Want me to do one for your firm?"
4. If yes → "Drop your website URL and I'll build it out."
5. Store URL → Tag as `plan-requested` → Notify Matt → Go to Layer 4

### Trigger: BOOK
**Post type:** Testimonial, CTA, strong case study
**CTA on post:** "Comment BOOK to grab 15 minutes on my calendar"
**ManyChat flow:**
1. Instant DM: "Here's my calendar: mattanthonyphoto.com/discovery-call — what kind of project are you working on?"
2. Wait for reply → Tag as `engaged-booking` → Notify Matt

### ManyChat Config

**Keyword triggers:**
| Keyword | Flow | Tag |
|---------|------|-----|
| AUDIT | Visual Audit Funnel | plan-requested |
| BOOK | Discovery Call Booking | engaged-booking |

**Custom fields (already configured):**
| Field | ID |
|-------|-----|
| Website URL | 14418207 |
| Company Name | 14418208 |
| Plan URL | 14418209 |
| Plan Status | 14418210 |

**Tags (already configured):**
| Tag | ID |
|-----|-----|
| builder-lead | 84044070 |
| plan-requested | 84044071 |
| plan-sent | 84044072 |
| replied | 84044073 |
| converted | 84044074 |

---

## Layer 4: Plan Closer (On Demand)

The full marketing plan is the precision weapon. Only deploy for qualified, warm prospects.

### When to generate a plan:
- Prospect has **replied** to a DM and shown genuine interest
- Prospect came through comment funnel and **requested** one
- Prospect is a **high-value target** (builders with $2M+ projects, architects with award-winning work)
- NEVER for cold prospects who haven't engaged

### How to generate:
```bash
python3 tools/warm_lead_plan.py \
  --company "Company Name" --owner "Contact Name" \
  --website "https://their-site.com" --email "email@company.com" \
  --location "City BC"
```

### Delivery:
Send the plan link via Instagram DM with a short message:
> "Put this together for you — [plan URL]. It covers your online presence, content strategy, and some ideas for awards positioning. Happy to walk through it on a quick call if anything stands out."

### After delivery:
- Update tracker: `update-status "@handle" --status "Plan Sent"`
- Set follow-up for 3 days: "Did you get a chance to look at the plan?"
- If they reply → Discovery call → Pipeline
- If no reply after 7 days → One more touch, then move on

---

## Prospect Sourcing

### Priority sources (Claude searches these):
1. **Cold email input sheet** — 2,251 leads across 11 ICP tabs. Cross-reference with IG search.
2. **Award nominees** — Georgie Awards, AIBC Awards, Western Living DOTY nominee lists
3. **Client followers** — Who follows @balmoralconstruction, @summerhillfinehomes, @sitelines_architecture
4. **Competitor followers** — Who engages with @ema_peter_photography, @andrew.fyfe, @kyle_r_graham
5. **Instagram Explore** — Location tags (Squamish, Whistler, Vancouver) + ICP hashtags
6. **Tagged accounts** — Who engages when project collaborators are tagged

### Adding new prospects:
```bash
python3 tools/ig_dm_tracker.py add-prospect \
  --company "Company Name" --contact "Owner Name" \
  --ig-handle "their_handle" --icp-type "Builder" \
  --region "Sea-to-Sky" --website "https://their-site.com" \
  --source "Cold email list"
```

---

## Multi-Channel Coordination

| Scenario | Action |
|----------|--------|
| Cold email sent in last 7 days | SKIP Instagram DM — don't double-tap |
| Cold email opened 3+ times, no reply | HIGH PRIORITY for IG DM — different channel breaks through |
| Email reply went cold | Warm up on IG, then re-engage via DM |
| IG DM reply, wants more info | Send marketing plan via email or DM |
| Prospect in both channels | Track in IG DM Tracker with Source = "Cold email list" |

---

## Pipeline Integration

### When a prospect replies:
1. Update tracker: `update-status "@handle" --status "Replied"`
2. Add to Unified Sales Pipeline (Source: Instagram, Stage: Engaged)
3. Mark `Pipeline Synced = Yes` in tracker

### When a prospect books a call:
1. Update tracker: `update-status "@handle" --status "Call Booked"`
2. Update Pipeline stage to "Discovery Booked"

### When a prospect converts:
1. Update tracker: `update-status "@handle" --status "Won"`
2. Update Pipeline stage accordingly

---

## Metrics & Targets

| Metric | Weekly | Monthly |
|--------|--------|---------|
| Prospects researched (Claude) | 15-20 | 60-80 |
| DMs prepped (Claude) | 15-20 | 60-80 |
| DMs sent (Matt) | 15-20 | 60-80 |
| Reply rate | 15%+ | 15%+ |
| Conversations started | 3-4 | 12-15 |
| Plans generated | 1-2 | 3-5 |
| Calls booked | 1 | 3-4 |

Weekly stats:
```bash
python3 tools/ig_dm_tracker.py stats
```

---

## Tools Reference

| Command | What it does |
|---------|-------------|
| `ig_dm_tracker.py create-sheet` | Create the tracker Google Sheet |
| `ig_dm_tracker.py add-prospect` | Add a prospect to the tracker |
| `ig_dm_tracker.py batch-prep` | Get prospects needing DMs written (Claude's starting point) |
| `ig_dm_tracker.py prep-dm "@handle" --message "DM text"` | Store a pre-written DM |
| `ig_dm_tracker.py update-status "@handle" --status "X"` | Update prospect status |
| `ig_dm_tracker.py log-dm "@handle" --message "X"` | Log a sent DM |
| `ig_dm_tracker.py get-queue` | Get today's full outreach queue |
| `ig_dm_tracker.py get-follow-ups` | Get follow-ups due today |
| `ig_dm_tracker.py stats` | Show outreach stats |
| `warm_lead_plan.py --company X --website Y` | Generate a marketing plan (Layer 4) |

---

## Edge Cases

**Prospect has no Instagram:**
Skip. They stay in the cold email pipeline only.

**Prospect follows you but hasn't engaged:**
Higher chance of reply. Start warm-up, DM in 2 days.

**They reply but go cold:**
Wait 7 days, share value with no ask. If still silent after 14 days, mark No Response.

**They're already in cold email pipeline:**
Check before DMing. 7-day buffer between channels. Email openers who didn't reply = high-priority DM targets.

**Website is down or garbage:**
Still DM them, but adjust the angle away from "I reviewed your online presence" toward craft recognition or awards.

**They work with a competitor:**
Skip. Focus on underserved prospects or those between photographers.
