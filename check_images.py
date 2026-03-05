import os, re

recipes_dir = r'C:\Stuff\Bell_Recipes_Project\content\recipes'
total = 0
has_image = 0
has_default = 0
no_image = 0

for f in sorted(os.listdir(recipes_dir)):
    if f.endswith('.md') and f != '_index.md':
        total += 1
        with open(os.path.join(recipes_dir, f), encoding='utf-8') as fh:
            content = fh.read()
        m = re.search(r'^image:\s*(.+)$', content, re.MULTILINE)
        if m:
            val = m.group(1).strip().strip('"')
            if 'default-recipe' in val or not val:
                has_default += 1
            else:
                has_image += 1
        else:
            no_image += 1

print(f'Total: {total}')
print(f'Custom image: {has_image}')
print(f'Default image: {has_default}')
print(f'No image field: {no_image}')
