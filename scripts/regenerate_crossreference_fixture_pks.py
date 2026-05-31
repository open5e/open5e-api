"""
One-off script to rewrite CrossReference.json fixture with deterministic string PKs.

Run from repo root with: pipenv run python manage.py shell < scripts/regenerate_crossreference_fixture_pks.py
Or: pipenv run python -c "
import os, sys, django
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'open5e.settings')
django.setup()
exec(open('scripts/regenerate_crossreference_fixture_pks.py').read())
"
"""
import json
from pathlib import Path

FIXTURE_PATH = Path("data/v2/wizards-of-the-coast/srd-2024/CrossReference.json")


def main():
    from django.contrib.contenttypes.models import ContentType

    from api_v2.models.crossreference import _crossreference_key_for

    path = Path(__file__).resolve().parent.parent / FIXTURE_PATH
    data = json.loads(path.read_text())

    # Collect all content type IDs used in the fixture.
    all_ct_ids = set()
    for rec in data:
        fields = rec["fields"]
        for fk in ("source_content_type", "reference_content_type"):
            val = fields.get(fk)
            if isinstance(val, int):
                all_ct_ids.add(val)

    # Resolve IDs to natural keys (e.g. ["api_v2", "rule"]) for human-readable fixtures.
    ct_id_to_natural = {}
    if all_ct_ids:
        for ct in ContentType.objects.filter(pk__in=all_ct_ids):
            ct_id_to_natural[ct.pk] = list(ct.natural_key())

    seen = set()
    for rec in data:
        fields = rec["fields"]
        # Deterministic string PK.
        base = _crossreference_key_for(
            fields["source_object_key"],
            fields["anchor"],
            fields["reference_object_key"],
        )
        key = base
        n = 1
        while key in seen:
            key = f"{base}_{n}"
            n += 1
        seen.add(key)
        rec["pk"] = key
        # Replace content type IDs with natural keys.
        for fk in ("source_content_type", "reference_content_type"):
            val = fields.get(fk)
            if isinstance(val, int) and val in ct_id_to_natural:
                fields[fk] = ct_id_to_natural[val]
            # If already a list (natural key), leave as-is.

    path.write_text(json.dumps(data, indent=2))
    print(f"Wrote {len(data)} records to {path}")


if __name__ == "__main__":
    import os
    import sys

    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
    import django
    django.setup()
    main()
