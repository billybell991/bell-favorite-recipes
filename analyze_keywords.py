"""Analyze recipe titles to find the most common food keywords for image searching."""
import os, re
from collections import Counter

CONTENT_DIR = 'content/recipes'

# Common food-related keywords to look for
FOOD_WORDS = set([
    'chicken', 'beef', 'pork', 'turkey', 'fish', 'salmon', 'shrimp', 'tuna',
    'steak', 'meatloaf', 'meatball', 'sausage', 'bacon', 'ham',
    'soup', 'stew', 'chili', 'chowder',
    'pasta', 'spaghetti', 'lasagna', 'macaroni', 'ziti', 'noodle',
    'salad', 'slaw', 'coleslaw',
    'cake', 'cookies', 'cookie', 'brownie', 'brownies', 'pie', 'tart',
    'bread', 'muffin', 'muffins', 'biscuit', 'biscuits', 'roll', 'rolls',
    'rice', 'risotto', 'quinoa',
    'potato', 'potatoes', 'fries',
    'casserole',
    'dip', 'sauce', 'gravy', 'salsa',
    'pancake', 'pancakes', 'waffle', 'waffles', 'french toast',
    'oatmeal', 'granola',
    'pizza', 'burger', 'sandwich', 'wrap', 'taco', 'tacos', 'burrito',
    'enchilada', 'enchiladas', 'quesadilla',
    'bean', 'beans', 'lentil', 'lentils',
    'corn', 'broccoli', 'cauliflower', 'zucchini', 'squash', 'mushroom',
    'apple', 'banana', 'blueberry', 'strawberry', 'lemon', 'orange', 'peach',
    'chocolate', 'vanilla', 'caramel', 'cinnamon',
    'cheese', 'cream', 'butter', 'egg', 'eggs',
    'wing', 'wings', 'thigh', 'thighs', 'breast', 'drumstick',
    'ribs', 'roast', 'chop', 'chops', 'cutlet',
    'fry', 'fried', 'grilled', 'baked', 'roasted', 'bbq', 'barbecue',
    'crispy', 'creamy', 'cheesy', 'spicy',
    'pudding', 'custard', 'mousse', 'fudge',
    'cobbler', 'crumble', 'crisp',
    'quiche', 'frittata', 'omelet', 'omelette',
])

recipes = []
for fname in sorted(os.listdir(CONTENT_DIR)):
    if not fname.endswith('.md'):
        continue
    fpath = os.path.join(CONTENT_DIR, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'image: ""' not in content:
        continue
    m = re.search(r'^title:\s*"(.+)"', content, re.MULTILINE)
    if m:
        recipes.append((fname, m.group(1)))

# Count keyword occurrences
keyword_counts = Counter()
recipe_keywords = {}  # fname -> list of matched keywords

for fname, title in recipes:
    words = re.findall(r'[a-z]+', title.lower())
    # Also check bigrams
    bigrams = [f'{words[i]} {words[i+1]}' for i in range(len(words)-1)]
    matched = []
    for w in words:
        if w in FOOD_WORDS:
            matched.append(w)
            keyword_counts[w] += 1
    recipe_keywords[fname] = matched

# Find recipes with NO keyword matches
unmatched = [(f, t) for f, t in recipes if not recipe_keywords[f]]

print(f'Total recipes: {len(recipes)}')
print(f'Recipes with keyword match: {len(recipes) - len(unmatched)}')
print(f'Recipes with NO keyword match: {len(unmatched)}')

print(f'\nTop 40 keywords:')
for word, count in keyword_counts.most_common(40):
    print(f'  {word}: {count}')

print(f'\nUnmatched recipes (will need custom search):')
for f, t in unmatched[:50]:
    print(f'  {t}')
if len(unmatched) > 50:
    print(f'  ... and {len(unmatched) - 50} more')
