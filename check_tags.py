import os, re
from collections import Counter

tags = Counter()
recipes_dir = 'content/recipes'
for f in sorted(os.listdir(recipes_dir)):
    if not f.endswith('.md') or f == '_index.md':
        continue
    with open(os.path.join(recipes_dir, f), encoding='utf-8') as fh:
        content = fh.read()
    cat_m = re.search(r'categories:\s*\[(.+?)\]', content)
    if cat_m and 'Mom' in cat_m.group(1):
        tag_m = re.search(r'tags:\s*\[(.+?)\]', content)
        if tag_m:
            for t in re.findall(r'"([^"]+)"', tag_m.group(1)):
                tags[t] += 1
for tag, count in sorted(tags.items()):
    print(f'  {tag}: {count}')
print(f'\nTotal unique tags: {len(tags)}')
