# Generate & Publish Proposals

## Objective
Go from discovery call to live proposal URL in under an hour.

## Tools
- `tools/generate_proposal.py` — Scaffold configs, generate HTML from templates
- `tools/publish_proposal.py` — Push to GitHub Pages

## The Three-Command Pipeline

### 1. Scaffold a config
```bash
python3 tools/generate_proposal.py scaffold creative-partner \
  --client rdc --owner "Ryan Fauquier" --company "RDC Fine Homes"
```
Creates `business/sales/configs/rdc-creative-partner.json` with all sections pre-filled with TODO placeholders and default pricing.

### 2. Fill in the config
Open the JSON and replace every TODO with client-specific content:
- **Story**: relationship context, the gap, stats
- **Cover**: headline, subtitle, cover image URL
- **Pricing**: adjust tiers, amounts, line items
- **Roadmap**: specific projects, dates, deliverables
- **Images**: pick 3-4 photo break images from the CDN library
- **Awards**: competitor stats, relevant awards
- **Next steps**: personal closing, first project name

Image CDN URLs are in the project page HTML files:
```
business/website/code-blocks/project-pages/warbler-whistler.html
business/website/code-blocks/project-pages/eagle-residence.html
business/website/code-blocks/project-pages/sugarloaf-residence.html
```

### 3. Generate + publish
```bash
python3 tools/generate_proposal.py generate business/sales/configs/rdc-creative-partner.json --publish
```
Generates the HTML, pushes to GitHub Pages, returns a live URL.

## Proposal Types

| Type | Command | Sections |
|------|---------|----------|
| Creative Partner retainer | `scaffold creative-partner` | Story, services, pricing (3 tiers), roadmap, vision, numbers, awards, next steps |
| One-off project | `scaffold project-photography` | Story, services, pricing (flat rate), next steps |

## Config Structure

```
business/sales/
  configs/                    # One JSON per proposal
    balmoral-creative-partner.json
    rdc-creative-partner.json
  templates/
    proposal.html.j2          # Master template (don't edit unless changing design)
```

### Key config fields

| Field | What it controls |
|-------|-----------------|
| `client.slug` | URL path and filename |
| `sections` | Which sections to include, in order |
| `cover.image_url` | Full-bleed cover photo |
| `images.breaks` | Photo breaks between sections (distributed in order) |
| `pricing.tiers` | Number and content of tier cards |
| `roadmap.months` | Pilot timeline entries |

## Common Operations

```bash
# Preview locally (no publish)
python3 tools/generate_proposal.py generate configs/rdc-creative-partner.json
# Then open business/sales/rdc-creative-partner.html in browser

# Re-publish after edits (same URL, overwrites)
python3 tools/generate_proposal.py generate configs/rdc-creative-partner.json --publish

# List all configs
python3 tools/generate_proposal.py list-configs

# List published proposals
python3 tools/publish_proposal.py list

# Remove a published proposal
python3 tools/publish_proposal.py delete rdc/creative-partner-proposal.html
```

## Post-Discovery Call Workflow

1. Finish call, open terminal
2. `scaffold` with client details
3. Fill in config (Claude can help draft the story, roadmap, and framing)
4. Pick images from CDN library
5. `generate --publish`
6. Send URL to client same day
