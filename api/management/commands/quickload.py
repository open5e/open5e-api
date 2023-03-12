"""Helper command to load all data sources."""

import subprocess

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """Implementation for the `manage.py quickload` subcommand."""

    def handle(self, *args, **options) -> None:
        """Main logic."""
        populate_db()


def populate_db() -> None:
    """Run `manage.py populatedb` for all data sources."""
    source_dirs = (
        './data/open5e_original/',
        './data/WOTC_5e_SRD_v5.1/',
        './data/tome_of_beasts/',
        './data/creature_codex/',
        './data/tome_of_beasts_2/',
        './data/deep_magic/',
        './data/menagerie/',
        './data/tome_of_beasts_3/',
    )
    # Flush the DB on the first pass.
    # Then append so that we don't flush what we made the first time.
    is_first_round = True
    for source_dir in source_dirs:
        cmd = ['pipenv', 'run', 'python', 'manage.py', 'populatedb']
        if is_first_round:
            cmd.append('--flush')
            is_first_round = False
        else:
            cmd.append('--append')
        cmd.append(source_dir)
        subprocess.run(cmd)
