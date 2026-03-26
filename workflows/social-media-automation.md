# Social Media Automation Workflow

n8n workflow specification for automating the social media content pipeline. Connects the Content Calendar (Google Sheets) to Claude API for caption generation, scheduling via Buffer/Postiz, analytics feedback, and daily briefings.

---

## Objective

Automate the full content lifecycle:
1. Generate captions from project metadata (with Vision)
2. Schedule posts across Instagram, LinkedIn, Pinterest
3. Pull engagement analytics back into the tracking sheet
4. Generate daily briefings with what's scheduled and what needs attention
5. Monthly strategy recommendations based on performance data

## Scheduling Options

| Option | Cost | Pros | Cons |
|--------|------|------|------|
| **Postiz (self-hosted)** | $0 | Free, MCP support, 30+ platforms, self-hosted | Requires hosting setup |
| **Buffer** | $18/mo | Simple API, reliable | Limited platforms, no MCP |
| **Metricool MCP** | ~$18/mo | Analytics + scheduling in Claude Code | Requires plan upgrade |
| **Manual** | $0 | Full control | Time-consuming |

**Recommended:** Postiz (free, self-hosted, native MCP) or Metricool (if analytics integration is worth $18/mo).

---

## Architecture Overview

```
Google Sheet (Content Calendar)
  │
  ├── New row detected (poll every 6 hours)
  │
  ├── [Node 1] Read project metadata from row
  │
  ├── [Node 2] Claude API — generate platform-specific captions
  │     ├── Instagram carousel caption
  │     ├── Instagram Reel caption
  │     ├── LinkedIn project story caption
  │     └── Pinterest pin title + description + alt text
  │
  ├── [Node 3] Write generated captions back to sheet for review
  │
  │   ── MANUAL REVIEW GATE ──
  │   (Matt reviews captions in sheet, edits if needed, marks "Approved")
  │
  ├── [Node 4] Approved row detected (poll every 2 hours)
  │
  ├── [Node 5] Buffer API — schedule posts
  │     ├── Instagram post (image + caption)
  │     ├── LinkedIn post (image + caption)
  │     └── Pinterest pin (image + title + description + URL)
  │
  ├── [Node 6] Update sheet status → "Scheduled"
  │
  └── [Node 7] Weekly analytics pull
        ├── Instagram Insights API → engagement data
        └── Write back to sheet Performance column
```

---

## Prerequisites

### API Keys Needed (add to .env)

```
ANTHROPIC_API_KEY=sk-ant-...      # Claude API for caption generation
BUFFER_ACCESS_TOKEN=...            # Buffer API for scheduling
META_ACCESS_TOKEN=...              # Instagram Graph API for analytics
PINTEREST_ACCESS_TOKEN=...         # Pinterest API for analytics (optional)
```

### Accounts to Set Up

1. **Buffer** — Sign up at buffer.com. Connect Instagram, LinkedIn, Pinterest.
   - Free plan: 3 channels, 10 posts/channel queue
   - Essentials plan: $6/mo per channel (recommended — $18/mo for 3 channels)
   - Get API access token from buffer.com/developers

2. **Meta Business Suite** — Required for Instagram Graph API analytics.
   - Connect @mattanthonyphoto Instagram to a Facebook Business page
   - Create a Meta App at developers.facebook.com
   - Request `instagram_basic`, `instagram_manage_insights`, `pages_read_engagement`

3. **Pinterest Business Account** — Already recommended in pinterest-playbook.md
   - API access at developers.pinterest.com

### Google Sheet Structure (Content Calendar)

Create a new Google Sheet or tab with these columns:

| Column | Field | Notes |
|--------|-------|-------|
| A | Project Name | Required |
| B | Client/Builder | For captions and tags |
| C | Location | For captions, hashtags, Pinterest SEO |
| D | Architect/Designer | For tags and credits |
| E | Standout Features | 2-3 key design elements |
| F | Notable Trades | Instagram tags |
| G | Testimonial | Optional — triggers testimonial post type |
| H | Image URLs | Google Drive links to source images |
| I | Status | NEW / GENERATING / REVIEW / APPROVED / SCHEDULED / PUBLISHED |
| J | IG Carousel Caption | Auto-generated, editable |
| K | IG Reel Caption | Auto-generated, editable |
| L | LinkedIn Caption | Auto-generated, editable |
| M | Pinterest Title | Auto-generated, editable |
| N | Pinterest Description | Auto-generated, editable |
| O | Pinterest Alt Text | Auto-generated, editable |
| P | Scheduled Date | When to publish |
| Q | IG Engagement | Auto-filled from analytics |
| R | LI Impressions | Auto-filled from analytics |
| S | Pinterest Clicks | Auto-filled from analytics |

---

## n8n Workflow Nodes

### Workflow 1: Caption Generation

**Trigger:** Google Sheets poll (every 6 hours) → check for rows where Status = "NEW"

**Node 1: Read New Rows**
- Type: Google Sheets
- Operation: Read rows
- Filter: Column I (Status) = "NEW"
- Return: All columns A-H

**Node 2: Set Status to GENERATING**
- Type: Google Sheets
- Operation: Update row
- Set Column I = "GENERATING"

**Node 3: Generate Captions (Claude API)**
- Type: HTTP Request
- Method: POST
- URL: `https://api.anthropic.com/v1/messages`
- Headers:
  - `x-api-key`: `{{$env.ANTHROPIC_API_KEY}}`
  - `anthropic-version`: `2023-06-01`
  - `content-type`: `application/json`
- Body: See prompt template below
- **IMPORTANT:** Do NOT set temperature parameter (causes 400 errors with some n8n versions)

**Prompt template for Node 3:**
```json
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 4096,
  "system": "You are writing social media captions for Matt Anthony Photography, an architectural photographer in Squamish, BC. Brand voice: professional but warm, calm, intentional, no hype. Target audience: architects, builders, designers in British Columbia. Return ONLY a JSON object with these keys: ig_carousel, ig_reel, linkedin_project, pinterest_title, pinterest_description, pinterest_alt_text. No markdown, no code fences, just the JSON.",
  "messages": [
    {
      "role": "user",
      "content": "Generate social media captions for this project:\n\nProject: {{$json.project_name}}\nClient: {{$json.client}}\nLocation: {{$json.location}}\nArchitect: {{$json.architect}}\nFeatures: {{$json.features}}\nTrades: {{$json.trades}}\n\nIG Carousel: Hook first line, 2-3 sentences about the design, CTA, tag collaborators. Under 300 words. No hashtags.\n\nIG Reel: 1-2 sentences max. Hook first.\n\nLinkedIn: B2B angle, first 2 lines are the hook, 3-5 short paragraphs, no links in body, end with 3-5 hashtags.\n\nPinterest Title: 60-80 chars, keyword-first. Format: [Style] [Type] in [Location], BC — [Feature]\n\nPinterest Description: 100-200 words, keyword-rich, end with link to mattanthonyphoto.com.\n\nPinterest Alt Text: One descriptive sentence with keywords."
    }
  ]
}
```

**Node 4: Parse JSON Response**
- Type: Code (JavaScript)
```javascript
const response = JSON.parse($input.first().json.content[0].text);
return [{
  json: {
    ig_carousel: response.ig_carousel,
    ig_reel: response.ig_reel,
    linkedin_project: response.linkedin_project,
    pinterest_title: response.pinterest_title,
    pinterest_description: response.pinterest_description,
    pinterest_alt_text: response.pinterest_alt_text,
    row_number: $input.first().json.row_number,
  }
}];
```

**Node 5: Write Captions to Sheet**
- Type: Google Sheets
- Operation: Update row (by row number)
- Set Columns J-O with generated captions
- Set Column I = "REVIEW"

---

### Workflow 2: Publish Approved Posts

**Trigger:** Google Sheets poll (every 2 hours) → check for rows where Status = "APPROVED" and Scheduled Date <= today

**Node 1: Read Approved Rows**
- Type: Google Sheets
- Filter: Column I = "APPROVED", Column P <= today's date

**Node 2: Post to Instagram via Buffer**
- Type: HTTP Request
- Method: POST
- URL: `https://api.bufferapp.com/1/updates/create.json`
- Body:
```json
{
  "access_token": "{{$env.BUFFER_ACCESS_TOKEN}}",
  "profile_ids": ["{{$env.BUFFER_INSTAGRAM_PROFILE_ID}}"],
  "text": "{{$json.ig_carousel_caption}}",
  "media": {
    "photo": "{{$json.image_url}}"
  },
  "scheduled_at": "{{$json.scheduled_date}}T09:00:00-07:00"
}
```

**Node 3: Post to LinkedIn via Buffer**
- Type: HTTP Request
- Method: POST
- URL: `https://api.bufferapp.com/1/updates/create.json`
- Body:
```json
{
  "access_token": "{{$env.BUFFER_ACCESS_TOKEN}}",
  "profile_ids": ["{{$env.BUFFER_LINKEDIN_PROFILE_ID}}"],
  "text": "{{$json.linkedin_caption}}",
  "media": {
    "photo": "{{$json.image_url}}"
  },
  "scheduled_at": "{{$json.scheduled_date}}T08:30:00-07:00"
}
```

**Node 4: Post to Pinterest via Buffer**
- Type: HTTP Request
- Method: POST
- URL: `https://api.bufferapp.com/1/updates/create.json`
- Body:
```json
{
  "access_token": "{{$env.BUFFER_ACCESS_TOKEN}}",
  "profile_ids": ["{{$env.BUFFER_PINTEREST_PROFILE_ID}}"],
  "text": "{{$json.pinterest_description}}",
  "media": {
    "photo": "{{$json.image_url}}",
    "title": "{{$json.pinterest_title}}",
    "link": "https://mattanthonyphoto.com/projects/{{$json.project_slug}}"
  }
}
```

**Node 5: Update Sheet Status**
- Type: Google Sheets
- Set Column I = "SCHEDULED"

---

### Workflow 3: Weekly Analytics Pull

**Trigger:** Cron — Every Monday at 9am Pacific

**Node 1: Read Published Rows**
- Type: Google Sheets
- Filter: Column I = "PUBLISHED" or "SCHEDULED", last 30 days

**Node 2: Instagram Insights**
- Type: HTTP Request
- For each post (if we have the IG media ID):
- URL: `https://graph.facebook.com/v19.0/{{media_id}}/insights?metric=impressions,reach,engagement,saved,shares&access_token={{$env.META_ACCESS_TOKEN}}`

**Node 3: Write Analytics to Sheet**
- Type: Google Sheets
- Update Columns Q-S with engagement data

---

## Local Tools (Run Manually or Via n8n Execute Command)

### Caption Generator (standalone)

For generating captions without n8n:

```bash
# All platforms at once
python tools/generate_captions.py generate \
  --project "The Perch" \
  --client "Balmoral Construction" \
  --location "Sunshine Coast" \
  --architect "Sitelines Architecture" \
  --features "cantilevered living, floor-to-ceiling glazing, ocean views" \
  --trades "@westcoast_millwork" \
  --output .tmp/the-perch-captions.json

# Single platform
python tools/generate_captions.py single \
  --project "The Perch" \
  --client "Balmoral Construction" \
  --location "Sunshine Coast" \
  --platform linkedin \
  --type project

# Batch from Google Sheet
python tools/generate_captions.py batch \
  --sheet-id "YOUR_CONTENT_CALENDAR_SHEET_ID" \
  --tab "Content Queue" \
  --output-tab "Generated Captions"
```

### Image Resize Pipeline (standalone)

```bash
# List available platform specs
python tools/resize_images.py list

# Create folder structure for a project
python tools/resize_images.py organize \
  --project-dir ./projects/the-perch/

# Resize all images in a folder for all platforms
python tools/resize_images.py batch \
  --input-dir ./projects/the-perch/delivered/ \
  --output-dir ./projects/the-perch/social/ \
  --seo-prefix "west-coast-modern-home-sunshine-coast-bc"

# Resize for specific platforms only
python tools/resize_images.py batch \
  --input-dir ./projects/the-perch/delivered/ \
  --output-dir ./projects/the-perch/social/ \
  --platforms instagram,pinterest

# Resize a single image
python tools/resize_images.py resize \
  --input ./photo.jpg \
  --output-dir ./social/
```

---

## Deployment Steps

### Step 1: API Keys
Add to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
BUFFER_ACCESS_TOKEN=...
BUFFER_INSTAGRAM_PROFILE_ID=...
BUFFER_LINKEDIN_PROFILE_ID=...
BUFFER_PINTEREST_PROFILE_ID=...
META_ACCESS_TOKEN=...
```

### Step 2: Google Sheet
Create the Content Calendar sheet with the column structure above. Share with the service account from `credentials.json`.

### Step 3: Test Caption Generator Locally
```bash
python tools/generate_captions.py generate \
  --project "Test Project" \
  --client "Test Builder" \
  --location "Squamish" \
  --features "timber frame, mountain views"
```

### Step 4: Test Image Resize Locally
```bash
python tools/resize_images.py resize \
  --input /path/to/test-image.jpg \
  --output-dir .tmp/social-test/
```

### Step 5: Buffer Setup
1. Create Buffer account, connect IG/LinkedIn/Pinterest profiles
2. Get access token from Buffer Developer Portal
3. Get profile IDs via: `curl https://api.bufferapp.com/1/profiles.json?access_token=YOUR_TOKEN`
4. Add all IDs to `.env`

### Step 6: Build n8n Workflow
Deploy Workflow 1 (Caption Generation) first. Test with one project. Then deploy Workflow 2 (Publishing) and Workflow 3 (Analytics).

Use the n8n instance at `n8n.srv1277163.hstgr.cloud`.

---

## Known Gotchas (from cold email pipeline experience)

- **Do NOT set temperature via n8n API** — causes 400 errors
- **Do NOT use continueRegularOutput on critical nodes** — can corrupt data flow
- **Vector Store connections are fragile via API** — not relevant here but noted
- **Buffer free plan** limits to 10 posts per channel queue — upgrade to Essentials ($18/mo total) for unlimited queue
- **Instagram carousel posting via Buffer** requires image URLs, not file uploads — host images on Google Drive with public links or use a CDN
- **LinkedIn document carousels (PDFs)** cannot be posted via Buffer API — these still need manual upload. Buffer handles single images and text.
- **Pinterest pin scheduling** via Buffer works but doesn't support all pin types — standard image pins only
- **Meta access tokens expire** — set up a long-lived token (60 days) and add a refresh reminder to your monthly review

---

## Workflow 4: Daily Briefing

**Trigger:** Cron — Every day at 7:30am Pacific

**Node 1: Read Content Calendar**
- Type: Google Sheets
- Read all rows from Content Calendar tab
- Filter: Date = today OR Date within next 7 days OR (Date < today AND Status != PUBLISHED)

**Node 2: Generate Briefing (Claude API)**
- Type: HTTP Request
- POST to `https://api.anthropic.com/v1/messages`
- Prompt: Summarize today's scheduled posts, flag overdue items, suggest engagement actions
- Include: Yesterday's analytics if available

**Node 3: Send Briefing**
- Type: Gmail (via MCP) or n8n Email node
- To: info@mattanthonyphoto.com
- Subject: "Daily Content Brief — [Date]"
- Body: Formatted briefing from Claude

**Alternative:** Run `python tools/social_media_manager.py brief` via n8n Execute Command node.

---

### Workflow 5: Monthly Analytics & Strategy

**Trigger:** Cron — 1st of each month at 9am Pacific

**Node 1: Pull Instagram Insights**
- Type: HTTP Request
- URL: Meta Graph API for last 30 days of post metrics

**Node 2: Pull Pinterest Analytics**
- Type: HTTP Request
- URL: Pinterest Analytics API for last 30 days

**Node 3: Write to Analytics Tab**
- Type: Google Sheets
- Append rows to Analytics tab in Content Calendar

**Node 4: Generate Strategy Report (Claude API)**
- Type: HTTP Request
- Prompt: Analyze last month's performance data, identify top/bottom performers, recommend content mix adjustments
- Include: All analytics data from Node 3

**Node 5: Send Report**
- Type: Gmail
- Subject: "Monthly Social Media Report — [Month]"
- Body: Full report with recommendations

**Alternative:** Run `python tools/social_media_manager.py report` via n8n Execute Command node.

---

## Postiz MCP Setup (Free, Self-Hosted)

If using Postiz instead of Buffer:

1. Deploy Postiz on existing hosting (Docker container):
   ```bash
   docker run -d -p 5000:5000 ghcr.io/gitroomhq/postiz-app
   ```

2. Connect your social accounts (Instagram, LinkedIn, Pinterest) in the Postiz UI

3. Add MCP to Claude Code:
   ```bash
   claude mcp add postiz http://your-server:5000/api/mcp/YOUR_API_KEY
   ```

4. Schedule posts directly from Claude Code terminal

---

## Metricool MCP Setup (Analytics + Scheduling)

1. Sign up at metricool.com (Advanced plan needed for MCP)
2. Connect Instagram, LinkedIn, Pinterest
3. Add to Claude Code:
   ```bash
   claude mcp add --transport http metricool https://ai.metricool.com/mcp
   ```
4. Available commands: schedule posts, pull analytics, competitor data, optimal posting times

---

## Monthly Cost

| Service | Cost |
|---------|------|
| Postiz (self-hosted) | $0 |
| Claude API (Sonnet, ~50 caption batches/mo) | $5-10/mo |
| n8n (existing instance) | $0 |
| Google Sheets | $0 |
| **Total (with Postiz)** | **~$5-10/mo** |

**Or with Buffer:**

| Service | Cost |
|---------|------|
| Buffer Essentials (3 channels) | $18/mo |
| Claude API | $5-10/mo |
| **Total (with Buffer)** | **~$25-30/mo** |
