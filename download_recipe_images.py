"""
Bulk download recipe images from Pexels based on recipe titles.
Searches Pexels for each recipe, picks the best food photo, downloads it,
and updates the recipe's front matter.
"""

import os
import re
import time
import glob
import requests
from urllib.parse import quote

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "content", "recipes")
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "static", "images", "recipes")
SEARCH_DELAY = 1.5  # seconds between Pexels searches to be polite

os.makedirs(IMAGE_DIR, exist_ok=True)

# Common words to strip from titles for better search results
STRIP_PREFIXES = []  # Keep full titles as user requested specificity


def get_recipe_files():
    """Get all recipe .md files with their titles and slugs."""
    recipes = []
    for filepath in sorted(glob.glob(os.path.join(CONTENT_DIR, "*.md"))):
        basename = os.path.basename(filepath)
        if basename == "_index.md":
            continue
        slug = basename.replace(".md", "")

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract title from front matter
        title_match = re.search(r'^title:\s*"(.+?)"', content, re.MULTILINE)
        if not title_match:
            continue
        title = title_match.group(1)

        # Check if image is already set (non-empty)
        image_match = re.search(r'^image:\s*"(.+?)"', content, re.MULTILINE)
        has_image = bool(image_match and image_match.group(1).strip())

        recipes.append({
            "filepath": filepath,
            "slug": slug,
            "title": title,
            "has_image": has_image,
        })
    return recipes


def clean_search_query(title):
    """Clean recipe title into a good search query for food photos."""
    query = title
    # Remove quotes and special chars
    query = query.replace('"', '').replace("'", "")
    # Keep the full title for specificity
    return query


def search_pexels(query):
    """Search Pexels and return the first food photo ID found."""
    search_url = f"https://www.pexels.com/search/{quote(query)}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        resp = requests.get(search_url, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text

        # Extract photo IDs from Pexels search results
        # Pattern: /photo/description-PHOTOID/ or /photo/PHOTOID/
        photo_ids = re.findall(r'/photo/[^/]*?(\d{4,})/?"', html)

        if photo_ids:
            # Return unique IDs (first few results)
            seen = []
            for pid in photo_ids:
                if pid not in seen:
                    seen.append(pid)
                if len(seen) >= 5:
                    break
            return seen
    except Exception as e:
        print(f"    Search error: {e}")

    return []


def try_download_photo(photo_id, output_path):
    """Try to download a Pexels photo by ID. Returns True if successful."""
    # Pexels image URL pattern
    url = f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=600"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 5000:
            # Verify it's a JPEG (starts with FFD8)
            if resp.content[:2] == b'\xff\xd8':
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                return True
    except Exception:
        pass
    return False


def update_front_matter(filepath, image_path):
    """Update the image field in a recipe's front matter."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace empty image field
    new_content = re.sub(
        r'^image:\s*""',
        f'image: "{image_path}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )

    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False


def get_fallback_queries(title):
    """Generate fallback search queries if the exact title doesn't yield results."""
    queries = [title]

    # Try without common prefixes
    prefixes_to_strip = [
        r"^Air Fryer\s+",
        r"^Instant Pot\s+",
        r"^Slow Cooker\s+",
        r"^Crock[ -]?Pot\s+",
        r"^Easy\s+",
        r"^Best\s+",
        r"^Simple\s+",
        r"^Homemade\s+",
        r"^Mom'?s?\s+",
        r"^Grandma'?s?\s+",
        r"^Classic\s+",
        r"^Old[ -]?Fashioned\s+",
    ]
    for prefix in prefixes_to_strip:
        stripped = re.sub(prefix, "", title, flags=re.IGNORECASE).strip()
        if stripped != title and stripped not in queries:
            queries.append(stripped)

    # Try just the main food words (last resort)
    # Remove parenthetical notes
    no_parens = re.sub(r'\s*\([^)]*\)', '', title).strip()
    if no_parens != title and no_parens not in queries:
        queries.append(no_parens)

    return queries


def main():
    print("=" * 60)
    print("Recipe Image Downloader")
    print("=" * 60)

    recipes = get_recipe_files()
    total = len(recipes)
    need_images = [r for r in recipes if not r["has_image"]]
    already_done = total - len(need_images)

    print(f"Total recipes: {total}")
    print(f"Already have images: {already_done}")
    print(f"Need images: {len(need_images)}")
    print()

    success_count = 0
    fail_count = 0
    failed_recipes = []

    for i, recipe in enumerate(need_images, 1):
        title = recipe["title"]
        slug = recipe["slug"]
        image_filename = f"{slug}.jpg"
        image_output = os.path.join(IMAGE_DIR, image_filename)
        image_web_path = f"/images/recipes/{image_filename}"

        print(f"[{i}/{len(need_images)}] {title}")

        # Skip if image file already exists on disk
        if os.path.exists(image_output) and os.path.getsize(image_output) > 5000:
            print(f"    Image file exists, updating front matter...")
            update_front_matter(recipe["filepath"], image_web_path)
            success_count += 1
            continue

        # Generate search queries
        queries = get_fallback_queries(clean_search_query(title))
        downloaded = False

        for query in queries:
            print(f"    Searching: '{query}'")
            photo_ids = search_pexels(query)
            time.sleep(SEARCH_DELAY)

            if not photo_ids:
                print(f"    No results for '{query}'")
                continue

            # Try downloading the first few photos until one works
            for pid in photo_ids[:3]:
                if try_download_photo(pid, image_output):
                    size_kb = os.path.getsize(image_output) / 1024
                    print(f"    Downloaded photo {pid} ({size_kb:.1f}KB)")
                    update_front_matter(recipe["filepath"], image_web_path)
                    downloaded = True
                    success_count += 1
                    break

            if downloaded:
                break

        if not downloaded:
            print(f"    FAILED - no suitable image found")
            fail_count += 1
            failed_recipes.append(title)

    print()
    print("=" * 60)
    print(f"DONE! Success: {success_count}, Failed: {fail_count}")
    print(f"Total with images: {already_done + success_count}/{total}")
    if failed_recipes:
        print()
        print("Failed recipes (need manual images):")
        for title in failed_recipes:
            print(f"  - {title}")
    print("=" * 60)


if __name__ == "__main__":
    main()
