"""Helper command to fully set up the API."""

import subprocess

from django.core.management.base import BaseCommand

from api.management.commands import quickload

class Command(BaseCommand):
    """Implementation for the `manage.py quicksetup` subcommand."""

    def handle(self, *args, **options):
        """Main logic."""
        migrate_db()
        collect_static()
        quickload.populate_db()
        rebuild_index()


def migrate_db() -> None:
    """Migrate the local database as needed to incorporate new model updates."""
    subprocess.run(['pipenv', 'run', 'python', 'manage.py', 'makemigrations'])
    subprocess.run(['pipenv', 'run', 'python', 'manage.py', 'python', 'migrate'])


def collect_static() -> None:
    """Collect static files in a single location."""
    subprocess.run(['pipenv', 'run', 'python', 'manage.py', 'collectstatic', '--noinput'])


def rebuild_index() -> None:
    """Freshen the search indexes."""
    subprocess.run(['pipenv', 'run', 'python', 'manage.py', 'update_index', '--remove'])
