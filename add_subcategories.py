"""Add subcategory field to Mom's Cookbook recipes based on their tags."""
import os
import re

RECIPES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "recipes")

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

updated = 0
skipped = 0

for f in sorted(os.listdir(RECIPES_DIR)):
    if not f.endswith('.md') or f == '_index.md':
        continue
    filepath = os.path.join(RECIPES_DIR, f)
    with open(filepath, 'r', encoding='utf-8') as fh:
        content = fh.read()

    # Only process Mom's Cookbook
    cat_m = re.search(r'categories:\s*\[(.+?)\]', content)
    if not cat_m or 'Mom' not in cat_m.group(1):
        continue

    # Skip if already has subcategory
    if 'subcategory:' in content:
        skipped += 1
        continue

    # Find the section from tags
    tag_m = re.search(r'tags:\s*\[(.+?)\]', content)
    if not tag_m:
        print(f"  NO TAGS: {f}")
        continue

    tags = re.findall(r'"([^"]+)"', tag_m.group(1))
    section = None
    for t in tags:
        if t.lower() in SECTION_MAP:
            section = SECTION_MAP[t.lower()]
            break

    if not section:
        print(f"  UNMAPPED: {f} tags={tags}")
        continue

    # Insert subcategory after categories line
    content = re.sub(
        r'(categories:\s*\[.+?\])',
        f'\\1\nsubcategory: "{section}"',
        content,
        count=1,
    )

    with open(filepath, 'w', encoding='utf-8') as fh:
        fh.write(content)

    updated += 1

print(f"Updated: {updated}")
print(f"Skipped (already had subcategory): {skipped}")
