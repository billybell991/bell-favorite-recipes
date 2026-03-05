import os, re
recipes_dir = 'content/recipes'
titles = []
for f in sorted(os.listdir(recipes_dir)):
    if not f.endswith('.md'): continue
    with open(os.path.join(recipes_dir, f), 'r', encoding='utf-8') as fh:
        content = fh.read()
    m = re.search(r'^title:\s*"(.+?)"', content, re.MULTILINE)
    if m:
        titles.append((f, m.group(1)))
for f, t in titles:
    print(t)
print(f'\n--- Total: {len(titles)} ---')
