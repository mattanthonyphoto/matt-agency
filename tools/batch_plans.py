"""Batch-generate builder marketing plans from a CSV of leads.

Usage:
    python3 tools/batch_plans.py <input_csv> [--limit N] [--dry-run] [--no-publish]

Input CSV format:
    Company Name,Website,Owner Name,Location
    "Ridgeline Custom Homes","https://ridgelinehomes.ca","Jake Morrison","Squamish BC"

If Owner Name is missing, defaults to "Owner".
If Location is missing, auto-detects from website or defaults to "BC".

Output:
    - Generated configs in business/sales/configs/
    - Published HTML plans on GitHub Pages
    - Results CSV at .tmp/batch-plans-results.csv
    - DM messages ready to copy-paste
"""

import csv
import json
import os
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from tools.site_audit import run_audit
from tools.generate_marketing_plan import generate, scaffold

CONFIG_DIR = os.path.join(BASE_DIR, "business", "sales", "configs")
OUTPUT_DIR = os.path.join(BASE_DIR, "business", "sales")
TMP_DIR = os.path.join(BASE_DIR, ".tmp")

# ─── Portfolio image pool (Squarespace CDN) ───
# Rotating set of images from Matt's portfolio for galleries and breaks
COVER_IMAGES = [
    "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/312b0797-a43a-4a51-906e-f913c78c7b79/fitzsimmons-whistler-architectural-photography-matt-anthony-.jpg-3.jpg",
    "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/64c6702a-78ea-4fe3-a601-78bce7c197a8/warbler-whistler-architectural-photography-matt-anthony-.jpg-5.jpg",
    "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/ef4086f4-81fa-468f-99bf-966ce7d83d89/warbler-whistler-architectural-photography-matt-anthony-.jpg-11.jpg",
    "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/e07b8aac-c1ec-4293-b956-79b41aa39f33/5322-backhouse-web-1.jpg",
]

GALLERY_EXTERIORS = [
    {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/58f835c2-21e3-441c-a6c1-629b91a2afaf/siteline-langley-16.jpg", "alt": "Fraserview Vista — exterior twilight, Langley"},
    {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/98b6bb8c-ede3-4de9-978a-fc8ae91554a6/warbler-whistler-architectural-photography-matt-anthony-.jpg-35.jpg", "alt": "Warbler Residence — rear elevation, Whistler"},
    {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/8149d10c-1661-4e39-80d9-538f24b4123a/warbler-whistler-architectural-photography-matt-anthony-.jpg-33.jpg", "alt": "Warbler Residence — mountain backdrop, Whistler"},
]

GALLERY_INTERIORS = [
    {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/2b3d3270-c8c3-4e1a-954a-4aca41b35b71/sandy-hook-sunshine-coast-architectural-photography-matt-anthony-.jpg-13.jpg", "alt": "Tranquil Retreat — wood ceiling living room"},
    {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/ab8c0b1a-742e-4485-9d50-a19c698594bf/fitzsimmons-whistler-architectural-photography-matt-anthony-.jpg-4.jpg", "alt": "Fitzsimmons Residence — open plan living room"},
    {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/c938566f-ee96-40da-aec4-d51ac9fa7e09/warbler-whistler-architectural-photography-matt-anthony-.jpg-13.jpg", "alt": "Warbler Residence — living room with natural materials"},
    {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/d4768559-4d0d-4403-a58c-02db15d5b177/fitzsimmons-whistler-architectural-photography-matt-anthony-.jpg-42.jpg", "alt": "Fitzsimmons Residence interior — Balmoral Construction"},
]

BREAK_IMAGES = [
    {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/ef4086f4-81fa-468f-99bf-966ce7d83d89/warbler-whistler-architectural-photography-matt-anthony-.jpg-11.jpg", "alt": "Warbler Residence at twilight — Whistler, BC", "caption": "Warbler Residence &middot; Whistler, BC &middot; Matt Anthony Photography"},
    {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/e07b8aac-c1ec-4293-b956-79b41aa39f33/5322-backhouse-web-1.jpg", "alt": "The Perch — modern coastal home, Sunshine Coast", "caption": "The Perch &middot; Sunshine Coast, BC &middot; Matt Anthony Photography"},
    {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/52135c1c-0414-47aa-ba78-6d225bc11f6b/siteline-langley.jpg", "alt": "Fraserview Vista luxury residence — Langley, BC", "caption": "Fraserview Vista &middot; Langley, BC &middot; Matt Anthony Photography"},
    {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/47eefcd4-72ce-4641-8ff0-a4ea2e8b9e12/fitzsimmons-whistler-architectural-photography-matt-anthony-.jpg-19.jpg", "alt": "Fitzsimmons Residence at twilight — Whistler, BC", "caption": "Fitzsimmons Residence &middot; Whistler, BC &middot; Matt Anthony Photography"},
    {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/0e7a6365-526e-4c0e-8b06-4939d5008849/5322-backhouse-web-4.jpg", "alt": "The Perch — suspended fireplace interior", "caption": "The Perch &middot; Sunshine Coast, BC &middot; Matt Anthony Photography"},
    {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/8149d10c-1661-4e39-80d9-538f24b4123a/warbler-whistler-architectural-photography-matt-anthony-.jpg-33.jpg", "alt": "Warbler Residence rear elevation — mountain backdrop", "caption": "Warbler Residence &middot; Whistler, BC &middot; Matt Anthony Photography"},
]

CTA_BG = "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/8a674d33-4176-43dd-89c1-a565c1c3df48/5322-backhouse-web-24.jpg"


def slugify(name):
    """Convert company name to URL-safe slug."""
    slug = name.lower().strip()
    # Remove common suffixes
    for suffix in ["ltd.", "ltd", "inc.", "inc", "corp.", "corp", "group", "construction", "homes", "builders"]:
        slug = re.sub(rf'\b{re.escape(suffix)}\b', '', slug)
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    # Collapse multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    return slug or "builder"


def score_to_grade(score):
    """Convert 0-100 score to letter grade."""
    if score >= 90: return "A"
    if score >= 85: return "A-"
    if score >= 80: return "B+"
    if score >= 75: return "B"
    if score >= 70: return "B-"
    if score >= 65: return "C+"
    if score >= 60: return "C"
    if score >= 55: return "C-"
    if score >= 50: return "D+"
    if score >= 45: return "D"
    if score >= 40: return "D-"
    return "F"


def score_to_color(score):
    """Convert score to traffic light color."""
    if score >= 70: return "good"
    if score >= 50: return "ok"
    return "poor"


def extract_strengths(audit_report):
    """Pull strengths from audit findings (findings are dicts with status/title/detail)."""
    strengths = []
    for category in ["seo", "local", "content", "visual_assets"]:
        for finding in audit_report.get("findings", {}).get(category, []):
            if finding.get("status") == "pass":
                strengths.append(finding.get("title", ""))
    return strengths[:3] if strengths else ["Website is live and accessible"]


def extract_gaps(audit_report):
    """Pull gaps from audit findings (findings are dicts with status/title/detail)."""
    gaps = []
    for category in ["seo", "local", "content", "visual_assets"]:
        for finding in audit_report.get("findings", {}).get(category, []):
            if finding.get("status") == "fail":
                gaps.append(finding.get("title", ""))
    return gaps[:4] if gaps else ["Online presence has room for improvement"]


def build_config(company_name, owner_name, website, location, audit_report, index):
    """Build a complete marketing plan config from audit data."""

    slug = slugify(company_name)
    scores = audit_report.get("scores", {})
    meta = audit_report.get("meta", {})

    # Map audit scores to plan scores
    seo_score = scores.get("seo", {}).get("value", 50)
    local_score = scores.get("local", {}).get("value", 40)
    content_score = scores.get("content", {}).get("value", 45)
    visual_score = scores.get("visual_assets", {}).get("value", 50)

    # Map to plan's 4 categories
    website_seo_val = seo_score
    social_val = min(content_score, 40)  # Conservative — we can't check social from site audit
    google_val = local_score
    visual_val = visual_score

    strengths = extract_strengths(audit_report)
    gaps = extract_gaps(audit_report)

    # Review count from audit
    review_count = "N/A"
    gbp_detected = meta.get("gbp_detected", False)
    pages_crawled = meta.get("pages_crawled", 0)
    project_page_count = meta.get("project_pages_count", 0)
    has_sitemap = meta.get("has_sitemap", False)
    has_schema = bool(meta.get("schema_types_found", []))

    # Website checklist — mark items done based on audit
    website_checklist = [
        {"text": "Add structured data (JSON-LD)", "detail": "Helps Google understand your business. LocalBusiness + Organization schema at minimum.", "done": has_schema},
        {"text": "Create project portfolio pages", "detail": "Each completed project gets its own page with professional photos, specs, and client context.", "done": project_page_count >= 3},
        {"text": "Write location-specific pages", "detail": f"{location} and surrounding areas. One page per service area.", "done": False},
        {"text": "Fix meta descriptions", "detail": "Every page needs a unique, compelling meta description under 160 characters.", "done": bool(meta.get("homepage_meta_description"))},
        {"text": "Add a blog with 2 posts/month", "detail": "Project case studies, build process insights, and local market content.", "done": False},
        {"text": "Optimize images with alt text", "detail": "Every image needs descriptive alt text. Good for SEO and accessibility.", "done": meta.get("total_missing_alt", 1) == 0},
    ]

    # Rotate images based on index
    cover_img = COVER_IMAGES[index % len(COVER_IMAGES)]
    gallery_1_imgs = [GALLERY_EXTERIORS[index % len(GALLERY_EXTERIORS)]]
    gallery_2_imgs = [GALLERY_INTERIORS[index % len(GALLERY_INTERIORS)]]
    break_imgs = [BREAK_IMAGES[i % len(BREAK_IMAGES)] for i in range(index, index + 5)]

    # Build the snapshot lead paragraph
    if website_seo_val >= 70:
        snapshot_lead = f"I took a close look at {company_name}'s digital presence, from your website to social media to Google. You've got a solid foundation to build on."
    elif website_seo_val >= 50:
        snapshot_lead = f"I took a close look at {company_name}'s digital presence, from your website to social media to Google. Here's an honest snapshot of where things are and where the biggest opportunities sit."
    else:
        snapshot_lead = f"I took a close look at {company_name}'s digital presence. The work you do clearly speaks for itself, but your online presence isn't telling that story yet. Here's where things stand."

    config = {
        "client": {
            "company": company_name,
            "slug": slug,
            "owner": owner_name,
            "owner_title": "Owner"
        },
        "plan": {
            "type": "builder-marketing-plan",
            "date": datetime.now().strftime("%B %Y"),
            "year": str(datetime.now().year),
            "filename": f"{slug}-marketing-plan.html"
        },
        "cover": {
            "eyebrow": "Marketing Playbook",
            "headline_html": f"How {company_name}<br>wins more<br><em>of the right clients.</em>",
            "subtitle": f"A personalized marketing strategy for {company_name}, built on what's actually working in BC's custom home market right now.",
            "cta_text": "See Where You Stand",
            "cta_target": "#snapshot",
            "image_url": cover_img,
            "image_position": "center 25%"
        },
        "images": {
            "breaks": break_imgs
        },
        "sections": [
            "snapshot", "opportunity", "gallery_1", "website", "gbp",
            "social", "gallery_2", "content_engine", "reviews", "referrals",
            "awards", "case_study", "numbers", "roadmap", "rhythm",
            "cta"
        ],

        # ─── SNAPSHOT ───
        "snapshot": {
            "eyebrow": "Where You Stand",
            "headline_html": f"A quick look at<br><em>{company_name} online.</em>",
            "lead": snapshot_lead,
            "paragraphs": [
                f"The good news: {strengths[0].lower() if strengths[0][0].isupper() else strengths[0]}. {'Also, ' + strengths[1].lower() + '.' if len(strengths) > 1 else ''} Anyone who finds {company_name} is going to see quality work.",
                f"The challenge: {gaps[0].lower() if gaps[0][0].isupper() else gaps[0]}. {gaps[1] + '.' if len(gaps) > 1 else ''} These are fixable gaps with outsized upside."
            ],
            "scores": [
                {"value": str(website_seo_val), "label": "Website & SEO", "grade": score_to_grade(website_seo_val), "color": score_to_color(website_seo_val)},
                {"value": str(social_val), "label": "Social Media", "grade": score_to_grade(social_val), "color": score_to_color(social_val)},
                {"value": str(google_val), "label": "Google Presence", "grade": score_to_grade(google_val), "color": score_to_color(google_val)},
                {"value": str(visual_val), "label": "Visual Assets", "grade": score_to_grade(visual_val), "color": score_to_color(visual_val)},
            ],
            "findings": [
                {
                    "area": "What's Working",
                    "status": "active",
                    "status_label": "Strong",
                    "points": strengths
                },
                {
                    "area": "Biggest Gaps",
                    "status": "needs-work",
                    "status_label": "Needs Work",
                    "points": gaps
                }
            ],
            "insight": {
                "title": "The Bottom Line",
                "content_html": f"<p>{company_name} builds great homes but the online presence doesn't fully reflect that yet. The good news is the fixes are straightforward, the competition in your market is beatable, and the upside is significant. This plan shows you exactly how to close the gap.</p>"
            }
        },

        # ─── OPPORTUNITY ───
        "opportunity": {
            "eyebrow": "The Opportunity",
            "headline_html": "What the top builders<br><em>in your market are doing.</em>",
            "lead": f"The {location or 'BC'} market has some strong custom home builders. But when you look at who's actually showing up online, the field thins out fast.",
            "paragraphs": [
                f"I looked at the builders in your area across every channel: website quality, social media activity, Google presence, professional photography, and awards. Some are doing it well. Most aren't. And that's your opportunity.",
                "The builders consistently landing the best projects aren't necessarily building better homes than you. They're just more visible where it counts. They show up in Google, they post consistently on social, and they have the professional imagery to back it up."
            ],
            "competitors": [
                {"name": "Top Local Builder", "is_you": False, "website": "good", "website_note": "Modern, fast", "social": "good", "social_note": "Active", "gbp": "good", "gbp_note": "25+ reviews", "photography": "good", "photography_note": "Professional", "awards": "good", "awards_note": "Multiple"},
                {"name": "Mid-Market Builder", "is_you": False, "website": "ok", "website_note": "Dated design", "social": "ok", "social_note": "Monthly", "gbp": "ok", "gbp_note": "Some reviews", "photography": "ok", "photography_note": "Mixed quality", "awards": "poor", "awards_note": "None"},
                {"name": "Another Competitor", "is_you": False, "website": "ok", "website_note": "Basic", "social": "poor", "social_note": "Dormant", "gbp": "good", "gbp_note": "15+ reviews", "photography": "ok", "photography_note": "Phone shots", "awards": "ok", "awards_note": "1 award"},
                {"name": company_name, "is_you": True, "website": score_to_color(website_seo_val), "website_note": "See below", "social": score_to_color(social_val), "social_note": "See below", "gbp": score_to_color(google_val), "gbp_note": "See below", "photography": score_to_color(visual_val), "photography_note": "See below", "awards": "poor", "awards_note": "TBD"}
            ],
            "insight": {
                "title": "What This Means",
                "content_html": f"<p>Only a handful of builders in your market are firing on all cylinders. The rest have the same gaps you do. That means this isn't about catching up to an impossible standard. It's about being one of the first to get it right. And right now, that position is wide open.</p>"
            }
        },

        # ─── WEBSITE & SEO ───
        "website": {
            "eyebrow": "Website & SEO",
            "headline_html": "Your website is your<br><em>24/7 sales team.</em>",
            "lead": "{company}'s website at {domain} has {page_info}. Here's what's working and where the biggest SEO wins are.".format(
                company=company_name,
                domain=website.replace("https://", "").replace("http://", "").rstrip("/"),
                page_info=f"{pages_crawled} pages" if pages_crawled > 1 else "a basic presence"
            ),
            "paragraphs": [
                "Your site has structured data markup, which is a good start." if has_schema else "Your site doesn't have structured data markup (JSON-LD), which means Google can't pull your business details into rich search results. Adding LocalBusiness schema is the single fastest technical win available.",
                f"You have {project_page_count} project-style pages, which is a solid foundation." if project_page_count >= 3 else "Dedicated project pages are where SEO and client trust intersect. Each completed build should have its own page with professional photos, specs, and location tags. These are what rank in Google.",
                "Your sitemap is set up, which helps Google index your pages." if has_sitemap else "No XML sitemap was detected. Adding one helps Google discover and index all your pages efficiently."
            ],
            "checklist": website_checklist,
            "insight": {
                "title": "The Professional Photography Connection",
                "content_html": "<p>Every recommendation above needs one thing to work: <strong>strong visual content</strong>. Project pages need professional photography. Blog posts need real images from real builds. Location pages need hero shots from that area. The website strategy and the content strategy are the same strategy.</p>"
            }
        },

        # ─── GBP ───
        "gbp": {
            "eyebrow": "Google Business Profile",
            "headline_html": "The free tool<br><em>most builders ignore.</em>",
            "lead": f"Google Business Profile signals were detected for {company_name}, but there's room to optimize." if gbp_detected else f"{company_name} doesn't appear to have a fully optimized Google Business Profile. This is the single highest-ROI action in this entire plan.",
            "paragraphs": [
                f"When someone searches 'custom home builder {location or 'BC'}', Google shows the map pack first. That's three businesses. GBP is how you get there.",
                "The fix isn't complicated. A fully optimized GBP with 20+ reviews, professional photos, and weekly posts would put you in the map pack within 90 days."
            ],
            "checklist": [
                {"text": "Claim and verify your GBP listing", "detail": "If you haven't already. Google will mail a postcard or call to verify.", "done": gbp_detected},
                {"text": "Complete every field", "detail": "Business hours, services, description, attributes. 100% completion helps ranking.", "done": False},
                {"text": "Add 25+ professional photos", "detail": "Completed projects, team, office, process shots. Updated monthly.", "done": False},
                {"text": "Post weekly updates", "detail": "Project milestones, completed builds, awards, team updates. Takes 5 minutes.", "done": False},
                {"text": "Build to 20+ reviews", "detail": "Ask every happy client. Respond to every review within 24 hours.", "done": False},
                {"text": "Add your service areas", "detail": f"{location or 'All areas you serve'} and surrounding communities.", "done": False}
            ],
            "stats": [
                {"value": "46%", "label": "Of Google Searches Are Local"},
                {"value": "76%", "label": "Visit Within 24 Hours"},
                {"value": "28%", "label": "Result in a Purchase"},
                {"value": "5x", "label": "More Views with Photos"}
            ],
            "insight": {
                "title": "Why This Matters for Builders",
                "content_html": f"<p>Your ideal client isn't scrolling Instagram looking for a builder. They're Googling 'custom home builder {location or 'near me'}.' GBP is how you intercept that search. And the builders in your market who've figured this out are getting those calls instead of you.</p>"
            }
        },

        # ─── SOCIAL MEDIA ───
        "social": {
            "eyebrow": "Social Media",
            "headline_html": "Show the work.<br><em>Consistently.</em>",
            "lead": f"Most builders in the {location or 'BC'} market are either not posting on social media or posting inconsistently. This is a wide-open opportunity.",
            "paragraphs": [
                "This isn't about becoming a social media company. It's about showing the work you're already doing in a way that attracts the clients you want.",
                "The builders getting the most traction on social aren't hiring agencies or spending hours on content. They're doing one thing well: showing the work in progress."
            ],
            "pillars": [
                {"title": "The Build", "frequency": "2x per week", "description": "Progress shots, framing, structural moments. The stuff that shows your team knows what they're doing. Phone photos work fine here."},
                {"title": "The Finished Product", "frequency": "1x per week", "description": "Professional photography of completed projects. These are the posts that get saved and shared. This is what attracts the right clients."},
                {"title": "The Team", "frequency": "1x per week", "description": "Crew on site, team lunches, jobsite culture. People hire people. Show the humans behind the builds."},
                {"title": "The Process", "frequency": "1x per week", "description": "Material selections, design decisions, problem-solving. Educational content positions you as the expert."}
            ],
            "insight": {
                "title": "The Content Math",
                "content_html": "<p>One professional photo shoot produces 20-25 images. That's <strong>5 weeks of social content</strong> from a single day. Add in your phone shots from site visits and team moments, and you have a full content calendar without ever running out of material.</p>"
            }
        },

        # ─── CONTENT ENGINE ───
        "content_engine": {
            "eyebrow": "The Content Engine",
            "headline_html": "One shoot feeds<br><em>every channel.</em>",
            "lead": "This is where everything connects. Professional project documentation isn't just about having nice photos on your website. It's the engine that powers your entire marketing system.",
            "paragraphs": [
                "One professional photo shoot of a completed project produces 20-25 edited images. Here's where those images go and what they do for you:"
            ],
            "channels": [
                {"title": "Website & SEO", "entries": ["Dedicated project page with full photo gallery", "Blog case study with build story and specs", "Location page hero images for local SEO", "Schema markup with project imagery"]},
                {"title": "Social Media", "entries": ["5+ weeks of Instagram and Facebook content", "LinkedIn portfolio posts for B2B credibility", "Before/after carousels and reel content", "Story content showing craftsmanship details"]},
                {"title": "Google Business Profile", "entries": ["Monthly photo updates (boosts ranking)", "Project completion posts with imagery", "Service area photos tied to locations", "Team and process documentation"]},
                {"title": "Sales & Proposals", "entries": ["Client presentation decks with real imagery", "Printed materials and brochures", "Award submission photography (Georgie, CHBA)", "Publication-ready images (Western Living, Dwell)"]}
            ],
            "numbers": [
                {"value": "25", "label": "Images per Shoot"},
                {"value": "5", "label": "Weeks of Content"},
                {"value": "4", "label": "Channels Fed"}
            ],
            "insight": {
                "title": "The Multiplier Effect",
                "content_html": "<p>Most builders think of photography as a one-time expense for the website. The builders winning the most work treat it as a content investment. One day of shooting creates months of marketing fuel across every platform. The ROI isn't in the photos themselves, it's in what those photos do across your entire marketing system.</p>"
            }
        },

        # ─── REVIEWS ───
        "reviews": {
            "eyebrow": "Reviews & Reputation",
            "headline_html": "Word of mouth,<br><em>at scale.</em>",
            "lead": f"For a builder of {company_name}'s caliber, 20+ Google reviews should be the minimum. Here's how to build that systematically.",
            "paragraphs": [
                "Custom home building is a high-trust, high-ticket decision. Potential clients aren't buying shoes online. They're investing hundreds of thousands in their family's home. Reviews are how they validate their gut feeling about you before they ever pick up the phone.",
                "The goal isn't hundreds of reviews. It's 20-30 genuine reviews from real clients that tell specific stories about working with you."
            ],
            "stats": [
                {"value": "?", "label": "Current Google Reviews"},
                {"value": "93%", "label": "Read Reviews Before Hiring"},
                {"value": "20", "label": "Reviews for Credibility"},
                {"value": "4.7", "label": "Minimum Target Rating"}
            ],
            "checklist": [
                {"text": "Send a review request within 1 week of project handover", "detail": "Strike while the excitement is fresh. Include a direct link to your Google review page.", "done": False},
                {"text": "Make it easy with a direct Google review link", "detail": "Don't send them to your website. Send the Google review URL so it's one click.", "done": False},
                {"text": "Respond to every review within 24 hours", "detail": "Thank them specifically. Mention the project. Shows potential clients you care.", "done": False},
                {"text": "Ask subcontractors and design partners too", "detail": "Architects, designers, and trades you work with can leave Google reviews about the collaboration.", "done": False},
                {"text": "Feature best reviews on your website", "detail": "Pull the strongest Google reviews onto your homepage and project pages.", "done": False}
            ],
            "insight": {
                "title": "The Compounding Effect",
                "content_html": "<p>Reviews compound. The first 10 get you into consideration. The next 10 get you ranked. After 20+, you're the obvious choice. And every review with a specific story does more than any ad could.</p>"
            }
        },

        # ─── REFERRALS ───
        "referrals": {
            "eyebrow": "Referral System",
            "headline_html": "Turn happy clients into<br><em>your sales team.</em>",
            "lead": "Most of your best projects probably came from referrals. The problem is that referrals happen randomly. A system makes them predictable.",
            "paragraphs": [
                f"In {location or 'BC'}, word of mouth is everything. But right now it's accidental. Someone mentions you at a dinner party, maybe the friend follows up, maybe they don't.",
                "The builders consistently landing the best projects have three things in common: they ask, they make it easy, and they follow up."
            ],
            "steps": [
                {"number": "1", "title": "The Ask", "description": "At project handover, ask directly: 'We loved working on this project. If you know anyone building or renovating, we'd appreciate the introduction.' Simple, honest, no incentive needed."},
                {"number": "2", "title": "Make It Easy", "description": "Give them something to share. A link to the project page on your website with professional photos. People share beautiful things without being asked twice."},
                {"number": "3", "title": "The Follow-Up", "description": "Thank every referrer personally. A handwritten note or a framed print of their home goes further than any gift card. Stay in their world with a quick check-in every 6 months."}
            ],
            "insight": {
                "title": "The Photography Connection",
                "content_html": "<p>The single best referral tool is a stunning project page with professional photography. When a past client tells their friend 'you should call our builder,' the friend Googles you. If what they find looks as good as the recommendation, you get the call. If it doesn't, you lose it.</p>"
            }
        },

        # ─── AWARDS ───
        "awards": {
            "eyebrow": "Awards & Publications",
            "headline_html": "The credentials<br><em>that close deals.</em>",
            "lead": f"Awards aren't vanity. They're the third-party validation that separates {company_name} from every other builder making the same claims.",
            "paragraphs": [
                "'Award-winning custom home builder' in your Google listing, on your website, and in your proposals changes the conversation. Most builders haven't submitted. That's the opportunity.",
                "A single strong submission with professional photography could land your first award this year."
            ],
            "channels": [
                {"title": "Award Programs", "entries": [
                    "Georgie Awards (CHBA BC) &mdash; deadline typically March",
                    "CHBA National Awards for Housing Excellence",
                    "HAVAN Awards (if Lower Mainland)",
                    "Gold Nugget Awards &mdash; international recognition"
                ]},
                {"title": "Publications", "entries": [
                    "Western Living &mdash; BC's premier shelter magazine",
                    "Mountain Life &mdash; strong for Sea-to-Sky builders",
                    "Dwell &mdash; design-focused, high credibility",
                    "Local newspaper home sections and features"
                ]}
            ],
            "insight": {
                "title": "The Requirement",
                "content_html": "<p>Every award submission and publication pitch requires one thing: <strong>professional photography</strong>. Not phone shots. Not point-and-shoot. Publication-quality imagery that meets specific technical requirements. Without it, your best project can't even enter the conversation.</p>"
            }
        },

        # ─── NUMBERS BAR ───
        "numbers": {
            "stats": [
                {"value": "25", "label": "Images per Shoot"},
                {"value": "12", "label": "Months of Content"},
                {"value": "7", "label": "Channels Fed"}
            ]
        },

        # ─── 90-DAY ROADMAP ───
        "roadmap": {
            "eyebrow": "90-Day Action Plan",
            "headline_html": "Where to start.<br><em>What to do first.</em>",
            "lead": f"You don't need to do everything at once. Here's the prioritized sequence based on what will move the needle fastest for {company_name}.",
            "paragraphs": [],
            "periods": [
                {"timeframe": "Week 1-2", "label_html": "Foundation:<br><em>Get Found</em>", "entries": [
                    "Claim and fully optimize your Google Business Profile",
                    "Add 15-20 of your best project photos to GBP",
                    "Ask your 5 most recent clients for Google reviews",
                    "Fix any critical website issues (broken links, missing pages, slow load)"
                ]},
                {"timeframe": "Week 3-4", "label_html": "Content:<br><em>Show the Work</em>", "entries": [
                    "Start posting 3x/week on Instagram (build progress + finished work + team)",
                    "Create your first project case study page on the website",
                    "Schedule your first professional photo shoot of a completed project",
                    "Set up your LinkedIn company page"
                ]},
                {"timeframe": "Month 2", "label_html": "Momentum:<br><em>Build the Library</em>", "entries": [
                    "Publish 2 blog posts (project case study + local market insight)",
                    "Launch your review request system (email template + direct link)",
                    "Post weekly GBP updates with project photos",
                    "Research award submission deadlines and requirements"
                ]},
                {"timeframe": "Month 3", "label_html": "Scale:<br><em>Compound the Gains</em>", "entries": [
                    "Second professional photo shoot (different project or in-progress build)",
                    "Submit first award application with professional imagery",
                    "Activate referral system with past client outreach",
                    "Review analytics: what's working, what to double down on"
                ]}
            ],
            "stats": [
                {"value": "90", "label": "Days to Transform"},
                {"value": "2", "label": "Pro Photo Shoots"},
                {"value": "50", "label": "Professional Images"},
                {"value": "20", "label": "Target Google Reviews"}
            ]
        },

        # ─── MONTHLY RHYTHM ───
        "rhythm": {
            "eyebrow": "The Monthly Rhythm",
            "headline_html": "Keep the engine<br><em>running.</em>",
            "lead": "After the first 90 days, marketing becomes a rhythm, not a project. Here's what a sustainable monthly cadence looks like.",
            "paragraphs": [],
            "cards": [
                {"frequency": "Weekly", "title": "Content & Social", "entries": ["3-4 Instagram posts (mix of build, finished, team)", "1 LinkedIn post (project update or insight)", "1 GBP post with photos", "Reply to all comments and DMs"]},
                {"frequency": "Monthly", "title": "Website & SEO", "entries": ["1 blog post or project case study", "Update project gallery with new photos", "Check Google Search Console for opportunities", "Update GBP with new project photos"]},
                {"frequency": "Monthly", "title": "Relationships", "entries": ["Send 2-3 review requests to recent clients", "Reach out to 1 past client for referral ask", "Connect with 2 architects or designers", "Engage with local builders and trades online"]},
                {"frequency": "Quarterly", "title": "Big Moves", "entries": ["1 professional photo shoot (completed project)", "Review award submission deadlines", "Audit website analytics and adjust strategy", "Plan next quarter's content calendar"]},
                {"frequency": "Quarterly", "title": "Content Production", "entries": ["Batch edit and distribute shoot images", "Create 3 months of social content from shoot", "Update website project pages", "Prep award submission materials"]},
                {"frequency": "Annually", "title": "Strategy Review", "entries": ["Full marketing audit (what worked, what didn't)", "Update website with best projects from the year", "Plan award submissions for the year", "Set content and growth targets for next 12 months"]}
            ],
            "insight": {
                "title": "The Real Secret",
                "content_html": "<p>The builders who win at marketing aren't spending more time on it. They're spending <strong>better</strong> time. One professional photo shoot per quarter produces enough content to fuel everything else for months. The system runs itself once the content exists.</p>"
            }
        },

        # ─── GALLERIES ───
        "gallery_1": {
            "columns": 1,
            "images": gallery_1_imgs,
            "caption": "Matt Anthony Photography"
        },
        "gallery_2": {
            "columns": 1,
            "images": gallery_2_imgs,
            "caption": "Matt Anthony Photography"
        },

        # ─── CASE STUDY ───
        "case_study": {
            "eyebrow": "Case Study",
            "headline_html": "What this looks like<br><em>in practice.</em>",
            "lead": "Balmoral Construction is a custom home builder in the Sea-to-Sky corridor. Here's what happened when they invested in professional documentation and a content-driven marketing strategy.",
            "browser": {
                "url_text": "balmoralconstruction.com",
                "screenshot": "https://images.squarespace-cdn.com/content/6824fd48afd1dd40cd73e146/93aadd7d-1feb-4c75-bf1e-25a901aa197f/www.balmoralconstruction.com_+%282%29+%281%29.png?content-type=image%2Fpng",
                "alt": "Balmoral Construction website — 42 pages built by Matt Anthony Photography"
            },
            "header_image": {
                "url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/64c6702a-78ea-4fe3-a601-78bce7c197a8/warbler-whistler-architectural-photography-matt-anthony-.jpg-5.jpg",
                "alt": "Warbler Residence — built by Balmoral Construction, Whistler",
                "eyebrow": "Balmoral Construction",
                "title_html": "From invisible online to<br><em>the builder people find first.</em>"
            },
            "paragraphs": [
                "When we started working together, Balmoral had completed over 50 custom homes across the Sea-to-Sky corridor but had zero online presence to show for it. No project pages, no professional photography, no awards, no content strategy.",
                "We built a full 42-page website with dedicated project pages, location-specific landing pages, and a blog. Every page is backed by professional architectural photography.",
                "We then launched a monthly content system: professional photo shoots, social media content, Google Business Profile optimization, and award submissions.",
                "The result: Balmoral now shows up in Google for every key search term in their market. Their website generates qualified leads. Their Instagram showcases the work. And for the first time, their online presence matches the quality of what they actually build."
            ],
            "stats": [
                {"value": "42", "label": "Website Pages Built"},
                {"value": "14", "label": "Project Pages"},
                {"value": "300+", "label": "Professional Images"},
                {"value": "7", "label": "Location Pages"}
            ],
            "gallery": [
                {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/40f0f4b4-0146-4139-8682-d3505ba00ba2/warbler-whistler-architectural-photography-matt-anthony-.jpg-36.jpg", "alt": "Warbler Residence — Balmoral Construction"},
                {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/0a5c4ead-f6f9-413c-aaad-b12b03837e78/fitzsimmons-whistler-architectural-photography-matt-anthony-.jpg.jpg", "alt": "Fitzsimmons Residence — Balmoral Construction"},
                {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/d4768559-4d0d-4403-a58c-02db15d5b177/fitzsimmons-whistler-architectural-photography-matt-anthony-.jpg-42.jpg", "alt": "Fitzsimmons interior — Balmoral Construction"},
                {"url": "https://images.squarespace-cdn.com/content/v1/6824fd48afd1dd40cd73e146/98b6bb8c-ede3-4de9-978a-fc8ae91554a6/warbler-whistler-architectural-photography-matt-anthony-.jpg-35.jpg", "alt": "Warbler exterior — Balmoral Construction"}
            ],
            "link": {
                "url": "https://www.balmoralconstruction.com",
                "text": "See the Balmoral website"
            },
            "insight": {
                "title": "The Takeaway",
                "content_html": "<p>Balmoral didn't need to change how they build homes. They needed to <strong>show</strong> how they build homes. The photography, the website, the content system, they're all the same investment. And it compounds every month.</p>"
            }
        },

        # ─── CTA ───
        "cta": {
            "eyebrow": "Let's Talk",
            "headline_html": "Ready to build your<br><em>content engine?</em>",
            "paragraphs": [
                "Everything in this plan starts with one thing: professional visual content. The website, the social, the awards, the reviews, they all need imagery that matches the quality of what you build.",
                "I run a full-service creative agency for builders across BC. Photography, website design, content strategy, social media, and brand development, all under one roof. Not a vendor you call once a year, but an embedded creative partner who keeps your marketing engine running."
            ],
            "bg_image": CTA_BG,
            "button": {
                "text": "Book a Discovery Call",
                "url": "https://mattanthonyphoto.com/contact"
            },
            "details": [
                {"label": "Specialization", "value": "Architectural & Construction Photography"},
                {"label": "Service Area", "value": "Sea-to-Sky, Sunshine Coast, Vancouver, Fraser Valley"},
                {"label": "Starting At", "value": "One shoot. See what's possible."}
            ]
        },

        # ─── CLOSING ───
        "closing": {
            "eyebrow": "What's Next",
            "headline_html": "This plan works.<br><em>If it gets executed.</em>",
            "paragraphs": [
                f"{owner_name}, I put this together because {company_name} builds the kind of homes that should be getting more attention than they are. The work is there. The marketing just needs to catch up.",
                "Every section of this plan connects back to one thing: having professional visual content to fuel the machine. Without it, the website stays thin, the social stays inconsistent, the awards stay unsubmitted, and the best clients keep finding your competitors first.",
                "I specialize in exactly this, architectural and construction photography built specifically for marketing. Not just pretty photos, but a content system that feeds every channel you need.",
                f"If you'd like to talk about getting the content engine started, I'm here. No pitch, just a conversation about what would make the biggest difference for {company_name} right now."
            ],
            "steps": [
                {"number": "1", "title": "Start with GBP", "description": "The highest-ROI action in this plan. Takes an afternoon, pays off for years."},
                {"number": "2", "title": "Shoot One Project", "description": "Pick your best recent build. One professional shoot creates months of content across every channel."},
                {"number": "3", "title": "Build the Rhythm", "description": "Once the content exists, the weekly posting and monthly updates take minutes, not hours."}
            ]
        }
    }

    return config


def generate_dm(company_name, owner_name, plan_url):
    """Generate the Instagram DM message."""
    first_name = owner_name.split()[0] if owner_name and owner_name != "Owner" else ""
    greeting = f"Hey {first_name}, " if first_name else "Hey, "

    return (
        f"{greeting}I put together a marketing playbook specifically for {company_name}. "
        f"It covers where you stand right now (website, Google, social, reviews) and "
        f"a 90-day plan to start winning more of the right clients.\n\n"
        f"No strings attached, just thought it'd be useful: {plan_url}"
    )


def process_builder(row, index, publish=True):
    """Process a single builder: audit → config → generate → publish."""

    company = row.get("Company Name", "").strip()
    website = row.get("Website", "").strip()
    owner = row.get("Owner Name", "Owner").strip() or "Owner"
    location = row.get("Location", "").strip() or None

    if not company or not website:
        return {"company": company, "status": "SKIPPED", "reason": "Missing company name or website"}

    slug = slugify(company)
    print(f"\n{'='*60}")
    print(f"  [{index+1}] {company}")
    print(f"  Website: {website}")
    print(f"{'='*60}")

    # Step 1: Site audit
    try:
        print(f"\n  [1/4] Running site audit...")
        audit = run_audit(website, company, location)
    except Exception as e:
        print(f"  ERROR in audit: {e}")
        traceback.print_exc()
        return {"company": company, "status": "FAILED", "reason": f"Audit error: {e}"}

    # Step 2: Build config
    try:
        print(f"\n  [2/4] Building config...")
        config = build_config(company, owner, website, location, audit, index)
        config_path = os.path.join(CONFIG_DIR, f"{slug}-marketing-plan.json")
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"  Config saved: {config_path}")
    except Exception as e:
        print(f"  ERROR building config: {e}")
        traceback.print_exc()
        return {"company": company, "status": "FAILED", "reason": f"Config error: {e}"}

    # Step 3: Generate HTML
    try:
        print(f"\n  [3/4] Generating HTML...")
        html_path = generate(config_path, publish=publish)
        if not html_path:
            return {"company": company, "status": "FAILED", "reason": "HTML generation returned None"}
    except Exception as e:
        print(f"  ERROR generating HTML: {e}")
        traceback.print_exc()
        return {"company": company, "status": "FAILED", "reason": f"Generate error: {e}"}

    # Step 4: Build result
    plan_url = f"https://mattanthonyphoto.github.io/matt-proposals/{slug}/{slug}-marketing-plan.html"
    dm_message = generate_dm(company, owner, plan_url)

    scores = audit.get("scores", {})
    result = {
        "company": company,
        "owner": owner,
        "website": website,
        "slug": slug,
        "status": "OK",
        "plan_url": plan_url,
        "dm_message": dm_message,
        "seo_score": scores.get("seo", {}).get("value", ""),
        "local_score": scores.get("local", {}).get("value", ""),
        "content_score": scores.get("content", {}).get("value", ""),
        "visual_score": scores.get("visual_assets", {}).get("value", ""),
    }

    print(f"\n  DONE: {plan_url}")
    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Batch generate builder marketing plans")
    parser.add_argument("input_csv", help="CSV with columns: Company Name, Website, Owner Name, Location")
    parser.add_argument("--limit", type=int, default=0, help="Max builders to process (0 = all)")
    parser.add_argument("--dry-run", action="store_true", help="Audit only, don't generate or publish")
    parser.add_argument("--no-publish", action="store_true", help="Generate HTML but don't publish to GitHub Pages")
    args = parser.parse_args()

    # Read CSV
    csv_path = Path(args.input_csv)
    if not csv_path.exists():
        print(f"ERROR: File not found: {csv_path}")
        sys.exit(1)

    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if args.limit > 0:
        rows = rows[:args.limit]

    print(f"\nBatch Plan Generator")
    print(f"{'='*60}")
    print(f"  Input: {csv_path}")
    print(f"  Builders: {len(rows)}")
    print(f"  Publish: {'No' if args.no_publish or args.dry_run else 'Yes'}")
    print(f"  Dry run: {'Yes' if args.dry_run else 'No'}")
    print(f"{'='*60}")

    results = []
    for i, row in enumerate(rows):
        if args.dry_run:
            company = row.get("Company Name", "").strip()
            website = row.get("Website", "").strip()
            if company and website:
                try:
                    audit = run_audit(website, company, row.get("Location", "").strip() or None)
                    scores = audit.get("scores", {})
                    results.append({
                        "company": company,
                        "status": "AUDITED",
                        "seo_score": scores.get("seo", {}).get("value", ""),
                        "local_score": scores.get("local", {}).get("value", ""),
                    })
                except Exception as e:
                    results.append({"company": company, "status": "FAILED", "reason": str(e)})
        else:
            result = process_builder(row, i, publish=not args.no_publish)
            results.append(result)

    # Write results CSV
    os.makedirs(TMP_DIR, exist_ok=True)
    results_path = os.path.join(TMP_DIR, "batch-plans-results.csv")
    if results:
        fieldnames = results[0].keys()
        with open(results_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

    # Print summary
    ok = sum(1 for r in results if r.get("status") == "OK")
    failed = sum(1 for r in results if r.get("status") == "FAILED")
    skipped = sum(1 for r in results if r.get("status") == "SKIPPED")

    print(f"\n{'='*60}")
    print(f"  BATCH COMPLETE")
    print(f"{'='*60}")
    print(f"  Success: {ok}")
    print(f"  Failed:  {failed}")
    print(f"  Skipped: {skipped}")
    print(f"  Results: {results_path}")
    print(f"{'='*60}")

    # Print DM messages for successful plans
    if ok > 0:
        print(f"\n{'='*60}")
        print(f"  READY-TO-SEND DMs")
        print(f"{'='*60}")
        for r in results:
            if r.get("status") == "OK":
                print(f"\n  --- {r['company']} ---")
                print(f"  URL: {r['plan_url']}")
                print(f"  DM:\n  {r['dm_message']}")
                print()


if __name__ == "__main__":
    main()
