"""
Find objects in a document that are candidates for adding cross-references.

One-shot run: pass --document and optionally blacklist paths. Output to console.
"""

from django.core.management.base import BaseCommand, CommandError

from api_v2.crossreference_utils import (
    get_document,
    get_source_models_and_filters_for_document,
    load_blacklist,
    write_crossreference_report_files,
)


class Command(BaseCommand):
    help = (
        "List objects with descriptions in a document that are candidates for "
        "adding cross-references. Output to console."
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
        source_blacklist_path = options["source_blacklist"]
        reference_blacklist_path = options["reference_blacklist"]
        sources_report_path = options["sources_report"]
        references_report_path = options["references_report"]

        try:
            doc = get_document(doc_key)
        except Exception as e:
            raise CommandError(f"Document not found: {doc_key} ({e})")

        source_blacklist = load_blacklist(source_blacklist_path)
        reference_blacklist = load_blacklist(reference_blacklist_path)

        pairs = get_source_models_and_filters_for_document(doc)
        candidates = []

        for model, filter_kwargs in pairs:
            qs = (
                model.objects.filter(**filter_kwargs)
                .exclude(desc__isnull=True)
                .exclude(desc="")
            )
            for obj in qs:
                pk = getattr(obj, "pk", None)
                if pk is None:
                    continue
                pk_str = str(pk)
                if pk_str in source_blacklist:
                    continue
                name = getattr(obj, "name", "") or ""
                desc_len = len(obj.desc) if obj.desc else 0
                try:
                    crossref_count = obj.crossreferences.count()
                except Exception:
                    crossref_count = 0
                candidates.append(
                    (model.__name__, pk_str, name, desc_len, crossref_count)
                )

        if sources_report_path and references_report_path:
            sources_report, references_report = write_crossreference_report_files(
                doc,
                sources_report_path,
                references_report_path,
                source_blacklist=source_blacklist,
                reference_blacklist=reference_blacklist,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Wrote sources report to {sources_report_path} and references report to {references_report_path}."
                )
            )
            # Top 10 sources with the most references
            self.stdout.write("")
            self.stdout.write("Top 10 sources (most references):")
            for i, entry in enumerate(sources_report[:10], 1):
                count = len(entry["crossreference_to"])
                anchors = sorted({m["anchor"] for m in entry.get("matches", [])})
                words = f" — {', '.join(anchors)}" if anchors else ""
                self.stdout.write(f"  {i}. {entry['url']} ({count}){words}")
            # Top 10 references with the most sources
            self.stdout.write("")
            self.stdout.write("Top 10 references (most sources):")
            for i, entry in enumerate(references_report[:10], 1):
                count = len(entry["crossreference_from"])
                anchors = sorted({m["anchor"] for m in entry.get("matches", [])})
                words = f" — {', '.join(anchors)}" if anchors else ""
                self.stdout.write(f"  {i}. {entry['url']} ({count}){words}")
            return

        if sources_report_path or references_report_path:
            raise CommandError(
                "Provide both --sources-report and --references-report, or neither."
            )

        self.stdout.write(f"Document: {doc_key}")
        self.stdout.write(
            "Candidates (objects with description; source-blacklist applied):"
        )
        for model_name, key, name, desc_len, crossref_count in candidates:
            self.stdout.write(
                f"  {model_name}\t{key}\t{name}\t{desc_len}\t{crossref_count}"
            )
        self.stdout.write(f"Total: {len(candidates)} candidates.")
