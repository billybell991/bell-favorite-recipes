import os, re
from collections import Counter

prefixes = ['Air Fryer', 'Instant Pot', 'Slow Cooker', 'Crock Pot', 'Crockpot',
    'One Pot', 'Sheet Pan', 'Quick and Easy', 'Quick & Easy', 'Quick',
    'Easy', 'Best', 'Classic', 'Simple', 'Homemade', 'Old Fashioned',
    'The Best', 'My Favorite', 'Copycat', 'Keto', 'Low Carb', 'Healthy']

def extract_term(title):
    term = title
    for p in sorted(prefixes, key=len, reverse=True):
        if term.lower().startswith(p.lower()):
            term = term[len(p):].strip(' -')
            break
    term = re.sub(r'\s*\(.*?\)\s*', ' ', term).strip()
    return term if len(term) > 2 else title

recipes = []
for f in sorted(os.listdir('content/recipes')):
    if not f.endswith('.md'):
        continue
    with open(os.path.join('content/recipes', f), 'r', encoding='utf-8') as fh:
        content = fh.read()
    if 'image: ""' not in content:
        continue
    m = re.search(r'^title:\s*"(.+)"', content, re.MULTILINE)
    if m:
        recipes.append((f, m.group(1)))

terms = [extract_term(t) for _, t in recipes]
unique_terms = sorted(set(terms))
print(f'Total recipes needing images: {len(recipes)}')
print(f'Unique search terms: {len(unique_terms)}')
print(f'\nSample terms:')
for t in unique_terms[:25]:
    count = terms.count(t)
    print(f'  [{count}] {t}')
print(f'  ...')
for t in unique_terms[-10:]:
    count = terms.count(t)
    print(f'  [{count}] {t}')
