"""
Assign Pexels CDN images to all recipes based on keyword matching.
Uses curated photo IDs collected from Pexels search results.
"""
import os
import re
import random

# CDN URL template
def pexels_url(photo_id):
    return f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=600"

# Some photos have descriptive filenames instead of standard pexels-photo-{id} format
SPECIAL_URLS = {
    60616: "https://images.pexels.com/photos/60616/fried-chicken-chicken-fried-crunchy-60616.jpeg?auto=compress&cs=tinysrgb&w=600",
    361184: "https://images.pexels.com/photos/361184/asparagus-steak-veal-steak-veal-361184.jpeg?auto=compress&cs=tinysrgb&w=600",
    3660: "https://images.pexels.com/photos/3660/food-restaurant-dinner-lunch.jpg?auto=compress&cs=tinysrgb&w=600",
    65175: "https://images.pexels.com/photos/65175/pexels-photo-65175.jpeg?auto=compress&cs=tinysrgb&w=600",
    45202: "https://images.pexels.com/photos/45202/brownie-dessert-cake-sweet-45202.jpeg?auto=compress&cs=tinysrgb&w=600",
    65882: "https://images.pexels.com/photos/65882/chocolate-dark-coffee-confiserie-65882.jpeg?auto=compress&cs=tinysrgb&w=600",
}

def get_url(photo_id):
    if photo_id in SPECIAL_URLS:
        return SPECIAL_URLS[photo_id]
    return pexels_url(photo_id)

# Curated photo pools by food category (all from Pexels search results)
PHOTO_POOLS = {
    "chicken": [35285814, 2338407, 2116094, 145804, 106343, 10648379, 5704254, 2232433, 1059943, 6163332],
    "fried chicken": [60616, 2232433, 5704254, 10648379],
    "cake": [291528, 1869342, 4109996, 3740237, 4110007, 1414234, 2144200, 1291712, 2144112, 140831, 1854652, 3913295],
    "cookies": [1020585, 298485, 2377471, 230325, 1342295, 859904, 4110538, 271458, 752503],
    "cookie": [1020585, 298485, 2377471, 230325, 1342295, 859904, 4110538, 271458, 752503],
    "bread": [6608542, 1555813, 1383908, 1571073, 209206, 1070461, 600620, 2067626, 1755785, 1374586, 4197920, 7693953],
    "rice": [1410235, 674574, 2641886],
    "dip": [1200354, 4411802, 6004783, 1200362, 9134587, 5848734, 6004794],
    "soup": [2664221, 5249632, 30635687, 29097082, 12077982, 3559899, 539451, 884600, 3296680, 1907227, 1731535, 724667, 1703272],
    "salad": [551997, 3070968, 5713762, 1332313, 3026019, 3109596, 1211887, 1152237, 4062511, 2097090, 1059905, 3599973, 764925, 2862154],
    "beef": [65175, 27305267, 7627420, 765082, 19774527, 4661503, 17942952, 7741852, 2098110, 8753745, 1618906],
    "steak": [361184, 65175, 27305267, 7627420, 35116032, 765082, 2098110, 8753745, 7741852],
    "chocolate": [1346341, 1343504, 14107, 960540, 697571, 4110008, 65882, 1998633, 918328, 2567854],
    "casserole": [32125954, 29535636, 806357, 7625714, 4078163, 5639274, 32125955, 6163259, 2337842, 1707917],
    "lasagna": [8971046, 35800369, 5949923, 5949921, 29535636, 4078163, 5724557],
    "potato": [31398314, 4661177],
    "muffin": [1414234, 2067626, 1070461, 1383908],
    "muffins": [1414234, 2067626, 1070461, 1383908],
    "brownie": [45202, 960540, 697571, 918328],
    "brownies": [45202, 960540, 697571, 918328],
    "cheesecake": [291528, 1854652, 3740193, 1869342, 2144200, 140831],
    "pie": [291528, 1854652, 3740193, 1869342, 2144200, 140831, 3913295],
    "pasta": [5724556, 11889305, 806357, 29535636],
    "spaghetti": [5724556, 11889305, 765082],
    "noodle": [1907227, 1731535, 884600, 1395319, 6646082, 28907756],
    "pork": [65175, 1618906, 7627420, 4661503, 7741852, 2098110],
    "ham": [65175, 1618906, 4661503],
    "bacon": [65175, 2098110, 4661503, 7741852],
    "fish": [3599973, 970105, 1234535, 8753745],
    "salmon": [3599973, 970105, 8753745],
    "shrimp": [970105, 3296680, 6646082, 1234535],
    "wings": [60616, 2232433, 5704254, 2338407, 10648379],
    "chili": [539451, 3559899, 2664221, 2365944, 724667],
    "stew": [16699418, 724667, 539451, 2664221, 30635687, 1703272],
    "broccoli": [3070968, 551997, 3109596, 3026019, 3872249],
    "apple": [1869342, 1414234, 3913295, 140831, 2144200],
    "strawberry": [1414234, 3913295, 960540, 12927134, 10309477],
    "lemon": [27305267, 28907756, 1234535],
    "banana": [1383908, 2067626, 1070461, 1755785],
    "corn": [3070968, 551997, 4198421, 3296680],
    "oatmeal": [1383908, 1070461, 1555813, 209206],
    "oat": [1383908, 1070461, 1555813, 209206],
    "smoothie": [3872249, 5249632],
    "french toast": [1383908, 1555813, 209206, 600620],
    "toast": [1383908, 1555813, 209206, 600620],
    "pancake": [1383908, 1555813, 1070461],
    "waffle": [2819088, 1383908],
    "doughnut": [271458, 1020585, 752503, 298485],
    "donut": [271458, 1020585, 752503, 298485],
    "enchilada": [4198421, 1707917, 5639274],
    "burger": [65175, 2098110, 3660],
    "sandwich": [251599, 1152237, 262978],
    "pizza": [4198421, 5639274, 11889305],
    "taco": [4198421, 1707917],
    "wrap": [551997, 1332313, 1211887],
    "crab": [970105, 6646082, 3296680],
    "turkey": [6163332, 2338407, 145804, 1059943],
    "cheese": [3070968, 3109596, 32125954, 32125955, 806357, 7625714],
    "mac": [806357, 5724556],
    "macaroni": [806357, 5724556],
    "biscuit": [1383908, 1555813, 271458, 752503],
    "scone": [1383908, 1555813, 271458],
    "roll": [1383908, 1555813, 1571073, 6608542],
    "fudge": [65882, 1998633, 918328, 1346341],
    "pudding": [2144200, 2144112, 1854652, 3740193],
    "custard": [2144200, 2144112, 1854652],
    "cobbler": [10309477, 3913295, 140831],
    "crisp": [10309477, 3913295, 140831],
    "crumble": [10309477, 3913295],
    "dumpling": [955137, 884600, 1907227],
    "bean": [30635687, 539451, 724667, 3559899],
    "chowder": [539451, 724667, 1703272, 12077982],
    "bisque": [539451, 29097082, 6072108],
    "jerky": [65175, 4661503, 7741852],
    "granola": [1383908, 1070461],
    "jam": [10309477, 3913295, 1414234],
    "jelly": [10309477, 3913295],
    "syrup": [1383908, 1555813],
    "sauce": [539451, 2365944, 2098110],
    "marinade": [65175, 2098110, 7741852],
    "glaze": [291528, 1869342, 271458],
    "frosting": [291528, 1869342, 1414234, 4109996],
    "icing": [291528, 1869342, 1414234],
    "candy": [65882, 918328, 271458, 1020585],
    "caramel": [697571, 1854652, 1998633],
    "toffee": [65882, 918328, 1998633],
    "truffle": [65882, 918328, 1346341],
    "mousse": [1854652, 697571, 1998633, 2567854],
    "meringue": [140831, 2144200, 3913295],
    "soufflé": [2144200, 2144112],
    "souffle": [2144200, 2144112],
    "bruschetta": [251599, 1152237, 326278],
    "guacamole": [1200354, 5848734, 6004783, 4411802],
    "hummus": [1200354, 5848734, 6004783],
    "salsa": [1200354, 6004783, 4411802, 5848734],
    "pesto": [11889305, 29535636, 5949921],
    "quiche": [5639274, 7625714, 4198421],
    "frittata": [5639274, 7625714],
    "omelet": [5639274, 7625714, 4198421],
    "egg": [2092903, 5639274, 7625714],
    "meatball": [5724556, 11889305, 765082],
    "meatloaf": [1618906, 1707917, 65175],
    "roast": [6163332, 1618906, 2098110, 65175],
    "bbq": [7741852, 2098110, 65175, 4661503],
    "barbecue": [7741852, 2098110, 65175],
    "grill": [361184, 7741852, 2098110, 65175],
    "air fryer": [60616, 35285814, 2232433, 5704254, 31398314],
    "slow cooker": [16699418, 724667, 2664221, 1618906],
    "crock pot": [16699418, 724667, 2664221],
    "instant pot": [16699418, 2664221, 724667],
    "vegetable": [3070968, 551997, 3109596, 4198421, 3026019],
    "veggie": [3070968, 551997, 3109596, 3026019],
    "fruit": [1414234, 3913295, 10309477],
    "berry": [1414234, 3913295, 12927134, 10309477],
    "blueberry": [1414234, 3913295, 291528],
    "raspberry": [4109996, 2567854, 918328],
    "cranberry": [1414234, 3913295],
    "peach": [10309477, 3913295, 140831],
    "pumpkin": [29097082, 6072108],
    "squash": [29097082, 6072108, 3070968],
    "zucchini": [3070968, 551997, 4198421],
    "eggplant": [1707917, 19145680, 4198421],
    "mushroom": [765082, 3070968, 551997],
    "spinach": [1152237, 3070968, 551997, 3026019],
    "avocado": [1211887, 551997, 1332313],
    "tomato": [539451, 3832330, 551997, 3070968],
    "pepper": [65175, 4198421, 3070968],
    "onion": [3070968, 551997, 4198421],
    "garlic": [16699418, 3559899, 65175],
    "herb": [29535636, 5949921, 3599973],
    "cinnamon": [271458, 1020585, 1383908],
    "vanilla": [271458, 1020585, 2144200],
    "nutmeg": [271458, 1383908],
    "ginger": [271458, 1020585, 884600],
    "honey": [1383908, 1070461, 271458],
    "maple": [1383908, 1555813],
    "coconut": [2862154, 674574],
    "almond": [1343504, 1383908],
    "pecan": [1383908, 140831, 3913295],
    "walnut": [1383908, 140831],
    "peanut": [1383908, 1070461],
    "cashew": [674574, 1410235],
}

# Generic food photos for recipes that don't match any keyword
GENERIC_FOOD = [
    1640777,   # food spread
    1565982,   # delicious food plate
    376464,    # food platter
    958545,    # cooking ingredients
    1099680,   # food photography
    461198,    # various dishes
    1279330,   # dinner table
    842571,    # cooking
    1640774,   # food spread
    1099682,   # food setup
]

def get_best_photo(title, used_photos):
    """Find the best matching photo for a recipe title."""
    title_lower = title.lower()

    # Try to find the most specific keyword match first
    # Sort keywords by length (longest first) for more specific matches
    sorted_keywords = sorted(PHOTO_POOLS.keys(), key=len, reverse=True)

    best_pool = None
    for keyword in sorted_keywords:
        # Use word boundary matching for short keywords to avoid false matches
        if len(keyword) <= 3:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, title_lower):
                best_pool = PHOTO_POOLS[keyword]
                break
        else:
            if keyword in title_lower:
                best_pool = PHOTO_POOLS[keyword]
                break

    if best_pool is None:
        best_pool = GENERIC_FOOD

    # Pick a photo that hasn't been used too many times
    # Count usage and prefer less-used photos
    pool_with_counts = []
    for pid in best_pool:
        count = used_photos.get(pid, 0)
        pool_with_counts.append((pid, count))

    # Sort by usage count (least used first), break ties randomly
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
    already_has = 0
    used_photos = {}

    random.seed(42)  # Reproducible results

    for filename in files:
        filepath = os.path.join(recipes_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if already has a non-empty image
        image_match = re.search(r'^image:\s*"(.+?)"', content, re.MULTILINE)
        if image_match and image_match.group(1).startswith("http"):
            already_has += 1
            continue

        # Extract title
        title_match = re.search(r'^title:\s*"(.+?)"', content, re.MULTILINE)
        if not title_match:
            skipped += 1
            continue

        title = title_match.group(1)
        photo_url = get_best_photo(title, used_photos)

        # Replace the image line
        new_content = re.sub(
            r'^image:\s*""',
            f'image: "{photo_url}"',
            content,
            count=1,
            flags=re.MULTILINE
        )

        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            updated += 1
            if updated <= 10:
                print(f"  {filename}: {title} -> photo assigned")
            elif updated == 11:
                print("  ... (continuing)")
        else:
            skipped += 1

    print(f"\nDone!")
    print(f"  Updated: {updated}")
    print(f"  Already had image: {already_has}")
    print(f"  Skipped: {skipped}")
    print(f"  Unique photos used: {len(used_photos)}")

    # Show distribution
    print(f"\nPhoto usage distribution:")
    usage_counts = sorted(used_photos.values(), reverse=True)
    if usage_counts:
        print(f"  Max uses of single photo: {usage_counts[0]}")
        print(f"  Min uses of single photo: {usage_counts[-1]}")
        print(f"  Average: {sum(usage_counts)/len(usage_counts):.1f}")


if __name__ == "__main__":
    main()
