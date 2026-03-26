# Generate Builder Marketing Plan

## Objective
Create a personalized marketing plan for a custom home builder that serves as a lead magnet. Sent via Instagram DM, it demonstrates expertise and opens the door to a photography conversation.

## When to Use
- Prospecting a builder via Instagram DM
- Builder found through cold research, Instantly leads, or networking
- Any time Matt wants to lead with value instead of a pitch

## Inputs Required
- Builder company name and owner name
- Their website URL
- Their Instagram handle
- Their city/service area

## Process

### 1. Research the Builder (10-15 minutes)
```bash
# Crawl their website for SEO data
python3 tools/site_audit.py https://builder-website.com "Company Name" \
  --location "City BC" --output .tmp/builder-audit.json
```

Also manually check:
- **Instagram:** Follower count, last post date, content quality, posting frequency
- **Google Business Profile:** Review count, photo count, completeness
- **Google Search:** Do they rank for "[type] builder [city]"?
- **Awards:** Any CHBA, Georgie, or other industry recognition?
- **Competitors:** Who else builds in their area? Who's doing marketing well?

### 2. Scaffold the Config
```bash
python3 tools/generate_marketing_plan.py scaffold \
  --client builder-slug \
  --owner "Owner Name" \
  --company "Company Name"
```

Output: `business/sales/configs/builder-slug-marketing-plan.json`

### 3. Fill the Config
Fill in all TODO fields with research data. Key personalization points:

- **Snapshot scores:** Derive from site audit + manual research (0-100 scale)
- **Competitor table:** 3-4 local builders with honest red/amber/green ratings
- **Website checklist:** Mark items as `done: true` if they've already done them
- **GBP section:** Customize based on whether they have GBP or not
- **Social section:** Reference their actual posting history
- **Reviews stats:** Use their actual Google review count
- **Awards section:** Reference awards relevant to their market
- **Closing:** Personalized message using their name and company

### 4. Choose Cover Image
Use a strong architectural exterior from the portfolio. Pick one that matches the builder's market:
- Mountain/ski: Warbler or Fitzsimmons images
- Coastal: Sugarloaf images
- Urban/modern: Eagle Residence images

CDN image URLs are in: `business/website/code-blocks/project-pages/`

### 5. Generate and Publish
```bash
# Generate HTML
python3 tools/generate_marketing_plan.py generate \
  business/sales/configs/builder-slug-marketing-plan.json --publish
```

Live URL: `https://mattanthonyphoto.github.io/matt-proposals/builder-slug/builder-slug-marketing-plan.html`

### 6. Send via Instagram DM

**Template DM:**
> Hey [first name], I put together a marketing playbook specifically for [Company Name]. It covers where you stand right now (website, Google, social, reviews) and a 90-day plan to start winning more of the right clients.
>
> No strings attached, just thought it'd be useful: [URL]

**Key principles:**
- Short, direct, no fluff
- Lead with what's in it for them
- No pitch in the DM itself
- Let the plan do the selling
- Follow up in 3-5 days if no response

## Output
- Published HTML at `matt-proposals/{slug}/{slug}-marketing-plan.html`
- Config saved at `business/sales/configs/{slug}-marketing-plan.json`

## Template
`business/sales/templates/builder-marketing-plan.html.j2`

## Sections (17 total)
1. **Snapshot** — Scores + findings on their current presence
2. **Opportunity** — Competitor comparison table
3. **Gallery 1** — 3-column photo strip (exteriors from different projects)
4. **Website & SEO** — Specific fixes with checklist
5. **Google Business Profile** — Setup/optimization with stats
6. **Social Media** — Content pillars strategy
7. **Gallery 2** — 2-column photo strip (interiors)
8. **Content Engine** — How one shoot feeds every channel (photography woven in)
9. **Reviews** — Systematic review generation with checklist
10. **Referrals** — 3-step referral system
11. **Awards** — Award programs + publications relevant to their market
12. **Case Study** — Balmoral Construction proof: 42 pages, 300+ images, full transformation
13. **Numbers Bar** — Key stats (animated counters)
14. **90-Day Roadmap** — Prioritized action plan with timeline
15. **Monthly Rhythm** — Ongoing cadence (weekly/monthly/quarterly/annual)
16. **CTA Banner** — Strong call-to-action with discovery call button, gold button on dark bg
17. **Closing** — Personal message + next steps

## Notes
- Photography is woven into sections naturally, not pitched directly
- The closing section mentions Matt's services softly — the follow-up DM is where the conversation happens
- Scores should be honest. Inflating bad scores kills credibility. Leading with strengths builds trust.
- Competitor data should be from actual research, not fabricated
- Keep file under 80KB (no base64 images, all from CDN)
