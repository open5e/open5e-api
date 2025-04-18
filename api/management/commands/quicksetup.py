"""Helper command to fully set up the API."""
import argparse
import shutil
from pathlib import Path

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

        parser.add_argument(
            "--clean",
            action="store_true",
            help="Flushes all existing database data before adding new objects.",
        )

    def handle(self, *args, **options):
        self.stdout.write('Checking if the directory is dirty...')
        if options['clean']:
            clean_dir()

        if is_dirty():
            self.stdout.write('Directory is dirty, consider the --clean argument.')
        else:
            self.stdout.write('Directory is clean')

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

def is_dirty() ->None:
    # TODO switch these over to server settings values.
    is_dirty=False
    if Path('./server/whoosh_index').is_dir():
        print("Found whoosh_index")
        is_dirty=True
    if Path(settings.STATIC_ROOT).is_dir():
        print("Found static root")
        is_dirty=True
    if Path(settings.DATABASES['default']['NAME']).exists():
        print("Found db file")
        is_dirty=True
    return is_dirty

def clean_dir() ->None:
    if Path('./server/whoosh_index').is_dir():
        shutil.rmtree(Path('./server/whoosh_index'))
    if Path(settings.STATIC_ROOT).is_dir():
        shutil.rmtree(Path(settings.STATIC_ROOT))
    if Path(settings.DATABASES['default']['NAME']).exists():
        Path(settings.DATABASES['default']['NAME']).unlink()

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