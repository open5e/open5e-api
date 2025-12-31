"""Helper command to fully set up the API."""
import argparse
import shutil
from pathlib import Path

from server import settings

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import IntegrityError


class Command(BaseCommand):
    """Implementation for the `manage.py quicksetup` subcommand."""

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--noindex",
            action="store_true",
            help="Skip building search indexes.",
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

        self.stdout.write('Migrating the database...')
        migrate_db()

        self.stdout.write('Collecting static files...')
        collect_static()

        if settings.INCLUDE_V1_DATA:
            self.stdout.write('Populating the v1 database...')
            try:
                import_v1()
            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(
                    f'V1 data import failed: Foreign key constraint error: {e}'
                ))
                self.stdout.write(self.style.ERROR(
                    'QUICKSETUP FAILED - Fix foreign key constraint violations before proceeding.'
                ))
                return

        if settings.INCLUDE_V2_DATA:
            self.stdout.write('Populating the v2 database...')
            try:
                import_v2()
            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(
                    f'V2 data import failed: Foreign key constraint error: {e}'
                ))
                self.stdout.write(self.style.ERROR(
                    'QUICKSETUP FAILED - Fix foreign key constraint violations before proceeding.'
                ))
                return

            if not options['noindex']:
                if settings.BUILD_V2_INDEX:
                    self.stdout.write('Building the search index...')
                    build_search_index()
            else:
                self.stdout.write('Skipping index build because of --noindex.')

        self.stdout.write(self.style.SUCCESS('API setup complete.'))


def migrate_db():
    call_command('makemigrations')
    call_command('migrate')


def is_dirty():
    is_dirty = False
    if Path('whoosh_index').is_dir():
        print("Found whoosh_index")
        is_dirty = True
    if Path(settings.STATIC_ROOT).is_dir():
        print("Found static root")
        is_dirty = True
    if Path(settings.DATABASES['default']['NAME']).exists():
        print("Found db file")
        is_dirty = True
    return is_dirty


def clean_dir():
    if Path('whoosh_index').is_dir():
        shutil.rmtree(Path('whoosh_index'))
    if Path(settings.STATIC_ROOT).is_dir():
        shutil.rmtree(Path(settings.STATIC_ROOT))
    if Path(settings.DATABASES['default']['NAME']).exists():
        Path(settings.DATABASES['default']['NAME']).unlink()
    if Path('server/vector_index.pkl').exists():
        Path('server/vector_index.pkl').unlink()


def import_v1():
    call_command('import', '--dir', 'data/v1')


def import_v2():
    call_command('import', '--dir', 'data/v2')


def collect_static():
    call_command('collectstatic', '--noinput')


def build_search_index():
    call_command('buildindex', '--v1', '--v2')
