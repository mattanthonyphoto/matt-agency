# Social Media System — Activation Report & Setup Guide

Everything is built. This document walks you through what exists, what's ready to use today, and exactly how to get each piece running and tested.

---

## What Was Built

### 19 files across 3 layers:

**Strategy Layer (8 files in `business/marketing/`)**

| File | What It Does |
|------|-------------|
| `content-strategy.md` | Master strategy — pillars, platform rules, repurposing chain, video strategy, metrics |
| `caption-templates.md` | Fill-in-the-blank caption frameworks for every post type on every platform |
| `hooks-scripts-library.md` | 53 proven hooks + 6 universal hook formulas + full scripts by pillar |
| `linkedin-b2b-playbook.md` | LinkedIn profile optimization, content schedule, client acquisition playbook |
| `pinterest-playbook.md` | Account setup, 11 board structures, pin SEO, posting cadence, growth timeline |
| `hashtag-system.md` | 5-tier system, 80+ hashtags, 10 pre-built copy-paste rotation groups |
| `analytics-dashboard.md` | KPIs by platform, benchmarks, monthly review template, revenue attribution |
| `email-templates.md` | Pre-existing — unchanged |

**Operations Layer (4 files in `workflows/`)**

| File | What It Does |
|------|-------------|
| `social-media-management.md` | Master SOP — one-command project ingest, weekly schedule, daily routines |
| `content-batching.md` | Step-by-step: one shoot → 15-25 content pieces |
| `social-media-automation.md` | n8n workflow spec — scheduling, analytics, daily briefings, Postiz/Metricool options |
| `social-media-activation.md` | This file — setup guide and activation checklist |

**Tools Layer (6 files in `tools/`)**

| Tool | What It Does |
|------|-------------|
| `social_media_manager.py` | Central engine: `ingest` (full pipeline), `plan` (4-week calendar), `brief` (daily), `report` (monthly) |
| `carousel_builder.py` | AI-curated carousel sets with slide-by-slide narratives using Claude Vision |
| `reel_planner.py` | Reel concepts, shot lists, scripts, audio suggestions (8 formats) |
| `generate_captions.py` | Vision-enhanced captions — Claude sees actual photos while writing |
| `resize_images.py` | AI-analyzed smart crops with gravity-based positioning per image |
| `content_calendar.py` | Google Sheet creation, population from content plans, status tracking |

---

## What's Ready to Use Right Now (No Setup Required)

These work today, just by reading them:

1. **All strategy documents** — Open `content-strategy.md` as your hub. It links to everything else.
2. **Hooks & caption templates** — Next time you're writing a post, open `hooks-scripts-library.md` + `caption-templates.md` side by side. Pick a hook, fill in the template.
3. **Hashtag groups** — Open `hashtag-system.md`, scroll to "Pre-Built Hashtag Groups", copy the set that matches your post type.
4. **Image resize tool** — Works right now on any image. No API keys needed.
5. **Content batching process** — Follow `content-batching.md` step by step on your next project delivery.

---

## Step-by-Step Activation

### Step 1: Test the Image Resize Tool (5 minutes)

This requires zero setup — Pillow is already installed.

**Test with a real project photo:**
```bash
# Resize a single image for all platforms
python3 tools/resize_images.py resize \
  --input /path/to/any/project-photo.jpg \
  --output-dir .tmp/resize-test/
```

**Expected output:**
```
Resizing: /path/to/any/project-photo.jpg
  ✓ Instagram feed (4:5 portrait): photo_ig.jpg (XXX KB)
  ✓ Instagram Story / Reel cover (9:16): photo_story.jpg (XXX KB)
  ✓ LinkedIn single image (1.91:1 landscape): photo_li.jpg (XXX KB)
  ✓ LinkedIn document carousel (4:5 portrait): photo_li_doc.jpg (XXX KB)
  ✓ Pinterest standard pin (2:3 portrait): photo_pin.jpg (XXX KB)
  ✓ Website / journal (16:9 landscape): photo_web.jpg (XXX KB)
```

**Verify:** Open `.tmp/resize-test/` and check each subfolder. Confirm the crops look good — center-weighted cropping works well for architectural shots but check that nothing critical is clipped on any extreme compositions.

**Test batch mode with SEO filenames:**
```bash
python3 tools/resize_images.py batch \
  --input-dir /path/to/a/delivered/project/folder/ \
  --output-dir .tmp/batch-test/ \
  --seo-prefix "west-coast-modern-home-squamish-bc"
```

**Verify:** Files should be named `west-coast-modern-home-squamish-bc-01_ig.jpg`, `west-coast-modern-home-squamish-bc-01_pin.jpg`, etc. This naming convention helps Pinterest and Google image search.

**Test folder organizer:**
```bash
python3 tools/resize_images.py organize \
  --project-dir .tmp/test-project/
```

**Verify:** Should create `social/instagram/`, `social/linkedin/`, `social/pinterest/`, `social/reels/`, `social/stories/` inside the project directory.

**✅ If all three pass, the image pipeline is operational.**

---

### Step 2: Set Up the Caption Generator (10 minutes)

**2a. Get your Anthropic API key:**
1. Go to console.anthropic.com
2. Sign in or create an account
3. Go to API Keys → Create Key
4. Copy the key (starts with `sk-ant-`)

**2b. Add it to your `.env`:**
```bash
# Open .env and add this line:
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**2c. Test with a real project:**
```bash
python3 tools/generate_captions.py generate \
  --project "The Perch" \
  --client "Balmoral Construction" \
  --location "Sunshine Coast" \
  --architect "Sitelines Architecture" \
  --features "cantilevered living space, floor-to-ceiling glazing, ocean views" \
  --trades "@balmoral_construction @sitelines_arch"
```

**Expected output:** 7 captions printed to the terminal — one for each platform/type:
- Instagram Carousel
- Instagram Reel
- Instagram Detail/Single
- Instagram BTS
- LinkedIn Project Story
- LinkedIn Industry Insight
- Pinterest Pin (title + description + alt text)

**2d. Test saving to file:**
```bash
python3 tools/generate_captions.py generate \
  --project "The Perch" \
  --client "Balmoral Construction" \
  --location "Sunshine Coast" \
  --architect "Sitelines Architecture" \
  --features "cantilevered living, floor-to-ceiling glazing, ocean views" \
  --output .tmp/perch-captions.json
```

**Verify:** Open `.tmp/perch-captions.json` — should contain all captions in a structured JSON file.

**2e. Test single caption generation:**
```bash
python3 tools/generate_captions.py single \
  --project "The Perch" \
  --client "Balmoral Construction" \
  --location "Sunshine Coast" \
  --platform linkedin \
  --type insight
```

**Verify:** Should output just one LinkedIn industry insight post.

**2f. Review the output quality:**
- Do the captions match your brand voice? (professional but warm, no hype, no exclamation marks)
- Are the hooks strong? (not "New work: The Perch for Balmoral" — should be curiosity gaps or story entries)
- Is the LinkedIn caption B2B-angled? (talking about the builder's business, not just the design)
- Does the Pinterest pin have a keyword-rich title and 100-200 word description?

If the tone is off, let me know and I'll adjust the brand voice prompt in the tool.

**✅ If captions generate and the voice is right, the caption tool is operational.**

---

### Step 3: Set Up Pinterest Account (20 minutes)

This is manual but high-leverage — Pinterest is passive traffic once set up.

**3a. Convert to Business Account:**
1. Log into Pinterest as @mattanthonyphoto
2. Settings → Account management → Convert to business account (free)
3. Claim your website: mattanthonyphoto.com

**3b. Verify Rich Pins:**
1. Go to developers.pinterest.com/tools/url-debugger/
2. Enter one of your project page URLs
3. Should show title, description, and link pulled from your Squarespace metadata
4. If not working, Rich Pins may need to be applied for (Pinterest reviews within 24 hours)

**3c. Create the 11 core boards** (from `pinterest-playbook.md`):

| # | Board Name |
|---|-----------|
| 1 | West Coast Modern Architecture |
| 2 | Custom Home Interiors |
| 3 | Architectural Photography Portfolio |
| 4 | Kitchen Design Inspiration |
| 5 | Modern Bathroom Design |
| 6 | Timber Frame & Wood Architecture |
| 7 | Mountain Home Architecture |
| 8 | Coastal Home Design |
| 9 | Architectural Details & Materials |
| 10 | Behind the Scenes — Architecture Photography |
| 11 | Construction Progress Photography |

For each board: add a keyword-rich description (templates in `pinterest-playbook.md`).

**3d. Pin your first 20-30 images:**
- Pull from your strongest 3-4 projects
- Use `resize_images.py` to create 2:3 Pinterest crops
- Write titles and descriptions using `caption-templates.md` → Pinterest templates
- Each pin links to the specific project page on mattanthonyphoto.com
- Spread across multiple boards

**✅ Once boards are created and first pins are live, Pinterest is operational.**

---

### Step 4: Optimize Your LinkedIn Profile (15 minutes)

Follow the checklist in `linkedin-b2b-playbook.md` → Profile Optimization:

- [ ] **Headline:** Change from "Architectural Photographer" to something like "Documenting design intent for builders, architects, and designers across British Columbia"
- [ ] **Banner image:** Your single strongest portfolio shot, wide format
- [ ] **About section:** Rewrite using the template in the playbook
- [ ] **Featured section:** Pin 3-4 items (strongest case study, a journal post, your website)
- [ ] **Request 3 recommendations** from past clients (Summerhill, Balmoral, Sitelines are good candidates)

**✅ Once profile is updated, LinkedIn B2B strategy is operational.**

---

### Step 5: Run Your First Full Content Batch (2.5 hours)

Pick your most recent completed project and run the full `content-batching.md` process:

**5a. Prepare assets (30 min):**
```bash
# Create the folder structure
python3 tools/resize_images.py organize \
  --project-dir /path/to/project/

# Batch resize all delivered images
python3 tools/resize_images.py batch \
  --input-dir /path/to/project/delivered/ \
  --output-dir /path/to/project/social/ \
  --seo-prefix "project-style-location-bc"
```

**5b. Generate captions (5 min + 60 min editing):**
```bash
# Generate all platform captions
python3 tools/generate_captions.py generate \
  --project "Project Name" \
  --client "Builder Name" \
  --location "Location" \
  --architect "Architect Name" \
  --features "feature 1, feature 2, feature 3" \
  --trades "@trade1 @trade2" \
  --output .tmp/project-captions.json
```

Then open the output, review each caption, and edit to taste. The AI gets you 80% there — your voice and project knowledge get it to 100%.

**5c. Write remaining captions manually (30 min):**
Some pieces need your personal touch:
- Client tag post (should feel personal, not AI-generated)
- BTS Reel caption (should reference what actually happened on the shoot)
- Educational angle (pick something specific you noticed about this project)

Use `hooks-scripts-library.md` for hooks and `caption-templates.md` for structure.

**5d. Schedule everything (30 min):**
For now, schedule manually in whatever tool you're using (ClickUp, or post natively). Map to the weekly schedule in `social-media-management.md`:
- Week 1: Hero carousel (IG), document carousel (LI), BTS Reel (IG), Pinterest pins
- Week 2: Client tag post, educational post, detail shots, more pins
- Week 3-4: Journal post, testimonial (when received), remaining pins

**✅ If you complete one full batch, the entire content production system is validated.**

---

### Step 6: Start the Daily Engagement Routine (10 min/day)

Starting tomorrow. From `social-media-management.md`:

1. **Check notifications** — respond to all comments (2 min)
2. **LinkedIn: comment on 3-5 posts** from architects, builders, developers. Meaningful comments. (5 min)
3. **Instagram Stories** — post if you have casual content (2 min)
4. **LinkedIn: send 2-3 connection requests** with personalized notes from `linkedin-b2b-playbook.md` templates (1 min)

---

### Step 7: Set Up Postiz (30 minutes) — When Ready to Automate Scheduling

This is optional — you can run the system manually forever. Postiz just removes the scheduling friction.

**7a. Deploy Postiz (self-hosted, free):**
```bash
docker run -d -p 5000:5000 ghcr.io/gitroomhq/postiz-app
```

**7b. Connect your social accounts:**
- Connect: Instagram (@mattanthonyphoto), LinkedIn (personal profile), Pinterest in the Postiz dashboard

**7c. Add Postiz MCP to Claude Code:**
```bash
claude mcp add postiz http://your-server:5000/api/mcp/YOUR_API_KEY
```

**7d. Test with a real post:**
Schedule one Instagram post via the Postiz dashboard first. Confirm it publishes correctly. Then try via the MCP to schedule directly from Claude Code.

**✅ Once Postiz is connected and tested, scheduling automation is operational.**

---

### Step 8: Create the Content Calendar Google Sheet (20 minutes) — When Ready for Batch Automation

Create a new Google Sheet with these columns (from `social-media-automation.md`):

| Col | Header |
|-----|--------|
| A | Project Name |
| B | Client/Builder |
| C | Location |
| D | Architect/Designer |
| E | Standout Features |
| F | Notable Trades |
| G | Testimonial |
| H | Image URLs |
| I | Status |
| J | IG Carousel Caption |
| K | IG Reel Caption |
| L | LinkedIn Caption |
| M | Pinterest Title |
| N | Pinterest Description |
| O | Pinterest Alt Text |
| P | Scheduled Date |
| Q | IG Engagement |
| R | LI Impressions |
| S | Pinterest Clicks |

**Test the batch caption generator:**
1. Add 1-2 projects to the sheet (columns A-H)
2. Set Status (column I) to anything
3. Create a blank "Generated Captions" tab
4. Run:
```bash
python3 tools/generate_captions.py batch \
  --sheet-id "YOUR_SHEET_ID" \
  --tab "Sheet1" \
  --output-tab "Generated Captions"
```

**Verify:** The "Generated Captions" tab should have all platform captions for each project.

**✅ Once the sheet is working with the batch tool, the content calendar is operational.**

---

### Step 9: Build the n8n Workflows (2-3 hours) — Final Automation

This is the last step. Only do this after everything above is tested and running smoothly.

Follow the spec in `social-media-automation.md`:
1. Build Workflow 1 (Caption Generation) on your n8n instance at `n8n.srv1277163.hstgr.cloud`
2. Test with one project row
3. Build Workflow 2 (Postiz Publishing)
4. Test with one scheduled post
5. Build Workflow 3 (Weekly Analytics Pull)
6. Test on a Monday

**✅ Once all 3 n8n workflows are deployed, the system is fully automated.**

---

## Monthly Operating Cost (Fully Automated)

| Item | Cost |
|------|------|
| Postiz (self-hosted) | $0 |
| Claude API (Sonnet, ~50 batches/mo) | $5-10/mo |
| n8n (existing instance) | $0 |
| Google Sheets | $0 |
| Pinterest | $0 |
| **Total** | **$5-10/mo** |

---

## Time Investment Summary

| Step | Time | When |
|------|------|------|
| 1. Test image resize | 5 min | Today |
| 2. Set up caption generator | 10 min | Today |
| 3. Set up Pinterest | 20 min | Today or tomorrow |
| 4. Optimize LinkedIn profile | 15 min | Today or tomorrow |
| 5. First full content batch | 2.5 hours | Next project delivery |
| 6. Daily engagement routine | 10 min/day | Starting tomorrow |
| 7. Set up Postiz | 30 min | When ready |
| 8. Content calendar sheet | 20 min | When ready |
| 9. n8n workflows | 2-3 hours | When everything else is stable |

**Total to get fully running: ~4-5 hours spread across a few days.**
**Ongoing: ~10 min/day engagement + 2.5 hours per project batch.**

---

## First Month Checklist

**Week 1:**
- [ ] Test image resize tool with a real project photo
- [ ] Add ANTHROPIC_API_KEY to .env and test caption generator
- [ ] Update LinkedIn profile (headline, banner, about, featured)
- [ ] Create Pinterest business account and 11 boards
- [ ] Pin first 20-30 images to Pinterest

**Week 2:**
- [ ] Run first full content batch on your most recent project
- [ ] Start daily 10-minute engagement routine
- [ ] Schedule first week of posts (manually or via Postiz)
- [ ] Request 3 LinkedIn recommendations from past clients

**Week 3:**
- [ ] Set up Postiz and connect all 3 channels
- [ ] Create content calendar Google Sheet
- [ ] Test batch caption generation from the sheet
- [ ] Pin 5 more images/day to Pinterest (building volume)

**Week 4:**
- [ ] Pull first round of analytics (follow template in `analytics-dashboard.md`)
- [ ] Review what's working, what's not
- [ ] Adjust hooks and content mix based on data
- [ ] Plan next month's content based on upcoming shoots

**End of Month 1:**
- [ ] Build n8n workflows if manual process feels ready to automate
- [ ] Complete first monthly review using the template
