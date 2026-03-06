import os, re

recipes_dir = 'content/recipes'
weak_patterns = [
    'baked to perfection', 'simmered to perfection', 'cooked to perfection',
    'grilled to perfection', 'fried to perfection', 'prepared to perfection',
    'mixed to perfection', 'blended to perfection', 'brewed to perfection',
    'crafted to perfection', 'chilled to perfection', 'frozen to perfection',
    'roasted to perfection', 'toasted to perfection', 'stirred to perfection',
    'seasoned to perfection',
]

total = 0
weak = 0
very_weak = 0
good = 0
weak_files = []
good_files = []

for f in sorted(os.listdir(recipes_dir)):
    if not f.endswith('.md') or f == '_index.md':
        continue
    total += 1
    path = os.path.join(recipes_dir, f)
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    m = re.search(r'description:\s*"([^"]*?)"', content)
    if not m:
        very_weak += 1
        weak_files.append((f, '(no description)'))
        continue
    desc = m.group(1)
    
    title_m = re.search(r'title:\s*"([^"]*?)"', content)
    title = title_m.group(1) if title_m else ''
    
    # Very weak: description is basically just the title
    if desc.lower().strip() == title.lower().strip():
        very_weak += 1
        weak_files.append((f, desc[:60]))
        continue
    
    is_weak = False
    for pat in weak_patterns:
        if pat in desc.lower():
            is_weak = True
            break
    
    if len(desc) < 60:
        is_weak = True
    
    if is_weak:
        weak += 1
        weak_files.append((f, desc[:80]))
    else:
        good += 1
        good_files.append((f, desc[:80]))

print(f'Total recipes: {total}')
print(f'Very weak (title only/missing): {very_weak}')
print(f'Weak (generic/short): {weak}')
print(f'Already good: {good}')
print(f'Total needing update: {very_weak + weak}')
print()
print('Sample WEAK blurbs:')
for f, d in weak_files[:25]:
    print(f'  {f}: "{d}"')
if len(weak_files) > 25:
    print(f'  ... and {len(weak_files)-25} more')
print()
print('Sample GOOD blurbs:')
for f, d in good_files[:10]:
    print(f'  {f}: "{d}"')
