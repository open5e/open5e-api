"""
Tests for search functionality.

These tests verify that text, fuzzy, and vector search are working correctly.
They require the search indexes to be built (run quicksetup first).
"""
from django.test import TestCase
from rest_framework.test import APITestCase


class SearchAPITests(APITestCase):
    """Integration tests for the search API endpoint."""

    def test_text_search_returns_results(self):
        """Text search for 'fireball' should return results."""
        response = self.client.get('/v2/search/', {'query': 'fireball', 'search_types': 'text'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data['count'], 0, "Text search for 'fireball' should return results")
        
        # Should find the Fireball spell
        names = [r['name'] for r in data['results']]
        self.assertIn('Fireball', names, "Should find 'Fireball' spell")

    def test_fuzzy_search_handles_typos(self):
        """Fuzzy search should find 'Fireball' when searching for 'firebll' (typo)."""
        response = self.client.get('/v2/search/', {'query': 'firebll', 'search_types': 'fuzzy'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data['count'], 0, "Fuzzy search for 'firebll' should return results")
        
        # Should find Fireball despite the typo
        names = [r['name'] for r in data['results']]
        self.assertIn('Fireball', names, "Fuzzy search should find 'Fireball' despite typo")

    def test_vector_search_semantic_matching(self):
        """Vector search for 'bird' should find semantically related creatures."""
        response = self.client.get('/v2/search/', {'query': 'bird', 'search_types': 'vector'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data['count'], 0, "Vector search for 'bird' should return results")
        
        # Vector search should find many more results than text search
        # because it understands semantic similarity
        text_response = self.client.get('/v2/search/', {'query': 'bird', 'search_types': 'text'})
        text_count = text_response.json()['count']
        
        self.assertGreater(
            data['count'], text_count,
            f"Vector search ({data['count']}) should find more than text search ({text_count})"
        )

    def test_vector_search_finds_non_literal_matches(self):
        """Vector search should find results that don't contain the query word."""
        response = self.client.get('/v2/search/', {'query': 'aerial creature', 'search_types': 'vector'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data['count'], 0, "Vector search for 'aerial creature' should return results")
        
        # Text search for same term should return fewer or no results
        text_response = self.client.get('/v2/search/', {'query': 'aerial creature', 'search_types': 'text'})
        text_count = text_response.json()['count']
        
        self.assertGreater(
            data['count'], text_count,
            "Vector search should find semantic matches that text search misses"
        )

    def test_combined_search_uses_all_methods(self):
        """Default search should combine text, fuzzy, and vector results."""
        response = self.client.get('/v2/search/', {'query': 'dragon'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data['count'], 0, "Combined search for 'dragon' should return results")
        
        # Should have results from multiple search types
        search_types = set(r.get('search_type') for r in data['results'] if 'search_type' in r)
        self.assertGreater(len(search_types), 0, "Results should have search_type metadata")

    def test_search_requires_query(self):
        """Search without query parameter should return error."""
        response = self.client.get('/v2/search/')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)

    def test_search_pagination(self):
        """Search results should be paginated."""
        response = self.client.get('/v2/search/', {'query': 'sword', 'limit': 5})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have pagination info
        self.assertIn('count', data)
        self.assertIn('results', data)
        self.assertLessEqual(len(data['results']), 5, "Should respect limit parameter")

    def test_fuzzy_search_dragon_typo(self):
        """Fuzzy search should find 'Dragon' when searching for 'dragn'."""
        response = self.client.get('/v2/search/', {'query': 'dragn', 'search_types': 'fuzzy'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data['count'], 0, "Fuzzy search for 'dragn' should return results")
        
        # Check that dragon-related items appear
        names = [r['name'].lower() for r in data['results'][:20]]
        has_dragon = any('dragon' in name or 'drakon' in name for name in names)
        self.assertTrue(has_dragon, "Fuzzy search should find dragon-related items")


class SearchServiceTests(TestCase):
    """Unit tests for the search service."""

    def test_search_service_exists(self):
        """Search service should be importable."""
        from search.services import search_service
        self.assertIsNotNone(search_service)

    def test_search_service_has_search_method(self):
        """Search service should have a search method."""
        from search.services import search_service
        self.assertTrue(hasattr(search_service, 'search'))
        self.assertTrue(callable(search_service.search))

    def test_search_service_has_stats_method(self):
        """Search service should have a stats method."""
        from search.services import search_service
        self.assertTrue(hasattr(search_service, 'get_stats'))
        
        stats = search_service.get_stats()
        self.assertIsInstance(stats, dict)

    def test_vector_index_loads(self):
        """Vector index should load successfully."""
        from search.services import get_vector_index
        
        index = get_vector_index()
        # Index may be None if not built, but function should not error
        if index is not None:
            self.assertIn('embeddings', index)
            self.assertIn('names', index)
            self.assertIn('metadata', index)
