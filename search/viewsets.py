"""
Search ViewSets for Open5e API v2.
Provides text, fuzzy, and semantic vector search.
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

from .services import search_service

logger = logging.getLogger(__name__)

# Initialize search service
# search_service is imported from services module

# Cache for highlighting patterns to avoid recompiling regexes
_highlight_pattern_cache = {}
_highlight_cache_size = 100


class SearchPagination(PageNumberPagination):
    """Custom pagination for search results."""
    page_size = 50
    page_size_query_param = 'limit'
    max_page_size = 1000


def _create_highlighted_text(text: str, query: str) -> str:
    """Create highlighted text by wrapping query terms in HTML tags."""
    global _highlight_pattern_cache
    
    if not text or not query:
        return text
    
    # Use cached pattern if available
    cache_key = query.lower().strip()
    if cache_key in _highlight_pattern_cache:
        pattern = _highlight_pattern_cache[cache_key]
    else:
        # Create new pattern with word boundaries for precise matching
        try:
            # Split query into individual words and escape special regex characters
            words = [re.escape(word.strip()) for word in query.split() if word.strip()]
            if not words:
                return text
            
            # Create pattern that matches any of the words with word boundaries
            pattern_str = r'\b(?:' + '|'.join(words) + r')\b'
            pattern = re.compile(pattern_str, re.IGNORECASE)
            
            # Cache the pattern
            _highlight_pattern_cache[cache_key] = pattern
            
            # Maintain cache size
            if len(_highlight_pattern_cache) > _highlight_cache_size:
                # Remove oldest entry
                oldest_key = next(iter(_highlight_pattern_cache))
                del _highlight_pattern_cache[oldest_key]
                
        except re.error:
            # If regex compilation fails, fall back to simple string replacement
            logger.warning(f"Regex compilation failed for query: {query}")
            words = [word.strip() for word in query.split() if word.strip()]
            highlighted = text
            for word in words:
                highlighted = highlighted.replace(word, f'<span class="highlighted">{word}</span>')
                highlighted = highlighted.replace(word.lower(), f'<span class="highlighted">{word.lower()}</span>')
                highlighted = highlighted.replace(word.upper(), f'<span class="highlighted">{word.upper()}</span>')
                highlighted = highlighted.replace(word.capitalize(), f'<span class="highlighted">{word.capitalize()}</span>')
            return highlighted
    
    # Apply highlighting with limited replacements to prevent excessive processing
    try:
        highlighted = pattern.sub(
            lambda m: f'<span class="highlighted">{m.group()}</span>', 
            text, 
            count=3  # Limit to 3 replacements per word to prevent excessive processing
        )
        return highlighted
    except Exception as e:
        logger.warning(f"Error applying highlighting: {e}")
        return text


class SearchViewSet(ViewSet):
    """
    ViewSet for performing searches across Open5e content.
    Supports text, fuzzy, and vector search.
    """
    
    pagination_class = SearchPagination
    
    @property
    def paginator(self):
        """Return the paginator instance associated with the view."""
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='query',
                description='Search query string',
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='limit',
                description='Number of results to return (max 1000)',
                required=False,
                type=int,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='search_types',
                description='Comma-separated list of search types to use (text,fuzzy,vector)',
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='highlight',
                description='Whether to highlight search terms in results',
                required=False,
                type=bool,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={200: 'Search results'},
        description='Search across Open5e content using text, fuzzy, and vector search.'
    )
    def list(self, request):
        """Perform a search and return results."""
        start_time = time.time()
        
        # Get search parameters
        query = request.query_params.get('query', '').strip()
        if not query:
            return Response(
                {'error': 'Query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse search parameters  
        search_types_param = request.query_params.get('search_types', '')
        highlight = request.query_params.get('highlight', 'true').lower() == 'true'
        
        # Parse search types
        if search_types_param:
            search_types = [t.strip() for t in search_types_param.split(',') if t.strip()]
        else:
            search_types = None  # Use service defaults
        
        try:
            # Get all results
            search_response = search_service.search(
                query=query,
                limit=2000,
                search_types=search_types
            )
            
            all_results = search_response['results']
            
            # Format all results first
            formatted_results = []
            for result in all_results:
                formatted_result = {
                    'name': result.name,
                    'description': result.description,
                    'object_type': result.object_type,
                    'document_name': result.document_name,
                    'schema_version': result.schema_version,
                    'score': round(result.score, 2),
                    'search_type': result.search_type,
                }
                
                # Add highlighting if requested
                if highlight:
                    highlighted_text = None
                    
                    # Use search highlighting if available
                    if result.highlighted_content:
                        highlighted_snippets = result.highlighted_content
                        
                        # The first snippet usually contains the name and beginning of description
                        if highlighted_snippets:
                            first_snippet = highlighted_snippets[0]
                            lines = first_snippet.split('\n')
                            if lines:
                                # First line should contain the highlighted name
                                highlighted_name = lines[0].strip()
                                # Check if the name actually contains highlighting
                                if '<em>' in highlighted_name:
                                    highlighted_text = highlighted_name.replace('<em>', '<span class="highlighted">').replace('</em>', '</span>')
                                else:
                                    # If name doesn't have highlights, use the description content
                                    if len(lines) > 1:
                                        highlighted_description = '\n'.join(lines[1:]).strip()
                                        # Add other snippets to description
                                        for snippet in highlighted_snippets[1:]:
                                            highlighted_description += '\n' + snippet
                                        highlighted_text = highlighted_description.replace('<em>', '<span class="highlighted">').replace('</em>', '</span>')
                                    else:
                                        # Fallback to just the highlighted name even without <em> tags
                                        highlighted_text = highlighted_name
                    else:
                        # Check if this is a fuzzy search with matched substring
                        if result.search_type == 'fuzzy' and hasattr(result, 'fuzzy_matched_substring') and result.fuzzy_matched_substring:
                            # Highlight the matched substring in the name
                            highlighted_text = result.name.replace(
                                result.fuzzy_matched_substring, 
                                f'<span class="highlighted">{result.fuzzy_matched_substring}</span>'
                            )
                        else:
                            # Fall back to manual highlighting - check which field has matches
                            highlighted_name = _create_highlighted_text(result.name, query)
                            highlighted_description = _create_highlighted_text(result.description, query)
                            
                            # Choose the field that actually contains highlighting
                            if '<span class="highlighted">' in highlighted_name:
                                highlighted_text = highlighted_name
                            elif '<span class="highlighted">' in highlighted_description:
                                highlighted_text = highlighted_description
                            else:
                                # If neither has highlights, default to name
                                highlighted_text = result.name
                    
                    if highlighted_text:
                        formatted_result['highlighted'] = highlighted_text
                
                # Add indexed fields if available
                if result.indexed_fields:
                    formatted_result['indexed_fields'] = result.indexed_fields
                
                formatted_results.append(formatted_result)
            
            # Apply DRF pagination
            paginator = self.paginator
            if paginator is not None:
                page = paginator.paginate_queryset(formatted_results, request)
                if page is not None:
                    # Calculate response time
                    response_time = round((time.time() - start_time) * 1000, 1)
                    
                    # Add metadata to paginated response
                    response = paginator.get_paginated_response(page)
                    response.data['meta'] = {
                        'query': query,
                        'response_time_ms': response_time,
                        'search_types_used': search_types or ['text', 'fuzzy', 'vector'],
                        'highlighting_enabled': highlight,
                    }
                    return response
            
            # Fallback if no pagination
            response_time = round((time.time() - start_time) * 1000, 1)
            response_data = {
                'count': len(formatted_results),
                'results': formatted_results,
                'meta': {
                    'query': query,
                    'response_time_ms': response_time,
                    'search_types_used': search_types or ['text', 'fuzzy', 'vector'],
                    'highlighting_enabled': highlight,
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Search error for query '{query}': {e}")
            return Response(
                {
                    'error': 'Search failed',
                    'details': str(e),
                    'query': query
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get search service statistics and status."""
        try:
            stats = search_service.get_stats()
            
            # Add additional runtime information
            stats.update({
                'cache_stats': {
                    'query_embeddings_cached': len(search_service._query_embedding_cache) if hasattr(search_service, '_query_embedding_cache') else 0,
                    'fuzzy_results_cached': len(search_service._fuzzy_search_cache) if hasattr(search_service, '_fuzzy_search_cache') else 0,
                    'highlight_patterns_cached': len(_highlight_pattern_cache),
                }
            })
            
            return Response(stats, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting search stats: {e}")
            return Response(
                {
                    'error': 'Failed to get search statistics',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """Check search service health."""
        try:
            # Test basic search functionality
            test_response = search_service.search(
                query="test",
                limit=1,
                search_types=['text']  # Just test basic functionality
            )
            
            health_status = {
                'status': 'healthy',
                'available_search_types': ['text', 'fuzzy', 'vector'],
                'basic_search_working': len(test_response['results']) >= 0,  # Even 0 results is OK
                'timestamp': time.time()
            }
            
            return Response(health_status, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return Response(
                {
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': time.time()
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            ) 