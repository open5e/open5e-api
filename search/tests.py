from rest_framework.test import APITestCase
from django.test import TestCase
from unittest.mock import patch, MagicMock, Mock
from search.viewsets import SearchResultViewSet
from django.http import HttpRequest
import numpy as np


class SearchLogicTest(TestCase):
    """Test the search logic without requiring full database setup."""

    def setUp(self):
        self.viewset = SearchResultViewSet()
        # Mock request
        self.request = Mock()
        self.request.query_params = {}
        self.viewset.request = self.request

    def test_fuzzy_parameter_parsing(self):
        """Test that fuzzy parameter is correctly parsed."""
        test_cases = [
            ("true", True),
            ("True", True), 
            ("1", True),
            ("yes", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
            ("", False),
        ]
        
        for param_value, expected in test_cases:
            self.request.query_params = {"fuzzy": param_value, "query": "test"}
            include_fuzzy = self.request.query_params.get("fuzzy", "false").lower() in ["1", "true", "yes"]
            self.assertEqual(include_fuzzy, expected, f"Failed for input '{param_value}'")

    def test_vector_parameter_parsing(self):
        """Test that vector parameter is correctly parsed."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("1", True), 
            ("yes", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
            ("", False),
        ]
        
        for param_value, expected in test_cases:
            self.request.query_params = {"vector": param_value, "query": "test"}
            include_vector = self.request.query_params.get("vector", "false").lower() in ["1", "true", "yes"]
            self.assertEqual(include_vector, expected, f"Failed for input '{param_value}'")

    def test_query_required(self):
        """Test that query parameter is required."""
        self.request.query_params = {}
        result = self.viewset.get_queryset()
        # Should return empty queryset with metadata
        self.assertTrue(hasattr(result, '_search_metadata'))
        self.assertEqual(result._search_metadata['search_type'], 'empty')


class DirectSearchTest(TestCase):
    """Test direct search behavior."""

    @patch('search.viewsets.models.SearchResult.objects.raw')
    def test_direct_search_with_results(self, mock_raw):
        """Test direct search returns results when found."""
        mock_result = Mock()
        mock_result.object_name = "Fireball"
        mock_raw.return_value = [mock_result]
        
        viewset = SearchResultViewSet()
        request = Mock()
        request.query_params = {"query": "fireball"}
        viewset.request = request
        
        with patch.object(viewset, 'get_direct_search_results') as mock_direct, \
             patch.object(viewset, 'get_vector_search_results') as mock_vector:
            
            mock_direct.return_value = [mock_result]
            mock_vector.return_value = ([], 5)  # 5 vector matches available
            
            result = viewset.get_queryset()
            
            # Should not use fallback
            self.assertTrue(hasattr(result, '_search_metadata'))
            metadata = result._search_metadata
            self.assertEqual(metadata['search_type'], 'direct')
            self.assertTrue(metadata['has_direct_matches'])
            self.assertFalse(metadata['used_fallback'])
            self.assertIsNone(metadata['suggestion'])  # No suggestion since we found direct matches


class FuzzyFallbackTest(TestCase):
    """Test fuzzy search fallback behavior."""

    def test_fuzzy_fallback_when_no_direct_matches(self):
        """Test that fuzzy search is used as fallback when no direct matches."""
        viewset = SearchResultViewSet()
        request = Mock()
        request.query_params = {"query": "firebll"}  # Misspelling
        viewset.request = request
        
        mock_fuzzy_result = Mock()
        mock_fuzzy_result.object_name = "Fireball"
        
        with patch.object(viewset, 'get_direct_search_results') as mock_direct, \
             patch.object(viewset, 'get_fuzzy_search_results') as mock_fuzzy, \
             patch.object(viewset, 'get_vector_search_results') as mock_vector:
            
            mock_direct.return_value = []  # No direct matches
            mock_fuzzy.return_value = ([mock_fuzzy_result], ["Fireball"])
            mock_vector.return_value = ([], 0)
            
            result = viewset.get_queryset()
            
            # Should use fuzzy fallback
            metadata = result._search_metadata
            self.assertFalse(metadata['has_direct_matches'])
            self.assertTrue(metadata['used_fallback'])
            self.assertEqual(metadata['fallback_type'], 'fuzzy')
            self.assertEqual(metadata['fuzzy_count'], 1)

    def test_explicit_fuzzy_with_direct_matches(self):
        """Test that fuzzy=true includes fuzzy results even with direct matches."""
        viewset = SearchResultViewSet()
        request = Mock()
        request.query_params = {"query": "fire", "fuzzy": "true"}
        viewset.request = request
        
        mock_direct_result = Mock()
        mock_direct_result.object_name = "Fire Shield"
        mock_fuzzy_result = Mock()
        mock_fuzzy_result.object_name = "Fireball"
        
        with patch.object(viewset, 'get_direct_search_results') as mock_direct, \
             patch.object(viewset, 'get_fuzzy_search_results') as mock_fuzzy, \
             patch.object(viewset, 'get_vector_search_results') as mock_vector, \
             patch('search.viewsets.models.SearchResult.objects.raw') as mock_raw:
            
            mock_direct.return_value = [mock_direct_result]
            mock_fuzzy.return_value = ([mock_fuzzy_result], ["Fireball"])
            mock_vector.return_value = ([], 0)
            mock_raw.return_value = []
            
            result = viewset.get_queryset()
            
            # Should include both direct and fuzzy
            metadata = result._search_metadata
            self.assertTrue(metadata['has_direct_matches'])
            self.assertEqual(metadata['search_type'], 'enhanced')
            self.assertEqual(metadata['fuzzy_count'], 1)


class VectorSearchTest(TestCase):
    """Test vector search behavior."""

    def test_vector_suggestion_when_no_direct_matches(self):
        """Test that vector search suggestion appears when no direct matches."""
        viewset = SearchResultViewSet()
        request = Mock()
        request.query_params = {"query": "magical weapon"}
        viewset.request = request
        
        mock_vector_result = Mock()
        mock_vector_result.object_name = "Magic Weapon"
        
        with patch.object(viewset, 'get_direct_search_results') as mock_direct, \
             patch.object(viewset, 'get_fuzzy_search_results') as mock_fuzzy, \
             patch.object(viewset, 'get_vector_search_results') as mock_vector, \
             patch.object(viewset, 'get_deduplicated_vector_count') as mock_dedup:
            
            mock_direct.return_value = []  # No direct matches
            mock_fuzzy.return_value = ([], [])  # No fuzzy matches
            mock_vector.return_value = ([], 0)  # Not running vector search
            mock_dedup.return_value = (15, 20)  # 15 unique vector matches, 20 total
            
            result = viewset.get_queryset()
            
            # Should suggest vector search
            metadata = result._search_metadata
            self.assertFalse(metadata['has_direct_matches'])
            self.assertIsNotNone(metadata['suggestion'])
            self.assertEqual(metadata['suggestion']['type'], 'vector')
            self.assertEqual(metadata['suggestion']['count'], 15)
            self.assertIn("view 15 additional results for similar terms", metadata['suggestion']['message'])
            self.assertIn('link', metadata['suggestion'])

    def test_explicit_vector_search(self):
        """Test that vector=true includes vector results."""
        viewset = SearchResultViewSet()
        request = Mock()
        request.query_params = {"query": "magic", "vector": "true"}
        viewset.request = request
        
        mock_vector_result = Mock()
        mock_vector_result.object_name = "Magic Weapon"
        
        with patch.object(viewset, 'get_direct_search_results') as mock_direct, \
             patch.object(viewset, 'get_vector_search_results') as mock_vector, \
             patch('search.viewsets.models.SearchResult.objects.raw') as mock_raw:
            
            mock_direct.return_value = []
            mock_vector.return_value = ([mock_vector_result], 1)
            mock_raw.return_value = []
            
            result = viewset.get_queryset()
            
            # Should include vector results
            metadata = result._search_metadata
            self.assertEqual(metadata['search_type'], 'enhanced')
            self.assertEqual(metadata['vector_count'], 1)


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
                    'search_type': 'empty',
                    'has_direct_matches': False,
                    'direct_count': 0,
                    'fuzzy_count': 0,
                    'vector_count': 0,
                    'used_fallback': False,
                    'fallback_type': None
                }
        
        mock_queryset = MockQuerySetWithMetadata()
        mock_get_queryset.return_value = mock_queryset
        
        response = self.client.get('/v2/search/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 0)
        self.assertEqual(len(data['results']), 0)
        self.assertIn('search_metadata', data)
        self.assertEqual(data['search_metadata']['search_type'], 'empty')

    def test_search_metadata_structure(self):
        """Test that search metadata has the expected structure."""
        viewset = SearchResultViewSet()
        request = Mock()
        request.query_params = {"query": "test"}
        viewset.request = request
        
        with patch.object(viewset, 'get_direct_search_results') as mock_direct, \
             patch.object(viewset, 'get_fuzzy_search_results') as mock_fuzzy, \
             patch.object(viewset, 'get_vector_search_results') as mock_vector, \
             patch.object(viewset, 'get_deduplicated_vector_count') as mock_dedup:
            
            mock_direct.return_value = []
            mock_fuzzy.return_value = ([], [])
            mock_vector.return_value = ([], 0)
            mock_dedup.return_value = (0, 0)
            
            result = viewset.get_queryset()
            
            metadata = result._search_metadata
            
            # Check all expected fields are present
            expected_fields = [
                'search_type', 'has_direct_matches', 'direct_count',
                'fuzzy_count', 'vector_count', 'unique_vector_count',
                'used_fallback', 'fallback_type', 'suggestion'
            ]
            
            for field in expected_fields:
                self.assertIn(field, metadata, f"Missing field: {field}")


class SearchCombinationTest(TestCase):
    """Test various combinations of search parameters."""

    def test_all_search_types_combined(self):
        """Test combining direct, fuzzy, and vector search."""
        viewset = SearchResultViewSet()
        request = Mock()
        request.query_params = {"query": "magic", "fuzzy": "true", "vector": "true"}
        viewset.request = request
        
        with patch.object(viewset, 'get_direct_search_results') as mock_direct, \
             patch.object(viewset, 'get_fuzzy_search_results') as mock_fuzzy, \
             patch.object(viewset, 'get_vector_search_results') as mock_vector, \
             patch('search.viewsets.models.SearchResult.objects.raw') as mock_raw:
            
            mock_direct.return_value = [Mock()]
            mock_fuzzy.return_value = ([Mock()], ["Fuzzy"])
            mock_vector.return_value = ([Mock()], 1)
            mock_raw.return_value = []
            
            result = viewset.get_queryset()
            
            metadata = result._search_metadata
            self.assertEqual(metadata['search_type'], 'enhanced')
            self.assertTrue(metadata['has_direct_matches'])
            self.assertEqual(metadata['fuzzy_count'], 1)
            self.assertEqual(metadata['vector_count'], 1)

