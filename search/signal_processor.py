"""
Custom Haystack signal processor that can be disabled during setup.
"""
import os
import logging
from haystack.signals import RealtimeSignalProcessor

logger = logging.getLogger(__name__)


class ConditionalSignalProcessor(RealtimeSignalProcessor):
    """
    A signal processor that can be disabled via environment variable.
    
    This allows us to temporarily disable automatic indexing during
    fixture loading when Elasticsearch isn't available.
    """
    
    def handle_save(self, sender, **kwargs):
        """Handle model save signals, but only if indexing is enabled."""
        if self._should_skip_indexing():
            return
        
        try:
            super().handle_save(sender, **kwargs)
        except Exception as e:
            # Log but don't crash during setup
            logger.debug(f"Indexing failed for {sender}: {e}")
    
    def handle_delete(self, sender, **kwargs):
        """Handle model delete signals, but only if indexing is enabled."""
        if self._should_skip_indexing():
            return
        
        try:
            super().handle_delete(sender, **kwargs)
        except Exception as e:
            # Log but don't crash during setup
            logger.debug(f"Index deletion failed for {sender}: {e}")
    
    def _should_skip_indexing(self):
        """Check if we should skip indexing based on environment variables."""
        # Skip indexing if explicitly disabled
        if os.environ.get('DISABLE_HAYSTACK_INDEXING', '').lower() in ['true', '1', 'yes']:
            return True
        
        # Skip indexing if Elasticsearch URL suggests it's not available
        es_url = os.environ.get('ELASTICSEARCH_URL', 'http://127.0.0.1:9200/')
        if 'localhost' in es_url or '127.0.0.1' in es_url:
            # In Docker build, localhost connections will fail
            # This is a heuristic to detect build environment
            import sys
            if 'manage.py' in sys.argv and any(cmd in sys.argv for cmd in ['loaddata', 'quicksetup']):
                return True
        
        return False 