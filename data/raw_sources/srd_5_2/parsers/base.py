"""Shared utilities for SRD PDF parsers."""
from __future__ import annotations
import re
import unicodedata
import pdfplumber

LIGATURE_MAP = {
    "ﬀ": "ff",
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
}

# Unicode minus sign (U+2212) used in PDF ability score modifiers
_MINUS_SIGN = "−"


def clean_text(s: str) -> str:
    """Strip ligatures, soft hyphens, Unicode minus sign (U+2212) → ASCII minus, normalize whitespace."""
    for ligature, replacement in LIGATURE_MAP.items():
        s = s.replace(ligature, replacement)
    s = s.replace("\xad", "")  # soft hyphen
    s = s.replace(_MINUS_SIGN, "-")  # Unicode minus sign (U+2212) → ASCII minus
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def slugify(name: str) -> str:
    """Normalize a name to a URL-safe slug for dict-key matching."""
    s = clean_text(name).lower()
    s = re.sub(r"[^a-zA-Z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    s = re.sub(r"-+", "-", s)
    return s


def parse_cost(s: str) -> dict | None:
    """Parse '10 GP' / '5 SP' / '2 CP' (also lowercase) into {"amount": float, "unit": str}."""
    m = re.search(r"([\d.]+)\s*(gp|sp|cp)", s, re.IGNORECASE)
    if not m:
        return None
    return {"amount": float(m.group(1)), "unit": m.group(2).lower()}


def parse_dice(s: str) -> dict | None:
    """Parse '2d6+3' or '1d8-1' (also with Unicode minus sign U+2212) into {"count": int, "die": int, "bonus": int}."""
    # Normalize Unicode minus sign (U+2212) to ASCII minus before matching
    s = s.replace(_MINUS_SIGN, "-")
    m = re.search(r"(\d+)[dD](\d+)([+-]\d+)?", s)
    if not m:
        return None
    return {
        "count": int(m.group(1)),
        "die": int(m.group(2)),
        "bonus": int(m.group(3)) if m.group(3) else 0,
    }


def extract_full_text(pdf_path: str) -> str:
    """Open PDF once, concatenate all page text (with table data injected inline).

    Call this in the main thread only — pdfplumber is not thread-safe when sharing
    an open PDF object. Parsers receive the returned string, not the file handle.

    Table rows are injected as §TABLE_ROW§col1|col2|col3§ sentinels so parsers
    can find structured data (ability scores, weapon rows) that doesn't survive
    plain text extraction reliably.
    """
    pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            # Inject table rows as sentinels for structured parsers
            table_lines: list[str] = []
            for table in page.extract_tables():
                for row in table:
                    if row and any(cell for cell in row if cell):
                        cells = [str(cell or "").strip() for cell in row]
                        table_lines.append("§TABLE_ROW§" + "|".join(cells) + "§")
            if table_lines:
                text = text + "\n" + "\n".join(table_lines)
            pages.append(text)
    return "\n".join(pages)


def extract_section(full_text: str, start_re: re.Pattern, end_re: re.Pattern) -> str:
    """Return the substring of full_text between first match of start_re and end_re."""
    m_start = start_re.search(full_text)
    if not m_start:
        raise ValueError(f"start marker not found: {start_re.pattern!r}")
    m_end = end_re.search(full_text, m_start.end())
    if not m_end:
        raise ValueError(f"end marker not found after start: {end_re.pattern!r}")
    return full_text[m_start.end():m_end.start()]
