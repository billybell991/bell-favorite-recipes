"""Quick audit: show every recipe title and its assigned photo ID."""
import os, re

recipes_dir = os.path.join(os.path.dirname(__file__), "content", "recipes")
results = []
for f in sorted(os.listdir(recipes_dir)):
    if not f.endswith('.md'):
        continue
    content = open(os.path.join(recipes_dir, f), 'r', encoding='utf-8').read()
    tm = re.search(r'^title:\s*"(.+?)"', content, re.MULTILINE)
    im = re.search(r'^image:\s*".*?photos/(\d+)/.*?"', content, re.MULTILINE)
    if tm:
        title = tm.group(1)
        pid = im.group(1) if im else 'NONE'
        results.append(f'{title} | {pid}')

for r in results:
    print(r)
print(f'\nTotal: {len(results)}')
