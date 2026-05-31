"""
Delete groups of crossreferences by source document.

Delegates to scripts/crossreference/delete_crossreferences.py.
"""

from django.core.management.base import BaseCommand, CommandError

from scripts.crossreference.delete_crossreferences import run as run_delete_crossreferences


class Command(BaseCommand):
    help = (
        "Delete CrossReference rows whose source object belongs to the given "
        "document. Optional: restrict by source model; protect sources/references "
        "with blacklists; use --dry-run to preview."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--document",
            type=str,
            required=True,
            help="Document key; delete crossreferences whose source is in this document.",
        )
        parser.add_argument(
            "--model",
            type=str,
            default=None,
            help="If set, only delete crossreferences whose source is this model (e.g. Spell, Item).",
        )
        parser.add_argument(
            "--source-blacklist",
            type=str,
            default=None,
            help="Path to file; do not delete crossreferences whose source key is in this set.",
        )
        parser.add_argument(
            "--reference-blacklist",
            type=str,
            default=None,
            help="Path to file; do not delete crossreferences whose reference key is in this set.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only print what would be deleted; do not delete.",
        )

    def handle(self, *args, **options):
        doc_key = options["document"]
        try:
            run_delete_crossreferences(
                doc_key,
                model_name=options["model"],
                source_blacklist_path=options["source_blacklist"],
                reference_blacklist_path=options["reference_blacklist"],
                dry_run=options["dry_run"],
                stdout=self.stdout,
                style_success=self.style.SUCCESS,
            )
        except Exception as e:
            if type(e).__name__ == "DoesNotExist" or "not found" in str(e).lower():
                raise CommandError(f"Document not found: {doc_key} ({e})") from e
            raise
