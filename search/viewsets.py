"""Clean search implementation with exact, fuzzy, and vector search."""
import pickle
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode

from rapidfuzz import process, fuzz
from rest_framework import viewsets
from rest_framework.response import Response

from search import models, serializers


class ResultsWithMetadata(list):
    """Custom list that can hold search metadata and behaves like a QuerySet."""
    def __init__(self, items, metadata=None):
        super().__init__(items)
        self._search_metadata = metadata
        # Add model attribute to satisfy DRF expectations
        self.model = models.SearchResult


class SearchResultViewSet(viewsets.ReadOnlyModelViewSet):
    """Unified search across exact text, fuzzy, and vector search methods."""

    serializer_class = serializers.SearchResultSerializer
    
    # Configuration
    VECTOR_INDEX_PATH = Path('server/vector_index.pkl')
    FUZZY_THRESHOLD = 75
    VECTOR_THRESHOLD = 0.05
    DEFAULT_LIMIT = 50

    def _parse_parameters(self):
        """Parse search parameters from request."""
        # Auto-detect schema version from URL path
        path = self.request.path
        if '/v1/' in path:
            schema_version = 'v1'
        elif '/v2/' in path:
            schema_version = 'v2'
        else:
            schema_version = 'v2'  # default
            
        return {
            'query': self.request.query_params.get('query'),
            'include_vector': self.request.query_params.get("vector", "false").lower() in ["1", "true", "yes"],
            'include_fuzzy': self.request.query_params.get("fuzzy", "false").lower() in ["1", "true", "yes"],
            'strict': self.request.query_params.get("strict", "false").lower() in ["1", "true", "yes"],
            'schema_version': self.request.query_params.get("schema", schema_version),
            'document_pk': self.request.query_params.get("document_pk", '%'),
            'object_model': self.request.query_params.get("object_model", '%')
        }

    def _load_index(self):
        """Load the search index."""
        if not hasattr(self, '_index'):
            with self.VECTOR_INDEX_PATH.open('rb') as f:
                self._index = pickle.load(f)
        return self._index

    def _exact_search(self, query, schema_version, document_pk, object_model):
        """Exact text search using SQLite FTS5."""
        sql = """
            SELECT 1 as id,
                   rank,
                   snippet(search_index, 4, '<span class="highlighted">', '</span>', '...', 20) as highlighted,
                   document_pk, object_pk, object_name, object_model, text, schema_version
            FROM search_index 
            WHERE schema_version LIKE %s 
              AND document_pk LIKE %s
              AND object_model LIKE %s
              AND search_index MATCH %s
              AND rank MATCH 'bm25(1.0, 1.0, 10.0)'
            ORDER BY rank
        """
        
        try:
            results = models.SearchResult.objects.raw(sql, [schema_version, document_pk, object_model, query])
            # Exact search gets perfect score of 1.0 and the query as matched_term for consistency
            return [(r.object_pk, r.highlighted, query, 1.0) for r in results]
        except:
            return []

    def _fuzzy_search(self, query, schema_version, document_pk, object_model):
        """Fuzzy search using RapidFuzz against individual words."""
        index = self._load_index()
        names = index['names']
        
        # Create mapping of words to names they belong to
        word_to_names = {}
        for name in names:
            # Split name into words (handle spaces, hyphens, etc.)
            words = re.findall(r'\b\w+\b', name.lower())
            for word in words:
                if word not in word_to_names:
                    word_to_names[word] = []
                word_to_names[word].append(name)
        
        # Get all unique words
        all_words = list(word_to_names.keys())
        
        # Fuzzy match query against individual words (case-insensitive)
        word_matches = process.extract(query.lower(), all_words, scorer=fuzz.ratio, limit=self.DEFAULT_LIMIT*3)
        good_word_matches = [(word, score) for word, score, _ in word_matches if score >= self.FUZZY_THRESHOLD]
        
        if not good_word_matches:
            return []
        
        # Collect all names that contain good word matches, with their best scores
        name_scores = {}
        for word, score in good_word_matches:
            for name in word_to_names[word]:
                # Keep the highest score for each name
                if name not in name_scores or score > name_scores[name]['score']:
                    name_scores[name] = {'score': score, 'matched_word': word}
        
        # Convert to list and sort
        name_matches = [(name, info['score'], info['matched_word']) for name, info in name_scores.items()]
        
        # Sort matches: exact word matches first, then by similarity score (descending)
        def sort_key(match):
            name, score, matched_word = match
            # Check if query exactly matches the word (case insensitive)
            is_exact_word_match = query.lower() == matched_word.lower()
            # Return tuple: (exact_word_priority, negative_score) for sorting
            return (0 if is_exact_word_match else 1, -score)
        
        name_matches.sort(key=sort_key)
        
        # Limit results
        name_matches = name_matches[:self.DEFAULT_LIMIT]
        
        # Get results for matched names
        match_name_to_info = {match[0]: {'term': match[2], 'score': match[1] / 100.0} for match in name_matches}  # Convert to 0-1 range
        matched_names = [match[0] for match in name_matches]
        
        placeholders = ','.join(['%s'] * len(matched_names))
        sql = f"""
            SELECT 1 as id, 0 as rank, text as highlighted,
                   document_pk, object_pk, object_name, object_model, text, schema_version
            FROM search_index
            WHERE object_name IN ({placeholders})
              AND schema_version LIKE %s
              AND document_pk LIKE %s  
              AND object_model LIKE %s
            ORDER BY object_name
        """
        
        try:
            results = models.SearchResult.objects.raw(
                sql, matched_names + [schema_version, document_pk, object_model]
            )
            # Return with proper ordering based on our sorted matches
            result_list = list(results)
            # Sort results to match our fuzzy match ordering
            name_to_result = {r.object_name: r for r in result_list}
            ordered_results = []
            for name in matched_names:
                if name in name_to_result:
                    result = name_to_result[name]
                    match_info = match_name_to_info[name]
                    ordered_results.append((result.object_pk, result.highlighted, match_info['term'], match_info['score']))
            
            return ordered_results
        except:
            return []

    def _vector_search(self, query, schema_version, document_pk, object_model):
        """Vector search using TF-IDF."""
        index = self._load_index()
        vectorizer = index['vectorizer'] 
        matrix = index['matrix']
        
        # Get similarity scores
        query_vec = vectorizer.transform([query])
        scores = (matrix @ query_vec.T).toarray().ravel()
        best_indices = scores.argsort()[::-1][:self.DEFAULT_LIMIT]
        
        # Filter by threshold and track scores
        good_results = []
        for i in best_indices:
            if scores[i] > self.VECTOR_THRESHOLD:
                good_results.append((i, scores[i]))
        
        if not good_results:
            return []
            
        # Get matched names with their scores
        matched_data = [(index['names'][i], score) for i, score in good_results]
        matched_names = [name for name, score in matched_data]
        
        # Get results for matched names  
        placeholders = ','.join(['%s'] * len(matched_names))
        sql = f"""
            SELECT 1 as id, 0 as rank, text as highlighted,
                   document_pk, object_pk, object_name, object_model, text, schema_version
            FROM search_index
            WHERE object_name IN ({placeholders})
              AND schema_version LIKE %s
              AND document_pk LIKE %s
              AND object_model LIKE %s
            ORDER BY object_name
        """
        
        try:
            results = models.SearchResult.objects.raw(
                sql, matched_names + [schema_version, document_pk, object_model]
            )
            
            # Create mapping from name to score
            name_to_score = dict(matched_data)
            
            # Return with vector similarity scores as match_score, no matched_term for vector
            result_list = []
            for result in results:
                score = name_to_score.get(result.object_name, 0.0)
                result_list.append((result.object_pk, result.highlighted, None, score))
            
            return result_list
        except:
            return []

    def _highlight_text(self, text, query_or_term):
        """Add highlighting to text for fuzzy/vector results."""
        if not text or not query_or_term:
            return text
            
        # Split query/term into words
        words = [w.strip() for w in re.split(r'\s+', query_or_term.lower()) if w.strip()]
        if not words:
            return text
            
        # Create pattern and highlight
        escaped_words = [re.escape(word) for word in words]
        pattern = r'\b(' + '|'.join(escaped_words) + r')\b'
        
        try:
            return re.sub(
                pattern, 
                r'<span class="highlighted">\1</span>', 
                text, 
                flags=re.IGNORECASE
            )
        except:
            return text

    def _merge_results(self, exact_results, fuzzy_results, vector_results, params):
        """Merge search results maintaining priority order."""
        # Extract PKs, highlighted text, matched terms, and scores
        exact_pks = [r[0] for r in exact_results]
        fuzzy_pks = [r[0] for r in fuzzy_results] 
        vector_pks = [r[0] for r in vector_results]
        
        # Store highlighted text, matched terms, and scores from searches
        highlighted_map = {r[0]: r[1] for r in exact_results}
        matched_term_map = {}
        match_score_map = {}
        
        # Store matched terms and scores for all search types - respect priority order
        for pk, highlighted, matched_term, score in exact_results:
            if matched_term is not None:
                matched_term_map[pk] = matched_term
            if score is not None:
                match_score_map[pk] = score
                
        # Only add fuzzy data if not already present (exact has priority)
        for pk, highlighted, matched_term, score in fuzzy_results:
            if matched_term is not None and pk not in matched_term_map:
                matched_term_map[pk] = matched_term
            if score is not None and pk not in match_score_map:
                match_score_map[pk] = score
                
        # Only add vector data if not already present (exact and fuzzy have priority)  
        for pk, highlighted, matched_term, score in vector_results:
            if matched_term is not None and pk not in matched_term_map:
                matched_term_map[pk] = matched_term
            if score is not None and pk not in match_score_map:
                match_score_map[pk] = score
        
        # Merge PKs in priority order, removing duplicates
        all_pks = []
        match_types = []
        seen = set()
        
        for pks, match_type in [(exact_pks, 'exact'), (fuzzy_pks, 'fuzzy'), (vector_pks, 'vector')]:
            for pk in pks:
                if pk not in seen:
                    all_pks.append(pk)
                    match_types.append(match_type)
                    seen.add(pk)
        
        if not all_pks:
            return []
            
        # Build final query with proper ordering
        placeholders = ','.join(['%s'] * len(all_pks))
        order_cases = [f"WHEN object_pk = %s THEN {i}" for i, pk in enumerate(all_pks)]
        match_type_cases = [f"WHEN object_pk = %s THEN '{mt}'" for pk, mt in zip(all_pks, match_types)]
        
        sql = f"""
            SELECT 1 as id,
                   CASE {' '.join(order_cases)} ELSE 999999 END as rank,
                   CASE {' '.join(match_type_cases)} ELSE 'unknown' END as match_type,
                   text as highlighted,
                   document_pk, object_pk, object_name, object_model, text, schema_version
            FROM search_index
            WHERE object_pk IN ({placeholders})
              AND schema_version LIKE %s
              AND document_pk LIKE %s
              AND object_model LIKE %s
            ORDER BY rank
        """
        
        try:
            results = list(models.SearchResult.objects.raw(
                sql, all_pks + all_pks + all_pks + [params['schema_version'], params['document_pk'], params['object_model']]
            ))
            
            # Apply highlighting, matched terms, and scores
            for result in results:
                if result.object_pk in highlighted_map:
                    # Use FTS5 highlighting for exact results
                    result.highlighted = highlighted_map[result.object_pk]
                else:
                    # For fuzzy results, highlight the matched term; for vector results, highlight the query
                    if getattr(result, 'match_type', '') == 'fuzzy' and result.object_pk in matched_term_map:
                        # Highlight the matched term for fuzzy results
                        result.highlighted = self._highlight_text(result.text, matched_term_map[result.object_pk])
                    else:
                        # Highlight the original query for vector results
                        result.highlighted = self._highlight_text(result.text, params['query'])
                
                # Add matched_term and match_score
                result.matched_term = matched_term_map.get(result.object_pk)
                result.match_score = match_score_map.get(result.object_pk)
                    
            return results
        except:
            return []

    def _filter_results(self, results, params):
        """Filter results based on search parameters."""
        exact_count = sum(1 for r in results if getattr(r, 'match_type', '') == 'exact')
        
        if params['strict']:
            # Strict mode: only requested types
            return [r for r in results if (
                (not params['include_vector'] and not params['include_fuzzy'] and getattr(r, 'match_type', '') == 'exact') or
                (params['include_fuzzy'] and getattr(r, 'match_type', '') == 'fuzzy') or
                (params['include_vector'] and getattr(r, 'match_type', '') == 'vector')
            )]
        else:
            # Normal mode: exact + requested + fallback logic
            should_include_fuzzy = params['include_fuzzy'] or (exact_count == 0)
            return [r for r in results if (
                getattr(r, 'match_type', '') == 'exact' or
                (getattr(r, 'match_type', '') == 'fuzzy' and should_include_fuzzy) or
                (getattr(r, 'match_type', '') == 'vector' and params['include_vector'])
            )]

    def _build_metadata(self, all_results, final_results, params):
        """Build search metadata."""
        exact_count = sum(1 for r in all_results if getattr(r, 'match_type', '') == 'exact')
        vector_count = sum(1 for r in all_results if getattr(r, 'match_type', '') == 'vector')
        
        metadata = {
            'exact_matches': exact_count > 0,
            'suggestion': None
        }
        
        # Add vector suggestion if there are vector results not included
        if vector_count > 0 and not params['include_vector']:
            vector_params = dict(self.request.query_params)
            vector_params.update({'query': params['query'], 'vector': 'true'})
            query_string = urlencode(vector_params)
            vector_link = self.request.build_absolute_uri(f"/v2/search/?{query_string}")
            
            metadata['suggestion'] = {
                'type': 'vector',
                'additional_matches': vector_count,
                'link': vector_link
            }
            
        return metadata

    def get_queryset(self):
        """Main search logic."""
        params = self._parse_parameters()
        
        if not params['query']:
            queryset = models.SearchResult.objects.none()
            queryset._search_metadata = {
                'exact_matches': False,
                'suggestion': None
            }
            return queryset
        
        # Run all search types in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            exact_future = executor.submit(self._exact_search, params['query'], params['schema_version'], params['document_pk'], params['object_model'])
            fuzzy_future = executor.submit(self._fuzzy_search, params['query'], params['schema_version'], params['document_pk'], params['object_model'])
            vector_future = executor.submit(self._vector_search, params['query'], params['schema_version'], params['document_pk'], params['object_model'])
            
            # Wait for all to complete and get results
            exact_results = exact_future.result()
            fuzzy_results = fuzzy_future.result()
            vector_results = vector_future.result()
        
        # Merge and process results
        all_results = self._merge_results(exact_results, fuzzy_results, vector_results, params)
        final_results = self._filter_results(all_results, params)
        metadata = self._build_metadata(all_results, final_results, params)
        
        # Return results with metadata
        return ResultsWithMetadata(final_results, metadata)

    def list(self, request, *args, **kwargs):
        """Return search results with metadata."""
        queryset = self.get_queryset()
        metadata = getattr(queryset, '_search_metadata', None)
        
        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            if metadata:
                paginated_response.data['search_metadata'] = metadata
            return paginated_response
        
        # Non-paginated response
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'results': serializer.data, 'count': len(serializer.data)}
        if metadata:
            response_data['search_metadata'] = metadata
        return Response(response_data)
