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
            from .services import get_tfidf_vectorizer, get_vector_index
            
            # Initialize TF-IDF vectorizer and build index
            get_tfidf_vectorizer()
            get_vector_index()
            
            logger.info("Search components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing search components: {e}")
            # Don't crash the app if search initialization fails
