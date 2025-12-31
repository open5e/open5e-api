"""Rebuild search indexes from data."""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Rebuild search indexes from data (takes 2-3 minutes)"

    def handle(self, *args, **options):
        self.stdout.write("Rebuilding search indexes...")
        call_command('buildindex', '--v1', '--v2')
        call_command('indexctl', 'pack')
        self.stdout.write(self.style.SUCCESS(
            "Done! Commit search/indexes/ and search/index_manifest.json"
        ))

