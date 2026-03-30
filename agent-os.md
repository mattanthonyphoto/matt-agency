# Matt Anthony — Agent OS

> **Last updated:** March 28, 2026
> **Owner:** Matt Anthony | Architectural Photographer | Squamish, BC
> **System:** WAT Framework (Workflows, Agents, Tools)
> **Delivery channel:** Telegram (@mattbriefing_bot)
> **Revenue target:** $125,000 (2026)

---

## Table of Contents

1. [Organization Map](#organization-map)
2. [System Architecture](#system-architecture)
3. [The WAT Framework](#the-wat-framework)
4. [Agent Fleet — 8 Agents, 23 Cron Jobs](#agent-fleet)
5. [Daily Timeline](#daily-timeline)
6. [Workflows — 14 SOPs](#workflows)
7. [Tools — 30+ Scripts](#tools)
8. [Integrations & API Stack](#integrations)
9. [Cold Email Pipeline](#cold-email-pipeline)
10. [Social Media System](#social-media-system)
11. [Proposal & Pitch System](#proposal-system)
12. [Production & Delivery](#production-system)
13. [Finance & Accounting](#finance-system)
14. [Website & SEO](#website-seo)
15. [Sales Playbooks & ICP Research](#sales-playbooks)
16. [Business Context](#business-context)
17. [Feedback & Operating Rules](#feedback-rules)
18. [Reference Config (API Keys, IDs, Sheets)](#reference-config)
19. [Known Issues & Constraints](#known-issues)

---

## 1. Organization Map {#organization-map}

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          MATT ANTHONY — AGENT OS                                │
│                     Architectural Photography Business                           │
│                        $125K Target · Squamish, BC                              │
└─────────────────────────────┬───────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────────┐
          │                   │                       │
    ┌─────▼─────┐     ┌──────▼──────┐        ┌───────▼───────┐
    │ WORKFLOWS │     │   AGENTS    │        │    TOOLS      │
    │ (14 SOPs) │     │ (8 Scripts) │        │ (30+ Scripts) │
    │ Markdown  │     │ Python/Cron │        │ Python/Node   │
    └─────┬─────┘     └──────┬──────┘        └───────┬───────┘
          │                  │                       │
          │    ┌─────────────┼─────────────┐         │
          │    │             │             │         │
          │    ▼             ▼             ▼         │
          │  INTELLIGENCE  OPERATIONS   STRATEGY     │
          │    │             │             │         │
          │    ▼             ▼             ▼         │
          └────────────► TELEGRAM ◄──────────────────┘
                        (Delivery)
```

### Agent Fleet — Organization Chart

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           AGENT FLEET (8 Agents)                             │
│                     Local Mac Cron · Telegram Delivery                        │
│                          agent_utils.py (shared)                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─── INTELLIGENCE LAYER ──────────────────────────────────────────────┐     │
│  │                                                                     │     │
│  │  ☀️  MORNING COMMAND          Daily 7am                              │     │
│  │     morning_command.py        Calendar + Email + Pipeline + Actions  │     │
│  │                                                                     │     │
│  │  📊 SUNDAY COMMAND            Sunday 7pm                             │     │
│  │     sunday_command.py         Revenue + Pipeline + Cash + Week Ahead │     │
│  │                                                                     │     │
│  │  📈 THE STRATEGIST            Mon/Thu + 1st/15th + Sunday            │     │
│  │     the_strategist.py         Campaigns · Win/Loss · Competitors ·   │     │
│  │     (4 modes)                 Attribution                            │     │
│  │                                                                     │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  ┌─── SALES & OUTREACH LAYER ──────────────────────────────────────────┐     │
│  │                                                                     │     │
│  │  📨 REPLY CLASSIFIER          Every 2hrs (8am-6pm)                   │     │
│  │     reply_classifier.py       Instantly replies → Classify → GHL     │     │
│  │                                                                     │     │
│  │  📱 THE OPERATOR              Daily/Tue-Thu/MWF/Sat/Wed              │     │
│  │     the_operator.py           DM Prep · Follow-Ups · Content ·       │     │
│  │     (5 modes)                 Leads · Reviews                        │     │
│  │                                                                     │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  ┌─── PRODUCTION LAYER ───────────────────────────────────────────────┐      │
│  │                                                                     │     │
│  │  📸 THE PRODUCER              Daily + Mon/Thu + Fri                   │     │
│  │     the_producer.py           Shoot Prep · Editor Handoff ·          │     │
│  │     (4 modes)                 Delivery Tracker · Cost-Share           │     │
│  │                                                                     │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  ┌─── FINANCE LAYER ──────────────────────────────────────────────────┐      │
│  │                                                                     │     │
│  │  💰 THE ACCOUNTANT            Wed/Fri + Mon + 1st/15th               │     │
│  │     the_accountant.py         Invoices · Expenses · Tax Reminders    │     │
│  │     (3 modes)                                                        │     │
│  │                                                                     │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  ┌─── INFRASTRUCTURE LAYER ────────────────────────────────────────────┐     │
│  │                                                                     │     │
│  │  👁️  THE WATCHDOG              Every 4hrs + Daily + 1st of month      │     │
│  │     the_watchdog.py           Health · GBP · Domains · Retainer      │     │
│  │     (4 modes)                                                        │     │
│  │                                                                     │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Integration Map

```
┌────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL INTEGRATIONS                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  CRM & PIPELINE              OUTREACH                                  │
│  ┌──────────────┐            ┌──────────────┐                          │
│  │ GoHighLevel  │◄──────────►│  Instantly    │                         │
│  │ (GHL)        │            │  Cold Email   │                         │
│  │ Pipeline,    │            │  3 Campaigns  │                         │
│  │ Contacts,    │            │  2 Domains    │                         │
│  │ Invoicing    │            └──────┬───────┘                          │
│  └──────┬───────┘                   │                                  │
│         │                    ┌──────▼───────┐                          │
│         │                    │   Icypeas    │                          │
│         │                    │   Email      │                          │
│         │                    │   Verify     │                          │
│         │                    └──────────────┘                          │
│         │                                                              │
│  COMMS & CALENDAR            CONTENT & SOCIAL                          │
│  ┌──────────────┐            ┌──────────────┐                          │
│  │ Gmail        │            │   Postiz     │                          │
│  │ (OAuth)      │            │   (MCP)      │                         │
│  │ Search,      │            │   IG, LI,    │                         │
│  │ Drafts       │            │   Pinterest  │                         │
│  └──────────────┘            └──────────────┘                          │
│  ┌──────────────┐            ┌──────────────┐                          │
│  │ Google Cal   │            │  Remotion    │                          │
│  │ (OAuth)      │            │  Reel Gen    │                          │
│  │ Events       │            │  React/TS    │                          │
│  └──────────────┘            └──────────────┘                          │
│                                                                        │
│  AUTOMATION                  DELIVERY                                  │
│  ┌──────────────┐            ┌──────────────┐                          │
│  │ n8n          │            │  Telegram    │                          │
│  │ Self-hosted  │            │  Bot API     │                          │
│  │ 7 active     │            │  Primary     │                          │
│  │ workflows    │            │  Channel     │                          │
│  └──────────────┘            └──────────────┘                          │
│  ┌──────────────┐            ┌──────────────┐                          │
│  │ GitHub Pages │            │  ManyChat    │                         │
│  │ Proposals +  │            │  IG DM       │                         │
│  │ Mockups      │            │  Automation  │                         │
│  └──────────────┘            └──────────────┘                          │
│                                                                        │
│  DATA & STORAGE              WEBSITE                                   │
│  ┌──────────────┐            ┌──────────────┐                          │
│  │ Google       │            │ Squarespace  │                          │
│  │ Sheets       │            │ 75 pages     │                          │
│  │ (Finance,    │            │ mattanthony  │                         │
│  │  Content,    │            │ photo.com    │                         │
│  │  Leads)      │            └──────────────┘                          │
│  └──────────────┘            ┌──────────────┐                          │
│  ┌──────────────┐            │ Balmoral     │                         │
│  │ Notion       │            │ Construction │                         │
│  │ (Marketing   │            │ .com         │                         │
│  │  Database)   │            └──────────────┘                          │
│  └──────────────┘                                                      │
│                                                                        │
│  AI / LLM                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Claude Code  │  │ OpenRouter   │  │ Apify        │                  │
│  │ (Opus 4.6)   │  │ (n8n LLM)   │  │ Web Scraping │                 │
│  │ Orchestrator │  │              │  │              │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Map

```
                    LEAD GENERATION FLOW
                    ════════════════════

  Google Sheets          Instantly           Gmail
  (11 ICP tabs)    ───►  (3 campaigns)  ───► (replies)
  ~2,251 leads           Builders             │
       │                 Architects            │
       │                 Designers             ▼
       │                                  Reply Classifier
       │                                  (every 2hrs)
       ▼                                      │
  Cold Email Pipeline                         ▼
  (cold_email.py)                         GHL Pipeline
  Verify → Qualify →                      (contacts +
  Research → Write →                       opportunities)
  Export to Instantly                          │
                                              ▼
                                         Morning Command
                                         Sunday Command
                                         (intelligence)


                    CONTENT PRODUCTION FLOW
                    ═══════════════════════

  Completed Shoot
       │
       ▼
  Content Batching ──► 15-20 pieces
  (2.5 hrs/project)       │
       │              ┌────┴────────────────┐
       │              │         │           │
       ▼              ▼         ▼           ▼
  Content Calendar   IG      LinkedIn    Pinterest
  (Google Sheet)   4-5/wk    3-4/wk     23/wk
       │              │         │           │
       ▼              └────┬────┘           │
  The Operator             ▼               │
  (content mode)        Postiz ◄───────────┘
  MWF 6:30am           (scheduler)


                    SALES PIPELINE FLOW
                    ════════════════════

  Cold Email ──► Reply ──► GHL Contact ──► Discovery Call
       │                        │               │
  IG DM ──────► Warm Lead ──────┘               ▼
       │                                    Proposal
  Referral ───► Introduction ───────────► (GitHub Pages)
       │                                        │
  Website ────► Contact Form ───────────►      ▼
  (n8n)        (n8n webhook)             Project Booked
                                               │
                                               ▼
                                         Production
                                         (The Producer)
                                               │
                                               ▼
                                         Delivery + Invoice
                                         (The Accountant)
                                               │
                                               ▼
                                         Cost-Share
                                         (30% licensing)
                                               │
                                               ▼
                                         Review Request
                                         (The Operator)
```

---

## 2. System Architecture {#system-architecture}

### Core Principle

**Separate probabilistic AI (reasoning) from deterministic code (execution).** If each AI step is 90% accurate, five steps in a row drops to 59%. By offloading execution to tested Python scripts, the AI focuses on orchestration and decision-making where it excels.

### Three Layers

| Layer | What | Where | Role |
|-------|------|-------|------|
| **Workflows** | Markdown SOPs | `workflows/` | The instructions — what to do, which tools, expected outputs |
| **Agents** | Claude Code | Conversation | The decision-maker — reads workflows, runs tools, handles failures |
| **Tools** | Python/Node scripts | `tools/` | The execution — API calls, data transforms, file ops |

### Infrastructure

| Component | Details |
|-----------|---------|
| **Runtime** | Mac cron (local, not cloud) |
| **Delivery** | Telegram bot (@mattbriefing_bot) |
| **CRM** | GoHighLevel ($150/mo) |
| **Cold Email** | Instantly ($140/mo, 2 domains, 3 campaigns) |
| **Automation** | n8n self-hosted on Hostinger |
| **Website** | Squarespace (mattanthonyphoto.com, 75 pages) |
| **AI** | Claude Code (Opus 4.6), OpenRouter (n8n LLM calls) |
| **Social** | Postiz (free, self-hosted) via MCP |
| **Email Verify** | Icypeas (credit-based) |
| **Scraping** | Apify (n8n integration) |
| **Video** | Remotion (React/TypeScript reel generator) |
| **IG Automation** | ManyChat Pro |
| **Proposals** | GitHub Pages (matt-proposals repo) |

---

## 3. The WAT Framework {#the-wat-framework}

### How It Operates

1. **Look for existing tools first** — Check `tools/` before building anything new
2. **Learn and adapt when things fail** — Read the error, fix the script, retest, update the workflow
3. **Keep workflows current** — Evolve SOPs as you learn; don't create/overwrite without asking

### The Self-Improvement Loop

```
Identify what broke → Fix the tool → Verify → Update workflow → Move on
```

### File Structure

```
.tmp/           # Temporary files (scraped data, intermediate exports)
tools/          # Python scripts for deterministic execution
workflows/      # Markdown SOPs defining what to do and how
business/       # Sales, marketing, operations docs
clients/        # Client-specific project files
.env            # API keys (NEVER store secrets anywhere else)
.claude/        # Claude Code settings, memory, permissions
```

**Core rule:** Local files are for processing. Anything Matt needs to see lives in cloud services (Google Sheets, Telegram, Gmail drafts, GitHub Pages).

---

## 4. Agent Fleet — 8 Agents, 23 Cron Jobs {#agent-fleet}

All agents share `tools/agent_utils.py` which provides:
- `send_telegram(text)` — HTML messages, auto-splits at 4096 chars
- `ghl_get(endpoint, params)` — GoHighLevel API
- `instantly_get(endpoint, params)` — Instantly API
- `search_gmail(query, max_results)` — Gmail search
- `get_today_events()` / `get_week_events()` — Google Calendar
- `get_google_creds()` — OAuth token management

### Agent 1: Morning Command

| | |
|---|---|
| **Script** | `tools/morning_command.py` |
| **Schedule** | Daily 7:00 AM |
| **Purpose** | Full daily briefing — calendar, email, pipeline, campaigns, top 3 actions |
| **Delivery** | 2 Telegram messages |

**What it pulls:**
- Google Calendar: today's events
- Gmail: last 24hrs (excludes promo/social/updates)
- GHL Pipeline: all open opportunities with deal aging (red 3+, yellow 1-3, green fresh)
- Instantly: campaign status (sent, opened, replied, bounced)
- Unsent Gmail drafts

**Output:** Top 3 prioritized actions weighted by revenue impact.

---

### Agent 2: Reply Classifier

| | |
|---|---|
| **Script** | `tools/reply_classifier.py` |
| **Schedule** | Every 2 hours, 8am-6pm |
| **Purpose** | Monitor cold email replies, classify intent, create CRM contacts |
| **Delivery** | Telegram (only when new replies found) |

**Classification logic:**

| Emoji | Category | Triggers | Action |
|-------|----------|----------|--------|
| `INTERESTED` | Warm lead | "interested", "tell me more", "let's chat" | Creates GHL contact (tags: `cold-email-reply`, `warm-lead`) |
| `PRICING` | Question | "pricing", "cost", "how much" | Creates GHL contact |
| `OBJECTION` | Pushback | "not interested", "too expensive" | Log only |
| `OOO` | Out of office | "out of office", "vacation" | Log only |
| `WRONG PERSON` | Mismatch | "wrong person", "try reaching" | Log only |
| `UNSUBSCRIBE` | Remove | "unsubscribe", "remove me" | Log only |

**Design:** Silent when nothing new — doesn't alert on zero activity.

---

### Agent 3: The Operator (5 Modes)

| | |
|---|---|
| **Script** | `tools/the_operator.py` |
| **Modes** | `dm`, `followup`, `content`, `leads`, `reviews` |

#### Mode: `dm` — Daily 6:00 AM
- Filters GHL contacts (removes clients/paid/converted)
- Generates 10 personalized IG DM openers (references company specifically, no links)
- Sends ready-to-copy list to Telegram

#### Mode: `followup` — Tue/Thu 8:00 AM
- Scans GHL opportunities for 3+ days no activity
- Max 5 per run
- Creates Gmail draft follow-ups (warm tone, includes /discovery-call link)
- Sends Telegram alert with drafts to review

#### Mode: `content` — Mon/Wed/Fri 6:30 AM
- Reads content calendar / posting guide
- Finds today's scheduled content
- Generates captions: IG + LinkedIn + Pinterest versions
- Rules: Hook <125 chars, 3-5 hashtags, CTA, credits, max 5 sentences
- Fallback: Suggests from rotation if nothing scheduled

#### Mode: `leads` — Saturday 10:00 AM
- Opens cold email input sheet (11 ICP tabs)
- Reports which tabs have unprocessed leads + count
- Tells Matt to run cold email pipeline

#### Mode: `reviews` — Wednesday 10:00 AM
- Checks GHL for tagged clients (`client`, `project-complete`, `delivered`)
- Filters out already-requested (`review-requested` tag)
- Creates Gmail draft review requests (max 3/run)
- Google review link: `https://g.page/r/CYUoPFBM2z9HEAE/review`

---

### Agent 4: The Watchdog (4 Modes)

| | |
|---|---|
| **Script** | `tools/the_watchdog.py` |
| **Modes** | `health`, `gbp`, `domains`, `retainer` |

#### Mode: `health` — Every 4 hours (6am, 10am, 2pm, 6pm, 10pm)
Checks and **only alerts if something fails**:
- mattanthonyphoto.com (status + load time <5s)
- n8n instance (healthz endpoint)
- GHL API, Instantly API, Gmail API
- balmoralconstruction.com

#### Mode: `gbp` — Daily 6:00 PM
- Searches Gmail for Google Business Profile notifications (reviews, questions, messages)
- Last 24 hours only; silent if no activity

#### Mode: `domains` — Daily 9:00 AM
- Checks Instantly campaigns are active (status=1)
- Checks sending account health/warmup
- Flags if domain gets flagged or campaign pauses

#### Mode: `retainer` — 1st of month 9:00 AM
- Sends Balmoral retainer deliverables checklist (always sends)
- Monthly tasks: website maintenance, SEO content, performance report, GBP update

---

### Agent 5: The Accountant (3 Modes)

| | |
|---|---|
| **Script** | `tools/the_accountant.py` |
| **Modes** | `invoices`, `expenses`, `tax` |

#### Mode: `invoices` — Wed/Fri 9:00 AM
- Finds invoices 14+ days old (sent, viewed, overdue, unpaid)
- Creates Gmail draft follow-ups (max 5/run)
- Sends Telegram alert with outstanding total
- Note: Steel Wood Structures $1,575 outstanding 9+ months

#### Mode: `expenses` — Monday 9:00 AM
- Searches Gmail for receipt/charge/subscription emails (last 7 days)
- Lists in Telegram
- Reminder to update finance sheet

#### Mode: `tax` — 1st + 15th of month (always sends)
- FHSA deadline (must open by Dec 31, 2026 — $8K deduction)
- Quarterly tax installments
- GST filing (due June 15)
- RRSP deadline (Mar 1)
- LOC balance ($16,574 at 8.94% = ~$123/mo interest)
- Monthly burn vs revenue

---

### Agent 6: The Producer (4 Modes)

| | |
|---|---|
| **Script** | `tools/the_producer.py` |
| **Modes** | `prep`, `handoff`, `delivery`, `costshare` |

#### Mode: `prep` — Daily 8:00 PM
- Checks tomorrow's calendar for shoots ("shoot", "photo", "session", "site visit")
- Sends prep checklist: cameras, lenses, tripod, drone, cards, flash, shot list, location scout, client confirmed, parking
- Silent if no shoots tomorrow

#### Mode: `handoff` — Mon/Thu 9:00 AM
- Checks GHL Production pipeline
- Lists projects with editor handoff checklist
- Editor: Alena Machinskaia (alenamachin@gmail.com, $2.50/photo)

#### Mode: `delivery` — Daily 5:00 PM
- Tracks GHL production pipeline age:
  - 5+ days: "Edits coming back from Alena"
  - 7+ days: "Standard window closing"
  - 10+ days: "Client expecting delivery!"
- SOP: Deliver within 7 days of shoot

#### Mode: `costshare` — Friday 2:00 PM
- Searches Gmail for delivery emails (last 14 days)
- Sends cost-share reminder: identify all parties, draft licensing email (30% fee)
- 2025 cost-share revenue: $7,822. Target 2026: $15,000+

---

### Agent 7: The Strategist (4 Modes)

| | |
|---|---|
| **Script** | `tools/the_strategist.py` |
| **Modes** | `campaigns`, `winloss`, `competitors`, `attribution` |

#### Mode: `campaigns` — Mon/Thu 10:00 AM
- Pulls Instantly data: sent, opened, replied, bounced
- Calculates open rate, reply rate, bounce rate
- Health flags: Bounce >5% = HIGH BOUNCE, Open <30% = LOW OPENS, Reply >3% = STRONG REPLIES

#### Mode: `winloss` — 1st of month
- GHL opportunities: won, lost, open
- Close rate, average deal value, revenue by source
- Identifies working vs non-working lead sources

#### Mode: `competitors` — 1st + 15th of month
- Pings competitor websites: Ema Peter, Martin Knowles, Fyfe Photography, Andrew Fyfe
- Checks online status + page size (proxy for content changes)

#### Mode: `attribution` — Sunday 6:00 PM (1hr before Sunday Command)
- GHL contacts grouped by source field
- Lead count per source with top tags
- Answers: "Where are my leads coming from?"

---

### Agent 8: Sunday Command

| | |
|---|---|
| **Script** | `tools/sunday_command.py` |
| **Schedule** | Sunday 7:00 PM |
| **Purpose** | Weekly CEO dashboard |
| **Delivery** | 3 Telegram messages |

**Message 1 — Numbers:**
- Revenue YTD vs $125K target (includes recurring estimate)
- This month's revenue, gap remaining, required monthly pace
- Outstanding/overdue invoices
- Pipeline: total value, deals by category, stale count

**Message 2 — Campaigns & Finance:**
- Cold email campaign status
- Cash flow: monthly burn (~$7,200), recurring ($1,417.50), gap
- LOC balance, interest
- FHSA and tax reminders

**Message 3 — Week Ahead & Actions:**
- Calendar events Mon-Sun
- Top 3 priorities (revenue-weighted)
- Weekly insight: one data-driven observation

---

## 5. Daily Timeline {#daily-timeline}

```
6:00 AM   📱 DM Prep (10 IG DMs ready)
6:00 AM   👁️ Watchdog health check
6:30 AM   📸 Content Operator (MWF — today's captions)
7:00 AM   ☀️ Morning Command (full briefing)
8:00 AM   📝 Follow-Up Drafter (Tue/Thu — stale deal drafts)
8:00 AM   📨 Reply Classifier (first run, then every 2hrs until 6pm)
9:00 AM   📡 Domain check (Instantly health)
9:00 AM   💳 Invoice Chaser (Wed/Fri)
9:00 AM   🧾 Expenses (Mon)
9:00 AM   📋 Retainer check (1st of month)
9:00 AM   📊 Tax reminders (1st + 15th)
10:00 AM  📊 Campaign analysis (Mon/Thu)
10:00 AM  ⭐ Reviews (Wed)
10:00 AM  🔄 Leads (Sat)
10:00 AM  📈 Win/Loss (1st of month)
10:00 AM  📨 Reply Classifier
11:00 AM  🔍 Competitors (1st + 15th)
12:00 PM  📨 Reply Classifier
2:00 PM   📨 Reply Classifier
2:00 PM   💰 Cost-Share (Fri)
4:00 PM   📨 Reply Classifier
5:00 PM   📦 Delivery tracker
6:00 PM   📨 Reply Classifier (last)
6:00 PM   📍 GBP monitor
6:00 PM   📊 Attribution (Sun)
7:00 PM   📊 Sunday Command (Sun)
8:00 PM   📸 Shoot Prep (if shoot tomorrow)
10:00 PM  👁️ Watchdog health check (last of day)
```

---

## 6. Workflows — 14 SOPs {#workflows}

All workflows live in `workflows/` as Markdown files.

| # | Workflow | File | Purpose |
|---|---------|------|---------|
| 1 | **Agent Fleet Playbook** | `agent-fleet.md` | Operating manual for all 23 cron jobs, troubleshooting, manual run commands |
| 2 | **Cold Email SOP** | `cold-email.md` | 14-part system: verify → qualify → research → generate → quality check → export |
| 3 | **Daily Outreach** | `daily-outreach.md` | 15-20 min morning routine: briefing → replies → warm leads → follow-ups |
| 4 | **Social Media Automation** | `social-media-automation.md` | n8n workflow specs: caption gen, publishing, analytics |
| 5 | **Social Media Management** | `social-media-management.md` | Master SOP: ingest → batch → schedule → engage → review |
| 6 | **Content Batching** | `content-batching.md` | Turn 1 shoot into 15-20+ content pieces (~2.5 hrs/project) |
| 7 | **Social Media Activation** | `social-media-activation.md` | 9-step setup guide (4-5 hrs total) |
| 8 | **Instagram DM Outreach** | `instagram-dm-outreach.md` | 4-layer system: prep → DM → comment funnel → plan closer |
| 9 | **Architect Outreach** | `architect-outreach.md` | Referral flywheel: warm-up → test shoot → cost-share → publication |
| 10 | **Builder Marketing Plan** | `generate-builder-marketing-plan.md` | Lead magnet: research → scaffold → generate → publish → DM |
| 11 | **Homepage Mockup Pitch** | `homepage-mockup-pitch.md` | Sales tool: scrape → redesign → render → pitch |
| 12 | **GEO Optimization** | `geo-optimization.md` | AI citation optimization via schema.org markup |
| 13 | **Generate Proposal** | `generate-proposal.md` | 3-command pipeline: scaffold → fill → generate HTML |
| 14 | **Publish Proposal** | `publish-proposal.md` | Upload to GitHub Pages (matt-proposals repo) |

---

## 7. Tools — 30+ Scripts {#tools}

### Agent Scripts (8 + 1 shared)

| Script | Purpose |
|--------|---------|
| `morning_command.py` | Daily 7am briefing |
| `reply_classifier.py` | Cold email reply classification |
| `the_operator.py` | 5-mode outreach/content/leads/reviews |
| `the_watchdog.py` | 4-mode health/domains/GBP/retainer |
| `the_accountant.py` | 3-mode invoices/expenses/tax |
| `the_producer.py` | 4-mode prep/handoff/delivery/costshare |
| `the_strategist.py` | 4-mode campaigns/winloss/competitors/attribution |
| `sunday_command.py` | Weekly CEO dashboard |
| `agent_utils.py` | Shared: Telegram, GHL, Instantly, Gmail, Calendar |

### Cold Email & Lead Gen

| Script | Purpose |
|--------|---------|
| `cold_email.py` | Full pipeline engine |
| `ig_dm_tracker.py` | IG DM prospect tracking |
| `instantly_monitor.py` | Campaign engagement data |
| `morning_briefing.py` | Daily signal compilation |
| `warm_lead_plan.py` | One-command marketing plan generation |

### Content & Social Media

| Script | Purpose |
|--------|---------|
| `social_media_manager.py` | Central content production engine |
| `carousel_builder.py` | AI-curated carousel sets (Claude Vision) |
| `reel_planner.py` | Reel concepts, scripts, audio suggestions |
| `generate_captions.py` | Vision-enhanced caption generation |
| `resize_images.py` | Smart-crop for all platforms |
| `content_calendar.py` | Google Sheet creation/population |

### Finance & Reporting

| Script | Purpose |
|--------|---------|
| `generate_finance_report.py` | Financial reporting |
| `update_finance_2026.py` | 2026 sheet updates |
| `import_2026_bank_csvs.py` | Bank transaction imports |
| `format_2026_sheet.py` | Sheet formatting |
| Various `import_*.py`, `audit_*.py` | Transaction processing |

### Proposals & Publishing

| Script | Purpose |
|--------|---------|
| `generate_proposal.py` | HTML proposal generation |
| `publish_proposal.py` | GitHub Pages deployment |
| `site_audit.py` | Website scraping for SEO data |
| `generate_site_audit_pdf.py` | PDF audit reports |
| `create_marketing_plan.py` | Marketing plan lead magnets |

### Prompts (Email Generation)

| File | Purpose |
|------|---------|
| `prompts/qualify_lead.md` | Lead qualification system prompt |
| `prompts/write_intro_email.md` | Cold intro email generation |
| `prompts/write_followup.md` | 3-day follow-up email generation |
| `prompts/write_breakup.md` | Final breakup email generation |

### Reel Generator (Node.js)

`tools/reel-generator/` — Remotion project for generating Instagram Reels with React/TypeScript. Components include `Root.tsx`, `PerchCaseStudy.tsx`, `WhatIDoReel.tsx`.

### Dashboard

`tools/dashboard.py` — Flask web app for business dashboard.

---

## 8. Integrations & API Stack {#integrations}

| Service | Purpose | Auth | Monthly Cost |
|---------|---------|------|-------------|
| **GoHighLevel** | CRM, pipeline, invoicing, contacts, booking | API key (`GHL_API_KEY`) | $150 |
| **Instantly** | Cold email sending, campaigns, warmup | API key (`INSTANTLY_API_KEY`) | $140 |
| **Gmail** | Search, draft creation, reply monitoring | OAuth (token.json) | — |
| **Google Calendar** | Event queries, shoot scheduling | OAuth (token.json) | — |
| **Google Sheets** | Finance, content calendar, leads, marketing | OAuth (token.json) | — |
| **Telegram** | All agent notifications | Bot token (`TELEGRAM_BOT_TOKEN`) | Free |
| **Icypeas** | Email verification | API key | Credit-based |
| **Apify** | Web scraping (n8n integration) | API key | Usage-based |
| **OpenRouter** | LLM calls from n8n workflows | API key | Usage-based |
| **Postiz** | Social media scheduling (IG, LinkedIn, Pinterest) | MCP | Free (self-hosted) |
| **ManyChat** | Instagram DM automation | API / MCP | Pro plan |
| **n8n** | Workflow automation (self-hosted) | Self-hosted | ~$5-10 hosting |
| **GitHub Pages** | Proposal/mockup hosting | `gh` CLI | Free |
| **Squarespace** | Main website (75 pages) | Admin | $17 |
| **Claude Code** | AI orchestrator (this system) | API | $85 |
| **Adobe CC** | Photo editing | Subscription | $80 |
| **Dropbox** | File storage/delivery | Subscription | $40 |
| **Google Workspace** | Email, Drive, Sheets, Calendar | Subscription | $50 |
| **Linear** | Project/task management | MCP | — |
| **Notion** | Marketing database, knowledge base | MCP | — |

### n8n Workflows (Self-Hosted)

**Instance:** `https://n8n.srv1277163.hstgr.cloud`

| Status | Workflow | Notes |
|--------|----------|-------|
| Active | Contact Form → GHL + Email + Sheet | Last success Mar 21 |
| Active | Pricing Guide Form → GHL + Emails + Sheet | Last success Mar 20 |
| Active | Project Brief Generator → GitHub Pages | Last success Mar 14 |
| Active | Cold Email System (70 nodes) | Last success Mar 20 |
| Erroring | Find Decision Makers Email | 3 consecutive errors Mar 23 |
| Erroring | Web Crawler - Find Decision Makers Name | Error Mar 22 |
| Inactive | Personalized Outreach Message (62 nodes) | Should deactivate |
| Archived | Gmail AI Filter, Newsletter Cleanup, KB Uploader, 3 cold email backups | — |

---

## 9. Cold Email Pipeline {#cold-email-pipeline}

### Overview

Complete 14-step system from raw lead to sent 3-email sequence.

### Pipeline Steps

1. **Lead Verification** — WebFetch with fallback chain (HTTPS → HTTP → www → WebSearch → directory)
2. **Qualification** — ICP scoring (Strong/Moderate/Weak/Disqualified) by architect/builder/designer/secondary criteria
3. **Decision Maker Research** — Hierarchy: owner → GM → PM → named contact
4. **Email Discovery** — Icypeas verification (pattern guesses have ~50% failure rate)
5. **Email Tier Classification** — Personal > initials-match > generic > none
6. **Award Research** — Always WebSearch prospect's award history
7. **Intro Email Generation** — Project-specific hook, ICP-specific angle, value prop from 10-13 variation pools
8. **Follow-Up Generation** — 4 sentences, 3 paragraphs, portfolio + case study links
9. **Breakup Generation** — 2-3 sentences, journal article as value-add
10. **Subject Lines** — Intro: 3-5 words, Follow-up: 2-4 words
11. **Quality Checks** — Content (7a), Structural (7b), Compliance/CASL (7c), Data completeness (7d)
12. **Export to Sheets** — Output sheet with all qualified leads
13. **Import to Instantly** — Campaign assignment
14. **Campaign Launch** — Sequence: Intro day 1, Follow-up day 4, Breakup day 8

### Active Campaigns

| Campaign | ICP | Domains |
|----------|-----|---------|
| Builders 2026 | Custom home builders | 2 sending accounts |
| Architects 2026 | Architecture firms | 2 sending accounts |
| Interior Designers | Design firms | Ready to launch |

### Benchmarks

- Open rate target: 50%+
- Reply rate target: 8-12%
- Bounce rate ceiling: <2%

### Lead Pool

~2,251 raw leads across 11 ICP tabs:
- **Primary:** Architects, Custom Home Builders, Interior Designers
- **Secondary:** Millwork, Window/Glazing, Structural Steel, Landscape Architecture, Commercial Construction, Development, Modular/Prefab, Concrete/Masonry, Roofing/Exterior

---

## 10. Social Media System {#social-media-system}

### Content Production Pipeline

```
Shoot Complete → Asset Selection → Content Batching (2.5hrs) → 15-20 pieces
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
              Instagram              LinkedIn            Pinterest
              4-5/week               3-4/week             23/week
              60-70% Reels           Document carousels    SEO pins
              20-30% Carousels       Thought leadership    11 boards
              10% Singles            B2B focus
```

### Tools

| Tool | Purpose |
|------|---------|
| `social_media_manager.py` | Central engine (ingest, plan, brief, report) |
| `generate_captions.py` | Claude Vision-enhanced captions |
| `carousel_builder.py` | AI-curated carousel sets |
| `reel_planner.py` | Reel concepts and scripts |
| `resize_images.py` | Platform-specific crops |
| `content_calendar.py` | Google Sheet management |

### Scheduling & Publishing

- **Postiz** (self-hosted, MCP) — Primary scheduler for IG, LinkedIn, Pinterest
- **Formatting rules:** HTML→plaintext for IG, never include account name
- **Stories:** No "swipe up" on static stories, use "see our latest post"

### Content Strategy Docs (in `business/marketing/`)

- `content-strategy.md` — Master strategy, pillars, repurposing chain
- `caption-templates.md` — Fill-in-the-blank frameworks
- `hooks-scripts-library.md` — 53 proven hooks + 6 universal formulas
- `hashtag-system.md` — 5-tier system, 80+ hashtags, 10 rotation groups
- `linkedin-b2b-playbook.md` — LinkedIn optimization
- `pinterest-playbook.md` — 11 board structures, SEO cadence
- `instagram-reactivation-calendar.md` — Reactivation plan (@mattanthonyphoto)

---

## 11. Proposal & Pitch System {#proposal-system}

### Proposal Generation

**3-command pipeline:**
1. `scaffold` — Creates config JSON from template
2. `fill` — Populates with client research data
3. `generate` — Renders standalone HTML

**Design system:** CSS tokens, typography (Playfair Display + Inter), animations (scroll reveals), section types, image CDN integration.

**Deployment:** `publish_proposal.py` → GitHub Pages (`matt-proposals` repo)
**URL pattern:** `https://mattanthonyphoto.github.io/matt-proposals/<name>/index.html`

### Homepage Mockup Pitch

**Purpose:** Personalized homepage redesign mockups as sales pitch tools for builders.

**Flow:** Scrape builder's current site → Render premium redesign → Publish → Pitch

**Design rules:** No custom cursors, design luxury builder aesthetic (not tech/agency).

**10 existing mockups** including Blackfish, KC Interior Design, Colour Craft Painting, and others.

### Builder Marketing Plan (Lead Magnet)

**6-step workflow:**
1. Research builder (site audit + IG + Google + awards + competitors)
2. Scaffold config
3. Fill with research
4. Choose cover image
5. Generate and publish
6. Send via IG DM

17 sections including snapshot scores, competitor comparison, optimization recommendations, content engine, and quarterly roadmap.

---

## 12. Production & Delivery {#production-system}

### Workflow

```
Shoot Booked → Prep (The Producer, 8pm night before)
     │
     ▼
Shoot Day → Cull & Select → Handoff to Editor
     │                           │
     │                    Alena Machinskaia
     │                    $2.50/photo
     │                           │
     ▼                           ▼
Delivery (7 days SOP) ← Edited Photos
     │
     ▼
Cost-Share (30% licensing fee to all parties)
     │
     ▼
Review Request (automated via The Operator)
```

### Team

| Role | Person | Rate | Contact |
|------|--------|------|---------|
| Photographer | Matt Anthony | — | matt@mattanthonyphoto.com |
| Photo Editor | Alena Machinskaia | $2.50/photo | alenamachin@gmail.com |

### Operations Docs (in `business/operations/`)

- `pricing.md` — Service pricing
- `onboarding-checklist.md` — Client onboarding
- `visual-direction.md` — Aesthetic/style direction
- `service-agreements.md` — Contracts
- `client-prep-guide.md` — Client preparation
- `creative-brief.md` — Project briefs
- `shoot-checklist.md` — Pre-shoot checklist
- `scout-notes.md` — Site scouting
- `shot-list-template.md` — Shot lists
- `delivery-workflow.md` — Delivery process

---

## 13. Finance & Accounting {#finance-system}

### Revenue

| Period | Amount | Notes |
|--------|--------|-------|
| **2024** | $75,000 gross / $20,800 net | T1/T2125 filed |
| **2025** | $105,237 | 89 invoices |
| **2026 Target** | $125,000 | 21 projects + 2 retainers |
| **2026 YTD (Q1)** | $5,701.50 | Recurring base: $1,417.50/mo |
| **2025 Cost-Share** | $7,822 | 2026 target: $15,000+ |

### Financial Position

| Item | Amount |
|------|--------|
| LOC Balance | $16,574 / $35K limit at 8.94% |
| LOC Interest | ~$123/mo |
| TFSA | $43,472 |
| Monthly Overhead | $4,717 |
| Owner Draw Target | $3,000/mo |
| Monthly Burn | ~$7,200 |

### Key Deadlines

- **FHSA:** Must open by Dec 31, 2026 ($8K deduction)
- **GST Filing:** Due June 15
- **RRSP:** Mar 1 deadline
- **Quarterly Installments:** CRA schedule

### Tracking

- **2025 Finance Sheet** — Google Sheets (complete)
- **2026 Finance Sheet** — Google Sheets (active)
- Bank CSV imports via `import_2026_bank_csvs.py`
- Rules: No duplicate split rows, use checkboxes, single row with Split%

---

## 14. Website & SEO {#website-seo}

### Main Site: mattanthonyphoto.com

- **Platform:** Squarespace
- **Pages:** 75 (7 location pages, 24+ journal articles, 22 FAQs)
- **Schema:** Strong JSON-LD markup
- **CSS Prefix System:** Custom design system for code blocks

### Client Site: balmoralconstruction.com

- **Pages:** 42-page rebuild
- **SEO Roadmap:** 6-month plan
- **Retainer:** $2,500-$3,500/mo Creative Partner proposal (sent Mar 24)

### GEO Optimization (AI Citations)

7 tasks in `workflows/geo-optimization.md`:
1. BlogPosting schema for 24 journal articles
2. Statistics integration
3. Outbound links in award guides
4. Review schema for testimonials
5. Content freshness signals
6. Expanded bio with credentials
7. Completed tasks tracking

### SEO Audit

76-page meta audit + GEO visibility check with fix checklist (`project_seo_geo_audit_march2026.md`).

---

## 15. Sales Playbooks & ICP Research {#sales-playbooks}

### Primary ICPs

| ICP | Key Docs | Angle |
|-----|----------|-------|
| **Architects** | `architect-icp-deep-profile.md`, `architect-objection-handling.md`, `architect-retainer-model.md`, `architect-awards-calendar.md` | Design-intent framing, publication pipeline, spring/summer prebooking |
| **Custom Home Builders** | `builder-icp-deep-profile.md`, `builder-website-audit.md`, `retainer-pitch-builders.md`, `objection-handling.md` | Cost-share value, construction progress documentation, Georgie timing |
| **Interior Designers** | `designer-icp-deep-profile.md`, `designer-objection-handling.md`, `designer-retainer-model.md` | Instagram-first buying behavior, editorial/lifestyle language |

### Retainer Models

| ICP | Tiers |
|-----|-------|
| **Architects** | Portfolio Partner ($2K/mo), Publication Partner ($3K/mo) |
| **Designers** | Content ($1.5K), Editorial ($2.5K), Creative ($3.5K) |
| **Builders** | Trust ladder: one-off → retainer (flexible) |

### Outreach Channels

| Channel | Status | Details |
|---------|--------|---------|
| Cold Email (Instantly) | LIVE | 3 campaigns, 2 domains |
| Instagram DMs | Active | 5/week (2 designers, 1-2 builder/spouse, 1 architect) |
| Architect Referral | In progress | STARK, McLintock, AKA as Tier 1 targets |
| Homepage Mockup Pitch | Active | 10 existing mockups |
| Builder Marketing Plan | Active | Lead magnet for DM outreach |

### Key Sales Docs

- `georgie-playbook-2026.md` — Pre/during/post gala plan (May 2026)
- `spouse-office-manager-channel.md` — Reaching actual marketing decision-makers
- `architect-referral-flywheel.md` — STARK as #1 target, full flywheel mechanics

### Pipeline (GHL)

- Discovery call CTA: always link to `/discovery-call` (never raw GHL widget URL)
- Close rate gaps identified in `project_sales_strategy.md`
- First warm reply: Kombi Construction (Brian) Mar 25

---

## 16. Business Context {#business-context}

### Owner Profile

- **Name:** Matt Anthony
- **Business:** Sole proprietorship, architectural photography
- **Location:** Squamish, BC (Sea-to-Sky Corridor)
- **GST#:** 79115 0261 RT0001
- **Phone:** 604.765.9270
- **Website:** mattanthonyphoto.com
- **Instagram:** @mattanthonyphoto (2,427 followers)
- **LinkedIn:** /in/mattanthonyphoto/
- **Certifications:** Transport Canada Advanced Drone Pilot

### Services

1. **Project Photography** — Architectural photo shoots
2. **Award & Publication Imagery** — Portfolio for submissions
3. **Build & Team Content** — Construction progress, team documentation
4. **Creative Partner** — Ongoing embedded creative retainer (expanded scope)

### Service Areas

Sea-to-Sky, Sunshine Coast, Vancouver, Fraser Valley, Okanagan

### Travel Costs (from cold email SOP)

| Location | Cost |
|----------|------|
| Whistler | $31 |
| Vancouver | $50-80 |
| Sunshine Coast | $100-150 |
| Victoria | $400-500 |

### 2026 Strategic Priorities

- Hit $125K revenue (21 projects + 2 retainers)
- Build recurring base via retainers
- Activate Instagram (dormant since Oct 2025)
- Scale cost-share to $15K+
- Open FHSA by Dec 31

### 2027 Vision

Scale to $150K+ with retainer base, team growth, and publication pipeline.

---

## 17. Feedback & Operating Rules {#feedback-rules}

These are hard-won rules from experience. Follow them exactly.

### Cold Email Rules

| Rule | Why |
|------|-----|
| No em/en dashes in cold emails — use commas | Formatting breaks in some clients |
| 10-13 variation pools, never repeat value props across a batch | Anti-template detection |
| Only qualified leads in output sheet | Keep output clean |
| Always verify emails via Icypeas | Pattern guesses have ~50% failure rate |
| Go down team hierarchy (GM, PM) when owner email not findable | Still reach the company |
| Never batch-mark leads without actually scraping each one | Quality over speed |
| Every cell filled with data or "Not found" with reason | Complete records |
| Retry with http://www., then WebSearch before marking site as down | Sites have weird configs |
| Always WebSearch prospect's award history — never assume zero | Awards = strongest hook |
| Architect emails: design-intent framing, spring/summer prebooking | Resonates with their identity |
| Discovery call CTAs must link to /discovery-call | Never use raw GHL widget URL |

### Social Media Rules

| Rule | Why |
|------|-----|
| Postiz IG: HTML→plaintext, never include account name | Platform formatting requirements |
| No "swipe up" on static stories — use "see our latest post" | Only video stories support swipe |

### Design Rules

| Rule | Why |
|------|-----|
| No custom cursors on mockups | Luxury builder aesthetic, not tech/agency |
| No gold font in sheets — white headers + black data rows | Readability |

### System Rules

| Rule | Why |
|------|-----|
| Verify GHL intake forms with Matt before treating as real leads | Test data gets mixed in |
| Separate clients from leads in Notion — GHL as source of truth | Data hygiene |
| No temperature setting via n8n API | API limitation |
| No `continueRegularOutput` on critical n8n nodes | Causes silent failures |
| VA premature at current revenue — revisit at $150K+ | Cost doesn't justify yet |

### Finance Rules

| Rule | Why |
|------|-----|
| No duplicate split rows — use checkboxes, single row with Split% | Sheet gets bloated |

---

## 18. Reference Config {#reference-config}

### API Credentials (.env)

```
GHL_API_KEY=pit-xxx
GHL_LOCATION_ID=6Nlxml1Rtjj35EjoKuLO
INSTANTLY_API_KEY=xxx
TELEGRAM_BOT_TOKEN=8186928770:xxx
TELEGRAM_CHAT_ID=8780007312
```

### Google OAuth

- **File:** `token.json` (auto-refreshed)
- **Scopes:** spreadsheets, drive, gmail.compose, gmail.readonly, calendar.readonly

### Telegram Bot

- **Bot:** @mattbriefing_bot
- **Chat ID:** 8780007312
- **Formatting:** HTML (bold, italic, code, links)
- **Message limit:** 4096 chars (auto-split in agent_utils.py)

### GitHub

- **Repo:** matt-agency (private, 474 files)
- **Proposals repo:** matt-proposals (public, GitHub Pages)

### n8n

- **Instance:** `https://n8n.srv1277163.hstgr.cloud`
- **Hosting:** Hostinger

### Instantly

- **Campaigns:** Builders 2026, Architects 2026, Interior Designers
- **Domains:** 2 sending accounts
- **API note:** v2 uses Authorization Bearer header (not query params). Deletion is org-wide. Bulk endpoint broken. Delete needs no content-type header.

### ManyChat

- **Status:** Pro plan active
- **Use:** IG DM automation, comment-to-DM funnels

### Postiz

- **Status:** Self-hosted, free
- **Integrations:** Instagram, LinkedIn, Pinterest
- **Access:** MCP server

### Key Google Sheets

- **2025 Finance Sheet** — Full year, 89 invoices
- **2026 Finance Sheet** — Active tracking
- **Cold Email Input Sheet** — 11 ICP tabs with TAB_MAP keys
- **Content Calendar** — Instagram schedule with carousel previews
- **Marketing Plan Sheet** — 8 tabs

### Notion

- **Marketing Database** — 51 items, 8 views
- **Database IDs** — Stored in `reference_notion_structure.md`

### GHL Pipelines

- **Sales Pipeline** — Open opportunities, deal aging
- **Production Pipeline** — Active projects, editor handoff

---

## 19. Known Issues & Constraints {#known-issues}

### Critical

| Issue | Status |
|-------|--------|
| Anthropic remote sandbox blocks outbound HTTP | All agents moved to local cron |
| 2 n8n workflows erroring (Find Decision Makers) | Needs investigation |
| Instagram dormant since October 2025 | Reactivation plan exists |
| $300/mo ad budget not being spent | No paid ads running |
| Google Business Profile not fully set up | Highest priority gap |

### Operational

| Issue | Status |
|-------|--------|
| `/construction-team-content` page serving wrong content | Known bug |
| FAQ typos on main site | Known |
| Fitzsimmons project missing JSON-LD | Known |
| Steel Wood Structures $1,575 outstanding 9+ months | Invoice chasing active |
| Python `operator.py` conflicts with built-in module | Renamed to `the_operator.py` |
| Google Calendar API requires separate OAuth scope | Must re-auth via browser |
| Instantly API v2 uses Bearer header, not query params | Implemented |
| Mac sleep can miss cron jobs | Known limitation |

### Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| Local cron over remote agents | Remote sandbox blocks outbound API calls |
| Telegram over email for alerts | Instant, scannable, no inbox clutter |
| Gmail drafts (not auto-send) for follow-ups | Human review before sending |
| Silent agents (no alert on zero activity) | Reduce notification fatigue |
| 7-day delivery SOP | Client expectation management |
| 30% cost-share fee | Industry standard for licensing |

---

## Appendix: Complete File Tree

```
Claude/
├── CLAUDE.md                          # WAT Framework instructions
├── agent-os.md                        # This document
├── .env                               # API keys
├── token.json                         # Google OAuth
├── .claude/
│   └── settings.local.json            # Permissions whitelist
│
├── workflows/                         # 14 SOPs
│   ├── agent-fleet.md
│   ├── cold-email.md
│   ├── daily-outreach.md
│   ├── social-media-automation.md
│   ├── social-media-management.md
│   ├── content-batching.md
│   ├── social-media-activation.md
│   ├── instagram-dm-outreach.md
│   ├── architect-outreach.md
│   ├── generate-builder-marketing-plan.md
│   ├── homepage-mockup-pitch.md
│   ├── geo-optimization.md
│   ├── generate-proposal.md
│   └── publish-proposal.md
│
├── tools/                             # 30+ execution scripts
│   ├── agent_utils.py                 # Shared API module
│   ├── morning_command.py             # Agent: Morning Command
│   ├── reply_classifier.py            # Agent: Reply Classifier
│   ├── the_operator.py                # Agent: The Operator (5 modes)
│   ├── the_watchdog.py                # Agent: The Watchdog (4 modes)
│   ├── the_accountant.py              # Agent: The Accountant (3 modes)
│   ├── the_producer.py                # Agent: The Producer (4 modes)
│   ├── the_strategist.py              # Agent: The Strategist (4 modes)
│   ├── sunday_command.py              # Agent: Sunday Command
│   ├── cold_email.py                  # Cold email pipeline
│   ├── ig_dm_tracker.py               # IG DM tracking
│   ├── instantly_monitor.py           # Campaign monitoring
│   ├── morning_briefing.py            # Signal compilation
│   ├── warm_lead_plan.py              # Marketing plan generation
│   ├── social_media_manager.py        # Content production
│   ├── carousel_builder.py            # Carousel creation
│   ├── reel_planner.py                # Reel planning
│   ├── generate_captions.py           # Caption generation
│   ├── resize_images.py               # Image resizing
│   ├── content_calendar.py            # Calendar management
│   ├── generate_proposal.py           # Proposal generation
│   ├── publish_proposal.py            # GitHub Pages deployment
│   ├── site_audit.py                  # SEO auditing
│   ├── dashboard.py                   # Flask dashboard
│   ├── prompts/
│   │   ├── qualify_lead.md            # Lead qualification prompt
│   │   ├── write_intro_email.md       # Intro email prompt
│   │   ├── write_followup.md          # Follow-up prompt
│   │   └── write_breakup.md           # Breakup email prompt
│   └── reel-generator/               # Remotion video project
│       ├── package.json
│       └── src/
│           ├── Root.tsx
│           ├── PerchCaseStudy.tsx
│           ├── WhatIDoReel.tsx
│           └── ...
│
├── business/
│   ├── CLAUDE.md                      # Business profile & context
│   ├── sales/                         # ICP profiles, objection handling, retainer models
│   ├── marketing/                     # Content strategy, templates, playbooks
│   ├── operations/                    # Pricing, onboarding, checklists, agreements
│   ├── website/                       # Deployment, alt-text, meta descriptions
│   └── lead-gen/                      # Lead generation strategies
│
└── clients/
    ├── Sacred Ways/                   # Active client project
    └── balmoral/                      # Balmoral Construction retainer
```

---

*This document is the complete operating manual for Matt Anthony's Agent OS — a fully automated business intelligence and operations system built on the WAT Framework (Workflows, Agents, Tools). Every agent, workflow, tool, integration, and operating rule is documented here.*
