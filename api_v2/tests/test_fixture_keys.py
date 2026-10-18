import json
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / 'data' / 'v2'


def test_fixture_pks_are_unique_per_model():
    """No two fixture records of the same model may share a pk.

    loaddata keeps whichever record loads last and raises nothing, so a duplicate
    silently replaces another record, and which one wins depends on file order.
    """
    seen = defaultdict(list)
    for path in sorted(DATA_DIR.rglob('*.json')):
        records = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(records, list):
            continue
        for record in records:
            if isinstance(record, dict) and 'model' in record and 'pk' in record:
                seen[(record['model'], record['pk'])].append(str(path.relative_to(DATA_DIR)))

    duplicates = {key: files for key, files in seen.items() if len(files) > 1}
    assert not duplicates, '\n'.join(
        f'{model} pk {pk!r} is defined in: {", ".join(files)}'
        for (model, pk), files in sorted(duplicates.items(), key=str))
