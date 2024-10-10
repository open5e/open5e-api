"""Helper command to fully set up the API."""
import argparse

from server import settings

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Implementation for the `manage.py quicksetup` subcommand."""

    def add_arguments(self, parser: argparse.ArgumentParser):
        """Define arguments for the `manage.py quicksetup` subcommand."""

        # Named (optional) arguments.
        parser.add_argument(
            "--noindex",
            action="store_true",
            help="Flushes all existing database data before adding new objects.",
        )

    def handle(self, *args, **options):
        """[TODO] Check if the directory is dirty."""
        # Does whoosh_index exist
        
        # Does staticfiles exist
        # Does db.sqlite3 exist

        
        """Main logic."""
        self.stdout.write('Migrating the database...')
        migrate_db()

        self.stdout.write('Collecting static files...')
        collect_static()

        if settings.INCLUDE_V1_DATA:
            self.stdout.write('Populating the v1 database...')
            import_v1()
            
            if not options['noindex']:
                if settings.BUILD_V1_INDEX:
                    build_haystack_index()
            else:
                self.stdout.write("Skipping v1 index build because of --noindex")
        else:
            self.stdout.write('Skipping v1 database population.')

        if settings.INCLUDE_V2_DATA:
            self.stdout.write('Populating the v2 database...')
            import_v2()

        if not options['noindex']:
            if settings.BUILD_V2_INDEX:
                self.stdout.write('Building the v2 index with both v1 and v2 data.')
                build_v1v2_searchindex()
        else:
            self.stdout.write('Skipping v2 index build because of --noindex.')

        self.stdout.write(self.style.SUCCESS('API setup complete.'))


def migrate_db() -> None:
    """Migrate the local database as needed to incorporate new model updates.
    This command is added primarily to assist in local development, because
    checking out and changing branches results in unclean model/dbs."""

    call_command('makemigrations')
    call_command('migrate')


def import_v1() -> None:
    """Import the v1 apps' database models."""
    call_command('import', '--dir', 'data/v1')


def import_v2() -> None:
    """Import the v2 apps' database models."""
    call_command('import', '--dir', 'data/v2')


def collect_static() -> None:
    """Collect static files in a single location."""
    call_command('collectstatic', '--noinput')


def build_haystack_index() -> None:
    """Freshen the haystack search indexes. This is an internal haystack
    API that is being called, and only applies to v1 data."""
    print("THIS ENTIRE COMMAND HAS BEEN DEPRECATED! EXPECT ERRORS.")
    call_command('update_index', '--remove')

def build_v1v2_searchindex() -> None:
    """Builds the custom search index defined in the api_v2 management
    commands. Only adds the v1 data."""
    call_command('buildindex','--v1','--v2')