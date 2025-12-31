import os
import sys
import logging
from haystack.signals import RealtimeSignalProcessor

logger = logging.getLogger(__name__)


class ConditionalSignalProcessor(RealtimeSignalProcessor):
    """Signal processor that skips indexing during bulk data loading."""

    def handle_save(self, sender, **kwargs):
        if self._should_skip_indexing():
            return
        try:
            super().handle_save(sender, **kwargs)
        except Exception as e:
            logger.debug(f"Indexing failed for {sender}: {e}")

    def handle_delete(self, sender, **kwargs):
        if self._should_skip_indexing():
            return
        try:
            super().handle_delete(sender, **kwargs)
        except Exception as e:
            logger.debug(f"Index deletion failed for {sender}: {e}")

    def _should_skip_indexing(self):
        if os.environ.get('DISABLE_HAYSTACK_INDEXING', '').lower() in ['true', '1', 'yes']:
            return True

        if 'manage.py' in sys.argv:
            skip_commands = ['loaddata', 'quicksetup', 'import', 'buildindex']
            if any(cmd in sys.argv for cmd in skip_commands):
                return True

        return False
