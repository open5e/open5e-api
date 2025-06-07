

import os
import json
import glob

from django.core.management import call_command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """Implementation for the `manage.py `dumpbyorg` subcommand."""

    help = 'Import all v2 model data recursively in structured directory.'

    def add_arguments(self, parser):
        parser.add_argument("-d",
                            "--dir",
                            type=str,
                            help="Directory to write files to.")
        parser.add_argument("--skip-concepts",
                            action="store_true",
                            help="Skip automatic concept population after import.")

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
        
        # After loading data, populate concept objects to aggregate equivalent content across systems
        if not options.get('skip_concepts', False):
            self.stdout.write(self.style.SUCCESS('Data import complete. Now populating concept aggregations...'))
            call_command('populate_concepts')
        else:
            self.stdout.write('Skipping concept population (--skip-concepts flag provided)')
