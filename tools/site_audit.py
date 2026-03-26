"""Perform a real SEO and local audit on a given website URL.

Usage:
    python3 tools/site_audit.py <url> "<company name>" [--location "City Province"] [--output path.json]

Example:
    python3 tools/site_audit.py https://summerhill.build "Summerhill Fine Homes" --location "Gibsons BC" --output business/sales/configs/summerhill-audit-data.json

Outputs JSON with scores, findings, and raw meta data that can feed into generate_audit.py configs.
"""

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from urllib.parse import urljoin, urlparse

try:
    import requests
except ImportError:
    print("ERROR: requests required. Run: pip3 install --user requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: beautifulsoup4 required. Run: pip3 install --user beautifulsoup4")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})
TIMEOUT = 15
CRAWL_DELAY = 1.0  # seconds between requests
MAX_PAGES = 30  # don't crawl the entire internet

_last_request_time = 0.0


def _rate_limit():
    """Ensure at least CRAWL_DELAY seconds between requests."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < CRAWL_DELAY:
        time.sleep(CRAWL_DELAY - elapsed)
    _last_request_time = time.time()


def fetch(url, allow_redirects=True):
    """Fetch a URL with rate limiting and error handling. Returns (response, error_string)."""
    _rate_limit()
    try:
        r = SESSION.get(url, timeout=TIMEOUT, allow_redirects=allow_redirects)
        return r, None
    except requests.exceptions.SSLError as e:
        return None, f"SSL error: {e}"
    except requests.exceptions.ConnectionError as e:
        return None, f"Connection error: {e}"
    except requests.exceptions.Timeout:
        return None, "Timeout"
    except requests.exceptions.RequestException as e:
        return None, str(e)


def fetch_soup(url):
    """Fetch and parse HTML. Returns (soup, response, error)."""
    r, err = fetch(url)
    if err:
        return None, None, err
    if r.status_code != 200:
        return None, r, f"HTTP {r.status_code}"
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        return soup, r, None
    except Exception as e:
        return None, r, f"Parse error: {e}"


# ---------------------------------------------------------------------------
# 1. Homepage & Technical Analysis
# ---------------------------------------------------------------------------

def check_ssl(url):
    """Check if HTTPS works."""
    parsed = urlparse(url)
    https_url = f"https://{parsed.netloc}{parsed.path}"
    r, err = fetch(https_url, allow_redirects=False)
    if err:
        return {"ssl_valid": False, "detail": err}
    return {"ssl_valid": r is not None and r.status_code < 500, "status": r.status_code if r else None}


def check_redirects(url):
    """Check redirect chain."""
    _rate_limit()
    try:
        r = SESSION.get(url, timeout=TIMEOUT, allow_redirects=True)
        chain = []
        if r.history:
            for h in r.history:
                chain.append({"url": h.url, "status": h.status_code})
        chain.append({"url": r.url, "status": r.status_code})
        return {
            "final_url": r.url,
            "redirect_count": len(r.history),
            "chain": chain,
            "has_www_redirect": any("www" in urlparse(h.url).netloc for h in r.history) if r.history else False,
            "https_redirect": any(urlparse(h.url).scheme == "http" for h in r.history) if r.history else False,
        }
    except Exception as e:
        return {"error": str(e)}


def analyze_page(soup, response):
    """Extract SEO signals from a parsed page."""
    result = {}

    # Meta title
    title_tag = soup.find("title")
    result["title"] = title_tag.get_text(strip=True) if title_tag else None
    result["title_length"] = len(result["title"]) if result["title"] else 0

    # Meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    result["meta_description"] = meta_desc["content"] if meta_desc and meta_desc.get("content") else None
    result["meta_description_length"] = len(result["meta_description"]) if result["meta_description"] else 0

    # Open Graph
    og_tags = {}
    for og in soup.find_all("meta", attrs={"property": re.compile(r"^og:")}):
        prop = og.get("property", "")
        content = og.get("content", "")
        if prop and content:
            og_tags[prop] = content
    result["og_tags"] = og_tags
    result["has_og_image"] = "og:image" in og_tags
    result["has_og_title"] = "og:title" in og_tags

    # Canonical
    canonical = soup.find("link", attrs={"rel": "canonical"})
    result["canonical"] = canonical["href"] if canonical and canonical.get("href") else None

    # Headings
    h1s = soup.find_all("h1")
    h2s = soup.find_all("h2")
    result["h1_count"] = len(h1s)
    result["h1_texts"] = [h.get_text(strip=True)[:120] for h in h1s[:5]]
    result["h2_count"] = len(h2s)
    result["h2_texts"] = [h.get_text(strip=True)[:120] for h in h2s[:10]]

    # Word count (visible text)
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    words = text.split()
    result["word_count"] = len(words)

    # Images
    images = soup.find_all("img")
    result["image_count"] = len(images)
    missing_alt = sum(1 for img in images if not img.get("alt") or img["alt"].strip() == "")
    result["images_missing_alt"] = missing_alt

    # Links
    links = soup.find_all("a", href=True)
    page_domain = urlparse(response.url).netloc if response else ""
    internal = 0
    external = 0
    for link in links:
        href = link["href"]
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        parsed = urlparse(urljoin(response.url, href)) if response else urlparse(href)
        if parsed.netloc == page_domain or not parsed.netloc:
            internal += 1
        else:
            external += 1
    result["internal_links"] = internal
    result["external_links"] = external

    # Schema.org JSON-LD
    json_ld = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type"):
                        json_ld.append(item.get("@type"))
            elif isinstance(data, dict):
                if data.get("@type"):
                    json_ld.append(data["@type"])
                if data.get("@graph"):
                    for item in data["@graph"]:
                        if isinstance(item, dict) and item.get("@type"):
                            json_ld.append(item.get("@type"))
        except (json.JSONDecodeError, TypeError):
            pass
    result["schema_types"] = json_ld

    # Page size estimate
    if response:
        result["page_size_kb"] = round(len(response.content) / 1024, 1)
        result["response_time_ms"] = round(response.elapsed.total_seconds() * 1000)

    return result


def check_robots_txt(base_url):
    """Fetch and analyze robots.txt."""
    url = urljoin(base_url, "/robots.txt")
    r, err = fetch(url)
    if err:
        return {"exists": False, "error": err}
    if r.status_code != 200:
        return {"exists": False, "status": r.status_code}
    text = r.text
    has_sitemap = "sitemap:" in text.lower()
    sitemap_urls = re.findall(r"(?i)sitemap:\s*(https?://\S+)", text)
    disallowed = re.findall(r"(?i)disallow:\s*(\S+)", text)
    return {
        "exists": True,
        "has_sitemap_reference": has_sitemap,
        "sitemap_urls": sitemap_urls,
        "disallowed_paths": disallowed[:20],
        "length": len(text),
    }


def check_sitemap(base_url, robots_data):
    """Fetch and analyze sitemap.xml."""
    urls_to_try = []
    if robots_data.get("sitemap_urls"):
        urls_to_try.extend(robots_data["sitemap_urls"])
    urls_to_try.append(urljoin(base_url, "/sitemap.xml"))
    urls_to_try.append(urljoin(base_url, "/sitemap_index.xml"))

    for sitemap_url in urls_to_try:
        r, err = fetch(sitemap_url)
        if err or not r or r.status_code != 200:
            continue
        content = r.text
        if "<urlset" in content or "<sitemapindex" in content:
            url_count = content.count("<loc>")
            is_index = "<sitemapindex" in content
            return {
                "exists": True,
                "url": sitemap_url,
                "is_index": is_index,
                "url_count": url_count,
            }

    return {"exists": False}


# ---------------------------------------------------------------------------
# 2. Google Business Profile Check
# ---------------------------------------------------------------------------

def check_gbp(company_name, location):
    """Try to detect Google Business Profile presence via search.
    NOTE: Google blocks automated scraping, so this is best-effort."""
    query = f"{company_name} {location}" if location else company_name
    search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
    r, err = fetch(search_url)
    if err:
        return {"checked": False, "error": err}
    if r.status_code != 200:
        return {"checked": False, "error": f"HTTP {r.status_code} (Google likely blocking automated requests)"}

    text = r.text.lower()
    indicators = {
        "knowledge_panel": any(x in text for x in ["kp-header", "knowledge-panel", "kno-ecr-pt"]),
        "maps_link": "maps.google" in text or "google.com/maps" in text,
        "rating_found": bool(re.search(r'(\d\.\d)\s*stars?|\d\.\d\s*\(\d+\)', text)),
        "hours_found": any(x in text for x in ["opening hours", "open now", "closed now", "hours"]),
        "phone_found": bool(re.search(r'\(\d{3}\)\s*\d{3}[\-\s]\d{4}', text)),
    }
    score = sum(1 for v in indicators.values() if v)
    indicators["likely_has_gbp"] = score >= 2
    indicators["confidence_note"] = (
        "Google often blocks automated requests. Verify manually." if score < 2
        else "Multiple GBP indicators found."
    )
    return {"checked": True, **indicators}


# ---------------------------------------------------------------------------
# 3. Local Directory Checks
# ---------------------------------------------------------------------------

def check_directory(name, url_template, company_name):
    """Check if a company appears on a directory site."""
    search_name = company_name.lower().replace(" ", "+")

    if name == "Houzz":
        url = f"https://www.houzz.com/professionals/query/{requests.utils.quote(company_name)}"
    elif name == "HomeStars":
        url = f"https://homestars.com/search?utf8=%E2%9C%93&search%5Bquery%5D={requests.utils.quote(company_name)}"
    elif name == "CHBA":
        url = f"https://www.chba.ca/find-a-member/?search={requests.utils.quote(company_name)}"
    else:
        url = url_template.format(query=requests.utils.quote(company_name))

    r, err = fetch(url)
    if err:
        return {"directory": name, "checked": False, "error": err}
    if r.status_code != 200:
        return {"directory": name, "checked": True, "found": False, "note": f"HTTP {r.status_code}"}

    text = r.text.lower()
    name_parts = company_name.lower().split()
    # Check if enough words from the company name appear in results
    matches = sum(1 for part in name_parts if len(part) > 3 and part in text)
    found = matches >= max(1, len([p for p in name_parts if len(p) > 3]) // 2)

    return {"directory": name, "checked": True, "found": found, "url": r.url}


def check_local_directories(company_name):
    """Check presence on major local directories."""
    directories = [
        ("Houzz", None),
        ("HomeStars", None),
        ("CHBA", None),
    ]
    results = []
    for name, template in directories:
        result = check_directory(name, template, company_name)
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# 4. Crawl Project/Portfolio Pages
# ---------------------------------------------------------------------------

def discover_internal_links(soup, base_url):
    """Extract all internal links from a page."""
    base_domain = urlparse(base_url).netloc
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
            # Clean URL (remove fragments and trailing slashes for dedup)
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
            if not any(ext in parsed.path.lower() for ext in [".pdf", ".jpg", ".png", ".gif", ".svg", ".webp", ".mp4"]):
                links.add(clean)
    return links


def identify_project_pages(all_pages):
    """Identify which crawled pages are likely project/portfolio pages."""
    project_keywords = [
        "project", "portfolio", "work", "gallery", "case-study",
        "homes", "builds", "properties", "residential", "commercial",
        "custom-home", "renovation", "design", "featured",
    ]
    project_pages = []
    for url, data in all_pages.items():
        path = urlparse(url).path.lower()
        is_project = any(kw in path for kw in project_keywords)
        # Also check if it's a subpage of a project section
        if not is_project and data.get("h1_texts"):
            h1_lower = " ".join(data["h1_texts"]).lower()
            is_project = any(kw in h1_lower for kw in ["project", "home", "residence", "house"])
        if is_project:
            project_pages.append({
                "url": url,
                "title": data.get("title", ""),
                "word_count": data.get("word_count", 0),
                "image_count": data.get("image_count", 0),
                "has_description": data.get("word_count", 0) > 100,
            })
    return project_pages


def crawl_site(start_url):
    """Crawl internal pages starting from the homepage."""
    visited = {}
    to_visit = {start_url.rstrip("/")}
    base_domain = urlparse(start_url).netloc

    print(f"  Crawling {base_domain}...", file=sys.stderr)

    while to_visit and len(visited) < MAX_PAGES:
        url = to_visit.pop()
        if url in visited:
            continue

        soup, response, err = fetch_soup(url)
        if err:
            visited[url] = {"error": err}
            continue

        page_data = analyze_page(soup, response)
        visited[url] = page_data

        # Discover more links
        new_links = discover_internal_links(soup, url)
        for link in new_links:
            if link not in visited:
                to_visit.add(link)

        count = len(visited)
        if count % 5 == 0:
            print(f"    ...crawled {count} pages", file=sys.stderr)

    print(f"  Crawled {len(visited)} pages total.", file=sys.stderr)
    return visited


# ---------------------------------------------------------------------------
# 5. Scoring & Report Generation
# ---------------------------------------------------------------------------

def calculate_scores(homepage_data, robots, sitemap, redirects, ssl, gbp, directories, project_pages, all_pages):
    """Calculate 0-100 scores for SEO, Local, Content, Visual Assets."""

    scores = {"seo": 100, "local": 100, "content": 100, "visual_assets": 100}
    findings = {"seo": [], "local": [], "content": [], "visual_assets": []}

    # --- SEO SCORING ---

    # SSL
    if not ssl.get("ssl_valid"):
        findings["seo"].append({"status": "fail", "title": "No valid SSL certificate", "detail": f"HTTPS check failed: {ssl.get('detail', 'unknown error')}"})
    else:
        findings["seo"].append({"status": "pass", "title": "Valid SSL certificate", "detail": "Site is served over HTTPS."})

    # Redirect chain
    rc = redirects.get("redirect_count", 0)
    if rc > 2:
        findings["seo"].append({"status": "fail", "title": f"Long redirect chain ({rc} redirects)", "detail": f"Chain: {' -> '.join(s['url'] for s in redirects.get('chain', []))}"})
    elif rc > 0:
        findings["seo"].append({"status": "pass", "title": f"Clean redirect ({rc} hop{'s' if rc > 1 else ''})", "detail": f"Final URL: {redirects.get('final_url', 'unknown')}"})

    # Meta title
    hp = homepage_data or {}
    if not hp.get("title"):
        findings["seo"].append({"status": "fail", "title": "Missing meta title", "detail": "The homepage has no <title> tag."})
    elif hp.get("title_length", 0) > 70:
        findings["seo"].append({"status": "warn", "title": f"Meta title too long ({hp['title_length']} chars)", "detail": f"Title: \"{hp['title']}\". Recommended: 50-60 characters."})
    elif hp.get("title_length", 0) < 20:
        findings["seo"].append({"status": "warn", "title": f"Meta title too short ({hp['title_length']} chars)", "detail": f"Title: \"{hp['title']}\". Should be more descriptive."})
    else:
        findings["seo"].append({"status": "pass", "title": "Good meta title", "detail": f"\"{hp['title']}\" ({hp['title_length']} chars)"})

    # Meta description
    if not hp.get("meta_description"):
        findings["seo"].append({"status": "fail", "title": "Missing meta description", "detail": "The homepage has no meta description tag. Search engines will auto-generate one."})
    elif hp.get("meta_description_length", 0) > 160:
        findings["seo"].append({"status": "warn", "title": f"Meta description too long ({hp['meta_description_length']} chars)", "detail": "Recommended: 120-155 characters."})
    elif hp.get("meta_description_length", 0) < 70:
        findings["seo"].append({"status": "warn", "title": f"Meta description too short ({hp['meta_description_length']} chars)", "detail": f"\"{hp['meta_description']}\""})
    else:
        findings["seo"].append({"status": "pass", "title": "Good meta description", "detail": f"\"{hp['meta_description'][:100]}...\" ({hp['meta_description_length']} chars)"})

    # H1
    h1_count = hp.get("h1_count", 0)
    if h1_count == 0:
        findings["seo"].append({"status": "fail", "title": "No H1 tag on homepage", "detail": "Every page should have exactly one H1."})
    elif h1_count > 1:
        findings["seo"].append({"status": "warn", "title": f"Multiple H1 tags ({h1_count})", "detail": f"H1s found: {', '.join(hp.get('h1_texts', []))}"})
    else:
        findings["seo"].append({"status": "pass", "title": "Single H1 tag", "detail": f"\"{hp.get('h1_texts', [''])[0]}\""})

    # Open Graph
    if not hp.get("has_og_image") or not hp.get("has_og_title"):
        missing = []
        if not hp.get("has_og_image"):
            missing.append("og:image")
        if not hp.get("has_og_title"):
            missing.append("og:title")
        findings["seo"].append({"status": "warn", "title": f"Missing Open Graph tags: {', '.join(missing)}", "detail": "Social media shares will look generic without proper OG tags."})
    else:
        findings["seo"].append({"status": "pass", "title": "Open Graph tags present", "detail": f"og:title, og:image found."})

    # Schema / JSON-LD
    schema_types = hp.get("schema_types", [])
    if not schema_types:
        findings["seo"].append({"status": "fail", "title": "No structured data (schema.org)", "detail": "No JSON-LD found. Add LocalBusiness, Organization, or WebSite schema."})
    else:
        findings["seo"].append({"status": "pass", "title": f"Structured data found: {', '.join(schema_types)}", "detail": "JSON-LD schema detected on homepage."})

    # Robots.txt
    if not robots.get("exists"):
        findings["seo"].append({"status": "fail", "title": "No robots.txt", "detail": "Missing robots.txt file. Search engines have no crawl guidance."})
    else:
        findings["seo"].append({"status": "pass", "title": "robots.txt exists", "detail": f"{len(robots.get('disallowed_paths', []))} disallowed paths."})

    # Sitemap
    if not sitemap.get("exists"):
        findings["seo"].append({"status": "fail", "title": "No sitemap.xml found", "detail": "Missing sitemap. Search engines can't efficiently discover pages."})
    else:
        findings["seo"].append({"status": "pass", "title": f"Sitemap found ({sitemap.get('url_count', '?')} URLs)", "detail": f"URL: {sitemap.get('url', 'unknown')}"})

    # Canonical tag
    if not hp.get("canonical"):
        findings["seo"].append({"status": "warn", "title": "No canonical tag on homepage", "detail": "Add a canonical tag to prevent duplicate content issues."})
    else:
        findings["seo"].append({"status": "pass", "title": "Canonical tag present", "detail": f"{hp['canonical']}"})

    # Page speed indicators
    response_time = hp.get("response_time_ms", 0)
    page_size = hp.get("page_size_kb", 0)
    if response_time > 3000:
        findings["seo"].append({"status": "fail", "title": f"Slow server response ({response_time}ms)", "detail": "First byte took over 3 seconds. Indicates server performance issues."})
    elif response_time > 1500:
        findings["seo"].append({"status": "warn", "title": f"Moderate server response ({response_time}ms)", "detail": "Aim for under 500ms TTFB."})
    else:
        findings["seo"].append({"status": "pass", "title": f"Good server response ({response_time}ms)", "detail": "First byte returned quickly."})

    if page_size > 5000:
        findings["seo"].append({"status": "fail", "title": f"Very large page size ({page_size:.0f} KB)", "detail": "Homepage is over 5MB. Will load slowly, especially on mobile."})
    elif page_size > 2000:
        findings["seo"].append({"status": "warn", "title": f"Large page size ({page_size:.0f} KB)", "detail": "Consider optimizing images and deferring non-critical resources."})

    # --- LOCAL SCORING ---

    # GBP
    if gbp.get("checked"):
        if gbp.get("likely_has_gbp"):
            findings["local"].append({"status": "pass", "title": "Google Business Profile detected", "detail": gbp.get("confidence_note", "")})
            if not gbp.get("rating_found"):
                findings["local"].append({"status": "warn", "title": "No Google reviews detected", "detail": "Reviews significantly impact local ranking. Ask satisfied clients for reviews."})
        else:
            findings["local"].append({"status": "fail", "title": "Google Business Profile not detected", "detail": f"{gbp.get('confidence_note', '')} Verify at business.google.com."})
    else:
        findings["local"].append({"status": "warn", "title": "Could not check Google Business Profile", "detail": f"Error: {gbp.get('error', 'unknown')}. Check manually at business.google.com."})

    # LocalBusiness schema
    local_schema = any("local" in s.lower() or "business" in s.lower() for s in schema_types)
    if not local_schema:
        findings["local"].append({"status": "fail", "title": "No LocalBusiness schema markup", "detail": "Add LocalBusiness or HomeBuilder JSON-LD schema with NAP, hours, and service area."})
    else:
        findings["local"].append({"status": "pass", "title": "LocalBusiness schema found", "detail": "Structured data includes business-type schema."})

    # Directories
    for d in directories:
        if d.get("found"):
            findings["local"].append({"status": "pass", "title": f"Listed on {d['directory']}", "detail": f"Found at {d.get('url', 'N/A')}"})
        elif d.get("checked"):
            findings["local"].append({"status": "warn", "title": f"Not found on {d['directory']}", "detail": "Consider creating a profile for citation building."})
        else:
            findings["local"].append({"status": "warn", "title": f"Could not check {d['directory']}", "detail": d.get("error", "")})

    # NAP check (look for phone/address on homepage)
    hp_text = " ".join(hp.get("h1_texts", []) + hp.get("h2_texts", []))
    # Simple phone regex check across all page text would need full text, we check what we have
    # This is a rough check - we note it as something to verify
    findings["local"].append({"status": "warn", "title": "NAP consistency check needed", "detail": "Verify name, address, and phone are consistent across website footer, GBP, and directory listings."})

    # --- CONTENT SCORING ---

    # Homepage word count
    wc = hp.get("word_count", 0)
    if wc < 100:
        findings["content"].append({"status": "fail", "title": f"Very thin homepage content ({wc} words)", "detail": "Homepage has minimal text. Aim for 300-500 words minimum for SEO."})
    elif wc < 300:
        findings["content"].append({"status": "warn", "title": f"Light homepage content ({wc} words)", "detail": "Consider adding more descriptive content about services and service area."})
    else:
        findings["content"].append({"status": "pass", "title": f"Good homepage content ({wc} words)", "detail": "Homepage has sufficient text content."})

    # Total pages crawled
    valid_pages = {u: d for u, d in all_pages.items() if "error" not in d}
    total_pages = len(valid_pages)
    if total_pages < 5:
        findings["content"].append({"status": "fail", "title": f"Very small site ({total_pages} pages)", "detail": "Fewer than 5 pages indexed. More content = more search opportunities."})
    elif total_pages < 15:
        findings["content"].append({"status": "warn", "title": f"Small site ({total_pages} pages)", "detail": "Consider adding more project pages, blog posts, or service pages."})
    else:
        findings["content"].append({"status": "pass", "title": f"{total_pages} pages crawled", "detail": "Site has a reasonable amount of content."})

    # Project pages analysis
    if project_pages:
        pp_count = len(project_pages)
        with_desc = sum(1 for p in project_pages if p["has_description"])
        without_desc = pp_count - with_desc

        findings["content"].append({"status": "pass" if pp_count >= 5 else "warn", "title": f"{pp_count} project/portfolio pages found", "detail": f"{with_desc} with descriptions (100+ words), {without_desc} image-only."})

        if without_desc > with_desc:
            findings["content"].append({"status": "fail", "title": f"{without_desc} of {pp_count} project pages lack descriptions", "detail": "Project pages with only images miss SEO value. Add 150-300 words describing scope, materials, and design intent."})
        elif without_desc > 0:
            findings["content"].append({"status": "warn", "title": f"{without_desc} project pages could use more content", "detail": "Adding descriptions to all project pages improves search visibility."})
        else:
            findings["content"].append({"status": "pass", "title": "All project pages have descriptions", "detail": "Good content coverage across portfolio."})

        # Average word count on project pages
        avg_wc = sum(p["word_count"] for p in project_pages) / pp_count if pp_count else 0
        if avg_wc < 50:
            findings["content"].append({"status": "fail", "title": f"Project pages average only {avg_wc:.0f} words", "detail": "Extremely thin. Each project should tell a story (200-400 words)."})
        elif avg_wc < 150:
            findings["content"].append({"status": "warn", "title": f"Project pages average {avg_wc:.0f} words", "detail": "Could be richer. Include design intent, challenges, materials used."})
    else:
        findings["content"].append({"status": "fail", "title": "No project/portfolio pages found", "detail": "Portfolio is a primary SEO and sales driver. Ensure project pages exist with descriptive URLs."})

    # Check for blog
    blog_pages = [u for u in all_pages if any(kw in urlparse(u).path.lower() for kw in ["/blog", "/news", "/journal", "/stories", "/articles"])]
    if not blog_pages:
        findings["content"].append({"status": "warn", "title": "No blog or journal section found", "detail": "Regular content (monthly posts) helps build search authority."})
    else:
        findings["content"].append({"status": "pass", "title": f"Blog/journal section found ({len(blog_pages)} pages)", "detail": "Active content publishing helps SEO."})

    # --- VISUAL ASSETS SCORING ---

    # Homepage images
    img_count = hp.get("image_count", 0)
    if img_count == 0:
        findings["visual_assets"].append({"status": "fail", "title": "No images on homepage", "detail": "For a builder/architect, strong visuals are essential."})
    elif img_count < 3:
        findings["visual_assets"].append({"status": "warn", "title": f"Only {img_count} images on homepage", "detail": "Consider a hero image and featured project gallery."})
    else:
        findings["visual_assets"].append({"status": "pass", "title": f"{img_count} images on homepage", "detail": "Good visual presence."})

    # Alt tags
    missing_alt = hp.get("images_missing_alt", 0)
    if img_count > 0:
        pct_missing = (missing_alt / img_count) * 100 if img_count else 0
        if pct_missing > 50:
            findings["visual_assets"].append({"status": "fail", "title": f"{missing_alt} of {img_count} images missing alt text ({pct_missing:.0f}%)", "detail": "Alt text is critical for image SEO and accessibility."})
        elif pct_missing > 20:
            findings["visual_assets"].append({"status": "warn", "title": f"{missing_alt} of {img_count} images missing alt text", "detail": "Add descriptive alt text to all images."})
        elif missing_alt == 0:
            findings["visual_assets"].append({"status": "pass", "title": "All images have alt text", "detail": "Good accessibility and SEO practice."})
        else:
            findings["visual_assets"].append({"status": "pass", "title": f"Most images have alt text ({missing_alt} missing)", "detail": "Minor improvements possible."})

    # Total images across site
    total_images = sum(d.get("image_count", 0) for d in all_pages.values() if "error" not in d)
    total_missing_alt = sum(d.get("images_missing_alt", 0) for d in all_pages.values() if "error" not in d)
    findings["visual_assets"].append({"status": "pass" if total_images > 20 else "warn",
                                       "title": f"{total_images} total images across site",
                                       "detail": f"{total_missing_alt} missing alt text site-wide."})

    # Project page image density
    if project_pages:
        avg_images = sum(p["image_count"] for p in project_pages) / len(project_pages)
        if avg_images < 3:
            findings["visual_assets"].append({"status": "fail", "title": f"Project pages average only {avg_images:.1f} images", "detail": "Portfolio pages need strong imagery. Aim for 8-15 high-quality photos per project."})
        elif avg_images < 8:
            findings["visual_assets"].append({"status": "warn", "title": f"Project pages average {avg_images:.1f} images", "detail": "Could showcase more of each project. Professional photography makes a difference."})
        else:
            findings["visual_assets"].append({"status": "pass", "title": f"Project pages average {avg_images:.1f} images", "detail": "Good visual coverage per project."})

    # og:image check
    if not hp.get("has_og_image"):
        findings["visual_assets"].append({"status": "warn", "title": "No Open Graph image", "detail": "Social shares will lack a preview image. Set og:image to a strong portfolio shot."})

    # --- CALCULATE NUMERIC SCORES ---
    for category in scores:
        for f in findings[category]:
            if f["status"] == "fail":
                scores[category] -= 15
            elif f["status"] == "warn":
                scores[category] -= 8
        scores[category] = max(0, scores[category])

    return scores, findings


def grade_from_score(score):
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "A-"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "B-"
    elif score >= 50:
        return "C"
    elif score >= 40:
        return "C-"
    elif score >= 30:
        return "D"
    elif score >= 20:
        return "D-"
    else:
        return "F"


def color_from_score(score):
    """Convert score to color class."""
    if score >= 70:
        return "good"
    elif score >= 50:
        return "mid"
    else:
        return "bad"


def build_report(url, company_name, location, scores, findings, homepage_data, all_pages, project_pages, robots, sitemap, ssl, redirects, gbp, directories):
    """Build the final JSON report."""

    valid_pages = {u: d for u, d in all_pages.items() if "error" not in d}

    # Compile meta data
    all_schema_types = set()
    total_word_count = 0
    total_images = 0
    total_missing_alt = 0
    for data in valid_pages.values():
        for st in data.get("schema_types", []):
            all_schema_types.add(st)
        total_word_count += data.get("word_count", 0)
        total_images += data.get("image_count", 0)
        total_missing_alt += data.get("images_missing_alt", 0)

    meta = {
        "url": url,
        "company_name": company_name,
        "location": location,
        "pages_crawled": len(all_pages),
        "pages_successful": len(valid_pages),
        "pages_errored": len(all_pages) - len(valid_pages),
        "total_word_count": total_word_count,
        "total_images": total_images,
        "total_missing_alt": total_missing_alt,
        "schema_types_found": sorted(all_schema_types),
        "project_pages_count": len(project_pages),
        "project_pages_with_descriptions": sum(1 for p in project_pages if p["has_description"]),
        "has_robots_txt": robots.get("exists", False),
        "has_sitemap": sitemap.get("exists", False),
        "sitemap_url_count": sitemap.get("url_count"),
        "ssl_valid": ssl.get("ssl_valid", False),
        "redirect_count": redirects.get("redirect_count", 0),
        "final_url": redirects.get("final_url"),
        "homepage_title": homepage_data.get("title") if homepage_data else None,
        "homepage_meta_description": homepage_data.get("meta_description") if homepage_data else None,
        "homepage_word_count": homepage_data.get("word_count", 0) if homepage_data else 0,
        "homepage_image_count": homepage_data.get("image_count", 0) if homepage_data else 0,
        "homepage_response_ms": homepage_data.get("response_time_ms") if homepage_data else None,
        "homepage_size_kb": homepage_data.get("page_size_kb") if homepage_data else None,
        "gbp_detected": gbp.get("likely_has_gbp", False) if gbp.get("checked") else None,
        "directories_checked": {d["directory"]: d.get("found", None) for d in directories},
        "project_pages": project_pages,
        "page_urls": sorted(valid_pages.keys()),
    }

    report = {
        "scores": {
            cat: {
                "value": scores[cat],
                "grade": grade_from_score(scores[cat]),
                "color": color_from_score(scores[cat]),
            }
            for cat in ["seo", "local", "content", "visual_assets"]
        },
        "findings": findings,
        "meta": meta,
    }

    return report


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_audit(url, company_name, location=None):
    """Run the full audit pipeline."""

    # Normalize URL
    if not url.startswith("http"):
        url = "https://" + url

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  Site Audit: {company_name}", file=sys.stderr)
    print(f"  URL: {url}", file=sys.stderr)
    if location:
        print(f"  Location: {location}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)

    # Step 1: SSL & Redirects
    print("[1/6] Checking SSL and redirects...", file=sys.stderr)
    ssl_result = check_ssl(url)
    redirect_result = check_redirects(url)
    final_url = redirect_result.get("final_url", url)

    # Step 2: Homepage analysis
    print("[2/6] Analyzing homepage...", file=sys.stderr)
    soup, response, err = fetch_soup(final_url)
    if err:
        print(f"  ERROR: Could not fetch homepage: {err}", file=sys.stderr)
        homepage_data = {}
    else:
        homepage_data = analyze_page(soup, response)

    # Step 3: Robots & Sitemap
    print("[3/6] Checking robots.txt and sitemap...", file=sys.stderr)
    robots_result = check_robots_txt(final_url)
    sitemap_result = check_sitemap(final_url, robots_result)

    # Step 4: GBP & Directories
    print("[4/6] Checking Google Business Profile and directories...", file=sys.stderr)
    gbp_result = check_gbp(company_name, location)
    directory_results = check_local_directories(company_name)

    # Step 5: Crawl site
    print("[5/6] Crawling site pages...", file=sys.stderr)
    all_pages = crawl_site(final_url)
    # Make sure homepage data is included
    all_pages[final_url.rstrip("/")] = homepage_data

    # Step 6: Identify project pages
    print("[6/6] Analyzing project pages and scoring...", file=sys.stderr)
    project_pages = identify_project_pages(all_pages)

    # Calculate scores
    scores, findings = calculate_scores(
        homepage_data, robots_result, sitemap_result, redirect_result,
        ssl_result, gbp_result, directory_results, project_pages, all_pages
    )

    # Build report
    report = build_report(
        url, company_name, location, scores, findings,
        homepage_data, all_pages, project_pages,
        robots_result, sitemap_result, ssl_result, redirect_result,
        gbp_result, directory_results
    )

    # Print summary
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  AUDIT RESULTS: {company_name}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    for cat in ["seo", "local", "content", "visual_assets"]:
        s = report["scores"][cat]
        label = cat.replace("_", " ").title()
        print(f"  {label:20s}  {s['value']:3d}/100  ({s['grade']})", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Perform an SEO and local audit on a website",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    python3 tools/site_audit.py https://summerhill.build "Summerhill Fine Homes" \\
        --location "Gibsons BC" \\
        --output business/sales/configs/summerhill-audit-data.json
        """,
    )
    parser.add_argument("url", help="Website URL to audit")
    parser.add_argument("company", help="Company name")
    parser.add_argument("--location", help="City/region for local SEO checks")
    parser.add_argument("--output", "-o", help="Output JSON file path (default: stdout)")

    args = parser.parse_args()

    report = run_audit(args.url, args.company, args.location)

    json_output = json.dumps(report, indent=2, ensure_ascii=False)

    if args.output:
        # Ensure output directory exists
        out_dir = os.path.dirname(args.output)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.output, "w") as f:
            f.write(json_output)
        print(f"Report written to: {args.output}", file=sys.stderr)
    else:
        print(json_output)


if __name__ == "__main__":
    main()
