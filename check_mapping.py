"""Check tag mapping for Mom's Cookbook recipes to the 12 Google Sites subsections."""
import os, re

SECTION_MAP = {
    "appetizers": "Appetizers",
    "dip": "Appetizers",
    "bread": "Breads",
    "breads": "Breads",
    "cake frosting": "Cake Frosting",
    "cake": "Cakes and Muffins",
    "cakes and muffins": "Cakes and Muffins",
    "muffins": "Cakes and Muffins",
    "casseroles": "Casseroles",
    "chicken": "Chicken",
    "cookies": "Cookies",
    "dessert": "Desserts",
    "desserts": "Desserts",
    "pie": "Desserts",
    "diabetic recipes": "Diabetic Recipes",
    "fish": "Fish",
    "salmon": "Fish",
    "shrimp": "Fish",
    "fun things": "Fun Things",
    "meat": "Meat",
    "beef": "Meat",
    "pork": "Meat",
    "stew": "Meat",
    "soup": "Meat",
    "pasta": "Casseroles",
    "potatoes": "Casseroles",
    "rice": "Casseroles",
    "salad": "Appetizers",
    "instant pot": "Casseroles",
}

recipes_dir = 'content/recipes'
unmapped = []
mapped_counts = {}

for f in sorted(os.listdir(recipes_dir)):
    if not f.endswith('.md') or f == '_index.md':
        continue
    with open(os.path.join(recipes_dir, f), encoding='utf-8') as fh:
        content = fh.read()
    cat_m = re.search(r'categories:\s*\[(.+?)\]', content)
    if not cat_m or 'Mom' not in cat_m.group(1):
        continue
    tag_m = re.search(r'tags:\s*\[(.+?)\]', content)
    if not tag_m:
        title_m = re.search(r'title:\s*"([^"]*)"', content)
        unmapped.append((f, title_m.group(1) if title_m else f, "NO TAGS"))
        continue
    tags = re.findall(r'"([^"]+)"', tag_m.group(1))
    # Find first matching section
    section = None
    for t in tags:
        if t.lower() in SECTION_MAP:
            section = SECTION_MAP[t.lower()]
            break
    if section:
        mapped_counts[section] = mapped_counts.get(section, 0) + 1
    else:
        title_m = re.search(r'title:\s*"([^"]*)"', content)
        unmapped.append((f, title_m.group(1) if title_m else f, str(tags)))

print("MAPPED SECTIONS:")
for s, c in sorted(mapped_counts.items()):
    print(f"  {s}: {c}")
print(f"\nTotal mapped: {sum(mapped_counts.values())}")

if unmapped:
    print(f"\nUNMAPPED ({len(unmapped)}):")
    for fn, title, tags in unmapped:
        print(f"  {title} -- tags: {tags}")
