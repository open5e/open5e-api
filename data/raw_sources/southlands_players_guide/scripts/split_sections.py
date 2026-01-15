#!/usr/bin/env python3
"""
Southlands Player's Guide Section Splitter

Splits the extracted PDF content into logical sections based on the TOC.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent
SECTIONS_DIR = RAW_DIR / "sections"
OUTPUT_DIR = RAW_DIR / "output"

# Section boundaries based on TOC (page numbers from the PDF)
SECTION_MAP = {
    "races": {"start": 3, "end": 26, "filename": "races.md"},
    "backgrounds": {"start": 27, "end": 35, "filename": "backgrounds.md"},
    "subclasses": {"start": 36, "end": 69, "filename": "subclasses.md"},
    "equipment": {"start": 70, "end": 72, "filename": "equipment.md"},
    "spells": {"start": 73, "end": 81, "filename": "spells.md"},
}


def load_pages() -> Dict[int, str]:
    """Load all extracted pages into a dictionary."""
    pages_dir = SECTIONS_DIR / "pages"
    pages = {}

    for page_file in sorted(pages_dir.glob("page_*.md")):
        # Extract page number from filename
        match = re.search(r'page_(\d+)\.md', page_file.name)
        if match:
            page_num = int(match.group(1))
            pages[page_num] = page_file.read_text(encoding="utf-8")

    return pages


def split_into_sections(pages: Dict[int, str]) -> Dict[str, str]:
    """Split pages into logical sections."""
    sections = {}

    for section_name, bounds in SECTION_MAP.items():
        section_content = []
        for page_num in range(bounds["start"], bounds["end"] + 1):
            if page_num in pages:
                # Remove the page header line
                content = pages[page_num]
                content = re.sub(r'^# Page \d+\n+', '', content)
                # Remove leading page numbers that appear at top
                content = re.sub(r'^\d+\n', '', content)
                section_content.append(content)

        sections[section_name] = "\n\n---\n\n".join(section_content)

    return sections


def save_sections(sections: Dict[str, str]):
    """Save sections to individual markdown files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for section_name, content in sections.items():
        filename = SECTION_MAP[section_name]["filename"]
        output_path = OUTPUT_DIR / filename
        output_path.write_text(content, encoding="utf-8")
        print(f"Saved {section_name} to {output_path}")


def main():
    print("=" * 60)
    print("Southlands Player's Guide Section Splitter")
    print("=" * 60)

    print("\nLoading pages...")
    pages = load_pages()
    print(f"Loaded {len(pages)} pages")

    print("\nSplitting into sections...")
    sections = split_into_sections(pages)

    for name, content in sections.items():
        print(f"  - {name}: {len(content)} characters")

    print("\nSaving sections...")
    save_sections(sections)

    print("\n" + "=" * 60)
    print("Section splitting complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
