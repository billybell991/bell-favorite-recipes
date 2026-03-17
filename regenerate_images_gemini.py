"""
Regenerate all recipe images using Gemini/Imagen AI.

Replaces generic Pexels stock photos with AI-generated food photography
that's tailored to each recipe's actual title and ingredients.

Usage:
    python regenerate_images_gemini.py              # Process all recipes
    python regenerate_images_gemini.py --limit 5    # Process first 5 only (test run)
    python regenerate_images_gemini.py --dry-run    # Show prompts without generating
    python regenerate_images_gemini.py --resume     # Skip already-generated images

TODO: Run a full pass to regenerate images for ALL recipes (use --resume to skip already-done ones).
      Command: python regenerate_images_gemini.py --resume
"""

import os
import re
import sys
import time
import argparse
import logging
from pathlib import Path

from dotenv import load_dotenv
from google import genai as google_genai
from google.genai import types as genai_types

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
RELAY_ENV = Path(r"c:\Stuff\ai_relay_server\.env")
CONTENT_DIR = Path(__file__).parent / "content" / "recipes"
IMAGE_DIR = Path(__file__).parent / "static" / "images" / "recipes"
LOG_FILE = Path(__file__).parent / "image_regen_log.txt"

# Model choices (in order of preference)
IMAGE_MODEL = "imagen-4.0-fast-generate-001"
FALLBACK_MODEL = "gemini-2.5-flash-image"  # Supports image output
ASPECT_RATIO = "16:9"  # Landscape for food photos

# Rate limiting
DELAY_BETWEEN_CALLS = 4.0  # seconds between API calls
MAX_RETRIES = 2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger("regen-images")


# ---------------------------------------------------------------------------
# Gemini client setup
# ---------------------------------------------------------------------------
def init_client():
    load_dotenv(RELAY_ENV)
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        log.error("GEMINI_API_KEY not found in %s", RELAY_ENV)
        sys.exit(1)
    client = google_genai.Client(api_key=api_key)
    log.info("Gemini client initialized")
    return client


# ---------------------------------------------------------------------------
# Recipe parsing
# ---------------------------------------------------------------------------
def parse_recipe(filepath: Path) -> dict:
    """Extract frontmatter fields and ingredients from a recipe .md file."""
    text = filepath.read_text(encoding="utf-8")

    # Split frontmatter
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}

    fm = parts[1]
    body = parts[2]

    def get_field(name):
        m = re.search(rf'^{name}:\s*"(.*)"\s*$', fm, re.MULTILINE)
        return m.group(1) if m else ""

    def get_list_field(name):
        m = re.search(rf'^{name}:\s*\[(.*?)\]\s*$', fm, re.MULTILINE)
        if m:
            return [x.strip().strip('"') for x in m.group(1).split(",") if x.strip()]
        return []

    # Extract first N ingredients from body
    ingredients = []
    in_ingredients = False
    for line in body.split("\n"):
        if re.match(r"^##\s*Ingredients", line, re.IGNORECASE):
            in_ingredients = True
            continue
        if in_ingredients:
            if line.startswith("##"):
                break
            item = re.sub(r"^[-*]\s*", "", line).strip()
            if item:
                ingredients.append(item)

    return {
        "title": get_field("title"),
        "categories": get_list_field("categories"),
        "description": get_field("description"),
        "image": get_field("image"),
        "slug": filepath.stem,
        "filepath": filepath,
        "ingredients": ingredients[:8],  # First 8 for prompt context
    }


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------
def build_food_prompt(recipe: dict) -> str:
    """Build a vivid food photography prompt from recipe data."""
    title = recipe["title"]
    ingredients = recipe.get("ingredients", [])
    category = recipe["categories"][0] if recipe.get("categories") else ""
    description = recipe.get("description", "").strip()

    # Build ingredient context (first 6 ingredients)
    ing_text = ""
    if ingredients:
        ing_text = f" Key ingredients: {', '.join(ingredients[:6])}."

    # Use the recipe description to give Gemini a stronger visual anchor
    desc_text = ""
    if description:
        desc_text = f" About this dish: {description}"

    # Category-specific styling hints
    style_hint = ""
    if "Keto" in category:
        style_hint = " Low-carb presentation, fresh greens and avocado tones."
    elif "Air Fryer" in category:
        style_hint = " Golden crispy textures, emphasize the crunch."
    elif "Instant Pot" in category:
        style_hint = " Steaming, hearty, comfort food feel."
    elif "Mom" in category or "Wedding" in category or "Family" in category:
        style_hint = " Homestyle, rustic, comforting kitchen setting."

    prompt = (
        f"Professional food photography of {title}.{desc_text} "
        f"Beautifully plated and styled, shot from a 45-degree angle with soft natural lighting. "
        f"Warm, inviting kitchen scene with subtle background blur (bokeh). "
        f"The dish should look delicious, appetizing, and true to a real homemade version.{ing_text}"
        f"{style_hint} "
        f"No text, no watermarks, no labels, no logos. Photorealistic style."
    )
    return prompt


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------
def generate_image(client, prompt: str, output_path: Path, model: str = IMAGE_MODEL) -> bool:
    """Generate and save a single image. Returns True on success."""
    try:
        if model.startswith("imagen"):
            result = client.models.generate_images(
                model=model,
                prompt=prompt,
                config=genai_types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=ASPECT_RATIO,
                ),
            )
            if not result.generated_images:
                return False
            image_data = result.generated_images[0].image.image_bytes
        else:
            result = client.models.generate_content(
                model=model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )
            image_data = None
            if result.candidates:
                for part in result.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                        image_data = part.inline_data.data
                        break
            if not image_data:
                return False

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_data)
        size_kb = len(image_data) / 1024
        log.info("  Saved: %s (%.0f KB)", output_path.name, size_kb)
        return True

    except Exception as e:
        err_str = str(e)
        if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
            log.warning("  Quota exhausted for model %s", model)
            raise  # Let caller handle quota exhaustion
        log.warning("  Generation failed: %s", e)
        return False


def update_frontmatter(filepath: Path, new_image_path: str):
    """Update the image field in a recipe's frontmatter."""
    text = filepath.read_text(encoding="utf-8")
    # Replace the image line
    updated = re.sub(
        r'^image:\s*".*"',
        f'image: "{new_image_path}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    filepath.write_text(updated, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Regenerate recipe images with Gemini AI")
    parser.add_argument("--limit", type=int, default=0, help="Process only N recipes (0=all)")
    parser.add_argument("--dry-run", action="store_true", help="Show prompts without generating")
    parser.add_argument("--resume", action="store_true", help="Skip recipes with existing generated images")
    parser.add_argument("--start-from", type=str, default="", help="Start from this slug (alphabetically)")
    args = parser.parse_args()

    # Collect all recipes
    recipe_files = sorted(CONTENT_DIR.glob("*.md"))
    recipe_files = [f for f in recipe_files if f.name != "_index.md"]
    log.info("Found %d recipe files", len(recipe_files))

    client = None
    if not args.dry_run:
        client = init_client()

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    success = 0
    failed = 0
    skipped = 0
    imagen_quota_hit = False  # Once Imagen quota is exhausted, skip it for all remaining

    for i, filepath in enumerate(recipe_files):
        recipe = parse_recipe(filepath)
        if not recipe or not recipe.get("title"):
            log.warning("Skipping %s (can't parse)", filepath.name)
            skipped += 1
            continue

        slug = recipe["slug"]

        # Start-from filter
        if args.start_from and slug < args.start_from:
            continue

        # Resume: skip if local image already exists
        out_path = IMAGE_DIR / f"{slug}.png"
        if args.resume and out_path.exists():
            skipped += 1
            continue

        prompt = build_food_prompt(recipe)
        count = success + failed + skipped + 1
        total = len(recipe_files)
        log.info("[%d/%d] %s", count, total, recipe["title"])

        if args.dry_run:
            print(f"\n{'='*60}")
            print(f"Recipe: {recipe['title']}")
            print(f"Slug:   {slug}")
            print(f"Prompt: {prompt}")
            success += 1
            if args.limit and success >= args.limit:
                break
            continue

        # Generate with retry + fallback
        ok = False
        quota_hit = False
        models_to_try = [FALLBACK_MODEL] if imagen_quota_hit else [IMAGE_MODEL, FALLBACK_MODEL]

        for model in models_to_try:
            try:
                ok = generate_image(client, prompt, out_path, model=model)
            except Exception:
                # Quota exhausted
                if model == IMAGE_MODEL:
                    imagen_quota_hit = True
                    log.info("  Imagen quota hit, switching to %s", FALLBACK_MODEL)
                    continue
                else:
                    quota_hit = True
                    break
            if ok:
                break
            time.sleep(DELAY_BETWEEN_CALLS)

        if quota_hit:
            log.warning("All model quotas exhausted. Stopping. Use --resume to continue later.")
            break

        if ok:
            # Update frontmatter to point to local image
            new_image = f"images/recipes/{slug}.png"
            update_frontmatter(filepath, new_image)
            success += 1
            log.info("  Updated frontmatter → %s", new_image)
        else:
            failed += 1
            log.error("  FAILED: %s", recipe["title"])

        if args.limit and (success + failed) >= args.limit:
            break

        time.sleep(DELAY_BETWEEN_CALLS)

    log.info("Done! Success: %d, Failed: %d, Skipped: %d", success, failed, skipped)


if __name__ == "__main__":
    main()
