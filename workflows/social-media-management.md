# Social Media Management Workflow

Master SOP for running Matt Anthony Photography's social media operation across Instagram, LinkedIn, Pinterest, and the website journal.

---

## Objective

Maintain a consistent, high-quality social media presence that drives B2B client acquisition and portfolio visibility across all platforms. Turn every completed shoot into 3-6 months of content with minimal ongoing effort.

---

## Required Inputs

- Delivered project images (web-sized exports from Dropbox)
- Project metadata: client name, project name, location, architect, builder, designer, notable trades
- Client testimonials (when available)
- BTS footage from shoot days (phone camera folder)
- Access to scheduling tool (Postiz MCP, Buffer, or manual)
- Access to Pinterest business account

## Tools

| Tool | What it does |
|------|-------------|
| `tools/social_media_manager.py` | Central engine: `ingest`, `plan`, `brief`, `report` |
| `tools/carousel_builder.py` | AI-curated carousel sets with slide-by-slide narratives |
| `tools/reel_planner.py` | Reel concepts, shot lists, scripts, audio suggestions |
| `tools/generate_captions.py` | Vision-enhanced captions (sees actual photos while writing) |
| `tools/resize_images.py` | AI-analyzed smart crops with gravity-based positioning |
| `tools/content_calendar.py` | Google Sheet creation, population, status tracking |

## Expected Outputs

- 14-20 posts/week across all platforms
- 4 carousel sets per project (3.1x engagement vs singles)
- 4-6 Reel concepts per project (2.5x reach driver)
- Monthly analytics review with AI-powered strategy recommendations
- Daily briefings on scheduled content and engagement tasks

---

## Weekly Posting Schedule

Optimized for 2026 algorithm priorities: Saves (25%), DM shares (20%), meaningful comments (15%).
Content mix: 60-70% Reels (reach), 20-30% Carousels (engagement), 10% Singles (grid aesthetic).

| Day | Instagram | LinkedIn | Pinterest | Stories |
|-----|-----------|----------|-----------|---------|
| Monday | Carousel (Project Reveal) | Document carousel (Project Story) | 5 pins | If shooting |
| Tuesday | Reel (BTS or Before/After) | Text post (Industry Insight) | — | If shooting |
| Wednesday | — | — | 5 pins | Optional |
| Thursday | Carousel (Educational or Detail) | Client Spotlight or Educational | 5 pins | If shooting |
| Friday | Reel (Process or Reveal) | Personal/Contrarian take | 5 pins | Optional |
| Saturday | Single image or throwback | — | 3 pins | Optional |

**Totals:** Instagram 4-5/week, LinkedIn 3-4/week, Pinterest 23 pins/week, Stories daily when active.

**Algorithm notes:**
- Carousels get 3.1x more engagement and 2x more saves than singles
- Reels drive 2.5x more reach — essential for discovery
- Instagram DM shares are 50% more powerful than any other signal
- LinkedIn document carousels get 11.2x more impressions than text
- First-hour engagement is decisive — post when audience is active, respond immediately

---

## Content Production Cycle

### Phase A: Project Ingest (Day of delivery — one command)

Run the full pipeline:

```bash
python tools/social_media_manager.py ingest \
  --project-dir "Photo Assets/Client/Project" \
  --project "Project Name" \
  --client "Builder Name" \
  --location "Location, BC" \
  --architect "Architect Name" \
  --features "feature 1, feature 2" \
  --trades "@builder_handle @architect_handle" \
  --website "https://mattanthonyphoto.com/project-slug"
```

This automatically:
1. **Analyzes every image** with Claude Vision (composition, subject, focal point, hero score)
2. **Smart-crops for all platforms** using gravity-based positioning (no blind center crops)
3. **Picks the right Instagram format per image** (landscape/square/portrait — not forced 4:5)
4. **Curates 3-4 carousel sets** with slide-by-slide narratives
5. **Generates vision-enhanced captions** (Claude sees the actual photos while writing)
6. **Creates a 4-week content plan** mapped to the posting schedule
7. **Plans 4-6 Reel concepts** with shot lists, scripts, and audio suggestions

**Output structure:**
```
Project/
  originals/          — Source images
  social/
    instagram/        — Smart-cropped (right ratio per image)
    stories/          — 9:16 with letterboxing where needed
    linkedin/         — 1.91:1 landscape
    pinterest/        — 2:3 (only images that work vertically)
    web/              — 16:9 journal
    manifest.json     — Full image analysis
    carousel-plan.json — Carousel sets with captions
    content-plan.json — 4-week posting calendar
    reel-plans.json   — Reel concepts and scripts
  captions/           — Standalone captions
```

**Manual follow-up:**
- Review phone camera roll for BTS footage
- Screen-capture 30-60 seconds of retouching for timelapse Reel
- Pull any drone footage clips

### Phase B: Content Batching (Within 1 week of delivery)

Block 2-3 hours. Work through the full repurposing chain for this project:

**Immediate posts (schedule for week 1-2):**

| # | Content Piece | Platform | Template Reference |
|---|--------------|----------|--------------------|
| 1 | Hero carousel (8-10 images) | Instagram | caption-templates.md → Project Reveal |
| 2 | Project story document carousel (PDF) | LinkedIn | caption-templates.md → LinkedIn Project Story |
| 3 | BTS Reel (15-30 sec) | Instagram | caption-templates.md → Behind the Scenes |
| 4 | 5-8 individual project pins | Pinterest | caption-templates.md → Pinterest Project Pin |
| 5 | Instagram Story series (3-5 slides) | Instagram Stories | Casual — "on location at..." or "new project delivered" |

**Week 2-3 posts:**

| # | Content Piece | Platform | Template Reference |
|---|--------------|----------|--------------------|
| 6 | Client tag post (1-2 hero images) | Instagram | Designed for client reshare |
| 7 | Educational post using this project | Instagram + LinkedIn | caption-templates.md → Educational |
| 8 | Detail/material close-up (single image) | Instagram | caption-templates.md → Project Detail |
| 9 | Before/after carousel or Reel | Instagram | caption-templates.md → Before/After |
| 10 | 3-5 more Pinterest pins (different images, different boards) | Pinterest | caption-templates.md → Pinterest Project Pin |

**Week 4+ posts:**

| # | Content Piece | Platform | Template Reference |
|---|--------------|----------|--------------------|
| 11 | Journal post (800-1500 words) | Website | SEO-optimized, links to service pages |
| 12 | Journal-derived Pinterest pins (3-5) | Pinterest | Educational Pin template |
| 13 | Testimonial graphic (when received) | Instagram + LinkedIn | caption-templates.md → Client Testimonial |

**Ongoing / Seasonal:**

| # | Content Piece | Platform | When |
|---|--------------|----------|------|
| 14 | Throwback re-share | Instagram | 3-6 months later, seasonal tie-in |
| 15 | Case study (if strong project) | LinkedIn + proposals | When story is complete |
| 16 | Award submission collateral | LinkedIn | Award season |

**Writing captions:**
- Open `hooks-scripts-library.md` — pick hooks by content pillar
- Open `caption-templates.md` — fill in the template
- Open `hashtag-system.md` — grab the pre-built set for this content type (rotate A/B)
- Write all captions in one sitting, save to a Google Sheet or scheduling tool draft

### Phase C: Scheduling (Same session as batching)

1. Load all images and captions into scheduling tool
2. Map to the weekly posting schedule above
3. Spread content across 2-4 weeks so one project doesn't flood the feed
4. Interleave with content from other projects and pillar types
5. Set Pinterest pins to auto-publish daily (3-5/day spread across the day)

### Phase D: Daily Engagement (10 minutes/day)

1. **Check notifications** — respond to all comments on your posts (2 min)
2. **LinkedIn engagement** — comment on 3-5 posts from architects, builders, developers in your network. Meaningful comments, not "Great work!" (5 min)
3. **Instagram Stories** — post 1-2 if shooting or have casual content (2 min)
4. **LinkedIn connection requests** — send 2-3 personalized requests to new prospects (1 min)

### Phase E: Weekly Review (15 minutes, Friday)

1. Check next week's scheduled posts — anything need adjusting?
2. Review this week's top-performing posts — what hook/format worked?
3. Fill any gaps in next week's schedule with evergreen or throwback content
4. Note any client wins, testimonials, or events to incorporate

### Phase F: Monthly Review (1 hour, first Monday of month)

See `analytics-dashboard.md` for the full review template. Key actions:
1. Pull metrics from all platforms
2. Compare to targets
3. Identify top 3 performing posts — what made them work?
4. Identify bottom 3 — what fell flat?
5. Adjust next month's content mix based on findings
6. Update hashtag rotation if any sets are underperforming
7. Plan any seasonal or event-tied content for the month ahead

---

## Content Calendar Management

### Calendar Structure (Google Sheets or ClickUp)

| Column | Purpose |
|--------|---------|
| Date | Scheduled publish date |
| Platform | IG / LinkedIn / Pinterest / Journal |
| Content Type | Carousel / Reel / Single / Document / Pin / Story / Journal |
| Pillar | Showcase / BTS / Client / Educational / Personal |
| Project | Which project this content comes from |
| Caption | Full caption text |
| Hashtag Set | Which pre-built set (e.g., "Reveal Set A") |
| Image Files | File names or links to assets |
| Status | Draft / Scheduled / Published |
| Performance | Engagement rate, saves, shares (filled post-publish) |

### Backlog Management

Maintain a running backlog of content ideas:
- Evergreen posts that can fill gaps (educational, throwbacks)
- Seasonal content planned 1 month ahead
- Client testimonials waiting to be designed
- Journal post topics in the pipeline

---

## Approval Flow (For Client-Tagged Content)

Before publishing any post that tags a client or uses their testimonial:

1. Draft the post with caption and images
2. Send to client for review via email: "Quick heads up — planning to share your project on [platform]. Here's the post. Let me know if you'd like any changes."
3. Wait for approval (or assume approved after 48 hours if you have a standing agreement)
4. Publish

For your own content (educational, BTS, personal) — no approval needed. Publish directly.

---

## Edge Cases

**No new projects to post:**
- Pull from the backlog — educational content, throwbacks, personal posts
- Reshare older projects with a new angle ("Revisiting this project 6 months later...")
- Create process/educational content that doesn't require new images

**Client asks you not to post their project:**
- Respect immediately. Remove from all scheduled posts across all platforms.
- Note in project metadata so it doesn't get re-queued later.

**A post performs unusually well:**
- Create a follow-up post within 48 hours while momentum is up
- Same project, different angle or deeper dive
- Pin the post to your IG profile if it's a carousel

**A post performs poorly:**
- Don't delete it — that looks worse than low engagement
- Analyze: was it the hook, the timing, the format, or the content?
- Note the learning in your monthly review

**Seasonal crunch (too many projects at once):**
- Prioritize the most visually striking or highest-profile client
- Stagger the rest — you have 3-6 months of runway per project
- Never sacrifice quality for quantity — skip a posting day rather than post weak content
