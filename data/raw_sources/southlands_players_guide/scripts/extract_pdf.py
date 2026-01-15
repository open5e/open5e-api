#!/usr/bin/env python3
"""
Southlands Player's Guide PDF Extractor

This script extracts content from the Southlands Player's Guide PDF and converts it to markdown sections.
Uses pymupdf (fitz) for PDF parsing.

Usage:
    pip install pymupdf
    python extract_pdf.py
"""

import fitz  # pymupdf
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Paths
SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent
PDF_PATH = RAW_DIR / "Southlands-Players-Guide-5E.pdf"
SECTIONS_DIR = RAW_DIR / "sections"
OUTPUT_DIR = RAW_DIR / "output"

# Content type patterns - used to identify different sections
SECTION_PATTERNS = {
    "spells": [
        r"^([\w\s\-\']+)\s*\n+(Cantrip|1st-level|2nd-level|3rd-level|4th-level|5th-level|6th-level|7th-level|8th-level|9th-level)",
        r"^([\w\s\-\']+)\s+\((Cantrip|1st-level|2nd-level|3rd-level|4th-level|5th-level|6th-level|7th-level|8th-level|9th-level)",
    ],
    "feats": [
        r"^([\w\s\-\']+)\s*\n+Prerequisite:",
        r"^Feat:\s*([\w\s\-\']+)",
    ],
    "monsters": [
        r"^([\w\s\-\']+)\s*\n+(Tiny|Small|Medium|Large|Huge|Gargantuan)",
        r"^([\w\s\-\']+)\s*\n+Armor Class",
    ],
    "magic_items": [
        r"^([\w\s\-\']+)\s*\n+(Wondrous item|Weapon|Armor|Ring|Rod|Staff|Wand|Potion|Scroll)",
        r"^([\w\s\-\']+)\s*,\s*(common|uncommon|rare|very rare|legendary)",
    ],
    "backgrounds": [
        r"^([\w\s\-\']+)\s*\n+Skill Proficiencies:",
    ],
    "races": [
        r"^([\w\s\-\']+)\s+Traits\s*\n",
        r"^([\w\s\-\']+)\s*\n+Ability Score Increase",
    ],
    "subclasses": [
        r"^([\w\s\-\']+)\s*\n+.*at \d+(st|nd|rd|th) level",
    ]
}


def extract_text_from_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    """Extract text from PDF with page numbers and formatting hints."""
    doc = fitz.open(str(pdf_path))
    pages = []

    for page_num, page in enumerate(doc, 1):
        # Extract text with layout preservation
        text = page.get_text("text")

        # Also get text blocks for better structure analysis
        blocks = page.get_text("dict")["blocks"]

        pages.append({
            "page_num": page_num,
            "text": text,
            "blocks": blocks
        })

        # Progress indicator
        if page_num % 50 == 0:
            print(f"Extracted page {page_num}/{len(doc)}")

    doc.close()
    print(f"Total pages extracted: {len(pages)}")
    return pages


def extract_text_with_structure(pdf_path: Path) -> str:
    """Extract full PDF text with page markers."""
    doc = fitz.open(str(pdf_path))
    full_text = []

    for page_num, page in enumerate(doc, 1):
        text = page.get_text("text")
        full_text.append(f"\n\n<!-- PAGE {page_num} -->\n\n{text}")

        if page_num % 50 == 0:
            print(f"Processed page {page_num}/{len(doc)}")

    doc.close()
    return "".join(full_text)


def identify_toc(pages: List[Dict]) -> Dict[str, int]:
    """Try to identify table of contents and section page numbers."""
    toc = {}

    # Look for TOC-like patterns in first 10 pages
    for page_data in pages[:15]:
        text = page_data["text"]

        # Look for lines with page numbers (e.g., "Chapter 1: Races......5")
        toc_pattern = r'^([\w\s\-:]+?)\.{2,}\s*(\d+)\s*$'
        matches = re.findall(toc_pattern, text, re.MULTILINE)

        for title, page_num in matches:
            toc[title.strip()] = int(page_num)

    return toc


def split_into_major_sections(full_text: str, toc: Dict[str, int]) -> Dict[str, str]:
    """Split the text into major sections based on TOC."""
    sections = {}

    # Common D&D sourcebook sections
    section_keywords = [
        "races", "character races",
        "classes", "subclasses", "archetypes",
        "backgrounds",
        "feats",
        "equipment", "magic items",
        "spells",
        "monsters", "creatures", "bestiary",
        "appendix"
    ]

    # Use page markers to split
    page_pattern = r'<!-- PAGE (\d+) -->'
    pages_split = re.split(page_pattern, full_text)

    # Rebuild with page info
    pages_with_content = []
    for i in range(1, len(pages_split), 2):
        if i + 1 < len(pages_split):
            page_num = int(pages_split[i])
            content = pages_split[i + 1]
            pages_with_content.append((page_num, content))

    return {"full": full_text, "pages": pages_with_content, "toc": toc}


def save_markdown_sections(content: Dict, output_dir: Path):
    """Save extracted content as markdown files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save full text
    full_text_path = output_dir / "full_text.md"
    with open(full_text_path, "w", encoding="utf-8") as f:
        f.write(content["full"])
    print(f"Saved full text to {full_text_path}")

    # Save TOC
    if content.get("toc"):
        toc_path = output_dir / "toc.json"
        with open(toc_path, "w", encoding="utf-8") as f:
            json.dump(content["toc"], f, indent=2)
        print(f"Saved TOC to {toc_path}")

    # Save individual pages for processing
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(exist_ok=True)

    for page_num, page_content in content.get("pages", []):
        page_path = pages_dir / f"page_{page_num:04d}.md"
        with open(page_path, "w", encoding="utf-8") as f:
            f.write(f"# Page {page_num}\n\n{page_content}")


def extract_spell_sections(full_text: str) -> List[Dict[str, str]]:
    """Extract spell entries from the text."""
    spells = []

    # Pattern for spell headers - typically:
    # SPELL NAME
    # Level School (Ritual)
    # Casting Time: X
    # Range: X
    # Components: V, S, M (materials)
    # Duration: X
    #
    # Description...

    # This is a simplified pattern - actual extraction may need refinement
    spell_pattern = re.compile(
        r'^([A-Z][A-Za-z\s\-\']+)\s*\n+'
        r'(Cantrip|1st-level|2nd-level|3rd-level|4th-level|5th-level|6th-level|7th-level|8th-level|9th-level)\s+'
        r'(\w+)\s*(\(ritual\))?\s*\n+'
        r'Casting Time:\s*([^\n]+)\n+'
        r'Range:\s*([^\n]+)\n+'
        r'Components?:\s*([^\n]+)\n+'
        r'Duration:\s*([^\n]+)\n+'
        r'(.*?)(?=\n[A-Z][A-Za-z\s\-\']+\s*\n+(?:Cantrip|1st-level|2nd-level|3rd-level|4th-level|5th-level|6th-level|7th-level|8th-level|9th-level)|\Z)',
        re.MULTILINE | re.DOTALL | re.IGNORECASE
    )

    for match in spell_pattern.finditer(full_text):
        spell = {
            "name": match.group(1).strip(),
            "level": match.group(2).strip(),
            "school": match.group(3).strip(),
            "ritual": bool(match.group(4)),
            "casting_time": match.group(5).strip(),
            "range": match.group(6).strip(),
            "components": match.group(7).strip(),
            "duration": match.group(8).strip(),
            "description": match.group(9).strip()
        }
        spells.append(spell)

    return spells


def main():
    """Main extraction workflow."""
    print("=" * 60)
    print("Southlands Player's Guide PDF Extractor")
    print("=" * 60)

    if not PDF_PATH.exists():
        # Try alternate location
        alt_path = Path(r"C:\Users\mnehm\Downloads\_PDFs\Southlands-Players-Guide-5E-v2-dzhhuz.pdf")
        if alt_path.exists():
            print(f"Using PDF from: {alt_path}")
            pdf_to_use = alt_path
        else:
            print(f"ERROR: PDF not found at {PDF_PATH}")
            print(f"       Also checked: {alt_path}")
            return
    else:
        pdf_to_use = PDF_PATH

    # Create output directories
    SECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\nExtracting from: {pdf_to_use}")
    print(f"Output directory: {SECTIONS_DIR}")

    # Step 1: Extract pages with structure info
    print("\n[1/4] Extracting text from PDF...")
    pages = extract_text_from_pdf(pdf_to_use)

    # Step 2: Identify TOC
    print("\n[2/4] Analyzing table of contents...")
    toc = identify_toc(pages)
    if toc:
        print(f"Found {len(toc)} TOC entries")
        for title, page in list(toc.items())[:10]:
            print(f"  - {title}: page {page}")

    # Step 3: Extract full text with page markers
    print("\n[3/4] Building full text with structure...")
    full_text = extract_text_with_structure(pdf_to_use)

    # Step 4: Save to markdown
    print("\n[4/4] Saving markdown files...")
    content = {
        "full": full_text,
        "pages": [(p["page_num"], p["text"]) for p in pages],
        "toc": toc
    }
    save_markdown_sections(content, SECTIONS_DIR)

    print("\n" + "=" * 60)
    print("Extraction complete!")
    print(f"Full text saved to: {SECTIONS_DIR / 'full_text.md'}")
    print(f"Individual pages saved to: {SECTIONS_DIR / 'pages'}")
    print("\nNext steps:")
    print("1. Review full_text.md to identify section boundaries")
    print("2. Run content-specific extraction scripts")
    print("3. Use LLM to convert to structured JSON")
    print("=" * 60)


if __name__ == "__main__":
    main()
