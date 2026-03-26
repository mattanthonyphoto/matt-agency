# Daily Outreach Machine

## Trigger
Matt says: "run my morning briefing" or "what should I do for outreach today"

## Daily Routine (15-20 min)

### Step 1: Refresh signals + read briefing (2 min)
```bash
python3 tools/morning_briefing.py briefing
```
This automatically pulls fresh Instantly data and syncs the Pipeline before showing the briefing. Use `--skip-refresh` if you already ran it recently.

The briefing shows:
- **URGENT**: Replies that need a response today
- **ACTION**: Follow-ups due (plan sent 5+ days) and multi-openers (3+ opens, ready for a plan)
- **WATCH**: Mild signals, no action needed
- **STALE**: 14+ days no movement, consider archiving

### Step 2: Handle replies (5-10 min)
For each URGENT item:
1. Open Gmail, read the reply
2. Respond personally — reference their company, keep it conversational
3. If positive: offer a call ("Would 15 minutes this week work?")
4. Update Pipeline status to "In Conversation" or "Meeting Booked"

### Step 3: Send plans to warm leads (5-10 min)
For each ACTION item that says "Generate marketing plan":
```bash
python3 tools/warm_lead_plan.py \
  --company "Company Name" --owner "Owner Name" \
  --website "https://their-site.com" --email "owner@company.com" \
  --location "City BC"
```
This runs the full pipeline:
1. Crawls their website (site audit)
2. Builds a personalized marketing plan config
3. Generates HTML and publishes to GitHub Pages
4. Updates the Pipeline tab with plan URL and sent date
5. Outputs a ready-to-send DM message

Send the plan via email or Instagram DM with a short personal note.

### Step 4: Send follow-up nudges (2 min)
For each ACTION item that says "Send nudge":
- Open the plan URL from the briefing
- Send a 2-line follow-up email:
  > "Hey [Name], wanted to make sure the marketing playbook landed. Let me know if any of it resonated — happy to walk through it."

### Step 5: Update Pipeline
After all actions, update any status changes directly in the Pipeline tab:
- Replied and responded → "In Conversation"
- Call booked → "Meeting Booked"
- Sent a plan → already updated by warm_lead_plan.py
- No interest after follow-up → "Not Interested"

## Weekly Review (Friday, 10 min)

```bash
python3 tools/morning_briefing.py stats
```

Review:
- **Stale leads (14+ days)**: Archive or send final follow-up
- **Pipeline health**: How many active, how many plans sent, reply rate
- **Next ICP**: If capacity allows, deploy Interior Designers campaign in Instantly
- **Instantly dashboard**: Check overall open rates and deliverability

## Manual Pipeline Additions

For leads from Instagram, referrals, or events — add directly to the Pipeline tab:
- Fill Company, Contact, ICP, Email
- Set Channel to "Instagram" or "Referral"
- Set Status to the current state

## Tools Reference

| Command | What it does |
|---------|-------------|
| `python3 tools/instantly_monitor.py pull-leads --campaign all` | Pull engagement data from Instantly, update Output Sheet |
| `python3 tools/instantly_monitor.py sync-pipeline` | Sync warm leads to Pipeline tab |
| `python3 tools/instantly_monitor.py warm-leads` | Return warm leads as JSON |
| `python3 tools/morning_briefing.py briefing` | Full morning briefing (auto-refreshes) |
| `python3 tools/morning_briefing.py follow-ups` | Just the follow-up list |
| `python3 tools/morning_briefing.py stats` | Pipeline summary stats |
| `python3 tools/warm_lead_plan.py --company X --owner Y --website Z --email E` | One-command plan generation |

## Architecture

```
Instantly (sends emails automatically)
    |
    v
instantly_monitor.py (pulls engagement data)
    |
    v
Output Sheet col L (Status) --> Pipeline tab (warm leads only)
    |
    v
morning_briefing.py (reads Pipeline, prioritizes)
    |
    v
Matt's action list (3-5 items)
    |
    v
warm_lead_plan.py (for "generate plan" actions)
    |
    ├── site_audit.py (crawl website)
    ├── batch_plans.py build_config (create plan config)
    ├── generate_marketing_plan.py (render HTML)
    ├── publish_proposal.py (push to GitHub Pages)
    └── Pipeline tab (update Plan Sent + Plan URL)
```
