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
    
    # Extract result counts from metadata and results
    metadata = data.get('search_metadata', {})
    total_results = data.get('count', 0)
    exact_matches = metadata.get('exact_matches', False)
    suggestion = metadata.get('suggestion', {})
    vector_suggestion_count = suggestion.get('additional_matches', 0) if suggestion else 0
    
    return timing, {
        'total_results': total_results,
        'exact_matches': exact_matches,
        'vector_suggestions': vector_suggestion_count
    }

def run_performance_test():
    """Run comprehensive performance comparison."""
    
    # Diverse test queries covering different scenarios
    test_queries = [
        # Short, common terms
        "fire",           # Likely many matches
        "sword",          # Likely many matches  
        "heal",           # Likely some matches
        "dragon",         # Likely some matches
        
        # Longer single terms
        "fireball",       # Specific spell, likely exact matches
        "teleport",       # Specific spell, likely exact matches
        "invisible",      # Descriptive term, moderate matches
        "legendary",      # Common descriptor, many matches
        
        # Multi-word terms
        "magic weapon",   # Common combination, many matches
        "chromatic orb",  # Specific spell, few exact matches
        
        # Edge cases
        "the",            # Very common word, massive exact matches
        "dragn",          # Misspelled "dragon", should trigger fuzzy fallback with many matches
    ]
    
    print("Performance Comparison: Default Mode vs Exact+Strict Mode")
    print("=" * 90)
    print(f"{'Query':<15} {'Default (ms)':<12} {'Exact+Strict (ms)':<17} {'Speedup':<8} {'Default Results':<15} {'Strict Results':<14}")
    print("-" * 90)
    
    improvements = []
    
    for query in test_queries:
        # Test default mode (multiple runs for accuracy)
        default_times = []
        default_results = None
        for _ in range(3):
            timing, results = time_search(query)
            if timing is not None:
                default_times.append(timing)
                if default_results is None:
                    default_results = results
        
        if not default_times:
            print(f"{query:<15} {'ERROR':<12} {'ERROR':<17} {'N/A':<8}")
            continue
            
        default_avg = mean(default_times)
        
        # Test exact+strict mode (multiple runs for accuracy)
        strict_times = []
        strict_results = None
        for _ in range(3):
            timing, results = time_search(query, {"strict": "true"})
            if timing is not None:
                strict_times.append(timing)
                if strict_results is None:
                    strict_results = results
        
        if not strict_times:
            print(f"{query:<15} {default_avg:<12.1f} {'ERROR':<17} {'N/A':<8}")
            continue
            
        strict_avg = mean(strict_times)
        
        # Calculate improvement
        speedup = ((default_avg - strict_avg) / default_avg) * 100
        improvements.append(speedup)
        
        # Format result information
        default_info = f"T:{default_results['total_results']}"
        if default_results['exact_matches']:
            default_info += " E:✓"
        if default_results['vector_suggestions'] > 0:
            default_info += f" V:{default_results['vector_suggestions']}"
            
        strict_info = f"T:{strict_results['total_results']}"
        if strict_results['exact_matches']:
            strict_info += " E:✓"
        if strict_results['vector_suggestions'] > 0:
            strict_info += f" V:{strict_results['vector_suggestions']}"
        
        print(f"{query:<15} {default_avg:<12.1f} {strict_avg:<17.1f} {speedup:<7.1f}% {default_info:<15} {strict_info:<14}")
    
    print("-" * 90)
    
    if improvements:
        avg_improvement = mean(improvements)
        positive_improvements = [x for x in improvements if x > 0]
        
        print(f"\nSummary:")
        print(f"Average performance change: {avg_improvement:.1f}%")
        if positive_improvements:
            print(f"Average improvement (positive cases): {mean(positive_improvements):.1f}%")
        print(f"Queries with performance improvement: {len(positive_improvements)}/{len(improvements)}")
    
    print(f"\nLegend:")
    print(f"T:X = Total results returned")
    print(f"E:✓ = Has exact matches") 
    print(f"V:X = Vector suggestions available")

if __name__ == "__main__":
    print("Starting performance comparison...")
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