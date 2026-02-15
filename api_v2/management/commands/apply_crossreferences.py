"""
Apply suggested cross-references to the database from text-matching.

Delegates to scripts/crossreference/apply_crossreferences.py.
"""

from django.core.management.base import BaseCommand, CommandError

from scripts.crossreference.apply_crossreferences import run as run_apply_crossreferences


class Command(BaseCommand):
    help = (
        "Create CrossReference rows from text-matching for the given document. "
        "Use --dry-run to preview; use --replace to delete existing crossrefs for "
        "the document before creating."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--document",
            type=str,
            required=True,
            help="Document key (e.g. srd-2024).",
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
            "--dry-run",
            action="store_true",
            help="Only print what would be created; do not create.",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Delete existing crossrefs whose source is in this document before creating.",
        )

    def handle(self, *args, **options):
        doc_key = options["document"]
        try:
            run_apply_crossreferences(
                doc_key,
                source_blacklist_path=options["source_blacklist"],
                reference_blacklist_path=options["reference_blacklist"],
                dry_run=options["dry_run"],
                replace_existing=options["replace"],
                stdout=self.stdout,
                style_success=self.style.SUCCESS,
            )
        except Exception as e:
            if type(e).__name__ == "DoesNotExist" or "not found" in str(e).lower():
                raise CommandError(f"Document not found: {doc_key} ({e})") from e
            if isinstance(e, ValueError):
                raise CommandError(str(e)) from e
            raise
