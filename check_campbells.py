import os, re

for f in sorted(os.listdir('content/recipes')):
    if f.startswith('campbells-') and f.endswith('.md'):
        with open(os.path.join('content/recipes', f), encoding='utf-8') as fh:
            content = fh.read()
        desc = re.search(r'^description:\s*"(.+?)"', content, re.MULTILINE)
        img = re.search(r'^image:\s*"(.+?)"', content, re.MULTILINE)
        print(f'{f}')
        print(f'  desc: {desc.group(1) if desc else "NONE"}')
        print(f'  img:  ...{img.group(1)[-50:] if img else "NONE"}')
        print()
