"""Helper command to load all data sources."""

import subprocess

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
]

class Command(BaseCommand):
    """Implementation for the `manage.py quickload` subcommand."""

    def handle(self, *args, **options) -> None:
        """Main logic."""
        populate_db()


def populate_db() -> None:
    """Run `manage.py populatedb` for all data sources."""
    cmd = ['pipenv', 'run', 'python', 'manage.py', 'populatedb', '--flush']
    cmd.extend(SOURCE_DIRS)
    subprocess.run(cmd)
