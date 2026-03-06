"""
Add descriptions (blurbs) and images to new Mom's Cookbook recipes
that have empty description and image fields.
Reuses the keyword-to-photo-ID mapping from assign_all_images_v4.py
and generates short descriptive blurbs from recipe content.
"""
import os
import re
import random

# ── Pexels URL helpers ───────────────────────────────────────────────────────

def pexels_url(photo_id):
    return f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=600"

SPECIAL_URLS = {
    45202: "https://images.pexels.com/photos/45202/brownie-dessert-cake-sweet-45202.jpeg?auto=compress&cs=tinysrgb&w=600",
}

def get_url(photo_id):
    return SPECIAL_URLS.get(photo_id, pexels_url(photo_id))

# ── Title overrides for tricky names ─────────────────────────────────────────

TITLE_OVERRIDES = {
    "Dandy Dog Bone Biscuits":        1020585,
    "Jason's Doggie Biscuits":        1020585,
    "Homemade Soap – (from the Hazelwood Cookbook)": 1020585,
    "Eagle Brand Milk Substitute":    1640777,
    "To Whip Evaporated Milk":        1640777,
    "Crumb Coating":                  1640777,
    "Kote-n-roast":                   1640777,
    "Cornmeal and Herb Chicken Coating": 1640777,
    "Cajun Spice":                    1640777,
    "Mock Maple Syrup":               4725733,
    "Mom's Mock Maple Syrup – Aboriginal Cooking": 4725733,
    "Russian Tea":                    4725733,
    "Hot Chocolate Mix - Cw":         4725733,
    "Festive Punch":                  4725733,
    "Judy Lafreniere's Punch":        4725733,
    "Slu8h":                          4725733,
    "Choke Cherry Wine":              4725733,
    "Plain Dandelion Wine":           4725733,
    "Melody Dressing":                3070968,
    "Do-das":                         2377471,
    "Carnival Chip Dainties":         2377471,
    "Chipits Crunchies":              2377471,
    "Crispy Chews":                   2377471,
    "Knox Blox":                      2377471,
    "Frontier Kitchen Dolly Drops":   2377471,
    "Betty Lance's Award-winning Banic": 5419309,
    "Sonia's Absolutely Fabulous Dessert": 998237,
    '"Dirt" Pie':                     998237,
    "Ribbon Squares":                 2377471,
    "Top Hat Triple-layer Bars":      2377471,
    "Kellogg's Crispix Recipe #3":    2377471,
    "Charlie Brown Party Mix":        2377471,
    "Zesty Party Crunch":             2377471,
    "Wild Bluebarry Smoothies (community Voices)": 4725733,
}

# ── Food keyword pools (photo IDs from assign_all_images_v4.py) ──────────────

FOOD_POOLS = {
    # Specific combos
    "chicken pie":            [7625714, 32125954, 19145679],
    "chicken broccoli":       [6107757, 6107772, 9219086],
    "spinach quiche":         [7625714, 32125954, 19145679],
    "breakfast quiche":       [7625714, 32125954, 19145679],
    "bacon pie":              [7625714, 32125954, 19145679],
    "ham cheese pie":         [7625714, 32125954, 19145679],
    "lasagne pie":            [31779545, 4079522, 34692582],
    "coconut pie":            [6163269, 4018839, 998237],
    "apple pie":              [6163269, 6163268, 4018839, 5836525, 7790871, 6163273],
    "pumpkin pie":            [6163269, 4018839, 998237, 6072108],
    "sugar pie":              [6163269, 4018839, 998237],
    "butter tart":            [6163269, 4018839, 998237, 219293],
    "butterscotch pie":       [6163269, 4018839, 998237],
    "rhubarb pie":            [6163269, 4018839, 7790871],
    "pecan pie":              [6163269, 4018839, 998237],
    "berry pie":              [6163269, 4018839, 998237, 15030594],
    "strawberry pie":         [6163269, 998237, 15030594, 4040768],
    "cream pie":              [6163269, 4018839, 998237, 219293],
    "sour cream apple pie":   [6163269, 6163268, 4018839, 7790871],
    "chocolate fudge":        [45202, 12364904, 4306222, 1579926],
    "peanut butter ball":     [2377471, 2372537, 298485],
    "peanut butter chocolate":[2377471, 2372537, 298485, 45202],
    "peanut butter square":   [2377471, 2372537, 298485],
    "peanut butter cup":      [2377471, 2372537, 298485, 45202],
    "peanut butter treat":    [2377471, 2372537, 298485],
    "peanut butter marshmallow": [2377471, 2372537, 298485],
    "chocolate square":       [45202, 12364904, 4306222, 2377471],
    "rice krispie":           [2377471, 2372537, 298485, 4276480],
    "rice krispies":          [2377471, 2372537, 298485, 4276480],
    "marshmallow roll":       [2377471, 2372537, 298485],
    "date square":            [2377471, 2372537, 298485, 4276480],
    "lemon square":           [2377471, 2372537, 298485, 4276480],
    "almond bar":             [2377471, 2372537, 298485, 4276480],
    "toffee bar":             [2377471, 2372537, 298485],
    "chocolate bar":          [45202, 12364904, 2377471],
    "sweet marie bar":        [2377471, 2372537, 298485],
    "golden graham":          [2377471, 2372537, 298485],
    "bread pudding":          [4018839, 998237, 5836525],
    "rice pudding":           [998237, 219293, 4018839],
    "bread butter pickle":    [1640777, 1565982],
    "dill pickle":            [1640777, 1565982],
    "pickled beet":           [1640777, 1565982],
    "pickled bean":           [1640777, 1565982],
    "pickled egg":            [1640777, 1565982],
    "mustard bean":           [1640777, 1565982],
    "freezer pickle":         [1640777, 1565982],
    "cucumber relish":        [1640777, 1565982],
    "beet salad":             [3070968, 2821743, 1213710],
    "caesar salad":           [3070968, 2821743, 1213710, 257816],
    "broccoli salad":         [3070968, 2821743, 1213710, 257816],
    "spinach salad":          [3070968, 2821743, 1213710, 1152237],
    "greek salad":            [3070968, 2821743, 1213710, 257816],
    "noodle salad":           [3070968, 2821743, 1213710, 257816, 4506876],
    "bean salad":             [3070968, 2821743, 1213710],
    "fruit dip":              [1213710, 1152237, 3026019, 2894651],
    "potato soup":            [539451, 724667, 1703272, 30635687],
    "cabbage soup":           [539451, 724667, 1703272, 30635687],
    "barley soup":            [539451, 724667, 1703272, 30635687],
    "vegetable soup":         [724667, 1703272, 32795462, 3559899, 30635687],
    "hamburger soup":         [724667, 1703272, 30635687, 30335662],
    "blueberry soup":         [539451, 724667, 1703272],
    "moose stew":             [30635676, 29145751, 3981486, 4768958],
    "wild rice":              [1311771, 3926133, 8956718, 2942320],
    "fry bread":              [5419309, 2067626, 830894],
    "corn bread":             [5419309, 2067626, 830894],
    "pumpkin bread":          [5419309, 2067626, 830894, 6072108],
    "carrot casserole":       [32125954, 7625714, 19145679, 32862467],
    "potato casserole":       [32125954, 32862467, 7625714],
    "zucchini casserole":     [32125954, 7625714, 19145679],
    "tomato casserole":       [32125954, 7625714, 16845652],
    "rice casserole":         [32125954, 7625714, 343871],
    "scalloped potato":       [32862467, 32125954, 7625714, 539451],
    "french fries":           [30648979, 253580, 32862467],
    "stir fry":               [332784, 42168, 4020143],
    "chocolate mousse":       [45202, 12364904, 998237],
    "maple fondue":           [998237, 219293, 3071821],
    "rhubarb crisp":          [6163269, 6163268, 4018839, 7790871],
    "rhubarb dessert":        [6163269, 4018839, 7790871],
    "fruit pizza":            [1566837, 905847, 998237],
    "chocolate pizza":        [1566837, 45202, 12364904],
    "potato pizza":           [1566837, 905847, 32862467],
    "pizza sauce":            [1566837, 905847, 16845652],
    "popcorn ball":           [2377471, 298485],
    "salmon steak":           [31909815, 29748127, 3763847],
    "salmon relish":          [31909815, 29748127, 3763847],
    "tourtiere":              [7625714, 32125954, 19145679, 4198421],
    "cranberry chutney":      [6163269, 4018839],
    "barbecue sauce":         [332784, 42168, 23325845],
    "barbecue marinade":      [332784, 42168, 23325845],
    "cocktail sauce":         [688802, 3763847, 332784],
    "honey garlic":           [332784, 42168, 2338407],
    "lemon marinade":         [3763847, 332784, 6608694],
    "chili sauce":            [7111387, 15881322, 14866629],
    "pork cassoulet":         [332784, 42168, 36051529, 30635676],
    "venison steak":          [30635676, 29145751, 332784],
    "peach salsa":            [7111387, 14866629, 15881322],
    "ratatouille":            [724667, 1703272, 32795462],
    "corn bread":             [5419309, 2067626, 830894],
    "tea biscuit":            [5419309, 2067626, 830894, 4114116],
    "blueberry biscuit":      [5419309, 2067626, 830894, 90607],
    "oatmeal pancake":        [2516025, 5710793, 5677021, 11198924],
    "pudding cake":           [998237, 219293, 4018839],
    "molasses cookie":        [2377471, 2372537, 1020585, 298485],
    "sugared nut":            [2377471, 2372537, 298485],
    "swedish nut":            [2377471, 2372537, 298485],
    "brownie":                [45202, 12364904, 30353753, 5773862],

    # Single word fallbacks
    "bannock":    [5419309, 2067626, 830894, 4114116],
    "fudge":      [45202, 12364904, 4306222, 1579926],
    "tart":       [6163269, 4018839, 998237, 219293],
    "tarts":      [6163269, 4018839, 998237, 219293],
    "pie":        [6163269, 6163268, 4018839, 5836525, 7790871, 6163273],
    "quiche":     [7625714, 32125954, 19145679],
    "pickle":     [1640777, 1565982],
    "pickles":    [1640777, 1565982],
    "relish":     [1640777, 1565982],
    "ketchup":    [1640777, 1565982],
    "soup":       [539451, 724667, 955137, 30635687, 1703272, 3296680],
    "stew":       [30635676, 29145751, 3981486, 4768958],
    "chili":      [7111387, 15881322, 14866629, 10658147],
    "salad":      [3070968, 2821743, 257816, 4506876, 1213710],
    "coleslaw":   [3070968, 2821743, 257816, 4506876],
    "slaw":       [3070968, 2821743, 257816],
    "dressing":   [3070968, 2821743, 1213710],
    "vinaigrette": [3070968, 2821743, 1213710],
    "vinegar":    [1640777, 1565982],
    "dip":        [1213710, 1152237, 3026019, 2894651],
    "fondue":     [998237, 219293, 3071821],
    "sauce":      [332784, 42168, 14537709],
    "marinade":   [332784, 42168, 23325845],
    "pudding":    [998237, 219293, 4018839],
    "square":     [2377471, 2372537, 298485, 4276480],
    "squares":    [2377471, 2372537, 298485, 4276480],
    "bar":        [2377471, 2372537, 298485, 4276480],
    "bars":       [2377471, 2372537, 298485, 4276480],
    "cookie":     [2377471, 2372537, 1020585, 298485, 4276480, 4187558],
    "cookies":    [2377471, 2372537, 1020585, 298485, 4276480, 4187558],
    "cake":       [998237, 219293, 4018839, 5836525, 6148262],
    "bread":      [5419309, 2067626, 5419308, 4114145, 4114116, 830894],
    "biscuit":    [5419309, 2067626, 830894, 4114116],
    "biscuits":   [5419309, 2067626, 830894, 4114116],
    "muffin":     [3650437, 3650438, 90607, 2764271, 4051591],
    "muffins":    [3650437, 3650438, 90607, 2764271, 4051591],
    "scone":      [5419309, 2067626, 830894],
    "pancake":    [2516025, 5710793, 5677021, 11198924],
    "chicken":    [6107757, 6107772, 4589138, 34138804, 9219086, 145804],
    "beef":       [30635676, 29145751, 3981486, 332784, 42168],
    "pork":       [332784, 42168, 36051529, 10939223, 14537709],
    "ham":        [332784, 42168, 36051529, 14537709],
    "bacon":      [332784, 42168, 36051529],
    "salmon":     [31909815, 29748127, 3763847, 33674236],
    "fish":       [3763847, 29748127, 2374946, 6608694],
    "codfish":    [3763847, 29748127, 2374946],
    "moose":      [30635676, 29145751, 3981486],
    "venison":    [30635676, 29145751, 3981486],
    "pizza":      [1566837, 905847, 2918537, 30478775],
    "burger":     [332784, 42168, 36051529],
    "lasagna":    [31779545, 4079522, 34692582],
    "lasagne":    [31779545, 4079522, 34692582],
    "dumpling":   [539451, 724667, 1703272, 30335662],
    "dumplings":  [539451, 724667, 1703272, 30335662],
    "casserole":  [32125954, 7625714, 19145679, 32862467],
    "rice":       [343871, 3926133, 8956718, 1630495, 723198],
    "potato":     [32862467, 32125954, 7625714, 539451, 30648979],
    "potatoes":   [32862467, 32125954, 7625714, 539451, 30648979],
    "carrot":     [32862467, 32125954, 7625714],
    "carrots":    [32862467, 32125954, 7625714],
    "zucchini":   [32125954, 7625714, 19145679],
    "corn":       [7111387, 15881322, 32795462],
    "spinach":    [3070968, 2821743, 1213710, 1152237],
    "broccoli":   [5644943, 5639476, 1277483],
    "cabbage":    [7625714, 32125954, 32862467],
    "cauliflower":[5644943, 5639476, 32795462],
    "tomato":     [16845652, 3832330, 539451],
    "beet":       [3070968, 2821743, 1213710],
    "beets":      [3070968, 2821743, 1213710],
    "onion":      [32125954, 7625714, 332784],
    "vegetable":  [724667, 1703272, 32795462, 3070968],
    "chocolate":  [45202, 12364904, 4311548, 4306222, 1028714],
    "caramel":    [998237, 3071821, 219293],
    "butterscotch": [998237, 219293, 2377471],
    "lemon":      [998237, 219293, 3071821],
    "pumpkin":    [6072108, 1277483, 13788765],
    "apple":      [6163269, 6163268, 4018839, 7790871],
    "rhubarb":    [6163269, 4018839, 7790871],
    "blueberry":  [90607, 3650437, 35174214, 9009967],
    "cranberry":  [6163269, 4018839],
    "raspberry":  [998237, 15030594, 4040768],
    "strawberry": [998237, 15030594, 4040768, 3323686],
    "peach":      [6163269, 4018839, 7790871],
    "coconut":    [2377471, 2372537, 298485],
    "peanut":     [2377471, 2372537, 298485],
    "almond":     [2377471, 2372537, 298485],
    "maple":      [998237, 219293, 4725733],
    "cream":      [998237, 219293, 3071821],
    "cheese":     [5107161, 5107162, 32125954, 7625714],
    "butter":     [5419309, 2067626, 830894],
    "toffee":     [2377471, 2372537, 298485],
    "candy":      [2377471, 2372537, 298485, 45202],
    "popcorn":    [2377471, 298485],
    "smoothie":   [90894, 4725733, 4736807],
    "punch":      [4725733, 90894],
    "wine":       [4725733, 90894],
    "artichoke":  [724667, 1703272, 32795462],
    "dessert":    [998237, 219293, 3071821, 4018839],
    "crisp":      [6163269, 4018839, 7790871],
    "fries":      [30648979, 253580, 32862467],
    "roast":      [332784, 42168, 36051529, 30635676],
    "meat":       [332784, 42168, 36051529, 14537709],
    "dinner":     [32125954, 7625714, 19145679, 32862467],
    "stuffing":   [7625714, 32125954, 332784],
}

# Subcategory-based fallback pools
SUBCAT_POOLS = {
    "Miscellaneous": [1640777, 1565982, 376464, 958545],
    "Native Cuisine": [5419309, 2067626, 830894, 30635676],
    "Pickles":        [1640777, 1565982, 376464],
    "Pies":           [6163269, 6163268, 4018839, 5836525, 7790871],
    "Puddings":       [998237, 219293, 4018839, 5836525],
    "Salads and Dressings": [3070968, 2821743, 257816, 4506876, 1213710],
    "Sauces":         [332784, 42168, 14537709, 1640777],
    "Snacks":         [2377471, 2372537, 298485, 4276480, 1020585],
    "Soups":          [539451, 724667, 955137, 30635687, 1703272],
    "Squares":        [2377471, 2372537, 298485, 4276480, 4187558],
    "Vegetables":     [32862467, 32125954, 7625714, 724667, 32795462],
}

# Generic fallback
GENERIC_FOOD = [1640777, 1565982, 376464, 958545, 1099680, 461198, 1279330, 842571]


def _pick_from_pool(pool, used_photos):
    pool_with_counts = [(pid, used_photos.get(pid, 0)) for pid in pool]
    random.shuffle(pool_with_counts)
    pool_with_counts.sort(key=lambda x: x[1])
    chosen = pool_with_counts[0][0]
    used_photos[chosen] = used_photos.get(chosen, 0) + 1
    return get_url(chosen)


def get_best_photo(title, subcategory, used_photos):
    # Check title overrides
    if title in TITLE_OVERRIDES:
        pid = TITLE_OVERRIDES[title]
        if pid is None:
            return None
        used_photos[pid] = used_photos.get(pid, 0) + 1
        return get_url(pid)

    search_text = title.lower()

    # Try food keywords (longest first for most specific match)
    sorted_keys = sorted(FOOD_POOLS.keys(), key=len, reverse=True)
    for keyword in sorted_keys:
        if keyword in search_text:
            return _pick_from_pool(FOOD_POOLS[keyword], used_photos)

    # Subcategory fallback
    if subcategory in SUBCAT_POOLS:
        return _pick_from_pool(SUBCAT_POOLS[subcategory], used_photos)

    # Generic fallback
    return _pick_from_pool(GENERIC_FOOD, used_photos)


# ── Blurb generation ─────────────────────────────────────────────────────────

def clean_title_for_blurb(title):
    """Remove parenthetical credits and source notes from title."""
    # Remove – (credit) or - (credit) parts (with or without closing paren)
    clean = re.sub(r'\s*[–—-]\s*\(.*$', '', title)
    # Remove (credit) parts (with or without closing paren)
    clean = re.sub(r'\s*\([^)]*(?:cookbook|cooking|metis|gail|aboriginal|nugget|kraft|community|creation|cowboy|hazelwood|good times|bill|heather|colette|carmen|barb|claire|louise|cw|purity|merit|serves|made with).*$', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\s*\(.*?\)\s*$', '', clean)
    # Remove trailing "– Credit Name" or "- Credit"
    clean = re.sub(r'\s*[–—-]\s*(?:Aboriginal|Metis|Gail|Nugget|Kraft|No\.\s*\d|Makes\s*\d|Using\s|Elsie|from\s).*$', '', clean, flags=re.IGNORECASE)
    # Remove trailing punctuation
    clean = clean.strip().rstrip('–—-_ ')
    # Remove "- Cw", "- Cw" etc
    clean = re.sub(r'\s*-\s*Cw\s*$', '', clean, flags=re.IGNORECASE)
    # Remove " for X" endings
    clean = re.sub(r'\s+for\s+(?:One|Two|1|\d+\s*Scone)\s*$', '', clean, flags=re.IGNORECASE)
    # Clean up leading/trailing quotes
    clean = clean.strip('\x22 ')
    return clean.strip()


def extract_descriptors(body):
    """Find cooking/appearance descriptors from instructions."""
    descriptors = []
    patterns = [
        (r'crisp[y]?', 'crispy'),
        (r'golden\s*brown', 'golden brown'),
        (r'golden', 'golden'),
        (r'tender', 'tender'),
        (r'creamy', 'creamy'),
        (r'flaky', 'flaky'),
        (r'juicy', 'juicy'),
        (r'fluffy', 'fluffy'),
        (r'crunchy', 'crunchy'),
        (r'caramelized', 'caramelized'),
        (r'glazed', 'glazed'),
        (r'savour[y]?', 'savoury'),
        (r'hearty', 'hearty'),
        (r'rich', 'rich'),
        (r'smooth', 'smooth'),
        (r'silky', 'silky'),
        (r'zesty', 'zesty'),
        (r'tangy', 'tangy'),
        (r'spicy', 'spicy'),
        (r'warm', 'warm'),
        (r'chilled', 'chilled'),
        (r'refreshing', 'refreshing'),
    ]
    text = body.lower()
    for pat, word in patterns:
        if re.search(pat, text) and word not in descriptors:
            descriptors.append(word)
    return descriptors[:2]


def detect_cooking_method(title, body):
    """Detect the primary cooking method from title and instructions."""
    text = (title + " " + body).lower()
    methods = [
        (r'\bbake[ds]?\b', 'baked'),
        (r'\broast(?:ed)?\b', 'roasted'),
        (r'\bfr(?:y|ied)\b', 'fried'),
        (r'\bsimmer(?:ed)?\b', 'simmered'),
        (r'\bboil(?:ed)?\b', 'cooked'),
        (r'\bmicrowave', 'microwaved'),
        (r'\bsaut[ée]', 'sautéed'),
        (r'\bgrill(?:ed)?\b', 'grilled'),
        (r'\bsteam(?:ed)?\b', 'steamed'),
        (r'\bstir.fry', 'stir-fried'),
        (r'\bslow.cook', 'slow-cooked'),
        (r'\bblend(?:ed)?\b', 'blended'),
        (r'\bchill(?:ed)?\b', 'chilled'),
        (r'\bfreez', 'frozen'),
        (r'\bno.bake', 'no-bake'),
        (r'\bmix(?:ed)?\b', 'mixed'),
    ]
    for pat, method in methods:
        if re.search(pat, text):
            return method
    return None


# Subcategory-specific endings
SUBCAT_ENDINGS = {
    "Pies":               "with a perfectly flaky crust",
    "Puddings":           "rich and comforting",
    "Salads and Dressings": "fresh and vibrant",
    "Sauces":             "perfect for any dish",
    "Snacks":             "perfect for any occasion",
    "Soups":              "warm and satisfying",
    "Squares":            "easy to make and impossible to resist",
    "Vegetables":         "a delicious side dish",
    "Pickles":            "a classic homemade preserve",
    "Native Cuisine":     "a treasured traditional recipe",
    "Miscellaneous":      "a family favorite",
}


def generate_blurb(title, body, subcategory):
    """Generate a short, appealing description for the recipe."""
    clean = clean_title_for_blurb(title)

    descriptors = extract_descriptors(body)
    method = detect_cooking_method(title, body)

    parts = []

    # Add up to 2 descriptors
    if descriptors:
        parts.append(", ".join(descriptors).capitalize())
        parts.append(clean)
    else:
        parts.append(clean)

    # Add cooking method or subcategory ending
    # Avoid awkward methods
    good_methods = ('baked', 'roasted', 'fried', 'simmered', 'grilled',
                    'sautéed', 'steamed', 'stir-fried', 'slow-cooked', 'chilled')
    if method and method in good_methods:
        parts.append(f"{method} to perfection")
    elif subcategory in SUBCAT_ENDINGS:
        parts.append(SUBCAT_ENDINGS[subcategory])
    else:
        parts.append("a delicious homemade treat")

    blurb = ", ".join(parts)

    # Capitalize first letter
    blurb = blurb[0].upper() + blurb[1:]

    # Clamp length
    if len(blurb) > 120:
        blurb = blurb[:117].rsplit(",", 1)[0]

    return blurb


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    import sys
    force = "--force" in sys.argv

    recipes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "recipes")

    # Target: only recipes in new subcategories
    new_subcats = {'Miscellaneous','Native Cuisine','Pickles','Pies','Puddings',
                   'Salads and Dressings','Sauces','Snacks','Soups','Squares','Vegetables'}

    files = sorted(f for f in os.listdir(recipes_dir) if f.endswith('.md') and f != '_index.md')

    used_photos = {}
    updated = 0
    skipped = 0
    generic = 0

    for filename in files:
        filepath = os.path.join(recipes_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse frontmatter
        parts = content.split('---', 2)
        if len(parts) < 3:
            continue

        fm = parts[1]
        body = parts[2]

        # Check subcategory
        sc_match = re.search(r'subcategory:\s*"([^"]*)"', fm)
        if not sc_match or sc_match.group(1) not in new_subcats:
            continue

        subcategory = sc_match.group(1)

        # Check if already has description and image (skip unless --force)
        desc_match = re.search(r'description:\s*"([^"]*)"', fm)
        img_match = re.search(r'image:\s*"([^"]*)"', fm)
        has_desc = bool(desc_match and desc_match.group(1).strip())
        has_img = bool(img_match and img_match.group(1).strip())

        if has_desc and has_img and not force:
            skipped += 1
            continue

        # Get title
        title_match = re.search(r'title:\s*"([^"]*)"', fm)
        if not title_match:
            continue
        title = title_match.group(1)

        new_content = content

        # Generate and set blurb
        if not has_desc or force:
            blurb = generate_blurb(title, body, subcategory)
            # Escape any double quotes in blurb
            blurb = blurb.replace('"', '\\"')
            new_content = re.sub(
                r'description:\s*"[^"]*"',
                f'description: "{blurb}"',
                new_content,
                count=1
            )

        # Assign image
        if not has_img or force:
            image_url = get_best_photo(title, subcategory, used_photos)
            if image_url:
                new_content = re.sub(
                    r'image:\s*"[^"]*"',
                    f'image: "{image_url}"',
                    new_content,
                    count=1
                )
                # Check if generic
                if any(str(gid) in image_url for gid in GENERIC_FOOD):
                    generic += 1
                    print(f"  GENERIC: {title}")

        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            updated += 1
            print(f"  OK: {title}")
        else:
            skipped += 1

    print(f"\n=== DONE ===")
    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")
    print(f"Generic photos: {generic}")
    print(f"Unique photos used: {len(used_photos)}")


if __name__ == "__main__":
    main()
