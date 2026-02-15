"""
Find objects in a document that are candidates for adding crossreferences.

Delegates to scripts/crossreference/find_candidates.py.
"""

from django.core.management.base import BaseCommand, CommandError

from scripts.crossreference.find_candidates import run as run_find_candidates


class Command(BaseCommand):
    help = (
        "List objects with descriptions in a document that are candidates for "
        "adding crossreferences. Output to console."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--document",
            type=str,
            required=True,
            help="Document key (e.g. srd-2014).",
        )
        parser.add_argument(
            "--source-blacklist",
            type=str,
            default=None,
            help="Path to file with source keys to exclude (one per line).",
        )
        parser.add_argument(
            "--reference-blacklist",
            type=str,
            default=None,
            help="Path to file with reference keys to exclude (one per line).",
        )
        parser.add_argument(
            "--sources-report",
            type=str,
            default=None,
            help="Write JSON report of source URLs and their crossreference_to list (most first).",
        )
        parser.add_argument(
            "--references-report",
            type=str,
            default=None,
            help="Write JSON report of reference URLs and their crossreference_from list (most first).",
        )

    def handle(self, *args, **options):
        doc_key = options["document"]
        try:
            run_find_candidates(
                doc_key,
                source_blacklist_path=options["source_blacklist"],
                reference_blacklist_path=options["reference_blacklist"],
                sources_report_path=options["sources_report"],
                references_report_path=options["references_report"],
                stdout=self.stdout,
                style_success=self.style.SUCCESS,
            )
        except Exception as e:
            if type(e).__name__ == "DoesNotExist" or "not found" in str(e).lower():
                raise CommandError(f"Document not found: {doc_key} ({e})") from e
            if isinstance(e, ValueError):
                raise CommandError(str(e)) from e
            raise
