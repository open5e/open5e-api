import os
import glob
from django.core.management import call_command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """Implementation for the `manage.py import` subcommand."""

    help = 'Import all model data recursively in structured directory.'

    def add_arguments(self, parser):
        parser.add_argument("-d",
                          "--dir",
                          type=str,
                          help="Directory to import from")

    def handle(self, *args, **options):
        data_dir = options['dir']
        
        self.stdout.write('Checking if directory exists.')
        if os.path.exists(data_dir) and os.path.isdir(data_dir):
            self.stdout.write('Directory {} exists.'.format(data_dir))
        else:
            self.stdout.write(self.style.ERROR(
                'Directory {} does not exist.'.format(data_dir)))
            exit(0)

        fixture_filepaths = glob.glob(data_dir + '/**/*.json', recursive=True)
        call_command('loaddata', fixture_filepaths)
