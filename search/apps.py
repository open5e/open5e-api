import pickle
from pathlib import Path
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'search'
    vector_index = None  # Class attribute to store the loaded index
    
    def ready(self):
        """Called when Django starts up - build vector index during startup."""
        logger.info("SearchConfig.ready() - Initializing search components...")
        
        # Import here to avoid circular imports
        try:
            from .services import get_embedding_model, get_vector_index
            
            # Initialize embedding model during startup
            logger.info("Loading embedding model during startup...")
            get_embedding_model()
            
            # Build vector index during startup so first search is fast
            logger.info("Building vector index during startup...")
            get_vector_index()
            
            logger.info("Search components initialized successfully!")
            
        except Exception as e:
            logger.error(f"Error initializing search components: {e}")
            # Don't crash the server if search initialization fails
