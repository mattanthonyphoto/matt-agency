# Homepage Mockup Pitch

Generate a redesigned homepage mockup for a builder, then use it as a pitch tool. The mockup shows them what their site *could* look like with professional photography and modern design.

## Objective

Create a personalized, live webpage that looks like a premium redesign of the builder's homepage — using their company name and branding, but with Matt's portfolio photography swapped in. The visual gap between their current site and the mockup is the pitch.

## When to Use

- Cold outreach to builders with outdated websites
- Follow-up to warm leads who haven't converted
- In-person/DM pitches where "show, don't tell" works better than a proposal
- Batch generation for targeted campaigns

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

### Cold Email / DM
> Hey {owner}, I put together a quick homepage concept for {company} — no strings attached, just thought you'd appreciate seeing what's possible with the right imagery.
>
> Take a look: {mockup_url}
>
> If it resonates, I'd love to chat about bringing this kind of visual quality to your actual site. Happy to jump on a quick call.

### Follow-Up (if they viewed it)
> Hey {owner}, noticed you checked out the homepage concept I put together for {company}. What did you think?
>
> That design paired with a proper shoot of your actual projects would be a serious upgrade. Worth a 15-minute call?

### In-Person / Networking
> "I actually mocked up what your homepage could look like — here, take a look." [show on phone]

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

## What Makes This Work

The mockup shows their brand elevated by modern design. Then the showcase section shows what professional photography would add on top. Two gaps exposed in one page:

1. **Design gap** — their current site vs the mockup (layout, typography, structure)
2. **Photography gap** — their current iPhone shots vs Matt's portfolio (the showcase section)

The builder sees both problems and the solution in one scroll.
