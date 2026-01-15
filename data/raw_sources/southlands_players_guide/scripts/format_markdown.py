#!/usr/bin/env python3
"""
Markdown Formatter for Southlands Player's Guide

Processes raw extracted markdown and reformats it with proper structure,
headers, lists, and tables to pass markdown linting.
"""

import re
from pathlib import Path
from typing import List, Tuple

SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = RAW_DIR / "output"


def clean_text(text: str) -> str:
    """Clean up common PDF extraction artifacts."""
    # Fix hyphenation at line breaks
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    # Fix em-dashes
    text = text.replace('‑', '-')
    # Remove page break artifacts
    text = re.sub(r'\n---\n+', '\n\n', text)
    # Fix multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def detect_headers(lines: List[str]) -> List[Tuple[int, str, int]]:
    """Detect potential headers (ALL CAPS lines, specific patterns)."""
    headers = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        # ALL CAPS headers (like CATFOLK, GNOLLS, etc.)
        if stripped.isupper() and len(stripped) > 2 and len(stripped) < 50:
            headers.append((i, stripped, 2))  # Level 2 header
        # Title case headers followed by traits
        elif re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+$', stripped):
            headers.append((i, stripped, 3))  # Level 3 header
    return headers


def format_trait_block(text: str) -> str:
    """Format a race trait block with proper markdown structure."""
    # Pattern for trait headers (Ability Score Increase, Size, etc.)
    trait_pattern = r'^(Ability Score Increase|Size|Speed|Darkvision|Languages?|Alignment|Age|Natural Weapons?|[A-Z][a-z]+ [A-Z][a-z]+)\.'

    lines = text.split('\n')
    result = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append('')
            continue

        # Check for trait headers
        trait_match = re.match(trait_pattern, stripped)
        if trait_match:
            trait_name = trait_match.group(1)
            rest = stripped[len(trait_name) + 1:].strip()
            result.append(f'**{trait_name}.** {rest}')
        else:
            result.append(stripped)

    return '\n'.join(result)


def format_table(headers: List[str], rows: List[List[str]]) -> str:
    """Format data as a markdown table."""
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))

    # Build table
    result = []

    # Header row
    header_line = '| ' + ' | '.join(h.ljust(widths[i]) for i, h in enumerate(headers)) + ' |'
    result.append(header_line)

    # Separator
    sep_line = '| ' + ' | '.join('-' * w for w in widths) + ' |'
    result.append(sep_line)

    # Data rows
    for row in rows:
        padded = []
        for i, cell in enumerate(row):
            if i < len(widths):
                padded.append(cell.ljust(widths[i]))
        row_line = '| ' + ' | '.join(padded) + ' |'
        result.append(row_line)

    return '\n'.join(result)


def detect_and_format_tables(text: str) -> str:
    """Detect tabular data and convert to markdown tables."""
    lines = text.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Look for d-roll tables (d8, d10, d6, etc.)
        if re.match(r'^d\d+$', line):
            # This is a table header
            die = line
            header_line = lines[i + 1].strip() if i + 1 < len(lines) else ""

            # Collect rows until we hit a non-table line
            rows = []
            j = i + 2
            while j < len(lines):
                row_line = lines[j].strip()
                if re.match(r'^\d+$', row_line):
                    # This is a roll number, next line is the result
                    roll = row_line
                    value = lines[j + 1].strip() if j + 1 < len(lines) else ""
                    rows.append([roll, value])
                    j += 2
                elif not row_line or re.match(r'^[A-Z]{2,}', row_line):
                    break
                else:
                    j += 1

            if rows:
                table = format_table([die, header_line], rows)
                result.append(table)
                result.append('')
                i = j
                continue

        result.append(lines[i])
        i += 1

    return '\n'.join(result)


def format_races_file(input_path: Path, output_path: Path):
    """Format the races markdown file."""
    content = input_path.read_text(encoding='utf-8')

    # Remove TOC section at the beginning
    toc_end = content.find('CHAPTER 1: RACES')
    if toc_end > 0:
        # Find the actual start of race content
        race_start = content.find('The Southlands are home to')
        if race_start > 0:
            content = '# Chapter 1: Races\n\n' + content[race_start:]

    # Clean text
    content = clean_text(content)

    # Format major race headers
    races = [
        'CATFOLK', 'DWARVES', 'GNOLLS', 'HUMANS OF THE SOUTHLANDS',
        'JINNBORN', 'MINOTAURS', 'TOSCULI',
        'HERU', 'LIZARDFOLK', 'RAMAG', 'SUBEK', 'TROLLKIN'
    ]

    for race in races:
        # Convert ALL CAPS to Title Case header
        title = race.title()
        content = re.sub(rf'^{race}$', f'\n## {title}\n', content, flags=re.MULTILINE)

    # Format section headers
    sections = ['Major Races', 'Minor Races', 'Two People, One Race',
                'Curiosity and Community', 'Other Races', 'Catfolk Adventurers']
    for section in sections:
        content = re.sub(rf'^{section}$', f'\n### {section}\n', content, flags=re.MULTILINE)

    # Format subrace headers
    subraces = ['Basteti', 'Nkosi', 'Southern Trollkin', 'Southern Dwarf',
                'Annites', 'Kushites', 'Morregi', 'Nurians', 'Tethyians', 'Zwana']
    for subrace in subraces:
        content = re.sub(rf'^{subrace}$', f'\n#### {subrace}\n', content, flags=re.MULTILINE)

    # Format trait headers
    trait_pattern = r'^(Ability Score Increase|Size|Speed|Darkvision|Languages|Alignment|Age)\.'
    content = re.sub(trait_pattern, r'**\1.**', content, flags=re.MULTILINE)

    # Detect and format tables
    content = detect_and_format_tables(content)

    output_path.write_text(content, encoding='utf-8')
    print(f"Formatted races saved to {output_path}")


def format_subclasses_file(input_path: Path, output_path: Path):
    """Format the subclasses markdown file."""
    content = input_path.read_text(encoding='utf-8')

    # Clean text
    content = clean_text(content)

    # Add main header
    if not content.startswith('#'):
        content = '# Chapter 3: Character Options\n\n' + content

    # Format class category headers
    categories = [
        'Barbarian Paths', 'Bardic Colleges', 'Cleric Domains',
        'Druid Circles', 'Martial Traditions', 'Sacred Oaths',
        'Ranger Archetypes', 'Roguish Archetypes', 'Sorcerous Origins',
        'Arcane Traditions', 'Lotus Magic', 'Hieroglyphic Magic'
    ]
    for cat in categories:
        content = re.sub(rf'^{cat}$', f'\n## {cat}\n', content, flags=re.MULTILINE)

    # Format specific subclass headers (ALL CAPS)
    subclass_pattern = r'^([A-Z][A-Z\s]+[A-Z])$'
    def replace_subclass(match):
        name = match.group(1).title()
        return f'\n### {name}\n'
    content = re.sub(subclass_pattern, replace_subclass, content, flags=re.MULTILINE)

    # Format feature headers (e.g., "Feature Name" followed by level requirement)
    feature_pattern = r'^([A-Za-z][A-Za-z\s]+)\nStarting when you|At (\d+)(st|nd|rd|th) level'

    output_path.write_text(content, encoding='utf-8')
    print(f"Formatted subclasses saved to {output_path}")


def main():
    print("=" * 60)
    print("Southlands Player's Guide Markdown Formatter")
    print("=" * 60)

    # Format races
    races_input = OUTPUT_DIR / "races.md"
    races_output = OUTPUT_DIR / "races_formatted.md"
    if races_input.exists():
        print("\nFormatting races...")
        format_races_file(races_input, races_output)

    # Format subclasses
    subclasses_input = OUTPUT_DIR / "subclasses.md"
    subclasses_output = OUTPUT_DIR / "subclasses_formatted.md"
    if subclasses_input.exists():
        print("\nFormatting subclasses...")
        format_subclasses_file(subclasses_input, subclasses_output)

    print("\n" + "=" * 60)
    print("Formatting complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
