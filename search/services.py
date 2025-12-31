"""
Search services for Open5e API using Elasticsearch with TF-IDF vector support.
"""
import json
import time
import logging
import pickle
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from haystack.query import SearchQuerySet

logger = logging.getLogger(__name__)

# Global TF-IDF model and index
_tfidf_vectorizer = None
_tfidf_matrix = None
_vector_index = None
_vector_index_loaded = False

# Query embedding cache - store recent query embeddings
_query_embedding_cache = {}
_max_cache_size = 100  # Cache up to 100 recent queries

# Fuzzy search cache - cache fuzzy results for repeated queries
_fuzzy_search_cache = {}
_fuzzy_cache_size = 50  # Smaller cache for fuzzy results

def get_tfidf_vectorizer():
    """Get the singleton TF-IDF vectorizer instance."""
    global _tfidf_vectorizer
    
    if _tfidf_vectorizer is None:
        logger.info("Creating TF-IDF vectorizer...")
        start_time = time.time()
        
        # Create TF-IDF vectorizer with optimized parameters
        _tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,  # Limit vocabulary size for speed
            stop_words='english',
            ngram_range=(1, 2),  # Include bigrams for better semantic understanding
            min_df=2,  # Ignore terms that appear in less than 2 documents
            max_df=0.8,  # Ignore terms that appear in more than 80% of documents
            lowercase=True,
            strip_accents='unicode'
        )
        
        load_time = time.time() - start_time
        logger.info(f"TF-IDF vectorizer created in {load_time:.2f}s")
            
    return _tfidf_vectorizer

def get_cached_query_embedding(query: str):
    """Get cached query TF-IDF vector or generate new one."""
    global _query_embedding_cache
    
    # Normalize query for cache key
    cache_key = query.lower().strip()
    
    if cache_key in _query_embedding_cache:
        logger.debug(f"Using cached TF-IDF vector for: '{query[:20]}...'")
        return _query_embedding_cache[cache_key]
    
    # Generate new TF-IDF vector
    vectorizer = get_tfidf_vectorizer()
    if vectorizer is None:
        return None
    
    start_time = time.time()
    # Transform the query using the fitted vectorizer
    try:
        query_vector = vectorizer.transform([query])
        # Convert to dense array and normalize
        query_vector = query_vector.toarray()[0]
        # Normalize the vector
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm
    except Exception as e:
        logger.warning(f"Could not vectorize query '{query}': {e}")
        return None
    
    embed_time = (time.time() - start_time) * 1000
    logger.debug(f"Generated new TF-IDF vector in {embed_time:.1f}ms for: '{query[:20]}...'")
    
    # Cache the vector
    _query_embedding_cache[cache_key] = query_vector
    
    # Maintain cache size using LRU eviction
    if len(_query_embedding_cache) > _max_cache_size:
        # Remove oldest entry (first in dict for Python 3.7+)
        oldest_key = next(iter(_query_embedding_cache))
        del _query_embedding_cache[oldest_key]
        logger.debug(f"Removed oldest query vector from cache")
    
    return query_vector

def get_vector_index():
    """Get or build the TF-IDF vector index with proper caching."""
    global _tfidf_vectorizer, _tfidf_matrix, _vector_index, _vector_index_loaded
    
    # Return cached index if already loaded
    if _vector_index_loaded and _vector_index is not None:
        return _vector_index
    
    logger.info("Building TF-IDF vector index...")
    start_time = time.time()
    
    # Get all documents for vector indexing
    from haystack.query import SearchQuerySet
    sqs = SearchQuerySet().all()
    
    names = []
    documents = []
    objects = []
    
    # Collect documents and prepare texts
    count = 0
    max_docs = 2000  # Increase limit since TF-IDF is more efficient
    
    for result in sqs:
        if hasattr(result, 'name') and result.name and count < max_docs:
            # Create text for TF-IDF (name + description)
            text = result.name
            if hasattr(result, 'description') and result.description:
                # Use more of the description since TF-IDF can handle it better
                text += " " + result.description[:200]
            
            names.append(result.name)
            documents.append(text)
            objects.append(result)
            count += 1
    
    if not documents:
        logger.warning("No documents found for TF-IDF indexing")
        return None
    
    # Build TF-IDF matrix
    vectorizer = get_tfidf_vectorizer()
    logger.info(f"Fitting TF-IDF on {len(documents)} documents...")
    
    # Fit and transform documents
    tfidf_matrix = vectorizer.fit_transform(documents)
    
    # Convert to dense array and normalize rows
    tfidf_dense = tfidf_matrix.toarray()
    # Normalize each document vector
    norms = np.linalg.norm(tfidf_dense, axis=1, keepdims=True)
    norms[norms == 0] = 1  # Avoid division by zero
    tfidf_normalized = tfidf_dense / norms
    
    _tfidf_matrix = tfidf_normalized
    _vector_index = {
        'names': names,
        'embeddings': tfidf_normalized,
        'objects': objects,
        'vectorizer': vectorizer
    }
    
    # Mark as loaded to prevent rebuilding
    _vector_index_loaded = True
    
    build_time = time.time() - start_time
    logger.info(f"TF-IDF vector index built: {_vector_index['embeddings'].shape} in {build_time:.2f}s")
    
    return _vector_index

@dataclass
class SearchResult:
    """Represents a search result with score and metadata."""
    name: str
    description: str
    object_type: str
    document_name: str
    schema_version: str
    score: float
    search_type: str
    indexed_fields: Dict[str, Any] = None
    highlighted_content: List[str] = None
    fuzzy_matched_substring: str = None

class ElasticsearchSearchService:
    """Search service using Elasticsearch with TF-IDF vector capabilities."""
    
    def __init__(self):
        """Initialize the search service."""
        self.vectorizer = get_tfidf_vectorizer()
    
    def _extract_indexed_fields(self, result) -> Dict[str, Any]:
        """Extract all indexed fields from a Haystack search result."""
        indexed_fields = {}
        
        # Define the fields we want to extract based on object type
        field_mappings = {
            'Spell': ['level', 'school', 'casting_time', 'spell_range', 'components', 'duration', 'classes'],
            'Creature': ['size', 'creature_type', 'challenge_rating', 'armor_class', 'hit_points'],
            'Item': ['item_type', 'rarity', 'requires_attunement'],
            'CharacterClass': ['hit_die'],
            'Background': [],
            'Feat': [],
            'Species': []
        }
        
        # Get the object type and corresponding fields
        object_type = getattr(result, 'object_type', 'Unknown')
        fields_to_extract = field_mappings.get(object_type, [])
        
        # Extract each field if it exists
        for field in fields_to_extract:
            if hasattr(result, field):
                value = getattr(result, field)
                if value:  # Only include non-empty values
                    indexed_fields[field] = value
        
        return indexed_fields

    def _calculate_edit_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._calculate_edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        # Create distance matrix
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost of insertions, deletions, or substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]

    def _calculate_fuzzy_score(self, query: str, result_name: str, max_score: float = 20.0) -> float:
        """Calculate distance-based score for fuzzy matches."""
        # Normalize strings for comparison
        query_norm = query.lower().strip()
        name_norm = result_name.lower().strip()
        
        # Calculate edit distance
        distance = self._calculate_edit_distance(query_norm, name_norm)
        
        # Calculate relative distance (0-1)
        max_len = max(len(query_norm), len(name_norm))
        if max_len == 0:
            return max_score
        
        relative_distance = distance / max_len
        
        # Convert to score (higher score for lower distance)
        # Score ranges from max_score (perfect match) down to 1.0 (high distance)
        score = max_score * (1.0 - relative_distance)
        
        # Ensure minimum score of 1.0 for any fuzzy match
        return max(score, 1.0)
    
    def _find_fuzzy_match_substring(self, query: str, result_name: str) -> str:
        """Find the best matching substring in the result name for fuzzy highlighting."""
        query_norm = query.lower().strip()
        name_norm = result_name.lower().strip()
        
        # If query is empty or longer than name, just return the whole name
        if not query_norm or len(query_norm) > len(name_norm):
            return result_name
        
        # Try to find the best substring match using sliding window
        best_distance = float('inf')
        best_match_start = 0
        best_match_end = len(query_norm)
        
        # Try all possible substrings of length similar to query
        for start in range(len(name_norm) - len(query_norm) + 1):
            end = start + len(query_norm)
            substring = name_norm[start:end]
            distance = self._calculate_edit_distance(query_norm, substring)
            
            if distance < best_distance:
                best_distance = distance
                best_match_start = start
                best_match_end = end
        
        # Also try substrings that are slightly longer/shorter
        for length_offset in [-1, 1, -2, 2]:
            new_length = len(query_norm) + length_offset
            if new_length <= 0 or new_length > len(name_norm):
                continue
                
            for start in range(len(name_norm) - new_length + 1):
                end = start + new_length
                substring = name_norm[start:end]
                distance = self._calculate_edit_distance(query_norm, substring)
                
                if distance < best_distance:
                    best_distance = distance
                    best_match_start = start
                    best_match_end = end
        
        # Extract the best matching substring from the original (not normalized) name
        # Map the positions back to the original string
        return result_name[best_match_start:best_match_end]

    def search(
        self, 
        query: str, 
        limit: int = 50,
        search_types: List[str] = None,
        boost_factors: Dict[str, float] = None,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Perform search with detailed profiling.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            search_types: List of search types to use ['text', 'fuzzy', 'vector']
            boost_factors: Boost factors for each search type
            filters: Additional filters to apply
            
        Returns:
            List of SearchResult objects
        """
        overall_start = time.time()
        
        if search_types is None:
            search_types = ['text', 'fuzzy', 'vector']
        
        if boost_factors is None:
            boost_factors = {'text': 1.0, 'fuzzy': 0.5, 'vector': 0.3}
        
        logger.info(f"Starting search for '{query}' with types: {search_types}")
        
        all_results = []
        
        # Perform searches in parallel
        parallel_start = time.time()
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            
            if 'text' in search_types:
                futures['text'] = executor.submit(self._text_search, query, limit, filters)
            
            if 'fuzzy' in search_types:
                futures['fuzzy'] = executor.submit(self._fuzzy_search, query, limit, filters)
            
            if 'vector' in search_types:
                futures['vector'] = executor.submit(self._vector_search, query, limit, filters)
            
            # Collect results
            search_results = {}
            for search_type, future in futures.items():
                search_start = time.time()
                try:
                    search_results[search_type] = future.result()
                    search_time = (time.time() - search_start) * 1000
                    logger.info(f"{search_type.title()} search completed in {search_time:.1f}ms")
                except Exception as e:
                    logger.error(f"Error in {search_type} search: {e}")
                    search_results[search_type] = []
        
        parallel_time = (time.time() - parallel_start) * 1000
        logger.info(f"All parallel searches completed in {parallel_time:.1f}ms")
        
        # Combine and score results
        combine_start = time.time()
        
        for search_type, results in search_results.items():
            boost = boost_factors.get(search_type, 1.0)
            for result in results:
                result.score *= boost
                result.search_type = search_type
                all_results.append(result)
        
        combine_time = (time.time() - combine_start) * 1000
        logger.info(f"Result combination completed in {combine_time:.1f}ms")
        
        # Deduplicate and sort
        dedup_start = time.time()
        unique_results = self._deduplicate_results(all_results)
        dedup_time = (time.time() - dedup_start) * 1000
        logger.info(f"Deduplication completed in {dedup_time:.1f}ms")
        
        # Sort by score
        sort_start = time.time()
        unique_results.sort(key=lambda x: x.score, reverse=True)
        sort_time = (time.time() - sort_start) * 1000
        logger.info(f"Sorting completed in {sort_time:.1f}ms")
        
        # Limit results but keep total count
        total_count = len(unique_results)
        final_results = unique_results[:limit]
        
        overall_time = (time.time() - overall_start) * 1000
        logger.info(f"Search completed: {len(final_results)} of {total_count} total results in {overall_time:.1f}ms total")
        
        return {
            'results': final_results,
            'total_count': total_count,
            'response_time_ms': overall_time
        }
    
    def _text_search(self, query: str, limit: int, filters: Dict[str, Any] = None) -> List[SearchResult]:
        """Perform text-based search with timing."""
        start_time = time.time()
        
        sqs_start = time.time()
        sqs = SearchQuerySet().filter(content=query).highlight()
        sqs_time = (time.time() - sqs_start) * 1000
        logger.debug(f"Text SQS filter: {sqs_time:.1f}ms")
        
        # Apply filters
        filter_start = time.time()
        if filters:
            for field, value in filters.items():
                sqs = sqs.filter(**{field: value})
        filter_time = (time.time() - filter_start) * 1000
        logger.debug(f"Text filtering: {filter_time:.1f}ms")
        
        # Execute query and convert results
        execute_start = time.time()
        results = []
        for result in sqs[:limit * 2]:  # Get more for deduplication
            if hasattr(result, 'name') and result.name:
                # Get highlighted content if available
                highlighted = getattr(result, 'highlighted', None)
                results.append(SearchResult(
                    name=result.name,
                    description=getattr(result, 'description', '') or '',
                    object_type=getattr(result, 'object_type', 'Unknown'),
                    document_name=getattr(result, 'document_name', 'Unknown'),
                    schema_version=getattr(result, 'schema_version', 'v2'),
                    score=25.0,  # High score for exact text matches
                    search_type='text',
                    indexed_fields=self._extract_indexed_fields(result),
                    highlighted_content=highlighted if highlighted else None
                ))
        execute_time = (time.time() - execute_start) * 1000
        logger.debug(f"Text execution: {execute_time:.1f}ms")
        
        total_time = (time.time() - start_time) * 1000
        logger.debug(f"Text search total: {total_time:.1f}ms, {len(results)} results")
        
        return results
    
    def _fuzzy_search(self, query: str, limit: int, filters: Dict[str, Any] = None) -> List[SearchResult]:
        """Perform optimized fuzzy search with timing."""
        global _fuzzy_search_cache
        start_time = time.time()
        
        # Check cache first
        cache_key = f"{query.lower()}:{limit}:{str(filters) if filters else 'none'}"
        if cache_key in _fuzzy_search_cache:
            logger.debug(f"Using cached fuzzy results for: '{query[:20]}...'")
            cached_time = (time.time() - start_time) * 1000
            logger.debug(f"Fuzzy search cached: {cached_time:.1f}ms, {len(_fuzzy_search_cache[cache_key])} results")
            return _fuzzy_search_cache[cache_key]
        
        # Optimization 1: Skip fuzzy search for very short queries (likely exact matches)
        if len(query.strip()) <= 2:
            logger.debug(f"Skipping fuzzy search for very short query: '{query}'")
            return []
        
        # Optimization 2: Limit query length to prevent expensive fuzzy operations
        if len(query) > 50:
            query = query[:50]
            logger.debug(f"Truncated long query for fuzzy search")
        
        # Optimization 3: Use name-only fuzzy search instead of full content
        # This avoids expensive fuzzy matching on long descriptions
        fuzzy_start = time.time()
        # Add fuzzy search with name field highlighting  
        sqs = SearchQuerySet().filter(name__fuzzy=query).highlight(
            pre_tags=['<em>'], 
            post_tags=['</em>'], 
            fields={'name': {}}
        )
        fuzzy_time = (time.time() - fuzzy_start) * 1000
        logger.debug(f"Fuzzy SQS filter (name only): {fuzzy_time:.1f}ms")
        
        # Apply filters
        filter_start = time.time()
        if filters:
            for field, value in filters.items():
                sqs = sqs.filter(**{field: value})
        filter_time = (time.time() - filter_start) * 1000
        logger.debug(f"Fuzzy filtering: {filter_time:.1f}ms")
        
        # Optimization 4: Reduce fetch limit for fuzzy search since it's expensive
        # Fuzzy search is less precise anyway, so fewer results are acceptable
        execute_start = time.time()
        results = []
        fetch_limit = min(limit, 100)  # Reasonable cap for fuzzy results
        
        for result in sqs[:fetch_limit]:
            if hasattr(result, 'name') and result.name:
                # Calculate distance-based score for this fuzzy match
                fuzzy_score = self._calculate_fuzzy_score(query, result.name)
                # Get highlighted content if available
                highlighted = getattr(result, 'highlighted', None)
                # Find the best matching substring for fuzzy highlighting
                matched_substring = self._find_fuzzy_match_substring(query, result.name)
                results.append(SearchResult(
                    name=result.name,
                    description=getattr(result, 'description', '') or '',
                    object_type=getattr(result, 'object_type', 'Unknown'),
                    document_name=getattr(result, 'document_name', 'Unknown'),
                    schema_version=getattr(result, 'schema_version', 'v2'),
                    score=fuzzy_score,  # Distance-based score for fuzzy matches
                    search_type='fuzzy',
                    indexed_fields=self._extract_indexed_fields(result),
                    highlighted_content=highlighted if highlighted else None,
                    fuzzy_matched_substring=matched_substring
                ))
        
        execute_time = (time.time() - execute_start) * 1000
        logger.debug(f"Fuzzy execution: {execute_time:.1f}ms")
        
        # Cache the results
        _fuzzy_search_cache[cache_key] = results
        
        # Maintain cache size
        if len(_fuzzy_search_cache) > _fuzzy_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(_fuzzy_search_cache))
            del _fuzzy_search_cache[oldest_key]
            logger.debug(f"Removed oldest fuzzy cache entry")
        
        total_time = (time.time() - start_time) * 1000
        logger.debug(f"Fuzzy search total: {total_time:.1f}ms, {len(results)} results")
        
        return results
    
    def _vector_search(self, query: str, limit: int, filters: Dict[str, Any] = None) -> List[SearchResult]:
        """Perform TF-IDF-based semantic search with timing."""
        start_time = time.time()
        
        try:
            # Get query TF-IDF vector
            embed_start = time.time()
            
            # Truncate query to reasonable length
            truncated_query = query[:100] if len(query) > 100 else query
            
            query_vector = get_cached_query_embedding(truncated_query)
            if query_vector is None:
                logger.debug("Could not generate query TF-IDF vector, skipping vector search")
                return []
                
            embed_time = (time.time() - embed_start) * 1000
            logger.debug(f"Query TF-IDF vector: {embed_time:.1f}ms")
            
            # Get TF-IDF index
            index_start = time.time()
            vector_index = get_vector_index()
            if vector_index is None or len(vector_index['embeddings']) == 0:
                logger.debug("TF-IDF index not available, skipping vector search")
                return []
                
            index_time = (time.time() - index_start) * 1000
            logger.debug(f"TF-IDF index access: {index_time:.1f}ms")
            
            # Calculate cosine similarities
            similarity_start = time.time()
            
            embeddings = vector_index['embeddings']
            
            # Use cosine similarity for TF-IDF vectors
            similarities = np.dot(embeddings, query_vector)
            
            similarity_time = (time.time() - similarity_start) * 1000
            logger.debug(f"TF-IDF similarity calculation: {similarity_time:.1f}ms for {len(similarities)} vectors")
            
            # Get top results efficiently
            top_start = time.time()
            
            # Use argpartition for faster top-k selection
            k = min(limit * 2, len(similarities))
            if k > 0:
                top_indices = np.argpartition(similarities, -k)[-k:]
                # Sort only the top results
                top_indices = top_indices[np.argsort(similarities[top_indices])][::-1]
            else:
                top_indices = []
            
            results = []
            for idx in top_indices:
                if idx < len(vector_index['objects']) and similarities[idx] > 0.01:  # Very low threshold for TF-IDF
                    obj = vector_index['objects'][idx]
                    results.append(SearchResult(
                        name=getattr(obj, 'name', 'Unknown'),
                        description=getattr(obj, 'description', '') or '',
                        object_type=getattr(obj, 'object_type', 'Unknown'),
                        document_name=getattr(obj, 'document_name', 'Unknown'),
                        schema_version=getattr(obj, 'schema_version', 'v2'),
                        score=float(similarities[idx]) * 20,  # Scale TF-IDF scores
                        search_type='vector',
                        indexed_fields=self._extract_indexed_fields(obj)
                    ))
            
            top_time = (time.time() - top_start) * 1000
            logger.debug(f"Top results processing: {top_time:.1f}ms")
            
            total_time = (time.time() - start_time) * 1000
            logger.debug(f"TF-IDF vector search total: {total_time:.1f}ms, {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"TF-IDF vector search error: {e}")
            # Return empty results instead of crashing
            return []
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Deduplicate results by name, keeping highest score."""
        start_time = time.time()
        
        seen = {}
        for result in results:
            key = result.name.lower()
            if key not in seen or result.score > seen[key].score:
                seen[key] = result
        
        dedup_time = (time.time() - start_time) * 1000
        logger.debug(f"Deduplication processed {len(results)} -> {len(seen)} in {dedup_time:.1f}ms")
        
        return list(seen.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search index statistics."""
        try:
            vector_index = get_vector_index()
            sqs = SearchQuerySet().all()
            
            return {
                'total_documents': len(vector_index['names']) if vector_index else 0,
                'vector_dimensions': vector_index['embeddings'].shape[1] if vector_index and len(vector_index['embeddings']) > 0 else 0,
                'elasticsearch_documents': len(list(sqs[:100])),  # Sample to avoid loading all
                'embedding_model': 'TF-IDF (scikit-learn)',
                'vectorizer_features': len(vector_index['vectorizer'].get_feature_names_out()) if vector_index else 0
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'error': str(e)}


# Global search service instance
search_service = ElasticsearchSearchService() 