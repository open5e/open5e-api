#!/usr/bin/env python3

import os
import sys
import django
import time
import requests
from statistics import mean

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
sys.path.append('/Users/moody/open5e-api')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Add parent directory
django.setup()

def time_search(query, params=None):
    """Time a search request and return timing + result info."""
    url = "http://127.0.0.1:8000/v2/search/"
    search_params = {"query": query}
    if params:
        search_params.update(params)
    
    start_time = time.time()
    response = requests.get(url, params=search_params)
    end_time = time.time()
    
    if response.status_code != 200:
        return None, f"Error: {response.status_code}"
    
    data = response.json()
    timing = (end_time - start_time) * 1000  # Convert to milliseconds
    
    # Just get the total count
    total_results = data.get('count', 0)
    metadata = data.get('search_metadata', {})
    exact_matches = metadata.get('exact_matches', False)
    
    return timing, {
        'total_results': total_results,
        'exact_matches': exact_matches
    }

def run_performance_test():
    """Run simplified performance comparison of search modes."""
    
    # Test queries covering different scenarios
    test_queries = [
        "fire",           # Common term, many exact matches
        "sword",          # Common term, many exact matches
        "heal",           # Common term, some matches
        "dragon",         # Common term, many matches
        "fireball",       # Specific spell, exact matches
        "teleport",       # Specific spell, exact matches
        "magic weapon",   # Multi-word, exact matches
        "chromatic orb",  # Specific spell, few matches
        "firbal",         # Typo, fuzzy fallback
        "dragn",          # Typo, fuzzy fallback
    ]
    
    results_table = []
    
    print("Search Mode Performance Comparison")
    print("=" * 80)
    print("Testing: Default (exact + fuzzy fallback) vs Fuzzy-strict vs Vector-strict")
    print()
    
    for query in test_queries:
        print(f"Testing '{query}'...")
        
        # Test Default mode (exact + fuzzy fallback if needed)
        default_times = []
        default_info = None
        for _ in range(3):
            timing, info = time_search(query)
            if timing is not None:
                default_times.append(timing)
                if default_info is None:
                    default_info = info
        
        # Test Fuzzy-strict mode
        fuzzy_times = []
        fuzzy_info = None
        for _ in range(3):
            timing, info = time_search(query, {"strict": "true", "fuzzy": "true"})
            if timing is not None:
                fuzzy_times.append(timing)
                if fuzzy_info is None:
                    fuzzy_info = info
        
        # Test Vector-strict mode
        vector_times = []
        vector_info = None
        for _ in range(3):
            timing, info = time_search(query, {"strict": "true", "vector": "true"})
            if timing is not None:
                vector_times.append(timing)
                if vector_info is None:
                    vector_info = info
        
        # Calculate averages and format results
        default_avg = mean(default_times) if default_times else 0
        fuzzy_avg = mean(fuzzy_times) if fuzzy_times else 0
        vector_avg = mean(vector_times) if vector_times else 0
        
        # Format result information
        def format_results(info):
            if not info:
                return "Error"
            total = info['total_results']
            return f"{total}"
        
        results_table.append({
            'query': query,
            'default_time': default_avg,
            'default_results': format_results(default_info),
            'fuzzy_time': fuzzy_avg,
            'fuzzy_results': format_results(fuzzy_info),
            'vector_time': vector_avg,
            'vector_results': format_results(vector_info)
        })
    
    # Output markdown table
    print("\nResults (Markdown Table):")
    print("=" * 80)
    print("| Query | Default Mode | | Fuzzy-Strict | | Vector-Strict | |")
    print("|-------|-------------|---|-------------|---|-------------|---|")
    print("| | Time (ms) | Results | Time (ms) | Results | Time (ms) | Results |")
    
    for row in results_table:
        print(f"| {row['query']} | {row['default_time']:.1f} | {row['default_results']} | "
              f"{row['fuzzy_time']:.1f} | {row['fuzzy_results']} | "
              f"{row['vector_time']:.1f} | {row['vector_results']} |")
    
    print()
    print("Legend:")
    print("- Default Mode: Runs exact search, falls back to fuzzy if exact finds 0 results")
    print("- Fuzzy-Strict: Only fuzzy search")
    print("- Vector-Strict: Only vector search")
    print("- Results: Total matches found across all pages (API returns 50 per page)")

if __name__ == "__main__":
    print("Starting simplified search performance comparison...")
    print("Make sure the Django dev server is running on http://127.0.0.1:8000")
    print()
    
    try:
        # Quick connectivity test
        response = requests.get("http://127.0.0.1:8000/v2/search/", params={"query": "test"})
        if response.status_code != 200:
            print(f"Server connectivity issue: {response.status_code}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("Cannot connect to server. Please start the Django dev server first:")
        print("python manage.py runserver")
        sys.exit(1)
    
    run_performance_test() 