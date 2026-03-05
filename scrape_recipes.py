"""
Bell Favorite Recipes — Google Sites Scraper (v2)
==================================================
Properly scrapes all recipes from Google Sites, handling:
- Index pages (treated as directories, not recipes)
- Sub-sections (Mom's Cookbook, Wedding Cookbook)
- Duplicate recipe names across categories
- Cross-section navigation links (ignored)

Usage:
    python scrape_recipes.py
"""

import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime

BASE_URL = "https://sites.google.com/view/bellfavoriterecipes"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "recipes")
DELAY = 0.3  # seconds between requests

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; BellRecipesScraper/2.0; personal-use)"
})

# ── Section Definitions ─────────────────────────────────────────────
# "Flat" sections: index page lists recipe links directly
FLAT_SECTIONS = {
    "air-fryer-recipes": "Air Fryer Recipes",
    "family-recipes": "Family Recipes",
    "friends-recipes": "Friends Recipes",
    "instant-pot-recipes": "Instant Pot Recipes",
    "keto-low-carb-recipes": "Keto & Low Carb",
    "maddys-recipes": "Maddy's Recipes",
    "mayas-recipes": "Maya's Recipes",
    "misc-recipes-internet": "Misc Recipes - Internet",
    "weight-watchers": "Weight Watchers",
}

# "Nested" sections: index page lists sub-category pages, which list recipes
NESTED_SECTIONS = {
    "moms-cookbook": {
        "category": "Mom's Cookbook",
        "subsections": [
            "appetizers", "breads", "cake-frosting", "cakes-and-muffins",
            "casseroles", "chicken", "cookies", "desserts", "diabetic-recipes",
            "fish", "fun-things", "meat",
        ],
    },
    "wedding-cookbook": {
        "category": "Wedding Cookbook",
        "subsections": [
            "appetizers", "breads", "cakessquares", "casseroles",
            "cookies", "dips", "drinks", "meat", "pastrypies",
            "pasta", "rice", "salads",
        ],
    },
}

# Misc Recipes (Cookbooks) — flat section
MISC_COOKBOOKS = {
    "slug": "misc-recipes-cookbooks",
    "category": "Misc Recipes - Cookbooks",
}

# Track all created slugs to handle duplicates
created_slugs = set()
stats = {"created": 0, "skipped_index": 0, "skipped_dup": 0, "errors": 0}


# ── Helpers ──────────────────────────────────────────────────────────
def fetch_page(url):
    """Fetch a page and return BeautifulSoup object."""
    try:
        resp = SESSION.get(url, timeout=30)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"    [ERROR] Failed to fetch {url}: {e}")
        stats["errors"] += 1
        return None


def slugify(text):
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def yaml_escape(text):
    """Escape text for YAML front matter."""
    if not text:
        return '""'
    text = text.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{text}"'


def get_child_links(soup, section_path):
    """
    Extract links that are DIRECT children of a section path.
    e.g. for section_path="/view/bellfavoriterecipes/air-fryer-recipes",
    only return links like "/view/bellfavoriterecipes/air-fryer-recipes/some-recipe"
    (exactly one level deeper). This prevents picking up cross-section nav links.
    """
    links = []
    seen_urls = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        text = a_tag.get_text(strip=True)
        if not text or not href:
            continue

        # Normalize: handle both relative and absolute URLs
        if href.startswith("/view/"):
            full_path = href
        elif "bellfavoriterecipes" in href:
            parsed = urlparse(href)
            full_path = parsed.path
        else:
            continue

        # Remove trailing slash
        full_path = full_path.rstrip("/")
        section_path_clean = section_path.rstrip("/")

        # Must start with the section path
        if not full_path.startswith(section_path_clean + "/"):
            continue

        # Get the remainder after the section path
        remainder = full_path[len(section_path_clean) + 1:]

        # Must be exactly one level deep (no further slashes)
        if "/" in remainder or not remainder:
            continue

        full_url = f"https://sites.google.com{full_path}"
        if full_url not in seen_urls:
            seen_urls.add(full_url)
            links.append((text, full_url, remainder))

    return links


def is_index_page(soup, title):
    """
    Detect if a page is an index/listing page rather than an actual recipe.
    Index pages contain mostly links to sub-pages with little recipe content.
    """
    text = soup.get_text(separator="\n", strip=True)

    # Count internal bellfavoriterecipes links in the body (not nav)
    all_links = soup.find_all("a", href=lambda h: h and "bellfavoriterecipes" in h)
    body_links = []
    for link in all_links:
        in_nav = False
        for parent in link.parents:
            if parent.name == 'nav':
                in_nav = True
                break
        if not in_nav:
            body_links.append(link)

    # Get meaningful text lines (not just whitespace or very short)
    lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 3]
    if not lines:
        return True

    # If there are many internal links and the content is mostly link text, it's an index
    link_texts = set(l.get_text(strip=True) for l in body_links)
    link_lines = sum(1 for l in lines if l in link_texts)

    if len(body_links) > 5 and link_lines / len(lines) > 0.4:
        return True

    return False


def extract_recipe_content(soup, title):
    """Extract recipe content from a page and convert to Markdown."""
    if not soup:
        return ""

    content_soup = BeautifulSoup(str(soup), "html.parser")

    # Remove head, header, footer, nav, scripts, styles, iframes
    for tag in content_soup.find_all(["head", "header", "footer", "nav", "script", "style", "iframe", "noscript"]):
        tag.decompose()

    # Remove "Skip to" links
    for a in content_soup.find_all("a", string=re.compile(r"Skip to", re.I)):
        a.decompose()

    # Remove "Report abuse" / "Google Sites" / "Search this site" text areas
    for elem in content_soup.find_all(string=re.compile(r"Google Sites|Report abuse|Search this site|Embedded Files", re.I)):
        if elem.parent and elem.parent.name:
            elem.parent.decompose()

    # Remove "Additional Links" section
    for heading in content_soup.find_all(["h2", "h3"], string=re.compile(r"Additional Links", re.I)):
        parent = heading.parent
        if parent:
            parent.decompose()

    # Remove page title h1
    for h1 in content_soup.find_all("h1"):
        if h1.get_text(strip=True).strip() == title.strip():
            h1.decompose()

    content = html_to_markdown(content_soup)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


def html_to_markdown(element):
    """Convert an HTML element tree to Markdown text."""
    if element is None:
        return ""
    if isinstance(element, str):
        return element.strip()
    if element.name is None:
        return element.get_text()

    if element.name in ['script', 'style', 'nav', 'iframe', 'head', 'header', 'footer', 'noscript']:
        return ""

    tag = element.name

    # For wrapper tags, just recurse into children
    if tag in ('html', 'body', '[document]'):
        result = ""
        for child in element.children:
            result += html_to_markdown(child)
        return result

    result = ""

    if tag in ('h1', 'h2'):
        text = element.get_text(strip=True)
        if text:
            result = f"\n## {text}\n\n"
    elif tag == 'h3':
        text = element.get_text(strip=True)
        if text:
            result = f"\n### {text}\n\n"
    elif tag in ('ul', 'ol'):
        items = element.find_all('li', recursive=False)
        for i, li in enumerate(items):
            li_text = li.get_text(strip=True)
            if li_text:
                prefix = f"{i + 1}." if tag == 'ol' else "-"
                result += f"{prefix} {li_text}\n"
        result += "\n"
    elif tag == 'li':
        return ""  # handled by parent ul/ol
    elif tag == 'p':
        text = element.get_text(strip=True)
        if text:
            result = f"{text}\n\n"
    elif tag == 'br':
        result = "\n"
    elif tag in ('strong', 'b'):
        text = element.get_text(strip=True)
        if text:
            result = f"**{text}**"
    elif tag in ('em', 'i'):
        text = element.get_text(strip=True)
        if text:
            result = f"*{text}*"
    elif tag == 'a':
        text = element.get_text(strip=True)
        href = element.get('href', '')
        if text and href and not href.startswith('#'):
            # Clean Google redirect URLs
            if 'google.com/url' in href:
                parsed = urlparse(href)
                params = parse_qs(parsed.query)
                if 'q' in params:
                    href = params['q'][0]
            # Skip internal bellfavoriterecipes navigation links
            if 'bellfavoriterecipes' not in href:
                result = f"[{text}]({href})"
            else:
                result = text
        elif text:
            result = text
    elif tag == 'img':
        src = element.get('src', '')
        alt = element.get('alt', 'Image')
        if src:
            result = f"![{alt}]({src})\n\n"
    else:
        for child in element.children:
            result += html_to_markdown(child)

    return result


def auto_structure_content(content):
    """Add Ingredients/Instructions headers if not present."""
    if "## " in content:
        return content

    lines = content.split('\n')
    has_bullets = any(line.strip().startswith('- ') for line in lines)
    has_numbered = any(re.match(r'^\d+\.', line.strip()) for line in lines)

    if has_bullets and has_numbered:
        new_lines = ["## Ingredients\n"]
        in_instructions = False
        for line in lines:
            stripped = line.strip()
            if not in_instructions and re.match(r'^\d+\.', stripped):
                in_instructions = True
                new_lines.append("\n## Instructions\n")
            new_lines.append(line)
        return '\n'.join(new_lines).strip()

    return content


def auto_tags(title):
    """Generate tags from recipe title."""
    tags = []
    title_lower = title.lower()
    keywords = {
        "chicken": "chicken", "beef": "beef", "pork": "pork",
        "fish": "fish", "salmon": "salmon", "shrimp": "shrimp",
        "soup": "soup", "salad": "salad", "pasta": "pasta",
        "bread": "bread", "cake": "cake", "cookie": "cookies",
        "muffin": "muffins", "pie": "pie", "rice": "rice",
        "potato": "potatoes", "dessert": "dessert",
        "instant pot": "instant pot", "air fryer": "air fryer",
        "keto": "keto", "stew": "stew", "dip": "dip",
    }
    for keyword, tag in keywords.items():
        if keyword in title_lower and tag not in tags:
            tags.append(tag)
    return tags


def save_recipe(title, category, content, subcategory=""):
    """Save a recipe as a Hugo Markdown file, handling duplicate slugs."""
    slug = slugify(title)
    if not slug:
        return

    # Handle duplicate slugs by appending category
    if slug in created_slugs:
        cat_slug = slugify(category)
        slug = f"{slug}-{cat_slug}"
        if slug in created_slugs:
            if subcategory:
                slug = f"{slug}-{slugify(subcategory)}"
            if slug in created_slugs:
                stats["skipped_dup"] += 1
                return

    filepath = os.path.join(OUTPUT_DIR, f"{slug}.md")
    created_slugs.add(slug)

    categories = [category]
    tags = auto_tags(title)
    if subcategory:
        tags.insert(0, subcategory.lower())

    structured = auto_structure_content(content)

    front_matter = f"""---
title: {yaml_escape(title)}
date: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S-05:00')}
draft: false
categories: [{', '.join(yaml_escape(c) for c in categories)}]
tags: [{', '.join(yaml_escape(t) for t in tags)}]
description: ""
source: ""
creditUrl: ""
credit: ""
prepTime: ""
cookTime: ""
servings: ""
image: ""
notes: ""
---

"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(front_matter + structured)

    stats["created"] += 1
    print(f"    [OK] {slug}.md")


# ── Scraping Logic ───────────────────────────────────────────────────
def scrape_flat_section(section_slug, category):
    """Scrape a flat section: index page -> recipe pages."""
    section_path = f"/view/bellfavoriterecipes/{section_slug}"
    url = f"{BASE_URL}/{section_slug}"
    print(f"\n--- {category} ({section_slug}) ---")

    soup = fetch_page(url)
    if not soup:
        return
    time.sleep(DELAY)

    links = get_child_links(soup, section_path)
    print(f"   Found {len(links)} recipe links")

    for title, recipe_url, _ in links:
        print(f"   > {title}")
        recipe_soup = fetch_page(recipe_url)
        if not recipe_soup:
            continue

        if is_index_page(recipe_soup, title):
            print(f"    [INDEX] Skipping index page: {title}")
            stats["skipped_index"] += 1
            time.sleep(DELAY)
            continue

        content = extract_recipe_content(recipe_soup, title)
        save_recipe(title, category, content)
        time.sleep(DELAY)


def scrape_nested_section(parent_slug, category, subsections):
    """Scrape a nested section: parent -> sub-category index -> recipe pages."""
    parent_path = f"/view/bellfavoriterecipes/{parent_slug}"
    print(f"\n=== {category} ({parent_slug}) ===")

    for sub_slug in subsections:
        sub_path = f"{parent_path}/{sub_slug}"
        sub_url = f"{BASE_URL}/{parent_slug}/{sub_slug}"
        sub_name = sub_slug.replace("-", " ").title()
        print(f"\n  -- {category} > {sub_name} --")

        soup = fetch_page(sub_url)
        if not soup:
            continue
        time.sleep(DELAY)

        links = get_child_links(soup, sub_path)
        print(f"     Found {len(links)} recipe links")

        for title, recipe_url, _ in links:
            print(f"     > {title}")
            recipe_soup = fetch_page(recipe_url)
            if not recipe_soup:
                continue

            if is_index_page(recipe_soup, title):
                print(f"      [INDEX] Skipping index page: {title}")
                stats["skipped_index"] += 1
                time.sleep(DELAY)
                continue

            content = extract_recipe_content(recipe_soup, title)
            save_recipe(title, category, content, subcategory=sub_name)
            time.sleep(DELAY)


# ── Main ─────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("Bell Favorite Recipes - Google Sites Scraper v2")
    print("=" * 60)
    print(f"Output: {OUTPUT_DIR}")
    print(f"Delay:  {DELAY}s per request")

    start = time.time()

    # 1. Flat sections
    for slug, category in FLAT_SECTIONS.items():
        scrape_flat_section(slug, category)

    # 2. Misc Cookbooks (flat)
    scrape_flat_section(MISC_COOKBOOKS["slug"], MISC_COOKBOOKS["category"])

    # 3. Nested sections (Mom's Cookbook, Wedding Cookbook)
    for slug, info in NESTED_SECTIONS.items():
        scrape_nested_section(slug, info["category"], info["subsections"])

    elapsed = time.time() - start

    print("\n" + "=" * 60)
    print(f"Done in {elapsed:.0f} seconds")
    print(f"   Created:        {stats['created']}")
    print(f"   Index skipped:  {stats['skipped_index']}")
    print(f"   Dup skipped:    {stats['skipped_dup']}")
    print(f"   Errors:         {stats['errors']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
