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
            # First, get a larger set of results to determine total count
            # We need to get enough results to handle pagination properly
            max_results_for_pagination = 2000  # Reasonable limit for pagination
            
            all_results = search_service.search(
                query=query,
                limit=max_results_for_pagination,
                search_types=search_types,
                boost_factors={'text': 1.0, 'fuzzy': 0.5, 'vector': 0.3},
                filters=filters
            )
            
            # Get true total count and apply pagination
            total_count = len(all_results)
            paginated_results = all_results[offset:offset + limit]
            
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
                    "highlighted": self._create_highlighted_text(result, query, match_type),
                    "match_type": match_type,
                    "matched_term": matched_term,
                    "match_score": self._normalize_score(result.score, result.search_type)
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

    def _normalize_score(self, score: float, search_type: str) -> float:
        """Normalize scores to 0-1 range based on search type."""
        if search_type == 'text':
            # Text scores are around 25.0
            return min(round(score / 25.0, 2), 1.0)
        elif search_type == 'fuzzy':
            # Fuzzy scores now range from 1.0 to 20.0 based on edit distance
            return min(round(score / 20.0, 2), 1.0)
        elif search_type == 'vector':
            # Vector scores are now in 0-20 range (similarity * 20)
            # So divide by 20 to normalize
            return min(round(score / 20.0, 2), 1.0)
        else:
            # Default normalization
            return min(round(score / 25.0, 2), 1.0)

    def _extract_matched_term(self, query: str, name: str) -> str:
        """Extract the matched term from the query."""
        query_words = query.lower().split()
        name_words = name.lower().split()
        
        for word in query_words:
            if any(word in name_word for name_word in name_words):
                return word
        return query_words[0] if query_words else query

    def _get_object_details(self, result) -> Dict[str, Any]:
        """Get object-specific details from search result indexed fields."""
        details = {}
        
        # Use the indexed_fields that were extracted from the Haystack search result
        indexed_fields = getattr(result, 'indexed_fields', {})
        
        if result.object_type == "Spell":
            # Extract spell details from indexed fields
            details = {
                "school": indexed_fields.get('school', 'Unknown'),
                "level": int(indexed_fields.get('level', 0))
            }
            
            # Add additional spell fields if available
            if 'casting_time' in indexed_fields:
                details["casting_time"] = indexed_fields['casting_time']
            if 'spell_range' in indexed_fields:
                details["range"] = indexed_fields['spell_range']
            if 'duration' in indexed_fields:
                details["duration"] = indexed_fields['duration']
            if 'components' in indexed_fields:
                details["components"] = indexed_fields['components']
            if 'classes' in indexed_fields:
                details["classes"] = indexed_fields['classes']
                
        elif result.object_type == "Creature":
            # Extract creature details from indexed fields
            details = {
                "cr": indexed_fields.get('challenge_rating', 'Unknown'),
                "type": indexed_fields.get('creature_type', 'Unknown'),
                "size": indexed_fields.get('size', 'Unknown')
            }
            
            # Add additional creature fields if available
            if 'armor_class' in indexed_fields:
                details["armor_class"] = indexed_fields['armor_class']
            if 'hit_points' in indexed_fields:
                details["hit_points"] = indexed_fields['hit_points']
                
        elif result.object_type == "Item":
            # Extract item details from indexed fields
            details = {
                "rarity": indexed_fields.get('rarity', 'Unknown'),
                "type": indexed_fields.get('item_type', 'Unknown')
            }
            
            # Add additional item fields if available
            if 'requires_attunement' in indexed_fields:
                details["requires_attunement"] = indexed_fields['requires_attunement']
                
        elif result.object_type == "CharacterClass":
            # Extract class details from indexed fields
            details = {
                "hit_die": indexed_fields.get('hit_die', 'Unknown')
            }
            
        elif result.object_type in ["Background", "Feat", "Species"]:
            # These types don't have additional specific fields in the current indexes
            details = {}
        
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

    def _create_highlighted_text(self, result, query: str, match_type: str = None) -> str:
        """Create highlighted text with HTML spans around matched terms."""
        # Use the determined match_type or fall back to search_type
        if match_type is None:
            match_type = getattr(result, 'search_type', 'exact')
        
        # For fuzzy results, try to highlight the name that matched fuzzily
        if match_type == 'fuzzy':
            return self._create_fuzzy_highlighted_text(result, query)
        
        # For vector/semantic results, highlight any query words that appear
        elif match_type == 'semantic':
            return self._create_vector_highlighted_text(result, query)
        
        # For text/exact results, use the existing logic
        else:
            return self._create_text_highlighted_text(result, query)

    def _create_fuzzy_highlighted_text(self, result, query: str) -> str:
        """Create highlighted text for fuzzy search results."""
        # For fuzzy results, the name is what matched fuzzily
        name = result.name
        text = result.description or result.name
        query_lower = query.lower().strip()
        name_lower = name.lower()
        
        # Strategy 1: Highlight the name itself since it's the fuzzy match
        # We'll highlight the closest matching parts
        highlighted_name = self._highlight_fuzzy_match_in_name(name, query_lower)
        
        # If we successfully highlighted the name, use it
        if '<span class="highlighted">' in highlighted_name:
            if result.description and len(result.description) > len(name):
                description_snippet = result.description[:120]
                return f"{highlighted_name}. {description_snippet}{'...' if len(result.description) > 120 else ''}"
            else:
                return highlighted_name
        
        # Strategy 2: Look for any exact query words in the description
        query_words = [word.strip().lower() for word in query.lower().split() if word.strip() and len(word.strip()) > 2]
        if query_words:
            return self._highlight_query_words_in_text(text, query_words)
        
        # Strategy 3: At minimum, highlight the name itself to show what matched
        return f'<span class="highlighted">{name}</span>. {text[:100]}{"..." if len(text) > 100 else ""}'
    
    def _highlight_fuzzy_match_in_name(self, name: str, query: str) -> str:
        """Highlight the closest matching parts of a name for fuzzy search."""
        name_lower = name.lower()
        highlighted_name = name
        
        # Strategy 1: Look for the query as a substring
        if query in name_lower:
            # Find the position and highlight it
            start_pos = name_lower.find(query)
            if start_pos != -1:
                # Extract the actual casing from the original name
                actual_match = name[start_pos:start_pos + len(query)]
                highlighted_name = highlighted_name.replace(
                    actual_match, 
                    f'<span class="highlighted">{actual_match}</span>',
                    1
                )
                return highlighted_name
        
        # Strategy 2: Look for longest common substring
        max_len = 0
        best_match_start = 0
        best_match_query_start = 0
        
        # Find longest common substring between query and name
        for i in range(len(query)):
            for j in range(len(name_lower)):
                length = 0
                while (i + length < len(query) and 
                       j + length < len(name_lower) and 
                       query[i + length] == name_lower[j + length]):
                    length += 1
                
                if length > max_len and length >= 3:  # At least 3 characters
                    max_len = length
                    best_match_start = j
                    best_match_query_start = i
        
        # If we found a good match, highlight it
        if max_len >= 3:
            actual_match = name[best_match_start:best_match_start + max_len]
            highlighted_name = highlighted_name.replace(
                actual_match,
                f'<span class="highlighted">{actual_match}</span>',
                1
            )
            return highlighted_name
        
        # Strategy 3: Highlight individual matching characters (for very fuzzy matches)
        # Look for query words that appear in the name
        query_words = query.split()
        for word in query_words:
            if len(word) >= 3 and word in name_lower:
                # Find the actual case version in the original name
                word_start = name_lower.find(word)
                if word_start != -1:
                    actual_word = name[word_start:word_start + len(word)]
                    highlighted_name = highlighted_name.replace(
                        actual_word,
                        f'<span class="highlighted">{actual_word}</span>',
                        1
                    )
                    return highlighted_name
        
        return highlighted_name

    def _create_vector_highlighted_text(self, result, query: str) -> str:
        """Create highlighted text for vector search results."""
        # For vector results, highlight any query words that appear in the text
        # This won't be perfect since vector search finds semantic matches,
        # but it's better than no highlighting
        text = result.description or result.name
        query_words = [word.strip().lower() for word in query.lower().split() if word.strip() and len(word.strip()) > 2]
        
        return self._highlight_query_words_in_text(text, query_words)

    def _highlight_query_words_in_text(self, text: str, query_words: List[str]) -> str:
        """Highlight query words in text and create an appropriate excerpt."""
        if not query_words:
            return self._create_excerpt(text, 0, 150)
        
        text_lower = text.lower()
        best_pos = 0
        matches_found = []
        
        # Find positions of all query word matches
        for word in query_words:
            pos = text_lower.find(word)
            if pos != -1:
                matches_found.append((pos, word))
                if not best_pos:  # Use first match for centering
                    best_pos = pos
        
        # If no exact matches found, try partial matches for semantic context
        if not matches_found:
            for word in query_words:
                for i in range(len(text_lower) - len(word) + 1):
                    # Look for words that contain the query word as substring
                    if word in text_lower[i:i+20]:  # Check in a small window
                        word_start = text_lower.find(' ', max(0, i-10))
                        word_end = text_lower.find(' ', i+20)
                        if word_start != -1 and word_end != -1:
                            best_pos = word_start
                            break
                if best_pos:
                    break
        
        # Create excerpt around the best match position
        excerpt_start = max(0, best_pos - 75)
        excerpt_end = min(len(text), best_pos + 150)
        excerpt = text[excerpt_start:excerpt_end]
        
        # Highlight exact word matches in the excerpt
        highlighted_excerpt = excerpt
        for word in query_words:
            if len(word) >= 2:
                # Case-insensitive replacement with word boundaries
                word_pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
                highlighted_excerpt = word_pattern.sub(
                    r'<span class="highlighted">\g<0></span>',
                    highlighted_excerpt,
                    count=3  # Limit replacements to avoid overhead
                )
        
        # Add ellipsis indicators
        if excerpt_start > 0:
            highlighted_excerpt = "..." + highlighted_excerpt
        if excerpt_end < len(text):
            highlighted_excerpt = highlighted_excerpt + "..."
        
        return highlighted_excerpt

    def _create_text_highlighted_text(self, result, query: str) -> str:
        """Create highlighted text for text search results (original logic)."""
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