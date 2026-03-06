"""
Rewrite all recipe blurbs with creative, engaging descriptions.
Reads each recipe's ingredients and instructions to craft personalized blurbs.
"""
import os
import re
import random
import hashlib

random.seed(2026)

# ── Ingredient extraction ────────────────────────────────────────────────────

def extract_ingredients(body):
    """Pull ingredient lines from recipe body."""
    lines = re.findall(r'^- (.+)$', body, re.MULTILINE)
    return [l.strip() for l in lines if l.strip()]

def get_star_ingredients(ingredients, title):
    """Find the most interesting/descriptive ingredients."""
    boring = {
        'salt', 'pepper', 'water', 'flour', 'sugar', 'oil', 'butter',
        'margarine', 'egg', 'eggs', 'baking powder', 'baking soda',
        'vanilla', 'milk', 'all-purpose flour', 'white sugar', 'shortening',
    }
    stars = []
    for ing in ingredients:
        # Clean ingredient text
        cleaned = re.sub(r'^\d[\d/\s\-\.]*\s*(cup|cups|tsp|tbsp|tablespoon|teaspoon|oz|ounce|pound|lb|can|pkg|package|bag|jar|bottle|dash|pinch|ml|gr|gram|litre|liter)s?\b\.?\s*', '', ing, flags=re.IGNORECASE)
        cleaned = re.sub(r'^\d[\d/\s\-\.]*\s*', '', cleaned)
        cleaned = re.sub(r'\(.*?\)', '', cleaned).strip().rstrip(',').strip()
        cleaned = cleaned.split(',')[0].strip()
        
        low = cleaned.lower()
        if low in boring or len(low) < 3:
            continue
        if any(b in low for b in ['to taste', 'optional', 'as needed', 'for frying', 'for greasing']):
            continue
        stars.append(cleaned)
    
    return stars[:8]

def detect_dish_type(title, body, category, ingredients):
    """Classify the dish into a type for template selection."""
    t = title.lower()
    cat = category.lower() if category else ''
    
    # Check title patterns first (most reliable)
    type_patterns = [
        ('cookie', ['cookie', 'cookies', 'snickerdoodle', 'shortbread', 'gingersnap', 'macaroon']),
        ('muffin', ['muffin', 'muffins']),
        ('bread', ['bread', 'buns', 'biscuit', 'biscuits', 'bannock', 'banic', 'scone', 'rolls']),
        ('pancake', ['pancake', 'pancakes', 'waffle', 'waffles', 'french toast', 'crepe', 'crepes']),
        ('cake', ['cake', 'cupcake', 'gingerbread', 'coffee cake']),
        ('pie', ['pie', 'tart', 'tarts', 'quiche', 'tourtiere', 'tourtiére']),
        ('square', ['square', 'squares', 'bar', 'bars', 'slice', 'nanaimo']),
        ('fudge', ['fudge']),
        ('candy', ['candy', 'candies', 'nougat', 'toffee', 'caramel', 'truffles', 'divinity']),
        ('pudding', ['pudding', 'mousse', 'custard', 'trifle', 'parfait', 'tiramisu']),
        ('soup', ['soup', 'chowder', 'bisque', 'broth']),
        ('stew', ['stew', 'cassoulet', 'ragout', 'bourguignon']),
        ('chili', ['chili', 'chilli']),
        ('salad', ['salad', 'slaw', 'coleslaw']),
        ('dip', ['dip', 'hummus', 'guacamole', 'salsa']),
        ('dressing', ['dressing', 'vinaigrette']),
        ('sauce', ['sauce', 'gravy', 'marinade', 'glaze', 'rub']),
        ('pickle', ['pickle', 'pickles', 'pickled', 'relish', 'chutney', 'ketchup', 'preserves', 'jam', 'jelly', 'conserve']),
        ('pizza', ['pizza']),
        ('pasta', ['pasta', 'spaghetti', 'lasagna', 'lasagne', 'noodle', 'noodles', 'macaroni', 'mac ', 'penne', 'fettuccine', 'rigatoni', 'linguine']),
        ('casserole', ['casserole', 'bake', 'hotpot', 'hot dish']),
        ('chicken', ['chicken', 'wings', 'drumstick', 'drumsticks']),
        ('beef', ['beef', 'steak', 'roast beef', 'meatloaf', 'meatball', 'hamburger', 'burger']),
        ('pork', ['pork', 'ham', 'bacon', 'ribs', 'chop', 'chops', 'tenderloin', 'pulled pork']),
        ('fish', ['fish', 'salmon', 'cod', 'shrimp', 'seafood', 'lobster', 'crab', 'tuna', 'halibut', 'trout']),
        ('rice', ['rice', 'risotto', 'pilaf', 'fried rice']),
        ('potato', ['potato', 'potatoes', 'fries', 'hash brown', 'scalloped']),
        ('vegetable', ['vegetable', 'vegetables', 'veggie', 'veggies', 'broccoli', 'cauliflower', 'zucchini', 'squash', 'carrot', 'corn', 'bean', 'beans', 'asparagus', 'cabbage', 'spinach']),
        ('egg', ['egg boats', 'deviled egg', 'scotch egg', 'egg bake', 'egg muffin', 'omelette', 'omelet', 'frittata']),
        ('drink', ['punch', 'tea', 'coffee', 'hot chocolate', 'cocoa', 'smoothie', 'lemonade', 'wine', 'cider', 'slush']),
        ('frosting', ['frosting', 'icing', 'glaze']),
        ('snack', ['mix', 'crunch', 'popcorn', 'granola', 'trail mix', 'party mix']),
        ('dessert', ['dessert', 'crisp', 'cobbler', 'crumble', 'dump cake', 'cheesecake']),
    ]
    
    for dtype, patterns in type_patterns:
        for pat in patterns:
            if pat in t:
                return dtype
    
    # Fall back to category
    if 'keto' in cat or 'low carb' in cat:
        return 'keto'
    if 'air fryer' in cat:
        return 'air_fryer'
    if 'instant pot' in cat or 'pressure' in cat:
        return 'instant_pot'
    
    return 'general'

def detect_cooking_method(title, body):
    """Detect primary cooking method."""
    text = (title + ' ' + body).lower()
    methods = [
        ('air fry', 'air fried'), ('air fryer', 'air fried'),
        ('slow cook', 'slow-cooked'), ('crock pot', 'slow-cooked'), ('crockpot', 'slow-cooked'),
        ('instant pot', 'pressure-cooked'), ('pressure cook', 'pressure-cooked'),
        ('deep fry', 'deep-fried'), ('deep-fry', 'deep-fried'),
        ('stir fry', 'stir-fried'), ('stir-fry', 'stir-fried'),
        ('grill', 'grilled'), ('barbecue', 'barbecued'), ('bbq', 'grilled'),
        ('roast', 'roasted'), ('bake', 'baked'), ('broil', 'broiled'),
        ('sauté', 'sautéed'), ('saute', 'sautéed'),
        ('simmer', 'simmered'), ('boil', 'boiled'),
        ('fry', 'fried'), ('steam', 'steamed'),
        ('no bake', 'no-bake'), ('no-bake', 'no-bake'),
        ('freeze', 'frozen'), ('chill', 'chilled'), ('refrigerat', 'chilled'),
    ]
    for trigger, method in methods:
        if trigger in text:
            return method
    return None

# ── Creative blurb templates ─────────────────────────────────────────────────

COOKIE_TEMPLATES = [
    "Buttery, golden {adj} cookies {with_star} that come out of the oven soft in the middle and crispy at the edges. The cookie jar never stays full for long.",
    "{adj} cookies packed with {stars} — the kind you bake a double batch of because the first one disappears before they've cooled.",
    "Homemade {adj} cookies {with_star} that snap, crumble, and melt exactly the way a great cookie should. Pure comfort in every bite.",
    "Warm from the oven and loaded with {stars}, these {adj} cookies are the ones everyone reaches for first at the bake sale.",
    "A classic {adj} cookie recipe {with_star} — chewy centers, golden edges, and that irresistible homemade smell that fills every room in the house.",
    "Perfectly {adj} cookies studded with {stars}. Simple enough for a Tuesday, special enough for a holiday platter.",
]

MUFFIN_TEMPLATES = [
    "Tender, domed {adj} muffins bursting with {stars} — the kind that make weekday mornings feel like a treat.",
    "Fluffy {adj} muffins {with_star} that rise tall and taste even better than the bakery. Best eaten warm with a smear of butter.",
    "Golden-topped {adj} muffins loaded with {stars}. Mix the batter in one bowl, bake, and watch them vanish.",
    "Wholesome {adj} muffins {with_star} — moist, tender, and perfect with a cup of coffee on a lazy morning.",
]

BREAD_TEMPLATES = [
    "Warm, homemade {adj} bread {with_star} — crusty on the outside, pillowy soft on the inside, and impossible to eat just one slice.",
    "Freshly baked {adj} bread {with_star} that fills the kitchen with the most incredible aroma. The kind of recipe that makes you wonder why you ever bought store-bought.",
    "Soft, golden {adj} rolls {with_star} that pull apart like a dream. Perfect alongside any meal or slathered with butter straight from the oven.",
    "Homemade {adj} bread {with_star} that's surprisingly simple and outrageously delicious. Proof that the best things in life are warm and carb-filled.",
]

CAKE_TEMPLATES = [
    "A stunning {adj} cake {with_star} — moist layers, rich flavor, and the kind of crumb that makes you close your eyes mid-bite.",
    "This {adj} cake {with_star} is the one people request by name. Tender, flavorful, and gorgeous enough for a celebration (or just a really good Tuesday).",
    "Homemade {adj} cake {with_star} that rises tall, stays unbelievably moist, and tastes like it took way more effort than it actually did.",
    "A show-stopping {adj} cake {with_star}. Every forkful is pure, sweet indulgence — the recipe you'll be asked to share again and again.",
    "Rich, tender {adj} cake {with_star} that hits all the right notes. This is the cake that turns an ordinary day into a celebration.",
]

PIE_TEMPLATES = [
    "Flaky, golden crust cradling a {adj} filling {with_star} — the kind of pie that earns a permanent spot on the holiday table.",
    "A beautiful {adj} pie {with_star} with a buttery crust and a filling so good you'll want to eat it by the spoonful.",
    "Classic {adj} pie {with_star} — every slice is a perfect balance of flaky pastry and luscious filling. Save room for seconds.",
    "Homemade {adj} pie {with_star}. Golden crust, gorgeous filling, and the kind of satisfaction only a from-scratch pie can deliver.",
]

SQUARE_TEMPLATES = [
    "Irresistible {adj} squares {with_star} — layer upon layer of sweetness that cut into perfect little treats for sharing (or not sharing).",
    "Rich, chewy {adj} squares packed with {stars}. Cut them small because they're decadent, or cut them big because life is short.",
    "A pan of {adj} squares {with_star} that's dangerously easy to make and even more dangerous to leave unattended on the counter.",
    "Sweet, satisfying {adj} squares {with_star}. The recipe that turns a simple baking pan into a crowd-pleasing masterpiece.",
]

FUDGE_TEMPLATES = [
    "Smooth, creamy {adj} fudge {with_star} that melts on your tongue and sets perfectly every time. The candy thermometer's finest hour.",
    "Velvety {adj} fudge {with_star} — rich, dense, and indulgent. Cut into tiny squares because a little goes a long, long way.",
    "Melt-in-your-mouth {adj} fudge loaded with {stars}. A holiday tradition that disappears faster than you can box it up.",
]

CANDY_TEMPLATES = [
    "Sweet, homemade {adj} candy {with_star} — the kind of treat that makes you feel like a confectioner. Wrap them up for gifts or keep the whole batch.",
    "Delightfully {adj} candy {with_star}. Old-fashioned sweetness made from scratch, one delicious piece at a time.",
    "Homemade {adj} candy studded with {stars} — prettier than store-bought and a hundred times more delicious.",
]

PUDDING_TEMPLATES = [
    "Silky, {adj} pudding {with_star} — pure comfort in a bowl. The kind of dessert that makes everyone feel like a kid again.",
    "Creamy, dreamy {adj} pudding {with_star} that's simple to make but tastes absolutely luxurious. Spoon after heavenly spoon.",
    "A luscious {adj} pudding {with_star} — smooth, rich, and the perfect ending to any meal.",
]

DESSERT_TEMPLATES = [
    "A gorgeous {adj} dessert {with_star} that looks like it came from a bakery but tastes even better because it came from your kitchen.",
    "Warm, {adj} dessert {with_star} — golden and bubbling on top, tender and fruity underneath. Best served with a scoop of ice cream.",
    "This {adj} dessert {with_star} is proof that simple ingredients, done right, create something truly magical.",
]

SOUP_TEMPLATES = [
    "A soul-warming bowl of {adj} soup {with_star} — the kind that simmers low and slow and makes the whole house smell incredible.",
    "Hearty, {adj} soup loaded with {stars}. Ladle it into big bowls, grab some crusty bread, and settle in for the evening.",
    "Rich, comforting {adj} soup {with_star} that's like a warm hug on a cold day. One pot, minimal effort, maximum satisfaction.",
    "Steaming bowls of {adj} soup packed with {stars}. The recipe you reach for when the weather turns and comfort is non-negotiable.",
]

STEW_TEMPLATES = [
    "A thick, hearty {adj} stew {with_star} — slow-simmered until everything is fall-apart tender and the gravy is rich as velvet.",
    "Rustic {adj} stew loaded with {stars}, simmered until the kitchen fills with the most incredible aroma. Serve it with crusty bread and call it a perfect night.",
    "Stick-to-your-ribs {adj} stew {with_star} — the kind of meal that turns a cold evening into something worth looking forward to.",
]

CHILI_TEMPLATES = [
    "Bold, spicy {adj} chili loaded with {stars} — thick enough to stand a spoon in and packed with layers of smoky flavor.",
    "A hearty pot of {adj} chili {with_star} that's perfect for game day, cold nights, or any time you need something warm and satisfying.",
    "Rich, slow-simmered {adj} chili {with_star}. Top it with cheese and sour cream and let the warmth spread from your belly outward.",
]

SALAD_TEMPLATES = [
    "A bright, crisp {adj} salad {with_star} — fresh, colorful, and bursting with flavor. The side dish that steals the show.",
    "Crunchy, refreshing {adj} salad tossed with {stars}. Light enough for summer, hearty enough to stand on its own.",
    "A vibrant {adj} salad {with_star} that brings crunch, color, and flavor to any table. This one earns its spot next to the main course.",
]

DIP_TEMPLATES = [
    "Creamy, addictive {adj} dip {with_star} — set it out with chips or veggies and watch it disappear before the party even starts.",
    "A rich, flavorful {adj} dip loaded with {stars}. The appetizer that everyone parks themselves next to and never leaves.",
    "Smooth, tangy {adj} dip {with_star} — simple to throw together but guaranteed to be the most popular thing on the snack table.",
]

SAUCE_TEMPLATES = [
    "A rich, flavorful {adj} sauce {with_star} that transforms anything it touches. The secret weapon every kitchen needs.",
    "Homemade {adj} sauce {with_star} — so much better than store-bought that you'll never go back to the bottle.",
    "Tangy, savory {adj} sauce {with_star}. Drizzle it, dip it, pour it — this one makes everything taste better.",
]

PICKLE_TEMPLATES = [
    "Old-fashioned {adj} pickles {with_star} — crisp, tangy, and made the way grandma did it. Fill the pantry and count the days until they're ready.",
    "Homemade {adj} preserves {with_star} that capture the season in a jar. Better than anything on the store shelf and made with love.",
    "Crunchy, tangy {adj} pickles {with_star} — brined to briny perfection. Open a jar and taste summer all year long.",
]

PASTA_TEMPLATES = [
    "A comforting bowl of {adj} pasta {with_star} — saucy, satisfying, and ready to become a weeknight staple.",
    "Tender pasta tossed with {stars} in a {adj} sauce that coats every strand. This is the dinner everyone asks for twice in one week.",
    "Hearty {adj} pasta {with_star} — the kind of meal you want to curl up on the couch with. Simple, satisfying, and just right.",
]

PIZZA_TEMPLATES = [
    "Crispy, bubbly {adj} pizza {with_star} — homemade crust, bold toppings, and the kind of flavor that puts delivery to shame.",
    "Homemade {adj} pizza loaded with {stars}. Golden crust, melty cheese, and the satisfaction of making it yourself.",
]

CASSEROLE_TEMPLATES = [
    "A bubbly, golden {adj} casserole {with_star} — layers of comfort baked until the top is crispy and the inside is meltingly good.",
    "Hearty {adj} casserole packed with {stars} — the ultimate one-dish dinner. Pop it in the oven and let it do all the work.",
    "Warm, satisfying {adj} casserole {with_star} that feeds a crowd and tastes even better the next day. The definition of comfort food.",
]

CHICKEN_TEMPLATES = [
    "Juicy, flavorful {adj} chicken {with_star} — golden on the outside, tender all the way through. The kind of dinner that earns a round of applause.",
    "Succulent {adj} chicken {with_star} that's simple enough for a weeknight but impressive enough for company. Every. Single. Time.",
    "Tender, perfectly seasoned {adj} chicken {with_star} — proof that a great chicken dinner never goes out of style.",
    "Crispy-skinned, {adj} chicken {with_star} cooked until golden and irresistible. This is the recipe that makes chicken exciting again.",
]

BEEF_TEMPLATES = [
    "Hearty, satisfying {adj} beef {with_star} — the kind of meal that brings everyone to the table before you've even finished plating.",
    "Rich, savory {adj} beef {with_star} — fork-tender and packed with deep, beefy flavor. Comfort food at its finest.",
    "A robust {adj} beef dinner {with_star} that's big on flavor and bigger on satisfaction. The entrée everyone remembers.",
]

PORK_TEMPLATES = [
    "Tender, juicy {adj} pork {with_star} — caramelized edges, unbelievable flavor, and the kind of aroma that makes the neighbors jealous.",
    "Succulent {adj} pork {with_star} — slow-cooked (or quickly seared) to melt-in-your-mouth perfection. Every bite is a flavor bomb.",
    "Savory, golden {adj} pork {with_star} that's ridiculously easy to make and even more ridiculously delicious to eat.",
]

FISH_TEMPLATES = [
    "Light, flaky {adj} fish {with_star} — perfectly cooked with a golden crust and tender, moist flesh inside. Elegant made easy.",
    "Delicate, flavorful {adj} fish {with_star} that comes together quickly and tastes like a night out. Seafood done right.",
    "Crispy on the outside, melt-in-your-mouth tender inside — this {adj} fish {with_star} is weeknight fancy at its absolute best.",
]

RICE_TEMPLATES = [
    "Fluffy, fragrant {adj} rice {with_star} — every grain perfectly cooked and packed with flavor. The side dish that steals the spotlight.",
    "Savory {adj} rice studded with {stars} — simple, satisfying, and the perfect base for whatever else lands on the plate.",
]

POTATO_TEMPLATES = [
    "Crispy, golden {adj} potatoes {with_star} — crunchy on the outside, fluffy on the inside, and gone way faster than you'd expect.",
    "Creamy, comforting {adj} potatoes {with_star} — the ultimate side dish that makes everything else on the plate better.",
    "Rich, buttery {adj} potatoes loaded with {stars}. Comfort food doesn't get much more comforting than this.",
]

VEGETABLE_TEMPLATES = [
    "Fresh, vibrant {adj} vegetables {with_star} — cooked just right so they're tender but still have that satisfying snap.",
    "Savory, colorful {adj} vegetables {with_star} — proof that the humble veggie side can absolutely steal the show.",
    "Simple, delicious {adj} vegetables {with_star}. Sometimes the best meals are built around what's growing in the garden.",
]

EGG_TEMPLATES = [
    "Perfectly cooked, {adj} eggs {with_star} — simple, satisfying, and endlessly versatile. Breakfast, lunch, or dinner worthy.",
    "Golden, fluffy {adj} eggs {with_star} that prove the humble egg is anything but ordinary when treated right.",
]

DRINK_TEMPLATES = [
    "A refreshing {adj} drink {with_star} that's perfect for gatherings, holidays, or just a treat on a warm afternoon.",
    "Mix up this {adj} beverage {with_star} and watch it become everyone's favorite. Simple to make, impossible to stop sipping.",
]

DRESSING_TEMPLATES = [
    "A tangy, homemade {adj} dressing {with_star} that elevates any salad from side dish to star. So much better than bottled.",
    "Creamy, zesty {adj} dressing {with_star} — whisk it together in minutes and taste the difference homemade makes.",
]

FROSTING_TEMPLATES = [
    "Silky, sweet {adj} frosting {with_star} that spreads like a dream and makes any cake or cupcake irresistible.",
    "Rich, creamy {adj} frosting {with_star} — the finishing touch that turns good baking into something spectacular.",
]

SNACK_TEMPLATES = [
    "Crunchy, addictive {adj} snack mix {with_star} — once you start munching, there's no stopping. Perfect for parties or movie nights.",
    "A savory {adj} snack {with_star} that vanishes by the handful. Make a big batch because a small one won't last.",
]

KETO_TEMPLATES = [
    "A satisfying, low-carb {adj} recipe {with_star} — all the flavor, none of the guilt. Proof that keto eating can be absolutely delicious.",
    "Rich, flavorful {adj} keto creation {with_star} that doesn't sacrifice an ounce of taste for staying low-carb.",
]

AIR_FRYER_TEMPLATES = [
    "Crispy, golden {adj} perfection {with_star} — air fried until crunchy on the outside and tender within. All the crunch, fraction of the oil.",
    "Perfectly air-fried {adj} goodness {with_star} that comes out golden and impossibly crispy every single time.",
]

INSTANT_POT_TEMPLATES = [
    "Tender, flavorful {adj} magic {with_star} — pressure-cooked to absolute perfection in a fraction of the usual time. Weeknight dinners have never been this good.",
    "Fall-apart tender {adj} deliciousness {with_star} that the Instant Pot delivers in record time. One pot, one timer, one incredible meal.",
]

PANCAKE_TEMPLATES = [
    "Fluffy, golden {adj} stacks {with_star} — griddle-kissed and ready for a cascade of syrup. Weekend mornings were made for these.",
    "Light, airy {adj} breakfast {with_star} that puffs up on the griddle and melts in your mouth. Short stack? Never.",
]

GENERAL_TEMPLATES = [
    "A delicious homemade {adj} recipe {with_star} — simple enough for any night of the week but special enough to remember.",
    "Flavorful, satisfying {adj} comfort food {with_star}. The kind of recipe that gets dog-eared in the cookbook and passed down through generations.",
    "Homemade {adj} goodness {with_star} — made from scratch with real ingredients and a whole lot of love. This one's a keeper.",
    "A tried-and-true {adj} recipe {with_star} that proves the best meals don't need to be complicated — just made with care.",
]

TEMPLATE_MAP = {
    'cookie': COOKIE_TEMPLATES, 'muffin': MUFFIN_TEMPLATES,
    'bread': BREAD_TEMPLATES, 'cake': CAKE_TEMPLATES,
    'pie': PIE_TEMPLATES, 'square': SQUARE_TEMPLATES,
    'fudge': FUDGE_TEMPLATES, 'candy': CANDY_TEMPLATES,
    'pudding': PUDDING_TEMPLATES, 'dessert': DESSERT_TEMPLATES,
    'soup': SOUP_TEMPLATES, 'stew': STEW_TEMPLATES,
    'chili': CHILI_TEMPLATES, 'salad': SALAD_TEMPLATES,
    'dip': DIP_TEMPLATES, 'sauce': SAUCE_TEMPLATES,
    'pickle': PICKLE_TEMPLATES, 'pasta': PASTA_TEMPLATES,
    'pizza': PIZZA_TEMPLATES, 'casserole': CASSEROLE_TEMPLATES,
    'chicken': CHICKEN_TEMPLATES, 'beef': BEEF_TEMPLATES,
    'pork': PORK_TEMPLATES, 'fish': FISH_TEMPLATES,
    'rice': RICE_TEMPLATES, 'potato': POTATO_TEMPLATES,
    'vegetable': VEGETABLE_TEMPLATES, 'egg': EGG_TEMPLATES,
    'drink': DRINK_TEMPLATES, 'dressing': DRESSING_TEMPLATES,
    'frosting': FROSTING_TEMPLATES, 'snack': SNACK_TEMPLATES,
    'keto': KETO_TEMPLATES, 'air_fryer': AIR_FRYER_TEMPLATES,
    'instant_pot': INSTANT_POT_TEMPLATES, 'pancake': PANCAKE_TEMPLATES,
    'general': GENERAL_TEMPLATES,
}

# ── Adjective pools ──────────────────────────────────────────────────────────

SWEET_ADJS = ['rich', 'decadent', 'heavenly', 'luscious', 'indulgent', 'sweet', 'melt-in-your-mouth']
SAVORY_ADJS = ['savory', 'hearty', 'rustic', 'bold', 'comforting', 'robust', 'satisfying']
BAKED_ADJS = ['golden', 'golden-brown', 'warm', 'fragrant', 'buttery', 'toasty']
FRESH_ADJS = ['bright', 'fresh', 'vibrant', 'crisp', 'zesty', 'garden-fresh']

def pick_adjective(dish_type, title, seed_str):
    """Pick a fitting adjective based on dish type."""
    rng = random.Random(seed_str)
    sweet_types = {'cookie', 'cake', 'pie', 'square', 'fudge', 'candy', 'pudding', 'dessert', 'muffin', 'frosting', 'pancake'}
    fresh_types = {'salad', 'dressing', 'vegetable', 'dip'}
    baked_types = {'bread'}
    
    if dish_type in sweet_types:
        return rng.choice(SWEET_ADJS)
    elif dish_type in fresh_types:
        return rng.choice(FRESH_ADJS)
    elif dish_type in baked_types:
        return rng.choice(BAKED_ADJS)
    else:
        return rng.choice(SAVORY_ADJS)

# ── Main blurb generator ─────────────────────────────────────────────────────

def generate_creative_blurb(title, body, category):
    """Generate a creative, engaging blurb for a recipe."""
    ingredients = extract_ingredients(body)
    star_ings = get_star_ingredients(ingredients, title)
    dish_type = detect_dish_type(title, body, category, ingredients)
    
    # Build star ingredient strings
    if len(star_ings) >= 3:
        stars_str = f"{star_ings[0]}, {star_ings[1]}, and {star_ings[2]}"
        with_star = f"with {star_ings[0]} and {star_ings[1]}"
    elif len(star_ings) == 2:
        stars_str = f"{star_ings[0]} and {star_ings[1]}"
        with_star = f"with {star_ings[0]} and {star_ings[1]}"
    elif len(star_ings) == 1:
        stars_str = star_ings[0]
        with_star = f"with {star_ings[0]}"
    else:
        stars_str = "simple, honest ingredients"
        with_star = ""
    
    # Pick adjective
    seed = hashlib.md5(title.encode()).hexdigest()
    adj = pick_adjective(dish_type, title, seed)
    
    # Pick template
    templates = TEMPLATE_MAP.get(dish_type, GENERAL_TEMPLATES)
    rng = random.Random(seed)
    template = rng.choice(templates)
    
    # Fill template
    blurb = template.format(adj=adj, stars=stars_str.lower(), with_star=with_star.lower())
    
    # Clean up any double spaces or empty with_star artifacts
    blurb = re.sub(r'\s+', ' ', blurb).strip()
    blurb = blurb.replace('  ', ' ')
    
    # Ensure first char is uppercase
    blurb = blurb[0].upper() + blurb[1:]
    
    return blurb


# ── File processing ──────────────────────────────────────────────────────────

def is_blurb_already_good(desc, title):
    """Check if an existing blurb is already high quality."""
    if not desc:
        return False
    d = desc.lower()
    t = title.lower()
    
    # If it's basically just the title, it's bad
    if d.strip() == t.strip():
        return False
    
    # If it uses generic templates, it's bad
    bad_phrases = [
        'to perfection', 'a delicious', 'perfect for any occasion',
        'a homemade treat', 'a family favorite',
    ]
    if any(bp in d for bp in bad_phrases):
        # But some of these might be in genuinely good blurbs too
        # Only mark as bad if the blurb is also short
        if len(desc) < 100:
            return False
    
    # If it's long and doesn't use generic phrases, it's probably already good
    if len(desc) >= 100:
        return True
    
    # Medium length without generic phrases - probably OK
    if len(desc) >= 70:
        return True
    
    return False


def process_all_recipes(dry_run=False, force=False):
    """Process all recipe files and update blurbs."""
    recipes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "recipes")
    
    files = sorted(f for f in os.listdir(recipes_dir) if f.endswith('.md') and f != '_index.md')
    
    updated = 0
    skipped = 0
    
    for filename in files:
        filepath = os.path.join(recipes_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse frontmatter
        parts = content.split('---', 2)
        if len(parts) < 3:
            skipped += 1
            continue
        
        fm = parts[1]
        body = parts[2]
        
        # Get title, category, description
        title_m = re.search(r'title:\s*"([^"]*)"', fm)
        cat_m = re.search(r'categories:\s*\["([^"]*)"\]', fm)
        desc_m = re.search(r'description:\s*"([^"]*)"', fm)
        
        if not title_m:
            skipped += 1
            continue
        
        title = title_m.group(1)
        category = cat_m.group(1) if cat_m else ''
        old_desc = desc_m.group(1) if desc_m else ''
        
        # Skip if already good (unless forcing)
        if not force and is_blurb_already_good(old_desc, title):
            skipped += 1
            continue
        
        # Generate new blurb
        new_blurb = generate_creative_blurb(title, body, category)
        
        # Escape quotes
        new_blurb = new_blurb.replace('"', '\\"')
        
        if dry_run:
            print(f"  {title}")
            print(f"    OLD: {old_desc[:80]}")
            print(f"    NEW: {new_blurb[:120]}")
            print()
            updated += 1
        else:
            new_content = re.sub(
                r'description:\s*"[^"]*"',
                f'description: "{new_blurb}"',
                content,
                count=1
            )
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                updated += 1
                if updated % 50 == 0:
                    print(f"  ... {updated} recipes updated so far ...")
    
    print(f"\n=== DONE ===")
    print(f"Updated: {updated}")
    print(f"Skipped (already good): {skipped}")


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv or "--preview" in sys.argv
    force = "--force" in sys.argv
    
    if dry:
        print("=== DRY RUN (preview only) ===\n")
    
    process_all_recipes(dry_run=dry, force=force)
