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

def clear_cache():
    """Clear Redis cache to ensure fresh test."""
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        client.flushall()
        return True
    except:
        return False

def time_search(query, params=None, no_limit=False):
    """Time a search request and return timing + result info."""
    url = "http://127.0.0.1:8000/v2/search/"
    search_params = {"query": query}
    if params:
        search_params.update(params)
    
    # Remove limit to get all results for performance testing
    if no_limit:
        search_params["limit"] = 99999999
    
    start_time = time.time()
    response = requests.get(url, params=search_params)
    end_time = time.time()
    
    if response.status_code != 200:
        return None, f"Error: {response.status_code}"
    
    data = response.json()
    timing = (end_time - start_time) * 1000  # Convert to milliseconds
    
    # Get result information
    total_results = data.get('count', 0)
    metadata = data.get('search_metadata', {})
    exact_matches = metadata.get('exact_matches', False)
    
    return timing, {
        'total_results': total_results,
        'exact_matches': exact_matches,
        'metadata': metadata
    }

def run_performance_test():
    """Run performance comparison with caching effects."""
    
    # Test queries covering different scenarios
    test_queries = [
        "fire",           # Common term, many exact matches
        "sword",          # Common term, many exact matches
        "fireball",       # Specific spell, exact matches
        "magic weapon",   # Multi-word, exact matches
        "firbal",         # Typo, fuzzy fallback
        "dragn",          # Typo, fuzzy fallback
        "healing",        # Common term for testing
        "teleport",       # Specific spell
    ]
    
    results_table = []
    
    print("Search Performance Comparison with Caching Effects")
    print("=" * 100)
    print("Testing: Default (exact + fuzzy fallback) vs Fuzzy-strict vs Vector-strict")
    print("Each test runs twice: COLD (no cache) and HOT (cached)")
    print("Using no limit to test full performance impact")
    print()
    
    for query in test_queries:
        print(f"Testing '{query}'...")
        
        # Test Default mode (exact + fuzzy fallback if needed)
        print("  Default mode...")
        clear_cache()
        cold_timing, cold_info = time_search(query, no_limit=True)
        hot_timing, hot_info = time_search(query, no_limit=True)
        default_cold = cold_timing if cold_timing else 0
        default_hot = hot_timing if hot_timing else 0
        default_info = cold_info if cold_info else {}
        
        # Test Fuzzy-strict mode
        print("  Fuzzy-strict mode...")
        clear_cache()
        cold_timing, cold_info = time_search(query, {"strict": "true", "fuzzy": "true"}, no_limit=True)
        hot_timing, hot_info = time_search(query, {"strict": "true", "fuzzy": "true"}, no_limit=True)
        fuzzy_cold = cold_timing if cold_timing else 0
        fuzzy_hot = hot_timing if hot_timing else 0
        fuzzy_info = cold_info if cold_info else {}
        
        # Test Vector-strict mode
        print("  Vector-strict mode...")
        clear_cache()
        cold_timing, cold_info = time_search(query, {"strict": "true", "vector": "true"}, no_limit=True)
        hot_timing, hot_info = time_search(query, {"strict": "true", "vector": "true"}, no_limit=True)
        vector_cold = cold_timing if cold_timing else 0
        vector_hot = hot_timing if hot_timing else 0
        vector_info = cold_info if cold_info else {}
        
        # Test Combined mode (all search types)
        print("  Combined mode...")
        clear_cache()
        cold_timing, cold_info = time_search(query, {"fuzzy": "true", "vector": "true"}, no_limit=True)
        hot_timing, hot_info = time_search(query, {"fuzzy": "true", "vector": "true"}, no_limit=True)
        combined_cold = cold_timing if cold_timing else 0
        combined_hot = hot_timing if hot_timing else 0
        combined_info = cold_info if cold_info else {}
        
        # Format result information
        def format_results(info):
            if not info:
                return "Error", "N/A"
            total = info['total_results']
            meta = info.get('metadata', {})
            exact = meta.get('exact_matches', False)
            return total, "exact" if exact else "fuzzy/vector"
        
        def format_cache_improvement(cold, hot):
            if cold <= 0 or hot <= 0:
                return "N/A"
            improvement = ((cold - hot) / cold) * 100
            return f"{improvement:.1f}%"
        
        default_results, default_type = format_results(default_info)
        fuzzy_results, fuzzy_type = format_results(fuzzy_info)
        vector_results, vector_type = format_results(vector_info)
        combined_results, combined_type = format_results(combined_info)
        
        results_table.append({
            'query': query,
            'default_cold': default_cold,
            'default_hot': default_hot,
            'default_results': default_results,
            'default_type': default_type,
            'default_cache_improvement': format_cache_improvement(default_cold, default_hot),
            'fuzzy_cold': fuzzy_cold,
            'fuzzy_hot': fuzzy_hot,
            'fuzzy_results': fuzzy_results,
            'fuzzy_cache_improvement': format_cache_improvement(fuzzy_cold, fuzzy_hot),
            'vector_cold': vector_cold,
            'vector_hot': vector_hot,
            'vector_results': vector_results,
            'vector_cache_improvement': format_cache_improvement(vector_cold, vector_hot),
            'combined_cold': combined_cold,
            'combined_hot': combined_hot,
            'combined_results': combined_results,
            'combined_cache_improvement': format_cache_improvement(combined_cold, combined_hot),
        })
    
    # Output detailed results table
    print("\nDetailed Results (All times in milliseconds):")
    print("=" * 120)
    print("| Query | Default Mode | | | Fuzzy-Strict | | Vector-Strict | | Combined Mode | |")
    print("|-------|-------------|---|---|-------------|---|-------------|---|-------------|---|")
    print("| | Cold | Hot | Cache↑ | Cold | Hot | Cold | Hot | Cold | Hot | Cache↑ |")
    
    for row in results_table:
        print(f"| {row['query']:<12} | "
              f"{row['default_cold']:.0f} | {row['default_hot']:.0f} | {row['default_cache_improvement']:<6} | "
              f"{row['fuzzy_cold']:.0f} | {row['fuzzy_hot']:.0f} | "
              f"{row['vector_cold']:.0f} | {row['vector_hot']:.0f} | "
              f"{row['combined_cold']:.0f} | {row['combined_hot']:.0f} | {row['combined_cache_improvement']:<6} |")
    
    # Summary table with results
    print("\nResults Summary:")
    print("=" * 80)
    print("| Query | Default | Fuzzy | Vector | Combined | Match Type |")
    print("|-------|---------|-------|--------|----------|------------|")
    
    for row in results_table:
        print(f"| {row['query']:<12} | "
              f"{row['default_results']:<7} | {row['fuzzy_results']:<5} | {row['vector_results']:<6} | "
              f"{row['combined_results']:<8} | {row['default_type']:<10} |")
    
    # Performance summary
    print("\nPerformance Summary:")
    print("=" * 50)
    
    # Calculate averages
    default_cold_avg = mean([row['default_cold'] for row in results_table if row['default_cold'] > 0])
    default_hot_avg = mean([row['default_hot'] for row in results_table if row['default_hot'] > 0])
    combined_cold_avg = mean([row['combined_cold'] for row in results_table if row['combined_cold'] > 0])
    combined_hot_avg = mean([row['combined_hot'] for row in results_table if row['combined_hot'] > 0])
    
    print(f"Average Default Mode (Cold):  {default_cold_avg:.1f}ms")
    print(f"Average Default Mode (Hot):   {default_hot_avg:.1f}ms")
    print(f"Average Combined Mode (Cold): {combined_cold_avg:.1f}ms")
    print(f"Average Combined Mode (Hot):  {combined_hot_avg:.1f}ms")
    print()
    print(f"Cache improvement (Default):  {((default_cold_avg - default_hot_avg) / default_cold_avg * 100):.1f}%")
    print(f"Cache improvement (Combined): {((combined_cold_avg - combined_hot_avg) / combined_cold_avg * 100):.1f}%")
    
    print()
    print("Legend:")
    print("- Default Mode: Exact search, falls back to fuzzy if 0 exact results")
    print("- Fuzzy-Strict: Only fuzzy search")
    print("- Vector-Strict: Only vector search") 
    print("- Combined Mode: Exact + Fuzzy + Vector (all enabled)")
    print("- Cold: No cache (first run)")
    print("- Hot: Cached (second run)")
    print("- Cache↑: Performance improvement from caching")

if __name__ == "__main__":
    print("Starting comprehensive search performance benchmark...")
    print("Make sure the Django dev server is running on http://127.0.0.1:8000")
    print("Make sure Redis is running for cache testing")
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
    
    # Test cache connectivity
    if not clear_cache():
        print("WARNING: Cannot connect to Redis. Cache testing will not work properly.")
        print("Make sure Redis is running: brew services start redis")
        print()
    
    run_performance_test() 