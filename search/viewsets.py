"""
Search ViewSets for Open5e API v2.
Provides backward-compatible search functionality using Elasticsearch.
"""
import time
import logging
import re
from collections import defaultdict
from typing import Dict, Any, List

from rest_framework import status
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .services import ElasticsearchSearchService

logger = logging.getLogger(__name__)

# Initialize search service
search_service = ElasticsearchSearchService()

# Cache for highlighting patterns to avoid recompiling regexes
_highlight_pattern_cache = {}
_highlight_cache_size = 100


class SearchPagination(PageNumberPagination):
    """Custom pagination for search results."""
    page_size = 50
    page_size_query_param = 'limit'
    max_page_size = 1000


class SearchViewSet(ViewSet):
    """
    Search ViewSet providing backward-compatible search functionality.
    Matches the expected Open5e API format.
    """
    
    pagination_class = SearchPagination

    @extend_schema(
        operation_id="search_content",
        summary="Search all content",
        description="Search across all D&D content with text, fuzzy, and vector search capabilities",
        parameters=[
            OpenApiParameter("query", str, description="Search query", required=True),
            OpenApiParameter("q", str, description="Search query (alias for 'query')", required=False),
            OpenApiParameter("limit", int, description="Results per page (default: 50, max: 1000)", required=False),
            OpenApiParameter("page", int, description="Page number", required=False),
            OpenApiParameter("search_types", str, description="Comma-separated: text,fuzzy,vector", required=False),
            OpenApiParameter("object_type", str, description="Filter by object type", required=False),
            OpenApiParameter("document", str, description="Filter by document", required=False),
        ],
    )
    def list(self, request):
        """Main search endpoint with backward compatibility."""
        start_time = time.time()
        
        # Get query from either 'query' or 'q' parameter for backward compatibility
        query = request.query_params.get('query', '').strip()
        if not query:
            query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response({
                'error': 'Query parameter "query" is required',
                'results': [],
                'count': 0
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse parameters
        limit = min(int(request.query_params.get('limit', 50)), 1000)
        page = int(request.query_params.get('page', 1))
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Parse search types
        search_types_param = request.query_params.get('search_types', 'text,fuzzy,vector')
        search_types = [t.strip() for t in search_types_param.split(',')]
        valid_types = {'text', 'fuzzy', 'vector'}
        search_types = [t for t in search_types if t in valid_types]
        if not search_types:
            search_types = ['text', 'fuzzy', 'vector']
        
        # Parse filters
        filters = {}
        if request.query_params.get('object_type'):
            filters['object_type'] = request.query_params.get('object_type')
        if request.query_params.get('document'):
            filters['document_name'] = request.query_params.get('document')
        
        try:
            # Perform search with pagination
            results = search_service.search(
                query=query,
                limit=limit + offset,  # Get more results to handle pagination
                search_types=search_types,
                boost_factors={'text': 1.0, 'fuzzy': 0.5, 'vector': 0.3},
                filters=filters
            )
            
            # Apply pagination
            paginated_results = results[offset:offset + limit]
            total_count = len(results)
            
            # Convert to expected format
            formatted_results = []
            for result in paginated_results:
                # Determine match type based on search type and score
                if 'text' in result.search_type and result.score > 10:
                    match_type = "exact"
                    matched_term = self._extract_matched_term(query, result.name)
                else:
                    match_type = "fuzzy" if 'fuzzy' in result.search_type else "semantic"
                    matched_term = query.lower()
                
                # Get object details
                object_details = self._get_object_details(result)
                
                formatted_result = {
                    "document": {
                        "key": self._get_document_key(result.document_name),
                        "name": result.document_name
                    },
                    "object_pk": self._get_object_pk(result),
                    "object_name": result.name,
                    "object": object_details,
                    "object_model": result.object_type,
                    "schema_version": result.schema_version,
                    "route": self._get_route(result.object_type),
                    "text": result.description or result.name,
                    "highlighted": self._create_highlighted_text(result, query),
                    "match_type": match_type,
                    "matched_term": matched_term,
                    "match_score": min(round(result.score / 25, 1), 1.0)  # Normalize to 0-1
                }
                formatted_results.append(formatted_result)
            
            # Build pagination URLs
            base_url = request.build_absolute_uri().split('?')[0]
            next_url = None
            prev_url = None
            
            if offset + limit < total_count:
                next_page = page + 1
                next_url = f"{base_url}?query={query}&page={next_page}&limit={limit}"
                if filters.get('object_type'):
                    next_url += f"&object_type={filters['object_type']}"
                if filters.get('document_name'):
                    next_url += f"&document={filters['document_name']}"
            
            if page > 1:
                prev_page = page - 1
                prev_url = f"{base_url}?query={query}&page={prev_page}&limit={limit}"
                if filters.get('object_type'):
                    prev_url += f"&object_type={filters['object_type']}"
                if filters.get('document_name'):
                    prev_url += f"&document={filters['document_name']}"
            
            # Determine if we have exact matches
            exact_matches = any(r['match_type'] == 'exact' for r in formatted_results)
            
            search_time = round((time.time() - start_time) * 1000, 1)
            
            return Response({
                "count": total_count,
                "next": next_url,
                "previous": prev_url,
                "results": formatted_results,
                "search_metadata": {
                    "exact_matches": exact_matches,
                    "search_time_ms": search_time,
                    "search_types": search_types
                }
            })
            
        except Exception as e:
            logger.error(f"Search error for query '{query}': {e}", exc_info=True)
            return Response({
                'error': f'Search failed: {str(e)}',
                'results': [],
                'count': 0
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _extract_matched_term(self, query: str, name: str) -> str:
        """Extract the matched term from the query."""
        query_words = query.lower().split()
        name_words = name.lower().split()
        
        for word in query_words:
            if any(word in name_word for name_word in name_words):
                return word
        return query_words[0] if query_words else query

    def _get_object_details(self, result) -> Dict[str, Any]:
        """Get object-specific details based on type."""
        details = {}
        
        if result.object_type == "Spell":
            # Extract spell details from search data if available
            details = {"school": "Unknown", "level": 0}
            # TODO: Extract from actual object data when available
        elif result.object_type == "Creature":
            details = {"cr": "Unknown", "type": "Unknown", "size": "Unknown"}
        elif result.object_type == "Item":
            details = {"rarity": "Unknown", "type": "Unknown"}
        
        return details

    def _get_object_pk(self, result) -> str:
        """Generate object primary key from result."""
        # Create a consistent object_pk format
        doc_key = self._get_document_key(result.document_name)
        name_key = result.name.lower().replace(' ', '-').replace("'", "")
        return f"{doc_key}_{name_key}"

    def _get_document_key(self, document_name: str) -> str:
        """Convert document name to key format."""
        doc_key_map = {
            "5e 2014 Rules": "srd-2014",
            "System Reference Document 5.1": "srd-2014", 
            "Adventurer's Guide": "a5e-ag",
            "Monstrous Menagerie": "a5e-mm",
            "Tome of Beasts": "tob",
            "Tome of Beasts 2": "tob2",
            "Tome of Beasts 3": "tob3",
            "Deep Magic for 5th Edition": "deepm",
            "Vault of Magic": "vault"
        }
        return doc_key_map.get(document_name, document_name.lower().replace(' ', '-'))

    def _get_route(self, object_type: str) -> str:
        """Get API route for object type."""
        route_map = {
            "Spell": "v2/spells/",
            "Creature": "v2/creatures/",
            "Item": "v2/items/",
            "Background": "v2/backgrounds/",
            "Feat": "v2/feats/",
            "Species": "v2/species/",
            "CharacterClass": "v2/classes/"
        }
        return route_map.get(object_type, "v2/")

    def _create_highlighted_text(self, result, query: str) -> str:
        """Create highlighted text with HTML spans around matched terms."""
        text = result.description or result.name
        
        # Cache key for this query to avoid recomputing
        cache_key = query.lower().strip()
        
        # Get or create regex pattern for highlighting
        if cache_key not in _highlight_pattern_cache:
            # Create optimized regex pattern for highlighting
            query_words = [word.strip() for word in query.lower().split() if word.strip()]
            if not query_words:
                return self._create_excerpt(text, 0, 100)
            
            # Escape special regex characters and create alternation pattern
            escaped_words = [re.escape(word) for word in query_words]
            pattern = r'\b(' + '|'.join(escaped_words) + r')\b'
            
            try:
                compiled_pattern = re.compile(pattern, re.IGNORECASE)
                _highlight_pattern_cache[cache_key] = (compiled_pattern, query_words)
                
                # Maintain cache size limit
                if len(_highlight_pattern_cache) > _highlight_cache_size:
                    # Remove oldest entry
                    oldest_key = next(iter(_highlight_pattern_cache))
                    del _highlight_pattern_cache[oldest_key]
                    
            except re.error:
                # Fallback for malformed regex - use simple word matching
                _highlight_pattern_cache[cache_key] = (None, query_words)
        
        pattern, query_words = _highlight_pattern_cache[cache_key]
        
        # Find best excerpt position based on matches
        text_lower = text.lower()
        best_pos = 0
        
        # Find the first match position for excerpt centering
        for word in query_words:
            pos = text_lower.find(word)
            if pos != -1:
                best_pos = pos
                break
        
        # Create excerpt around the match
        excerpt_start = max(0, best_pos - 60)
        excerpt_end = min(len(text), best_pos + 150)
        excerpt = text[excerpt_start:excerpt_end]
        
        # Apply HTML highlighting efficiently
        if pattern:
            # Use regex replacement for complex patterns
            highlighted_excerpt = pattern.sub(
                r'<span class="highlighted">\1</span>', 
                excerpt
            )
        else:
            # Fallback to simple string replacement for performance
            highlighted_excerpt = excerpt
            for word in query_words:
                if len(word) >= 2:  # Only highlight meaningful words
                    # Case-insensitive replacement with word boundaries
                    word_pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
                    highlighted_excerpt = word_pattern.sub(
                        f'<span class="highlighted">{word}</span>',
                        highlighted_excerpt,
                        count=3  # Limit replacements to avoid overhead
                    )
        
        # Add ellipsis indicators
        if excerpt_start > 0:
            highlighted_excerpt = "..." + highlighted_excerpt
        if excerpt_end < len(text):
            highlighted_excerpt = highlighted_excerpt + "..."
        
        return highlighted_excerpt
    
    def _create_excerpt(self, text: str, center_pos: int, length: int) -> str:
        """Create a text excerpt centered around a position."""
        start = max(0, center_pos - length // 2)
        end = min(len(text), start + length)
        excerpt = text[start:end]
        
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(text):
            excerpt = excerpt + "..."
        
        return excerpt

    @extend_schema(
        operation_id="search_stats",
        summary="Get search statistics",
        description="Get information about the search index",
    )
    @action(detail=False, methods=['GET'])
    def stats(self, request):
        """Get search index statistics."""
        try:
            stats = search_service.get_stats()
            return Response(stats)
        except Exception as e:
            logger.error(f"Error getting search stats: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 