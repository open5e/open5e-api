"""
Search services for Open5e API using Elasticsearch with vector support.
"""
import json
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from haystack.query import SearchQuerySet
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Global model instance to avoid reloading
_embedding_model = None
_vector_index = None
_vector_index_loaded = False  # Add explicit loaded flag

# Query embedding cache - store recent query embeddings
_query_embedding_cache = {}
_max_cache_size = 100  # Cache up to 100 recent queries

# Fuzzy search cache - cache fuzzy results for repeated queries
_fuzzy_search_cache = {}
_fuzzy_cache_size = 50  # Smaller cache for fuzzy results

def get_embedding_model():
    """Get the singleton embedding model instance with better caching."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading sentence transformer model...")
        start_time = time.time()
        
        # Load with optimizations
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Warm up the model with a dummy encode to load everything into memory
        _ = _embedding_model.encode("warmup")
        
        load_time = time.time() - start_time
        logger.info(f"Sentence transformer loaded and warmed up in {load_time:.2f}s")
    return _embedding_model


def get_cached_query_embedding(query: str) -> np.ndarray:
    """Get query embedding with caching to avoid repeated computation."""
    global _query_embedding_cache
    
    # Normalize query for caching (lowercase, trimmed)
    cache_key = query.lower().strip()[:100]  # Truncate for consistent caching
    
    # Check cache first
    if cache_key in _query_embedding_cache:
        logger.debug(f"Using cached embedding for query: '{cache_key[:20]}...'")
        return _query_embedding_cache[cache_key]
    
    # Generate new embedding
    start_time = time.time()
    model = get_embedding_model()
    
    # Optimize encoding: disable progress bar, use float32
    embedding = model.encode(
        cache_key, 
        show_progress_bar=False,
        convert_to_tensor=False,
        normalize_embeddings=True  # Pre-normalize for faster cosine similarity
    ).astype(np.float32)
    
    embed_time = (time.time() - start_time) * 1000
    logger.debug(f"Generated new embedding in {embed_time:.1f}ms for: '{cache_key[:20]}...'")
    
    # Cache the result
    _query_embedding_cache[cache_key] = embedding
    
    # Maintain cache size limit (simple LRU by removing oldest)
    if len(_query_embedding_cache) > _max_cache_size:
        # Remove oldest entry (simple approach - could use OrderedDict for true LRU)
        oldest_key = next(iter(_query_embedding_cache))
        del _query_embedding_cache[oldest_key]
        logger.debug(f"Removed oldest cached embedding: '{oldest_key[:20]}...'")
    
    return embedding


def get_vector_index():
    """Get or build the vector index with proper caching."""
    global _vector_index, _vector_index_loaded
    
    # Return cached index if already loaded
    if _vector_index_loaded and _vector_index is not None:
        return _vector_index
    
    logger.info("Building optimized vector index...")
    start_time = time.time()
    
    # Get all documents for vector indexing - LIMIT to reduce size
    from haystack.query import SearchQuerySet
    sqs = SearchQuerySet().all()
    
    names = []
    embeddings = []
    objects = []
    
    model = get_embedding_model()
    
    # Process in batches for better performance
    batch_size = 50  # Smaller batches for memory efficiency
    count = 0
    max_docs = 1000  # Reduce to 1000 docs for faster builds
    
    batch_texts = []
    batch_objects = []
    
    for result in sqs:
        if hasattr(result, 'name') and result.name and count < max_docs:
            # Create text for embedding (name + description)
            text = result.name
            if hasattr(result, 'description') and result.description:
                text += " " + result.description[:50]  # Even shorter description
            
            batch_texts.append(text)
            batch_objects.append(result)
            count += 1
            
            # Process batch
            if len(batch_texts) >= batch_size:
                # Generate embeddings in batch (much faster)
                batch_embeddings = model.encode(
                    batch_texts,
                    show_progress_bar=False,
                    normalize_embeddings=True  # Normalize for faster similarity computation
                )
                
                for i, embedding in enumerate(batch_embeddings):
                    names.append(batch_objects[i].name)
                    embeddings.append(embedding)
                    objects.append(batch_objects[i])
                
                batch_texts = []
                batch_objects = []
    
    # Process remaining batch
    if batch_texts:
        batch_embeddings = model.encode(
            batch_texts,
            show_progress_bar=False,
            normalize_embeddings=True  # Normalize for faster similarity computation
        )
        for i, embedding in enumerate(batch_embeddings):
            names.append(batch_objects[i].name)
            embeddings.append(embedding)
            objects.append(batch_objects[i])
    
    _vector_index = {
        'names': names,
        'embeddings': np.array(embeddings, dtype=np.float32),  # Use float32 for speed
        'objects': objects
    }
    
    # Mark as loaded to prevent rebuilding
    _vector_index_loaded = True
    
    build_time = time.time() - start_time
    logger.info(f"Optimized vector index built: ({len(names)}, {len(embeddings[0]) if embeddings else 0}) in {build_time:.2f}s")
    
    return _vector_index


@dataclass
class SearchResult:
    """Represents a search result."""
    name: str
    description: str
    object_type: str
    document_name: str
    schema_version: str
    score: float
    search_type: str


class ElasticsearchSearchService:
    """Search service using Elasticsearch with vector capabilities."""
    
    def __init__(self):
        """Initialize the search service."""
        self.embedding_model = get_embedding_model()
    
    def search(
        self, 
        query: str, 
        limit: int = 50,
        search_types: List[str] = None,
        boost_factors: Dict[str, float] = None,
        filters: Dict[str, Any] = None
    ) -> List[SearchResult]:
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
        
        # Limit results
        final_results = unique_results[:limit]
        
        overall_time = (time.time() - overall_start) * 1000
        logger.info(f"Search completed: {len(final_results)} results in {overall_time:.1f}ms total")
        
        return final_results
    
    def _text_search(self, query: str, limit: int, filters: Dict[str, Any] = None) -> List[SearchResult]:
        """Perform text-based search with timing."""
        start_time = time.time()
        
        sqs_start = time.time()
        sqs = SearchQuerySet().filter(content=query)
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
                results.append(SearchResult(
                    name=result.name,
                    description=getattr(result, 'description', '') or '',
                    object_type=getattr(result, 'object_type', 'Unknown'),
                    document_name=getattr(result, 'document_name', 'Unknown'),
                    schema_version=getattr(result, 'schema_version', 'v2'),
                    score=25.0,  # High score for exact text matches
                    search_type='text'
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
        sqs = SearchQuerySet().filter(name__fuzzy=query)
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
        fetch_limit = min(limit, 30)  # Cap fuzzy results to reduce processing time
        
        for result in sqs[:fetch_limit]:
            if hasattr(result, 'name') and result.name:
                results.append(SearchResult(
                    name=result.name,
                    description=getattr(result, 'description', '') or '',
                    object_type=getattr(result, 'object_type', 'Unknown'),
                    document_name=getattr(result, 'document_name', 'Unknown'),
                    schema_version=getattr(result, 'schema_version', 'v2'),
                    score=15.0,  # Medium score for fuzzy matches
                    search_type='fuzzy'
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
        """Perform optimized vector-based semantic search with timing."""
        start_time = time.time()
        
        try:
            # Quick optimization: Cache query embeddings for repeated queries
            embed_start = time.time()
            
            # Truncate query to reasonable length to speed up embedding
            truncated_query = query[:100] if len(query) > 100 else query
            
            query_embedding = get_cached_query_embedding(truncated_query)
            embed_time = (time.time() - embed_start) * 1000
            logger.debug(f"Query embedding: {embed_time:.1f}ms")
            
            # Get vector index (should be cached now)
            index_start = time.time()
            vector_index = get_vector_index()
            index_time = (time.time() - index_start) * 1000
            logger.debug(f"Vector index access: {index_time:.1f}ms")
            
            if len(vector_index['embeddings']) == 0:
                logger.warning("Vector index is empty")
                return []
            
            # Calculate similarities more efficiently
            similarity_start = time.time()
            
            # Use faster similarity calculation for smaller indexes
            embeddings = vector_index['embeddings']
            
            # Since embeddings are normalized, use dot product instead of cosine similarity
            # This is much faster and equivalent for normalized vectors
            similarities = np.dot(query_embedding, embeddings.T)
            
            similarity_time = (time.time() - similarity_start) * 1000
            logger.debug(f"Similarity calculation: {similarity_time:.1f}ms for {len(similarities)} vectors")
            
            # Get top results efficiently
            top_start = time.time()
            
            # Use argpartition for faster top-k selection
            k = min(limit * 2, len(similarities))  # Get 2x limit for filtering
            if k > 0:
                top_indices = np.argpartition(similarities, -k)[-k:]
                # Sort only the top results
                top_indices = top_indices[np.argsort(similarities[top_indices])][::-1]
            else:
                top_indices = []
            
            results = []
            for idx in top_indices:
                if idx < len(vector_index['objects']) and similarities[idx] > 0.15:  # Lower threshold
                    obj = vector_index['objects'][idx]
                    results.append(SearchResult(
                        name=getattr(obj, 'name', 'Unknown'),
                        description=getattr(obj, 'description', '') or '',
                        object_type=getattr(obj, 'object_type', 'Unknown'),
                        document_name=getattr(obj, 'document_name', 'Unknown'),
                        schema_version=getattr(obj, 'schema_version', 'v2'),
                        score=float(similarities[idx]) * 15,  # Slightly lower scaling
                        search_type='vector'
                    ))
            
            top_time = (time.time() - top_start) * 1000
            logger.debug(f"Top results processing: {top_time:.1f}ms")
            
            total_time = (time.time() - start_time) * 1000
            logger.debug(f"Vector search total: {total_time:.1f}ms, {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
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
                'total_documents': len(vector_index['names']),
                'vector_dimensions': vector_index['embeddings'].shape[1] if len(vector_index['embeddings']) > 0 else 0,
                'elasticsearch_documents': len(list(sqs[:100])),  # Sample to avoid loading all
                'embedding_model': 'all-MiniLM-L6-v2'
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'error': str(e)}


# Global search service instance
search_service = ElasticsearchSearchService() 