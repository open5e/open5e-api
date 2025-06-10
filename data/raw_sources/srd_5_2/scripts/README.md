# SRD 5.2 Conversion Scripts

This directory contains scripts specific to processing and converting the D&D System Reference Document 5.2 (SRD 5.2) content.

## Purpose

These scripts are stored here rather than in a general scripts directory because they are:

1. **Document-specific**: Tailored specifically for the SRD 5.2 format and structure
2. **One-time use**: Designed for the initial conversion of SRD 5.2 content to Open5e API v2 format
3. **Reference material**: Kept for future reference in case similar conversions are needed
4. **Tightly coupled**: Depend on the specific markdown format and structure of the SRD 5.2 document

## Scripts

### convert_spells_srd52_improved.py
- **Purpose**: Converts spells from the SRD 5.2 markdown format to Open5e API v2 JSON format
- **Input**: `../sections/08_spells.md` (or the full SRD document)
- **Output**: `../../v2/wizards-of-the-coast/srd-5-2/Spell.json`
- **Features**: 
  - Parses spell headers to extract level, school, and classes
  - Handles spell components, duration, range, and casting time
  - Cleans markdown formatting from spell names and descriptions
  - Creates proper primary keys for the v2 API

### Usage Notes

These scripts were used during the initial import of SRD 5.2 content. If you need to re-run them or adapt them for similar content:

1. Ensure the input file paths are correct relative to this directory
2. Check that the output directory structure exists
3. Review the parsing logic if the source format has changed
4. Run the Django management commands to load the generated fixtures

## Related Files

- Source document: `../DND-SRD-5.2-CC.md`
- Split sections: `../sections/`
- Generated v2 data: `../../v2/wizards-of-the-coast/srd-5-2/` 