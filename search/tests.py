import json
from unittest.mock import Mock, patch

from django.test import TestCase
from rest_framework.test import APITestCase

from search.viewsets import SearchResultViewSet


class SearchLogicTest(TestCase):
    """Test basic search logic and parameter parsing."""

    def setUp(self):
        self.viewset = SearchResultViewSet()
        self.request = Mock()
        self.viewset.request = self.request

    def test_fuzzy_parameter_parsing(self):
        """Test that fuzzy parameter is parsed correctly."""
        # Test fuzzy=true
        self.request.query_params = {"fuzzy": "true"}
        params = self.viewset._parse_parameters()
        self.assertTrue(params['include_fuzzy'])

        # Test fuzzy=false
        self.request.query_params = {"fuzzy": "false"}
        params = self.viewset._parse_parameters()
        self.assertFalse(params['include_fuzzy'])

        # Test default (not specified)
        self.request.query_params = {}
        params = self.viewset._parse_parameters()
        self.assertFalse(params['include_fuzzy'])

    def test_vector_parameter_parsing(self):
        """Test that vector parameter is parsed correctly."""
        # Test vector=true
        self.request.query_params = {"vector": "true"}
        params = self.viewset._parse_parameters()
        self.assertTrue(params['include_vector'])

        # Test vector=false
        self.request.query_params = {"vector": "false"}
        params = self.viewset._parse_parameters()
        self.assertFalse(params['include_vector'])

        # Test default (not specified)
        self.request.query_params = {}
        params = self.viewset._parse_parameters()
        self.assertFalse(params['include_vector'])

    def test_query_required(self):
        """Test that query parameter is required."""
        self.request.query_params = {}
        
        result = self.viewset.get_queryset()
        
        # Should have metadata for empty query
        self.assertTrue(hasattr(result, '_search_metadata'))
        metadata = result._search_metadata
        self.assertEqual(metadata['exact_matches'], False)

    def test_strict_parameter_parsing(self):
        """Test that strict parameter is parsed correctly."""
        # Test strict=true
        self.request.query_params = {"strict": "true"}
        params = self.viewset._parse_parameters()
        self.assertTrue(params['strict'])

        # Test default (not specified)
        self.request.query_params = {}
        params = self.viewset._parse_parameters()
        self.assertFalse(params['strict'])


class SearchMethodTest(TestCase):
    """Test individual search methods."""

    def setUp(self):
        self.viewset = SearchResultViewSet()

    def test_extract_result_data(self):
        """Test result data extraction."""
        results = [
            (1, 'highlighted1', 'term1', 0.9),
            (2, 'highlighted2', None, 0.8),
            (3, 'highlighted3', 'term3', 0.7),
        ]
        
        pks, highlighted_map, matched_term_map, match_score_map = self.viewset._extract_result_data(results)
        
        self.assertEqual(pks, [1, 2, 3])
        self.assertEqual(highlighted_map, {1: 'highlighted1', 2: 'highlighted2', 3: 'highlighted3'})
        self.assertEqual(matched_term_map, {1: 'term1', 3: 'term3'})  # None values filtered out
        self.assertEqual(match_score_map, {1: 0.9, 2: 0.8, 3: 0.7})

    @patch('search.viewsets.SearchResultViewSet._load_index')
    def test_build_word_index(self, mock_load_index):
        """Test word index building for fuzzy search."""
        names = ['Fire Shield', 'Fireball', 'Magic Weapon', 'Sword +1']
        
        word_index = self.viewset._build_word_index(names)
        
        # Check expected mappings
        self.assertIn('fire', word_index)
        self.assertIn('Fire Shield', word_index['fire'])  # "Fire Shield" contains "fire"
        
        self.assertIn('fireball', word_index)
        self.assertIn('Fireball', word_index['fireball'])  # "Fireball" contains "fireball"
        
        self.assertIn('magic', word_index)
        self.assertIn('Magic Weapon', word_index['magic'])
        
        self.assertIn('sword', word_index)
        self.assertIn('Sword +1', word_index['sword'])

    def test_highlight_text(self):
        """Test text highlighting functionality."""
        text = "This is a magic weapon spell"
        
        # Test single word highlighting
        result = self.viewset._highlight_text(text, "magic")
        self.assertIn('<span class="highlighted">magic</span>', result)
        
        # Test multiple word highlighting  
        result = self.viewset._highlight_text(text, "magic weapon")
        self.assertIn('<span class="highlighted">magic</span>', result)
        self.assertIn('<span class="highlighted">weapon</span>', result)
        
        # Test case insensitive
        result = self.viewset._highlight_text(text, "MAGIC")
        self.assertIn('<span class="highlighted">magic</span>', result)


class SearchMetadataTest(APITestCase):
    """Test search metadata in API responses."""

    @patch('search.viewsets.SearchResultViewSet.get_queryset')
    def test_api_handles_missing_query(self, mock_get_queryset):
        """Test API handles missing query parameter gracefully."""
        # Create a mock queryset with metadata using the same pattern as the viewset
        class MockQuerySetWithMetadata(list):
            def __init__(self):
                super().__init__([])
                self._search_metadata = {
                    'exact_matches': False,
                    'suggestion': None
                }
        
        mock_queryset = MockQuerySetWithMetadata()
        mock_get_queryset.return_value = mock_queryset
        
        response = self.client.get('/v2/search/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 0)
        self.assertEqual(len(data['results']), 0)
        self.assertIn('search_metadata', data)
        self.assertEqual(data['search_metadata']['exact_matches'], False)

    def test_build_metadata_with_exact_results(self):
        """Test metadata building with exact results."""
        viewset = SearchResultViewSet()
        request = Mock()
        request.query_params = {"query": "test"}
        viewset.request = request
        
        # Mock result with match_type attribute
        mock_result = Mock()
        mock_result.match_type = 'exact'
        all_results = [mock_result]
        final_results = [mock_result]
        params = {'include_vector': False}
        
        metadata = viewset._build_metadata(all_results, final_results, params)
        
        self.assertEqual(metadata['exact_matches'], True)
        self.assertIsNone(metadata['suggestion'])

    def test_build_metadata_with_vector_suggestion(self):
        """Test metadata building with vector suggestion."""
        viewset = SearchResultViewSet()
        request = Mock()
        request.query_params = {"query": "test"}
        request.build_absolute_uri = Mock(return_value="http://test.com/search")
        viewset.request = request
        
        all_results = []
        final_results = []
        params = {'query': 'test', 'include_vector': False}
        vector_count = 10
        
        metadata = viewset._build_metadata(all_results, final_results, params, vector_count)
        
        self.assertEqual(metadata['exact_matches'], False)
        self.assertIsNotNone(metadata['suggestion'])
        self.assertEqual(metadata['suggestion']['type'], 'vector')
        self.assertEqual(metadata['suggestion']['additional_matches'], 10)

    def test_search_metadata_structure(self):
        """Test that search metadata has the expected structure."""
        viewset = SearchResultViewSet()
        request = Mock()
        request.query_params = {"query": "test"}
        viewset.request = request
        
        all_results = []
        final_results = []
        params = {'include_vector': False}
        
        metadata = viewset._build_metadata(all_results, final_results, params)
        
        # Check all expected fields are present
        expected_fields = ['exact_matches', 'suggestion']
        
        for field in expected_fields:
            self.assertIn(field, metadata, f"Missing field: {field}")


class SearchIntegrationTest(TestCase):
    """Test search integration with mocked database calls."""

    @patch('search.viewsets.SearchResultViewSet._execute_search_query')
    @patch('search.viewsets.SearchResultViewSet._load_index')
    def test_exact_search_integration(self, mock_load_index, mock_execute):
        """Test exact search method integration."""
        # Mock database result
        mock_result = Mock()
        mock_result.object_pk = 1
        mock_result.highlighted = 'Fire<span class="highlighted">ball</span>'
        mock_execute.return_value = [mock_result]
        
        viewset = SearchResultViewSet()
        results = viewset._exact_search('fireball', '%', '%', '%')
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 1)  # pk
        self.assertEqual(results[0][2], 'fireball')  # matched_term
        self.assertEqual(results[0][3], 1.0)  # score

    @patch('search.viewsets.SearchResultViewSet._load_index')
    def test_vector_search_count_integration(self, mock_load_index):
        """Test vector search count method."""
        # Mock index data with numpy-like behavior
        import numpy as np
        
        mock_vectorizer = Mock()
        mock_matrix = Mock()
        
        # Create actual numpy arrays for realistic behavior
        query_vec = np.array([[0.1, 0.2, 0.3, 0.4]])
        mock_vectorizer.transform.return_value = type('MockSparse', (), {
            'T': query_vec.T
        })()
        
        # Mock matrix multiplication result
        scores = np.array([0.1, 0.3, 0.02, 0.8])
        mock_matrix.__matmul__ = Mock(return_value=type('MockResult', (), {
            'toarray': Mock(return_value=type('MockArray', (), {
                'ravel': Mock(return_value=scores)
            })())
        })())
        
        mock_load_index.return_value = {
            'vectorizer': mock_vectorizer,
            'matrix': mock_matrix
        }
        
        viewset = SearchResultViewSet()
        # With threshold 0.05, should match scores 0.1, 0.3, 0.8 = 3 matches
        count = viewset._vector_search_count('test query', '%', '%', '%')
        
        self.assertEqual(count, 3)

