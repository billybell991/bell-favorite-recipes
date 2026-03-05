import os, re

recipes_dir = 'content/recipes'
cats_set = set()
tags_set = set()
data = []

for f in sorted(os.listdir(recipes_dir)):
    if not f.endswith('.md'):
        continue
    with open(os.path.join(recipes_dir, f), encoding='utf-8') as fh:
        content = fh.read()
    
    tm = re.search(r'title:\s*"(.+?)"', content)
    cm = re.search(r'categories:\s*\[(.+?)\]', content)
    tgm = re.search(r'tags:\s*\[(.+?)\]', content)
    
    title = tm.group(1) if tm else '???'
    cats = [c.strip().strip('"') for c in cm.group(1).split(',')] if cm else []
    tags = [t.strip().strip('"') for t in tgm.group(1).split(',')] if tgm else []
    
    for c in cats:
        if c: cats_set.add(c)
    for t in tags:
        if t: tags_set.add(t)
    
    data.append((title, cats, tags, f))

print("=== CATEGORIES ===")
for c in sorted(cats_set):
    print(f"  {c}")

print(f"\n=== TAGS (unique: {len(tags_set)}) ===")
for t in sorted(tags_set):
    print(f"  {t}")

print(f"\nTotal recipes: {len(data)}")

print("\n=== ALL RECIPES ===")
for title, cats, tags, fname in data:
    c = ', '.join(cats) if cats else '-'
    t = ', '.join(tags) if tags else '-'
    print(f"  {title} | cat: {c} | tags: {t}")
