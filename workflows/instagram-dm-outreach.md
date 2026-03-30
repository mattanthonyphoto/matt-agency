# Instagram DM Outreach System

## Trigger
Matt says: "run my IG outreach", "DM queue", "who should I DM today", "prep my DMs", or "Instagram prospecting"

---

## Architecture

Four-layer system. Claude handles research and writing. Matt handles sending.

| Layer | Who | What | Time |
|-------|-----|------|------|
| **1. Daily Prep** | Claude | Research prospects, build briefs, queue in sheet | 2-5 min (Claude) |
| **2. Matt Engages + DMs** | Matt | Warm-up engagement + write DMs from briefs in his own voice | 15 min |
| **3. Comment Funnel** | ManyChat | Auto-respond to comment triggers, collect info, notify Matt | Automated |
| **4. Plan Closer** | Claude | Generate full marketing plan for warm, qualified prospects | On demand |

### ICP Channel Strategy

Instagram DMs are NOT the right channel for every ICP. But the research shows some exceptions:

| ICP | Primary Channel | Instagram DM? | Why |
|-----|----------------|---------------|-----|
| **Interior Designers** | Instagram DM | YES — primary target | They live on IG, check DMs, respond to collaboration messages |
| **Residential Builders** | Email (Instantly) | Secondary — supplement only | Use IG DMs for email openers who didn't reply (3+ opens, no response) |
| **Builder Spouse/OM** | Instagram DM + Email | YES — high priority | The marketing decision-maker in $1M-$5M builder businesses. They run the company IG, check DMs, and are already frustrated by bad photos. See `business/sales/spouse-office-manager-channel.md` |
| **Sea-to-Sky Architects** | Instagram DM + Email | YES — for local firms with active IG | STARK (25K followers), McLintock, AKA are all local and active on IG. Use DMs for relationship-building, not pitching. See `business/sales/architect-referral-flywheel.md` |
| **Vancouver Architects** | Email + LinkedIn | NO | Professional outreach = LinkedIn/email. Ema Peter dominates this space. |
| **Trades** | Email | NO | B2B manufacturing, phone/email operations |

**Volume:** 5 prospects per week (2 designers, 1-2 builders/spouse-OMs, 1 local architect). Not 20.
**Warm-up:** 7-10 days of genuine engagement before the first DM. Not 2 days.
**Voice notes:** Use 15-30 second voice notes for follow-ups (30-40% higher reply rate than text).

### Georgie Awards Warm-Up Track (April-May 2026)

During April-May, add a parallel track for Georgie finalist builders:
- Follow finalist accounts NOW, engage with specific project comments for 2-3 weeks
- At the gala (May 23), your name will already be familiar
- Post-gala (May 24-25), DM follow-ups feel like continuing a conversation, not cold outreach
- See full playbook: `business/sales/georgie-playbook-2026.md`

### Builder Entry Point: Construction Progress

When DMing builders, the entry point should NOT be a $3,500 completed project shoot. Lead with construction progress photography ($1K-$1.5K/visit):
- Lower commitment, immediate value (client updates, social content)
- Monthly visits create dependency over 8-18 months
- Locks in the completed shoot when the project finishes
- See `business/sales/retainer-pitch-builders.md` for the trust ladder

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

### Step 3: Write the DM

Claude writes a ready-to-send DM for each prospect. Matt copy-pastes it.

**The DM must sound like genuine curiosity, not a photographer looking for work.**

Rules:
- Under 80 words. Shorter is better. Two sentences is ideal.
- Ask a specific question about THEIR work that they'd enjoy answering
- Do NOT mention photography, your services, portfolio, or what you do
- Do NOT say "I'd love to collaborate" or "let's connect" or any variation
- Reference a verified, specific detail (project name, material, technique)
- Every detail in the DM must be confirmed from their website or a public source — never guess
- End with a question mark
- Sound like a peer who noticed something interesting, not a vendor prospecting

**What a good DM looks like:**

> That Skeena kitchen — did you run the walnut on your own CNC or was that outsourced? The grain matching across those panels is next level.

> The Conifers hitting Step 5 in Sechelt is impressive. How are you handling the embodied carbon tracking — is there a tool you like or is it still manual?

> The Japandia project is stunning. What inspired the Japandi direction in a North Shore context? I keep seeing it in Whistler but not down here.

**What a bad DM looks like:**

> Hey, I'm an architectural photographer in Squamish. I love your work and would love to chat about photographing your next project.

> Your projects are incredible. Have you thought about professional photography for your portfolio?

The photography conversation happens naturally later — after they reply, after rapport exists. Not in the opener.

### Step 4: Store in the tracker

```bash
python3 tools/ig_dm_tracker.py prep-dm "@handle" \
  --message "The ready-to-send DM" \
  --angle "craft-curiosity" \
  --notes "Research: [key details about the prospect, why this hook was chosen]"
```

### Step 5: Present the queue to Matt

```
## Today's IG Outreach — [Date]

### Ready to Send (copy-paste these)

1. @daintreedesignstudio — Joel Trigg (Designer, Squamish)
   Day 8 of warm-up. Ready to DM.

   > That Skeena kitchen — did you guys run the walnut on your own
   > CNC or outsource it? The grain matching is next level.

2. @gnar.inc — Eddie Dearden (Designer, Whistler)
   Day 7 of warm-up. Ready to DM.

   > The Conifers hitting Step 5 in Sechelt is impressive. How are
   > you handling embodied carbon tracking — is there a tool you
   > like or is it still mostly manual?

### Still Warming (keep engaging)
- @bryn.maryanna.interiors — Day 4 of 7. Like a post today.
- @haslerhomesltd — Day 3 of 7. React to their Story.

### Follow-Ups Due
- @handle — Day 4, no reply. Voice note:
  "Hey [name], saw your [recent post] — [genuine 15-sec reaction]"

### Stats
- X in pipeline / X warming / X DMs sent this week / X replies
```

Matt opens phone, copies messages, sends. 5 minutes.

### Step 6: After Matt sends

Matt tells Claude: "sent the DMs" or "sent to @handle1 and @handle2"

Claude logs them:
```bash
python3 tools/ig_dm_tracker.py log-dm "@handle" --message "the DM that was sent"
```

### Step 7: Follow-ups

For prospects needing follow-up, Claude writes:
- **Day 4 voice note script** — 15-30 second voice note referencing something new they posted. Matt records and sends.
- **Day 10 text** — Share something valuable (article, case study, a project that reminded you of theirs). Zero ask.
- **Day 17+ no reply** — Mark as No Response.

Follow-ups must also never mention photography. Stay curious about their work.

---

## Layer 2: Matt's 5 Minutes (Manual)

### Daily warm-up (while scrolling IG naturally)
For each prospect in the warm-up phase — do this as part of your normal IG use, not as a task:
1. Watch their Stories (they see who views)
2. Like 1-2 posts when they show up in your feed
3. Once during the week, leave one genuine comment on a project post

### Sending DMs (when Claude says "Ready to Send")
1. Open the queue Claude presented
2. Copy-paste each DM
3. Send from the Instagram app
4. Tell Claude: "sent"

### When they reply
1. Continue the conversation naturally. Stay curious about their work.
2. If they ask what you do, be honest and brief.
3. After 2-3 exchanges, if there's mutual interest: "Would love to grab a coffee" or "I'd love to see that project in person"
4. If qualified → Claude generates a marketing plan (Layer 4) as a gift
5. If they want a call → mattanthonyphoto.com/discovery-call

### Voice note follow-ups
When Claude provides a voice note script for a follow-up:
1. Record a 15-30 second voice note in the Instagram DM thread
2. Keep it casual — like you're talking to someone you've met before
3. Reference something they posted recently

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
| Designer in cold email list | IG DM is the better channel. Prioritize IG over email. |
| Builder cold email sent in last 7 days | SKIP Instagram DM — don't double-tap |
| Builder email opened 3+ times, no reply | HIGH PRIORITY for IG DM — different channel breaks through |
| Architect | Do NOT DM on Instagram. Keep on email + LinkedIn only. |
| Email reply went cold | Warm up on IG for 7 days, then DM with fresh angle |
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
| New prospects researched (Claude) | 5 | 20 |
| Research briefs delivered | 5 | 20 |
| DMs sent (Matt) | 3-5 | 12-20 |
| Voice note follow-ups | 2-3 | 8-12 |
| Reply rate | 15-20%+ | 15-20%+ |
| Conversations started | 1-2 | 4-8 |
| Plans generated | 1 | 2-4 |
| Calls booked | 1 | 2-4 |

**Expected conversion funnel (monthly):**
20 prospects researched → 12-20 DMs sent → 3-4 replies → 2 real conversations → 1 plan sent → 1 call booked

**Why lower volume works:** Quality over quantity. 5 deeply researched prospects with genuine 7-day warm-up and a DM written in Matt's voice will outperform 50 spray-and-pray messages. The research shows personalized warm outreach gets 15-20% reply rates vs 1-5% for cold DMs.

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
