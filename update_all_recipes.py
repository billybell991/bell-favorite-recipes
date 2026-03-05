"""
Generate blurbs + update images for ALL recipes.
- Reads each recipe's title + instructions
- Crafts a vivid food description blurb
- Saves blurb to the description field
- Searches Pexels with the blurb for a matching image
- Validates the image URL works before saving

Supports:
  --dry-run         Preview without changing files
  --category=X      Only process one category
  --blurbs-only     Only generate descriptions, skip image search
  --images-only     Only update images (use existing descriptions as search)
  --skip-existing   Skip recipes that already have a description
  --batch=N         Process N recipes then stop (for rate limiting)
  --offset=N        Start from recipe N (0-based, for resuming)
"""
import os
import re
import sys
import time
import json
import requests

API_KEY = os.environ.get("PEXELS_API_KEY", "")
HEADERS = {"Authorization": API_KEY}
RECIPE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "recipes")

# Non-food recipes that need special handling
SKIP_TITLES = {
    "baker's clay instructions",
    "ornament clay dough",
    "playdough",
    "frontier kitchen chemical garden",
    "helpful hints for healthy cooking",
}


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


def extract_instructions(body):
    """Pull instruction text from the recipe body."""
    lines = []
    in_section = False
    for line in body.splitlines():
        if re.match(r"^##\s*Instructions", line, re.IGNORECASE):
            in_section = True
            continue
        if in_section:
            if re.match(r"^##\s", line):
                break
            if re.match(r"^Credit", line, re.IGNORECASE):
                break
            if re.match(r"^\[", line):
                break
            stripped = line.strip()
            stripped = re.sub(r"^\d+\.\s*", "", stripped)
            if stripped:
                lines.append(stripped)
    # If no ## Instructions section, try to get paragraph text after ingredients
    if not lines:
        in_body = False
        past_ingredients = False
        for line in body.splitlines():
            if re.match(r"^##\s*Ingredients", line, re.IGNORECASE):
                in_body = True
                continue
            if in_body and not line.strip().startswith("- ") and line.strip():
                past_ingredients = True
            if past_ingredients:
                stripped = line.strip()
                if stripped and not stripped.startswith("- "):
                    if re.match(r"^(Credit|NOTE|VARIATION|Yield|Tip|Here's a link|\[)", stripped, re.IGNORECASE):
                        break
                    lines.append(stripped)
    return lines


def extract_ingredients(body):
    """Pull ingredient lines from the body."""
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


def build_blurb(title, instructions):
    """
    Craft a vivid, appetizing description of the finished dish
    based on the title and cooking instructions.
    """
    clean_title = title
    # Remove category-style prefixes
    clean_title = re.sub(r"\bair\s*fryer\b", "", clean_title, flags=re.IGNORECASE)
    clean_title = re.sub(r"\binstant\s*pot\b", "", clean_title, flags=re.IGNORECASE)
    clean_title = re.sub(r"\bketo\b", "", clean_title, flags=re.IGNORECASE)
    clean_title = re.sub(r"\blow[- ]carb\b", "", clean_title, flags=re.IGNORECASE)
    clean_title = re.sub(r"\(.*?\)", "", clean_title)  # remove parentheticals
    clean_title = clean_title.strip(" -–—:,.")

    # Extract descriptors from instructions
    descriptors = []
    descriptor_patterns = [
        (r"\bcrisp[y]?\b", "crispy"),
        (r"\bgolden\s*brown\b", "golden brown"),
        (r"\bjuicy\b", "juicy"),
        (r"\btender\b", "tender"),
        (r"\bcrunchy\b", "crunchy"),
        (r"\bflaky\b", "flaky"),
        (r"\bcreamy\b", "creamy"),
        (r"\bcaramelized\b", "caramelized"),
        (r"\bbreaded\b", "breaded"),
        (r"\bglazed\b", "glazed"),
        (r"\bfluffy\b", "fluffy"),
        (r"\brich\b", "rich"),
        (r"\bhearty\b", "hearty"),
        (r"\bmoist\b", "moist"),
        (r"\bbubbly\b", "bubbly"),
        (r"\btoasted\b", "toasted"),
        (r"\bsavory\b", "savory"),
    ]
    full_text = " ".join(instructions).lower()
    for pat, word in descriptor_patterns:
        if re.search(pat, full_text) and word not in descriptors:
            # Skip "golden brown" if we already have it, and vice versa
            if word == "golden brown":
                descriptors = [d for d in descriptors if d != "golden"]
            descriptors.append(word)

    # Detect cooking method
    methods = []
    method_patterns = [
        (r"\bbake[ds]?\b", "baked"),
        (r"\bfr[yi](?:ed|ing)\b", "fried"),
        (r"\bslow\s*cook", "slow-cooked"),
        (r"\bpressure\s*cook", "pressure-cooked"),
        (r"\bgrilled?\b", "grilled"),
        (r"\broast(?:ed|ing)?\b", "roasted"),
        (r"\bsimmer", "simmered"),
        (r"\bsaut[eé]", "sautéed"),
        (r"\bsteam", "steamed"),
        (r"\bbroil", "broiled"),
        (r"\bsmok(?:ed|ing)\b", "smoked"),
    ]
    for pat, word in method_patterns:
        if re.search(pat, full_text) and word not in methods:
            methods.append(word)

    # Build the blurb
    parts = []

    # Lead with 1-2 descriptors
    if descriptors:
        parts.append(" and ".join(descriptors[:2]))

    # The dish name
    parts.append(clean_title.lower())

    # Add cooking method if found, but avoid redundancy
    # (e.g. don't say "baked chicken, baked to perfection")
    if methods:
        method = methods[0]
        if method.rstrip("d") not in clean_title.lower():
            parts.append(method + " to perfection")

    blurb = ", ".join(parts) if parts else clean_title.lower()

    # Capitalize first letter
    blurb = blurb[0].upper() + blurb[1:] if blurb else clean_title

    # Trim length for a good search query + readable description
    if len(blurb) > 120:
        blurb = blurb[:120].rsplit(",", 1)[0]

    return blurb


def build_search_query(blurb, title):
    """
    Create a Pexels search query from the blurb.
    Shorter and more focused than the full blurb.
    """
    # Use the cleaned title as the primary search, with key descriptors
    clean_title = title
    clean_title = re.sub(r"\bair\s*fryer\b", "", clean_title, flags=re.IGNORECASE)
    clean_title = re.sub(r"\binstant\s*pot\b", "", clean_title, flags=re.IGNORECASE)
    clean_title = re.sub(r"\bketo\b", "", clean_title, flags=re.IGNORECASE)
    clean_title = re.sub(r"\blow[- ]carb\b", "", clean_title, flags=re.IGNORECASE)
    clean_title = re.sub(r"\(.*?\)", "", clean_title)
    clean_title = clean_title.strip(" -–—:,.")

    # Extract a couple descriptors from the blurb for flavor
    words = blurb.lower().split()
    good_adjectives = {"crispy", "golden", "creamy", "tender", "juicy", "flaky",
                       "crunchy", "glazed", "caramelized", "hearty", "fluffy",
                       "rich", "warm", "toasted", "savory", "moist"}
    adjectives = [w.strip(",") for w in words if w.strip(",") in good_adjectives]

    query = " ".join(adjectives[:2]) + " " + clean_title if adjectives else clean_title
    query = query.strip()

    # Keep it under ~60 chars for best API results
    if len(query) > 60:
        query = query[:60].rsplit(" ", 1)[0]

    return query


def search_pexels(query, per_page=5):
    """Search Pexels and return photo list."""
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": per_page, "orientation": "landscape"},
            headers=HEADERS, timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get("photos", [])
        if resp.status_code == 429:
            print("    RATE LIMITED - waiting 60s...")
            time.sleep(60)
            return search_pexels(query, per_page)
        print(f"    API error: HTTP {resp.status_code}")
        return []
    except Exception as e:
        print(f"    API error: {e}")
        return []


def pick_working_photo(photos, used_ids):
    """Pick first photo whose URL loads (HTTP 200), avoiding duplicates."""
    for photo in photos:
        pid = photo["id"]
        if pid in used_ids:
            continue
        url = f"https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg?auto=compress&cs=tinysrgb&w=600"
        try:
            r = requests.head(url, timeout=10, allow_redirects=True)
            if r.status_code == 200:
                used_ids.add(pid)
                return url, pid
        except Exception:
            pass
    return None, None


def update_frontmatter(fm, description=None, image_url=None):
    """Update description and/or image in frontmatter."""
    if description is not None:
        # Escape any quotes in the description
        safe_desc = description.replace('"', '\\"')
        fm = re.sub(r'description:\s*"[^"]*"', f'description: "{safe_desc}"', fm)
    if image_url is not None:
        fm = re.sub(r'image:\s*"[^"]*"', f'image: "{image_url}"', fm)
    return fm


def save_recipe(filepath, fm, body):
    """Write the recipe file back."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"---{fm}---{body}")


def main():
    dry_run = "--dry-run" in sys.argv
    blurbs_only = "--blurbs-only" in sys.argv
    images_only = "--images-only" in sys.argv
    skip_existing = "--skip-existing" in sys.argv

    category = None
    batch_size = None
    offset = 0
    for arg in sys.argv[1:]:
        if arg.startswith("--category="):
            category = arg.split("=", 1)[1]
        elif arg.startswith("--batch="):
            batch_size = int(arg.split("=", 1)[1])
        elif arg.startswith("--offset="):
            offset = int(arg.split("=", 1)[1])

    if not blurbs_only and not API_KEY:
        print("ERROR: Set PEXELS_API_KEY environment variable")
        sys.exit(1)

    files = sorted(f for f in os.listdir(RECIPE_DIR)
                   if f.endswith(".md") and f != "_index.md")

    print(f"Total recipe files: {len(files)}")
    print(f"Category: {category or 'ALL'}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    if blurbs_only:
        print("Blurbs only (no image search)")
    if images_only:
        print("Images only (use existing descriptions)")
    if batch_size:
        print(f"Batch: {batch_size} recipes starting at offset {offset}")
    print()

    used_ids = set()
    updated = 0
    skipped = 0
    failed = 0
    processed = 0

    for idx, filename in enumerate(files):
        filepath = os.path.join(RECIPE_DIR, filename)
        fm, body, title = read_recipe(filepath)
        if not fm or not title:
            continue

        # Category filter
        if category:
            cat_match = re.search(r'categories:\s*\["([^"]*)"\]', fm)
            if not cat_match or category.lower() not in cat_match.group(1).lower():
                continue

        # Offset/batch
        processed += 1
        if processed <= offset:
            continue
        if batch_size and (processed - offset) > batch_size:
            print(f"\nBatch limit reached ({batch_size}). Use --offset={processed - 1} to continue.")
            break

        # Skip non-food
        if title.lower() in SKIP_TITLES:
            skipped += 1
            continue

        # Check existing description
        desc_match = re.search(r'description:\s*"([^"]*)"', fm)
        existing_desc = desc_match.group(1).strip() if desc_match else ""

        if skip_existing and existing_desc:
            skipped += 1
            continue

        # === BLURB GENERATION ===
        if not images_only or not existing_desc:
            instructions = extract_instructions(body)
            blurb = build_blurb(title, instructions)

            if not blurb or len(blurb) < 5:
                blurb = title  # fallback to title
        else:
            blurb = existing_desc

        # === IMAGE SEARCH ===
        new_url = None
        if not blurbs_only:
            query = build_search_query(blurb, title)

            photos = search_pexels(query)

            # Fallback: try simpler query
            if not photos:
                fallback = re.sub(r"\bair\s*fryer\b|\binstant\s*pot\b|\bketo\b", "",
                                  title, flags=re.IGNORECASE).strip(" -–—:,.")
                fallback = fallback + " food"
                photos = search_pexels(fallback)
                time.sleep(0.3)

            if photos:
                new_url, pid = pick_working_photo(photos, used_ids)

        # === OUTPUT ===
        if dry_run:
            status = []
            if not images_only:
                status.append(f"blurb=\"{blurb[:60]}...\"" if len(blurb) > 60 else f"blurb=\"{blurb}\"")
            if new_url:
                status.append(f"img=OK(id={pid})")
            elif not blurbs_only:
                status.append("img=FAILED")
            print(f"  {title}: {', '.join(status)}")
        else:
            new_fm = fm
            if not images_only:
                new_fm = update_frontmatter(new_fm, description=blurb)
            if new_url:
                new_fm = update_frontmatter(new_fm, image_url=new_url)
            if new_fm != fm:
                save_recipe(filepath, new_fm, body)
                label = []
                if not images_only:
                    label.append("blurb")
                if new_url:
                    label.append("image")
                print(f"  UPDATED ({'+'.join(label)}): {title}")
            elif not blurbs_only and not new_url:
                print(f"  FAILED (no image): {title}")
                failed += 1
                continue

        updated += 1

        # Rate limit
        if not blurbs_only:
            time.sleep(0.5)

    print(f"\nDone! Updated: {updated}, Skipped: {skipped}, Failed: {failed}")


if __name__ == "__main__":
    main()
