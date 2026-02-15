"""
Delete cross-references by source document with optional model and blacklists.

Called by management command delete_crossreferences.
"""

from scripts.crossreference.core import (
    get_crossreferences_by_source_document,
    get_document,
    load_blacklist,
)


def run(
    doc_key: str,
    *,
    model_name: str | None = None,
    source_blacklist_path: str | None = None,
    reference_blacklist_path: str | None = None,
    dry_run: bool = False,
    stdout=None,
    style_success=None,
):
    """
    Resolve document, load blacklists, get crossref queryset, then delete (or dry-run).

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

    qs = get_crossreferences_by_source_document(
        doc,
        source_model_name=model_name,
        source_blacklist=source_blacklist,
        reference_blacklist=reference_blacklist,
    )
    count = qs.count()

    if dry_run:
        write(
            f"Would delete {count} crossreferences (source document {doc_key}). "
            "Run without --dry-run to delete."
        )
        return

    qs.delete()
    write(success(f"Deleted {count} crossreferences (source document {doc_key})."))
