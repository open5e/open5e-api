# Crossreference scripts

Crossreference candidate finding, report generation, deletion by document, and applying suggested links to the database.

## Modules

- **core.py** – Matching logic, blacklists, document scoping, `identify_crossreferences_from_text`, report building, URL helpers. Used by all other scripts.

- **find_candidates.py** – List source candidates and optionally write JSON reports (sources + references) and print top 10.

- **delete_crossreferences.py** – Delete `CrossReference` rows whose source is in a given document (optional model + blacklists, `--dry-run`).

- **apply_crossreferences.py** – Create `CrossReference` rows from the same text-matching logic; supports `--dry-run` and `--replace`.

## How to run

Invoke via Django management commands. Blacklist paths are typically at project root (e.g. `crossreference_source_blacklist.txt`, `crossreference_reference_blacklist.txt`).

```bash
manage.py find_crossreference_candidates --document srd-2024 [--sources-report ...] [--references-report ...]
manage.py delete_crossreferences --document srd-2024 [--dry-run]
manage.py apply_crossreferences --document srd-2024 [--dry-run] [--replace]
```

## Typical workflow

1. Run `find_crossreference_candidates` with report paths; inspect the generated JSON reports.
2. Tune blacklists as needed.
3. Run `apply_crossreferences --dry-run` to see how many rows would be created (and replaced if using `--replace`).
4. Run `apply_crossreferences` to write to the database. Use `--replace` to clear existing crossreferences for that document before creating new ones.
