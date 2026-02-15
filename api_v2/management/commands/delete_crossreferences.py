"""
Delete groups of cross-references by source document.

Optionally restrict by source model and/or protect sources/references via blacklists.
"""

from django.core.management.base import BaseCommand, CommandError

from api_v2.crossreference_utils import (
    get_crossreferences_by_source_document,
    get_document,
    load_blacklist,
)


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
            help="Document key; delete crossrefs whose source is in this document.",
        )
        parser.add_argument(
            "--model",
            type=str,
            default=None,
            help="If set, only delete crossrefs whose source is this model (e.g. Spell, Item).",
        )
        parser.add_argument(
            "--source-blacklist",
            type=str,
            default=None,
            help="Path to file; do not delete crossrefs whose source key is in this set.",
        )
        parser.add_argument(
            "--reference-blacklist",
            type=str,
            default=None,
            help="Path to file; do not delete crossrefs whose reference key is in this set.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only print what would be deleted; do not delete.",
        )

    def handle(self, *args, **options):
        doc_key = options["document"]
        model_name = options["model"]
        source_blacklist_path = options["source_blacklist"]
        reference_blacklist_path = options["reference_blacklist"]
        dry_run = options["dry_run"]

        try:
            doc = get_document(doc_key)
        except Exception as e:
            raise CommandError(f"Document not found: {doc_key} ({e})")

        source_blacklist = load_blacklist(source_blacklist_path)
        reference_blacklist = load_blacklist(reference_blacklist_path)

        qs = get_crossreferences_by_source_document(
            doc,
            source_model_name=model_name,
            source_blacklist=source_blacklist,
            reference_blacklist=reference_blacklist,
        )
        count = qs.count()

        if dry_run:
            self.stdout.write(
                f"Would delete {count} crossreferences (source document {doc_key}). "
                "Run without --dry-run to delete."
            )
            return

        qs.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {count} crossreferences (source document {doc_key})."
            )
        )
