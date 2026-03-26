# GEO Optimization Workflow

## Objective
Implement all fixes identified in the GEO audit (`business/geo-audit-march2026.md`) to make mattanthonyphoto.com fully optimized for AI citation by generative engines (ChatGPT, Perplexity, Google AI Overviews, Gemini).

## Platform
Squarespace — all schema changes go through code injection (site-wide header or per-page).

## Prerequisites
- Read `business/geo-audit-march2026.md` for full context and current scores
- Access to Squarespace admin for mattanthonyphoto.com
- Current site schema (already has LocalBusiness, Person, FAQPage, Service offers)

---

## Task 1: BlogPosting Schema + Author Attribution (Priority 1)
**Impact:** High — unlocks AI citation of all 24 journal articles

### What to do
Generate `BlogPosting` JSON-LD for each of the 24 journal articles.

### Schema template
```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "[Article Title]",
  "description": "[1-2 sentence summary]",
  "author": {
    "@type": "Person",
    "name": "Matt Anthony",
    "url": "https://www.mattanthonyphoto.com/bio",
    "jobTitle": "Architectural Photographer & Filmmaker"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Matt Anthony Photography",
    "url": "https://www.mattanthonyphoto.com",
    "logo": {
      "@type": "ImageObject",
      "url": "[LOGO_URL]"
    }
  },
  "datePublished": "[YYYY-MM-DD]",
  "dateModified": "[YYYY-MM-DD]",
  "image": "[FEATURED_IMAGE_URL]",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://www.mattanthonyphoto.com/journal/[slug]"
  }
}
```

### Journal articles to cover (24 total)
1. `/journal/roi-professional-architectural-photography-builders`
2. `/journal/georgie-awards-guide`
3. `/journal/havan-awards-guide`
4. `/journal/chba-national-awards-guide`
5. `/care-awards-guide`
6. `/ovation-awards-guide`
7. `/journal/raic-awards-guide`
8. `/journal/architectural-photography-for-publications`
9. `/gold-nugget-awards-guide`
10. `/ida-awards-guide`
11. `/journal/how-to-photograph-your-project-for-award-submissions`
12. `/journal/why-your-award-submission-photos-arent-working`
13. `/journal/what-georgie-award-judges-look-for-submission-photography`
14. `/journal/how-to-prepare-project-architectural-photo-shoot`
15. `/journal/project-photography-vs-real-estate-photography`
16. `/journal/documenting-design-intent-photography-before-build-finished`
17. `/journal/seasonal-considerations-architectural-photography-bc`
18. `/journal/5-details-make-or-break-architectural-interior-photography`
19. `/journal/what-architects-should-look-for-hiring-photographer`
20. `/journal/summerhill-fine-homes-visual-brand-ongoing-photography`
21. `/journal/behind-the-shoot-the-perch-sunshine-coast`
22. `/journal/architectural-photography-whistler-mountain-projects`
23. `/journal/construction-lifestyle-photography-best-social-media-investment-builders`
24. `/journal/how-to-build-visual-library-website-proposals-awards`

### Steps
1. Fetch each article to get: title, description, featured image URL, and estimate publish date from content cues
2. Generate the BlogPosting JSON-LD for each
3. Output as a single file with all 24 code blocks, labeled by page, ready to paste into Squarespace per-page code injection
4. Also generate visible byline HTML/CSS that Matt can add to blog post template: "By Matt Anthony | [Date]"

### Visible author byline (for Squarespace blog template)
Suggest CSS + HTML for a byline block:
```html
<div class="post-byline">
  <span class="post-author">By <a href="/bio">Matt Anthony</a></span>
  <span class="post-date">| March 24, 2026</span>
</div>
```

---

## Task 2: Add Statistics Across Key Pages (Priority 2)
**Impact:** High — makes content quotable by AI

### What to do
Draft specific, factual statistics to add to these pages. **Ask Matt to confirm all numbers before publishing.**

### Pages and suggested placements
- **Homepage** (hero or about section): "X+ projects documented for architects and builders across British Columbia"
- **Homepage** (about section): "Based in Squamish, serving X regions across BC since [year]"
- **`/bio`**: "X years specializing in architectural photography", "X+ completed projects", "Working with X+ firms"
- **Service pages**: "Delivered in 5-10 business days" (already in FAQ, formalize in body copy)
- **Case studies**: Add project stats — square footage, image count delivered, what the images were used for

### Output
A document listing each stat, which page it goes on, and where in the page it should be placed. Flag any numbers that need Matt's confirmation.

---

## Task 3: Outbound Authority Links in Award Guides (Priority 3)
**Impact:** High — award guides are prime AI citation targets

### What to do
Add outbound links to official award program pages, submission portals, and relevant industry bodies.

### Links to add per guide
| Guide | Required outbound links |
|-------|------------------------|
| Georgie Awards | CHBA BC official page, submission portal, judging criteria page |
| HAVAN Awards | HAVAN official page, awards program page |
| CHBA National | CHBA national site, awards categories page |
| CARE Awards | CARE awards official page |
| Ovation Awards | GVHBA Ovation awards page |
| RAIC Awards | RAIC official page, awards program |
| Gold Nugget Awards | PCBC Gold Nugget official page |
| IDA Awards | IDA official page |
| Publications guide | Link to Dezeen submissions, Dwell, ArchDaily submission guidelines |

### Also add across site
- `/bio`: Link to Transport Canada drone regulations
- Location pages: Link to BC Energy Step Code official documentation
- Case studies: Link to each client's website

### Steps
1. Fetch each award guide to find the best insertion points for outbound links
2. Research and verify current URLs for each award program's official pages
3. Output a document with: page, anchor text, URL, and where in the content to insert

---

## Task 4: Review Schema for Testimonials (Priority 4)
**Impact:** Medium — closes trust/verification loop

### What to do
Add `Review` JSON-LD schema to the homepage testimonial section.

### Schema template
```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Matt Anthony Photography",
  "review": [
    {
      "@type": "Review",
      "author": {
        "@type": "Person",
        "name": "[Client Name]"
      },
      "reviewBody": "[Testimonial text]",
      "reviewRating": {
        "@type": "Rating",
        "ratingValue": "5",
        "bestRating": "5"
      }
    }
  ]
}
```

### Steps
1. Fetch homepage to extract exact testimonial text and client names
2. Generate Review schema JSON-LD with all testimonials
3. Output code block ready for Squarespace site-wide code injection

---

## Task 5: Content Freshness — Publication Dates (Priority 5)
**Impact:** Medium — freshness signal for AI

### What to do
- Ensure all blog posts show publication dates (Squarespace blog settings)
- Add `dateModified` to page schema for cornerstone content
- Create a quarterly refresh schedule for award guides (update submission deadlines, add new tips)

### Steps
1. Check if Squarespace blog settings expose dates (Settings > Blog > Post Display)
2. If not natively available, provide CSS to show the date element Squarespace hides by default
3. Output a refresh calendar: which pages to update each quarter and what to update

---

## Task 6: Expand Bio with Verifiable Credentials (Priority 6)
**Impact:** Medium — strengthens Person entity

### What to do
Draft expanded bio content with specific, verifiable details. **All details need Matt's confirmation.**

### Content to draft
- Years in business
- Total projects/clients served
- Notable clients list (already partially there)
- Awards won (by Matt or by clients using his imagery)
- Publications featured in
- Industry memberships or affiliations
- Education/training relevant to photography

### Output
Draft copy for `/bio` page with placeholders for numbers Matt needs to confirm.

---

## Completed Tasks — March 24, 2026

### Task 2 (Statistics) — PARTIALLY COMPLETE
**Service pages** now include citeable statistics in body copy and counter-animated stat strips:
- Services Hub: "19 Projects Documented | 5 Case Studies | 42 Pages Built | 7 Service Areas"
- Project Photography: "19 Projects | 4 Case Studies | 7 Service Areas"
- Build & Team Content: "12 Instagram Posts | 5 Reels | 6 LinkedIn Posts" (per-shoot ROI stats)
- Creative Partner: "42 Pages | 4 Projects | 6 Geo-Targeted Pages | 12+ Months" (Balmoral proof stats)

**Case studies** now include machine-readable statistics in HTML:
- Balmoral: 42 pages, 14 project pages, 6 location pages, 6 service pages, 8 blog posts, 4 JSON-LD schemas
- All 5 case studies have results stat grids with specific numbers

**Still needed:** Stats on homepage hero/about section and `/bio` page. Needs Matt's confirmation on totals.

### Task 4 (Review Schema) — PARTIALLY COMPLETE
**All 5 case studies** now include `Review` JSON-LD schema within their `Article` schema:
- Balmoral: Marc Harvey review
- Summerhill: Kyle Paisley review
- Sitelines: Jade Draper review
- Window Merchant: Jeremy Kirbyson review
- LRD Studio: Lauren Ritz review

**Still needed:** Homepage testimonial section Review schema (site-wide code injection).

### Task 7 (Client Website Links) — COMPLETE
All 5 case studies link to client websites in testimonial attribution:
- balmoralconstruction.com, summerhillfinehomes.com, sitelinesarchitecture.com, thewindowmerchant.com, lrdstudio.ca

### Service Page SEO — COMPLETE
- All 5 service pages now have: meta descriptions, canonical URLs, OG tags (title, description, url, type, image), JSON-LD Service schema with OfferCatalog
- Previously missing on Build & Team Content and Creative Partner (were blank)
- Fixed missing og:image on Award & Publication Imagery

---

## Execution Notes

- **Do not publish anything without Matt's approval** — output all changes as ready-to-paste code blocks and copy drafts
- **Schema changes**: Test with Google Rich Results Test (https://search.google.com/test/rich-results) before deploying
- **Statistics**: Every number must be confirmed by Matt. Use "[X]" as placeholder for unconfirmed figures
- **Outbound links**: Verify all URLs are live before recommending
- **Squarespace constraints**: All schema goes in code injection. Per-page schema in Page Settings > Advanced > Header Code Injection. Site-wide schema in Settings > Advanced > Code Injection (header)

## Success Criteria
- All 24 journal articles have BlogPosting schema with author + dates
- Homepage, bio, and service pages contain 5-8 specific statistics
- All 10 award guides link to official program pages
- Testimonials have Review schema
- Publication dates visible on all journal posts
- Bio page expanded with verifiable credentials
- All schema passes Google Rich Results validation
