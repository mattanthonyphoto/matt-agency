# Homepage Mockup Pitch

Generate a redesigned homepage mockup for a builder, then use it as a pitch tool. The mockup shows them what their site *could* look like with professional photography and modern design.

## Objective

Create a personalized, live webpage that looks like a premium redesign of the builder's homepage — using their company name and branding, but with Matt's portfolio photography swapped in. The visual gap between their current site and the mockup is the pitch.

## When to Use

- Cold outreach to builders with outdated websites
- Follow-up to warm leads who haven't converted
- In-person/DM pitches where "show, don't tell" works better than a proposal
- Batch generation for targeted campaigns
- **Spouse/Office Manager channel** — send mockups to the person who manages the website, not just the builder. They immediately see where the images would go and can sell it internally. See `business/sales/spouse-office-manager-channel.md`

## Priority Targets (from March 2026 audit)

These builders have the biggest gap between build quality and website photography:
1. **CMC Homes** — Luxury Kadenwood builds, placeholder SVGs on website
2. **Vista Coastal Builders** — Squamish, luxury template with no content
3. **Alair Homes Squamish** — Georgie finalist, franchise needs local content
See full audit: `business/sales/builder-website-audit.md`

## Required Inputs

| Input | Required | Source |
|-------|----------|--------|
| Company name | Yes | Lead sheet or discovery |
| Website URL | Yes | Lead sheet or discovery |
| Owner name | No | Lead sheet (defaults to "Owner") |
| Location | No | Auto-detected from audit or defaults to "British Columbia" |

## Quick Start (One Command)

```bash
python3 tools/generate_homepage_mockup.py create \
  --company "Ridgeline Homes" \
  --website "https://ridgelinehomes.ca" \
  --owner "Jake" \
  --location "Squamish BC" \
  --publish
```

This runs the full pipeline:
1. **Audit** their website (pulls company info, project pages, SEO signals)
2. **Build config** with their branding + Matt's portfolio images
3. **Render** HTML from the homepage-mockup template
4. **Publish** to GitHub Pages → returns a live URL

## Manual / Custom Workflow

### Step 1: Scaffold a config
```bash
python3 tools/generate_homepage_mockup.py scaffold --company "Ridgeline Homes"
```
Creates `business/sales/configs/ridgeline-homepage-mockup.json` with defaults.

### Step 2: Customize the config
Edit the JSON to personalize:
- `builder.colors` — match their brand colors if known
- `hero.headline_html` — tailor to their positioning
- `projects` — swap project names to match their actual builds
- `about.paragraphs` — customize to their story
- `stats` — adjust to their actual numbers
- `testimonial` — use a real quote if available

### Step 3: Render
```bash
python3 tools/generate_homepage_mockup.py render business/sales/configs/ridgeline-homepage-mockup.json --publish
```

## Batch Generation

For processing multiple builders from a CSV:
```csv
Company Name,Website,Owner Name,Location
"Ridgeline Homes","https://ridgelinehomes.ca","Jake","Squamish BC"
"Peak Construction","https://peakconstruction.ca","Sarah","Whistler BC"
```

Use the agent to loop through rows, calling `generate_homepage_mockup.py create` for each with `--index N` to rotate image selections.

## Pitch Templates

### Cold Email / DM (to builder)
> Hey {owner}, I put together a quick homepage concept for {company}, no strings attached, just thought you'd appreciate seeing what's possible with the right imagery.
>
> Take a look: {mockup_url}
>
> If it resonates, I'd love to chat about bringing this kind of visual quality to your actual site. Happy to jump on a quick call.

### To Spouse / Office Manager (preferred for $1M-$5M builders)
> Hey {name}, I've been following {company} and your projects are seriously impressive. I put together a quick homepage concept showing what {company}'s site could look like with professional photography.
>
> Take a look: {mockup_url}
>
> I know you're the one keeping the website and social updated, imagine having a full library of images like this ready to go. Happy to chat if it's interesting.

### Follow-Up (if they viewed it)
> Hey {owner}, noticed you checked out the homepage concept I put together for {company}. What did you think?
>
> That design paired with a proper shoot of your actual projects would be a serious upgrade. Worth a 15-minute call?

### In-Person / Networking
> "I actually mocked up what your homepage could look like, here, take a look." [show on phone]

## Config Structure

```json
{
  "builder": {
    "company": "Company Name",
    "slug": "company",
    "location": "City, BC",
    "email": "info@company.com",
    "phone": "",
    "colors": {
      "primary": "#2C3E50",
      "accent": "#C9A96E",
      "light": "#F6F4F0",
      "dark": "#1A1A18"
    }
  },
  "hero": { ... },
  "projects": [ ... ],
  "about": { ... },
  "stats": [ ... ],
  "process": { ... },
  "testimonial": { ... },
  "contact": { ... },
  "images": { "breaks": [ ... ] },
  "photographer": {
    "cta_url": "https://mattanthonyphoto.com/discovery-call",
    "cta_text": "Book a Discovery Call"
  }
}
```

## Output

- **Config:** `business/sales/configs/{slug}-homepage-mockup.json`
- **HTML:** `business/sales/{slug}-homepage-mockup.html`
- **Live URL:** `https://mattanthonyphoto.github.io/matt-proposals/{slug}/{slug}-homepage-mockup.html`

## Key Design Notes

- The mockup uses the builder's actual brand — their images, copy, colors, logo, fonts
- Logo auto-processed: white background removed via PIL, white version generated for dark sections
- A **"The Difference" showcase section** near the bottom displays Matt's portfolio with "Imagine your projects captured like this" — this is the photography pitch
- A **concept banner** at the bottom credits Matt Anthony Photography with a discovery call CTA
- Section nav dots on the right track scroll position
- Animations: scroll reveals, parallax hero, Ken Burns on photo breaks, counter animation on stats
- Single self-contained HTML file — no external dependencies beyond Google Fonts
- Mobile responsive, print-friendly

## Digital Presence Upsell Path

The mockup is the top of a four-rung revenue ladder. Every interaction should move the prospect one rung up.

### The Ladder

| Rung | Offer | Price | Trigger |
|------|-------|-------|---------|
| 1 | **Homepage Mockup** | Free | Cold outreach, networking |
| 2 | **Website Build** | $4,500–$6,500 one-time | They like the mockup, want the real thing |
| 3 | **Digital Presence Retainer** | $1,250/mo (6-month min) | Site is live, needs ongoing SEO + management |
| 4 | **Creative Partner** | $2,500–$3,500/mo (12-month) | They want photography + content + site as one package |

### Rung 2: Website Build — What's Included

- Full site redesign + build on Squarespace
- SEO foundations (meta titles/descriptions, schema markup, page speed)
- Matt's portfolio images as placeholders until they book a shoot (or their existing images cleaned up)
- Mobile responsive, modern layout based on the mockup they already approved
- 30-day post-launch support (bug fixes, copy tweaks, image swaps)
- Hosting: client pays Squarespace directly ($17–$33/mo)

**Scope boundary:** Design + content only. No custom apps, e-commerce, booking systems, or integrations beyond standard Squarespace features. If they need forms or booking, use built-in Squarespace tools or embed GHL.

### Rung 3: Digital Presence Retainer — What's Included

- Ongoing site management (updates, image swaps, new pages as needed)
- 1–2 SEO blog posts/month (targeting local search terms)
- Google Business Profile setup and management
- Monthly performance snapshot (traffic, rankings, lead form submissions)
- Technical SEO maintenance (broken links, speed, schema)
- Priority response within 24 hours

**Not included:** Photography, social media management, paid ads. Those are Creative Partner territory.

**Proof case:** Balmoral Construction — $1,260/mo for web + SEO management, 1+ year running.

### Rung 4: Creative Partner — The Full Package

Everything in Digital Presence, plus:
- Project photography (shoots, editing, delivery)
- Social media content + management
- Award submission packages
- Brand strategy and visual identity
- Content calendar and quarterly planning

See existing retainer models in `business/sales/` for ICP-specific tiers (builder, architect, designer).

### When to Pitch Each Rung

| Signal | Pitch |
|--------|-------|
| They reply to the mockup positively | Website Build |
| They ask "what would it cost to actually do this?" | Website Build |
| Site build is wrapping up, they ask about maintenance | Digital Presence Retainer |
| They mention needing new photos for the site | Photography project → Creative Partner |
| They're already on Digital Presence and keep asking for more | Creative Partner |
| They say "can you just handle all of this?" | Creative Partner |

### Pitch Templates — Website Build

#### After Mockup Interest
> Glad you liked the concept! The good news is that mockup is basically a blueprint — I can build the real thing on Squarespace so you own it, update it yourself, and it actually starts ranking on Google.
>
> For a full site redesign like what you saw, it's $4,500–$6,500 depending on page count. That includes SEO setup, mobile optimization, and 30 days of post-launch support.
>
> Want me to put together a proper scope for {company}?

#### After Website Build Delivery
> Now that the site is live, the next step is making sure people actually find it. SEO takes consistent work — blog posts targeting "{location} custom home builder," keeping your Google Business Profile active, making sure the technical side stays clean.
>
> I offer a Digital Presence retainer at $1,250/mo that covers all of that, plus ongoing site updates whenever you finish a new project. It's basically what I do for Balmoral Construction — their site traffic has grown steadily since we started.
>
> Want me to walk you through what that looks like?

#### Digital Presence → Creative Partner Upsell
> You've got the site and SEO dialed in. The missing piece is the content itself — right now you're working with {iPhone shots / old photos / stock images}. Imagine every project you finish getting shot professionally, those images going straight onto the site, social media, and into award submissions.
>
> That's what my Creative Partner clients get — photography, site, SEO, social, awards, all handled. It's $2,500–$3,500/mo and replaces 3-4 separate vendors. Worth a conversation?

## What Makes This Work

The mockup shows their brand elevated by modern design. Then the showcase section shows what professional photography would add on top. Two gaps exposed in one page:

1. **Design gap** — their current site vs the mockup (layout, typography, structure)
2. **Photography gap** — their current iPhone shots vs Matt's portfolio (the showcase section)

The builder sees both problems and the solution in one scroll.

The Digital Presence ladder means you're never leaving money on the table. Every mockup is a potential $15K–$42K/year client if you walk them up the rungs.
