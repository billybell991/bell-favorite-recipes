"""
Update recipe images using Pexels API search.
Cleans recipe titles and searches Pexels for a matching photo.
"""
import os
import re
import sys
import time
import json
import requests

API_KEY = os.environ.get("PEXELS_API_KEY", "")

# Noise patterns to strip from titles before searching
NOISE_PATTERNS = [
    r"\(.*?\)",          # anything in parentheses: (Mom's), (Yan's), (Tracey)
    r"#\d+",            # numbering: #2
    r"\bno\.\s*\d+",    # "No. 2"
    r"\bno\s+\d+",      # "No 2"
    r"'s\b",            # possessives that got through
    r"\bwedding\s+cookbook\b",
    r"\bmom\s+cookbook\b",
    r"\- ",              # trailing dashes
]

# Titles that are non-food or need manual overrides (skip API search)
SKIP_TITLES = {
    "baker's clay instructions",
    "ornament clay dough",
    "playdough",
    "frontier kitchen chemical garden",
    "helpful hints for healthy cooking",
    "all recipes",
}


def clean_title(title):
    """Remove noise from recipe title to make a better search query."""
    q = title
    for pat in NOISE_PATTERNS:
        q = re.sub(pat, "", q, flags=re.IGNORECASE)
    # Collapse whitespace
    q = re.sub(r"\s+", " ", q).strip()
    # Remove leading/trailing punctuation
    q = q.strip("-–—:,.")
    return q.strip()


def search_pexels(query, per_page=5):
    """Search Pexels API and return list of photo dicts."""
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": per_page, "orientation": "landscape"},
            headers={"Authorization": API_KEY},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("photos", [])
        else:
            print(f"  API error for '{query}': HTTP {resp.status_code}")
            return []
    except Exception as e:
        print(f"  API error for '{query}': {e}")
        return []


def get_photo_url(photos, used_ids):
    """Pick the best photo URL from search results, avoiding already-used IDs."""
    for photo in photos:
        pid = photo["id"]
        if pid not in used_ids:
            used_ids.add(pid)
            return f"https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg?auto=compress&cs=tinysrgb&w=600"
    # If all are used, just take the first one
    if photos:
        pid = photos[0]["id"]
        return f"https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg?auto=compress&cs=tinysrgb&w=600"
    return None


def read_frontmatter(filepath):
    """Read a markdown file and return (frontmatter_text, body_text, title)."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split on --- delimiters
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, None, None

    fm = parts[1]
    body = parts[2]

    title_match = re.search(r'title:\s*"([^"]*)"', fm)
    title = title_match.group(1) if title_match else None

    return fm, body, title


def update_image_in_frontmatter(fm, new_url):
    """Replace the image field in frontmatter text."""
    return re.sub(r'image:\s*"[^"]*"', f'image: "{new_url}"', fm)


def process_recipes(recipe_dir, category_filter=None, dry_run=False):
    """Process recipe files optionally filtered by category."""
    files = sorted(f for f in os.listdir(recipe_dir) if f.endswith(".md") and f != "_index.md")

    updated = 0
    skipped = 0
    failed = 0
    used_ids = set()

    for filename in files:
        filepath = os.path.join(recipe_dir, filename)
        fm, body, title = read_frontmatter(filepath)

        if not fm or not title:
            continue

        # Category filter
        if category_filter:
            cat_match = re.search(r'categories:\s*\["([^"]*)"', fm)
            if not cat_match or category_filter.lower() not in cat_match.group(1).lower():
                continue

        # Skip non-food recipes
        if title.lower() in SKIP_TITLES:
            print(f"  SKIP (non-food): {title}")
            skipped += 1
            continue

        query = clean_title(title)
        if len(query) < 3:
            print(f"  SKIP (too short after cleaning): {title} -> '{query}'")
            skipped += 1
            continue

        print(f"  Searching: '{query}' (from: {title})")

        photos = search_pexels(query)

        if not photos:
            # Fallback: try with fewer words (drop adjectives, keep nouns)
            words = query.split()
            if len(words) > 3:
                fallback = " ".join(words[-3:])  # last 3 words (usually the food)
                print(f"    Fallback search: '{fallback}'")
                photos = search_pexels(fallback)
                time.sleep(0.2)

        if not photos:
            print(f"    FAILED: No photos found for '{title}'")
            failed += 1
            continue

        new_url = get_photo_url(photos, used_ids)
        if not new_url:
            failed += 1
            continue

        # Get old URL for comparison
        old_match = re.search(r'image:\s*"([^"]*)"', fm)
        old_url = old_match.group(1) if old_match else ""

        if dry_run:
            print(f"    DRY RUN: Would update {filename}")
            print(f"      Old: .../{old_url.split('/')[-1][:40] if old_url else 'none'}")
            print(f"      New: .../{new_url.split('/')[-1][:40]}")
        else:
            new_fm = update_image_in_frontmatter(fm, new_url)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"---{new_fm}---{body}")
            print(f"    UPDATED: {filename}")

        updated += 1
        # Rate limit: Pexels allows 200 requests/hour
        time.sleep(0.5)

    print(f"\nDone! Updated: {updated}, Skipped: {skipped}, Failed: {failed}")


if __name__ == "__main__":
    recipe_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "recipes")

    # Parse arguments
    dry_run = "--dry-run" in sys.argv
    category = None
    for arg in sys.argv[1:]:
        if arg.startswith("--category="):
            category = arg.split("=", 1)[1]

    if not API_KEY:
        print("ERROR: Set PEXELS_API_KEY environment variable")
        sys.exit(1)

    print(f"Recipe dir: {recipe_dir}")
    print(f"Category filter: {category or 'ALL'}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE (will update files)'}")
    print()

    process_recipes(recipe_dir, category_filter=category, dry_run=dry_run)
