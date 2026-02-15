"""
Shared utilities for cross-reference candidate finding and deletion by document.

Used by find_crossref_candidates and delete_crossreferences management commands.
"""

import json
import re
from pathlib import Path

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models.fields.related import ForeignKey

from api_v2.models import CrossReference, Document

# FK field names that point to a "parent" entity; sources with these will not link to that parent.
PARENT_FIELD_NAMES = ("parent", "subclass_of")

# Object keys containing any of these substrings are excluded as both sources and references.
EXCLUDED_KEY_SUBSTRINGS = ("spellcasting-levels",)

# Reference names that are never suggested as links (e.g. ordinal table headers like "1st", "6th").
EXCLUDED_REFERENCE_NAMES = frozenset({"1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th"})


# Map api_v2 model name to URL path segment (router basename) for building /v2/{basename}/{pk}/.
MODEL_TO_URL_BASENAME = {
    "Item": "items",
    "ItemSet": "itemsets",
    "ItemCategory": "itemcategories",
    "ItemRarity": "itemrarities",
    "Ability": "abilities",
    "AbilityDescription": "abilities",
    "Skill": "skills",
    "SkillDescription": "skills",
    "Armor": "armor",
    "Weapon": "weapons",
    "WeaponProperty": "weaponproperties",
    "Species": "species",
    "SpeciesTrait": "species",
    "Feat": "feats",
    "FeatBenefit": "feats",
    "Background": "backgrounds",
    "BackgroundBenefit": "backgrounds",
    "Creature": "creatures",
    "CreatureTrait": "creatures",
    "CreatureAction": "creatures",
    "CreatureType": "creaturetypes",
    "CreatureTypeDescription": "creaturetypes",
    "CreatureSet": "creaturesets",
    "Document": "documents",
    "DamageType": "damagetypes",
    "DamageTypeDescription": "damagetypes",
    "Language": "languages",
    "Alignment": "alignments",
    "AlignmentDescription": "alignments",
    "Condition": "conditions",
    "ConditionDescription": "conditions",
    "Spell": "spells",
    "SpellSchool": "spellschools",
    "SpellCastingOption": "spells",
    "ClassFeature": "classes",
    "ClassFeatureItem": "classes",
    "CharacterClass": "classes",
    "Size": "sizes",
    "Environment": "environments",
    "Rule": "rules",
    "RuleSet": "rulesets",
    "Image": "images",
    "Service": "services",
}


def build_object_url(content_type: ContentType, object_key: str) -> str:
    """Return the API v2 path for an object, e.g. /v2/spells/srd_fireball/."""
    model = content_type.model_class()
    if model is None:
        return f"/v2/unknown/{object_key}/"
    basename = MODEL_TO_URL_BASENAME.get(model.__name__)
    if basename is None:
        basename = (model._meta.verbose_name_plural or model.__name__.lower() + "s").replace(" ", "")
    return f"/v2/{basename}/{object_key}/"


# Model classification for document scoping (aligned with export command).
SKIPPED_MODEL_NAMES = [
    "Document",
    "GameSystem",
    "License",
    "Publisher",
    "SearchResult",
]
CHILD_MODEL_NAMES = [
    "SpeciesTrait",
    "FeatBenefit",
    "BackgroundBenefit",
    "ClassFeatureItem",
    "SpellCastingOption",
    "CreatureAction",
    "CreatureTrait",
]
CHILD_CHILD_MODEL_NAMES = ["CreatureActionAttack"]

# Models that can be mentioned in descriptions (reference targets for text-matching).
REFERENCE_MODEL_NAMES = [
    "Spell",
    "Item",
    "Condition",
    "ConditionDescription",
    "Feat",
    "Rule",
    "RuleSet",
    "WeaponProperty",
    "DamageTypeDescription",
    "AbilityDescription",
    "SkillDescription",
    "AlignmentDescription",
    "CreatureTypeDescription",
    "Language",
    "Environment",
    "Background",
    "Species",
    "CharacterClass",
    "ClassFeature",
]


def _model_has_name(model) -> bool:
    """Return True if the model has a name field."""
    return any(f.name == "name" for f in model._meta.get_fields())


def get_reference_models_and_filters_for_document(doc):
    """
    Return (model, filter_kwargs) for all api_v2 models that are in REFERENCE_MODEL_NAMES,
    have a name field, and belong to the given document.
    """
    result = []
    for model in apps.get_models():
        if model._meta.app_label != "api_v2":
            continue
        if model.__name__ not in REFERENCE_MODEL_NAMES:
            continue
        if not _model_has_name(model):
            continue

        if model.__name__ in CHILD_CHILD_MODEL_NAMES:
            filter_kwargs = {"parent__parent__document": doc}
        elif model.__name__ in CHILD_MODEL_NAMES:
            filter_kwargs = {"parent__document": doc}
        else:
            filter_kwargs = {"document": doc}

        result.append((model, filter_kwargs))
    return result


def get_reference_candidates_for_document(doc):
    """
    Yield (content_type, object_key, name) for every reference candidate in the document.
    Name is stripped; used for case-insensitive substring match in descriptions.
    """
    for model, filter_kwargs in get_reference_models_and_filters_for_document(doc):
        ct = ContentType.objects.get_for_model(model)
        qs = model.objects.filter(**filter_kwargs)
        for obj in qs:
            name = getattr(obj, "name", None)
            if name is None or not str(name).strip():
                continue
            yield ct, str(obj.pk), str(name).strip()


def get_document(doc_key: str) -> Document:
    """Resolve document by key. Raises Document.DoesNotExist if not found."""
    return Document.objects.get(key=doc_key)


def load_blacklist(file_path: str | None) -> set[str]:
    """
    Load a blacklist from a file: one object key per line (stripped, empty lines skipped).
    If file_path is None or file is missing, return empty set.
    """
    if not file_path:
        return set()
    path = Path(file_path)
    if not path.exists():
        return set()
    keys = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            key = line.strip()
            if key:
                keys.add(key)
    return keys


def _model_has_description(model) -> bool:
    """Return True if the model has a desc field (i.e. can be a crossref source)."""
    return any(f.name == "desc" for f in model._meta.get_fields())


def get_source_models_and_filters_for_document(doc, model_name: str | None = None):
    """
    Return a list of (model, filter_kwargs) for all api_v2 models that have
    HasDescription (desc field) and belong to the given document.

    doc: Document instance.
    model_name: If set, only include this model (e.g. 'Spell', 'Item').

    Each filter_kwargs is suitable for model.objects.filter(**filter_kwargs).
    """
    result = []
    for model in apps.get_models():
        if model._meta.app_label != "api_v2":
            continue
        if model.__name__ in SKIPPED_MODEL_NAMES:
            continue
        if not _model_has_description(model):
            continue
        if model_name is not None and model.__name__ != model_name:
            continue

        if model.__name__ in CHILD_CHILD_MODEL_NAMES:
            filter_kwargs = {"parent__parent__document": doc}
        elif model.__name__ in CHILD_MODEL_NAMES:
            filter_kwargs = {"parent__document": doc}
        else:
            filter_kwargs = {"document": doc}

        result.append((model, filter_kwargs))
    return result


def get_crossreferences_by_source_document(
    doc,
    *,
    source_model_name: str | None = None,
    source_blacklist: set[str] | None = None,
    reference_blacklist: set[str] | None = None,
):
    """
    Return a queryset of CrossReference rows whose source object is in the given
    document, optionally restricted by source model. Excludes rows whose
    source_object_key is in source_blacklist or reference_object_key is in
    reference_blacklist.
    """
    source_blacklist = source_blacklist or set()
    reference_blacklist = reference_blacklist or set()

    pairs = get_source_models_and_filters_for_document(doc, model_name=source_model_name)
    crossref_ids = []

    for model, filter_kwargs in pairs:
        ct = ContentType.objects.get_for_model(model)
        keys_in_scope = set(
            model.objects.filter(**filter_kwargs).values_list("pk", flat=True)
        )
        if not keys_in_scope:
            continue
        qs = CrossReference.objects.filter(
            source_content_type=ct,
            source_object_key__in=keys_in_scope,
        )
        if source_blacklist:
            qs = qs.exclude(source_object_key__in=source_blacklist)
        if reference_blacklist:
            qs = qs.exclude(reference_object_key__in=reference_blacklist)
        crossref_ids.extend(qs.values_list("pk", flat=True))

    if not crossref_ids:
        return CrossReference.objects.none()
    return CrossReference.objects.filter(pk__in=crossref_ids)


def get_all_crossreferences_for_document(doc):
    """Return queryset of all CrossReference rows whose source is in the given document."""
    return get_crossreferences_by_source_document(
        doc,
        source_model_name=None,
        source_blacklist=set(),
        reference_blacklist=set(),
    )


def _get_parent_keys_to_skip(obj) -> set[tuple[int, str]]:
    """
    For an object that may have a parent-like FK (e.g. parent, subclass_of),
    return a set of (content_type_id, parent_key) that should not be suggested as references.
    """
    result = set()
    model = type(obj)
    for field_name in PARENT_FIELD_NAMES:
        try:
            field = model._meta.get_field(field_name)
        except Exception:
            continue
        if not isinstance(field, ForeignKey):
            continue
        parent_id = getattr(obj, field.attname, None)
        if parent_id is None:
            continue
        parent_model = field.remote_field.model
        if isinstance(parent_model, str):
            if "." in parent_model:
                parent_model = apps.get_model(parent_model)
            else:
                parent_model = apps.get_model(model._meta.app_label, parent_model)
        parent_ct = ContentType.objects.get_for_model(parent_model)
        result.add((parent_ct.id, str(parent_id)))
    return result


def _match_in_forbidden_context(desc: str, match_start: int, match_end: int) -> bool:
    """
    Return True if the match at (match_start, match_end) is inside bold, a header line,
    or a table header line. Such matches are excluded (don't link).
    """
    # Bold: **...** or __...__
    for bold_pattern in (r"\*\*(.*?)\*\*", r"__(.*?)__"):
        for m in re.finditer(bold_pattern, desc):
            if m.start() <= match_start and match_end <= m.end():
                return True

    # Which line contains the match?
    lines = desc.split("\n")
    char_pos = 0
    line_idx = 0
    for idx, line in enumerate(lines):
        if char_pos <= match_start < char_pos + len(line):
            line_idx = idx
            break
        char_pos += len(line) + 1

    line = lines[line_idx]

    # Header: line starts with # (optional leading whitespace)
    if line.lstrip().startswith("#"):
        return True

    # Table header: this line has | and is the first line of a run of table lines
    if "|" in line:
        block_start = line_idx
        while block_start > 0 and "|" in lines[block_start - 1]:
            block_start -= 1
        if block_start == line_idx:
            return True

    return False


def identify_crossreferences_from_text(
    doc,
    source_blacklist: set[str] | None = None,
    reference_blacklist: set[str] | None = None,
):
    """
    Find suggested (source, reference) links by matching reference names in source descriptions.
    Returns (by_source, by_reference):
    - by_source: dict key_src -> (src_url, list of (ref_url, anchor))
    - by_reference: dict key_ref -> (ref_url, list of (src_url, anchor))
    """
    source_blacklist = source_blacklist or set()
    reference_blacklist = reference_blacklist or set()
    # Precompile word-boundary regex per ref (avoids recompiling for every source).
    ref_candidates = []
    for ref_ct, ref_key, ref_name in get_reference_candidates_for_document(doc):
        if ref_key in reference_blacklist or not ref_name or len(ref_name) < 2:
            continue
        if ref_name in EXCLUDED_REFERENCE_NAMES:
            continue
        if any(sub in ref_key for sub in EXCLUDED_KEY_SUBSTRINGS):
            continue
        pattern = re.compile(
            r"\b" + re.escape(ref_name) + r"\b",
            re.IGNORECASE,
        )
        ref_candidates.append((ref_ct, ref_key, ref_name, pattern))

    by_source = {}
    by_reference = {}

    for model, filter_kwargs in get_source_models_and_filters_for_document(doc):
        for obj in (
            model.objects.filter(**filter_kwargs)
            .exclude(desc__isnull=True)
            .exclude(desc="")
        ):
            pk_str = str(obj.pk)
            if pk_str in source_blacklist:
                continue
            if any(sub in pk_str for sub in EXCLUDED_KEY_SUBSTRINGS):
                continue
            desc = obj.desc or ""
            desc_len = len(desc)
            src_ct = ContentType.objects.get_for_model(model)
            src_url = build_object_url(src_ct, pk_str)
            key_src = (src_ct.id, pk_str)
            seen_refs = set()
            parents_to_skip = _get_parent_keys_to_skip(obj)

            for ref_ct, ref_key, ref_name, pattern in ref_candidates:
                # Don't allow an object to reference itself
                if (ref_ct.id, ref_key) == (src_ct.id, pk_str):
                    continue
                # Don't allow an object to reference its parent (e.g. class feature -> class, trait -> species)
                if (ref_ct.id, ref_key) in parents_to_skip:
                    continue
                if len(ref_name) > desc_len:
                    continue
                # Require at least one match that is not in bold/header/table-header
                found_allowed = False
                for m in pattern.finditer(desc):
                    if not _match_in_forbidden_context(desc, m.start(), m.end()):
                        found_allowed = True
                        break
                if not found_allowed:
                    continue
                key_ref = (ref_ct.id, ref_key)
                if (key_src, key_ref) in seen_refs:
                    continue
                seen_refs.add((key_src, key_ref))
                ref_url = build_object_url(ref_ct, ref_key)

                if key_src not in by_source:
                    by_source[key_src] = (src_url, [])
                by_source[key_src][1].append((ref_url, ref_name))

                if key_ref not in by_reference:
                    by_reference[key_ref] = (ref_url, [])
                by_reference[key_ref][1].append((src_url, ref_name))

    return by_source, by_reference


def build_crossreference_reports(
    doc,
    source_blacklist: set[str] | None = None,
    reference_blacklist: set[str] | None = None,
    use_text_matching: bool = True,
):
    """
    Build two report structures for the document.

    When use_text_matching=True (default for report files): uses text-match identification
    (reference names in source descriptions). Each entry includes "matches" with anchor.
    When use_text_matching=False: uses existing CrossReference rows from the DB.

    Returns (sources_report, references_report).
    """
    source_blacklist = source_blacklist or set()
    reference_blacklist = reference_blacklist or set()

    if use_text_matching:
        by_source, by_reference = identify_crossreferences_from_text(
            doc,
            source_blacklist=source_blacklist,
            reference_blacklist=reference_blacklist,
        )
        # Build sources report: every source candidate with suggested links and matches
        candidate_entries = []
        for model, filter_kwargs in get_source_models_and_filters_for_document(doc):
            for obj in (
                model.objects.filter(**filter_kwargs)
                .exclude(desc__isnull=True)
                .exclude(desc="")
            ):
                pk_str = str(obj.pk)
                if pk_str in source_blacklist:
                    continue
                ct = ContentType.objects.get_for_model(model)
                url = build_object_url(ct, pk_str)
                key_src = (ct.id, pk_str)
                refs_with_anchor = by_source.get(key_src, (url, []))[1]
                ref_urls = sorted({r[0] for r in refs_with_anchor})
                matches = [{"url": r[0], "anchor": r[1]} for r in refs_with_anchor]
                candidate_entries.append((url, ref_urls, matches))

        sources_report = [
            {"url": url, "crossreference_to": ref_urls, "matches": matches}
            for url, ref_urls, matches in candidate_entries
        ]
        sources_report.sort(key=lambda x: len(x["crossreference_to"]), reverse=True)

        references_report = [
            {
                "url": url,
                "crossreference_from": sorted({m[0] for m in src_list}),
                "matches": [{"url": m[0], "anchor": m[1]} for m in src_list],
            }
            for _key, (url, src_list) in by_reference.items()
        ]
        references_report.sort(
            key=lambda x: len(x["crossreference_from"]), reverse=True
        )
        return sources_report, references_report

    # DB-based: existing CrossReference rows only
    qs = get_all_crossreferences_for_document(doc)
    by_source = {}
    by_reference = {}

    for cr in qs.select_related("source_content_type", "reference_content_type"):
        src_url = build_object_url(cr.source_content_type, cr.source_object_key)
        ref_url = build_object_url(cr.reference_content_type, cr.reference_object_key)
        key_src = (cr.source_content_type_id, cr.source_object_key)
        key_ref = (cr.reference_content_type_id, cr.reference_object_key)
        if key_src not in by_source:
            by_source[key_src] = (src_url, set())
        by_source[key_src][1].add(ref_url)
        if key_ref not in by_reference:
            by_reference[key_ref] = (ref_url, set())
        by_reference[key_ref][1].add(src_url)

    candidate_entries = []
    for model, filter_kwargs in get_source_models_and_filters_for_document(doc):
        for obj in (
            model.objects.filter(**filter_kwargs)
            .exclude(desc__isnull=True)
            .exclude(desc="")
        ):
            pk_str = str(obj.pk)
            if pk_str in source_blacklist:
                continue
            ct = ContentType.objects.get_for_model(model)
            url = build_object_url(ct, pk_str)
            key_src = (ct.id, pk_str)
            ref_urls = by_source[key_src][1] if key_src in by_source else set()
            candidate_entries.append((url, ref_urls))

    sources_report = [
        {"url": url, "crossreference_to": sorted(ref_urls)}
        for url, ref_urls in candidate_entries
    ]
    sources_report.sort(key=lambda x: len(x["crossreference_to"]), reverse=True)

    references_report = [
        {"url": url, "crossreference_from": sorted(src_urls)}
        for _key, (url, src_urls) in by_reference.items()
    ]
    references_report.sort(
        key=lambda x: len(x["crossreference_from"]), reverse=True
    )
    return sources_report, references_report


def write_crossreference_report_files(
    doc,
    sources_path: str,
    references_path: str,
    source_blacklist: set[str] | None = None,
    reference_blacklist: set[str] | None = None,
):
    """Build both reports, write them as JSON to the given paths, and return (sources_report, references_report)."""
    sources_report, references_report = build_crossreference_reports(
        doc,
        source_blacklist=source_blacklist,
        reference_blacklist=reference_blacklist,
    )
    with open(sources_path, "w", encoding="utf-8") as f:
        json.dump(sources_report, f, indent=2)
    with open(references_path, "w", encoding="utf-8") as f:
        json.dump(references_report, f, indent=2)
    return sources_report, references_report
