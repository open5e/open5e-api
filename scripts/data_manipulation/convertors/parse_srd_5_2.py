"""Parse the SRD 5.2 PDF into the Open5e v2 data format.

This script expects ``pdfminer.six`` to be installed. Due to network
restrictions in some development environments, you may need to install
it manually before running this script::

    pipenv run pip install pdfminer.six

The script extracts raw text from ``data/raw_sources/srd_5_2/SRD_CC_v5.2.pdf``
and then attempts to split that text into logical sections.  Each
section can then be converted into the structured JSON fixtures used by
``open5e``.

At the moment only minimal scaffolding is provided.  The ``parse_*``
functions should be implemented to handle the specifics of the SRD 5.2
layout.  When finished, JSON files mirroring those in
``data/v2/wizards-of-the-coast/srd-2014`` should be written to
``data/v2/wizards-of-the-coast/srd-2024``.
"""

from __future__ import annotations

import json
import pathlib
from typing import Dict, List

try:
    from pdfminer.high_level import extract_text
except Exception as exc:  # pragma: no cover - pdfminer not installed
    extract_text = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

PDF_PATH = pathlib.Path("data/raw_sources/srd_5_2/SRD_CC_v5.2.pdf")
OUTPUT_DIR = pathlib.Path("data/v2/wizards-of-the-coast/srd-2024")


def main() -> None:
    if extract_text is None:
        raise RuntimeError(
            "pdfminer.six is required to run this script: %s" % IMPORT_ERROR
        )

    raw_text = extract_text(str(PDF_PATH))
    sections = split_into_sections(raw_text)
    data = {
        "abilities": parse_abilities(sections.get("Abilities", "")),
        "classes": parse_classes(sections.get("Classes", "")),
        "feats": parse_feats(sections.get("Feats", "")),
        "monsters": parse_monsters(sections.get("Monsters", "")),
        "spells": parse_spells(sections.get("Spells", "")),
    }

    write_json_files(data)


def split_into_sections(text: str) -> Dict[str, str]:
    """Very rough splitter based on simple headings."""
    sections: Dict[str, str] = {}
    current = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.upper() in {"ABILITIES", "CLASSES", "FEATS", "MONSTERS", "SPELLS"}:
            current = line.title()
            sections[current] = []
        elif current:
            sections[current].append(line)
    return {k: "\n".join(v) for k, v in sections.items()}


def parse_abilities(text: str) -> List[Dict[str, str]]:
    """Parse ability score definitions from text."""
    # TODO: Implement parsing logic
    return []


def parse_classes(text: str) -> List[Dict[str, str]]:
    """Parse classes and subclasses from text."""
    # TODO: Implement parsing logic
    return []


def parse_feats(text: str) -> List[Dict[str, str]]:
    """Parse feats from text."""
    # TODO: Implement parsing logic
    return []


def parse_monsters(text: str) -> List[Dict[str, str]]:
    """Parse monster stat blocks from text."""
    # TODO: Implement parsing logic
    return []


def parse_spells(text: str) -> List[Dict[str, str]]:
    """Parse spells from text."""
    # TODO: Implement parsing logic
    return []


def write_json_files(data: Dict[str, List[Dict[str, str]]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mapping = {
        "abilities": OUTPUT_DIR / "Ability.json",
        "classes": OUTPUT_DIR / "CharacterClass.json",
        "feats": OUTPUT_DIR / "Feat.json",
        "monsters": OUTPUT_DIR / "Creature.json",
        "spells": OUTPUT_DIR / "Spell.json",
    }
    for key, path in mapping.items():
        with path.open("w") as fh:
            json.dump(data[key], fh, indent=2)


if __name__ == "__main__":  # pragma: no cover
    main()
