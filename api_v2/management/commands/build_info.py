"""Write server/build_info.json for the /health endpoint.

The Docker build runs this, because the runtime image doesn't include
pyproject.toml or the data fixtures that /health reports on.
"""
import json

from django.core.management.base import BaseCommand

from server.health import BUILD_INFO_PATH, collect_build_info


class Command(BaseCommand):
    help = 'Write the version, release, schema and data hashes for /health to server/build_info.json.'

    def add_arguments(self, parser):
        parser.add_argument('--release-id',
                            help='The release, e.g. v2.2.3-66-g35e06545. Defaults to OPEN5E_RELEASE_ID or git describe.')

    def handle(self, *args, **options):
        info = collect_build_info(release_id=options['release_id'])
        BUILD_INFO_PATH.write_text(json.dumps(info, indent=2) + '\n', encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(
            f"Wrote {BUILD_INFO_PATH}: version {info['version']}, release {info['releaseId']}, "
            f"{len(info['data'])} documents"))
