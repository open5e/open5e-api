#!/usr/bin/env python3
"""Benchmark vector search methods."""

import time
import statistics
import os
import sys
import django

# Setup Django
sys.path.append('/Users/moody/open5e-api')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from search.viewsets import SearchResultViewSet

def benchmark_vector_methods(queries=None, trials=5):
    """Benchmark different vector search approaches."""
    
    test_queries = queries or [
        "fireball",     # Common spell
        "sword",        # Common weapon  
        "heal",         # Common spell
        "dragon",       # Common creature
        "lightning"     # Another spell
    ]
    
    viewset = SearchResultViewSet()
    search_args_base = ('v2', '%', '%')  # schema, document_pk, object_model
    
    results = {}
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        search_args = (query,) + search_args_base
        
        # Test full vector search
        full_times = []
        for i in range(trials):
            start = time.perf_counter()
            full_results = viewset._vector_search(*search_args)
            end = time.perf_counter()
            full_times.append(end - start)
            if i == 0:
                full_count = len(full_results)
                print(f"  Full search: {full_count} results")
        
        # Test count-only vector search  
        count_times = []
        for i in range(trials):
            start = time.perf_counter()
            count_result = viewset._vector_search_count(*search_args)
            end = time.perf_counter()
            count_times.append(end - start)
            if i == 0:
                print(f"  Count search: {count_result} results")
        
        # Test exists-only vector search
        exists_times = []
        for i in range(trials):
            start = time.perf_counter()
            exists_result = viewset._vector_search_exists(*search_args)
            end = time.perf_counter()
            exists_times.append(end - start)
            if i == 0:
                print(f"  Exists search: {exists_result}")
        
        # Calculate averages
        full_avg = statistics.mean(full_times) * 1000
        count_avg = statistics.mean(count_times) * 1000
        exists_avg = statistics.mean(exists_times) * 1000
        
        print(f"  Full vector avg: {full_avg:.1f}ms")
        print(f"  Count only avg: {count_avg:.1f}ms ({((full_avg-count_avg)/full_avg*100):.1f}% faster)")
        print(f"  Exists only avg: {exists_avg:.1f}ms ({((full_avg-exists_avg)/full_avg*100):.1f}% faster)")
        
        results[query] = {
            'full_ms': full_avg,
            'count_ms': count_avg, 
            'exists_ms': exists_avg,
            'count_speedup': (full_avg-count_avg)/full_avg*100,
            'exists_speedup': (full_avg-exists_avg)/full_avg*100
        }
    
    # Summary
    if results:
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        
        all_count_speedups = [r['count_speedup'] for r in results.values()]
        all_exists_speedups = [r['exists_speedup'] for r in results.values()]
        
        avg_count_speedup = statistics.mean(all_count_speedups)
        avg_exists_speedup = statistics.mean(all_exists_speedups)
        
        print(f"Count-only average speedup: {avg_count_speedup:.1f}%")
        print(f"Exists-only average speedup: {avg_exists_speedup:.1f}%")
        print(f"Best count speedup: {max(all_count_speedups):.1f}%")
        print(f"Best exists speedup: {max(all_exists_speedups):.1f}%")
        
        return results
    
    return {}

if __name__ == "__main__":
    print("Vector Search Performance Benchmark")
    print("Testing: Full vs Count-only vs Exists-only")
    print(f"Trials per method: 5")
    
    try:
        results = benchmark_vector_methods()
        
        if not results:
            print("\nNo successful tests completed!")
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc() 