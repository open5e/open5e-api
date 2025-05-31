"""Search query and parameter parsing."""
from rest_framework import viewsets
from rest_framework.response import Response
from rapidfuzz import process, fuzz
from pathlib import Path
import pickle
import logging
from urllib.parse import urlencode
import re

from search import models
from search import serializers

logger = logging.getLogger(__name__)


# Search configuration constants
class SearchConfig:
    VECTOR_INDEX_PATH = Path('server/vector_index.pkl')
    FUZZY_THRESHOLD = 60
    VECTOR_THRESHOLD = 0.05
    DEFAULT_LIMIT = 50
    BM25_WEIGHTS = "bm25(1.0, 1.0, 10.0)"  # 10x weight to NAME column
    SNIPPET_CONFIG = "snippet(search_index,4,'<span class=\"highlighted\">','</span>','...',20)"
    
    # Schema version handling
    VALID_SCHEMA_VERSIONS = ['v1', 'v2']
    DEFAULT_SCHEMA_VERSION = 'v2'


class SearchResultViewSet(viewsets.ReadOnlyModelViewSet):
    """Search viewset that provides unified search across direct text, fuzzy, and vector search methods."""

    serializer_class = serializers.SearchResultSerializer
    ordering_fields = []

    def _load_search_index(self):
        """Load and cache the search index for fuzzy and vector operations."""
        if not hasattr(self, '_search_index'):
            if not SearchConfig.VECTOR_INDEX_PATH.exists():
                return None
            try:
                with SearchConfig.VECTOR_INDEX_PATH.open('rb') as fh:
                    self._search_index = pickle.load(fh)
            except Exception as e:
                logger.error(f"Error loading search index: {e}")
                return None
        return self._search_index

    def _parse_search_parameters(self):
        """Extract and normalize search parameters from request."""
        # Determine schema version based on API endpoint version
        # Extract version from URL path: /v1/search/ -> v1, /v2/search/ -> v2
        path = self.request.path
        if '/v1/' in path:
            default_schema = 'v1'
        elif '/v2/' in path:
            default_schema = 'v2'
        else:
            # Fallback: try request.version or use configured default
            api_version = getattr(self.request, 'version', SearchConfig.DEFAULT_SCHEMA_VERSION)
            default_schema = api_version if api_version in SearchConfig.VALID_SCHEMA_VERSIONS else SearchConfig.DEFAULT_SCHEMA_VERSION
        
        return {
            'query': self.request.query_params.get('query'),
            'include_vector': self.request.query_params.get("vector", "false").lower() in ["1", "true", "yes"],
            'include_fuzzy': self.request.query_params.get("fuzzy", "false").lower() in ["1", "true", "yes"],
            'strict': self.request.query_params.get("strict", "false").lower() in ["1", "true", "yes"],
            'schema_version': self.request.query_params.get("schema", default_schema),
            'document_pk': self.request.query_params.get("document_pk", '%'),
            'object_model': self.request.query_params.get("object_model", '%')
        }

    def _build_search_sql(self, placeholders, filters, order_by="rank", include_rank=True, include_match_type=False, 
                         pk_list=None, match_types=None):
        """Build SQL query for search results with optional ranking and search type."""
        columns = [
            "1 as id",  # ID column is required
            SearchConfig.SNIPPET_CONFIG + " as highlighted",
            "document_pk", "object_pk", "object_name", "object_model", "text", "schema_version"
        ]
        
        if include_rank:
            if include_match_type and pk_list and match_types:
                # Build CASE statements for ranking and search type
                order_cases = [f"WHEN object_pk = %s THEN {i}" for i, (pk, _) in enumerate(zip(pk_list, match_types))]
                match_type_cases = [f"WHEN object_pk = %s THEN '{match_type}'" for pk, match_type in zip(pk_list, match_types)]
                
                columns.insert(1, f"CASE {' '.join(order_cases)} ELSE 999999 END as rank")
                columns.insert(2, f"CASE {' '.join(match_type_cases)} ELSE 'unknown' END as match_type")
            else:
                columns.insert(1, "rank" if order_by == "rank" else "0 as rank")
        
        return f"SELECT {','.join(columns)} FROM search_index WHERE {' AND '.join(filters)} ORDER BY {order_by}"

    def _extract_pks_safely(self, results):
        """Safely extract object_pk values from search results."""
        try:
            return [r.object_pk for r in list(results)]
        except Exception:
            return []

    def _build_name_based_query(self, names, schema_version, document_pk, object_model):
        """Build SQL query for fuzzy and vector searches that match by object names."""
        if not names:
            return models.SearchResult.objects.none()
            
        placeholders = ','.join(['%s' for _ in names])
        filters = [
            f"object_name IN ({placeholders})",
            "schema_version LIKE %s",
            "document_pk LIKE %s",
            "object_model LIKE %s"
        ]
        
        sql = self._build_search_sql(placeholders, filters, order_by="object_name", include_rank=False)
        params = names + [schema_version, document_pk, object_model]
        return models.SearchResult.objects.raw(sql, params)

    def _attach_metadata_safely(self, results, metadata):
        """Safely attach metadata to results, handling both QuerySet and list cases."""
        try:
            results._search_metadata = metadata
            return results
        except AttributeError:
            # Handle case where this might be a list in tests
            class ResultsWithMetadata(list):
                def __init__(self, items):
                    super().__init__(items)
                    self._search_metadata = metadata
            
            if hasattr(results, '__iter__') and not hasattr(results, '_search_metadata'):
                return ResultsWithMetadata(list(results))
            return results

    def _highlight_text_manually(self, text, query):
        """Manually highlight query terms in text for fuzzy and vector search results."""
        if not text or not query:
            return text
        
        # Split query into words and create a pattern that matches any of them
        query_words = [word.strip() for word in re.split(r'\s+', query.lower()) if word.strip()]
        if not query_words:
            return text
        
        # Create regex pattern for case-insensitive matching
        # Escape special regex characters and join with OR
        escaped_words = [re.escape(word) for word in query_words]
        pattern = r'\b(' + '|'.join(escaped_words) + r')\b'
        
        # Replace matches with highlighted versions
        def highlight_match(match):
            return f'<span class="highlighted">{match.group(0)}</span>'
        
        try:
            highlighted = re.sub(pattern, highlight_match, text, flags=re.IGNORECASE)
            return highlighted
        except Exception:
            # If regex fails for any reason, return original text
            return text

    def _highlight_vector_features(self, text, feature_words):
        """Highlight specific TF-IDF features that contributed to vector similarity."""
        if not text or not feature_words:
            return text
        
        # Create regex pattern for the specific feature words
        escaped_words = [re.escape(word) for word in feature_words if word.strip()]
        if not escaped_words:
            return text
            
        pattern = r'\b(' + '|'.join(escaped_words) + r')\b'
        
        # Replace matches with highlighted versions
        def highlight_match(match):
            return f'<span class="highlighted">{match.group(0)}</span>'
        
        try:
            highlighted = re.sub(pattern, highlight_match, text, flags=re.IGNORECASE)
            return highlighted
        except Exception:
            # If regex fails for any reason, return original text
            return text

    def get_direct_search_results(self, query, schema_version, document_pk, object_model):
        """Get direct text search results."""
        try:
            filters = [
                "schema_version LIKE %s",
                "document_pk LIKE %s", 
                "object_model LIKE %s",
                "search_index MATCH %s",
                f"rank MATCH '{SearchConfig.BM25_WEIGHTS}'"
            ]
            
            sql = self._build_search_sql("", filters, order_by="rank")
            return models.SearchResult.objects.raw(sql, [schema_version, document_pk, object_model, query])
        except Exception as e:
            logger.error(f"Error in direct search: {e}")
            return models.SearchResult.objects.none()

    def get_fuzzy_search_results(self, query, schema_version, document_pk, object_model, limit=SearchConfig.DEFAULT_LIMIT):
        """Get fuzzy search results."""
        try:
            index = self._load_search_index()
            if not index:
                return models.SearchResult.objects.none(), []
            
            names = index['names']
            matches = process.extract(query, names, scorer=fuzz.partial_ratio, limit=limit*2)
            matched_items = [m for m in matches if m[1] > SearchConfig.FUZZY_THRESHOLD]
            
            if not matched_items:
                return models.SearchResult.objects.none(), []
            
            fuzzy_names = [match[0] for match in matched_items[:limit]]
            return self._build_name_based_query(fuzzy_names, schema_version, document_pk, object_model), fuzzy_names
            
        except Exception as e:
            logger.error(f"Error in fuzzy search: {e}")
            return models.SearchResult.objects.none(), []

    def get_vector_search_results(self, query, schema_version, document_pk, object_model, limit=SearchConfig.DEFAULT_LIMIT):
        """Get vector search results."""
        try:
            index = self._load_search_index()
            if not index:
                return models.SearchResult.objects.none(), 0, {}
            
            vectorizer = index['vectorizer']
            matrix = index['matrix']
            q_vec = vectorizer.transform([query])
            scores = (matrix @ q_vec.T).toarray().ravel()
            best = scores.argsort()[::-1][:SearchConfig.DEFAULT_LIMIT]
            
            matched_indices = [i for i in best if scores[i] > SearchConfig.VECTOR_THRESHOLD]
            
            if not matched_indices:
                return models.SearchResult.objects.none(), 0, {}
            
            # Extract matching features for each result
            feature_names = vectorizer.get_feature_names_out()
            q_vec_array = q_vec.toarray()[0]  # Convert to 1D array
            matching_features = {}
            
            for i in matched_indices[:limit]:
                doc_vec = matrix[i].toarray()[0]  # Get document vector as 1D array
                
                # Find features that contributed to the similarity
                # Both query and document must have non-zero values for the feature to contribute
                contributing_features = []
                for feature_idx, feature_name in enumerate(feature_names):
                    if q_vec_array[feature_idx] > 0 and doc_vec[feature_idx] > 0:
                        # Calculate contribution: product of query and document weights
                        contribution = q_vec_array[feature_idx] * doc_vec[feature_idx]
                        contributing_features.append((feature_name, contribution))
                
                # Sort by contribution and take top features
                contributing_features.sort(key=lambda x: x[1], reverse=True)
                top_features = [f[0] for f in contributing_features[:10]]  # Top 10 contributing words
                
                object_name = index['names'][i]
                matching_features[object_name] = top_features
            
            vector_names = [index['names'][i] for i in matched_indices[:limit]]
            return self._build_name_based_query(vector_names, schema_version, document_pk, object_model), len(matched_indices), matching_features
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return models.SearchResult.objects.none(), 0, {}

    def merge_search_results(self, direct_pks, fuzzy_pks, vector_pks, schema_version, document_pk, object_model):
        """Merge search results from different sources with proper priority ordering."""
        # Combine all PKs, removing duplicates while preserving order (direct > fuzzy > vector)
        all_pks = []
        seen = set()
        match_types = []
        
        # Add results by priority: direct > fuzzy > vector
        for pks, match_type in [(direct_pks, 'direct'), (fuzzy_pks, 'fuzzy'), (vector_pks, 'vector')]:
            for pk in pks:
                if pk not in seen:
                    all_pks.append(pk)
                    match_types.append(match_type)
                    seen.add(pk)
        
        if not all_pks:
            return models.SearchResult.objects.none()
        
        placeholders = ','.join(['%s' for _ in all_pks])
        filters = [
            f"object_pk IN ({placeholders})",
            "schema_version LIKE %s",
            "document_pk LIKE %s",
            "object_model LIKE %s"
        ]
        
        sql = self._build_search_sql(
            placeholders, filters, order_by="rank", include_rank=True, 
            include_match_type=True, pk_list=all_pks, match_types=match_types
        )
        
        params = all_pks + all_pks + all_pks + [schema_version, document_pk, object_model]
        return models.SearchResult.objects.raw(sql, params)

    def build_vector_search_link(self, query, current_params):
        """Build a URL for vector search with current parameters."""
        params = dict(current_params)
        params.update({'query': query, 'vector': 'true'})
        query_string = urlencode(params)
        path = f"/v2/search/?{query_string}"
        return self.request.build_absolute_uri(path)

    def perform_unified_search(self, query, schema_version, document_pk, object_model, include_fuzzy=False, include_vector=False, strict=False):
        """
        Clean unified search approach:
        1. Run all search methods
        2. Merge in priority order 
        3. Calculate metadata on complete results
        4. Filter final results based on parameters
        """
        # 1. Run all searches
        direct_results = self.get_direct_search_results(query, schema_version, document_pk, object_model)
        fuzzy_results, _ = self.get_fuzzy_search_results(query, schema_version, document_pk, object_model)
        vector_results, total_vector_matches, matching_features = self.get_vector_search_results(query, schema_version, document_pk, object_model)
        
        # Store highlighted text from direct search results
        highlighted_text = {}
        try:
            for result in direct_results:
                highlighted_text[result.object_pk] = result.highlighted
        except Exception:
            pass
        
        direct_pks = self._extract_pks_safely(direct_results)
        fuzzy_pks = self._extract_pks_safely(fuzzy_results)
        vector_pks = self._extract_pks_safely(vector_results)
        
        # 2. Merge all in priority order
        all_results = self.merge_search_results(direct_pks, fuzzy_pks, vector_pks, schema_version, document_pk, object_model)
        all_results_list = list(all_results)
        
        # Restore highlighted text for direct search results
        for result in all_results_list:
            if result.object_pk in highlighted_text:
                result.highlighted = highlighted_text[result.object_pk]
            else:
                # Apply smart highlighting for fuzzy and vector results
                match_type = getattr(result, 'match_type', '')
                if match_type == 'vector' and result.object_name in matching_features:
                    # Use TF-IDF features for vector results
                    features = matching_features[result.object_name]
                    logger.info(f"Vector features for '{result.object_name}': {features}")
                    result.highlighted = self._highlight_vector_features(result.text, features)
                else:
                    # Use query words for fuzzy results
                    result.highlighted = self._highlight_text_manually(result.text, query)
        
        # 3. Calculate metadata on complete dataset
        vector_count = sum(1 for r in all_results_list if getattr(r, 'match_type', '') == 'vector')
        used_fallback = len(direct_pks) == 0 and len(fuzzy_pks) > 0
        
        # 4. Filter results based on parameters
        if strict:
            # Strict mode: only include explicitly requested types
            final_results = [
                r for r in all_results_list 
                if ((not include_vector and not include_fuzzy and getattr(r, 'match_type', '') == 'direct') or
                    (include_fuzzy and getattr(r, 'match_type', '') == 'fuzzy') or
                    (include_vector and getattr(r, 'match_type', '') == 'vector'))
            ]
        else:
            # Normal mode: include direct + requested types, with fallback logic
            should_include_fuzzy = include_fuzzy or (len(direct_pks) == 0)
            final_results = [
                r for r in all_results_list 
                if (getattr(r, 'match_type', '') == 'direct' or
                    (getattr(r, 'match_type', '') == 'fuzzy' and should_include_fuzzy) or
                    (getattr(r, 'match_type', '') == 'vector' and include_vector))
            ]
        
        metadata = {
            'direct_matches': len(direct_pks) > 0,
            'used_fallback': used_fallback,
            'suggestion': None
        }
        
        # Add vector search suggestion if there are additional vector results
        if vector_count > 0 and not include_vector:
            metadata['suggestion'] = {
                'type': 'vector',
                'additional_matches': vector_count,
                'link': None  # Will be set in get_queryset
            }
        
        return {'results': final_results, 'metadata': metadata}

    def get_queryset(self):
        """Builds and runs the DB query based on querystring params"""
        params = self._parse_search_parameters()
        
        if params['query'] is None:
            queryset = models.SearchResult.objects.none()
            empty_metadata = {
                'direct_matches': False,
                'used_fallback': False,
                'suggestion': None
            }
            return self._attach_metadata_safely(queryset, empty_metadata)

        # Use unified search method
        search_result = self.perform_unified_search(
            params['query'], params['schema_version'], params['document_pk'], params['object_model'],
            include_fuzzy=params['include_fuzzy'], include_vector=params['include_vector'], strict=params['strict']
        )
        
        final_results = search_result['results']
        search_metadata = search_result['metadata']

        # Add vector search link if there are additional unique vector results
        if search_metadata.get('suggestion') and search_metadata['suggestion']['type'] == 'vector':
            vector_link = self.build_vector_search_link(params['query'], self.request.query_params)
            search_metadata['suggestion']['link'] = vector_link

        return self._attach_metadata_safely(final_results, search_metadata)

    def list(self, request, *args, **kwargs):
        """Override list to include search metadata in the response."""
        queryset = self.get_queryset()
        search_metadata = getattr(queryset, '_search_metadata', None)
        
        # Get the paginated response
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            if search_metadata:
                paginated_response.data['search_metadata'] = search_metadata
            return paginated_response

        # Non-paginated response
        serializer = self.get_serializer(queryset, many=True)
        response_data = {'results': serializer.data, 'count': len(serializer.data)}
        if search_metadata:
            response_data['search_metadata'] = search_metadata
        return Response(response_data)
