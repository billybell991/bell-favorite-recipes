"""
Update recipe images using blurb-based Pexels API search.
Reads each recipe's ingredients + instructions, generates a descriptive
food blurb, and uses that as the Pexels search query for a better image match.
"""
import os
import re
import sys
import time
import requests

API_KEY = os.environ.get("PEXELS_API_KEY", "")
HEADERS = {"Authorization": API_KEY}

# ── helpers ──────────────────────────────────────────────────────────────────

def read_recipe(filepath):
    """Return (frontmatter, body, title) from a recipe markdown file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, None, None
    fm = parts[1]
    body = parts[2]
    m = re.search(r'title:\s*"([^"]*)"', fm)
    title = m.group(1) if m else None
    return fm, body, title


def extract_ingredients(body):
    """Pull ingredient lines from the markdown body."""
    ingredients = []
    in_section = False
    for line in body.splitlines():
        if re.match(r"^##\s*Ingredients", line, re.IGNORECASE):
            in_section = True
            continue
        if in_section:
            if re.match(r"^##\s", line):
                break
            stripped = line.strip().lstrip("- ").strip()
            if stripped:
                ingredients.append(stripped)
    return ingredients


def extract_instructions(body):
    """Pull instruction text from the markdown body."""
    lines = []
    in_section = False
    for line in body.splitlines():
        if re.match(r"^##\s*Instructions", line, re.IGNORECASE):
            in_section = True
            continue
        if in_section:
            if re.match(r"^##\s", line):
                break
            # Stop at credit lines
            if re.match(r"^Credit", line, re.IGNORECASE):
                break
            if re.match(r"^\[", line):
                break
            stripped = line.strip()
            # Remove leading numbers like "1. "
            stripped = re.sub(r"^\d+\.\s*", "", stripped)
            if stripped and stripped.lower() not in ("tips:", "notes:"):
                lines.append(stripped)
    return lines


def build_blurb(title, ingredients, instructions):
    """
    Build a short, vivid food description from the title + instructions only.
    Ingredients are intentionally ignored — they add noise about raw materials
    rather than describing the finished dish.
    """
    # Clean "air fryer" out of the title to focus on the food itself
    clean_title = re.sub(r"\bair\s*fryer\b", "", title, flags=re.IGNORECASE).strip()
    clean_title = clean_title.strip("-–— ")

    # Extract cooking/appearance descriptors from instructions
    descriptors = []
    descriptor_patterns = [
        r"crisp[y]?", r"golden\s*brown", r"golden", r"juicy", r"tender",
        r"crunchy", r"flaky", r"creamy", r"caramelized",
        r"breaded", r"glazed", r"browned", r"seared",
    ]
    full_text = " ".join(instructions).lower()
    for pat in descriptor_patterns:
        if re.search(pat, full_text):
            word = re.search(pat, full_text).group()
            if word not in descriptors:
                descriptors.append(word)

    # Build blurb: up to 2 descriptors + dish name + "served on a plate"
    blurb_parts = []
    if descriptors:
        blurb_parts.append(" ".join(descriptors[:2]))
    blurb_parts.append(clean_title)
    blurb_parts.append("served on a plate")

    blurb = " ".join(blurb_parts)
    # Trim to reasonable length for API query (max ~80 chars works best)
    if len(blurb) > 100:
        blurb = blurb[:100].rsplit(" ", 1)[0]

    return blurb


def search_pexels(query, per_page=5):
    """Search Pexels and return photo list."""
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": per_page, "orientation": "landscape"},
            headers=HEADERS, timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("photos", [])
        print(f"    API error: HTTP {resp.status_code}")
        return []
    except Exception as e:
        print(f"    API error: {e}")
        return []


def pick_working_photo(photos, used_ids):
    """Pick the first photo whose URL actually loads (HTTP 200)."""
    for photo in photos:
        pid = photo["id"]
        if pid in used_ids:
            continue
        url = f"https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg?auto=compress&cs=tinysrgb&w=600"
        try:
            r = requests.head(url, timeout=10, allow_redirects=True)
            if r.status_code == 200:
                used_ids.add(pid)
                return url, pid, photo.get("alt", "")
        except Exception:
            pass
    return None, None, None


def update_image_in_file(filepath, new_url):
    """Replace the image URL in a recipe file's frontmatter."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r'image:\s*"[^"]*"', f'image: "{new_url}"', content)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    recipe_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "recipes")
    dry_run = "--dry-run" in sys.argv

    category_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("--category="):
            category_filter = arg.split("=", 1)[1]

    if not API_KEY:
        print("ERROR: Set PEXELS_API_KEY environment variable")
        sys.exit(1)

    print(f"Recipe dir: {recipe_dir}")
    print(f"Category filter: {category_filter or 'ALL'}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    files = sorted(f for f in os.listdir(recipe_dir) if f.endswith(".md") and f != "_index.md")
    used_ids = set()
    updated = 0
    skipped = 0
    failed = 0

    for filename in files:
        filepath = os.path.join(recipe_dir, filename)
        fm, body, title = read_recipe(filepath)
        if not fm or not title:
            continue

        # Category filter
        if category_filter:
            cat_match = re.search(r'categories:\s*\["([^"]*)"', fm)
            if not cat_match or category_filter.lower() not in cat_match.group(1).lower():
                continue

        print(f"── {title} ──")

        ingredients = extract_ingredients(body)
        instructions = extract_instructions(body)

        if not ingredients:
            print(f"  SKIP: no ingredients found")
            skipped += 1
            continue

        blurb = build_blurb(title, ingredients, instructions)
        print(f"  Blurb: \"{blurb}\"")

        photos = search_pexels(blurb)

        # Fallback: simpler query if blurb is too specific
        if not photos:
            # Try just the cleaned title + "food"
            fallback = re.sub(r"\bair\s*fryer\b", "", title, flags=re.IGNORECASE).strip() + " food"
            print(f"  Fallback: \"{fallback}\"")
            photos = search_pexels(fallback)
            time.sleep(0.3)

        if not photos:
            print(f"  FAILED: no photos found")
            failed += 1
            continue

        url, pid, alt = pick_working_photo(photos, used_ids)
        if not url:
            print(f"  FAILED: no working photo URLs")
            failed += 1
            continue

        print(f"  Photo: ID={pid}")
        print(f"  Alt: \"{alt[:80]}\"")

        if dry_run:
            print(f"  DRY RUN: would update {filename}")
        else:
            update_image_in_file(filepath, url)
            print(f"  UPDATED: {filename}")

        updated += 1
        time.sleep(0.5)  # rate limit

    print(f"\nDone! Updated: {updated}, Skipped: {skipped}, Failed: {failed}")


if __name__ == "__main__":
    main()
