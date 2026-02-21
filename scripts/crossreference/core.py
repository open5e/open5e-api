"""
Core cross-reference logic: matching, reports, blacklists, document scoping.

Used by find_candidates and delete_crossreferences scripts. Requires Django.
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

# Reference names that are ambiguous (common word vs named entity). When these appear
# lowercase in text we exclude the match unless context suggests the entity (e.g. spell).
AMBIGUOUS_REFERENCE_NAMES_NEEDING_CONTEXT = frozenset({
    "fly", "sleep", "light", "resistance",
})


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
# CHILD_*, CHILD_CHILD_*, and any model with "Description" in the name are excluded (see get_reference_models_and_filters_for_document).
REFERENCE_MODEL_NAMES = [
    "Spell",
    "Item",
    "Condition",
    "Feat",
    "Rule",
    "RuleSet",
    "WeaponProperty",
    "Language",
    "Environment",
    "Background",
    "Species",
    "CharacterClass",
    "ClassFeature",
    "DamageType",
    "Alignment",
    "CreatureType",
    "Ability",
    "Skill",
]


def _model_has_name(model) -> bool:
    """Return True if the model has a name field."""
    return any(f.name == "name" for f in model._meta.get_fields())


def get_reference_models_and_filters_for_document(doc):
    """
    Return (model, filter_kwargs) for all api_v2 models that are in REFERENCE_MODEL_NAMES,
    have a name field, and belong to the given document.
    Child and grandchild models (CHILD_*) and any model whose name includes "Description" are excluded as references.
    """
    result = []
    for model in apps.get_models():
        if model._meta.app_label != "api_v2":
            continue
        if model.__name__ not in REFERENCE_MODEL_NAMES:
            continue
        if model.__name__ in CHILD_MODEL_NAMES or model.__name__ in CHILD_CHILD_MODEL_NAMES:
            continue
        if "Description" in model.__name__:
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
    Relative paths are resolved against the project root (Django BASE_DIR) when the
    path as given does not exist, so blacklists load correctly regardless of cwd.
    """
    if not file_path:
        return set()
    path = Path(file_path)
    if not path.exists():
        # Resolve relative paths against project root so blacklists load regardless of cwd
        try:
            from django.conf import settings
            root = Path(settings.BASE_DIR)
            if not path.is_absolute():
                alt = root / path
                if alt.exists():
                    path = alt
                else:
                    return set()
            else:
                return set()
        except Exception:
            return set()
    keys = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            key = line.strip()
            if key:
                keys.add(key)
    return keys


def _model_has_description(model) -> bool:
    """Return True if the model has a desc field (i.e. can be a crossreference source)."""
    return any(f.name == "desc" for f in model._meta.get_fields())


def _is_crossreference_source(obj) -> bool:
    """Return True if this object should be treated as a crossreference source (API and scripts)."""
    return bool(
        getattr(obj, "is_crossreference_source", None)
        and callable(getattr(obj, "is_crossreference_source", None))
        and obj.is_crossreference_source()
    )


def get_source_models_and_filters_for_document(doc, model_name: str | None = None):
    """
    Return a list of (model, filter_kwargs) for all api_v2 models that have
    HasDescription (desc field) and belong to the given document.
    doc: Document instance.
    model_name: If set, only include this model (e.g. 'Spell', 'Item').

    Each filter_kwargs is suitable for model.objects.filter(**filter_kwargs).
    Callers must filter iterated objects by _is_crossreference_source(obj).
    """
    result = []
    for model in apps.get_models():
        if model._meta.app_label != "api_v2":
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
            # Only include models that belong to a document (have document FK).
            if not any(f.name == "document" for f in model._meta.get_fields()):
                continue
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
    crossreference_ids = []

    for model, filter_kwargs in pairs:
        ct = ContentType.objects.get_for_model(model)
        qs = model.objects.filter(**filter_kwargs)
        keys_in_scope = set()
        for obj in qs.iterator(chunk_size=500):
            if _is_crossreference_source(obj):
                keys_in_scope.add(str(obj.pk))
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
        crossreference_ids.extend(qs.values_list("pk", flat=True))

    if not crossreference_ids:
        return CrossReference.objects.none()
    return CrossReference.objects.filter(pk__in=crossreference_ids)


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


def _match_likely_common_word(ref_name: str, matched_text: str) -> bool:
    """
    Return True if this match is likely the common word rather than the named entity.
    Only applies to ambiguous names (see AMBIGUOUS_REFERENCE_NAMES_NEEDING_CONTEXT):
    when such a reference name is capitalized (e.g. "Fly", "Resistance") but the
    occurrence in the source is all lowercase ("fly", "resistance"), treat it as
    the common word and exclude it to reduce false positives.
    """
    if not ref_name or not matched_text:
        return False
    if ref_name.lower() not in AMBIGUOUS_REFERENCE_NAMES_NEEDING_CONTEXT:
        return False
    if not any(c.isupper() for c in ref_name):
        return False
    return matched_text.islower()


# Lighting-condition phrases: "Light" here is not the spell or weapon property.
_LIGHTING_PHRASES = ("bright light", "dim light")


def _match_is_lighting_condition(
    desc: str, match_start: int, match_end: int, ref_name: str
) -> bool:
    """
    Return True when the match is "Light" as part of "Bright Light" or "Dim Light"
    (lighting conditions), not the Light spell or Light weapon property.
    """
    if not ref_name or ref_name.lower() != "light":
        return False
    # Need enough context before "Light" to see "Bright " or "Dim "
    start = max(0, match_start - 7)
    window = desc[start:match_end].lower()
    return any(phrase in window for phrase in _LIGHTING_PHRASES)


# Context window (chars before/after match) for spell vs weapon-property disambiguation.
_CONTEXT_WINDOW = 120
# Phrases/words that suggest the mention is the spell, not the weapon property.
_CONTEXT_SUGGESTS_SPELL = frozenset({
    "cast", "spell", "cantrip", "concentration", "prepared", "slot", "slots",
    "evocation", "spellcasting", "cast this spell", "spell's", "the spell ",
})
# Phrases/words that suggest the mention is the weapon property, not the spell.
_CONTEXT_SUGGESTS_WEAPON_PROPERTY = frozenset({
    "light weapon", "weapon property", "weapon has", "weapons with",
    "property.", "properties", "melee weapon", "ranged weapon",
    "has the light", "the light property", "light property",
})
# Phrases/words that suggest "Light" is armor/equipment (e.g. "Light and Medium armor"), not the spell.
_CONTEXT_SUGGESTS_ARMOR_OR_EQUIPMENT = frozenset({
    "light and medium", " and medium armor", "armor training",
    "light armor", "medium armor", "heavy armor",
})
# Phrases/words that suggest "Shield" is the physical item, not the spell.
_CONTEXT_SUGGESTS_SHIELD_ITEM = frozenset({
    "wield a shield", "wielding a shield", "don shield", "donning a shield",
    "armor and shield", "shield's ac", "shield ac", "shield (armor)",
    "carry a shield", "holding a shield", "equip a shield", "shield and armor",
    "shields and", "or shield", "and shields", "proficiency with shields",
})
# Phrases that suggest "Light" or "Heavy" refer to the crossbow items, not the spell or weapon property.
_CONTEXT_SUGGESTS_CROSSBOW_ITEM = frozenset({
    "light crossbow", "heavy crossbow", "hand crossbow",
})
# "Acid" here is damage type, not the Acid item (vial).
_CONTEXT_SUGGESTS_ACID_DAMAGE_TYPE = frozenset({
    " acid damage", "acid damage", "resistance to acid", "immunity to acid",
    "vulnerability to acid", "acid resistance", "acid immunity",
})
# "Chain" here is part of "Chain Lightning" (spell), not the Chain item.
_CONTEXT_SUGGESTS_CHAIN_LIGHTNING_SPELL = frozenset({
    "chain lightning",
})


def _match_context_mismatch(
    desc: str,
    match_start: int,
    match_end: int,
    ref_ct: ContentType,
    ref_name: str = "",
) -> bool:
    """
    Return True when the surrounding context suggests a different meaning than
    this reference type (e.g. "Light" spell vs Light weapon property, or Shield
    spell vs Shield item). When True, the match should be skipped for this reference.
    """
    model_cls = ref_ct.model_class()
    if model_cls is None:
        return False
    model_name = model_cls.__name__
    start = max(0, match_start - _CONTEXT_WINDOW)
    end = min(len(desc), match_end + _CONTEXT_WINDOW)
    context = desc[start:end].lower()
    ref_lower = (ref_name or "").lower()
    if model_name == "Spell":
        if (
            any(phrase in context for phrase in _CONTEXT_SUGGESTS_WEAPON_PROPERTY)
            or any(phrase in context for phrase in _CONTEXT_SUGGESTS_ARMOR_OR_EQUIPMENT)
        ):
            return True
        if ref_lower == "shield" and any(
            phrase in context for phrase in _CONTEXT_SUGGESTS_SHIELD_ITEM
        ):
            return True
        if ref_lower == "light" and any(
            phrase in context for phrase in _CONTEXT_SUGGESTS_CROSSBOW_ITEM
        ):
            return True
    if model_name == "WeaponProperty":
        if ref_lower == "light" and any(
            phrase in context for phrase in _CONTEXT_SUGGESTS_CROSSBOW_ITEM
        ):
            return True
        if ref_lower == "heavy" and any(
            phrase in context for phrase in _CONTEXT_SUGGESTS_CROSSBOW_ITEM
        ):
            return True
        return any(phrase in context for phrase in _CONTEXT_SUGGESTS_SPELL)
    if model_name == "Item" and ref_lower == "shield":
        return any(phrase in context for phrase in _CONTEXT_SUGGESTS_SPELL)
    if model_name == "Item" and ref_lower == "acid":
        return any(phrase in context for phrase in _CONTEXT_SUGGESTS_ACID_DAMAGE_TYPE)
    if model_name == "Item" and ref_lower == "chain":
        return any(phrase in context for phrase in _CONTEXT_SUGGESTS_CHAIN_LIGHTNING_SPELL)
    return False


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
            if not _is_crossreference_source(obj):
                continue
            desc = obj.desc or ""
            desc_len = len(desc)
            src_ct = ContentType.objects.get_for_model(model)
            src_url = build_object_url(src_ct, pk_str)
            key_src = (src_ct.id, pk_str)
            seen_refs = set()
            seen_ref_names_per_source: dict[tuple[int, str], set[str]] = {}
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
                # Require at least one match that is not in bold/header/table-header,
                # not likely the common word (e.g. "fly" vs "Fly" the spell), and
                # not context-mismatched (e.g. "Light" weapon property vs Light spell)
                found_allowed = False
                for m in pattern.finditer(desc):
                    if _match_in_forbidden_context(desc, m.start(), m.end()):
                        continue
                    if _match_likely_common_word(ref_name, desc[m.start() : m.end()]):
                        continue
                    if _match_is_lighting_condition(desc, m.start(), m.end(), ref_name):
                        continue
                    if _match_context_mismatch(desc, m.start(), m.end(), ref_ct, ref_name):
                        continue
                    found_allowed = True
                    break
                if not found_allowed:
                    continue
                key_ref = (ref_ct.id, ref_key)
                if (key_src, key_ref) in seen_refs:
                    continue
                # Only one link per distinct reference name per source (e.g. one "Proficiency" from acid)
                ref_name_lower = ref_name.lower()
                if key_src not in seen_ref_names_per_source:
                    seen_ref_names_per_source[key_src] = set()
                if ref_name_lower in seen_ref_names_per_source[key_src]:
                    continue
                seen_ref_names_per_source[key_src].add(ref_name_lower)
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
                if not _is_crossreference_source(obj):
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
            if not _is_crossreference_source(obj):
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
