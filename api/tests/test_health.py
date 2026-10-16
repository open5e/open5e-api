import json
import tempfile
import tomllib
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.test import TestCase
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.settings import spectacular_settings

from search.apps import SearchConfig
from server import health


class HealthTest(TestCase):
    """The test database is empty, so documents are mocked where a passing state is needed."""

    def setUp(self):
        health.build_info.cache_clear()
        self.addCleanup(health.build_info.cache_clear)

    def get(self, path='/health'):
        return self.client.get(path)

    def healthy(self):
        """Patch the checks that depend on loaded data into a passing state."""
        documents = mock.patch('api_v2.models.Document.objects.count', return_value=24)
        index = mock.patch.object(SearchConfig, 'vector_index', {'matrix': object()})
        documents.start(), index.start()
        self.addCleanup(documents.stop)
        self.addCleanup(index.stop)

    def test_empty_database_fails(self):
        response = self.get()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response['Content-Type'], 'application/health+json')
        body = response.json()
        self.assertEqual(body['status'], 'fail')
        self.assertEqual(body['checks']['data:documents'][0]['status'], 'fail')
        self.assertEqual(body['checks']['database:responseTime'][0]['status'], 'pass')

    def test_passes_with_data_and_index(self):
        self.healthy()
        response = self.get()

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['status'], 'pass')
        self.assertEqual(body['serviceId'], 'open5e-api')
        self.assertEqual(body['checks']['data:documents'][0]['observedValue'], 24)

    def test_missing_search_index_only_warns(self):
        self.healthy()
        with mock.patch.object(SearchConfig, 'vector_index', None), \
                mock.patch.object(health, 'VECTOR_INDEX_PATH', Path('/nonexistent/vector_index.pkl')):
            response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'warn')
        self.assertEqual(response.json()['checks']['search:vectorIndex'][0]['status'], 'warn')

    def test_trailing_slash_is_not_redirected(self):
        self.healthy()

        self.assertEqual(self.get('/health/').status_code, 200)

    def test_is_never_cached(self):
        self.assertEqual(self.get()['Cache-Control'], 'no-store')

    def test_only_allows_get_and_head(self):
        self.assertEqual(self.client.post('/health').status_code, 405)

    def test_reports_live_build_info_without_a_build_file(self):
        with mock.patch.object(health, 'BUILD_INFO_PATH', Path('/nonexistent/build_info.json')):
            body = self.get().json()

        with (Path(settings.BASE_DIR) / 'pyproject.toml').open('rb') as f:
            self.assertEqual(body['version'], tomllib.load(f)['project']['version'])
        self.assertTrue(body['releaseId'])
        self.assertTrue(body['schema']['v2'].startswith('sha256:'))
        self.assertIn('srd-2024', body['data'])
        self.assertTrue(body['data']['srd-2024'].startswith('sha256:'))

    def test_reads_the_build_file(self):
        info = {'version': '9.9.9', 'releaseId': 'v9.9.9-1-gabcdef0',
                'schema': {'v2': 'sha256:1'}, 'data': {'core': 'sha256:2'}}
        build_file = Path(self.enterContext(tempfile.TemporaryDirectory())) / 'build_info.json'
        build_file.write_text(json.dumps(info))

        with mock.patch.object(health, 'BUILD_INFO_PATH', build_file):
            body = self.get().json()

        self.assertEqual({k: body[k] for k in info}, info)

    def test_schema_hash_ignores_the_release_version(self):
        """The OpenAPI document includes the version, but the hash is for the shape only."""
        before = health.get_schema_hashes()
        with mock.patch.object(spectacular_settings, 'VERSION', '9.9.9'):
            self.assertEqual(SchemaGenerator().get_schema(request=None, public=True)['info']['version'], '9.9.9')
            self.assertEqual(health.get_schema_hashes(), before)
