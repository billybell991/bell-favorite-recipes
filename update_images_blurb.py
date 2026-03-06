"""
Update recipe images using description-based Pexels API search.
Reads each recipe's description (blurb) from frontmatter and extracts
food-relevant keywords to search Pexels for a better-matching image.
"""
import os
import re
import sys
import time
import requests

API_KEY = os.environ.get("PEXELS_API_KEY", "")
HEADERS = {"Authorization": API_KEY}

# ── helpers ──────────────────────────────────────────────────────────────────

# Non-food words to strip from descriptions before searching
REMOVE_WORDS = {
    # Adjectives
    'amazing', 'amazingly', 'beautiful', 'best', 'big', 'bright', 'buttery',
    'chewy', 'classic', 'comforting', 'creamy', 'crispy', 'crunchy', 'crusty',
    'decadent', 'delicious', 'dense', 'easy', 'famous', 'flaky', 'fluffy',
    'fresh', 'freshly', 'genius', 'golden', 'golden-topped', 'gorgeous',
    'great', 'hearty', 'heavenly', 'homemade', 'hot', 'incredible',
    'indulgent', 'irresistible', 'juicy', 'luscious', 'luxurious',
    'moist', 'old-fashioned', 'perfect', 'perfectly', 'pillowy', 'pure',
    'quick', 'rich', 'rustic', 'silky', 'simple', 'smooth', 'soft',
    'soul-warming', 'special', 'steaming', 'stunning', 'succulent', 'sweet',
    'tangy', 'tender', 'thick', 'ultimate', 'unbelievably', 'velvety',
    'warm', 'wholesome', 'wonderful',
    'addictive', 'satisfying', 'show-stopping', 'crowd-pleasing',
    # Filler/narrative words
    'kind', 'one', 'everyone', 'never', 'ever', 'way', 'thing', 'things',
    'life', 'best', 'first', 'last', 'long', 'full', 'right', 'like',
    'good', 'makes', 'make', 'made', 'come', 'comes', 'feels',
    'feel', 'stays', 'stay', 'turns', 'turn', 'hits', 'hit',
    'enough', 'simply', 'truly', 'really', 'exactly',
    'always', 'absolutely', 'totally', 'completely',
    'recipe', 'recipes', 'kitchen', 'house', 'home', 'room', 'table',
    'counter', 'oven', 'pan', 'pot', 'bowl', 'plate', 'platter',
    'batch', 'double', 'second', 'seconds', 'morning', 'evening',
    'day', 'tuesday', 'holiday', 'celebration', 'occasion', 'party',
    'bake', 'sale', 'bakery', 'store', 'bought',
    'proof', 'someone', 'something', 'anything', 'everything',
    'wonder', 'effort', 'satisfaction', 'comfort', 'treat',
    'ask', 'asked', 'share', 'shared', 'reach', 'reaches', 'request',
    'disappears', 'disappear', 'vanish', 'unattended', 'impossible',
    'dangerous', 'dangerously', 'outrageously',
    'once', 'start', 'stop', 'stopping', 'munching', 'nights', 'movie',
    'parties', 'smear', 'cup', 'coffee', 'lazy', 'better', 'straight',
    'dream', 'alongside', 'meal', 'slathered', 'inside', 'outside',
    'pull', 'apart', 'wonder', 'aroma', 'smell', 'fills', 'incredible',
    'bite', 'forkful', 'spoonful', 'spoon', 'slice', 'piece',
    'jar', 'eyes', 'close', 'mid-bite', 'name', 'gorgeous',
    'tastes', 'taste', 'needed', 'took', 'actually',
    'knew', 'doing', 'bright', 'citrusy', 'showstopper',
    'goodness', 'scratch', 'real', 'ingredients', 'whole',
    'no-bake', 'looks', 'looked', 'looking', 'large', 'medium', 'small',
    'sized', 'flavorful', 'food', 'line', 'sheet', 'foil', 'grease',
    'topped', 'topping', 'put', 'top', 'melted', 'folded', 'around',
    'baked', 'cooked', 'served', 'tossed', 'mixed', 'rubbed',
    'seasoned', 'prepared', 'finished', 'stuffed',
    'tsp', 'tbsp', 'tspcinnamon', 'cups',
    # People/names and narrative
    'tracey', 'colette', 'pep', 'grandma', 'mom', 'ann', 'yan',
    'career', 'girl', 'husband', 'poor', 'man',
    'gets', 'got', 'came', 'went', 'dog-eared', 'cookbook',
    'melt-in-your-mouth', 'golden-brown',
    'pkg', 'package',
    'passed', 'down', 'generations', 'shatters', 'crumble', 'crumbles',
    'store-bought', 'make-ahead', 'triple-coated', 'steeped',
    'slices', 'lean', 'boneless',
    # Common English
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
    'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
    'would', 'could', 'should', 'may', 'might', 'can', 'shall',
    'that', 'this', 'these', 'those', 'it', 'its', 'they', 'them',
    'their', 'we', 'our', 'you', 'your', 'he', 'she', 'his', 'her',
    'who', 'which', 'what', 'where', 'when', 'how', 'why',
    'not', 'no', 'nor', 'so', 'if', 'than', 'too', 'very',
    'just', 'about', 'above', 'after', 'again', 'all', 'also', 'any',
    'because', 'before', 'between', 'both', 'each', 'even', 'every',
    'into', 'more', 'most', 'much', 'only', 'other', 'out', 'over',
    'own', 'same', 'some', 'still', 'such', 'then', 'there', 'through',
    'under', 'until', 'up', 'upon', 'while',
}

# Food-related words to KEEP even if short
FOOD_WORDS = {
    'pie', 'ham', 'jam', 'dip', 'rib', 'rub', 'tea', 'egg', 'cod', 'rum',
    'rye', 'fig', 'nut', 'oat', 'yam',
}


def read_recipe(filepath):
    """Return (frontmatter, body, title, description) from a recipe markdown file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, None, None, None
    fm = parts[1]
    body = parts[2]
    m = re.search(r'title:\s*"([^"]*)"', fm)
    title = m.group(1) if m else None
    d = re.search(r'description:\s*"((?:[^"\\]|\\.)*)"', fm)
    description = d.group(1) if d else None
    return fm, body, title, description


# Extra words to remove only from description (not from title)
DESC_ONLY_REMOVE = {
    'charlie', 'brown', 'instant', 'mix',
}


def build_search_query(title, description):
    """
    Build a Pexels search query using the title as the primary signal,
    enriched with food nouns from the description (adjectives stripped).
    """
    if not description:
        clean = re.sub(r"\(.*?\)", "", title)
        clean = re.sub(r"'s\b", "", clean)
        return clean.strip()

    # Use title as base, enrich with food nouns from description
    clean_title = re.sub(r"\(.*?\)", "", title)
    clean_title = re.sub(r"'s\b", "", clean_title).strip()

    text = description
    text = re.sub(r"[^a-zA-Z\s-]", " ", text)
    words = text.lower().split()

    kept = []
    seen = set()

    # Add title words first (most important signal)
    for w in clean_title.lower().split():
        w = w.strip("-")
        if w and w not in REMOVE_WORDS and w not in seen:
            kept.append(w)
            seen.add(w)

    # Then add food nouns from description (with extra filtering)
    for w in words:
        w = w.strip("-")
        if not w or (len(w) < 3 and w not in FOOD_WORDS):
            continue
        if w in REMOVE_WORDS or w in DESC_ONLY_REMOVE:
            continue
        if w not in seen:
            kept.append(w)
            seen.add(w)

    # Keep 4-6 words max for best Pexels results
    query = " ".join(kept[:6])
    return query


def search_pexels(query, per_page=5):
    """Search Pexels and return photo list, with retry on 429."""
    for attempt in range(5):
        try:
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                params={"query": query, "per_page": per_page, "orientation": "landscape"},
                headers=HEADERS, timeout=10,
            )
            if resp.status_code == 200:
                return resp.json().get("photos", [])
            if resp.status_code == 429:
                wait = 2 ** attempt * 5  # 5, 10, 20, 40, 80 seconds
                print(f"    Rate limited (429), waiting {wait}s (attempt {attempt+1}/5)...")
                time.sleep(wait)
                continue
            print(f"    API error: HTTP {resp.status_code}")
            return []
        except Exception as e:
            print(f"    API error: {e}")
            return []
    print(f"    Giving up after 5 retries")
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

    # Load already-processed files for resume capability
    done_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image_update_done.txt")
    already_done = set()
    if os.path.exists(done_file):
        with open(done_file, "r", encoding="utf-8") as df:
            already_done = {line.strip() for line in df if line.strip()}
        print(f"Resuming: {len(already_done)} recipes already processed, skipping them.")

    used_ids = set()
    updated = 0
    skipped = 0
    failed = 0

    for filename in files:
        filepath = os.path.join(recipe_dir, filename)
        fm, body, title, description = read_recipe(filepath)
        if not fm or not title:
            continue

        # Category filter
        if category_filter:
            cat_match = re.search(r'categories:\s*\["([^"]*)"', fm)
            if not cat_match or category_filter.lower() not in cat_match.group(1).lower():
                continue

        if filename in already_done:
            skipped += 1
            continue

        print(f"-- {title} --")

        query = build_search_query(title, description)
        print(f"  Query: \"{query}\"")

        photos = search_pexels(query)

        # Fallback: try just the title cleaned up
        if not photos:
            fallback = re.sub(r"\(.*?\)", "", title).strip()
            fallback = re.sub(r"'s\b", "", fallback).strip()
            print(f"  Fallback: \"{fallback}\"")
            time.sleep(1.5)
            photos = search_pexels(fallback)

        # Second fallback: last 2-3 words of the title (usually the food noun)
        if not photos:
            words = re.sub(r"\(.*?\)", "", title).split()
            if len(words) > 2:
                fallback2 = " ".join(words[-3:])
                print(f"  Fallback2: \"{fallback2}\"")
                time.sleep(1.5)
                photos = search_pexels(fallback2)

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
            with open(done_file, "a", encoding="utf-8") as df:
                df.write(filename + "\n")
        updated += 1
        time.sleep(2)  # rate limit

    print(f"\nDone! Updated: {updated}, Skipped: {skipped}, Failed: {failed}")


if __name__ == "__main__":
    main()
