import os, re

d = os.path.join(os.path.dirname(__file__), "content", "recipes")
subcats = {}
for f in sorted(os.listdir(d)):
    if not f.endswith('.md') or f == '_index.md':
        continue
    c = open(os.path.join(d, f), encoding='utf-8').read()
    m = re.search(r'subcategory: "([^"]+)"', c)
    t = re.search(r'title: "([^"]+)"', c)
    img = re.search(r'image: "([^"]+)"', c)
    desc = re.search(r'description: "([^"]+)"', c)
    if m and t:
        sc = m.group(1)
        has_img = bool(img and img.group(1))
        has_desc = bool(desc and desc.group(1))
        if sc not in subcats:
            subcats[sc] = []
        subcats[sc].append((t.group(1), has_img, has_desc))

new_scs = ['Miscellaneous','Native Cuisine','Pickles','Pies','Puddings',
           'Salads and Dressings','Sauces','Snacks','Soups','Squares','Vegetables']
for sc in new_scs:
    items = subcats.get(sc, [])
    print(f'\n=== {sc} ({len(items)}) ===')
    for title, hi, hd in items[:5]:
        print(f'  {title}  img={hi}  desc={hd}')
    if len(items) > 5:
        print(f'  ... and {len(items)-5} more')
