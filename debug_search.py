import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from search.viewsets import SearchResultViewSet
from unittest.mock import Mock
from rapidfuzz import fuzz

# Test the similarity score directly
print("=== Direct similarity test ===")
print(f"'birb' vs 'bird': {fuzz.ratio('birb', 'bird')}")
print(f"Threshold is: 75")

request = Mock()
request.path = '/v2/search/'

viewset = SearchResultViewSet()
viewset.request = request

test_queries = ['birb', 'BIRB', 'Birb', 'bird', 'BIRD', 'Bird']

for query in test_queries:
    print(f"\n=== Testing '{query}' ===")
    try:
        results = viewset._fuzzy_search(query, 'v2', '%', '%')
        print(f'Found {len(results)} fuzzy results')
        for i, (pk, highlighted, matched_term, score) in enumerate(results[:2]):
            print(f'{i+1}. matched_term: {matched_term}, score: {score:.3f}')
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc() 