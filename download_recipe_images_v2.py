"""
Bulk download recipe images from multiple free image sources.
Uses Pexels with proper session handling, falls back to Unsplash.
"""

import os
import re
import time
import json
import glob
import requests
from urllib.parse import quote

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "content", "recipes")
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "static", "images", "recipes")
SEARCH_DELAY = 2.0  # seconds between searches

os.makedirs(IMAGE_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
})


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
        title_match = re.search(r'^title:\s*"(.+?)"', content, re.MULTILINE)
        if not title_match:
            continue
        title = title_match.group(1)
        image_match = re.search(r'^image:\s*"(.+?)"', content, re.MULTILINE)
        has_image = bool(image_match and image_match.group(1).strip())
        recipes.append({
            "filepath": filepath,
            "slug": slug,
            "title": title,
            "has_image": has_image,
        })
    return recipes


def clean_query(title):
    """Clean recipe title into search-friendly query."""
    q = title
    q = re.sub(r'\s*\([^)]*\)', '', q)  # Remove parenthetical
    q = q.replace('"', '').replace("!", "").replace("'s", "")
    q = q.strip()
    return q


def get_search_queries(title):
    """Generate ordered list of search queries from recipe title."""
    queries = [clean_query(title)]
    # Simplified version without prefixes
    for prefix in ["Air Fryer ", "Instant Pot ", "Slow Cooker ", "Crock Pot ", "Crockpot ",
                    "Easy ", "Best ", "Simple ", "Homemade ", "Mom ", "Moms ", "Grandma ",
                    "Classic ", "Old Fashioned ", "Old-Fashioned ", "Quick ",
                    "The Best ", "Our Favorite ", "My Favorite "]:
        if queries[0].lower().startswith(prefix.lower()):
            stripped = queries[0][len(prefix):].strip()
            if stripped and stripped not in queries:
                queries.append(stripped)
                break
    # Also try just the core food name (remove numbers, adjectives at start)
    core = re.sub(r'^\d+[-\s]', '', queries[-1])
    if core != queries[-1] and core not in queries:
        queries.append(core)
    return queries


def search_unsplash(query):
    """Search Unsplash and return photo URLs to try."""
    search_url = f"https://unsplash.com/s/photos/{quote(query.replace(' ', '-'))}"
    try:
        resp = session.get(search_url, timeout=15)
        if resp.status_code != 200:
            return []
        # Extract photo IDs from the page
        # Pattern: /photos/SLUG-PHOTOID format
        matches = re.findall(r'https://images\.unsplash\.com/photo-([0-9]+-[0-9a-f]+)\?', resp.text)
        unique = []
        seen = set()
        for m in matches:
            if m not in seen:
                seen.add(m)
                unique.append(m)
            if len(unique) >= 5:
                break
        return unique
    except Exception as e:
        print(f"    Unsplash search error: {e}")
        return []


def download_unsplash(photo_id, output_path):
    """Download an Unsplash photo."""
    url = f"https://images.unsplash.com/photo-{photo_id}?w=600&q=80&auto=format"
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 5000:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception:
        pass
    return False


def search_pixabay_free(query):
    """Try Pixabay's free embeddable image search."""
    search_url = f"https://pixabay.com/images/search/{quote(query)}/"
    try:
        resp = session.get(search_url, timeout=15)
        if resp.status_code != 200:
            return []
        # Extract image URLs
        matches = re.findall(r'https://cdn\.pixabay\.com/photo/\d+/\d+/\d+/\d+/\d+/[^"]+_640\.[a-z]+', resp.text)
        unique = []
        seen = set()
        for m in matches:
            if m not in seen:
                seen.add(m)
                unique.append(m)
            if len(unique) >= 5:
                break
        return unique
    except Exception as e:
        print(f"    Pixabay search error: {e}")
        return []


def download_url(url, output_path):
    """Download any image URL."""
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 3000:
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


def try_all_sources(query, output_path):
    """Try multiple image sources for a query. Returns True if downloaded."""
    # Source 1: Unsplash
    photo_ids = search_unsplash(query)
    if photo_ids:
        for pid in photo_ids[:3]:
            if download_unsplash(pid, output_path):
                return "unsplash"
    time.sleep(1)

    # Source 2: Pixabay
    urls = search_pixabay_free(query)
    if urls:
        for url in urls[:3]:
            if download_url(url, output_path):
                return "pixabay"

    return None


def main():
    print("=" * 60)
    print("Recipe Image Downloader v2")
    print("Using Unsplash + Pixabay")
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
            print(f"    Image exists on disk, updating front matter")
            update_front_matter(recipe["filepath"], image_web_path)
            success_count += 1
            continue

        # Try each search query
        queries = get_search_queries(title)
        downloaded = False

        for query in queries:
            print(f"    Searching: '{query}'")
            source = try_all_sources(query, image_output)
            if source:
                size_kb = os.path.getsize(image_output) / 1024
                print(f"    OK from {source} ({size_kb:.1f}KB)")
                update_front_matter(recipe["filepath"], image_web_path)
                downloaded = True
                success_count += 1
                break
            time.sleep(SEARCH_DELAY)

        if not downloaded:
            print(f"    FAILED")
            fail_count += 1
            failed_recipes.append(title)

        # Progress update every 50
        if i % 50 == 0:
            print(f"\n--- Progress: {i}/{len(need_images)} | OK: {success_count} | Failed: {fail_count} ---\n")

    print()
    print("=" * 60)
    print(f"DONE! Success: {success_count}, Failed: {fail_count}")
    print(f"Total with images: {already_done + success_count}/{total}")
    if failed_recipes:
        print(f"\nFailed recipes ({len(failed_recipes)}):")
        for t in failed_recipes:
            print(f"  - {t}")
    print("=" * 60)


if __name__ == "__main__":
    main()
