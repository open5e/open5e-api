"""
Re-export cross-reference logic from scripts.crossreference.core for backwards compatibility.

Management commands find_crossref_candidates and delete_crossreferences delegate to
scripts/crossreference/find_candidates.py and delete_crossreferences.py.
"""

from scripts.crossreference.core import (
    REFERENCE_MODEL_NAMES,
    build_crossreference_reports,
    build_object_url,
    get_all_crossreferences_for_document,
    get_crossreferences_by_source_document,
    get_document,
    get_reference_candidates_for_document,
    get_reference_models_and_filters_for_document,
    get_source_models_and_filters_for_document,
    identify_crossreferences_from_text,
    load_blacklist,
    write_crossreference_report_files,
)

__all__ = [
    "REFERENCE_MODEL_NAMES",
    "build_crossreference_reports",
    "build_object_url",
    "get_all_crossreferences_for_document",
    "get_crossreferences_by_source_document",
    "get_document",
    "get_reference_candidates_for_document",
    "get_reference_models_and_filters_for_document",
    "get_source_models_and_filters_for_document",
    "identify_crossreferences_from_text",
    "load_blacklist",
    "write_crossreference_report_files",
]
