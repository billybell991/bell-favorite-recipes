"""
Bulk assign Pexels CDN image URLs to all recipes.
Groups recipes by search term, saves progress for resume capability.
"""
import os, re, sys, time, random, json
import requests
from urllib.parse import quote

CONTENT_DIR = 'content/recipes'
PROGRESS_FILE = 'image_progress.json'

STRIP_PREFIXES = [
    'Air Fryer', 'Instant Pot', 'Slow Cooker', 'Crock Pot', 'Crockpot',
    'One Pot', 'Sheet Pan', 'Quick and Easy', 'Quick & Easy', 'Quick',
    'Easy', 'Best Ever', 'Best', 'Classic', 'Simple', 'Homemade',
    'Old Fashioned', 'The Best', 'My Favorite', 'Copycat', 'Keto',
    'Low Carb', 'Healthy', 'Skinny', 'Amazing', 'Perfect', 'Ultimate',
    'Delicious', 'Super',
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}


def extract_search_term(title):
    """Strip common cooking prefixes to get the core food term."""
    term = title
    for p in sorted(STRIP_PREFIXES, key=len, reverse=True):
        if term.lower().startswith(p.lower()):
            term = term[len(p):].strip(' -\u2013\u2014')
            break
    term = re.sub(r'\s*\(.*?\)\s*', ' ', term).strip()
    return term if len(term) > 2 else title


def search_pexels(session, query):
    """Search Pexels for food photos. Returns list of CDN URLs or 'BLOCKED'."""
    url = f'https://www.pexels.com/search/{quote(query)}/'
    try:
        resp = session.get(url, timeout=20)
        if resp.status_code == 403:
            return 'BLOCKED'
        if resp.status_code != 200:
            print(f'    HTTP {resp.status_code}', flush=True)
            return []

        # Extract photo CDN URLs from page
        pattern = r'https://images\.pexels\.com/photos/(\d+)/([^"?\s]+\.(?:jpeg|jpg|png))'
        matches = re.findall(pattern, resp.text)

        urls = []
        seen = set()
        for photo_id, filename in matches:
            if photo_id not in seen:
                seen.add(photo_id)
                urls.append(
                    f'https://images.pexels.com/photos/{photo_id}/{filename}?auto=compress&cs=tinysrgb&w=600'
                )
        return urls[:10]
    except requests.exceptions.Timeout:
        print(f'    Timeout', flush=True)
        return []
    except Exception as e:
        print(f'    Error: {e}', flush=True)
        return []


def simplify_query(term):
    """Try simpler versions of the search term."""
    words = term.split()
    if len(words) >= 3:
        return ' '.join(words[-2:])
    return None


def main():
    # Load progress
    progress = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            progress = json.load(f)

    # Gather recipes needing images
    recipes = []
    for fname in sorted(os.listdir(CONTENT_DIR)):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(CONTENT_DIR, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'image: ""' not in content:
            continue
        m = re.search(r'^title:\s*"(.+)"', content, re.MULTILINE)
        if m:
            recipes.append((fname, fpath, m.group(1)))

    total = len(recipes)
    remaining = [r for r in recipes if r[0] not in progress]

    print(f'Total needing images: {total}', flush=True)
    print(f'Already processed: {total - len(remaining)}', flush=True)
    print(f'Remaining: {len(remaining)}', flush=True)

    if not remaining:
        print('All done!', flush=True)
        return

    # Group by search term
    term_groups = {}
    for fname, fpath, title in remaining:
        term = extract_search_term(title)
        if term not in term_groups:
            term_groups[term] = []
        term_groups[term].append((fname, fpath, title))

    print(f'Unique search terms: {len(term_groups)}', flush=True)
    print(f'Starting searches...\n', flush=True)

    session = requests.Session()
    session.headers.update(HEADERS)

    # Warm up session with homepage visit
    try:
        session.get('https://www.pexels.com/', timeout=15)
        time.sleep(random.uniform(2, 3))
    except Exception:
        pass

    success = 0
    failed = 0
    blocked = False
    search_count = 0

    for i, (term, group) in enumerate(sorted(term_groups.items())):
        if blocked:
            break

        recipe_names = ', '.join(t for _, _, t in group)
        print(f'[{i+1}/{len(term_groups)}] "{term}" ({len(group)} recipes: {recipe_names})', flush=True)

        urls = search_pexels(session, term)
        search_count += 1

        if urls == 'BLOCKED':
            print('  >>> BLOCKED by Pexels! Saving progress...', flush=True)
            blocked = True
            break

        # Retry with simpler term if no results
        if not urls:
            simpler = simplify_query(term)
            if simpler:
                time.sleep(random.uniform(2, 4))
                print(f'  Retry: "{simpler}"', flush=True)
                urls = search_pexels(session, simpler)
                search_count += 1
                if urls == 'BLOCKED':
                    blocked = True
                    break

        if not urls:
            for fname, fpath, title in group:
                progress[fname] = None
                failed += 1
            print(f'  MISS - no images found', flush=True)
        else:
            for j, (fname, fpath, title) in enumerate(group):
                img_url = urls[j % len(urls)]
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = content.replace('image: ""', f'image: "{img_url}"', 1)
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                progress[fname] = img_url
                success += 1
            print(f'  OK - {len(group)} recipes assigned', flush=True)

        # Save progress
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2)

        # Rate-limit: longer delay every 50 searches to avoid blocking
        if search_count % 50 == 0:
            delay = random.uniform(15, 25)
            print(f'  [Cooling down {delay:.0f}s after {search_count} searches]', flush=True)
        else:
            delay = random.uniform(4, 8)
        time.sleep(delay)

    # Final summary
    print(f'\n{"="*50}', flush=True)
    print(f'SUMMARY', flush=True)
    print(f'  Searches made: {search_count}', flush=True)
    print(f'  Recipes assigned: {success}', flush=True)
    print(f'  No image found: {failed}', flush=True)
    if blocked:
        done = sum(1 for v in progress.values() if v is not None)
        left = total - len(progress)
        print(f'  Still remaining: {left}', flush=True)
        print(f'  Run this script again to resume from where it stopped.', flush=True)
    print(f'{"="*50}', flush=True)


if __name__ == '__main__':
    main()
