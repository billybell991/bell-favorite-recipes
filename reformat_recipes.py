"""
Reformat recipe markdown files to have consistent ## Ingredients and ## Instructions sections.
Handles the common patterns found in the Mom's Cookbook and Wedding Cookbook recipes:
  - Bullet list of ingredients followed by paragraph instructions
  - Sometimes a preamble before ingredients (e.g. "Submitted by..." or "Preheat oven...")
  - Notes, credits, variations at the end
"""
import os
import re
import sys

RECIPE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "recipes")


def has_sections(body):
    """Check if the body already has ## Ingredients or ## Instructions headers."""
    return bool(re.search(r"^##\s*(Ingredients|Instructions)", body, re.MULTILINE | re.IGNORECASE))


def is_ingredient_line(line):
    """Detect if a line looks like an ingredient (starts with - and has food/measurement words)."""
    stripped = line.strip()
    if not stripped.startswith("- "):
        return False
    # Filter out lines that are clearly instructions disguised as bullets
    content = stripped[2:].strip().lower()
    # If it starts with a verb, it's probably an instruction
    instruction_starters = [
        "preheat", "combine", "mix", "stir", "bake", "cook", "place",
        "pour", "add", "spread", "remove", "let", "serve", "arrange",
        "roll", "cut", "drain", "cover", "heat", "bring", "set",
        "wash", "peel", "slice", "chop", "mash", "beat", "whisk",
        "fold", "grease", "spray", "line", "turn", "flip", "cool",
    ]
    first_word = content.split()[0] if content.split() else ""
    if first_word in instruction_starters:
        return False
    return True


def is_bullet_line(line):
    """Check if a line is any bullet point."""
    return line.strip().startswith("- ")


def split_body(body):
    """
    Split the recipe body into (preamble, ingredients, instructions, notes).
    Returns strings for each section.
    """
    lines = body.split("\n")

    # Find runs of ingredient-like bullet lines
    ingredient_start = None
    ingredient_end = None
    in_ingredients = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        if is_ingredient_line(line):
            if not in_ingredients:
                ingredient_start = i
                in_ingredients = True
            ingredient_end = i
        elif in_ingredients:
            # We've left the ingredient block
            # But allow small gaps (empty lines between ingredient groups)
            # Check if the next non-empty line is also an ingredient
            look_ahead_is_ingredient = False
            for j in range(i, min(i + 3, len(lines))):
                if lines[j].strip() and is_ingredient_line(lines[j]):
                    look_ahead_is_ingredient = True
                    break
                elif lines[j].strip() and not is_ingredient_line(lines[j]):
                    break
            if look_ahead_is_ingredient:
                continue
            else:
                in_ingredients = False

    if ingredient_start is None:
        # No clear ingredient list found - return body as-is
        return None, None, None, None

    # Build sections
    preamble_lines = lines[:ingredient_start]
    ingredient_lines = lines[ingredient_start:ingredient_end + 1]
    rest_lines = lines[ingredient_end + 1:]

    # Clean up preamble (remove leading/trailing blank lines)
    preamble = "\n".join(preamble_lines).strip()

    # Clean up ingredients
    ingredients = "\n".join(ingredient_lines).strip()

    # Process the rest into instructions and notes
    rest_text = "\n".join(rest_lines).strip()

    # Try to separate notes/credits from instructions
    instructions = []
    notes = []
    in_notes = False

    for line in rest_lines:
        stripped = line.strip()
        lower = stripped.lower()

        # Detect notes/credits/variations section
        if (lower.startswith("note:") or lower.startswith("notes:") or
            lower.startswith("credit") or lower.startswith("here's a link") or
            lower.startswith("variation") or lower.startswith("yield:") or
            lower.startswith("tip:") or lower.startswith("tips:") or
            lower.startswith("submitted by") or
            (stripped.startswith("[") and "http" in stripped)):
            in_notes = True

        if in_notes:
            notes.append(line)
        else:
            instructions.append(line)

    instructions_text = "\n".join(instructions).strip()
    notes_text = "\n".join(notes).strip()

    return preamble, ingredients, instructions_text, notes_text


def reformat_body(body):
    """Add ## Ingredients and ## Instructions headers to the body."""
    preamble, ingredients, instructions, notes = split_body(body)

    if ingredients is None:
        # Couldn't parse - leave as-is
        return body

    parts = []

    if preamble:
        parts.append(preamble)
        parts.append("")

    parts.append("## Ingredients")
    parts.append("")
    parts.append(ingredients)
    parts.append("")

    if instructions:
        parts.append("## Instructions")
        parts.append("")
        parts.append(instructions)
        parts.append("")

    if notes:
        parts.append(notes)
        parts.append("")

    return "\n".join(parts)


def process_recipes(dry_run=False, category_filter=None):
    """Process all recipe files that need reformatting."""
    files = sorted(f for f in os.listdir(RECIPE_DIR)
                   if f.endswith(".md") and f != "_index.md")

    reformatted = 0
    skipped_has_sections = 0
    skipped_no_ingredients = 0
    total = 0

    for filename in files:
        filepath = os.path.join(RECIPE_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Split frontmatter and body
        parts = content.split("---", 2)
        if len(parts) < 3:
            continue

        fm = parts[1]
        body = parts[2]

        # Category filter
        if category_filter:
            cat_match = re.search(r'categories:\s*\["([^"]*)"\]', fm)
            if not cat_match or category_filter.lower() not in cat_match.group(1).lower():
                continue

        total += 1

        # Skip if already has proper sections
        if has_sections(body):
            skipped_has_sections += 1
            continue

        # Try to reformat
        new_body = reformat_body(body)

        if new_body == body:
            skipped_no_ingredients += 1
            continue

        if dry_run:
            title_match = re.search(r'title:\s*"([^"]*)"', fm)
            title = title_match.group(1) if title_match else filename
            print(f"  WOULD REFORMAT: {title}")
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"---{fm}---\n{new_body}")

        reformatted += 1

    print(f"\nTotal: {total}")
    print(f"Reformatted: {reformatted}")
    print(f"Already had sections: {skipped_has_sections}")
    print(f"Could not parse: {skipped_no_ingredients}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    category = None
    for arg in sys.argv[1:]:
        if arg.startswith("--category="):
            category = arg.split("=", 1)[1]

    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Category: {category or 'ALL'}")
    process_recipes(dry_run=dry_run, category_filter=category)
