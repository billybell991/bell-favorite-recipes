"""Convert subcategory: "X" to subcategories: ["X"] in all recipe files."""
import os, re

d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "recipes")
count = 0
for f in sorted(os.listdir(d)):
    if not f.endswith('.md'):
        continue
    path = os.path.join(d, f)
    c = open(path, 'r', encoding='utf-8').read()
    m = re.search(r'^subcategory:\s*"([^"]+)"', c, re.MULTILINE)
    if m:
        old = m.group(0)
        val = m.group(1)
        new_val = f'subcategories: ["{val}"]'
        c2 = c.replace(old, new_val, 1)
        open(path, 'w', encoding='utf-8').write(c2)
        count += 1
print(f"Converted {count} files")
