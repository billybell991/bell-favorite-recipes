import os, re

recipes = ['cook-up-rice', '5-ingredient-mac-n-cheese', '7-layer-dinner', 
           '90-second-keto-bread-in-a-mug', 'air-fryer-chicken-thighs', 
           'air-fryer-mashed-potato-balls']

for slug in recipes:
    for f in os.listdir('content/recipes'):
        if f.startswith(slug):
            with open(os.path.join('content/recipes', f), encoding='utf-8') as fh:
                content = fh.read()
            title = re.search(r'title:\s*"(.+?)"', content).group(1)
            img = re.search(r'image:\s*".*?photos/(\d+)/.*?"', content)
            pid = img.group(1) if img else 'NONE'
            print(f'{title} => photo ID {pid}')
