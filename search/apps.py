"""
Search app configuration for Open5e API.
"""
import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class SearchConfig(AppConfig):
    """Configuration for the search app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'search'
    
    def ready(self):
        """Initialize search components when Django starts."""
        try:
            logger.info("Initializing search components...")
            from .services import get_tfidf_vectorizer
            
            # Initialize TF-IDF vectorizer (doesn't require Elasticsearch)
            get_tfidf_vectorizer()
            # Skip vector index building during startup - it will be built on first search
            
            logger.info("Search components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing search components: {e}")
            # Don't crash the app if search initialization fails
