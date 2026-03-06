import os, re

recipe_dir = r'c:\Stuff\Bell_Recipes_Project\content\recipes'
samples = [
    'charlie-brown-party-mix.md', 'apple-crisp.md', 'air-fryer-chicken-thighs.md',
    'french-onion-soup.md', 'banana-bread.md', 'antipasto-roll-ups.md',
    'shipwreck.md', 'nougat-candy-tracey.md', 'amazingly-easy-apple-crisp.md',
    'almond-bars.md', 'lemon-coffee-cake-peps-grandma.md',
    'classic-pickled-eggs-colettes.md', 'aloha-sweet-sour-pork.md',
    '5-ingredient-mac-n-cheese.md', 'french-toast-bake-tracey.md',
    'air-fryer-panko-chicken-thighs.md', 'apple-pie.md',
]

# Adjectives/adverbs/filler to strip - keep only food nouns
REMOVE_WORDS = {
    # Adjectives
    'amazing', 'amazingly', 'beautiful', 'best', 'big', 'bright', 'buttery',
    'chewy', 'classic', 'comforting', 'creamy', 'crispy', 'crunchy', 'crusty',
    'decadent', 'delicious', 'dense', 'easy', 'famous', 'flaky', 'fluffy',
    'fresh', 'freshly', 'genius', 'golden', 'golden-topped', 'gorgeous',
    'great', 'hearty', 'heavenly', 'homemade', 'hot', 'incredible',
    'indulgent', 'irresistible', 'juicy', 'luscious', 'luxurious',
    'moist', 'old-fashioned', 'perfect', 'perfectly', 'pillowy', 'pure',
    'quick', 'rich', 'rustic', 'silky', 'simple', 'smooth', 'soft',
    'soul-warming', 'special', 'steaming', 'stunning', 'succulent', 'sweet',
    'tangy', 'tender', 'thick', 'ultimate', 'unbelievably', 'velvety',
    'warm', 'wholesome', 'wonderful',
    'addictive', 'satisfying', 'show-stopping', 'crowd-pleasing',
    # Filler/narrative words
    'kind', 'one', 'everyone', 'never', 'ever', 'way', 'thing', 'things',
    'life', 'first', 'last', 'long', 'full', 'right', 'like',
    'good', 'makes', 'make', 'made', 'come', 'comes', 'feels',
    'feel', 'stays', 'stay', 'turns', 'turn', 'hits', 'hit',
    'enough', 'simply', 'truly', 'really', 'exactly',
    'always', 'absolutely', 'totally', 'completely',
    'recipe', 'recipes', 'kitchen', 'house', 'home', 'room', 'table',
    'counter', 'oven', 'pan', 'pot', 'bowl', 'plate', 'platter',
    'batch', 'double', 'second', 'seconds', 'morning', 'evening',
    'day', 'tuesday', 'holiday', 'celebration', 'occasion', 'party',
    'bake', 'sale', 'bakery', 'store', 'bought',
    'proof', 'someone', 'something', 'anything', 'everything',
    'wonder', 'effort', 'satisfaction', 'comfort', 'treat',
    'ask', 'asked', 'share', 'shared', 'reach', 'reaches', 'request',
    'disappears', 'disappear', 'vanish', 'unattended', 'impossible',
    'dangerous', 'dangerously', 'outrageously',
    'once', 'start', 'stop', 'stopping', 'munching', 'nights', 'movie',
    'parties', 'smear', 'cup', 'coffee', 'lazy', 'better', 'straight',
    'dream', 'alongside', 'meal', 'slathered', 'inside', 'outside',
    'pull', 'apart', 'wonder', 'aroma', 'smell', 'fills', 'incredible',
    'bite', 'forkful', 'spoonful', 'spoon', 'slice', 'piece',
    'jar', 'eyes', 'close', 'mid-bite', 'name', 'gorgeous',
    'tastes', 'taste', 'needed', 'took', 'actually',
    'knew', 'doing', 'bright', 'citrusy', 'showstopper',
    'goodness', 'scratch', 'real', 'ingredients', 'whole',
    'no-bake', 'looks', 'looked', 'looking', 'large', 'medium', 'small',
    'sized', 'flavorful', 'food', 'line', 'sheet', 'foil', 'grease',
    'topped', 'topping', 'put', 'top', 'melted', 'folded', 'around',
    'baked', 'cooked', 'served', 'tossed', 'mixed', 'rubbed',
    'seasoned', 'prepared', 'finished', 'stuffed',
    'tsp', 'tbsp', 'tspcinnamon', 'cup', 'cups',
    # People/names and narrative
    'tracey', 'colette', 'pep', 'grandma', 'mom', 'ann', 'yan',
    'career', 'girl', 'husband', 'poor', 'man',
    'gets', 'got', 'came', 'went', 'dog-eared', 'cookbook',
    'melt-in-your-mouth', 'golden-brown',
    'pkg', 'package',
    'passed', 'down', 'generations', 'shatters', 'crumble', 'crumbles',
    'store-bought', 'make-ahead', 'triple-coated', 'steeped',
    'slices', 'lean', 'boneless',
    # Common English
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
    'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
    'would', 'could', 'should', 'may', 'might', 'can', 'shall',
    'that', 'this', 'these', 'those', 'it', 'its', 'they', 'them',
    'their', 'we', 'our', 'you', 'your', 'he', 'she', 'his', 'her',
    'who', 'which', 'what', 'where', 'when', 'how', 'why',
    'not', 'no', 'nor', 'so', 'if', 'than', 'too', 'very',
    'just', 'about', 'above', 'after', 'again', 'all', 'also', 'any',
    'because', 'before', 'between', 'both', 'each', 'even', 'every',
    'into', 'more', 'most', 'much', 'only', 'other', 'out', 'over',
    'own', 'same', 'some', 'still', 'such', 'then', 'there', 'through',
    'under', 'until', 'up', 'upon', 'while',
}

FOOD_WORDS = {
    'pie', 'ham', 'jam', 'dip', 'rib', 'rub', 'tea', 'egg', 'cod', 'rum',
    'rye', 'fig', 'nut', 'oat', 'yam',
}

# Extra words to remove only from description (not from title)
DESC_ONLY_REMOVE = {
    'charlie', 'brown', 'instant', 'mix',
}

def build_query(title, description):
    if not description:
        return re.sub(r'\(.*?\)', '', title).strip()

    # Strategy: use title as base, enrich with food nouns from description
    clean_title = re.sub(r'\(.*?\)', '', title)
    clean_title = re.sub(r"'s\b", "", clean_title).strip()

    text = description
    text = re.sub(r'[^a-zA-Z\s-]', ' ', text)
    words = text.lower().split()
    kept = []
    seen = set()
    # Add title words first (most important signal)
    for w in clean_title.lower().split():
        w = w.strip('-')
        if w and w not in REMOVE_WORDS and w not in seen:
            kept.append(w)
            seen.add(w)
    # Then add food nouns from description (with extra filtering)
    for w in words:
        w = w.strip('-')
        if not w or (len(w) < 3 and w not in FOOD_WORDS):
            continue
        if w in REMOVE_WORDS or w in DESC_ONLY_REMOVE:
            continue
        if w not in seen:
            kept.append(w)
            seen.add(w)
    # Keep 4-6 words max for best Pexels results
    query = ' '.join(kept[:6])
    return query

for s in samples:
    path = os.path.join(recipe_dir, s)
    if not os.path.exists(path):
        continue
    content = open(path, 'r', encoding='utf-8').read()
    m = re.search(r'description:\s*"((?:[^"\\]|\\.)*)"', content)
    t = re.search(r'title:\s*"([^"]*)"', content)
    if m and t:
        query = build_query(t.group(1), m.group(1))
        print(f'{t.group(1)}')
        print(f'  DESC: {m.group(1)[:120]}')
        print(f'  QUERY: {query}')
        print()
