# mattanthonyphoto.com — Deployment Guide
## March 19, 2026

---

## Pre-Deployment

1. **Back up current site**: Squarespace > Settings > Advanced > Import/Export
2. **Have Google Search Console access ready**
3. All code blocks are in `business/website/code-blocks/` as both `.html` and `.txt` files
4. Use the `.txt` files for easy copy-paste into Squarespace

---

## Step 1: Sitewide Header (DO THIS FIRST)

1. Go to **Settings > Advanced > Code Injection > Header**
2. Delete everything currently there
3. Open `sitewide-header.txt`
4. Select all (Cmd+A), copy (Cmd+C)
5. Paste into the Header field (Cmd+V)
6. **Save**

**Verify:** Visit any page — nav should show "Creative Partner" (not "Visual Partner Retainer"), Projects link should work, header goes solid on scroll.

---

## Step 2: Custom CSS

1. Go to **Design > Custom CSS**
2. Replace everything with:

```css
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400&family=DM+Sans:wght@300;400;500&family=Josefin+Sans:wght@700&display=swap');

body { background: #1a1a18 !important; }

#header, header, .header {
  display: none !important;
  height: 0 !important;
  visibility: hidden !important;
  overflow: hidden !important;
}

#footer, footer, .footer-wrapper, [data-section-type="footer"] {
  display: none !important;
  height: 0 !important;
}

.sqs-announcement-bar-dropzone { display: none !important; }
.item-pagination { display: none !important; }
.page-title-wrapper, .page-description-wrapper, .collection-item-title { display: none !important; }

#page, #sections {
  background: transparent !important;
  max-width: none !important;
  padding: 0 !important;
}

.page-section, .page-section .content-wrapper {
  min-height: 0 !important;
  padding: 0 !important;
  max-width: none !important;
}

.fluid-engine {
  display: block !important;
  grid-template-columns: none !important;
  grid-template-rows: none !important;
}

.fe-block {
  position: relative !important;
  grid-area: auto !important;
  width: 100% !important;
}

.sqs-block-code {
  padding: 0 !important;
  margin: 0 !important;
  max-width: none !important;
  width: 100% !important;
}

.sqs-block-code .sqs-block-content {
  padding: 0 !important;
  max-width: none !important;
}
```

3. **Save**

---

## Step 3: Deploy Homepage

1. Go to the homepage in Squarespace editor
2. Click the code block
3. Delete all existing code
4. Open `homepage.txt`, select all, copy
5. Paste into code block
6. **Save**

**Verify:** Hero with "Documenting design intent", 3x3 project grid, nav works, buttons gold, testimonials visible, footer at bottom.

---

## Step 4: Deploy Service Pages

For each page: edit the code block, delete old code, paste from the `.txt` file, save.

| Page | File | Notes |
|------|------|-------|
| /project-photography | `project-photography.txt` | |
| /award-publication-imagery | `award-publication-imagery.txt` | |
| /construction-team-content | `build-team-content.txt` | **Fixes broken page** |
| /creative-partner | `creative-partner.txt` | **New page — create in Squarespace first** |

**For Creative Partner (new page):**
1. In Squarespace, create a new blank page
2. Set the URL slug to `creative-partner`
3. Add a Code Block
4. Paste `creative-partner.txt`
5. Save

---

## Step 5: Deploy Core Pages

| Page | File |
|------|------|
| /bio | `bio.txt` |
| /process | `process.txt` |
| /faqs | `faqs.txt` |
| /contact | `contact.txt` |
| /journal | `journal.txt` |

---

## Step 6: Deploy Case Studies

| Page | File |
|------|------|
| /summerhill-fine-homes | `summerhill-fine-homes.txt` |
| /balmoral-construction | `balmoral-construction.txt` |
| /sitelines-architecture | `sitelines-architecture.txt` |
| /the-window-merchant | `the-window-merchant.txt` |
| /lrd-studio-interior-design | `lrd-studio-interior-design.txt` |

---

## Step 7: Deploy Project Pages

| Page | File |
|------|------|
| /the-perch-sunshine-coast | `the-perch-sunshine-coast.txt` |
| /warbler-whistler | `warbler-whistler.txt` |
| /fitzsimmons-whistler | `fitzsimmons-whistler.txt` |
| /fraser-valley-vista | `fraser-valley-vista.txt` |
| /seventh-day-adventist-bc-headquarters | `seventh-day-adventist-bc-headquarters.txt` |
| /pitt-meadows-residence | `pitt-meadows-residence.txt` |
| /tranquil-retreat | `tranquil-retreat.txt` |
| /browns-residence | `browns-residence.txt` |
| /net-zero-build-whistler | `net-zero-build-whistler.txt` |
| /silver-star-residence | `silver-star-residence.txt` |
| /sugarloaf-residence | `sugarloaf-residence.txt` |
| /eagle-residence | `eagle-residence.txt` |
| /wakefield-rooftop-oasis | `wakefield-rooftop-oasis.txt` |
| /gambier-island-residence | `gambier-island-residence.txt` |
| /art-deco-reno | `art-deco-reno.txt` |
| /sunridge-whistler | `sunridge-whistler.txt` |
| /west-10th-vancouver | `west-10th-vancouver.txt` |
| /balsam-way | `balsam-way.txt` |
| /sunset-beach | `sunset-beach.txt` |

---

## Step 8: Deploy Location Pages

| Page | File |
|------|------|
| /squamish-architectural-photography | `squamish-architectural-photography.txt` |
| /whistler-architectural-photography | `whistler-architectural-photography.txt` |

---

## Step 9: Redirects & Cleanup

In **Settings > Advanced > URL Mappings**, add:
```
/visual-partner-retainer -> /creative-partner 301
```

**No-index these pages** (Page Settings > SEO > Hide from search):
- /project-intake-form
- /pricing-guide-thank-you

**Set to Draft or delete** (stale pages):
- /services/project-one-f5w4d-absrg
- /services/jobsite-progression-photography
- /services/team-headshots-photography
- /services/architectural-interiors-photography

---

## Step 10: Google Search Console

1. Go to Google Search Console
2. Submit sitemap: `https://www.mattanthonyphoto.com/sitemap.xml`
3. Request indexing for priority pages:
   - Homepage
   - 4 service pages
   - 5 case studies
   - 7 location pages
   - Journal

---

## Post-Deployment Checklist

For each page verify:
- [ ] Hero image loads with title overlaid correctly (not pushed to bottom)
- [ ] Nav shows "Creative Partner" not "Visual Partner Retainer"
- [ ] Projects link goes to /projects (not /projects-1)
- [ ] "Book a Discovery Call" button is gold with dark text
- [ ] "Get Pricing" link appears and works
- [ ] Footer renders at bottom with correct links
- [ ] No Squarespace "Next Project" overlay bleeding through
- [ ] No Squarespace page title appearing outside the code block
- [ ] Images load (check gallery section)
- [ ] Mobile: nav toggle works, text doesn't overflow

---

## What Each Code Block Contains

Every page includes:
- Squarespace element hiding CSS (item-pagination, page-title-wrapper, etc.)
- Page-specific CSS with proper prefix
- Meta description + canonical + OG tags (at bottom of file)
- Page-specific JSON-LD schema (at bottom of file)
- Descriptive alt text on all images
- loading="lazy" on below-fold images
- "Get Pricing" secondary CTA + footer link
- Creative Partner naming (not Visual Partner Retainer)
- Fixed /projects links (not /projects-1)
- Fixed footer LinkedIn rel="noopener"
