import os, re

recipe_dir = r'c:\Stuff\Bell_Recipes_Project\content\recipes'
weak = 0
total = 0
for f in os.listdir(recipe_dir):
    if not f.endswith('.md') or f.startswith('_'):
        continue
    total += 1
    path = os.path.join(recipe_dir, f)
    content = open(path, 'r', encoding='utf-8').read()
    m = re.search(r'^description:\s*["\'](.+?)["\']', content, re.MULTILINE)
    if m:
        blurb = m.group(1)
        if blurb.startswith('A delicious recipe for') or blurb.startswith('Learn how to make') or len(blurb) < 40:
            weak += 1
    else:
        weak += 1

print(f'Total recipes: {total}')
print(f'Weak/missing blurbs: {weak}')
print(f'Good blurbs: {total - weak}')

# Show the weak ones
for f in os.listdir(recipe_dir):
    if not f.endswith('.md') or f.startswith('_'):
        continue
    path = os.path.join(recipe_dir, f)
    content = open(path, 'r', encoding='utf-8').read()
    m = re.search(r'^description:\s*["\'](.+?)["\']', content, re.MULTILINE)
    if m:
        desc = m.group(1)
        if desc.startswith('A delicious recipe for') or desc.startswith('Learn how to make') or len(desc) < 40:
            print(f'  WEAK: {f}  ->  "{desc[:80]}"')
    else:
        print(f'  MISSING: {f}')
