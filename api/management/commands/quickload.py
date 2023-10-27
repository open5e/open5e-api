"""Helper command to load all data sources."""

import subprocess

from django.core.management import call_command
from django.core.management.base import BaseCommand

# SOURCE_DIRS contains every data directory full of JSON to import.
SOURCE_DIRS = [
    './data/open5e_original/',
    './data/WOTC_5e_SRD_v5.1/',
    './data/tome_of_beasts/',
    './data/creature_codex/',
    './data/tome_of_beasts_2/',
    './data/deep_magic/',
    './data/menagerie/',
    './data/tome_of_beasts_3/',
    './data/a5e_srd/',
    './data/kobold_press/',
    './data/deep_magic_extended/',
    './data/warlock/',
    './data/vault_of_magic',
    './data/tome_of_heroes/',
    './data/taldorei/'
]

class Command(BaseCommand):
    """Implementation for the `manage.py quickload` subcommand."""

    help = 'Load all data sources by running `populatedb` for each source dir.'

    def handle(self, *args, **options) -> None:
        """Main logic."""
        self.stdout.write('Loading data from all sources...')
        populate_db()
        self.stdout.write(self.style.SUCCESS('Data loading complete.'))


def populate_db() -> None:
    """Run `manage.py populatedb` for all data sources."""
    call_command('populatedb', '--flush', *SOURCE_DIRS)
