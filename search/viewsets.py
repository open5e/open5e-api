"""Search implementation with exact, fuzzy, and vector search."""
import pickle
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode

from rapidfuzz import process, fuzz
from rest_framework import viewsets
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from search import models, serializers
from search.apps import SearchConfig


class ResultsWithMetadata(list):
    """Custom list that can hold search metadata and behaves like a QuerySet."""
    def __init__(self, items, metadata=None):
        super().__init__(items)
        self._search_metadata = metadata
        # Add model attribute to satisfy DRF expectations
        self.model = models.SearchResult


@extend_schema_view(
    list=extend_schema(
        operation_id="search_list",
        summary="Search across D&D 5E content",
        description="""
        Search across all Open5e content and objects.

        If multiple search types are requested, the results are first sorted, then merged & deduplicated in order of decreasing precision:
        - Exact matches(name first, then other fields)
        - Fuzzy matches (similarity, descending)
        - Vector matches (similarity, descending)

        """,
        parameters=[
            OpenApiParameter(
                name="query",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="The search term to find. Required parameter.",
                examples=[
                    OpenApiExample("Existing term", value="fireball"),
                    OpenApiExample("Typo example", value="firbal"),
                    OpenApiExample("Multi-word", value="magic weapon"),
                ]
            ),
            OpenApiParameter(
                name="strict",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Strict mode: only return explicitly requested search types. When false (default), exact search always runs with fuzzy fallback if no results found.",
                examples=[
                    OpenApiExample("Strict mode", value="true"),
                    OpenApiExample("Default mode", value="false"),
                ]
            ),
            OpenApiParameter(
                name="fuzzy",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Include fuzzy individual word matches in name fields only. Default: false (but used as fallback in default mode).",
                examples=[
                    OpenApiExample("Enable fuzzy matching", value="true"),
                    OpenApiExample("Disable fuzzy matching", value="false"),
                ]
            ),
            OpenApiParameter(
                name="vector",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Include vector search results against name + description. Finds semantically similar content using TF-IDF similarity. Default: false.",
                examples=[
                    OpenApiExample("Enable vector", value="true"),
                    OpenApiExample("Disable vector", value="false"),
                ]
            ),
            OpenApiParameter(
                name="object_model",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter results to specific content type. Default: all types.",
                examples=[
                    OpenApiExample("Spells only", value="Spell"),
                    OpenApiExample("Creatures only", value="Creature"),
                    OpenApiExample("Items only", value="Item"),
                    OpenApiExample("All types", value="%"),
                ]
            ),
            OpenApiParameter(
                name="document_pk",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter results to specific document. Use document key/slug. Default: all documents.",
                examples=[
                    OpenApiExample("SRD only", value="srd-2014"),
                    OpenApiExample("All documents", value="%"),
                ]
            ),
            OpenApiParameter(
                name="schema",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="API schema version to search. Default: 'v2'.",
                examples=[
                    OpenApiExample("API v2", value="v2"),
                    OpenApiExample("API v1", value="v1"),
                ]
            ),
        ],
        responses={
            200: serializers.SearchResultSerializer(many=True),
            400: "Bad request - missing or invalid query parameter"
        },
        examples=[
            OpenApiExample(
                "Default search",
                summary="Basic search with exact + fuzzy fallback",
                description="Searches for 'fireball' using exact text search, with fuzzy fallback if no exact matches",
                value={
                    "query": "fireball"
                }
            ),
            OpenApiExample(
                "Fuzzy search for typo",
                summary="Explicit fuzzy search for handling typos",
                description="Searches for 'firbal' using fuzzy search to handle the typo and find 'fireball'",
                value={
                    "query": "firbal",
                    "fuzzy": "true"
                }
            ),
            OpenApiExample(
                "Vector semantic search",
                summary="Add semantic similarity search",
                description="Finds exact matches for 'healing' and content semantically similar to 'healing' using vector search",
                value={
                    "query": "healing",
                    "vector": "true"
                }
            ),
            OpenApiExample(
                "Strict mode - vector only",
                summary="Strict mode: vector only search",
                description="Returns only vector matches for 'fire' eg. 'heat', 'flame', 'scorching'",
                value={
                    "query": "fire",
                    "strict": "true",
                    "vector": "true"
                }
            ),
            OpenApiExample(
                "Combined search modes",
                summary="Multiple search types combined",
                description="Combines exact, fuzzy, and vector search for comprehensive results",
                value={
                    "query": "magic",
                    "fuzzy": "true",
                    "vector": "true"
                }
            ),
            OpenApiExample(
                "Filtered search",
                summary="Search filtered to specific content type",
                description="Search for dragons but only in creature content",
                value={
                    "query": "dragon",
                    "object_model": "Creature"
                }
            ),
        ]
    )
)
class SearchResultViewSet(viewsets.ReadOnlyModelViewSet):
    """Unified search across exact text, fuzzy, and vector search methods."""

    serializer_class = serializers.SearchResultSerializer
    
    # Configuration constants
    VECTOR_INDEX_PATH = Path('server/vector_index.pkl')
    FUZZY_THRESHOLD = 75
    VECTOR_THRESHOLD = 0.05
    BASE_SELECT_FIELDS = "document_pk, object_pk, object_name, object_model, text, schema_version"
    WHERE_FILTERS = "schema_version LIKE %s AND document_pk LIKE %s AND object_model LIKE %s"

    def _parse_parameters(self):
        """Parse search parameters from request."""
        return {
            'query': self.request.query_params.get('query'),
            'include_vector': self.request.query_params.get("vector", "false").lower() in ["1", "true", "yes"],
            'include_fuzzy': self.request.query_params.get("fuzzy", "false").lower() in ["1", "true", "yes"],
            'strict': self.request.query_params.get("strict", "false").lower() in ["1", "true", "yes"],
            'schema_version': self.request.query_params.get("schema", "v2"),
            'document_pk': self.request.query_params.get("document_pk", '%'),
            'object_model': self.request.query_params.get("object_model", '%')
        }

    def _load_index(self):
        """Get the pre-loaded search index from app configuration."""
        if SearchConfig.vector_index is None:
            # Fallback: load on demand if not pre-loaded
            if not hasattr(SearchResultViewSet, '_fallback_index'):
                with self.VECTOR_INDEX_PATH.open('rb') as f:
                    SearchResultViewSet._fallback_index = pickle.load(f)
            return SearchResultViewSet._fallback_index
        
        return SearchConfig.vector_index

    def _execute_search_query(self, sql, params):
        """Execute a search query with error handling."""
        try:
            return list(models.SearchResult.objects.raw(sql, params))
        except Exception:
            return []

    def _build_name_lookup_query(self, matched_names, schema_version, document_pk, object_model):
        """Build SQL query for looking up results by object names."""
        placeholders = ','.join(['%s'] * len(matched_names))
        sql = f"""
            SELECT 1 as id, 0 as rank, text as highlighted,
                   {self.BASE_SELECT_FIELDS}
            FROM search_index
            WHERE object_name IN ({placeholders})
              AND {self.WHERE_FILTERS}
            ORDER BY object_name
        """
        params = matched_names + [schema_version, document_pk, object_model]
        return sql, params

    def _exact_search(self, query, schema_version, document_pk, object_model):
        """Exact text search using SQLite FTS5."""
        sql = f"""
            SELECT 1 as id,
                   rank,
                   snippet(search_index, 4, '<span class="highlighted">', '</span>', '...', 20) as highlighted,
                   {self.BASE_SELECT_FIELDS}
            FROM search_index 
            WHERE {self.WHERE_FILTERS}
              AND search_index MATCH %s
              AND rank MATCH 'bm25(1.0, 1.0, 10.0)'
            ORDER BY rank
        """
        
        results = self._execute_search_query(sql, [schema_version, document_pk, object_model, query])
        # Exact search gets perfect score of 1.0 and the query as matched_term for consistency
        return [(r.object_pk, r.highlighted, query, 1.0) for r in results]

    def _build_word_index(self, names):
        """Build mapping of words to names for fuzzy search."""
        word_to_names = {}
        for name in names:
            # Split name into words (handle spaces, hyphens, etc.)
            words = re.findall(r'\b\w+\b', name.lower())
            for word in words:
                if word not in word_to_names:
                    word_to_names[word] = []
                word_to_names[word].append(name)
        return word_to_names

    def _find_fuzzy_matches(self, query, word_to_names):
        """Find fuzzy matches and return sorted name matches."""
        all_words = list(word_to_names.keys())
        
        # Fuzzy match query against individual words (case-insensitive)
        word_matches = process.extract(query.lower(), all_words, scorer=fuzz.ratio)
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
        return name_matches

    def _process_name_matches(self, name_matches, schema_version, document_pk, object_model):
        """Process name matches into ordered results."""
        if not name_matches:
            return []
            
        # Get results for matched names
        match_name_to_info = {match[0]: {'term': match[2], 'score': match[1] / 100.0} for match in name_matches}  # Convert to 0-1 range
        matched_names = [match[0] for match in name_matches]
        
        sql, params = self._build_name_lookup_query(matched_names, schema_version, document_pk, object_model)
        results = self._execute_search_query(sql, params)
        
        # Return with proper ordering based on our sorted matches
        name_to_result = {r.object_name: r for r in results}
        ordered_results = []
        for name in matched_names:
            if name in name_to_result:
                result = name_to_result[name]
                match_info = match_name_to_info[name]
                ordered_results.append((result.object_pk, result.highlighted, match_info['term'], match_info['score']))
        
        return ordered_results

    def _fuzzy_search(self, query, schema_version, document_pk, object_model):
        """Fuzzy search using RapidFuzz against individual words."""
        index = self._load_index()
        names = index['names']
        
        word_to_names = self._build_word_index(names)
        name_matches = self._find_fuzzy_matches(query, word_to_names)
        return self._process_name_matches(name_matches, schema_version, document_pk, object_model)

    def _vector_search(self, query, schema_version, document_pk, object_model):
        """Vector search using TF-IDF."""
        index = self._load_index()
        vectorizer = index['vectorizer'] 
        matrix = index['matrix']
        
        # Get similarity scores
        query_vec = vectorizer.transform([query])
        scores = (matrix @ query_vec.T).toarray().ravel()
        best_indices = scores.argsort()[::-1]
        
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
        
        sql, params = self._build_name_lookup_query(matched_names, schema_version, document_pk, object_model)
        results = self._execute_search_query(sql, params)
        
        # Create mapping from name to score
        name_to_score = dict(matched_data)
        
        # Return with vector similarity scores as match_score, no matched_term for vector
        result_list = []
        for result in results:
            score = name_to_score.get(result.object_name, 0.0)
            result_list.append((result.object_pk, result.highlighted, None, score))
        
        return result_list

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
        except Exception:
            return text

    def _merge_results(self, exact_results, fuzzy_results, vector_results, params):
        """Fast merge of pre-sorted result lists with deduplication."""
        # Fast merge with priority: exact > fuzzy > vector
        # Each list is already sorted correctly, just combine and dedupe
        seen_pks = set()
        merged_data = []
        match_types = []
        
        # Process in priority order: exact, fuzzy, vector
        for results, match_type in [(exact_results, 'exact'), (fuzzy_results, 'fuzzy'), (vector_results, 'vector')]:
            for result_tuple in results:
                pk = result_tuple[0]
                if pk not in seen_pks:
                    seen_pks.add(pk)
                    merged_data.append(result_tuple)
                    match_types.append(match_type)
        
        if not merged_data:
            return []
        
        # Build simple lookup query - no complex CASE statements needed
        pks = [r[0] for r in merged_data]
        placeholders = ','.join(['%s'] * len(pks))
        
        sql = f"""
            SELECT 1 as id, object_pk, object_name, object_model, text, document_pk, schema_version
            FROM search_index
            WHERE object_pk IN ({placeholders})
              AND {self.WHERE_FILTERS}
        """
        
        params_list = pks + [params['schema_version'], params['document_pk'], params['object_model']]
        raw_results = self._execute_search_query(sql, params_list)
        
        # Create lookup map for fast access
        pk_to_raw = {r.object_pk: r for r in raw_results}
        
        # Build final results in correct order with all metadata
        final_results = []
        for i, (result_tuple, match_type) in enumerate(zip(merged_data, match_types)):
            pk, highlighted, matched_term, score = result_tuple
            
            if pk in pk_to_raw:
                raw_result = pk_to_raw[pk]
                
                # Set the core attributes
                raw_result.id = 1
                raw_result.rank = i  # Preserve merge order
                raw_result.match_type = match_type
                raw_result.matched_term = matched_term
                raw_result.match_score = score
                
                # Set highlighting
                if match_type == 'exact':
                    # Use the FTS5 highlighting for exact matches
                    raw_result.highlighted = highlighted
                elif match_type == 'fuzzy' and matched_term:
                    # Highlight the matched term for fuzzy results
                    raw_result.highlighted = self._highlight_text(raw_result.text, matched_term)
                else:
                    # Highlight the original query for vector results
                    raw_result.highlighted = self._highlight_text(raw_result.text, params['query'])
                
                final_results.append(raw_result)
        
        return final_results

    def _filter_results(self, results, params):
        """Filter results based on search parameters."""
        if params['strict']:
            # Strict mode: only requested types
            return [r for r in results if (
                (not params['include_vector'] and not params['include_fuzzy'] and getattr(r, 'match_type', '') == 'exact') or
                (params['include_fuzzy'] and getattr(r, 'match_type', '') == 'fuzzy') or
                (params['include_vector'] and getattr(r, 'match_type', '') == 'vector')
            )]
        else:
            # Normal mode: include exact and fuzzy (already filtered), but vector only if requested
            return [r for r in results if (
                getattr(r, 'match_type', '') == 'exact' or
                getattr(r, 'match_type', '') == 'fuzzy' or
                (getattr(r, 'match_type', '') == 'vector' and params['include_vector'])
            )]

    def _build_metadata(self, all_results, final_results, params):
        """Build simple search metadata."""
        exact_count = sum(1 for r in all_results if getattr(r, 'match_type', '') == 'exact')
        
        metadata = {
            'exact_matches': exact_count > 0
        }
            
        return metadata

    def get_queryset(self):
        """Main search logic - simplified."""
        params = self._parse_parameters()
        
        if not params['query']:
            queryset = models.SearchResult.objects.none()
            queryset._search_metadata = {
                'exact_matches': False
            }
            return queryset
        
        search_args = (params['query'], params['schema_version'], params['document_pk'], params['object_model'])
        
        # Determine which searches to run
        searches_to_run = ['exact']  # Always start with exact
        
        # Add explicitly requested searches
        if params['include_fuzzy']:
            searches_to_run.append('fuzzy')
        if params['include_vector']:
            searches_to_run.append('vector')
        
        # Run initial searches in parallel
        search_functions = {
            'exact': self._exact_search,
            'fuzzy': self._fuzzy_search,
            'vector': self._vector_search
        }
        
        results = {}
        with ThreadPoolExecutor(max_workers=len(searches_to_run)) as executor:
            futures = {
                search_type: executor.submit(search_functions[search_type], *search_args)
                for search_type in searches_to_run
            }
            
            for search_type, future in futures.items():
                results[search_type] = future.result()
        
        # Fallback logic: if exact found nothing and we're not in strict mode and fuzzy wasn't explicitly requested
        exact_results = results.get('exact', [])
        if len(exact_results) == 0 and not params['strict'] and not params['include_fuzzy']:
            results['fuzzy'] = self._fuzzy_search(*search_args)
        
        # Extract results with empty list defaults
        fuzzy_results = results.get('fuzzy', [])
        vector_results = results.get('vector', [])

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
