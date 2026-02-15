"""
Apply suggested cross-references to the database from text-matching results.

Supports --dry-run and --replace (delete existing for document first).
Called by management command apply_crossreferences.
"""

from api_v2.models import CrossReference

from scripts.crossreference.core import (
    build_object_url,
    get_crossreferences_by_source_document,
    get_document,
    get_reference_candidates_for_document,
    identify_crossreferences_from_text,
    load_blacklist,
)


def run(
    doc_key: str,
    *,
    source_blacklist_path: str | None = None,
    reference_blacklist_path: str | None = None,
    dry_run: bool = False,
    replace_existing: bool = False,
    stdout=None,
    style_success=None,
):
    """
    Run text-matching for the document, then create CrossReference rows (or report counts if dry_run).

    If replace_existing, delete existing crossrefs whose source is in the document first.
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

    success = style_success if style_success is not None else lambda x: x

    by_source, _by_reference = identify_crossreferences_from_text(
        doc,
        source_blacklist=source_blacklist,
        reference_blacklist=reference_blacklist,
    )

    ref_url_to_ct_key = {}
    for ref_ct, ref_key, _ref_name in get_reference_candidates_for_document(doc):
        url = build_object_url(ref_ct, ref_key)
        ref_url_to_ct_key[url] = (ref_ct, ref_key)

    to_create = []
    for key_src, (src_url, ref_list) in by_source.items():
        src_ct_id, source_object_key = key_src
        for ref_url, anchor in ref_list:
            if ref_url not in ref_url_to_ct_key:
                continue
            ref_ct, ref_key = ref_url_to_ct_key[ref_url]
            to_create.append(
                CrossReference(
                    document=doc,
                    source_content_type_id=src_ct_id,
                    source_object_key=source_object_key,
                    reference_content_type=ref_ct,
                    reference_object_key=ref_key,
                    anchor=anchor,
                )
            )

    if dry_run:
        replace_count = 0
        if replace_existing:
            qs = get_crossreferences_by_source_document(
                doc,
                source_blacklist=source_blacklist,
                reference_blacklist=reference_blacklist,
            )
            replace_count = qs.count()
        write(
            f"Would create {len(to_create)} crossreferences (source document {doc_key})."
        )
        if replace_existing:
            write(f"Would delete {replace_count} existing crossreferences first.")
        write("Run without --dry-run to apply.")
        return

    if replace_existing:
        qs = get_crossreferences_by_source_document(
            doc,
            source_blacklist=source_blacklist,
            reference_blacklist=reference_blacklist,
        )
        replace_count = qs.count()
        qs.delete()
        write(f"Deleted {replace_count} existing crossreferences.")

    CrossReference.objects.bulk_create(to_create)
    write(success(f"Created {len(to_create)} crossreferences (source document {doc_key})."))
