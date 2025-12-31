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
        # Search components are loaded lazily on first use
        # No initialization needed during Django startup
        logger.info("Search app ready - components will load on first use")
