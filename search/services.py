"""
Search services for Open5e API.
- Text search: Whoosh/Haystack for exact and partial word matches
- Fuzzy search: Edit distance for typo tolerance  
- Vector search: spaCy word embeddings for semantic similarity
"""
import time
import logging
import pickle
from typing import List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from haystack.query import SearchQuerySet

logger = logging.getLogger(__name__)

# Global state
_vector_index = None
_vector_index_loaded = False
_spacy_model = None

# Caches
_query_embedding_cache = {}
_fuzzy_search_cache = {}


def get_vector_index():
    """Load the pre-built semantic vector index from disk."""
    global _vector_index, _vector_index_loaded
    
    if _vector_index_loaded:
        return _vector_index
    
    _vector_index_loaded = True
    
    try:
        from pathlib import Path
        from django.conf import settings
        
        index_path = Path(settings.BASE_DIR) / "server" / "vector_index.pkl"
        
        if not index_path.exists():
            logger.warning(f"Vector index not found at {index_path}")
            _vector_index = None
            return None
            
        logger.info("Loading semantic vector index...")
        start_time = time.time()
        
        with index_path.open("rb") as fh:
            _vector_index = pickle.load(fh)
        
        load_time = time.time() - start_time
        if 'embeddings' in _vector_index:
            logger.info(f"Loaded {len(_vector_index['embeddings'])} embeddings in {load_time:.2f}s")
        
        return _vector_index
        
    except Exception as e:
        logger.error(f"Failed to load vector index: {e}")
        _vector_index = None
        return None


def get_spacy_model():
    """Get or load the spaCy model for query embedding."""
    global _spacy_model
    
    if _spacy_model is not None:
        return _spacy_model
    
    try:
        import spacy
        
        logger.info("Loading spaCy model: en_core_web_md")
        _spacy_model = spacy.load("en_core_web_md")
        _spacy_model.select_pipes(disable=["ner", "parser"])
        return _spacy_model
        
    except ImportError:
        logger.warning("spaCy not installed, vector search disabled")
        return None
    except OSError:
        logger.warning("spaCy model en_core_web_md not found, vector search disabled")
        return None
    except Exception as e:
        logger.error(f"Failed to load spaCy model: {e}")
        return None


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


class SearchService:
    """Search service combining text, fuzzy, and semantic vector search."""

    def _calculate_edit_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._calculate_edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]

    def _calculate_fuzzy_score(self, query: str, result_name: str, max_score: float = 20.0) -> float:
        """Calculate distance-based score for fuzzy matches."""
        query_norm = query.lower().strip()
        name_norm = result_name.lower().strip()
        
        distance = self._calculate_edit_distance(query_norm, name_norm)
        max_len = max(len(query_norm), len(name_norm))
        
        if max_len == 0:
            return max_score
        
        relative_distance = distance / max_len
        score = max_score * (1.0 - relative_distance)
        
        return max(score, 1.0)

    def search(
        self, 
        query: str, 
        limit: int = 50,
        search_types: List[str] = None,
        boost_factors: Dict[str, float] = None,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Perform search combining text, fuzzy, and semantic vector search."""
        start_time = time.time()
        
        if search_types is None:
            search_types = ['text', 'fuzzy', 'vector']
        
        if boost_factors is None:
            boost_factors = {'text': 1.0, 'fuzzy': 0.5, 'vector': 0.8}
        
        logger.info(f"Searching for '{query}' with types: {search_types}")
        
        all_results = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            
            if 'text' in search_types:
                futures['text'] = executor.submit(self._text_search, query, limit, filters)
            
            if 'fuzzy' in search_types:
                futures['fuzzy'] = executor.submit(self._fuzzy_search, query, limit, filters)
            
            if 'vector' in search_types:
                futures['vector'] = executor.submit(self._vector_search, query, limit, filters)
            
            for search_type, future in futures.items():
                try:
                    results = future.result()
                    boost = boost_factors.get(search_type, 1.0)
                    for result in results:
                        result.score *= boost
                        result.search_type = search_type
                        all_results.append(result)
                except Exception as e:
                    logger.error(f"Error in {search_type} search: {e}")
        
        unique_results = self._deduplicate_results(all_results)
        unique_results.sort(key=lambda x: x.score, reverse=True)
        
        total_count = len(unique_results)
        final_results = unique_results[:limit]
        
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"Search completed: {len(final_results)}/{total_count} results in {elapsed:.1f}ms")
        
        return {
            'results': final_results,
            'total_count': total_count,
            'response_time_ms': elapsed
        }

    def _text_search(self, query: str, limit: int, filters: Dict[str, Any] = None) -> List[SearchResult]:
        """Text search using Whoosh/Haystack."""
        try:
            sqs = SearchQuerySet().filter(content=query)
            
            if filters:
                for field, value in filters.items():
                    sqs = sqs.filter(**{field: value})
            
            results = []
            for result in list(sqs[:limit * 2]):
                if hasattr(result, 'name') and result.name:
                    results.append(SearchResult(
                        name=result.name,
                        description=getattr(result, 'description', '') or '',
                        object_type=getattr(result, 'object_type', 'Unknown'),
                        document_name=getattr(result, 'document_name', 'Unknown'),
                        schema_version=getattr(result, 'schema_version', 'v2'),
                        score=25.0,
                        search_type='text',
                        indexed_fields=self._extract_indexed_fields(result)
                    ))
            return results
            
        except Exception as e:
            logger.warning(f"Text search failed: {e}")
            return self._sqlite_fts_search(query, limit)

    def _sqlite_fts_search(self, query: str, limit: int) -> List[SearchResult]:
        """Fallback to SQLite FTS5."""
        from django.db import connection
        
        results = []
        try:
            with connection.cursor() as cursor:
                escaped_query = query.replace('"', '""')
                cursor.execute(
                    'SELECT object_name, object_model, schema_version, document_pk '
                    'FROM search_index WHERE search_index MATCH %s ORDER BY rank LIMIT %s',
                    [f'"{escaped_query}"', limit]
                )
                
                for name, model, schema, doc_pk in cursor.fetchall():
                    results.append(SearchResult(
                        name=name,
                        description='',
                        object_type=model,
                        document_name=doc_pk,
                        schema_version=schema,
                        score=20.0,
                        search_type='text',
                        indexed_fields={}
                    ))
        except Exception as e:
            logger.error(f"SQLite FTS search failed: {e}")
        
        return results

    def _fuzzy_search(self, query: str, limit: int, filters: Dict[str, Any] = None) -> List[SearchResult]:
        """Fuzzy search using edit distance on document names."""
        global _fuzzy_search_cache
        
        cache_key = f"{query.lower()}:{limit}"
        if cache_key in _fuzzy_search_cache:
            return _fuzzy_search_cache[cache_key]
        
        if len(query.strip()) <= 2:
            return []
        
        vector_index = get_vector_index()
        if not vector_index:
            return []
        
        names = vector_index.get('names', [])
        metadata = vector_index.get('metadata', [])
        
        scored = []
        query_lower = query.lower()
        query_first = query_lower[0] if query_lower else ''
        
        for idx, name in enumerate(names):
            name_lower = name.lower()
            
            # Pre-filter: first letter must match, or query appears as substring
            if name_lower.startswith(query_first) or query_lower in name_lower:
                score = self._calculate_fuzzy_score(query, name)
                if score > 5.0:  # Require closer match
                    scored.append((idx, score, name))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score, name in scored[:limit]:
            meta = metadata[idx] if idx < len(metadata) else {}
            results.append(SearchResult(
                name=name,
                description=meta.get('description', ''),
                object_type=meta.get('object_type', 'Unknown'),
                document_name=meta.get('document_pk', 'Unknown'),
                schema_version=meta.get('schema_version', 'v2'),
                score=score,
                search_type='fuzzy',
                indexed_fields={}
            ))
        
        _fuzzy_search_cache[cache_key] = results
        if len(_fuzzy_search_cache) > 50:
            _fuzzy_search_cache.pop(next(iter(_fuzzy_search_cache)))
        
        return results

    def _vector_search(self, query: str, limit: int, filters: Dict[str, Any] = None) -> List[SearchResult]:
        """Semantic vector search using spaCy word embeddings."""
        global _query_embedding_cache
        
        vector_index = get_vector_index()
        if not vector_index or 'embeddings' not in vector_index:
            logger.debug("Vector index not available")
            return []
        
        nlp = get_spacy_model()
        if nlp is None:
            logger.debug("spaCy model not available")
            return []
        
        cache_key = query.lower().strip()
        if cache_key in _query_embedding_cache:
            query_embedding = _query_embedding_cache[cache_key]
        else:
            doc = nlp(query)
            vectors = [token.vector for token in doc if token.has_vector]
            if vectors:
                query_embedding = np.mean(vectors, axis=0)
                norm = np.linalg.norm(query_embedding)
                if norm > 0:
                    query_embedding = query_embedding / norm
            else:
                logger.debug(f"No word vectors found for query: {query}")
                return []
            
            _query_embedding_cache[cache_key] = query_embedding
            if len(_query_embedding_cache) > 100:
                _query_embedding_cache.pop(next(iter(_query_embedding_cache)))
        
        embeddings = vector_index['embeddings']
        similarities = np.dot(embeddings, query_embedding)
        
        top_indices = np.argsort(similarities)[-limit * 2:][::-1]
        
        names = vector_index.get('names', [])
        metadata = vector_index.get('metadata', [])
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.3:
                meta = metadata[idx] if idx < len(metadata) else {}
                results.append(SearchResult(
                    name=names[idx],
                    description=meta.get('description', ''),
                    object_type=meta.get('object_type', 'Unknown'),
                    document_name=meta.get('document_pk', 'Unknown'),
                    schema_version=meta.get('schema_version', 'v2'),
                    score=float(similarities[idx]) * 25,
                    search_type='vector',
                    indexed_fields={}
                ))
        
        return results

    def _extract_indexed_fields(self, result) -> Dict[str, Any]:
        """Extract indexed fields from a Haystack result."""
        field_mappings = {
            'Spell': ['level', 'school', 'casting_time', 'spell_range', 'components', 'duration', 'classes'],
            'Creature': ['size', 'creature_type', 'challenge_rating', 'armor_class', 'hit_points'],
            'Item': ['item_type', 'rarity', 'requires_attunement'],
        }
        
        object_type = getattr(result, 'object_type', 'Unknown')
        fields_to_extract = field_mappings.get(object_type, [])
        
        indexed_fields = {}
        for field in fields_to_extract:
            if hasattr(result, field):
                value = getattr(result, field)
                if value:
                    indexed_fields[field] = value
        
        return indexed_fields

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Deduplicate by name, keeping highest score."""
        seen = {}
        for result in results:
            key = result.name.lower()
            if key not in seen or result.score > seen[key].score:
                seen[key] = result
        return list(seen.values())

    def get_stats(self) -> Dict[str, Any]:
        """Get search index statistics."""
        try:
            vector_index = get_vector_index()
            
            stats = {
                'search_backend': 'Whoosh + SQLite FTS5',
                'vector_backend': 'spaCy word embeddings',
            }
            
            if vector_index:
                stats['total_documents'] = len(vector_index.get('names', []))
                if 'embeddings' in vector_index:
                    stats['embedding_dimensions'] = vector_index['embeddings'].shape[1]
                if 'vector_size' in vector_index:
                    stats['vector_size'] = vector_index['vector_size']
            
            return stats
        except Exception as e:
            return {'error': str(e)}


search_service = SearchService()
