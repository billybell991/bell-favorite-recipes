"""
Import Mom's Cookbook recipes from .doc files into Hugo markdown.
Reads .doc files using Word COM automation, parses title/ingredients/instructions,
and generates Hugo-compatible .md files with correct frontmatter.
"""

import sys
sys.path.append(r'C:\Users\bbell\AppData\Local\Programs\Python\Python312\Lib\site-packages\win32')
sys.path.append(r'C:\Users\bbell\AppData\Local\Programs\Python\Python312\Lib\site-packages\win32\lib')

import win32com.client
import os
import re
from datetime import datetime

SOURCE_DIR = r'C:\Stuff\Moms_Cookbook_New'
OUTPUT_DIR = r'C:\Stuff\Bell_Recipes_Project\content\recipes'


def slugify(text):
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def clean_title(raw_title):
    """Convert ALL CAPS title to Title Case."""
    # Remove extra spaces
    title = re.sub(r'\s+', ' ', raw_title.strip())
    # Title case, but keep small words lowercase
    words = title.split()
    small_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at',
                   'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was'}
    result = []
    for i, w in enumerate(words):
        if i == 0 or w.lower() not in small_words:
            result.append(w.capitalize())
        else:
            result.append(w.lower())
    return ' '.join(result)


def parse_recipe_text(text):
    """Parse raw text from a .doc file into title, ingredients, and instructions."""
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Split into lines, strip trailing whitespace
    lines = [line.rstrip() for line in text.split('\n')]

    # Remove trailing empty lines
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        return None, [], ''

    # Title is the first non-empty line
    title_line = ''
    content_start = 0
    for i, line in enumerate(lines):
        if line.strip():
            title_line = line.strip()
            content_start = i + 1
            break

    title = clean_title(title_line)

    # Skip blank lines after title
    while content_start < len(lines) and not lines[content_start].strip():
        content_start += 1

    # Now parse the rest into ingredients and instructions
    # Ingredients are typically tab-indented or tab-separated
    # Instructions are regular paragraph text
    ingredients = []
    instructions_lines = []
    in_instructions = False

    for line in lines[content_start:]:
        stripped = line.strip()
        if not stripped:
            if in_instructions:
                instructions_lines.append('')
            continue

        # Check if this line looks like ingredients (tab-separated columns or tab-indented)
        if not in_instructions and '\t' in line:
            # Split by tabs to get multi-column ingredients
            parts = [p.strip() for p in line.split('\t') if p.strip()]
            ingredients.extend(parts)
        elif not in_instructions and (
            stripped.startswith('-') or
            re.match(r'^\d+[\s./]', stripped) or
            re.match(r'^[½¼¾⅓⅔⅛]', stripped)
        ):
            # Looks like an ingredient line
            ingredients.append(stripped)
        else:
            # This is instructions text
            in_instructions = True
            instructions_lines.append(stripped)

    instructions = '\n\n'.join(
        para.strip() for para in '\n'.join(instructions_lines).split('\n\n')
        if para.strip()
    )

    return title, ingredients, instructions


def make_markdown(title, subcategory, ingredients, instructions, date_str):
    """Generate Hugo markdown content."""
    # Escape quotes in title and description
    safe_title = title.replace('"', '\\"')

    frontmatter = f'''---
title: "{safe_title}"
date: {date_str}
draft: false
categories: ["Mom's Cookbook"]
subcategory: "{subcategory}"
tags: ["{subcategory.lower()}"]
description: ""
source: ""
creditUrl: ""
credit: ""
prepTime: ""
cookTime: ""
servings: ""
image: ""
notes: ""
---'''

    body_parts = []
    if ingredients:
        body_parts.append('## Ingredients\n')
        for ing in ingredients:
            # Clean up the ingredient line
            ing = ing.strip()
            if ing.startswith('-'):
                body_parts.append(f'{ing}')
            else:
                body_parts.append(f'- {ing}')
        body_parts.append('')

    if instructions:
        body_parts.append('## Instructions\n')
        body_parts.append(instructions)
        body_parts.append('')

    return frontmatter + '\n' + '\n'.join(body_parts)


def check_duplicate(slug, output_dir):
    """Check if a recipe with this slug already exists."""
    path = os.path.join(output_dir, f'{slug}.md')
    if os.path.exists(path):
        return True
    return False


def main():
    # Collect all existing slugs to avoid duplicates
    existing = set()
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.md'):
            existing.add(f[:-3])

    # Initialize Word COM
    word = win32com.client.Dispatch('Word.Application')
    word.Visible = False

    now = datetime.now()
    date_str = now.strftime('%Y-%m-%dT%H:%M:%S-05:00')

    created = 0
    skipped = 0
    errors = 0
    dupes = 0

    try:
        for subdir in sorted(os.listdir(SOURCE_DIR)):
            subdir_path = os.path.join(SOURCE_DIR, subdir)
            if not os.path.isdir(subdir_path):
                continue

            subcategory = subdir  # Folder name IS the subcategory
            print(f'\n=== {subcategory} ===')

            for filename in sorted(os.listdir(subdir_path)):
                if not filename.lower().endswith(('.doc', '.docx')):
                    continue
                # Skip macOS resource fork files
                if filename.startswith('._'):
                    continue

                filepath = os.path.join(subdir_path, filename)
                try:
                    doc = word.Documents.Open(filepath)
                    text = doc.Content.Text
                    doc.Close(False)
                except Exception as e:
                    print(f'  ERROR reading {filename}: {e}')
                    errors += 1
                    continue

                title, ingredients, instructions = parse_recipe_text(text)
                if not title:
                    print(f'  SKIP (no title): {filename}')
                    skipped += 1
                    continue

                slug = slugify(title)
                if not slug:
                    slug = slugify(os.path.splitext(filename)[0])

                # Handle duplicates by appending subcategory
                if slug in existing:
                    slug = f'{slug}-moms-cookbook'
                if slug in existing:
                    slug = f'{slug}-{slugify(subcategory)}'
                if slug in existing:
                    print(f'  DUPE: {title} ({slug})')
                    dupes += 1
                    continue

                md_content = make_markdown(title, subcategory, ingredients, instructions, date_str)
                out_path = os.path.join(OUTPUT_DIR, f'{slug}.md')
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)

                existing.add(slug)
                created += 1
                print(f'  + {title} -> {slug}.md ({len(ingredients)} ingredients)')

    finally:
        word.Quit()

    print(f'\n=== DONE ===')
    print(f'Created: {created}')
    print(f'Skipped: {skipped}')
    print(f'Duplicates: {dupes}')
    print(f'Errors: {errors}')


if __name__ == '__main__':
    main()
