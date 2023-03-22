"""Helper command to fully set up the API."""

from django.core.management import call_command
from django.core.management.base import BaseCommand

from api.management.commands import quickload

class Command(BaseCommand):
    """Implementation for the `manage.py quicksetup` subcommand."""

    def handle(self, *args, **options):
        """Main logic."""
        self.stdout.write('Migrating the database...')
        migrate_db()

        self.stdout.write('Collecting static files...')
        collect_static()

        self.stdout.write('Populating the database...')
        quickload.populate_db()

        self.stdout.write('Rebuilding the search index...')
        rebuild_index()

        self.stdout.write(self.style.SUCCESS('API setup complete.'))


def migrate_db() -> None:
    """Migrate the local database as needed to incorporate new model updates."""
    call_command('makemigrations')
    call_command('migrate')


def collect_static() -> None:
    """Collect static files in a single location."""
    call_command('collectstatic', '--noinput')


def rebuild_index() -> None:
    """Freshen the search indexes."""
    call_command('update_index', '--remove')
