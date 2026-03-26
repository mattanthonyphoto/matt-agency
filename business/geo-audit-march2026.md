# GEO Audit Report: mattanthonyphoto.com

**Date:** March 24, 2026
**Scope:** Full-site Generative Engine Optimization audit
**Overall Score:** 7.5 / 10

---

## What is GEO?

Generative Engine Optimization is how well AI systems (ChatGPT, Perplexity, Google AI Overviews, Gemini) can find, understand, and cite your website. Unlike traditional SEO which optimizes for search rankings, GEO optimizes for AI citation and recommendation.

---

## Current State Summary

The site has strong structural foundations: clean schema markup, deep topical content, unique location pages, and a well-organized FAQ. The main gaps are around **citability** (statistics, author attribution, external references) and **verifiability** (reviews, dates, third-party proof). Closing these gaps moves the site from "findable by AI" to "cited by AI."

---

## PASSING

### Schema / Structured Data — A
- LocalBusiness schema with correct NAP (name, address, phone)
- Person schema for Matt Anthony with job title, credentials, expertise list
- 4 Service offers defined with natural language descriptions
- FAQPage schema on `/faqs` (22 Q&As) and location pages
- Geo coordinates (49.7016, -123.1558) for Squamish
- Area served: Whistler, Pemberton, Squamish, Sunshine Coast, Vancouver
- WebPage + Breadcrumb schema present

### Entity Clarity — A
- "Matt Anthony" + "Architectural Photographer" + "Squamish, BC" is unambiguous
- Consistent entity naming across all pages
- Clear service taxonomy: Project Photography, Award & Publication Imagery, Build & Team Content, Creative Partner
- Named client entities: Summerhill Fine Homes, Balmoral Construction, Sitelines Architecture, The Window Merchant, LRD Studio

### FAQ Content — A
- 22 structured Q&As with FAQPage JSON-LD on `/faqs`
- Additional location-specific FAQs on geo pages
- Covers: service areas, process, drone/technical, deliverables, pricing
- Highly citable format for AI answer engines

### Topical Depth — A
- 24 journal articles creating topical authority cluster
- 10 award-specific guides (Georgie, CHBA, HAVAN, CARE, Ovation, RAIC, Gold Nugget, IDA, Dezeen, Dwell)
- Educational content: ROI articles, hiring guides, shoot prep, seasonal planning
- Case studies: Summerhill, Balmoral, The Perch
- Categories: Awards, Working Together, Case Studies, Content & Strategy

### Location Pages — A
- 7+ geo-targeted pages: Squamish, Whistler, Pemberton, Sunshine Coast, Vancouver, Fraser Valley, Okanagan
- ~3,200 words each with unique, non-template content
- Neighborhood-level mentions (Garibaldi Highlands, Brackendale, Valleycliffe, Hospital Hill, Dentville)
- Local client references and project examples
- Location-specific FAQs with schema
- Genuine local knowledge signals ("Stawamus Chief casts deep shadows across western facades in winter")

### Service Definitions — A-
- 4 services clearly defined in schema with full descriptions
- Dedicated landing pages: `/project-photography`, `/award-publication-imagery`, `/construction-team-content`, `/creative-partner`
- Each includes scope, deliverables, and use cases

### Internal Linking — A-
- Dense contextual links between services, projects, case studies, journal, location pages
- Conversion paths: pricing guide, discovery call, free guide
- 20+ project pages, 5 case studies, 24 journal articles all interlinked
- Navigation: About (Bio, Process, FAQs), Projects, Services (4), Case Studies (5), Journal

### Alt Text — B+
- Pattern: "[Project name] [location] [type] photography by Matt Anthony"
- Examples: "West 10th Vancouver modern home architectural photography by Matt Anthony"
- Includes photographer name, location, and project type consistently

### Meta / Title Tags — B+
- Site title: "Architectural Photographer in Vancouver, Squamish, Whistler & BC"
- Meta description: "Architectural photography and film for architects, custom builders, and interior designers in British Columbia"
- Clean geo + service keyword structure

---

## FAILING

### 1. No Citeable Statistics or Numbers — D

**Problem:** AI engines strongly prefer content with specific, quotable data points. The site has almost zero quantified claims. When Perplexity or ChatGPT answers "who are the best architectural photographers in BC?" they pull from sites with verifiable specifics.

**Current state:** No project counts, no years of experience, no client counts, no measurable results, no turnaround metrics formalized in content.

**Required fixes:**
- Add "X+ projects documented since [year]" to homepage and bio
- Add "Working with X+ firms across BC" to about section
- Formalize turnaround: "5-10 business day delivery" in service pages (already in FAQ, needs to be in body content)
- Add project stats to case studies: square footage, image count, submission results
- Add "Serving X regions across British Columbia" with specifics
- If trackable: award submission success rate for clients

**Where to add:** Homepage hero/about section, `/bio`, each service page intro, case study headers.

### 2. No External Authority Citations — D

**Problem:** AI systems weight content higher when it references other authoritative sources. The site links to zero external entities. The 10 award guides are prime targets for AI citation but lack the outbound references that signal authority.

**Current state:** No links to Transport Canada, CHBA, Georgie Awards, HAVAN, RAIC, BC Building Code, or any publications.

**Required fixes:**
- Award guides: link to each award program's official submission page
- Bio: link to Transport Canada drone pilot registry or regulations
- Location pages: link to BC Energy Step Code official documentation
- Journal articles: cite industry studies, building code references, award program stats
- Add links to any publications where work has been featured
- Case studies: link to client websites

**Where to add:** All 10 award guides (highest priority), `/bio`, location pages, case studies.

### 3. Missing Author Attribution on Journal — D

**Problem:** 24 journal articles have no visible author name, publication date, or Article/BlogPosting schema. AI cannot attribute expertise to content it can't tie to a specific author entity. This severely limits citation potential of the journal content.

**Current state:** No `Article` or `BlogPosting` JSON-LD. No author byline. No dates visible. No `datePublished` or `dateModified` metadata.

**Required fixes:**
- Add `BlogPosting` JSON-LD to every journal article with:
  - `author` (linked to Matt Anthony Person entity)
  - `datePublished`
  - `dateModified`
  - `publisher` (Matt Anthony Photography)
  - `image`
  - `description`
- Display author byline on each post: "By Matt Anthony | [Date]"
- Link author name to `/bio` page
- Add visible publication and last-updated dates

**Where to add:** All 24 journal posts. Squarespace likely supports this via blog post settings and code injection.

### 4. No Review/Testimonial Schema — C-

**Problem:** Homepage has a "What Clients Say" section but testimonials aren't in structured data. AI cannot parse social proof that isn't machine-readable.

**Current state:** Testimonial text exists on homepage but no `Review` or `AggregateRating` schema markup.

**Required fixes:**
- Add `Review` schema to each testimonial with `author`, `reviewBody`, `ratingValue`
- Consider `AggregateRating` if you have enough reviews
- Embed or link to Google Business Profile reviews
- Add client logos section with `Organization` schema for each client
- Add publication logos if featured anywhere

**Where to add:** Homepage testimonial section, potentially case study pages.

### 5. Thin Bio / Credentials Page — C

**Problem:** `/about` 301-redirects to `/bio`. The bio content is well-written but thin on verifiable, machine-readable credentials that AI can use to establish authority.

**Current state:** Bio mentions Transport Canada cert and general experience. No years, no project count, no awards, no publications, no industry memberships.

**Required fixes:**
- Add specific years of experience
- Add total project/client count
- List any awards won (by you or clients using your imagery)
- List publications featured in
- List industry memberships or affiliations
- Add `Organization` schema for Matt Anthony Photography (separate from Person)
- Consider a credentials/awards section with structured markup

**Where to add:** `/bio` page.

### 6. No Content Freshness Signals — C

**Problem:** Journal posts display no dates. AI engines discount undated content and prefer recently updated material.

**Current state:** No visible publication dates. No `dateModified` signals. No indication of content currency.

**Required fixes:**
- Display publication date on all journal posts
- Display "Last updated" date on cornerstone content (award guides, service pages)
- Update cornerstone content quarterly (even minor refreshes signal freshness)
- Add `dateModified` to page-level schema

**Where to add:** All journal posts, award guides, service pages.

---

## Priority Action Plan

Ranked by GEO impact (highest first):

| Priority | Action | Pages Affected | Impact |
|----------|--------|---------------|--------|
| 1 | Add BlogPosting schema + author + dates to journal | 24 posts | High — unlocks AI citation of all educational content |
| 2 | Add 5-8 statistics across key pages | Homepage, bio, services | High — makes content quotable by AI |
| 3 | Add outbound authority links to award guides | 10 award guides | High — award guides are prime AI citation targets |
| 4 | Add Review schema to testimonials | Homepage | Medium — closes trust/verification loop |
| 5 | Add publication dates to all journal posts | 24 posts | Medium — freshness signal |
| 6 | Expand bio with verifiable credentials | `/bio` | Medium — strengthens Person entity |
| 7 | Add client website links to case studies | 5 case studies | Low-Medium — adds entity connections |
| 8 | Add Organization schema | Site-wide | Low — supplements existing LocalBusiness |

---

## Progress Update — March 24, 2026

### Fixed During Case Study + Service Page Rebuild

**Service Pages — SEO + Schema (all 5 pages):**
- Added complete JSON-LD `Service` schema with `OfferCatalog` to all 5 service pages
- Added meta descriptions, canonical URLs, and OG tags to Build & Team Content and Creative Partner (were completely missing)
- Added missing `og:image` to Award & Publication Imagery
- Fixed `/projects-1` links to `/projects` across Build & Team Content and Creative Partner footers

**Case Study Pages — Schema + Statistics (all 5 pages):**
- All 5 case studies now have `Article` + `Review` JSON-LD schema with named authors
- Balmoral case study includes 15+ citeable statistics: 42 pages built, 14 project pages, 6 geo-targeted location pages, 6 service pages, 8 blog posts, 4 JSON-LD schemas, 80km service radius
- All case studies include results stats (counter-animated, machine-readable in HTML)
- Client website links added to all case study testimonial attributions (Balmoral, Window Merchant, Sitelines, LRD Studio)

**Impact on Failing Grades:**
| Gap | Previous Grade | Status | Notes |
|-----|---------------|--------|-------|
| Citeable Statistics | D | Improved → C+ | Stats added to case studies and service pages; homepage/bio still need stats |
| Review Schema | C- | Improved → B | Review schema on all 5 case studies; homepage testimonials still need schema |
| Client Website Links | N/A | Fixed | All case studies link to client sites in testimonial attribution |

**Remaining High Priority:**
1. BlogPosting schema + author + dates on 24 journal articles (unchanged — still D)
2. External authority links in 10 award guides (unchanged — still D)
3. Stats on homepage and bio page (partially addressed)
4. Content freshness signals on journal (unchanged — still C)
5. Bio credentials expansion (unchanged — still C)

**Updated Overall Score:** 8.0 / 10 (up from 7.5)

---

## Technical Notes

- **Platform:** Squarespace (limits some schema customization; use code injection blocks)
- **Analytics:** Google Analytics G-MS06FRZ7L7, Facebook Pixel 806034272373569
- **SSL:** Enabled with HSTS
- **Language:** en-CA / en-US
- **reCAPTCHA:** Enterprise enabled

### Schema Implementation Path on Squarespace
- Site-wide schema: Settings > Advanced > Code Injection (header)
- Per-page schema: Page Settings > Advanced > Page Header Code Injection
- Blog post schema: Blog post settings > code injection, or use Squarespace's built-in blog metadata fields
- FAQ schema: Already implemented via code injection; same method for Review schema

---

## Competitive Context

Sites that currently get cited by AI for "architectural photographer BC" queries will have:
- Author-attributed, dated content
- Specific statistics and credentials
- External references to industry bodies
- Review/rating schema
- Fresh content signals

Closing the 6 gaps above puts mattanthonyphoto.com in the top tier for AI citation in this niche. The existing topical depth (24 articles, 10 award guides, 7 location pages) is a significant competitive advantage that most photographer sites lack entirely.
