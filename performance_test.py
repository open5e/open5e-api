#!/usr/bin/env python3
"""Performance test to compare default mode vs strict exact-only mode."""

import time
import statistics
import requests
import sys

def test_search_performance(base_url, query, num_trials=10):
    """Test search performance for different modes."""
    
    # Test queries that likely have exact matches
    test_queries = [query] if query else [
        "fireball",     # Common spell
        "sword",        # Common weapon  
        "heal",         # Common spell
        "dragon",       # Common creature
        "magic"         # Common term
    ]
    
    results = {}
    
    for test_query in test_queries:
        print(f"\nTesting query: '{test_query}'")
        
        # Test default mode
        default_times = []
        for i in range(num_trials):
            start = time.perf_counter()
            response = requests.get(f"{base_url}/v2/search/", params={'query': test_query})
            end = time.perf_counter()
            
            if response.status_code == 200:
                default_times.append(end - start)
                if i == 0:  # Show result count for first trial
                    data = response.json()
                    exact_count = len([r for r in data.get('results', []) if r.get('match_type') == 'exact'])
                    total_count = len(data.get('results', []))
                    print(f"  Default mode: {exact_count} exact / {total_count} total results")
            else:
                print(f"  Default mode failed: {response.status_code}")
                continue
        
        # Test strict exact-only mode
        strict_times = []
        for i in range(num_trials):
            start = time.perf_counter()
            response = requests.get(f"{base_url}/v2/search/", params={'query': test_query, 'strict': 'true'})
            end = time.perf_counter()
            
            if response.status_code == 200:
                strict_times.append(end - start)
                if i == 0:  # Show result count for first trial
                    data = response.json()
                    exact_count = len(data.get('results', []))
                    print(f"  Strict exact: {exact_count} results")
            else:
                print(f"  Strict mode failed: {response.status_code}")
                continue
        
        if default_times and strict_times:
            default_avg = statistics.mean(default_times) * 1000  # Convert to ms
            strict_avg = statistics.mean(strict_times) * 1000
            speedup = (default_avg - strict_avg) / default_avg * 100
            
            print(f"  Default mode avg: {default_avg:.1f}ms")
            print(f"  Strict exact avg: {strict_avg:.1f}ms") 
            print(f"  Speedup: {speedup:.1f}% faster")
            
            results[test_query] = {
                'default_ms': default_avg,
                'strict_ms': strict_avg,
                'speedup_pct': speedup
            }
    
    # Summary
    if results:
        print(f"\n{'='*50}")
        print("SUMMARY")
        print(f"{'='*50}")
        
        all_speedups = [r['speedup_pct'] for r in results.values()]
        avg_speedup = statistics.mean(all_speedups)
        
        print(f"Average speedup across all queries: {avg_speedup:.1f}%")
        print(f"Best speedup: {max(all_speedups):.1f}%")
        print(f"Worst speedup: {min(all_speedups):.1f}%")
        
        return results
    
    return {}

if __name__ == "__main__":
    base_url = "http://localhost:8000"  # Adjust if needed
    query = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("Performance Test: Default Mode vs Strict Exact-Only")
    print(f"Base URL: {base_url}")
    print(f"Trials per query: 10")
    
    try:
        results = test_search_performance(base_url, query)
        
        if not results:
            print("\nNo successful tests completed!")
            
    except KeyboardInterrupt:
        print("\nTest interrupted!")
    except Exception as e:
        print(f"\nError: {e}") 