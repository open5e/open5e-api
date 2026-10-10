"""The /health endpoint: whether this instance can serve requests, and what it's running.

The response follows the Health Check Response Format for HTTP APIs
(`application/health+json`, draft-inadarei-api-health-check). As well as the
draft's fields, it has:

- `schema`: a hash of the OpenAPI document for each API version, which only
  changes when the shape of the API does.
- `data`: a hash of each v2 document's fixture files, which only changes when
  that document's data does.

The version, release, schema and data are fixed for a build, so the Docker
build writes them to server/build_info.json (`manage.py build_info`). Without
that file, as in local development, they're worked out on the first request.
The checks run on every request.
"""
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_safe

BASE_DIR = Path(settings.BASE_DIR)
BUILD_INFO_PATH = BASE_DIR / 'server' / 'build_info.json'
V2_DATA_DIR = BASE_DIR / 'data' / 'v2'
VECTOR_INDEX_PATH = BASE_DIR / 'server' / 'vector_index.pkl'


def get_version():
    return settings.VERSION


def get_release_id():
    """The build's release, e.g. v2.2.3-66-g35e06545, from the environment or git."""
    if os.environ.get('OPEN5E_RELEASE_ID'):
        return os.environ['OPEN5E_RELEASE_ID']
    try:
        return subprocess.run(
            ['git', 'describe', '--tags', '--always'], cwd=BASE_DIR,
            capture_output=True, text=True, timeout=2, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return 'development'


def sha256(chunks):
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk)
    return f'sha256:{digest.hexdigest()}'


def get_schema_hashes():
    from drf_spectacular.generators import SchemaGenerator
    schema = SchemaGenerator().get_schema(request=None, public=True)
    # Leave out `info`, which has the release version, so the hash only changes
    # with the shape of the API. The OpenAPI document only describes v2.
    shape = {k: v for k, v in schema.items() if k != 'info'}
    return {'v2': sha256([json.dumps(shape, sort_keys=True, default=str).encode()])}


def get_data_hashes():
    """A hash of each v2 document's fixture files, keyed by document."""
    hashes = {}
    for document_file in sorted(V2_DATA_DIR.glob('**/Document.json')):
        folder = document_file.parent
        files = sorted(folder.glob('*.json'))
        key = json.loads(document_file.read_text(encoding='utf-8'))[0]['pk']
        hashes[key] = sha256(f.name.encode() + f.read_bytes() for f in files)
    return hashes


def collect_build_info(release_id=None):
    return {
        'version': get_version(),
        'releaseId': release_id or get_release_id(),
        'schema': get_schema_hashes(),
        'data': get_data_hashes(),
    }


@lru_cache(maxsize=1)
def build_info():
    if BUILD_INFO_PATH.exists():
        return json.loads(BUILD_INFO_PATH.read_text(encoding='utf-8'))
    return collect_build_info()


def check(status, **fields):
    return [{'status': status, 'time': datetime.now(timezone.utc).isoformat(), **fields}]


def database_check():
    try:
        start = time.perf_counter()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        elapsed = round((time.perf_counter() - start) * 1000, 1)
        return check('pass', componentType='datastore', observedValue=elapsed, observedUnit='ms')
    except Exception:
        return check('fail', componentType='datastore', output='The database is unavailable.')


def documents_check():
    """The data has been imported: an empty database can't serve anything useful."""
    from api_v2.models import Document
    try:
        count = Document.objects.count()
    except Exception:
        return check('fail', componentType='datastore', output='Documents could not be counted.')
    if count == 0:
        return check('fail', componentType='datastore', observedValue=0, output='No documents are loaded.')
    return check('pass', componentType='datastore', observedValue=count)


def search_index_check():
    """Only vector search needs the index, so a missing index is a warning, not a failure.

    Search loads the index on demand if it wasn't loaded at startup, so the file
    being there is enough.
    """
    from search.apps import SearchConfig
    if SearchConfig.vector_index or VECTOR_INDEX_PATH.exists():
        return check('pass', componentType='component')
    return check('warn', componentType='component', output='The vector search index is missing.')


@require_safe
def health(request):
    checks = {
        'database:responseTime': database_check(),
        'data:documents': documents_check(),
        'search:vectorIndex': search_index_check(),
    }
    statuses = {c[0]['status'] for c in checks.values()}
    status = 'fail' if 'fail' in statuses else 'warn' if 'warn' in statuses else 'pass'

    info = build_info()
    body = {
        'status': status,
        'version': info['version'],
        'releaseId': info['releaseId'],
        'serviceId': 'open5e-api',
        'description': 'Open5e API',
        'checks': checks,
        'schema': info['schema'],
        'data': info['data'],
    }
    response = JsonResponse(body, status=503 if status == 'fail' else 200,
                            content_type='application/health+json')
    # Monitors need the current state, never a cached copy.
    response['Cache-Control'] = 'no-store'
    return response
