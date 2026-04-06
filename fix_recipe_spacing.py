import os
import re
import sys

RECIPE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "recipes")

UNITS = [
    'teaspoons', 'teaspoon', 'tablespoons', 'tablespoon', 'tbsp', 'tsp',
    'cups', 'cup', 'ounces', 'ounce', 'oz', 'pounds', 'pound', 'lbs', 'lb',
    'grams', 'gram', 'kg', 'ml', 'liters', 'liter',
    'cloves', 'clove', 'slices', 'slice', 'pinches', 'pinch',
    'packages', 'package', 'pkgs', 'pkg',
    'containers', 'container', 'quarts', 'quart',
    'gallons', 'gallon', 'pints', 'pint', 'each', 'scant',
    'degrees', 'minutes', 'hours', 'seconds', 'inches', 'inch', 'feet',
]
UNITS.sort(key=len, reverse=True)

# Compiled patterns
UNIT_REGEX = re.compile(
    r'(?i)(\b\d+(?:[\s\-\/\.]\d+)?\s*)\b(' + '|'.join(re.escape(u) for u in UNITS) + r')([a-zA-Z]{2,})'
)
# multi-digit number immediately followed by 3+ lowercase letters (not ordinal endings: st/nd/rd/th)
NUMBER_WORD_REGEX = re.compile(r'(\d+)((?!st\b|nd\b|rd\b|th\b)[a-z]{3,})')
# ordinal (4th) immediately followed by a letter — "4thcup" → "4th cup"
ORDINAL_WORD_REGEX = re.compile(r'(\d(?:st|nd|rd|th))([a-zA-Z])')
# lowercase letter immediately followed by a digit — "to325" → "to 325"
# Exclude dimension "x" between digits: 9x13, 13x9, 8x8x2
WORD_NUMBER_REGEX = re.compile(r'(?<=[a-zA-Z])([a-wyz])(\d+)|([a-z])(x)(\d)')
PAREN_OPEN_REGEX = re.compile(r'([a-zA-Z0-9])\((?!s\))')
PAREN_CLOSE_REGEX = re.compile(r'\)([a-zA-Z0-9])')

# Known false-positive word+number combos to skip (e.g. "No. 2" abbrev, etc.)
_URL_RE = re.compile(r'https?://')


def is_url_context(line):
    return bool(_URL_RE.search(line))


def fix_unit_match(m):
    prefix, unit, suffix = m.group(1), m.group(2), m.group(3)
    combined = unit + suffix
    if combined.lower() in UNITS or suffix.lower() in ('s', 'es'):
        return m.group(0)
    return f"{prefix}{unit} {suffix}"


def fix_line(line):
    # Skip URLs — too many digit/letter combos in paths/params
    if is_url_context(line):
        return line

    # 1. ordinal immediately followed by word: "4thcup" → "4th cup"
    line = ORDINAL_WORD_REGEX.sub(r'\1 \2', line)

    # 2. digit immediately followed by 3+ letters (not ordinals): "325degrees" → "325 degrees"
    line = NUMBER_WORD_REGEX.sub(r'\1 \2', line)

    # 3. unit word run-on after number: "2 tbspolive" → "2 tbsp olive"
    line = UNIT_REGEX.sub(fix_unit_match, line)

    # 4. lowercase letter immediately followed by digit: "to325" → "to 325"
    #    But not dimension x: 9x13 stays 9x13
    def word_num_sub(m):
        if m.group(3):  # it matched the x-dimension branch — leave it
            return m.group(0)
        return f"{m.group(1)} {m.group(2)}"
    line = WORD_NUMBER_REGEX.sub(word_num_sub, line)

    # 5. Missing space before ( — "Fahrenheit(oven)" but not "(s)"
    line = PAREN_OPEN_REGEX.sub(r'\1 (', line)

    # 6. Missing space after )
    line = PAREN_CLOSE_REGEX.sub(r') \1', line)

    return line


def split_frontmatter(content):
    """Return (frontmatter_block, body) splitting on the closing --- of frontmatter."""
    if content.startswith('---'):
        end = content.find('\n---', 3)
        if end != -1:
            cutoff = end + 4  # include the closing ---\n
            return content[:cutoff], content[cutoff:]
    return '', content


def fix_standalone_colons(body):
    """Remove lines that consist only of a colon (artifact from scraping)."""
    return re.sub(r'\n[ \t]*:[ \t]*\n', '\n', body)


def should_fix_line(line):
    """Return True for body lines we want to apply spacing fixes to."""
    stripped = line.strip()
    # ingredient lines (- item)
    if stripped.startswith('- '):
        return True
    # numbered instruction lines (1. text, 2. text, etc.)
    if re.match(r'^\d+\.\s', stripped):
        return True
    # plain paragraph lines in body (not blank, not headers, not code fences)
    if stripped and not stripped.startswith('#') and not stripped.startswith('```') \
            and not stripped.startswith('|') and not stripped.startswith('['):
        return True
    return False


def process_file(filepath, dry_run=True):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    frontmatter, body = split_frontmatter(content)

    new_body = fix_standalone_colons(body)

    lines = new_body.split('\n')
    new_lines = []
    for line in lines:
        if should_fix_line(line):
            new_line = fix_line(line)
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    new_body = '\n'.join(new_lines)
    new_content = frontmatter + new_body

    if new_content != content:
        if dry_run:
            # Show a diff-style summary
            old_lines = content.splitlines()
            new_lines_all = new_content.splitlines()
            for i, (o, n) in enumerate(zip(old_lines, new_lines_all), 1):
                if o != n:
                    print(f"  [{os.path.basename(filepath)}:{i}]")
                    print(f"    OLD: {o}")
                    print(f"    NEW: {n}")
            # catch length difference (removal of colon lines)
            if len(old_lines) != len(new_lines_all):
                print(f"  [{os.path.basename(filepath)}] line count changed: {len(old_lines)} → {len(new_lines_all)}")
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
    return False


def main():
    dry_run = '--apply' not in sys.argv
    print(f"Scanning recipes in: {RECIPE_DIR}")
    print(f"Mode: {'DRY RUN (pass --apply to write changes)' if dry_run else 'APPLY'}\n")

    scanned = fixed = 0
    for root, dirs, files in os.walk(RECIPE_DIR):
        for fname in sorted(files):
            if fname.endswith('.md'):
                fp = os.path.join(root, fname)
                result = process_file(fp, dry_run=dry_run)
                scanned += 1
                if result:
                    fixed += 1
                    print(f"Fixed: {fname}")

    if dry_run:
        print(f"\nScanned {scanned} files. Run with --apply to write changes.")
    else:
        print(f"\nScanned {scanned} files, fixed {fixed}.")

if __name__ == "__main__":
    main()
