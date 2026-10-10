# SRD 5.2 sources

Source material for the `srd-2024` document.

| Path | What it is |
|------|------------|
| `SRD_CC_v5.2.1.pdf` | The official SRD 5.2.1 from D&D Beyond. **Use this as the reference** when checking or correcting `srd-2024` data. |
| `SRD_CC_v5.2.pdf` | The official SRD 5.2, kept for comparison. Page numbers differ from 5.2.1. |
| `starting-files/`, `sections/` | **Historical.** The markdown the `srd-2024` data was first imported from. |
| `scripts/` | The one-time conversion scripts that read the markdown. |

## The markdown is historical

The markdown was used for the initial import, and is kept as a record of it. Don't correct it, and don't re-import from it:

- It matches neither PDF. For example, it has the Awakened Tree's Slam as 13 (2d8 + 4) where both PDFs have 14 (3d6 + 4), and it is missing content such as the hags' Coven Magic trait and the Octopus.
- The `srd-2024` JSON in `data/v2/wizards-of-the-coast/srd-2024/` has since been corrected beyond it, so it is now the data to change, checked against the 5.2.1 PDF.

See #1006 for the comparison.
