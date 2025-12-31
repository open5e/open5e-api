"""
Custom Haystack signal processor that can be disabled during setup.
"""
import os
import sys
import logging
from haystack.signals import RealtimeSignalProcessor

logger = logging.getLogger(__name__)


class ConditionalSignalProcessor(RealtimeSignalProcessor):
    """
    A signal processor that can be disabled via environment variable.
    
    This allows us to temporarily disable automatic indexing during
    fixture loading or when running management commands.
    """
    
    def handle_save(self, sender, **kwargs):
        """Handle model save signals, but only if indexing is enabled."""
        if self._should_skip_indexing():
            return
        
        try:
            super().handle_save(sender, **kwargs)
        except Exception as e:
            logger.debug(f"Indexing failed for {sender}: {e}")
    
    def handle_delete(self, sender, **kwargs):
        """Handle model delete signals, but only if indexing is enabled."""
        if self._should_skip_indexing():
            return
        
        try:
            super().handle_delete(sender, **kwargs)
        except Exception as e:
            logger.debug(f"Index deletion failed for {sender}: {e}")
    
    def _should_skip_indexing(self):
        """Check if we should skip indexing based on environment or context."""
        # Skip indexing if explicitly disabled
        if os.environ.get('DISABLE_HAYSTACK_INDEXING', '').lower() in ['true', '1', 'yes']:
            return True
        
        # Skip during data loading commands
        if 'manage.py' in sys.argv:
            skip_commands = ['loaddata', 'quicksetup', 'import', 'buildindex']
            if any(cmd in sys.argv for cmd in skip_commands):
                return True
        
        return False
