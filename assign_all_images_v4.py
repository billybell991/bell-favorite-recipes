"""
Image assignment script v4.
KEY CHANGES from v3:
- All chicken pools use VERIFIED photo IDs (thigh≠breast≠wing≠drumstick)
- Added panko/breaded chicken entries
- Added ultra-specific compound entries (e.g. "air fryer panko chicken thigh")
- Added ribs pool with verified BBQ rib photos
- Added TITLE_OVERRIDES for recipes that can't be matched by keywords
- Non-food recipes (clay, playdough) get craft/generic photos
"""
import os
import re
import random

def pexels_url(photo_id):
    return f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=600"

SPECIAL_URLS = {
    45202: "https://images.pexels.com/photos/45202/brownie-dessert-cake-sweet-45202.jpeg?auto=compress&cs=tinysrgb&w=600",
}

def get_url(photo_id):
    return SPECIAL_URLS.get(photo_id, pexels_url(photo_id))


# ──────────────────────────────────────────────────────────
# TITLE OVERRIDES - checked first, before any keyword matching.
# Maps exact recipe titles to specific verified photo IDs.
# Used for recipes with obscure names or special cases.
# ──────────────────────────────────────────────────────────
TITLE_OVERRIDES = {
    # Non-food / craft recipes
    "Baker's Clay Instructions":     1020585,   # generic baking supplies / flour
    "Ornament Clay Dough":           1020585,
    "Playdough":                     1020585,
    "Frontier Kitchen Chemical Garden": 1020585,
    "Helpful Hints for Healthy Cooking": 1640777, # generic food spread

    # Recipes with person names as titles (no food description)
    "All Recipes":                   None,       # skip this index page

    # Obscure names that won't keyword-match well
    "Bannock (Yan's)":               5419309,    # bread/flatbread
    "Maritime Madness":              32125954,   # casserole
    "Husband's Delight":             32125954,   # casserole
    "Career Girl's Supper":          332784,     # meat dish
    "Poor Man's Steak":              332784,     # steak
    "Lazy Man's Casserole":          32125954,   # casserole
    "Grand-Peres":                   998237,     # dessert dumplings
    "SINamon Buns":                  5419309,    # cinnamon buns
    "Oile Bolen (Dutch Donut)":      3650437,    # donut/fried dough
    "Kapusta":                       32125954,   # cabbage casserole
    "Shipwreck":                     32125954,   # casserole
    "Sucre a creme":                 998237,     # sugar cream dessert
    "Yuck-a-Flux (The Party Drink)": 4725733,    # drink
    "Roasted Bull Elephant":         332784,     # joke recipe, use meat
    "Chaffle (Cheese Waffle)":       5710793,    # waffle
    "Cora's Bran Muffins":           3650437,    # muffins
    "Christmas Crack":               2377471,    # candy/toffee
    "Nougat Candy (Tracey)":         2377471,    # candy
}


# ──────────────────────────────────────────────────────────
# FOOD KEYWORDS - matched with highest priority
# Sorted by length at runtime (longest/most-specific first)
#
# VERIFIED photo IDs are marked. IDs from Pexels descriptions
# have been cross-checked to ensure they show the correct food.
# ──────────────────────────────────────────────────────────
FOOD_POOLS = {
    # ─── ULTRA-SPECIFIC: method + food combos (matched first due to length) ───
    "air fryer panko chicken thigh":  [33143862, 4078178, 29653208, 5652265],   # VERIFIED: breaded/katsu chicken
    "air fryer panko chicken breast": [33143862, 4078178, 29653208, 5652265],
    "air fryer panko chicken":        [33143862, 4078178, 29653208, 5652265],
    "air fryer chicken thigh":        [4589138, 8392454, 24902945],             # VERIFIED: actual chicken thighs
    "air fryer chicken breast":       [6107757, 6107772, 6107768, 9219086],     # VERIFIED: actual chicken breasts
    "air fryer chicken wing":         [2338407, 8862753, 8862763, 7788311],     # VERIFIED: actual wings
    "air fryer chicken drumstick":    [145804, 5652264, 10303257, 34305982],    # VERIFIED: actual drumsticks

    # ─── COOKIES (compound phrases) ───
    "chocolate chip cookie":  [2377471, 33756110, 8081574, 2372537, 14133100, 1020585, 5379480, 4276480, 4187558, 1325467, 298485],
    "chocolate chip banana muffin": [3650437, 4792403, 4051559, 3650438],
    "peanut butter cookie":   [2377471, 2372537, 1020585, 298485, 4276480],
    "oatmeal raisin cookie":  [2377471, 2372537, 1020585, 298485, 4276480],
    "oatmeal cookie":         [2377471, 2372537, 1020585, 298485, 4276480, 4187558],
    "sugar cookie":           [2377471, 2372537, 1020585, 298485, 4276480, 4187558, 14133100],
    "shortbread cookie":      [2377471, 2372537, 298485, 1020585, 4276480],
    "gingerbread cookie":     [2377471, 2372537, 298485, 1020585],
    "butterscotch cookie":    [2377471, 2372537, 298485],

    # ─── MAC & CHEESE ───
    "mac and cheese":         [5107161, 5107162, 5107163, 9397238, 32083398, 10993148, 25524074, 5060461],
    "mac 'n' cheese":         [5107161, 5107162, 5107163, 9397238, 32083398, 10993148, 25524074],
    "macaroni and cheese":    [5107161, 5107162, 5107163, 9397238, 32083398, 10993148],
    "macaroni cheese":        [5107161, 5107162, 5107163, 9397238, 32083398],
    "mac n cheese":           [5107161, 5107162, 5107163, 9397238, 32083398],

    # ─── CHICKEN (ALL VERIFIED from Pexels search descriptions) ───
    "panko chicken thigh":    [33143862, 4078178, 29653208, 5652265],           # VERIFIED: breaded/katsu chicken
    "panko chicken breast":   [33143862, 4078178, 29653208, 5652265],
    "panko chicken":          [33143862, 4078178, 29653208, 5652265],
    "breaded chicken":        [33143862, 4078178, 29653208, 5652265],

    "chicken thigh":          [4589138, 8392454, 24902945],                     # VERIFIED: roasted thighs w/potatoes, seasoned thighs tray, fried thighs pan
    "chicken breast":         [6107757, 6107772, 6107768, 9219086, 34138804, 6107765],  # VERIFIED: sliced breast, whole breasts, grilled breasts
    "chicken wing":           [2338407, 8862753, 8862763, 7788311],             # VERIFIED: roasted wings, BBQ wings, wings plate, sesame wings
    "chicken wings":          [2338407, 8862753, 8862763, 7788311],
    "chicken drumstick":      [145804, 5652264, 10303257, 34305982, 33406],     # VERIFIED: roasted drumsticks, fried, glazed, grilled, plated
    "chicken parmesan":       [6107757, 6107772, 9219086],                      # chicken breast photos (parmesan is breaded breast)
    "chicken broccoli":       [6107757, 6107772, 9219086],
    "chicken dumpling":       [539451, 724667, 1703272, 12077982],
    "chicken pot pie":        [7625714, 32125954, 19145679],
    "chicken soup":           [539451, 724667, 1703272, 12077982, 30635687],
    "chicken salad":          [3070968, 2821743, 1213710, 257816, 4506876],
    "buffalo chicken":        [2338407, 8862753, 8862763, 7788311],             # buffalo = wings style
    "fried chicken":          [60616, 5652260, 13823475, 3926125],              # VERIFIED: crispy fried chicken pieces
    "baked chicken":          [4589138, 8392454, 24902945],                     # use thigh photos (baked chicken often = thighs)
    "grilled chicken":        [34138804, 6107765, 6107757, 6107772],            # VERIFIED: grilled breast photos
    "bbq chicken":            [2338407, 8862753, 8862763, 7788311],             # BBQ chicken = often wings
    "honey garlic chicken":   [2338407, 8862753, 7788311, 145804],              # honey garlic = wings or drumsticks
    "chicken fried rice":     [343871, 723198, 1630495],
    "chicken pad thai":       [31779545, 4079522, 30343602],                    # pasta/noodle photos
    "chicken bacon":          [6107757, 6107772, 9219086],                      # chicken breast
    "chicken tetrazzini":     [31779545, 4079522, 30343602],                    # pasta dish
    "chicken taquito":        [7111387, 14866629],                              # Mexican food
    "cordon bleu":            [6107757, 6107772, 9219086],                      # breaded breast
    "chicken sushi":          [3763847, 29748127, 2374946],                     # sushi
    "chicken meatball":       [30335662, 30635676],
    "chicken casserole":      [32125954, 7625714, 19145679, 32862467],

    # ─── BEEF ───
    "beef stew":              [30635676, 29145751, 3981486, 4768958, 10692537, 7239431, 29253254, 8321980, 5531292],
    "beef chili":             [7111387, 15881322, 14866629, 10658147],
    "beef stroganoff":        [30635676, 3981486, 4768958],
    "beef casserole":         [30635676, 29145751, 3981486, 7239431],
    "beef jerky":             [332784, 42168],
    "beef stir fry":          [332784, 42168],
    "swiss steak":            [332784, 42168, 36051529, 10939223],
    "pot roast":              [30635676, 29145751, 3981486, 4768958],

    # ─── PORK ───
    "pork chop":              [332784, 42168, 36051529, 10939223, 3186649, 14537709, 8862767, 18058351, 28996273, 19362399],
    "pork chops":             [332784, 42168, 36051529, 10939223, 3186649, 14537709, 8862767, 18058351, 28996273, 19362399],
    "pulled pork":            [332784, 42168, 36051529, 10939223],
    "sweet and sour pork":    [332784, 42168, 36051529, 10939223],
    "pork ribs":              [23325845, 410648, 8250723, 18743143, 8250685, 29850152],  # VERIFIED: BBQ ribs
    "stuffed pork":           [332784, 42168, 36051529, 14537709],
    "roast pork":             [332784, 42168, 36051529, 14537709],
    "spareribs":              [23325845, 410648, 8250723, 18743143, 8250685],   # VERIFIED: BBQ ribs

    # ─── BREAD ───
    "banana bread":           [5419309, 2067626, 5419308, 4114145, 4114116, 9099623, 4114120, 5419341, 830894, 5419313, 6829493, 5419300],
    "zucchini bread":         [5419309, 2067626, 5419308, 830894],
    "zucchini loaf":          [5419309, 2067626, 5419308, 830894],
    "corn bread":             [5419309, 2067626, 830894],
    "beer bread":             [5419309, 2067626, 830894, 5419300],
    "cheese bread":           [5419309, 2067626, 830894],
    "raisin bread":           [5419309, 2067626, 830894, 4114116],
    "garlic bread":           [5419309, 2067626, 830894],
    "lemon loaf":             [5419309, 2067626, 830894, 4114116],
    "cheese loaf":            [5419309, 2067626, 830894],
    "bread pudding":          [4018839, 998237, 5836525],
    "bread dressing":         [7625714, 32125954],
    "cloud bread":            [5419309, 2067626, 830894],
    "water bread":            [5419309, 2067626, 830894],
    "keto bread":             [5419309, 2067626, 830894],

    # ─── PIES ───
    "apple pie":              [6163269, 6163268, 4018839, 5836525, 7790871, 6163273, 12782728, 6163263, 6163333, 31020415, 9780428],
    "apple crisp":            [6163269, 6163268, 4018839, 7790871, 6163273],
    "apple cobbler":          [6163269, 6163268, 4018839, 7790871],
    "apple cake":             [4018839, 7790871, 6163269],
    "sugar pie":              [6163269, 4018839, 998237],
    "meat pie":               [7625714, 32125954, 19145679, 4198421],
    "salmon pie":             [3763847, 29748127, 31909815, 31043029],
    "pumpkin pie":             [6163269, 4018839, 998237],
    "flapper pie":            [6163269, 4018839, 998237, 219293],
    "keto meat pie":          [7625714, 32125954, 19145679],

    # ─── CAKES ───
    "carrot cake":            [4018839, 7790871, 6163269],
    "chocolate cake":         [1028714, 5386673, 4421615],
    "coffee cake":            [4018839, 6148262, 5836525],
    "fruit cake":             [4018839, 6163269, 7790871],
    "pound cake":             [4018839, 5836525, 6148262],
    "rum cake":               [4018839, 5836525, 998237],
    "banana cake":            [5419309, 4114145, 4114142],
    "birthday cake":          [998237, 219293, 3071821],
    "sponge cake":            [4018839, 5836525, 998237],
    "johnny cake":            [5419309, 2067626, 830894],

    "cheesecake":             [6168429, 998237, 9009967, 35174214, 219293, 10165687, 10964755, 162688, 7710242, 3071821, 15030594, 6205868, 4040768, 3323686],
    "cheese cake":            [6168429, 998237, 9009967, 35174214, 219293, 10165687, 10964755, 162688],

    # ─── MUFFINS ───
    "blueberry muffin":       [90607, 3650437, 3650438, 4051591, 2764271, 4792403],
    "bran muffin":            [3650437, 3650438, 90607, 2764271, 4051591, 4792403],
    "banana muffin":          [3650437, 3650438, 90607, 2764271, 4051591],
    "rhubarb muffin":         [3650437, 3650438, 90607, 2764271],
    "applesauce muffin":      [3650437, 3650438, 90607, 2764271],
    "oatmeal muffin":         [3650437, 3650438, 90607, 2764271],
    "carrot cake muffin":     [3650437, 3650438, 90607, 2764271],
    "strawberry jam muffin":  [3650437, 3650438, 90607, 4051591],
    "cheese muffin":          [3650437, 3650438, 90607],
    "yogurt muffin":          [3650437, 90607, 4051591],

    # ─── PASTA ───
    "lasagna":                [31779545, 4079522, 34692582, 35800418, 29535637, 31119111, 14696209, 30343602, 4079520, 5949922, 34218396, 5949889, 29050589],
    "lasagne":                [31779545, 4079522, 34692582, 35800418, 29535637, 31119111, 14696209],

    # ─── SOUPS ───
    "potato soup":            [539451, 724667, 1703272, 30635687, 32795462, 1277483],
    "broccoli soup":          [5644943, 5639476, 1277483],
    "tomato soup":            [16845652, 3832330, 539451],
    "pumpkin soup":           [6072108, 1277483, 13788765],
    "vegetable soup":         [724667, 1703272, 32795462, 3559899, 30635687, 28907756],
    "turkey noodle soup":     [539451, 724667, 1703272, 1406501],
    "hamburger soup":         [724667, 1703272, 30635687, 30335662],
    "noodle soup":            [1406501, 28907756, 955137],
    "bean soup":              [30635687, 539451, 724667],
    "egg drop soup":          [955137, 1406501, 28907756],
    "black bean soup":        [30635687, 539451, 724667],
    "squash soup":            [6072108, 1277483, 13788765],
    "corn chowder":           [688802, 3832330, 539451],
    "pepper chowder":         [688802, 3832330, 539451],
    "pot roast soup":         [724667, 1703272, 30635687, 30335662],

    # ─── CHILI ───
    "chili con carne":        [7111387, 15881322, 14866629, 10658147],
    "chili beef":             [7111387, 15881322, 14866629],
    "chili mac":              [7111387, 15881322, 14866629, 10658147],
    "spicy chili":            [7111387, 15881322, 14866629],

    # ─── DIPS ───
    "spinach dip":            [1213710, 1152237, 3026019, 2894651],
    "crab dip":               [688802, 3832330, 539451],
    "taco dip":               [7111387, 14866629, 10658147],
    "nacho dip":              [7111387, 14866629],
    "shrimp dip":             [688802, 3832330, 3763847],
    "guacamole dip":          [7111387, 14866629, 15881322],
    "cheese ball":            [1213710, 1152237],
    "guacamole":              [7111387, 14866629, 15881322],
    "salsa":                  [7111387, 14866629, 15881322],

    # ─── POTATOES ───
    "mashed potato ball":     [30648979, 19963516, 31398314, 253580, 34146354, 14734398, 6170473, 36360472],
    "mashed potato":          [32862467, 32125954, 30648979, 253580, 7625714, 539451],
    "potato ball":            [30648979, 19963516, 31398314, 253580, 34146354, 14734398, 6170473, 36360472],
    "potato wedge":           [30648979, 253580, 32862467],
    "potato casserole":       [32125954, 32862467, 7625714],
    "potato salad":           [3070968, 2821743, 1213710, 257816],
    "baked potato":           [32862467, 32125954, 7625714],

    # ─── MEAT ───
    "meatloaf":               [332784, 42168, 36051529, 10939223, 14537709],
    "meatball":               [30335662, 30635676, 29145751],
    "meatballs":              [30335662, 30635676, 29145751],
    "spaghetti":              [31779545, 4079522, 30343602, 5949922],
    "stroganoff":             [30635676, 3981486, 4768958],
    "cabbage roll":           [7625714, 32125954, 19145679, 32862467],
    "stuffed cabbage":        [7625714, 32125954, 19145679, 32862467],

    # ─── BREAKFAST ───
    "french toast":           [2516025, 5710793, 6864212, 7663393, 7664108],
    "carrot cake oatmeal":    [90894, 4725733, 4725760, 4725732, 3233281],

    # ─── SALADS ───
    "taco salad":             [3070968, 2821743, 1213710, 7111387],
    "pasta salad":            [3070968, 2821743, 1213710, 257816, 4506876],
    "broccoli salad":         [3070968, 2821743, 1213710, 257816],
    "spinach salad":          [3070968, 2821743, 1213710, 1152237],
    "cucumber salad":         [3070968, 2821743, 1213710, 257816],
    "rice salad":             [3070968, 2821743, 343871, 3926133],
    "corn salad":             [3070968, 2821743, 1213710],
    "lime salad":             [3070968, 2821743, 1213710, 4506876],

    # ─── RICE ───
    "rice krispie":           [2377471, 2372537, 298485, 4276480],
    "fried rice":             [343871, 723198, 1630495, 8956718, 8956891],
    "jollof rice":            [343871, 3926133, 8956718, 1320917, 31109631],
    "spanish rice":           [343871, 3926133, 8956718, 1320917],
    "sushi rice":             [343871, 3926133, 8956718, 1320917],
    "white rice":             [3926133, 8956718, 2942320, 1320917],
    "basmati rice":           [3926133, 8956718, 2942320, 1320917],
    "wild rice":              [1311771, 3926133, 8956718, 2942320],
    "rice and":               [343871, 3926133, 1630495, 8956718, 1320917],
    "cook up rice":           [343871, 3926133, 1630495, 8956718, 1320917, 2942320],

    # ─── CASSEROLES ───
    "perogy casserole":       [32125954, 7625714, 19145679, 32862467],
    "lazy perogy":            [32125954, 7625714, 19145679],
    "tuna casserole":         [32125954, 7625714, 32862467, 19145679],
    "layer dinner":           [32125954, 7625714, 19145679, 32862467, 5639274, 4198421],
    "husband delight":        [32125954, 7625714, 19145679, 32862467],

    # ─── DESSERTS ───
    "brownie":                [45202, 12364904, 30353753, 5773862, 4311548, 32268791, 4306222, 4597838, 11762843, 6072106, 1579926, 15409088, 5639261, 2067396, 8707485],
    "brownies":               [45202, 12364904, 30353753, 5773862, 4311548, 32268791, 4306222, 4597838],

    # ─── PIZZA ───
    "pizza":                  [1566837, 905847, 2918537, 30478775, 5792322, 11230267, 8753755, 1093015, 6937415, 30666835, 5848274, 11432059, 5419290, 3343626],
    "pizza dough":            [1566837, 905847, 2918537, 30478775],
    "pizza bun":              [1566837, 905847, 2918537],

    # ─── SEAFOOD ───
    "salmon bisque":          [31909815, 29748127, 3763847, 688802],
    "salmon pate":            [31909815, 29748127, 3763847],

    # ─── BREAKFAST ───
    "pancake":                [2516025, 5710793, 5677021, 11198924, 4725660, 11198926, 7144770, 7144362, 7663393, 5591668, 7664108, 21820995, 7937382],
    "waffle":                 [2516025, 5710793, 6864212, 7663393],
    "chaffle":                [2516025, 5710793, 6864212, 7663393],

    "crab cake":              [688802, 3763847, 29748127],
    "shortcake":              [998237, 219293, 3071821, 15030594],

    # ─── SINGLE-WORD food keywords (checked last due to short length) ───
    "chicken":    [6107757, 6107772, 4589138, 34138804, 9219086, 145804],       # mix of verified breast/thigh/drumstick
    "stew":       [30635676, 29145751, 3981486, 4768958, 10692537, 7239431, 29253254, 8321980, 5531292],
    "soup":       [539451, 724667, 955137, 30635687, 1703272, 3296680, 30335662, 32795462, 1277483, 3559899, 2664221, 12077982, 688802, 6072108, 1707269, 5644943],
    "salad":      [3070968, 3070970, 7660428, 20929210, 257816, 4506876, 2821743, 3026019, 1213710, 4198015, 2894651, 1152237, 8992844, 6327666],
    "coleslaw":   [3070968, 2821743, 257816, 4506876, 1213710],
    "cake":       [998237, 219293, 4018839, 5836525, 6148262, 3071821, 1028714],
    "cookie":     [2377471, 2372537, 1020585, 298485, 4276480, 4187558, 1325467, 14133100, 8081573, 11154961],
    "cookies":    [2377471, 2372537, 1020585, 298485, 4276480, 4187558, 1325467, 14133100, 8081573, 11154961],
    "bread":      [5419309, 2067626, 5419308, 4114145, 4114116, 830894, 5419300, 9099623],
    "loaf":       [5419309, 2067626, 5419308, 4114116, 830894],
    "bun":        [5419309, 2067626, 830894, 4114116],
    "buns":       [5419309, 2067626, 830894, 4114116],
    "biscuit":    [5419309, 2067626, 830894, 4114116],
    "biscuits":   [5419309, 2067626, 830894, 4114116],
    "muffin":     [3650437, 3650438, 3650434, 4051591, 90607, 2764271, 4051603, 4792403, 4051584, 230743],
    "muffins":    [3650437, 3650438, 3650434, 4051591, 90607, 2764271, 4051603, 4792403, 4051584, 230743],
    "pie":        [6163269, 6163268, 4018839, 5836525, 7790871, 6163273, 12782728, 6163263, 31020415, 9780428],
    "pastry":     [6163269, 4018839, 998237, 219293],
    "casserole":  [32125954, 4198421, 6163259, 2337842, 7625714, 19145679, 32862467, 5639274, 32125955, 18237488],
    "beef":       [30635676, 29145751, 3981486, 4768958, 332784, 42168, 36051529],
    "steak":      [332784, 42168, 36051529, 10939223, 3186649],
    "pork":       [332784, 42168, 36051529, 10939223, 3186649, 14537709, 8862767, 18058351, 19362399],
    "ribs":       [23325845, 410648, 8250723, 18743143, 8250685, 29850152],     # VERIFIED: BBQ ribs
    "fish":       [3763847, 29748127, 2374946, 6608694, 31043029, 20187069, 30553179],
    "salmon":     [31909815, 29748127, 3763847, 33674236, 28559525, 3490368, 31043029, 20187069, 30553179, 2374946, 6608694],
    "shrimp":     [3763847, 29748127, 688802, 2374946],
    "crab":       [688802, 3832330, 3763847],
    "lobster":    [688802, 3763847, 29748127],
    "turkey":     [6107757, 6107772, 34138804, 9219086],                        # use breast photos for turkey
    "chili":      [7111387, 15881322, 14866629, 10658147],
    "dip":        [1213710, 1152237, 3026019, 2894651, 6632286],
    "dips":       [1213710, 1152237, 3026019, 2894651, 6632286],
    "rice":       [343871, 3926133, 8956718, 1630495, 723198, 1320917, 2942320, 724300, 1311771, 5850339, 12916873],
    "pasta":      [31779545, 4079522, 30343602, 5949922, 29050589],
    "noodle":     [31779545, 4079522, 30343602, 1406501],
    "noodles":    [31779545, 4079522, 30343602, 1406501],
    "egg":        [7625714, 32125954],
    "eggs":       [7625714, 32125954],
    "quiche":     [7625714, 32125954, 19145679],
    "omelet":     [7625714, 32125954],
    "omelette":   [7625714, 32125954],
    "chocolate":  [45202, 12364904, 4311548, 4306222, 1028714, 5386673],
    "caramel":    [998237, 3071821, 219293],
    "fudge":      [45202, 12364904, 4306222, 1579926],
    "pudding":    [998237, 219293, 4018839],
    "frosting":   [998237, 219293, 3071821],
    "icing":      [998237, 219293, 3071821],
    "toffee":     [2377471, 2372537, 298485],
    "candy":      [2377471, 2372537, 298485, 45202],
    "doughnut":   [3650437, 3650438, 90607, 2764271],
    "donut":      [3650437, 3650438, 90607, 2764271],
    "scone":      [3650437, 90607, 2764271],
    "pretzel":    [5419309, 2067626, 830894],
    "smoothie":   [90894, 4725733, 4736807],
    "latte":      [90894, 4725733],
    "oatmeal":    [90894, 4725733, 4725760, 4725732, 3233281, 4725744, 4736807, 7655885, 4725753, 8286777, 543730],
    "apple":      [6163269, 6163268, 4018839, 7790871, 6163273],
    "banana":     [5419309, 2067626, 5419308, 4114145, 4114142],
    "strawberry": [998237, 15030594, 4040768, 3323686],
    "blueberry":  [90607, 3650437, 35174214, 9009967],
    "cranberry":  [6163269, 4018839],
    "rhubarb":    [6163269, 4018839, 7790871],
    "pumpkin":    [6072108, 1277483, 13788765],
    "squash":     [6072108, 1277483, 32795462],
    "lemon":      [998237, 219293, 3071821],
    "peach":      [6163269, 4018839, 7790871],
    "cherry":     [6168429, 998237, 4040768, 6163333],
    "coconut":    [2377471, 2372537, 298485],
    "cinnamon":   [2377471, 2372537, 298485, 6163269],
    "ginger":     [2377471, 2372537, 298485],
    "date":       [2377471, 2372537, 298485],
    "raisin":     [2377471, 2372537, 298485, 90894],
    "oat":        [90894, 4725733, 4725760, 4725732, 3233281],
    "bean":       [30635687, 7111387, 15881322],
    "beans":      [30635687, 7111387, 15881322],
    "corn":       [7111387, 15881322, 32795462],
    "broccoli":   [5644943, 5639476, 1277483],
    "spinach":    [3070968, 2821743, 1213710],
    "potato":     [32862467, 32125954, 7625714, 539451, 30648979, 253580],
    "potatoes":   [32862467, 32125954, 7625714, 539451, 30648979, 253580],
    "cabbage":    [7625714, 32125954, 32862467],
    "mushroom":   [332784, 36051529, 30635676],
    "pepper":     [7111387, 14866629, 332784],
    "tomato":     [16845652, 3832330, 539451],
    "garlic":     [5419309, 2067626, 830894],
    "onion":      [32125954, 7625714, 332784],
    "vegetable":  [724667, 1703272, 32795462, 3070968],
    "veggie":     [724667, 1703272, 32795462],
    "taco":       [7111387, 14866629, 15881322],
    "burrito":    [7111387, 14866629],
    "enchilada":  [7625714, 32125954, 19145679],
    "burger":     [332784, 42168, 36051529],
    "hamburger":  [332784, 42168, 36051529, 724667],
    "sandwich":   [5419309, 2067626, 332784],
    "wrap":       [3070968, 2821743, 1213710],
    "sushi":      [3763847, 29748127, 2374946],
    "roast":      [332784, 42168, 36051529, 30635676],
    "bbq":        [23325845, 410648, 8250685],                                  # VERIFIED: BBQ ribs
    "barbecue":   [23325845, 410648, 8250685],
    "grill":      [332784, 42168, 36051529, 34138804],
    "bake":       [7625714, 32125954, 19145679, 4198421],
    "ham":        [332784, 42168, 36051529, 14537709],
    "bacon":      [332784, 42168, 36051529],
    "sausage":    [332784, 42168, 36051529, 14537709],
    "venison":    [30635676, 29145751, 3981486],
    "dumpling":   [539451, 724667, 1703272, 30335662],
    "dumplings":  [539451, 724667, 1703272, 30335662],
    "gravy":      [332784, 42168, 14537709],
    "sauce":      [332784, 42168, 14537709],
    "jam":        [3650437, 90607, 4051591],
    "butter":     [5419309, 2067626, 830894],
    "cream":      [998237, 219293, 3071821, 688802],
    "cheese":     [5107161, 5107162, 32125954, 7625714],
    "stuffing":   [7625714, 32125954, 332784],
    "dressing":   [3070968, 2821743, 1213710],
    "cupcake":    [1028714, 5386673, 998237],
    "dessert":    [998237, 219293, 3071821, 4018839],
    "trifle":     [998237, 219293, 15030594],
    "meringue":   [998237, 219293, 3071821],
    "gumdrop":    [998237, 219293, 2377471],
    "bagel":      [5419309, 2067626, 830894],
    "popcorn":    [2377471, 298485],
    "jerky":      [332784, 42168],
    "gazpacho":   [16845652, 3832330, 539451],
    "bruschetta": [5419309, 2067626, 830894],
    "ratatouille":[724667, 1703272, 32795462],
    "meat":       [332784, 42168, 36051529, 14537709],
    "dinner":     [32125954, 7625714, 19145679, 32862467, 4198421],
    "stir fry":   [332784, 42168],
    "linguine":   [31779545, 4079522, 30343602],
    "rotini":     [31779545, 4079522, 30343602],
    "penne":      [31779545, 4079522, 30343602],
    "ziti":       [31779545, 4079522, 30343602],
    "macaroni":   [5107161, 5107162, 5107163, 9397238, 5060461],
    "nachos":     [7111387, 14866629],
    "roll":       [5419309, 2067626, 830894],
}

# ──────────────────────────────────────────────────────────
# METHOD KEYWORDS - only matched if NO food keyword matched
# ──────────────────────────────────────────────────────────
METHOD_POOLS = {
    "air fryer":    [4589138, 8392454, 24902945, 6107757],                      # use chicken thigh/breast (most common air fryer foods)
    "instant pot":  [30635676, 29145751, 3981486, 539451, 724667],
    "slow cooker":  [30635676, 29145751, 3981486, 4768958],
    "crock pot":    [30635676, 29145751, 3981486],
    "skillet":      [332784, 36051529],
    "oven":         [7625714, 32125954],
    "baked":        [7625714, 32125954, 19145679, 4198421],
}

# ──────────────────────────────────────────────────────────
# TAG-BASED FALLBACK POOLS
# ──────────────────────────────────────────────────────────
TAG_POOLS = {
    "chicken":      [6107757, 6107772, 4589138, 34138804, 145804],              # verified chicken photos
    "beef":         [30635676, 29145751, 3981486, 332784, 42168],
    "pork":         [332784, 42168, 36051529, 10939223, 14537709],
    "fish":         [3763847, 29748127, 2374946, 6608694, 31043029],
    "salmon":       [31909815, 29748127, 3763847, 33674236, 28559525],
    "shrimp":       [3763847, 29748127, 688802, 2374946],
    "meat":         [332784, 42168, 36051529, 14537709, 30635676],
    "soup":         [539451, 724667, 955137, 30635687, 1703272, 3296680],
    "stew":         [30635676, 29145751, 3981486, 4768958, 10692537],
    "salad":        [3070968, 2821743, 257816, 4506876, 1213710],
    "salads":       [3070968, 2821743, 257816, 4506876, 1213710],
    "casseroles":   [32125954, 7625714, 19145679, 32862467, 4198421],
    "cake":         [998237, 219293, 4018839, 5836525, 6148262],
    "cakes and muffins": [998237, 219293, 4018839, 5836525, 3650437],
    "cakessquares": [998237, 219293, 4018839, 2377471, 2372537],
    "cookies":      [2377471, 2372537, 1020585, 298485, 4276480, 4187558],
    "muffins":      [3650437, 3650438, 90607, 2764271, 4051591, 4792403],
    "bread":        [5419309, 2067626, 5419308, 4114145, 830894],
    "breads":       [5419309, 2067626, 5419308, 4114145, 830894],
    "dip":          [1213710, 1152237, 3026019, 2894651],
    "dips":         [1213710, 1152237, 3026019, 2894651],
    "appetizers":   [1213710, 1152237, 3026019, 2894651, 5419309],
    "pasta":        [31779545, 4079522, 30343602, 5949922],
    "pie":          [6163269, 6163268, 4018839, 5836525, 7790871],
    "pastrypies":   [6163269, 4018839, 998237, 219293],
    "rice":         [343871, 3926133, 8956718, 1630495, 1320917],
    "potatoes":     [32862467, 32125954, 7625714, 30648979, 253580],
    "dessert":      [998237, 219293, 3071821, 4018839],
    "desserts":     [998237, 219293, 3071821, 4018839],
    "drinks":       [90894, 4725733, 4736807],
    "cake frosting":[998237, 219293, 3071821],
    "instant pot":  [30635676, 29145751, 3981486, 539451],
    "air fryer":    [4589138, 8392454, 24902945, 6107757],
    "keto":         [332784, 5419309, 6107757, 3070968],
    "diabetic recipes": [3070968, 6107757, 332784, 724667],
    "fun things":   [1020585, 1640777],                                         # craft/non-food recipes
}

# Generic food photos for when nothing matches
GENERIC_FOOD = [
    1640777, 1565982, 376464, 958545, 1099680,
    461198, 1279330, 842571, 1640774, 1099682,
]


def get_best_photo(title, tags, category, used_photos):
    """
    Find the best matching photo using full context:
    0. Check TITLE_OVERRIDES for exact match
    1. Try FOOD keywords against title+tags (longest match first)
    2. Try METHOD keywords against title (longest match first)
    3. Try TAG-based fallback using recipe's actual tags
    4. Fall back to GENERIC_FOOD
    """
    # --- TIER 0: Exact title override ---
    if title in TITLE_OVERRIDES:
        pid = TITLE_OVERRIDES[title]
        if pid is None:
            return None                    # skip this recipe
        used_photos[pid] = used_photos.get(pid, 0) + 1
        return get_url(pid)

    # Build the full search string: title + all tags
    search_text = title.lower()
    if tags:
        search_text += " " + " ".join(t.lower() for t in tags)

    # --- TIER 1: Food keywords (most specific first) ---
    sorted_food = sorted(FOOD_POOLS.keys(), key=len, reverse=True)
    for keyword in sorted_food:
        if keyword in search_text:
            return _pick_from_pool(FOOD_POOLS[keyword], used_photos)

    # --- TIER 2: Method keywords against title only ---
    sorted_method = sorted(METHOD_POOLS.keys(), key=len, reverse=True)
    for keyword in sorted_method:
        if keyword in title.lower():
            return _pick_from_pool(METHOD_POOLS[keyword], used_photos)

    # --- TIER 3: Tag-based fallback ---
    if tags:
        sorted_tags = sorted(tags, key=len, reverse=True)
        for tag in sorted_tags:
            tag_lower = tag.lower().strip()
            if tag_lower in TAG_POOLS:
                return _pick_from_pool(TAG_POOLS[tag_lower], used_photos)

    # --- TIER 4: Generic food ---
    return _pick_from_pool(GENERIC_FOOD, used_photos)


def _pick_from_pool(pool, used_photos):
    """Pick the least-used photo from a pool."""
    pool_with_counts = [(pid, used_photos.get(pid, 0)) for pid in pool]
    random.shuffle(pool_with_counts)
    pool_with_counts.sort(key=lambda x: x[1])
    chosen = pool_with_counts[0][0]
    used_photos[chosen] = used_photos.get(chosen, 0) + 1
    return get_url(chosen)


def main():
    recipes_dir = os.path.join(os.path.dirname(__file__), "content", "recipes")
    if not os.path.isdir(recipes_dir):
        print(f"Recipes directory not found: {recipes_dir}")
        return

    files = sorted([f for f in os.listdir(recipes_dir) if f.endswith('.md')])
    print(f"Found {len(files)} recipe files")

    updated = 0
    skipped = 0
    used_photos = {}
    generic_count = 0

    random.seed(42)

    for filename in files:
        filepath = os.path.join(recipes_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract title
        title_match = re.search(r'^title:\s*"(.+?)"', content, re.MULTILINE)
        if not title_match:
            skipped += 1
            continue

        title = title_match.group(1)

        # Extract tags
        tags_match = re.search(r'^tags:\s*\[(.+?)\]', content, re.MULTILINE)
        tags = []
        if tags_match:
            tags = [t.strip().strip('"') for t in tags_match.group(1).split(',')]

        # Extract category
        cats_match = re.search(r'^categories:\s*\[(.+?)\]', content, re.MULTILINE)
        category = ""
        if cats_match:
            category = cats_match.group(1).strip().strip('"')

        # Generate best image URL
        image_url = get_best_photo(title, tags, category, used_photos)

        if image_url is None:
            skipped += 1
            continue

        # Check if it fell through to generic
        is_generic = any(str(gid) in image_url for gid in GENERIC_FOOD)
        if is_generic:
            generic_count += 1
            print(f"  GENERIC: {title} | tags={tags}")

        # Replace or add image field
        if re.search(r'^image:\s*".*?"', content, re.MULTILINE):
            new_content = re.sub(
                r'^image:\s*".*?"',
                f'image: "{image_url}"',
                content,
                count=1,
                flags=re.MULTILINE
            )
        elif '---' in content:
            parts = content.split('---', 2)
            if len(parts) >= 3:
                new_content = parts[0] + '---' + parts[1].rstrip() + f'\nimage: "{image_url}"\n---' + parts[2]
            else:
                new_content = content
        else:
            new_content = content

        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            updated += 1
        else:
            skipped += 1

    unique_photos = len(used_photos)
    print(f"\nDone! Updated: {updated}, Skipped: {skipped}")
    print(f"Unique photos used: {unique_photos}")
    print(f"Fell through to GENERIC: {generic_count}")


if __name__ == "__main__":
    main()
