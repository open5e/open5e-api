"""
Find crossreference candidates for a document; optionally write report files and print top 10.

Called by management command find_crossreference_candidates.
"""

from scripts.crossreference.core import (
    get_document,
    get_source_models_and_filters_for_document,
    load_blacklist,
    write_crossreference_report_files,
    _is_crossreference_source,
)


def run(
    doc_key: str,
    *,
    source_blacklist_path: str | None = None,
    reference_blacklist_path: str | None = None,
    sources_report_path: str | None = None,
    references_report_path: str | None = None,
    stdout=None,
    style_success=None,
):
    """
    Run find-candidates logic: resolve document, load blacklists, then either
    write reports + print top 10 (if both report paths given) or print candidate list.

    stdout: object with .write(str). If None, print() is used.
    style_success: callable(str) -> str for success message. If None, identity.
    """
    doc = get_document(doc_key)
    source_blacklist = load_blacklist(source_blacklist_path)
    reference_blacklist = load_blacklist(reference_blacklist_path)

    def write(line: str) -> None:
        if stdout is not None:
            stdout.write(line)
        else:
            print(line)

    success = (style_success if style_success is not None else lambda x: x)

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
            if not _is_crossreference_source(obj):
                continue
            pk_str = str(pk)
            if pk_str in source_blacklist:
                continue
            name = getattr(obj, "name", "") or ""
            desc_len = len(obj.desc) if obj.desc else 0
            try:
                crossreference_count = obj.crossreferences.count()
            except Exception:
                crossreference_count = 0
            candidates.append(
                (model.__name__, pk_str, name, desc_len, crossreference_count)
            )

    if sources_report_path and references_report_path:
        sources_report, references_report = write_crossreference_report_files(
            doc,
            sources_report_path,
            references_report_path,
            source_blacklist=source_blacklist,
            reference_blacklist=reference_blacklist,
        )
        write(success(
            f"Wrote sources report to {sources_report_path} and references report to {references_report_path}."
        ))
        write("")
        write("Top 10 sources (most references):")
        for i, entry in enumerate(sources_report[:10], 1):
            count = len(entry["crossreference_to"])
            anchors = sorted({m["anchor"] for m in entry.get("matches", [])})
            words = f" — {', '.join(anchors)}" if anchors else ""
            write(f"  {i}. {entry['url']} ({count}){words}")
        write("")
        write("Top 10 references (most sources):")
        for i, entry in enumerate(references_report[:10], 1):
            count = len(entry["crossreference_from"])
            anchors = sorted({m["anchor"] for m in entry.get("matches", [])})
            words = f" — {', '.join(anchors)}" if anchors else ""
            write(f"  {i}. {entry['url']} ({count}){words}")
        return

    if sources_report_path or references_report_path:
        raise ValueError(
            "Provide both --sources-report and --references-report, or neither."
        )

    write(f"Document: {doc_key}")
    write(
        "Candidates (objects with description; source-blacklist applied):"
    )
    for model_name, key, name, desc_len, crossreference_count in candidates:
        write(
            f"  {model_name}\t{key}\t{name}\t{desc_len}\t{crossreference_count}"
        )
    write(f"Total: {len(candidates)} candidates.")
