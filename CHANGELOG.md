# Changelog

All notable changes to this project will be documented in this file.

## [v1.13.0] - 2026-04-14

### Features
- Added filter on monsters for environments (#884)
- Added character creation rules from srd-2024 (#878)
- Feature: split V2 Item model into `Item` and `MagicItem` models (#889)
- Added `ExcludeFieldsMixin` to model viewsets (#872)

### Bug Fixes
- [BUGFIX] Fixed `EagerLoadingMixin` early return error (#898)
- [BUGFIX] `GameContentSerializer` now inherits from `ModelSerializer` (#899)
- [BUGFIX] Fixed data errors on `/v2/rulesets/srd_combat-sequence` (#893)
- Bugfix: separated mixed up V1/V2 endpoints (#890)
- Fixed bugs in srd-2024 spell markdown (#859, #857)
- Fixed missing srd-2024 creature reactions (#860)
- Fixed bugs in srd-2024 `CreatureAction` data (#849)
- Fixed markdown errors in Creature spellcasting traits/actions (#855)
- Fixed srd-2024 spell casting time `bonus_action` → `bonus-action` (#870)
- Fixed missing srd-2024 champion subclass level assignments (#868)
- Fixed missing srd-2024 dragon attack data (#874)
- Fixed srd-2014 dragon breath weapon recharge data (#853)
- Removed prepended asterisks from toh/tdcs `FeatBenefit` `desc` fields (#852)
- Removed Mithral and Adamantine Hide Armor from srd-2014 dataset (#861)
- Fixed parsing reaction conditions without parentheses (#842)
- Fixed markdown bugs in srd-2014 brass dragons (#912)
- Fixed bug in srd-2014 skeleton resistances/immunities (#907)
- Updated srd-2024 goliath giant ancestry markdown: added missing list bullets (#909)
- Fixed typo in srd-2024 Adult Green Dragon spellcasting action (#891)
- Fixed missing `ClassFeatureItem` for Fighter two extra attacks action (#895)
- Removed leading slashes on Image `file_url`s (#886)
- Added missing dash to bfrd mechanist starting equipment markdown (#863)

### Data / Content
- Consolidated CRs into single `challenge_rating` field (#910)
- Convert distance fields to integer (#845)
- Fix spell data regressions and omissions (#844)

### Refactors / Removals
- Removed `/manifest` endpoint and `Manifest` model (#875)
- Removed `/version` endpoint (#875)
- Removed `server/vector_index.pkl` from repo (#883)

### CI/CD
- Upgrade GitHub Action versions to Node 24 compatible versions (#901)

### Dependencies
- Bump django from 5.2.1 to 5.2.13 (#904, #908)
- Bump urllib3 from 2.4.0 to 2.6.3 (#906)
- Bump requests from 2.32.3 to 2.33.0 (#905)

**Full Changelog**: https://github.com/open5e/open5e-api/compare/v1.12.0...v1.13.0

---

## [v1.12.0] - 2025-11-30

**Full Changelog**: https://github.com/open5e/open5e-api/compare/v1.11.0...v1.12.0

## [v1.11.0] - 2025-10-25

**Full Changelog**: https://github.com/open5e/open5e-api/compare/v1.10.0...v1.11.0

## [v1.10.0] - 2025-08-03

**Full Changelog**: https://github.com/open5e/open5e-api/compare/v.1.9.0...v1.10.0

## [v1.9.0] - 2025-03-02

**Full Changelog**: https://github.com/open5e/open5e-api/compare/v.1.8.0...v.1.9.0

## [v1.8.0] - 2024-12-20

**Full Changelog**: https://github.com/open5e/open5e-api/compare/v1.7.0...v.1.8.0
