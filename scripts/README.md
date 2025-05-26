# Open5e API Scripts

This directory contains general-purpose scripts for the Open5e API project.

## Organization

### General Scripts (This Directory)
Scripts in this directory are:
- **Project-wide utilities**: Used across the entire Open5e API project
- **Deployment scripts**: For managing deployments and infrastructure
- **Testing utilities**: General testing and validation scripts
- **Maintenance tools**: Database management, cache clearing, etc.

### Document-Specific Scripts (Located Elsewhere)
Some scripts are stored alongside the specific source data they were built to process, rather than in this general directory.

**For Example:**
- `data/raw_sources/srd_5_2/scripts/` - Scripts specific to processing D&D SRD 5.2 markdown content; kept in case eg. there is an updated version of this file that can be re-processed with it, or a similar file is released by that publisher.

## Usage Guidelines

When adding new scripts, consider:
1. **Is this script general-purpose?** → Place it here
2. **Is this script specific to one document/dataset?** → Place it with the source data
3. **Will this script be reused across multiple documents?** → Place it here or in `data_manipulation/`

This organization helps maintain a clean separation between general project utilities and document-specific processing logic. 