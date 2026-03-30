# Balmoral Construction — SEO Meta Reference

Use this document when configuring each page's SEO fields in the Squarespace dashboard.

**Where to set these in Squarespace:**
- Page Settings > SEO > SEO Title (meta title)
- Page Settings > SEO > SEO Description (meta description)
- Page Settings > SEO > URL Slug
- The H1 is already set in the injected code on each page

**Guidelines:**
- Meta titles: Under 60 characters. Primary keyword first, brand last.
- Meta descriptions: Under 160 characters. Include differentiator, location, and CTA.
- Blog post titles include `(2026)` for freshness signals — update annually.
- Location pages lead with `[service] in [city], BC` — the exact query people search.

---

## Audit Summary (March 27, 2026)

**Critical findings:**
- **0 of 41 pages have the recommended meta titles set** — all are using Squarespace auto-generated titles
- **0 of 41 pages have meta descriptions** — every page is missing this entirely
- **7 new pages** added since last reference (Balsam, Wedgewoods, Pinewood, Windline, Land Consultation, Permit Coordination, duplicate blog post)
- **Duplicate blog post** at `/blog/building-in-pemberton-vs-whistler-1` — should be deleted or 301 redirected to `/blog/building-in-pemberton-vs-whistler`
- **Contact URL** is `/contact-2` in Squarespace but links in code point to `/contact` — verify redirect is in place
- **Homepage** is at `/home` in sitemap but should canonical to `/`

**What Squarespace is auto-generating vs what should be set:**

| Page | Current Auto Title | Should Be |
|------|-------------------|-----------|
| `/` | (none/generic) | `Custom Home Builder in Whistler, Pemberton & Squamish \| Balmoral Construction` |
| `/warbler-way` | `Warbler Way Custom Home Whistler — Balmoral Construction` | `Warbler Way — Custom Home in Whistler \| Balmoral Construction` |
| `/whistler-home-builder` | `Whistler Luxury Custom Homes — Balmoral Construction` | `Custom Home Builder in Whistler, BC \| Balmoral Construction` |
| `/services` | `Custom Home Building & Renovation Services — Balmoral Construction` | `Services \| Custom Home Building, Renovations & Contracting \| Balmoral` |

---

## Sitemap Structure

```
balmoralconstruction.com/
│
├── /                              Homepage
├── /about                         About
├── /contact-2                     Contact
├── /reviews                       Reviews
├── /work                          Portfolio Hub
│
├── /services                      Services Hub
│   ├── /custom-home-building      Custom Home Building
│   ├── /home-renovations          Home Renovations
│   ├── /general-contracting       General Contracting
│   ├── /project-management        Project Management
│   ├── /land-consultation         Land Consultation ← NEW
│   └── /permit-coordination       Permit Coordination ← NEW
│
├── /whistler-home-builder         Whistler — Custom Homes
├── /whistler-home-renovations     Whistler — Renovations
├── /pemberton-home-builder        Pemberton — Custom Homes
├── /pemberton-home-renovations    Pemberton — Renovations
├── /squamish-home-builder         Squamish — Custom Homes
├── /squamish-home-renovations     Squamish — Renovations
│
├── /warbler-way                   Project — Whistler
├── /cerulean                      Project — Pemberton
├── /sugarloaf                     Project — Pemberton
├── /white-gold-2                  Project — Whistler
├── /white-gold                    Project — Whistler
├── /fitzsimmons                   Project — Whistler
├── /fitzsimmons-north             Project — Whistler (under construction)
├── /eagle                         Project — Pemberton
├── /mountain-view                 Project — Whistler
├── /drifter                       Project — Whistler
├── /balsam                        Project — Whistler ← NEW
├── /wedgewoods                    Project — Whistler ← NEW
├── /pinewood                      Project — Pemberton ← NEW
├── /windline                      Project — Squamish ← NEW
│
├── /blog                          Blog Hub
│   ├── /blog/how-much-does-it-cost-to-build-a-custom-home-in-whistler
│   ├── /blog/how-much-does-it-cost-to-build-a-custom-home-in-pemberton
│   ├── /blog/building-in-pemberton-vs-whistler
│   ├── /blog/building-in-pemberton-vs-whistler-1  ← DUPLICATE — delete or 301
│   ├── /blog/bc-building-permit-process-explained
│   ├── /blog/bc-energy-step-code-for-homeowners
│   ├── /blog/project-spotlight-warbler-way
│   └── /blog/project-spotlight-sugarloaf
```

**Total: 41 pages (40 unique + 1 duplicate to remove)**

---

## Core Pages

### Homepage `/`
- **Meta Title:** `Custom Home Builder in Whistler, Pemberton & Squamish | Balmoral Construction`
- **Meta Description:** `Boutique custom home builder in the Sea to Sky Corridor. Balmoral Construction builds luxury homes in Whistler, Pemberton & Squamish. 20+ years experience. Talk to us.`
- **H1:** `Custom Home Builder in Whistler, Pemberton & Squamish`

### About `/about`
- **Meta Title:** `About Balmoral Construction | Sea to Sky Custom Home Builder Since 2011`
- **Meta Description:** `Meet the Balmoral team — Marc Harvey, Jeremy Lewis, and Jonny Tweedie. Boutique builder delivering hands-on custom homes in Whistler, Pemberton & Squamish since 2011.`
- **H1:** `About Balmoral Construction`

### Contact `/contact-2`
- **Meta Title:** `Contact Balmoral Construction | Start Your Custom Home Build`
- **Meta Description:** `Ready to build? Contact Balmoral Construction at (604) 907-2237 or marc@balmoralconstruction.com. Based in Pemberton, building across Whistler, Pemberton & Squamish.`
- **H1:** `Start a Conversation`

### Reviews `/reviews`
- **Meta Title:** `Reviews & Testimonials | Balmoral Construction — Whistler & Pemberton`
- **Meta Description:** `Read what our clients say about building with Balmoral Construction. BC New Home Warranty and National Home Warranty registered. Real reviews from Sea to Sky homeowners.`
- **H1:** `Client Reviews`

### Portfolio `/work`
- **Meta Title:** `Our Work | Custom Homes in Whistler & Pemberton | Balmoral Construction`
- **Meta Description:** `14 custom home projects across the Sea to Sky Corridor. Explore our portfolio of completed builds in Whistler, Pemberton & Squamish.`
- **H1:** `Our Work`

---

## Services Pages

### Services Hub `/services`
- **Meta Title:** `Services | Custom Home Building, Renovations & Contracting | Balmoral`
- **Meta Description:** `Full-service custom home building in the Sea to Sky Corridor. Custom homes, renovations, general contracting, and project management in Whistler, Pemberton & Squamish.`
- **H1:** `Our Services`

### Custom Home Building `/custom-home-building`
- **Meta Title:** `Custom Home Building | Whistler, Pemberton & Squamish | Balmoral Construction`
- **Meta Description:** `Concept-to-completion custom home building in the Sea to Sky Corridor. Boutique service, hands-on management, and 20+ years of experience. From land consulting to occupancy.`
- **H1:** `Custom Home Building`

### Home Renovations `/home-renovations`
- **Meta Title:** `Home Renovations | Whistler, Pemberton & Squamish | Balmoral Construction`
- **Meta Description:** `Large-scale home renovations across the Sea to Sky Corridor. Kitchens, bathrooms, full gut renovations, and suite additions built for mountain and coastal climates.`
- **H1:** `Home Renovations`

### General Contracting `/general-contracting`
- **Meta Title:** `General Contracting | Sea to Sky Corridor | Balmoral Construction`
- **Meta Description:** `General contracting for residential projects in Whistler, Pemberton & Squamish. Standard to alternative building methods including ICF construction. Warranty registered.`
- **H1:** `General Contracting`

### Project Management `/project-management`
- **Meta Title:** `Project Management | Custom Home Builds | Balmoral Construction`
- **Meta Description:** `End-to-end project management for custom homes in the Sea to Sky Corridor. Permit coordination, trade management, and daily site presence from start to occupancy.`
- **H1:** `Project Management`

### Land Consultation `/land-consultation`
- **Meta Title:** `Land Consultation | Sea to Sky Property Evaluation | Balmoral Construction`
- **Meta Description:** `Property evaluation before you buy or build in the Sea to Sky Corridor. Lot assessment, site challenges, and build feasibility for Whistler, Pemberton & Squamish land.`
- **H1:** `Land Consultation`

### Permit Coordination `/permit-coordination`
- **Meta Title:** `Building Permit Coordination | Whistler, Pemberton & Squamish | Balmoral`
- **Meta Description:** `Navigate building permits across the Sea to Sky Corridor. RMOW, VOPB, and District of Squamish expertise from application to occupancy. Balmoral handles the process.`
- **H1:** `Building Permit Coordination`

---

## Location Pages

### Whistler — Custom Homes `/whistler-home-builder`
- **Meta Title:** `Custom Home Builder in Whistler, BC | Balmoral Construction`
- **Meta Description:** `Build your custom home in Whistler with Balmoral Construction. Kadenwood, White Gold, Wedgwood — we know every neighbourhood. RMOW permits, snow loads, ski-in/ski-out builds.`
- **H1:** `Custom Home Builder in Whistler, BC`

### Whistler — Renovations `/whistler-home-renovations`
- **Meta Title:** `Home Renovations in Whistler, BC | Balmoral Construction`
- **Meta Description:** `Whistler home renovations by Balmoral Construction. Kitchens, bathrooms, full renovations, and envelope upgrades built for alpine conditions. RMOW permit experts.`
- **H1:** `Home Renovations in Whistler, BC`

### Pemberton — Custom Homes `/pemberton-home-builder`
- **Meta Title:** `Custom Home Builder in Pemberton, BC | Balmoral Construction`
- **Meta Description:** `Pemberton's local custom home builder. Balmoral Construction is based in Pemberton — valley floor, benchlands, and rural properties. VOPB permit specialists.`
- **H1:** `Custom Home Builder in Pemberton, BC`

### Pemberton — Renovations `/pemberton-home-renovations`
- **Meta Title:** `Home Renovations in Pemberton, BC | Balmoral Construction`
- **Meta Description:** `Pemberton home renovations by Balmoral Construction. Heritage farmhouses to modern valley homes — kitchens, suites, full renovations. Local builder, daily site presence.`
- **H1:** `Home Renovations in Pemberton, BC`

### Squamish — Custom Homes `/squamish-home-builder`
- **Meta Title:** `Custom Home Builder in Squamish, BC | Balmoral Construction`
- **Meta Description:** `Custom home building in Squamish by Balmoral Construction. Coastal moisture expertise, District of Squamish permits, and Sea to Sky trade network. Start your build today.`
- **H1:** `Custom Home Builder in Squamish, BC`

### Squamish — Renovations `/squamish-home-renovations`
- **Meta Title:** `Home Renovations in Squamish, BC | Balmoral Construction`
- **Meta Description:** `Squamish home renovations by Balmoral Construction. Rain screen expertise, suite additions, full gut renovations. From Valleycliffe to Garibaldi Highlands.`
- **H1:** `Home Renovations in Squamish, BC`

---

## Project Pages

### Warbler Way `/warbler-way`
- **Meta Title:** `Warbler Way — Custom Home in Whistler | Balmoral Construction`
- **Meta Description:** `Contemporary alpine home in Whistler's Wedgwood neighbourhood. Black metal cladding, cedar accents, and custom millwork. Designed by Shelter Residential Design, built by Balmoral.`
- **H1:** `Warbler Way`

### Cerulean `/cerulean`
- **Meta Title:** `Cerulean — Custom Home in Pemberton | Balmoral Construction`
- **Meta Description:** `Modern custom home in Pemberton with panoramic mountain views. Clean contemporary lines and warm interiors set against Mount Currie and the Lillooet Range. Built by Balmoral.`
- **H1:** `Cerulean`

### Sugarloaf `/sugarloaf`
- **Meta Title:** `Sugarloaf — 4,800 Sq Ft Custom Home in Pemberton | Balmoral Construction`
- **Meta Description:** `4,800 sq ft custom home in Pemberton with Mount Currie views. Stark Architecture, Innotech windows, Blueprint Millwork cabinetry. Built by Balmoral Construction.`
- **H1:** `Sugarloaf`

### White Gold 2 `/white-gold-2`
- **Meta Title:** `White Gold 2 — Custom Home in Whistler | Balmoral Construction`
- **Meta Description:** `The second White Gold collaboration — a refined custom home in Whistler. Evolved design language, tighter material palette, and alpine sensitivity. Built by Balmoral.`
- **H1:** `White Gold 2`

### White Gold `/white-gold`
- **Meta Title:** `White Gold — Custom Home in Whistler | Balmoral Construction`
- **Meta Description:** `The original White Gold custom home in Whistler. Warm materials, alpine sensitivity, and mountain views that set the benchmark. Built by Balmoral Construction.`
- **H1:** `White Gold`

### Fitzsimmons `/fitzsimmons`
- **Meta Title:** `Fitzsimmons — Custom Home in Whistler | Balmoral Construction`
- **Meta Description:** `Modern alpine home on Fitzsimmons Road in Whistler. Disciplined design, clean proportions, and precision construction built without compromise by Balmoral Construction.`
- **H1:** `Fitzsimmons`

### Fitzsimmons North `/fitzsimmons-north`
- **Meta Title:** `Fitzsimmons North — Under Construction in Whistler | Balmoral Construction`
- **Meta Description:** `Custom home currently under construction on Fitzsimmons Road in Whistler. Follow the progress of Balmoral Construction's latest Whistler build.`
- **H1:** `Fitzsimmons North`

### Eagle `/eagle`
- **Meta Title:** `Eagle — ICF Custom Home in Pemberton | Balmoral Construction`
- **Meta Description:** `Insulated concrete form custom home in Pemberton's Benchlands. Non-combustible, wildfire-resistant construction with Innotech windows and Novat millwork. Built by Balmoral.`
- **H1:** `Eagle`

### Mountain View `/mountain-view`
- **Meta Title:** `Mountain View — Custom Home in Whistler | Balmoral Construction`
- **Meta Description:** `Custom home in Whistler with panoramic mountain views. Thoughtful architecture that frames the Coast Mountains from every room. Built by Balmoral Construction.`
- **H1:** `Mountain View`

### Drifter `/drifter`
- **Meta Title:** `Drifter — Custom Home in Whistler | Balmoral Construction`
- **Meta Description:** `Custom home in Whistler built with expert finishing carpentry and attention to detail. Mountain living designed for comfort and durability. Built by Balmoral Construction.`
- **H1:** `Drifter`

### Balsam `/balsam`
- **Meta Title:** `Balsam — 4,000 Sq Ft Custom Home in Whistler | Balmoral Construction`
- **Meta Description:** `4,000 sq ft alpine retreat in Whistler steps from the Village. Vaulted ceilings, wood-burning fireplace, and Innotech windows. Designed by Kat Sullivan, built by Balmoral.`
- **H1:** `Balsam`

### Wedgewoods `/wedgewoods`
- **Meta Title:** `Wedgewoods — 4,500 Sq Ft Rancher in Whistler | Balmoral Construction`
- **Meta Description:** `4,500 sq ft single-storey rancher in Whistler's WedgeWoods with Wedge Mountain views. Maya Wassenberg design, Blueprint millwork, Britt Lothrop interiors. Built by Balmoral.`
- **H1:** `Wedgewoods`

### Pinewood `/pinewood`
- **Meta Title:** `Pinewood — ICF Custom Home in Pemberton | Balmoral Construction`
- **Meta Description:** `3,500 sq ft insulated concrete home on the Pemberton Plateau. Energy-efficient ICF construction, Innotech windows, and Blueprint millwork. Built by Balmoral Construction.`
- **H1:** `Pinewood`

### Windline `/windline`
- **Meta Title:** `Windline — Equestrian Development in Squamish | Balmoral Construction`
- **Meta Description:** `Rural equestrian development in Brackendale, Squamish. Riding arena, barns, and staff housing with modern design and Marvin windows. Built by Balmoral Construction.`
- **H1:** `Windline`

---

## Blog Posts

### Blog Hub `/blog`
- **Meta Title:** `Blog | Custom Home Building Insights | Balmoral Construction`
- **Meta Description:** `Cost guides, building science, permit advice, and project spotlights from Balmoral Construction. Practical knowledge for building in Whistler, Pemberton & Squamish.`
- **H1:** `Blog`

### Cost Guide — Whistler `/blog/how-much-does-it-cost-to-build-a-custom-home-in-whistler`
- **Meta Title:** `How Much Does It Cost to Build a Custom Home in Whistler? (2026)`
- **Meta Description:** `Whistler custom home costs range from $500-$800+ per sq ft. Detailed breakdown of what drives costs — site complexity, snow loads, finishes, and ski access. By Balmoral.`
- **H1:** `How Much Does It Cost to Build a Custom Home in Whistler?`

### Cost Guide — Pemberton `/blog/how-much-does-it-cost-to-build-a-custom-home-in-pemberton`
- **Meta Title:** `How Much Does It Cost to Build a Custom Home in Pemberton? (2026)`
- **Meta Description:** `Pemberton custom home costs range from $400-$600+ per sq ft. Compare to Whistler pricing, understand what drives costs, and plan your budget. By Balmoral Construction.`
- **H1:** `How Much Does It Cost to Build a Custom Home in Pemberton?`

### Pemberton vs Whistler `/blog/building-in-pemberton-vs-whistler`
- **Meta Title:** `Building in Pemberton vs Whistler — Cost, Land & Lifestyle Compared`
- **Meta Description:** `Considering Pemberton or Whistler for your custom home? Compare construction costs, land prices, permits, climate, and lifestyle. Honest guide from a builder who works in both.`
- **H1:** `Building in Pemberton vs Whistler`

### DUPLICATE — Delete `/blog/building-in-pemberton-vs-whistler-1`
- **Action:** Delete this page or set up a 301 redirect to `/blog/building-in-pemberton-vs-whistler`
- **Reason:** Duplicate content hurts SEO. Google may index the wrong version or split ranking signals between both.

### BC Permit Process `/blog/bc-building-permit-process-explained`
- **Meta Title:** `BC Building Permit Process Explained — Sea to Sky Guide (2026)`
- **Meta Description:** `Step-by-step guide to building permits for Whistler (RMOW), Pemberton (VOPB), and Squamish. Timelines, costs, common delays, and how to avoid them. By Balmoral.`
- **H1:** `BC Building Permit Process Explained`

### Energy Step Code `/blog/bc-energy-step-code-for-homeowners`
- **Meta Title:** `BC Energy Step Code for Homeowners — What You Need to Know (2026)`
- **Meta Description:** `BC Energy Step Code explained for homeowners building in the Sea to Sky Corridor. What each step means, costs, rebates, and how it affects your custom home build.`
- **H1:** `BC Energy Step Code for Homeowners`

### Spotlight — Warbler Way `/blog/project-spotlight-warbler-way`
- **Meta Title:** `Project Spotlight: Warbler Way — Custom Home in Whistler | Balmoral`
- **Meta Description:** `Behind the build of Warbler Way in Whistler's Wedgwood neighbourhood. Black metal, cedar, and custom millwork — how Balmoral brought Shelter Residential Design's vision to life.`
- **H1:** `Project Spotlight: Warbler Way`

### Spotlight — Sugarloaf `/blog/project-spotlight-sugarloaf`
- **Meta Title:** `Project Spotlight: Sugarloaf — 4,800 Sq Ft Home in Pemberton | Balmoral`
- **Meta Description:** `Behind the build of Sugarloaf in Pemberton. 4,800 sq ft, Mount Currie views, Stark Architecture design, Innotech windows, Blueprint Millwork. By Balmoral Construction.`
- **H1:** `Project Spotlight: Sugarloaf`

---

## Open Graph Tags (Site-Wide via Squarespace Code Injection)

Add to **Settings > Advanced > Code Injection > Header** for site-wide defaults:

```html
<meta property="og:site_name" content="Balmoral Construction">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@balmoralconstruction">
```

Each page's `og:title`, `og:description`, and `og:image` should be set via the Squarespace SEO panel (Squarespace auto-generates these from the page SEO title, description, and featured image).

---

## Technical SEO Checklist

- [ ] XML sitemap submitted to Google Search Console
- [ ] robots.txt references sitemap: `Sitemap: https://www.balmoralconstruction.com/sitemap.xml`
- [ ] Canonical URLs set (Squarespace handles this automatically)
- [ ] Google Business Profile NAP matches: Balmoral Construction Inc., 1704 Sugarloaf Place, Pemberton, BC V0N 2L3, (604) 907-2237
- [ ] All images use descriptive filenames and alt text (done in code)
- [ ] JSON-LD schema on all pages: HomeAndConstructionBusiness, FAQPage, ImageGallery, BlogPosting
- [ ] llms.txt and ai.txt for AI search optimization
- [ ] 301 redirects configured for any old URL patterns
- [ ] Page load speed: target < 3s (Squarespace CDN handles image delivery)
- [ ] Delete or 301 redirect `/blog/building-in-pemberton-vs-whistler-1` (duplicate)
- [ ] Verify `/home` → `/` redirect is working
- [ ] Verify `/contact` → `/contact-2` redirect is working (or rename slug)
- [ ] Resubmit sitemap after all meta changes are applied

---

*Last updated: 2026-03-27*
