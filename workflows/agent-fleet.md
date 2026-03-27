# Agent Fleet Playbook

Complete operating manual for the 23-job automated agent fleet. Everything delivers to Telegram (@mattbriefing_bot). All scripts live in `tools/`. Logs at `/tmp/*.log`.

**Requirement:** Mac must be awake for cron jobs to fire. If it sleeps through a scheduled time, that job is skipped until the next occurrence.

**Manual run:** Any agent can be triggered manually:
```bash
python3 tools/morning_command.py
python3 tools/the_operator.py followup
python3 tools/the_watchdog.py health
python3 tools/the_accountant.py invoices
python3 tools/the_producer.py prep
python3 tools/the_strategist.py campaigns
```

**View schedule:** `crontab -l`
**Edit schedule:** `crontab -e`
**Check logs:** `cat /tmp/morning_command.log`

---

## 1. MORNING COMMAND

**Script:** `tools/morning_command.py`
**Schedule:** Daily 7:00 AM
**Log:** `/tmp/morning_command.log`
**Delivers:** 2 Telegram messages

### What it does
Pulls data from 4 sources and compiles a daily command center briefing.

### Data sources
1. **Google Calendar** — today's events via Calendar API REST call
2. **Gmail** — last 24 hours of email via Gmail API (excludes promotions, social, updates)
3. **GHL Pipeline** — all open opportunities via GHL API, flags stale deals (3+ days = red, 1-3 = yellow)
4. **Instantly** — campaign status for Builders, Architects, Interior Designers

### Message 1 content
- Today's schedule (events with times, locations, context from descriptions)
- Email highlights (client replies, new inquiries, invoicing, flagged unsent drafts)
- Deal pulse (red/yellow/green deals, pipeline value, total active deals)

### Message 2 content
- Campaign stats (active campaigns, status)
- Content today (what's scheduled from the posting guide)
- Top 3 actions (prioritized by revenue impact)

### How it decides Top 3 Actions
1. Any red (stale 3+ days) deals → "Follow up on [deal]"
2. Any unsent Gmail drafts → "Send [X] unsent drafts"
3. New replies in Instantly → "Check unibox for replies"

### When it stays silent
Never — it always sends. Even if everything is clean, it sends "Inbox clear" and "No events scheduled."

### Dependencies
- `.env` (GHL_API_KEY, GHL_LOCATION_ID, INSTANTLY_API_KEY)
- `token.json` (Google OAuth — Gmail + Calendar scopes)
- `agent_utils.py` (shared utilities)

---

## 2. REPLY CLASSIFIER

**Script:** `tools/reply_classifier.py`
**Schedule:** Every 2 hours — 8am, 10am, 12pm, 2pm, 4pm, 6pm
**Log:** `/tmp/reply_classifier.log`
**Delivers:** 1 Telegram message (only if new replies found)

### What it does
Monitors Instantly unibox for cold email replies. Classifies each reply. Creates GHL contacts for warm leads.

### Classification system
| Label | Trigger words | Action |
|-------|--------------|--------|
| 🟢 INTERESTED | "interested", "tell me more", "let's chat", "availability", "schedule" | Creates GHL contact with tags `cold-email-reply` + `warm-lead` |
| 🟡 PRICING QUESTION | "pricing", "rates", "cost", "how much", "packages" | Creates GHL contact (same tags) |
| 🟠 OBJECTION | "not interested", "no thanks", "already have", "too expensive" | Flagged for review |
| ⚪ OOO | "out of office", "on vacation", "returning" | Logged, no action |
| 🔵 WRONG PERSON | "wrong person", "try reaching", "forward this to" | Flagged — find correct contact |
| 🔴 UNSUBSCRIBE | "unsubscribe", "remove me", "stop emailing" | Flagged — remove from Instantly |

### GHL contact creation (for INTERESTED + PRICING)
- Extracts first/last name from sender
- Extracts company from email domain
- Sets source to "Cold Email - [Campaign Name]"
- Tags: `cold-email-reply`, `warm-lead`

### When it stays silent
When no new replies are found in the last 2 hours. This is by design — you only get pinged when something needs attention.

### Known limitation
- Checks Instantly unibox API which may not have reply timestamps. Falls back to including all if can't parse dates.
- Company name extracted from email domain (rough — "ianpaineconstruction" becomes "Ianpaineconstruction"). Review in GHL.

---

## 3. THE OPERATOR

**Script:** `tools/the_operator.py`
**5 modes, each on its own schedule**

### Mode: `dm`
**Schedule:** Daily 6:00 AM
**Log:** `/tmp/operator_dm.log`

**What it does:** Pulls contacts from GHL, filters out existing clients (tagged `client`, `paid`, `converted`), generates personalized DM openers for the top 10 prospects. Sends to Telegram as a ready-to-send list.

**Your action:** Open Instagram, find each prospect, paste the DM. Takes ~15 minutes.

**Current limitation:** DMs are template-based from GHL data. For deeper personalization (referencing specific projects, awards, recent posts), run the full IG DM workflow manually: `python3 tools/ig_dm_tracker.py`.

### Mode: `followup`
**Schedule:** Tuesday + Thursday 8:00 AM
**Log:** `/tmp/operator_followup.log`

**What it does:** Scans GHL pipeline for open deals with no activity in 3+ days. For each stale deal (max 5 per run), creates a Gmail draft follow-up email. Sends Telegram alert listing each draft.

**Email template:** Professional, warm, references their company. Includes discovery call link (mattanthonyphoto.com/discovery-call). Not pushy — "just don't want this to slip through the cracks."

**Your action:** Open Gmail drafts, review each one (personalize if needed), hit send.

**Important:** These are drafts, not sent emails. You always review before sending.

### Mode: `content`
**Schedule:** Monday, Wednesday, Friday 6:30 AM
**Log:** `/tmp/operator_content.log`

**What it does:** Reads the instagram posting guide (`business/marketing/social-media/instagram-posting-guide.md`). Finds today's scheduled content. Generates IG caption (hook + body + credits + CTA + hashtags), LinkedIn version, and Pinterest version. Sends all 3 to Telegram.

**If no content is scheduled for today:** Generates a suggestion based on project rotation (The Perch, Warbler, Eagle, Sugarloaf, Fitzsimmons) with partner handles.

**Your action:** Copy caption from Telegram, grab images from Photo Assets folder, post to IG via Postiz or natively. Copy LinkedIn/Pinterest versions for those platforms.

**Caption rules built in:**
- Hook under 125 chars
- 3-5 hashtags (1 broad, 1 niche, 1 location, 1 community, 1 trending)
- Credit line with partner handles
- Save/send CTA

### Mode: `leads`
**Schedule:** Saturday 10:00 AM
**Log:** `/tmp/operator_leads.log`

**What it does:** Opens the cold email input sheet (11 ICP tabs). Finds the next tab with unprocessed leads. Reports how many are ready and which tab. Tells you to run the cold email pipeline.

**Your action:** Run `python3 tools/cold_email.py` with the flagged tab to qualify, enrich, generate sequences, and export to Instantly.

**Tab priority:** Millwork → Windows → Steel → Landscape → Lighting → Flooring → Hardware → Envelope

**Current limitation:** Doesn't auto-run the cold email pipeline (it's a heavy process with paid API calls — Icypeas, web scraping). Reports what's ready so you can decide.

### Mode: `reviews`
**Schedule:** Wednesday 10:00 AM
**Log:** `/tmp/operator_reviews.log`

**What it does:** Checks GHL for clients tagged `client`, `project-complete`, or `delivered` who haven't been tagged `review-requested`. Creates Gmail draft review request emails (max 3 per run) with the direct Google review link.

**Falls back to:** Known happy clients (Summerhill, Sitelines, Koze) if no tagged clients found.

**Review link:** https://g.page/r/CYUoPFBM2z9HEAE/review

**Your action:** Open Gmail drafts, review, send. Then tag the client `review-requested` in GHL so they don't get asked twice.

**Q2 rock target:** 10 Google reviews by June 15.

---

## 4. THE WATCHDOG

**Script:** `tools/the_watchdog.py`
**4 modes — only alerts when something's wrong**

### Mode: `health`
**Schedule:** Every 4 hours — 6am, 10am, 2pm, 6pm, 10pm
**Log:** `/tmp/watchdog_health.log`

**Checks:**
1. mattanthonyphoto.com — HTTP status + load time (flags if >5s)
2. n8n instance (n8n.srv1277163.hstgr.cloud/healthz)
3. GHL API — contacts endpoint responds
4. Instantly API — campaigns endpoint responds
5. Gmail API — can search messages
6. Balmoral website — balmoralconstruction.com (non-critical)

**When it alerts:** Only if something fails. You should rarely see messages from this agent. If you're getting alerts, something is broken.

**When it stays silent:** All systems healthy. Logs "all systems healthy" but sends nothing to Telegram.

### Mode: `gbp`
**Schedule:** Daily 6:00 PM
**Log:** `/tmp/watchdog_gbp.log`

**What it does:** Searches Gmail for Google Business Profile notifications (new reviews, questions, messages) from the last 24 hours.

**Why 6pm:** Gives you time to respond same-day. Google rewards fast responses to reviews.

**Your action:** If alerted, go to Google Business Profile and respond to the review/question within 24 hours.

**When it stays silent:** No GBP activity. No alert sent.

### Mode: `domains`
**Schedule:** Daily 9:00 AM
**Log:** `/tmp/watchdog_domains.log`

**What it does:** Checks all Instantly campaigns are active (status=1). Checks sending account health/warmup status.

**Why this matters:** If a sending domain gets flagged or a campaign pauses, your entire cold email system stops silently. This catches it.

**Your action:** If alerted, check Instantly dashboard. Re-warm any flagged domains. Reactivate paused campaigns.

**When it stays silent:** All campaigns active, all accounts healthy.

### Mode: `retainer`
**Schedule:** 1st of every month, 9:00 AM
**Log:** `/tmp/watchdog_retainer.log`

**What it does:** Sends a Balmoral retainer deliverables checklist for the month. Shows email activity with Marc. Lists monthly tasks: website maintenance, SEO content, performance report, GBP update.

**Always sends:** This is a monthly reminder, not a conditional alert.

**Your action:** Check off each deliverable as you complete it during the month. Don't let a $2,500/mo client churn because a blog post was forgotten.

---

## 5. THE ACCOUNTANT

**Script:** `tools/the_accountant.py`
**3 modes**

### Mode: `invoices`
**Schedule:** Wednesday + Friday 9:00 AM
**Log:** `/tmp/accountant_invoices.log`

**What it does:** Pulls all invoices from GHL. Finds any with status `sent`, `viewed`, `overdue`, or `unpaid` that are 14+ days old. Creates Gmail draft follow-up emails (max 5 per run). Sends Telegram alert with total outstanding.

**Email tone:** Polite, not aggressive. "Just want to make sure this didn't slip through the cracks."

**Your action:** Review Gmail drafts, personalize if needed, send. For Steel Wood ($1,575, 9+ months), consider a stronger follow-up or write-off.

**Why Wed + Fri:** Mid-week + end-of-week. Catches invoices before weekends when people forget.

### Mode: `expenses`
**Schedule:** Monday 9:00 AM
**Log:** `/tmp/accountant_expenses.log`

**What it does:** Searches Gmail for receipt, charge, subscription, and renewal emails from the last 7 days. Lists them in Telegram.

**Your action:** Open your 2026 finance sheet and categorize each charge. Flag anything unexpected.

**Why Monday:** Start the week knowing what was charged last week.

### Mode: `tax`
**Schedule:** 1st and 15th of every month
**Log:** `/tmp/accountant_tax.log`

**Always sends.** Includes:
- FHSA deadline countdown (must open before Dec 31, 2026 — $8,000 deduction)
- Quarterly tax installment reminders (30 days before due)
- GST filing reminder (due June 15)
- RRSP deadline (Mar 1 for prior tax year)
- LOC balance and interest cost ($16,574 at 8.94% = ~$123/mo)
- Monthly burn breakdown vs revenue

---

## 6. THE PRODUCER

**Script:** `tools/the_producer.py`
**4 modes**

### Mode: `prep`
**Schedule:** Daily 8:00 PM
**Log:** `/tmp/producer_prep.log`

**What it does:** Checks tomorrow's Google Calendar for events containing "shoot", "photo", "session", "project", "site visit" (in title or description). If found, sends a shoot prep checklist to Telegram.

**Checklist includes:** Camera bodies, lenses, tripod, drone, memory cards, flash, shot list, location scouted, client confirmed, parking/access.

**When it stays silent:** No shoots tomorrow. Most days you won't hear from this agent.

**Your action:** Pack gear tonight. Leave 30 min early.

**Known limitation:** Calendar scope requires the re-authorized token. If Calendar returns 403, this agent won't find shoots. Run the OAuth re-auth command to fix.

### Mode: `handoff`
**Schedule:** Monday + Thursday 9:00 AM
**Log:** `/tmp/producer_handoff.log`

**What it does:** Checks GHL for opportunities in the Production pipeline (IDs: gwY9Bs918EJnG31qua09, vPYWW2NnhYFcdc7SfwyS). Lists each with an editor handoff checklist.

**Checklist:** Cull selects → Create Dropbox folder → Email Alena (photo count + style direction + deadline) → Set delivery deadline (7 days).

**Editor:** Alena Machinskaia (alenamachin@gmail.com, $2.50/photo)

**When it stays silent:** No projects in production pipeline.

### Mode: `delivery`
**Schedule:** Daily 5:00 PM
**Log:** `/tmp/producer_delivery.log`

**What it does:** Checks GHL production pipeline for project age:
- 🟢 5+ days: "Edits should be coming back from Alena"
- 🟡 7+ days: "Standard delivery window closing"
- 🔴 10+ days: "Client expecting delivery!"

**SOP:** Deliver within 7 days of shoot. 10+ days = client anxiety.

**When it stays silent:** No projects in production, or all under 5 days.

### Mode: `costshare`
**Schedule:** Friday 2:00 PM
**Log:** `/tmp/producer_costshare.log`

**What it does:** Searches Gmail for recent delivery emails (last 14 days). If found, sends a cost-share reminder with the checklist: identify all parties (architect, designer, builder, sub-trades), draft licensing email (30% fee), include portfolio link.

**Revenue context:** 90% hit rate on cost-share, near-100% margin. 2025 was $7,822. Target $15,000+ in 2026. Every project is worth 1.3-1.9x its face value.

**Your action:** For each completed project, identify who else was involved and send licensing outreach.

---

## 7. THE STRATEGIST

**Script:** `tools/the_strategist.py`
**4 modes**

### Mode: `campaigns`
**Schedule:** Monday + Thursday 10:00 AM
**Log:** `/tmp/strategist_campaigns.log`

**What it does:** Pulls campaign data from Instantly. Attempts to fetch per-campaign analytics (sent, opened, replied, bounced). Calculates open rate, reply rate, bounce rate. Flags unhealthy campaigns.

**Health thresholds:**
- Bounce >5% → 🔴 HIGH BOUNCE (clean list)
- Open <30% → 🟡 LOW OPENS (test subject lines)
- Reply >3% → 🟢 STRONG REPLIES

**Includes recommendations:** When to deploy Interior Designers, when to test new subject lines, when to re-verify with Icypeas.

**Known limitation:** Instantly API analytics endpoints vary by plan. May return limited data.

### Mode: `winloss`
**Schedule:** 1st of every month
**Log:** `/tmp/strategist_winloss.log`

**What it does:** Pulls all GHL opportunities. Categorizes into won, lost, and open. Calculates close rate, average deal value, and revenue by source. Identifies which lead sources produce revenue vs which are just activity.

**Why monthly:** Needs enough data points to find patterns. Weekly would be noise.

**Your action:** Review the close rate and source breakdown. Double down on what's working. Cut what isn't.

### Mode: `competitors`
**Schedule:** 1st and 15th of every month
**Log:** `/tmp/strategist_competitors.log`

**What it does:** Pings competitor websites (Ema Peter, Martin Knowles, Fyfe Photography, Andrew Fyfe) to check they're online and measure page size (rough proxy for content changes).

**What to monitor manually:** New portfolio additions, pricing changes, award wins, blog content, social media frequency.

**Why this matters:** If a competitor adds 5 new projects while your portfolio is static, you're falling behind in search rankings.

### Mode: `attribution`
**Schedule:** Sunday 6:00 PM (1 hour before Sunday Command)
**Log:** `/tmp/strategist_attribution.log`

**What it does:** Pulls all GHL contacts. Groups by source field. Shows lead count per source with top tags. Helps answer: "Where are my leads actually coming from?"

**Why before Sunday Command:** So when you read the weekly review, you already have attribution context.

**Your action:** Make sure every new GHL contact has a source tag. The data is only as good as the tagging.

---

## 8. SUNDAY COMMAND

**Script:** `tools/sunday_command.py`
**Schedule:** Sunday 7:00 PM
**Log:** `/tmp/sunday_command.log`
**Delivers:** 3 Telegram messages

### What it does
Full weekly business review pulling from every system.

### Message 1 — Numbers
- Revenue YTD vs $125,000 target (includes recurring estimate)
- This month's revenue
- Gap remaining and required monthly pace
- Outstanding/overdue invoices
- Pipeline: total value, deals by category (hot/warm/nurture), stale count

### Message 2 — Campaigns & Finance
- Cold email campaign status (all active campaigns)
- Cash flow: monthly burn (~$7,200), recurring revenue ($1,417.50), gap to breakeven
- LOC balance and interest
- FHSA and tax reminders

### Message 3 — Week Ahead & Actions
- Calendar events for Mon-Sun (from Google Calendar)
- Top 3 priorities (revenue-weighted)
- Weekly insight: one data-driven observation about what's working or not

### When it sends
Always. This is your CEO dashboard — it arrives every Sunday at 7pm so you start Monday prepared.

---

## Shared Infrastructure

### agent_utils.py
All agents import from this shared module:
- `send_telegram(text)` — sends HTML message, auto-splits at 4096 chars
- `ghl_get(endpoint, params)` — authenticated GHL API call
- `get_ghl_contacts()`, `get_ghl_opportunities()`, `get_ghl_invoices()` — GHL helpers
- `instantly_get(endpoint, params)` — authenticated Instantly API call
- `get_instantly_campaigns()`, `get_instantly_replies()` — Instantly helpers
- `search_gmail(query, max_results)` — Gmail search via API
- `get_today_events()`, `get_week_events()` — Google Calendar via REST
- `get_google_creds()` — OAuth token management

### Environment (.env)
```
GHL_API_KEY=pit-xxx
GHL_LOCATION_ID=6Nlxml1Rtjj35EjoKuLO
INSTANTLY_API_KEY=xxx
TELEGRAM_BOT_TOKEN=8186928770:xxx (falls back to hardcoded)
TELEGRAM_CHAT_ID=8780007312 (falls back to hardcoded)
```

### Google OAuth (token.json)
Scopes: spreadsheets, drive, gmail.compose, gmail.readonly, calendar.readonly
Re-auth command (run in terminal if Calendar stops working):
```bash
cd ~/Documents/Claude && python3 -c "from google_auth_oauthlib.flow import InstalledAppFlow; flow = InstalledAppFlow.from_client_secrets_file('credentials.json', ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/gmail.compose','https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/calendar.readonly']); creds = flow.run_local_server(port=0); open('token.json','w').write(creds.to_json()); print('Done')"
```

---

## Daily Timeline

```
6:00 AM   📱 DM Prep (10 IG DMs ready)
6:00 AM   👁️ Watchdog health check
6:30 AM   📸 Content Operator (MWF — today's caption)
7:00 AM   ☀️ Morning Command (full briefing)
8:00 AM   📝 Follow-Up Drafter (Tue/Thu — stale deal drafts)
8:00 AM   📨 Reply Classifier (+ repeats every 2hrs until 6pm)
9:00 AM   📡 Domain check (Instantly health)
9:00 AM   💳 Invoice Chaser (Wed/Fri)
9:00 AM   🧾 Expenses (Mon)
9:00 AM   📋 Retainer check (1st of month)
9:00 AM   📊 Tax reminders (1st + 15th)
10:00 AM  📊 Campaign analysis (Mon/Thu)
10:00 AM  ⭐ Reviews (Wed)
10:00 AM  🔄 Leads (Sat)
10:00 AM  📈 Win/Loss (1st of month)
11:00 AM  🔍 Competitors (1st + 15th)
2:00 PM   💰 Cost-Share (Fri)
5:00 PM   📦 Delivery tracker
6:00 PM   📍 GBP monitor
6:00 PM   📊 Attribution (Sun)
7:00 PM   📊 Sunday Command (Sun)
8:00 PM   📸 Shoot Prep (if shoot tomorrow)
10:00 PM  👁️ Watchdog health check (last of day)
```

## Troubleshooting

**Agent didn't fire:**
1. Was Mac asleep? Check: `pmset -g log | grep -i wake`
2. Check log: `cat /tmp/[agent_name].log`
3. Run manually: `python3 tools/[script].py [mode]`

**Gmail/Calendar 403 error:**
Token expired or missing scope. Run the re-auth command above.

**GHL API empty response:**
Check API key in `.env`. Verify at GHL dashboard that private integration is active.

**Instantly 401:**
API key may have changed. Update in `.env`.

**Telegram not delivering:**
Test: `curl -s "https://api.telegram.org/bot8186928770:AAHdsaUe761y7W-1j-0VQoIxfBVCpla19_8/getMe"`
If that fails, bot token may be revoked. Create new bot via @BotFather.

**Cron not running at all:**
macOS may need permission: System Settings → Privacy & Security → Full Disk Access → add Terminal/iTerm.
