"""
Build v2 API URLs for cross-reference targets using the same URLconf as the API.

Uses the api_v2 router as source of truth for top-level resources, plus a small
fallback map for nested reference models that do not have their own viewset.
"""

from django.urls import reverse


# Nested reference models (no own viewset) -> basename for their resource URL.
# Used only when the reference's content type is not in the router-derived map.
REFERENCE_MODEL_TO_BASENAME = {
    "AbilityDescription": "abilities",
    "SkillDescription": "skills",
    "SpeciesTrait": "species",
    "FeatBenefit": "feats",
    "BackgroundBenefit": "backgrounds",
    "CreatureTrait": "creatures",
    "CreatureAction": "creatures",
    "CreatureTypeDescription": "creaturetypes",
    "DamageTypeDescription": "damagetypes",
    "AlignmentDescription": "alignments",
    "ConditionDescription": "conditions",
    "SpellCastingOption": "spells",
    "ClassFeature": "classes",
    "ClassFeatureItem": "classes",
}


def _get_model_to_basename():
    """Build model class -> basename map from the api_v2 router (lazy to avoid circular imports)."""
    from api_v2.urls import router

    result = {}
    for _prefix, viewset, basename in router.registry:
        queryset = getattr(viewset, "queryset", None)
        if queryset is not None:
            model = getattr(queryset, "model", None)
            if model is not None:
                result[model] = basename
    return result


def _get_basename_for_object(model, object_key):
    """
    Return the API basename for this model and primary key.

    Item uses two endpoints: magicitems for magic items (rarity set), items otherwise.
    Other models use the router/REFERENCE_MODEL_TO_BASENAME.
    """
    if model.__name__ == "Item":
        try:
            obj = model.objects.get(pk=object_key)
            return "magicitems" if obj.is_magic_item else "items"
        except model.DoesNotExist:
            return "items"
    model_to_basename = _get_model_to_basename()
    basename = model_to_basename.get(model)
    if basename is None:
        basename = REFERENCE_MODEL_TO_BASENAME.get(model.__name__)
    return basename


def _build_object_url(content_type, object_key, request=None):
    """Build v2 API URL for the given content type and key. Returns None if no basename."""
    model = content_type.model_class() if content_type else None
    if model is None:
        return None
    basename = _get_basename_for_object(model, object_key)
    if basename is None:
        return None
    view_name = f"{basename}-detail"
    path = reverse(view_name, kwargs={"pk": object_key})
    if request is not None:
        return request.build_absolute_uri(path)
    return path


def get_reference_url(crossreference, request=None):
    """
    Return the v2 API URL for the object pointed to by this CrossReference.

    Uses Django's reverse() with the api_v2 router (model -> basename from
    router.registry) and REFERENCE_MODEL_TO_BASENAME for nested reference
    models. For Item, uses magicitems vs items by is_magic_item. If request
    is provided, returns an absolute URI.
    """
    return _build_object_url(
        crossreference.reference_content_type,
        crossreference.reference_object_key,
        request,
    )


def get_source_url(crossreference, request=None):
    """
    Return the v2 API URL for the source object of this CrossReference.

    The source is the object that contains the description and the link.
    Same basename logic as get_reference_url (including Item -> magicitems/items).
    If request is provided, returns an absolute URI. Returns None if no URL.
    """
    return _build_object_url(
        crossreference.source_content_type,
        crossreference.source_object_key,
        request,
    )
