"""Update images for the 6 new Campbell's recipes using Pexels API."""
import os
import re
import time
import requests

API_KEY = os.environ.get("PEXELS_API_KEY", "")
RECIPES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "recipes")
HEADERS = {"Authorization": API_KEY}

TARGET_FILES = [
    "campbells-2-step-honey-mustard-chicken.md",
    "campbells-2-step-lemon-broccoli-chicken.md",
    "campbells-2-step-mushroom-pork-chops.md",
    "campbells-easy-2-step-beefy-taco-joes.md",
    "campbells-easy-2-step-chicken.md",
    "campbells-easy-2-step-creamy-chicken-pasta.md",
]

SEARCH_QUERIES = {
    "campbells-2-step-honey-mustard-chicken.md": "honey mustard chicken breast",
    "campbells-2-step-lemon-broccoli-chicken.md": "lemon broccoli chicken",
    "campbells-2-step-mushroom-pork-chops.md": "mushroom pork chops",
    "campbells-easy-2-step-beefy-taco-joes.md": "sloppy joe sandwich beef",
    "campbells-easy-2-step-chicken.md": "creamy chicken skillet",
    "campbells-easy-2-step-creamy-chicken-pasta.md": "creamy chicken pasta vegetables",
}

used_ids = set()

for filename in TARGET_FILES:
    query = SEARCH_QUERIES[filename]
    print(f"\n{filename}")
    print(f"  Searching: {query}")

    resp = requests.get(
        "https://api.pexels.com/v1/search",
        headers=HEADERS,
        params={"query": query, "per_page": 15, "orientation": "landscape"},
        timeout=15,
    )

    if resp.status_code == 429:
        print("  Rate limited! Waiting 60s...")
        time.sleep(60)
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers=HEADERS,
            params={"query": query, "per_page": 15, "orientation": "landscape"},
            timeout=15,
        )

    if resp.status_code != 200:
        print(f"  ERROR: {resp.status_code}")
        continue

    photos = resp.json().get("photos", [])
    chosen = None
    for photo in photos:
        if photo["id"] not in used_ids:
            url = photo["src"]["medium"]
            try:
                check = requests.head(url, timeout=10)
                if check.status_code == 200:
                    chosen = photo
                    break
            except:
                continue

    if not chosen:
        print("  No suitable photo found")
        continue

    used_ids.add(chosen["id"])
    image_url = chosen["src"]["medium"]
    print(f"  Found: {image_url}")

    filepath = os.path.join(RECIPES_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    content = re.sub(
        r'^image:\s*".*?"',
        f'image: "{image_url}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  Updated!")
    time.sleep(0.5)

print("\nDone!")
