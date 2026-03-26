"""Generate a homepage redesign mockup for a builder — scrape their site, extract their brand, render a premium version.

Usage:
    python3 tools/generate_homepage_mockup.py create \
      --company "UltraLux Custom Homes" --website "https://ultraluxhomes.ca" \
      [--owner "Owner"] [--location "Vancouver BC"] [--publish]

    python3 tools/generate_homepage_mockup.py render <config.json> [--publish]

    python3 tools/generate_homepage_mockup.py scaffold --company "UltraLux Custom Homes"

The mockup uses THEIR brand — their images, their copy, their colors, their logo.
Wrapped in a modern premium design that shows what their site could look like.
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

try:
    from jinja2 import Environment, BaseLoader
except ImportError:
    print("ERROR: jinja2 required. Run: pip3 install --user jinja2")
    sys.exit(1)

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: requests and beautifulsoup4 required.")
    print("  pip3 install --user requests beautifulsoup4")
    sys.exit(1)

try:
    from PIL import Image
    import numpy as np
    import base64
    import io
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

TEMPLATE_DIR = os.path.join(BASE_DIR, "business", "sales", "templates")
CONFIG_DIR = os.path.join(BASE_DIR, "business", "sales", "configs")
OUTPUT_DIR = os.path.join(BASE_DIR, "business", "sales")
TEMPLATE_FILE = "homepage-mockup.html.j2"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
})
TIMEOUT = 15


# ─────────────────────────────────────────────
# Site Scraper
# ─────────────────────────────────────────────

def fetch_page(url):
    """Fetch a URL, return BeautifulSoup object or None."""
    try:
        resp = SESSION.get(url, timeout=TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"  Could not fetch {url}: {e}", file=sys.stderr)
        return None


def clean_image_url(src, base_url):
    """Normalize an image URL — make absolute, upsize wsimg.com images."""
    if not src or src.startswith("data:"):
        return None
    if src.startswith("//"):
        src = "https:" + src
    elif not src.startswith("http"):
        src = urljoin(base_url, src)
    # Upsize wsimg.com images for hero/gallery use
    if "wsimg.com" in src and "/rs=" in src:
        # Replace resize params with large version
        src = re.sub(r'/rs=[^/]+', '/rs=w:1920,cg:true,m', src)
    return src


def extract_images(soup, base_url):
    """Extract all meaningful images from a page."""
    images = []
    seen = set()

    # <img> tags
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        url = clean_image_url(src, base_url)
        if not url or url in seen:
            continue
        # Skip tiny icons, tracking pixels, social icons
        if any(skip in url.lower() for skip in [
            "favicon", "icon", "logo", "pixel", "tracking", "badge",
            "facebook", "instagram", "twitter", "tiktok", "youtube",
            "1x1", "spacer", "arrow", "chevron"
        ]):
            continue
        alt = img.get("alt", "")
        images.append({"url": url, "alt": alt})
        seen.add(url)

    # Background images from inline styles
    for el in soup.find_all(style=True):
        style = el.get("style", "")
        bg_matches = re.findall(r'background(?:-image)?\s*:\s*url\(["\']?([^"\')\s]+)["\']?\)', style)
        for bg_url in bg_matches:
            url = clean_image_url(bg_url, base_url)
            if url and url not in seen:
                images.append({"url": url, "alt": ""})
                seen.add(url)

    # <source> tags and srcset
    for source in soup.find_all("source"):
        srcset = source.get("srcset", "")
        # Get the largest image from srcset
        parts = srcset.split(",")
        for part in parts:
            part = part.strip().split(" ")[0]
            url = clean_image_url(part, base_url)
            if url and url not in seen:
                images.append({"url": url, "alt": ""})
                seen.add(url)

    return images


def extract_logo(soup, base_url):
    """Try to find the logo image URL."""
    # Common logo patterns
    for selector in [
        'img[class*="logo"]', 'img[alt*="logo"]', 'img[id*="logo"]',
        'a[class*="logo"] img', '.header img', 'header img:first-of-type',
        'nav img:first-of-type', '.navbar-brand img',
    ]:
        logo = soup.select_one(selector)
        if logo:
            src = logo.get("src") or logo.get("data-src") or ""
            url = clean_image_url(src, base_url)
            if url:
                # For logos, get high quality but don't upsize to 1920
                if "wsimg.com" in url:
                    url = re.sub(r'/rs=[^/]+', '/rs=h:100,cg:true,m', url)
                return url
    return None


def extract_colors_from_css(soup):
    """Extract brand colors from inline styles and style tags."""
    colors = {
        "bg": "#FFFFFF",
        "text": "#1B1B1B",
        "accent": "#C9A96E",
        "accent_bg": "#F6F4F0",
        "body_text": "#575757",
    }

    style_text = ""
    for style in soup.find_all("style"):
        style_text += style.get_text() + " "

    # Look for button/accent colors
    btn_colors = re.findall(r'(?:button|btn|cta)[^}]*?(?:background(?:-color)?)\s*:\s*(#[0-9a-fA-F]{3,8}|rgb[a]?\([^)]+\))', style_text, re.IGNORECASE)
    if btn_colors:
        colors["accent"] = btn_colors[0]

    # Look for primary text color
    body_colors = re.findall(r'body[^}]*?color\s*:\s*(#[0-9a-fA-F]{3,8}|rgb[a]?\([^)]+\))', style_text)
    if body_colors:
        colors["text"] = body_colors[0]

    return colors


def extract_fonts(soup):
    """Extract font families from the page."""
    fonts = {"heading": "Archivo Black", "body": "Montserrat"}

    # Check Google Fonts links
    for link in soup.find_all("link", href=True):
        href = link["href"]
        if "fonts.googleapis.com" in href:
            font_matches = re.findall(r'family=([^:&]+)', href)
            for fm in font_matches:
                name = fm.replace("+", " ")
                fonts.setdefault("all", []).append(name)

    # Check CSS for font-family declarations
    style_text = ""
    for style in soup.find_all("style"):
        style_text += style.get_text() + " "

    # Heading fonts (h1, h2)
    heading_fonts = re.findall(r'h[12][^}]*?font-family\s*:\s*["\']?([^"\';\n,]+)', style_text)
    if heading_fonts:
        fonts["heading"] = heading_fonts[0].strip().strip("'\"")

    # Body fonts
    body_fonts = re.findall(r'body[^}]*?font-family\s*:\s*["\']?([^"\';\n,]+)', style_text)
    if body_fonts:
        fonts["body"] = body_fonts[0].strip().strip("'\"")

    return fonts


def extract_text_content(soup):
    """Extract meaningful text content organized by type."""
    content = {
        "headings": [],
        "paragraphs": [],
        "hero_text": "",
        "tagline": "",
    }

    # Page title
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text().strip()
        # Extract tagline from title
        for sep in ["|", " - ", ":"]:
            if sep in title:
                parts = title.split(sep)
                if len(parts) >= 2:
                    content["tagline"] = parts[-1].strip()
                break

    # All headings
    for tag in ["h1", "h2", "h3"]:
        for el in soup.find_all(tag):
            text = el.get_text(separator=" ", strip=True)
            if text and len(text) > 3 and len(text) < 200:
                content["headings"].append({"level": tag, "text": text})

    # Hero text (first h1 or large heading)
    h1 = soup.find("h1")
    if h1:
        content["hero_text"] = h1.get_text(separator=" ", strip=True)

    # Paragraphs (meaningful ones, not tiny footer text)
    for p in soup.find_all("p"):
        text = p.get_text(separator=" ", strip=True)
        if text and 30 < len(text) < 1000:
            content["paragraphs"].append(text)

    return content


def extract_contact_info(soup, base_url):
    """Extract phone, email, address from the page."""
    text = soup.get_text()
    contact = {}

    # Phone
    phone_match = re.search(r'\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}', text)
    if phone_match:
        contact["phone"] = phone_match.group()

    # Email
    for a in soup.find_all("a", href=True):
        if a["href"].startswith("mailto:"):
            contact["email"] = a["href"].replace("mailto:", "").split("?")[0]
            break

    if "email" not in contact:
        email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
        if email_match:
            contact["email"] = email_match.group()

    # Address — look for common patterns
    for el in soup.find_all(["p", "span", "div", "address"]):
        el_text = el.get_text(strip=True)
        if re.search(r'\d+.*(?:street|st|ave|road|rd|blvd|drive|dr|way)\b', el_text, re.IGNORECASE):
            contact["address"] = el_text[:200]
            break

    return contact


def extract_services(soup):
    """Extract service offerings from the page."""
    services = []
    seen = set()

    # Look for service cards/sections
    for container in soup.find_all(["section", "div"], class_=True):
        classes = " ".join(container.get("class", []))
        if not any(kw in classes.lower() for kw in ["service", "card", "feature", "offer"]):
            continue
        heading = container.find(["h2", "h3", "h4"])
        desc = container.find("p")
        if heading:
            title = heading.get_text(strip=True)
            if title and title not in seen and len(title) < 100:
                svc = {"title": title}
                if desc:
                    svc["description"] = desc.get_text(strip=True)[:300]
                services.append(svc)
                seen.add(title)

    return services


def process_logo(logo_url):
    """Download a logo, remove white background, and create a white version.

    Returns (transparent_data_uri, white_data_uri) on success,
    or (original_url, None) if PIL is unavailable or processing fails.
    """
    if not HAS_PIL or not logo_url:
        return (logo_url, None)

    try:
        resp = SESSION.get(logo_url, timeout=TIMEOUT)
        resp.raise_for_status()
        image_bytes = resp.content

        img = Image.open(io.BytesIO(image_bytes)).convert('RGBA')
        data = np.array(img)
        r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]

        # White pixels -> transparent
        threshold = 240
        white_mask = (r > threshold) & (g > threshold) & (b > threshold)
        data[white_mask, 3] = 0

        # Anti-aliased edges
        near_white = (r > 200) & (g > 200) & (b > 200) & ~white_mask
        whiteness = np.minimum(r.astype(float), np.minimum(g.astype(float), b.astype(float)))
        edge_alpha = np.clip((255 - whiteness) * (255 / 55), 0, 255).astype(np.uint8)
        data[near_white, 3] = edge_alpha[near_white]

        result = Image.fromarray(data)

        # Transparent version -> base64
        buf = io.BytesIO()
        result.save(buf, format='PNG')
        logo_b64 = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

        # White version (all visible pixels turned white, for dark backgrounds)
        white_data = data.copy()
        visible = white_data[:,:,3] > 0
        white_data[visible, 0] = 255
        white_data[visible, 1] = 255
        white_data[visible, 2] = 255
        white_result = Image.fromarray(white_data)
        buf2 = io.BytesIO()
        white_result.save(buf2, format='PNG')
        logo_white_b64 = 'data:image/png;base64,' + base64.b64encode(buf2.getvalue()).decode()

        print(f"    Logo processed: background removed + white version created")
        return (logo_b64, logo_white_b64)

    except Exception as e:
        print(f"    Logo processing failed ({e}), using original URL", file=sys.stderr)
        return (logo_url, None)


def scrape_site(website, company_name):
    """Deep-scrape a builder's website to extract brand, content, and images."""
    print(f"  Scraping {website}...")
    base_url = website.rstrip("/")

    data = {
        "images": [],
        "logo_url": None,
        "colors": {},
        "fonts": {},
        "content": {},
        "contact": {},
        "services": [],
        "pages_scraped": [],
    }

    # Scrape homepage
    homepage = fetch_page(base_url)
    if not homepage:
        print("  ERROR: Could not fetch homepage", file=sys.stderr)
        return data

    data["images"] = extract_images(homepage, base_url)
    raw_logo_url = extract_logo(homepage, base_url)
    logo_transparent, logo_white = process_logo(raw_logo_url)
    data["logo_url"] = logo_transparent
    data["logo_white_url"] = logo_white
    data["colors"] = extract_colors_from_css(homepage)
    data["fonts"] = extract_fonts(homepage)
    data["content"] = extract_text_content(homepage)
    data["contact"] = extract_contact_info(homepage, base_url)
    data["pages_scraped"].append("homepage")

    print(f"    Homepage: {len(data['images'])} images, logo={'found' if data['logo_url'] else 'not found'}")

    # Find nav links to scrape additional pages
    nav_pages = {}
    for a in homepage.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True).lower()
        if text in ["about", "services", "gallery", "portfolio", "projects",
                     "process", "our work", "what we do", "contact", "contact us"]:
            full_url = urljoin(base_url + "/", href)
            parsed = urlparse(full_url)
            base_parsed = urlparse(base_url)
            if parsed.netloc == base_parsed.netloc or not parsed.netloc:
                nav_pages[text] = full_url

    # Scrape key pages
    for page_name, page_url in nav_pages.items():
        time.sleep(0.5)  # Rate limit
        print(f"    Scraping /{page_name}...")
        soup = fetch_page(page_url)
        if not soup:
            continue

        page_images = extract_images(soup, page_url)
        data["images"].extend(page_images)
        data["pages_scraped"].append(page_name)

        # Extract page-specific content
        page_content = extract_text_content(soup)

        if page_name in ["about"]:
            data["about_content"] = page_content
        elif page_name in ["services", "what we do"]:
            data["services_content"] = page_content
            svcs = extract_services(soup)
            if svcs:
                data["services"] = svcs
        elif page_name in ["process"]:
            data["process_content"] = page_content
        elif page_name in ["gallery", "portfolio", "projects", "our work"]:
            data["gallery_content"] = page_content
            print(f"      Found {len(page_images)} gallery images")
        elif page_name in ["contact", "contact us"]:
            contact = extract_contact_info(soup, page_url)
            data["contact"].update(contact)

    # Deduplicate images
    seen_urls = set()
    unique_images = []
    for img in data["images"]:
        # Normalize URL for dedup (strip resize params)
        norm_url = re.sub(r'/rs=[^/]+', '', img["url"])
        if norm_url not in seen_urls:
            unique_images.append(img)
            seen_urls.add(norm_url)
    data["images"] = unique_images

    print(f"  Scrape complete: {len(data['images'])} unique images, {len(data['pages_scraped'])} pages")
    return data


# ─────────────────────────────────────────────
# Config Builder
# ─────────────────────────────────────────────

def slugify(name):
    """Convert company name to URL-safe slug."""
    slug = name.lower().strip()
    for suffix in ["ltd.", "ltd", "inc.", "inc", "corp.", "corp", "group",
                    "construction", "homes", "builders", "building", "custom"]:
        slug = re.sub(rf'\b{re.escape(suffix)}\b', '', slug)
    slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
    slug = re.sub(r'-+', '-', slug)
    return slug or "builder"


def pick_best_images(images, count, prefer_keywords=None):
    """Pick the best images from a list, preferring those with relevant alt text."""
    if not images:
        return []
    if prefer_keywords:
        scored = []
        for img in images:
            alt = (img.get("alt", "") or "").lower()
            score = sum(1 for kw in prefer_keywords if kw in alt)
            scored.append((score, img))
        scored.sort(key=lambda x: -x[0])
        return [s[1] for s in scored[:count]]
    return images[:count]


def build_config(company_name, website, scrape_data, owner_name=None, location=None):
    """Build a homepage mockup config from scraped site data."""

    slug = slugify(company_name)
    domain = website.replace("https://", "").replace("http://", "").rstrip("/")

    # Brand data from scrape
    colors = scrape_data.get("colors", {})
    fonts = scrape_data.get("fonts", {})
    content = scrape_data.get("content", {})
    contact = scrape_data.get("contact", {})
    images = scrape_data.get("images", [])
    logo_url = scrape_data.get("logo_url")
    logo_white_url = scrape_data.get("logo_white_url")
    services_list = scrape_data.get("services", [])

    # Location
    loc = location or "British Columbia"

    # Build Google Fonts import string
    heading_font = fonts.get("heading", "Archivo Black")
    body_font = fonts.get("body", "Montserrat")
    font_import = f"{heading_font.replace(' ', '+')}:wght@400;700&family={body_font.replace(' ', '+')}:wght@300;400;500;600"

    # Hero image — pick the first large image (usually the hero/banner)
    hero_img = images[0]["url"] if images else ""

    # Gallery images — skip the first (hero), take next several
    gallery_images = images[1:10] if len(images) > 1 else images[:3]

    # Break images (for photo separators between sections)
    all_imgs = images[3:] if len(images) > 3 else images
    break_imgs = []
    for i, img in enumerate(all_imgs[:4]):
        break_imgs.append({
            "url": img["url"],
            "alt": img.get("alt", f"{company_name} project"),
            "caption": "",
        })

    # Projects — build from gallery images
    projects = []
    for i, img in enumerate(gallery_images[:6]):
        alt = img.get("alt", "")
        projects.append({
            "name": alt if alt and len(alt) > 3 else f"Project {i + 1}",
            "location": loc,
            "description": "",
            "image_url": img["url"],
        })

    # About image
    about_img = images[2]["url"] if len(images) > 2 else (images[0]["url"] if images else "")

    # Copy from their site
    hero_text = content.get("hero_text", "")
    tagline = content.get("tagline", "")
    paragraphs = content.get("paragraphs", [])

    # Hero headline — use their actual h1 or tagline
    if hero_text and len(hero_text) < 80:
        hero_headline_html = hero_text
    elif tagline and len(tagline) < 60:
        hero_headline_html = tagline
    else:
        hero_headline_html = f"{company_name}"

    # Hero subtitle — use their first meaningful paragraph
    hero_subtitle = ""
    for p in paragraphs:
        if len(p) > 40 and len(p) < 200:
            hero_subtitle = p
            break
    if not hero_subtitle:
        hero_subtitle = f"Custom homes built with precision, designed for the way you live."

    # About paragraphs — pull from their about page or homepage
    about_paragraphs = []
    about_content = scrape_data.get("about_content", {})
    if about_content and about_content.get("paragraphs"):
        about_paragraphs = about_content["paragraphs"][:3]
    elif paragraphs:
        about_paragraphs = paragraphs[:3]
    else:
        about_paragraphs = [
            f"{company_name} is a design-build firm specializing in custom homes.",
            "From concept through completion, every project reflects our commitment to quality craftsmanship and transparent communication."
        ]

    # Process steps — pull from their process page or use their services
    process_steps = []
    process_content = scrape_data.get("process_content", {})
    if process_content and process_content.get("headings"):
        for h in process_content["headings"]:
            if h["level"] in ["h2", "h3"] and len(h["text"]) < 60:
                process_steps.append({"title": h["text"], "description": ""})
        # Try to pair with paragraphs
        process_paragraphs = process_content.get("paragraphs", [])
        for i, step in enumerate(process_steps):
            if i < len(process_paragraphs):
                step["description"] = process_paragraphs[i][:200]

    # Services — use scraped services or fall back to headings
    services = []
    if services_list:
        services = services_list[:6]
    else:
        services_content = scrape_data.get("services_content", {})
        if services_content and services_content.get("headings"):
            for h in services_content["headings"]:
                if h["level"] in ["h2", "h3"] and len(h["text"]) < 60:
                    services.append({"title": h["text"], "description": ""})

    # Nav items — based on what sections we have content for
    nav_items = ["Projects"]
    if about_paragraphs:
        nav_items.append("About")
    if services:
        nav_items.append("Services")
    if process_steps:
        nav_items.append("Process")
    nav_items.append("Contact")

    config = {
        "builder": {
            "company": company_name,
            "slug": slug,
            "location": loc,
            "email": contact.get("email", f"info@{domain}"),
            "phone": contact.get("phone", ""),
            "address": contact.get("address", ""),
            "website": website,
            "logo_url": logo_url or "",
            "logo_white_url": logo_white_url or "",
            "colors": {
                "primary": colors.get("text", "#1B1B1B"),
                "accent": colors.get("accent", "#C9A96E"),
                "accent_bg": colors.get("accent_bg", "#F6F4F0"),
                "light": "#FFFFFF",
                "dark": colors.get("text", "#1A1A18"),
                "body_text": colors.get("body_text", "#575757"),
            },
            "fonts": {
                "heading": heading_font,
                "body": body_font,
                "import": font_import,
            },
        },
        "nav_items": nav_items,
        "mockup": {
            "type": "homepage-mockup",
            "date": datetime.now().strftime("%B %Y"),
            "filename": f"{slug}-homepage-mockup.html",
        },
        "hero": {
            "eyebrow": loc,
            "headline_html": hero_headline_html,
            "subtitle": hero_subtitle,
            "cta_text": "View Our Work",
            "cta_secondary": "Get in Touch",
            "image_url": hero_img,
            "image_position": "center 30%",
        },
        "projects_eyebrow": "Portfolio",
        "projects_headline_html": "Our Work",
        "projects_lead": "",
        "projects": projects,
        "images": {"breaks": break_imgs},
        "about": {
            "eyebrow": "About",
            "headline_html": f"About {company_name}",
            "paragraphs": about_paragraphs,
            "image_url": about_img,
        },
        "stats": [
            {"value": "20+", "label": "Years Experience"},
            {"value": "100+", "label": "Homes Built"},
            {"value": "100%", "label": "Client Satisfaction"},
        ],
        "photographer": {
            "name": "Matt Anthony Photography",
            "cta_url": "https://mattanthonyphoto.com/discovery-call",
            "cta_text": "Book a Discovery Call",
        },
        "contact": {
            "eyebrow": "Get in Touch",
            "headline_html": f"Start Your<br>Next Project",
            "subtitle": f"Ready to build? Contact {company_name} to discuss your vision.",
            "cta_text": "Get in Touch",
        },
        "year": str(datetime.now().year),
    }

    # Optional sections
    if services:
        config["services"] = {
            "eyebrow": "Services",
            "headline_html": "What We Do",
            "items": services,
        }

    if process_steps and len(process_steps) >= 2:
        config["process"] = {
            "eyebrow": "Our Process",
            "headline_html": "How We Build",
            "lead": "",
            "steps": process_steps[:4],
        }

    # SEO footer — service areas, contact, structured data
    config["footer"] = {
        "description": f"{company_name} is a custom home builder serving {loc}. Design, construction, and project management for residential builds.",
        "hours": "Mon\u2013Fri 9am\u20135pm",
        "service_areas": [loc] if loc else ["British Columbia"],
    }

    return config


# ─────────────────────────────────────────────
# Render & Publish
# ─────────────────────────────────────────────

def render(config_path, output_path=None, publish=False):
    """Render a homepage mockup HTML from a JSON config."""
    config_path = Path(config_path)
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        return None

    with open(config_path) as f:
        config = json.load(f)

    required = ["builder", "hero"]
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
        slug = config["builder"]["slug"]
        filename = config.get("mockup", {}).get("filename", f"{slug}-homepage-mockup.html")
        output_path = os.path.join(OUTPUT_DIR, filename)

    with open(output_path, "w") as f:
        f.write(html)

    size = os.path.getsize(output_path) / 1024
    print(f"Generated: {output_path} ({size:.1f} KB)")

    if publish:
        slug = config["builder"]["slug"]
        filename = config.get("mockup", {}).get("filename", f"{slug}-homepage-mockup.html")
        try:
            from tools.publish_proposal import upload
            url = upload(output_path, slug, filename)
            if url:
                print(f"Published: {url}")
                return url
        except Exception as e:
            print(f"WARNING: Publish failed: {e}", file=sys.stderr)

    return output_path


def scaffold(company_name):
    """Create a starter config with placeholder values."""
    slug = slugify(company_name)
    scrape_data = {"images": [], "colors": {}, "fonts": {}, "content": {}, "contact": {}}
    config = build_config(company_name, f"https://{slug}.com", scrape_data)

    config_path = os.path.join(CONFIG_DIR, f"{slug}-homepage-mockup.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Scaffold created: {config_path}")
    return config_path


def generate(company_name, website, owner_name=None, location=None, publish=False):
    """Full pipeline: scrape site → build config → render → optionally publish."""
    slug = slugify(company_name)

    # Step 1: Scrape site
    print(f"\n[1/3] Scraping {website}...")
    scrape_data = scrape_site(website, company_name)

    # Step 2: Build config
    print(f"[2/3] Building config from scraped data...")
    config = build_config(company_name, website, scrape_data, owner_name, location)

    config_path = os.path.join(CONFIG_DIR, f"{slug}-homepage-mockup.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"  Config saved: {config_path}")

    # Step 3: Render + optional publish
    print(f"[3/3] Rendering mockup...")
    result = render(config_path, publish=publish)

    return result


def main():
    parser = argparse.ArgumentParser(description="Generate homepage redesign mockups for builders")
    subparsers = parser.add_subparsers(dest="command")

    gen_parser = subparsers.add_parser("create", help="Scrape + generate + optionally publish")
    gen_parser.add_argument("--company", required=True, help="Builder company name")
    gen_parser.add_argument("--website", required=True, help="Builder website URL")
    gen_parser.add_argument("--owner", default=None, help="Owner/contact name")
    gen_parser.add_argument("--location", default=None, help="City Province")
    gen_parser.add_argument("--publish", action="store_true", help="Publish to GitHub Pages")

    render_parser = subparsers.add_parser("render", help="Render from existing config")
    render_parser.add_argument("config", help="Path to JSON config")
    render_parser.add_argument("--output", default=None, help="Output HTML path")
    render_parser.add_argument("--publish", action="store_true", help="Publish to GitHub Pages")

    scaffold_parser = subparsers.add_parser("scaffold", help="Create starter config")
    scaffold_parser.add_argument("--company", required=True, help="Builder company name")

    args = parser.parse_args()

    if args.command == "create":
        generate(args.company, args.website, args.owner, args.location, args.publish)
    elif args.command == "render":
        render(args.config, args.output, args.publish)
    elif args.command == "scaffold":
        scaffold(args.company)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
