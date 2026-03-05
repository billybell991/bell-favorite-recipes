import os, re

recipe_dir = 'content/recipes'
titles = []
for f in sorted(os.listdir(recipe_dir)):
    if f.endswith('.md'):
        path = os.path.join(recipe_dir, f)
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        m = re.search(r'^title:\s*["\'](.+?)["\']', content, re.MULTILINE)
        if not m:
            m = re.search(r'^title:\s*(.+)', content, re.MULTILINE)
        title = m.group(1).strip() if m else f
        tags_m = re.search(r'^tags:\s*\[(.+?)\]', content, re.MULTILINE)
        cats_m = re.search(r'^categories:\s*\[(.+?)\]', content, re.MULTILINE)
        tags = tags_m.group(1) if tags_m else ''
        cats = cats_m.group(1) if cats_m else ''
        titles.append(f'{title}|||{tags}|||{cats}')
for t in titles:
    print(t)
print(f'TOTAL: {len(titles)}')
