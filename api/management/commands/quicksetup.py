"""Helper command to fully set up the API."""
import argparse

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Implementation for the `manage.py quicksetup` subcommand."""

    def add_arguments(self, parser: argparse.ArgumentParser):
        """Define arguments for the `manage.py quicksetup` subcommand."""
        parser.add_argument(
            "--noindex",
            action="store_true",
            help="Flushes all existing database data before adding objects.",
        )

    def handle(self, *args, **options):
        """Contents and callouts of the script."""
        self.stdout.write('Migrating the database...')
        migrate_db()

        self.stdout.write('Collecting static files...')
        collect_static()

        self.stdout.write('Populating the v1 database...')
        import_v1()

        self.stdout.write('Populating the v2 database...')
        import_v2()

        if options["noindex"]:
            self.stdout.write('Skipping search index rebuild due to --noindex')
        else:
            self.stdout.write('Rebuilding the search index...')
            rebuild_index()

        self.stdout.write(self.style.SUCCESS('API setup complete.'))


def import_v1() -> None:
    """Import the v1 apps' database models."""
    call_command('import', '--dir', 'data/v1')


def import_v2() -> None:
    """Import the v2 apps' database models."""
    call_command('import', '--dir', 'data/v2')


def migrate_db() -> None:
    """Migrate the local database as needed to incorporate new modelupdates."""
    call_command('makemigrations')
    call_command('migrate')


def collect_static() -> None:
    """Collect static files in a single location."""
    call_command('collectstatic', '--noinput')


def rebuild_index() -> None:
    """Freshen the search indexes."""
    call_command('update_index', '--remove')
