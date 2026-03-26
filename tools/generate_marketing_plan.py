"""Generate personalized builder marketing plans from JSON configs.

Usage:
    python3 tools/generate_marketing_plan.py scaffold --client <slug> --owner <name> --company <name>
    python3 tools/generate_marketing_plan.py generate <config.json> [--output <path>] [--publish]
    python3 tools/generate_marketing_plan.py list-configs

The marketing plan is a lead magnet — a personalized, in-depth guide showing
a builder how to market their business. Photography is woven in naturally as
the content engine that feeds every channel.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    from jinja2 import Environment, BaseLoader
except ImportError:
    print("ERROR: jinja2 required. Run: pip3 install --user jinja2")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "business", "sales", "templates")
CONFIG_DIR = os.path.join(BASE_DIR, "business", "sales", "configs")
OUTPUT_DIR = os.path.join(BASE_DIR, "business", "sales")
TEMPLATE_FILE = "builder-marketing-plan.html.j2"


def generate(config_path, output_path=None, publish=False):
    """Generate an HTML marketing plan from a config file."""
    config_path = Path(config_path)
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        return None

    with open(config_path) as f:
        config = json.load(f)

    required = ["client", "plan", "cover", "sections"]
    missing = [r for r in required if r not in config]
    if missing:
        print(f"ERROR: Config missing required fields: {', '.join(missing)}")
        return None

    template_path = os.path.join(TEMPLATE_DIR, TEMPLATE_FILE)
    if not os.path.exists(template_path):
        print(f"ERROR: Template not found: {template_path}")
        return None

    with open(template_path) as f:
        template_str = f.read()

    env = Environment(loader=BaseLoader(), autoescape=False)
    template = env.from_string(template_str)
    html = template.render(**config)

    if not output_path:
        slug = config["client"]["slug"]
        filename = config["plan"].get("filename", f"{slug}-marketing-plan.html")
        output_path = os.path.join(OUTPUT_DIR, filename)

    with open(output_path, "w") as f:
        f.write(html)

    size = os.path.getsize(output_path) / 1024
    print(f"Generated: {output_path} ({size:.1f} KB)")

    if publish:
        slug = config["client"]["slug"]
        filename = config["plan"].get("filename", f"{slug}-marketing-plan.html")
        publish_cmd = [
            sys.executable, os.path.join(BASE_DIR, "tools", "publish_proposal.py"),
            "upload", output_path,
            "--client", slug,
            "--name", filename
        ]
        subprocess.run(publish_cmd)

    return output_path


def scaffold(client_slug, owner_name, company_name):
    """Create a starter config with TODO placeholders."""
    config = {
        "client": {
            "company": company_name,
            "slug": client_slug,
            "owner": owner_name,
            "owner_title": "Owner"
        },
        "plan": {
            "type": "builder-marketing-plan",
            "date": "TODO: Month Year",
            "year": "2026",
            "filename": f"{client_slug}-marketing-plan.html"
        },
        "cover": {
            "eyebrow": f"Marketing Playbook",
            "headline_html": f"How {company_name}<br>wins more<br><em>of the right clients.</em>",
            "subtitle": f"A personalized marketing strategy for {company_name}, built on what's actually working in BC's custom home market right now.",
            "cta_text": "See Where You Stand",
            "cta_target": "#snapshot",
            "image_url": "TODO: Squarespace CDN URL — use a strong architectural exterior",
            "image_position": "center 25%"
        },
        "images": {
            "breaks": [
                {"url": "TODO: CDN URL", "alt": "TODO: Description", "caption": "TODO: Project &middot; Location &middot; Matt Anthony Photography"},
                {"url": "TODO: CDN URL", "alt": "TODO: Description", "caption": "TODO: Project &middot; Location &middot; Matt Anthony Photography"},
                {"url": "TODO: CDN URL", "alt": "TODO: Description", "caption": "TODO: Project &middot; Location &middot; Matt Anthony Photography"},
                {"url": "TODO: CDN URL", "alt": "TODO: Description", "caption": "TODO: Project &middot; Location &middot; Matt Anthony Photography"},
                {"url": "TODO: CDN URL", "alt": "TODO: Description", "caption": "TODO: Project &middot; Location &middot; Matt Anthony Photography"}
            ]
        },
        "sections": [
            "snapshot", "opportunity", "gallery_1", "website", "gbp",
            "social", "gallery_2", "content_engine", "reviews", "referrals",
            "awards", "case_study", "numbers", "roadmap", "rhythm",
            "cta", "closing"
        ],

        # ─── SNAPSHOT ───
        "snapshot": {
            "eyebrow": "Where You Stand",
            "headline_html": f"A quick look at<br><em>{company_name} online.</em>",
            "lead": f"TODO: Brief, honest assessment of {company_name}'s current digital presence. Be specific — reference their actual website, social, and Google presence.",
            "paragraphs": [
                "TODO: What they're doing well (always lead with strengths).",
                "TODO: Where the gaps are (be direct but not harsh)."
            ],
            "scores": [
                {"value": "TODO", "label": "Website & SEO", "grade": "TODO", "color": "ok"},
                {"value": "TODO", "label": "Social Media", "grade": "TODO", "color": "poor"},
                {"value": "TODO", "label": "Google Presence", "grade": "TODO", "color": "ok"},
                {"value": "TODO", "label": "Visual Assets", "grade": "TODO", "color": "ok"}
            ],
            "findings": [
                {
                    "area": "What's Working",
                    "status": "active",
                    "status_label": "Strong",
                    "points": [
                        "TODO: Specific thing they do well",
                        "TODO: Another strength"
                    ]
                },
                {
                    "area": "Biggest Gaps",
                    "status": "needs-work",
                    "status_label": "Needs Work",
                    "points": [
                        "TODO: Specific gap with impact",
                        "TODO: Another gap"
                    ]
                }
            ],
            "insight": {
                "title": "The Bottom Line",
                "content_html": f"<p>TODO: One-paragraph summary. Something like: '{company_name} builds great homes but the online presence doesn't reflect that yet. The good news is the fixes are straightforward and the upside is significant.'</p>"
            }
        },

        # ─── OPPORTUNITY ───
        "opportunity": {
            "eyebrow": "The Opportunity",
            "headline_html": "What the top builders<br><em>in your market are doing.</em>",
            "lead": "TODO: Frame the competitive landscape. Most builders in BC are leaving marketing on the table. The ones winning the best projects have figured out a few key things.",
            "paragraphs": [
                "TODO: Specific observations about their local market. Who's showing up in Google? Who's active on Instagram? Who's winning awards?",
                "TODO: The gap this creates — and why it's actually good news for them."
            ],
            "competitors": [
                {"name": "TODO: Competitor 1", "is_you": False, "website": "good", "website_note": "Modern", "social": "good", "social_note": "Active", "gbp": "good", "gbp_note": "Optimized", "photography": "good", "photography_note": "Professional", "awards": "good", "awards_note": "Multiple"},
                {"name": "TODO: Competitor 2", "is_you": False, "website": "ok", "website_note": "Decent", "social": "poor", "social_note": "Inactive", "gbp": "ok", "gbp_note": "Basic", "photography": "ok", "photography_note": "Mixed", "awards": "poor", "awards_note": "None"},
                {"name": company_name, "is_you": True, "website": "TODO", "website_note": "TODO", "social": "TODO", "social_note": "TODO", "gbp": "TODO", "gbp_note": "TODO", "photography": "TODO", "photography_note": "TODO", "awards": "TODO", "awards_note": "TODO"}
            ],
            "insight": {
                "title": "What This Means",
                "content_html": "<p>TODO: Insight about what the gap means practically. The builders getting the best clients aren't necessarily building better homes — they're just more visible. This plan closes that gap.</p>"
            }
        },

        # ─── WEBSITE & SEO ───
        "website": {
            "eyebrow": "Website & SEO",
            "headline_html": "Your website is your<br><em>24/7 sales team.</em>",
            "lead": "TODO: Assessment of their current website. Be specific — mention their actual URL, what platform it's on, what works and what doesn't.",
            "paragraphs": [
                "TODO: Specific SEO observations (do they rank for anything? schema markup? meta descriptions?)",
                "TODO: Content gaps (project pages? case studies? blog?)",
                "TODO: Technical issues if any (mobile, speed, etc.)"
            ],
            "checklist": [
                {"text": "Add structured data (JSON-LD)", "detail": "Helps Google understand your business. LocalBusiness + Organization schema at minimum.", "done": False},
                {"text": "Create project portfolio pages", "detail": "Each completed project gets its own page with professional photos, specs, and client context.", "done": False},
                {"text": "Write location-specific pages", "detail": "TODO: Specific locations they serve — one page per area.", "done": False},
                {"text": "Fix meta descriptions", "detail": "Every page needs a unique, compelling meta description under 160 characters.", "done": False},
                {"text": "Add a blog with 2 posts/month", "detail": "Project case studies, build process insights, and local market content.", "done": False},
                {"text": "Optimize images with alt text", "detail": "Every image needs descriptive alt text. Good for SEO and accessibility.", "done": False}
            ],
            "insight": {
                "title": "The Professional Photography Connection",
                "content_html": "<p>Every recommendation above needs one thing to work: <strong>strong visual content</strong>. Project pages need professional photography. Blog posts need real images from real builds. Location pages need hero shots from that area. The website strategy and the content strategy are the same strategy.</p>"
            }
        },

        # ─── GBP ───
        "gbp": {
            "eyebrow": "Google Business Profile",
            "headline_html": "The free tool<br><em>most builders ignore.</em>",
            "lead": "TODO: Check if they have a GBP. If yes, assess it. If no, explain why this is the single highest-ROI action they can take.",
            "paragraphs": [
                "When someone searches 'custom home builder [their city]', Google shows the map pack first. That's three businesses. GBP is how you get there.",
                "TODO: Specific observations about their GBP (or lack of one). How many reviews? Photos? Posts?"
            ],
            "checklist": [
                {"text": "Claim and verify your GBP listing", "detail": "If you haven't already. Google will mail a postcard or call to verify.", "done": False},
                {"text": "Complete every field", "detail": "Business hours, services, description, attributes. 100% completion helps ranking.", "done": False},
                {"text": "Add 25+ professional photos", "detail": "Completed projects, team, office, process shots. Updated monthly.", "done": False},
                {"text": "Post weekly updates", "detail": "Project milestones, completed builds, awards, team updates. Takes 5 minutes.", "done": False},
                {"text": "Build to 20+ reviews", "detail": "Ask every happy client. Respond to every review within 24 hours.", "done": False},
                {"text": "Add your service areas", "detail": "TODO: List their actual service areas.", "done": False}
            ],
            "stats": [
                {"value": "46%", "label": "Of Google Searches Are Local"},
                {"value": "76%", "label": "Visit Within 24 Hours"},
                {"value": "28%", "label": "Result in a Purchase"},
                {"value": "5x", "label": "More Views with Photos"}
            ],
            "insight": {
                "title": "Why This Matters for Builders",
                "content_html": "<p>Your ideal client isn't scrolling Instagram looking for a builder. They're Googling 'custom home builder Squamish' or 'luxury home builder Whistler.' GBP is how you intercept that search. And the builders in your market who've figured this out are getting those calls instead of you.</p>"
            }
        },

        # ─── SOCIAL MEDIA ───
        "social": {
            "eyebrow": "Social Media",
            "headline_html": "Show the work.<br><em>Consistently.</em>",
            "lead": "TODO: Assessment of their current social presence. Check their Instagram, LinkedIn, Facebook. What's the posting frequency? Content quality? Engagement?",
            "paragraphs": [
                "TODO: Specific observations about what they're posting (or not posting).",
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
                {"title": "Website & SEO", "entries": [
                    "Dedicated project page with full photo gallery",
                    "Blog case study with build story and specs",
                    "Location page hero images for local SEO",
                    "Schema markup with project imagery"
                ]},
                {"title": "Social Media", "entries": [
                    "5+ weeks of Instagram and Facebook content",
                    "LinkedIn portfolio posts for B2B credibility",
                    "Before/after carousels and reel content",
                    "Story content showing craftsmanship details"
                ]},
                {"title": "Google Business Profile", "entries": [
                    "Monthly photo updates (boosts ranking)",
                    "Project completion posts with imagery",
                    "Service area photos tied to locations",
                    "Team and process documentation"
                ]},
                {"title": "Sales & Proposals", "entries": [
                    "Client presentation decks with real imagery",
                    "Printed materials and brochures",
                    "Award submission photography (Georgie, CHBA)",
                    "Publication-ready images (Western Living, Dwell)"
                ]}
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
            "lead": "TODO: Check their current Google review count and rating. Be specific.",
            "paragraphs": [
                "TODO: Context on why reviews matter specifically for builders (high-trust, high-ticket purchases).",
                "The goal isn't hundreds of reviews. It's 20-30 genuine reviews from real clients that tell specific stories about working with you."
            ],
            "stats": [
                {"value": "TODO", "label": "Current Google Reviews"},
                {"value": "93%", "label": "Read Reviews Before Hiring"},
                {"value": "20", "label": "Reviews for Credibility"},
                {"value": "4.7", "label": "Minimum Target Rating"}
            ],
            "checklist": [
                {"text": "Send a review request within 1 week of project handover", "detail": "Strike while the excitement is fresh. Include a direct link to your Google review page.", "done": False},
                {"text": "Make it easy — send the direct Google review link", "detail": "Don't send them to your website. Send the Google review URL so it's one click.", "done": False},
                {"text": "Respond to every review within 24 hours", "detail": "Thank them specifically. Mention the project. Shows potential clients you care.", "done": False},
                {"text": "Ask subcontractors and partners too", "detail": "Architects, designers, and trades you work with can leave Google reviews about the experience.", "done": False},
                {"text": "Feature reviews on your website", "detail": "Pull the best Google reviews onto your homepage and project pages.", "done": False}
            ],
            "insight": {
                "title": "The Compounding Effect",
                "content_html": "<p>Reviews compound. The first 10 get you into consideration. The next 10 get you ranked. After 20+, you're the obvious choice. And every review with a specific story ('they built our dream home in Whistler and handled the permit challenges beautifully') does more than any ad could.</p>"
            }
        },

        # ─── REFERRALS ───
        "referrals": {
            "eyebrow": "Referral System",
            "headline_html": "Turn happy clients into<br><em>your sales team.</em>",
            "lead": "Most of your best projects probably came from referrals. The problem is that referrals happen randomly. A system makes them predictable.",
            "paragraphs": [
                "TODO: If you know anything about how they currently get referrals, reference it here.",
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
            "lead": "TODO: Check if they've won any awards. Most builders haven't submitted. That's the opportunity.",
            "paragraphs": [
                "Awards aren't vanity. They're the third-party validation that separates you from every other builder making the same claims. 'Award-winning custom home builder' in your Google listing, on your website, and in your proposals changes the conversation.",
                "TODO: Specific awards relevant to their market (Georgie, CHBA, etc.)."
            ],
            "channels": [
                {"title": "Award Programs", "entries": [
                    "Georgie Awards (CHBA BC) &mdash; deadline typically March",
                    "CHBA National Awards for Housing Excellence",
                    "HAVAN Awards (if Lower Mainland)",
                    "Gold Nugget Awards &mdash; international recognition",
                    "TODO: Other relevant regional awards"
                ]},
                {"title": "Publications", "entries": [
                    "Western Living &mdash; BC's premier shelter magazine",
                    "Mountain Life &mdash; strong for Sea-to-Sky builders",
                    "Dwell &mdash; design-focused, high credibility",
                    "ArchDaily / Dezeen &mdash; if projects are design-forward",
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
            "lead": "You don't need to do everything at once. Here's the prioritized sequence based on what will move the needle fastest for your business.",
            "paragraphs": [],
            "periods": [
                {
                    "timeframe": "Week 1-2",
                    "label_html": "Foundation:<br><em>Get Found</em>",
                    "entries": [
                        "Claim and fully optimize your Google Business Profile",
                        "Add 15-20 of your best project photos to GBP",
                        "Ask your 5 most recent clients for Google reviews",
                        "Fix any critical website issues (broken links, missing pages, slow load)"
                    ]
                },
                {
                    "timeframe": "Week 3-4",
                    "label_html": "Content:<br><em>Show the Work</em>",
                    "entries": [
                        "Start posting 3x/week on Instagram (build progress + finished work + team)",
                        "Create your first project case study page on the website",
                        "Schedule your first professional photo shoot of a completed project",
                        "Set up your LinkedIn profile as a company page (if not done)"
                    ]
                },
                {
                    "timeframe": "Month 2",
                    "label_html": "Momentum:<br><em>Build the Library</em>",
                    "entries": [
                        "Publish 2 blog posts (project case study + local market insight)",
                        "Launch your review request system (email template + direct link)",
                        "Post weekly GBP updates with project photos",
                        "Research and identify 2-3 award submissions for this year"
                    ]
                },
                {
                    "timeframe": "Month 3",
                    "label_html": "Scale:<br><em>Compound the Gains</em>",
                    "entries": [
                        "Second professional photo shoot (different project or in-progress build)",
                        "Submit first award application with professional imagery",
                        "Activate referral system with past client outreach",
                        "Review analytics: what's working, what to double down on"
                    ]
                }
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
                {
                    "frequency": "Weekly",
                    "title": "Content & Social",
                    "entries": [
                        "3-4 Instagram posts (mix of build, finished, team)",
                        "1 LinkedIn post (project update or insight)",
                        "1 GBP post with photos",
                        "Reply to all comments and DMs"
                    ]
                },
                {
                    "frequency": "Monthly",
                    "title": "Website & SEO",
                    "entries": [
                        "1 blog post or project case study",
                        "Update project gallery with new photos",
                        "Check Google Search Console for opportunities",
                        "Update GBP with new project photos"
                    ]
                },
                {
                    "frequency": "Monthly",
                    "title": "Relationships",
                    "entries": [
                        "Send 2-3 review requests to recent clients",
                        "Reach out to 1 past client for referral ask",
                        "Connect with 2 architects or designers",
                        "Engage with local builders and trades online"
                    ]
                },
                {
                    "frequency": "Quarterly",
                    "title": "Big Moves",
                    "entries": [
                        "1 professional photo shoot (completed project)",
                        "Review award submission deadlines",
                        "Audit website analytics and adjust strategy",
                        "Plan next quarter's content calendar"
                    ]
                },
                {
                    "frequency": "Quarterly",
                    "title": "Content Production",
                    "entries": [
                        "Batch edit and distribute shoot images",
                        "Create 3 months of social content from shoot",
                        "Update website project pages",
                        "Prep award submission materials"
                    ]
                },
                {
                    "frequency": "Annually",
                    "title": "Strategy Review",
                    "entries": [
                        "Full marketing audit (what worked, what didn't)",
                        "Update website with best projects from the year",
                        "Plan award submissions for the year",
                        "Set content and growth targets for next 12 months"
                    ]
                }
            ],
            "insight": {
                "title": "The Real Secret",
                "content_html": "<p>The builders who win at marketing aren't spending more time on it. They're spending <strong>better</strong> time. One professional photo shoot per quarter produces enough content to fuel everything else for months. The system runs itself once the content exists.</p>"
            }
        },

        # ─── INLINE GALLERIES ───
        "gallery_1": {
            "columns": 3,
            "images": [
                {"url": "TODO: CDN URL — exterior shot, different project", "alt": "TODO"},
                {"url": "TODO: CDN URL — interior shot, different project", "alt": "TODO"},
                {"url": "TODO: CDN URL — twilight shot, different project", "alt": "TODO"}
            ],
            "caption": "TODO: Project 1 &middot; Project 2 &middot; Project 3 &mdash; Matt Anthony Photography"
        },
        "gallery_2": {
            "columns": 2,
            "images": [
                {"url": "TODO: CDN URL — interior", "alt": "TODO"},
                {"url": "TODO: CDN URL — interior", "alt": "TODO"}
            ],
            "caption": "TODO: Project Names &mdash; Matt Anthony Photography"
        },

        # ─── CASE STUDY (Balmoral) ───
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
                f"I work with builders across BC as an embedded creative partner, not a vendor you call once a year. One shoot per quarter produces enough content to fuel every channel in this plan for months."
            ],
            "bg_image": "TODO: CDN URL — strong interior or twilight exterior",
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
            "headline_html": f"This plan works.<br><em>If it gets executed.</em>",
            "paragraphs": [
                f"TODO: Personal closing. Something like: '{owner_name}, I put this together because {company_name} builds the kind of homes that should be getting more attention than they are. The work is there. The marketing just needs to catch up.'",
                "Every section of this plan connects back to one thing: having professional visual content to fuel the machine. Without it, the website stays thin, the social stays inconsistent, the awards stay unsubmitted, and the best clients keep finding your competitors first.",
                "I specialize in exactly this — architectural and construction photography built specifically for marketing. Not just pretty photos, but a content system that feeds every channel you need.",
                "TODO: Soft CTA. 'If you'd like to talk about getting the content engine started, I'm here. No pitch, just a conversation about what would make the biggest difference for [company] right now.'"
            ],
            "steps": [
                {"number": "1", "title": "Start with GBP", "description": "The highest-ROI action in this plan. Takes an afternoon, pays off for years."},
                {"number": "2", "title": "Shoot One Project", "description": "Pick your best recent build. One professional shoot creates months of content across every channel."},
                {"number": "3", "title": "Build the Rhythm", "description": "Once the content exists, the weekly posting and monthly updates take minutes, not hours."}
            ]
        }
    }

    os.makedirs(CONFIG_DIR, exist_ok=True)
    out_path = os.path.join(CONFIG_DIR, f"{client_slug}-marketing-plan.json")
    with open(out_path, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"Scaffolded: {out_path}")
    print(f"Fill in the TODO fields, then run:")
    print(f"  python3 tools/generate_marketing_plan.py generate {out_path}")
    print(f"  python3 tools/generate_marketing_plan.py generate {out_path} --publish")
    return out_path


def list_configs():
    """List available marketing plan configs."""
    if not os.path.exists(CONFIG_DIR):
        print("No configs found")
        return
    configs = sorted(Path(CONFIG_DIR).glob("*-marketing-plan.json"))
    if not configs:
        print("No marketing plan configs found")
        return
    print("Marketing plan configs:")
    for c in configs:
        with open(c) as f:
            data = json.load(f)
        client = data.get("client", {}).get("company", "?")
        print(f"  {c.name:<45} {client}")


def main():
    parser = argparse.ArgumentParser(description="Generate builder marketing plans")
    sub = parser.add_subparsers(dest="command")

    p_gen = sub.add_parser("generate", help="Generate marketing plan HTML")
    p_gen.add_argument("config", help="Path to config JSON")
    p_gen.add_argument("--output", help="Output HTML path")
    p_gen.add_argument("--publish", action="store_true", help="Publish to GitHub Pages")

    p_scaffold = sub.add_parser("scaffold", help="Create starter config")
    p_scaffold.add_argument("--client", required=True, help="Client slug")
    p_scaffold.add_argument("--owner", required=True, help="Owner/contact name")
    p_scaffold.add_argument("--company", required=True, help="Company name")

    sub.add_parser("list-configs", help="List marketing plan configs")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == "generate":
        generate(args.config, args.output, args.publish)
    elif args.command == "scaffold":
        scaffold(args.client, args.owner, args.company)
    elif args.command == "list-configs":
        list_configs()


if __name__ == "__main__":
    main()
