"""Find the 16 recipes that still don't have ## Ingredients / ## Instructions sections."""
import os, re

RECIPE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "recipes")

for f in sorted(os.listdir(RECIPE_DIR)):
    if not f.endswith('.md') or f == '_index.md':
        continue
    with open(os.path.join(RECIPE_DIR, f), encoding='utf-8') as fh:
        content = fh.read()
    parts = content.split('---', 2)
    if len(parts) < 3:
        continue
    body = parts[2]
    if not re.search(r'^##\s*(Ingredients|Instructions)', body, re.MULTILINE | re.IGNORECASE):
        title_m = re.search(r'title:\s*"([^"]*)"', parts[1])
        title = title_m.group(1) if title_m else f
        print(f"  {title}  ({f})")
