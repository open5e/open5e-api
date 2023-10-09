

import os
import json
import glob

from django.core.management import call_command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """Implementation for the `manage.py `dumpbyorg` subcommand."""

    help = 'Import all v2 model data recursively in structured directory.'

    def add_arguments(self, parser):
        parser.add_argument("-d", "--dir", type=str,
                            help="Directory to write files to.")
        parser.add_argument("--noindex", action="store_true", default=False,
                            help="Does not trigger search indexing")
        parser.add_argument("--nomonsterspell", action="store_true", default=False,
                            help="Does not trigger v1 monster-spell relationship.")

    def build_v1_monster_spell(self):
        self.stdout.write('Creating monster-spell relationship.')

    def build_index(self):
        self.stdout.write('Building search index.')

    def handle(self, *args, **options) -> None:
        self.stdout.write('Checking if directory exists.')
        if os.path.exists(options['dir']) and os.path.isdir(options['dir']):
            self.stdout.write('Directory {} exists.'.format(options['dir']))
        else:
            self.stdout.write(self.style.ERROR(
                'Directory {} does not exist.'.format(options['dir'])))
            exit(0)

        fixture_filepaths = glob.glob(options['dir'] + '/**/*.json', recursive=True)

        call_command('loaddata', fixture_filepaths)
        
        if not options['nomonsterspell']:
            self.build_v1_monster_spell()

        if not options['noindex']:
            self.build_index()
