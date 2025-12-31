import logging
import os
import sys

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'search'

    def ready(self):
        self._maybe_schedule_background_reindex()

    def _maybe_schedule_background_reindex(self):
        if 'manage.py' in sys.argv:
            skip_commands = [
                'quicksetup', 'migrate', 'makemigrations', 'buildindex',
                'indexctl', 'loaddata', 'import', 'collectstatic', 'shell',
                'test', 'check', 'rebuild_index', 'update_index'
            ]
            if any(cmd in sys.argv for cmd in skip_commands):
                return

        if os.environ.get('DISABLE_BACKGROUND_REINDEX', '').lower() in ('true', '1', 'yes'):
            return

        # Only run in the reloader's main process for runserver
        is_runserver = 'runserver' in sys.argv
        is_main_process = os.environ.get('RUN_MAIN') == 'true'
        if is_runserver and not is_main_process:
            return

        from django.conf import settings
        from search.background_indexer import schedule_background_reindex

        delay = getattr(settings, 'SEARCH_INDEX_REFRESH_DELAY', 60)
        rebuild_vector = getattr(settings, 'SEARCH_INDEX_REFRESH_VECTOR', True)

        if delay and delay > 0:
            schedule_background_reindex(
                delay_seconds=delay,
                rebuild_vector=rebuild_vector
            )
