"""
Search indexes for Whoosh text search.
Vector search is handled separately via spaCy word embeddings.
"""
from haystack import indexes


class BaseSearchIndex(indexes.SearchIndex):
    """Base search index with common fields for text search."""
    
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name')
    description = indexes.CharField()
    object_type = indexes.CharField()
    document_name = indexes.CharField()
    schema_version = indexes.CharField()
    
    def prepare_description(self, obj):
        """Prepare description field from various sources."""
        if hasattr(obj, 'desc') and obj.desc:
            return obj.desc
        elif hasattr(obj, 'description') and obj.description:
            return obj.description
        return ""
    
    def prepare_object_type(self, obj):
        """Get the object type name."""
        return obj.__class__.__name__
    
    def prepare_document_name(self, obj):
        """Get document name."""
        try:
            if hasattr(obj, 'document') and obj.document:
                return obj.document.display_name_or_name
        except Exception:
            pass
        return "Unknown"
    
    def prepare_schema_version(self, obj):
        """Get schema version."""
        try:
            if hasattr(obj, 'document') and obj.document:
                return getattr(obj.document, 'schema_version', 'v2') or 'v2'
        except Exception:
            pass
        return 'v2'


class SpellIndex(BaseSearchIndex, indexes.Indexable):
    """Search index for spells."""
    
    # Spell-specific fields
    level = indexes.CharField()
    school = indexes.CharField()
    casting_time = indexes.CharField()
    spell_range = indexes.CharField()
    components = indexes.CharField()
    duration = indexes.CharField()
    classes = indexes.MultiValueField()
    
    def get_model(self):
        from api_v2.models import Spell
        return Spell
    
    def prepare_level(self, obj):
        return str(obj.level) if obj.level is not None else "0"
    
    def prepare_school(self, obj):
        return obj.school.name if obj.school else ""
    
    def prepare_casting_time(self, obj):
        return obj.casting_time or ""
    
    def prepare_spell_range(self, obj):
        return obj.range_text or ""
    
    def prepare_components(self, obj):
        components = []
        if hasattr(obj, 'verbal') and obj.verbal:
            components.append('V')
        if hasattr(obj, 'somatic') and obj.somatic:
            components.append('S')
        if hasattr(obj, 'material') and obj.material:
            components.append('M')
        return ', '.join(components)
    
    def prepare_duration(self, obj):
        return obj.duration or ""
    
    def prepare_classes(self, obj):
        # Use the many-to-many relationship
        return [cls.name for cls in obj.classes.all()]


class CreatureIndex(BaseSearchIndex, indexes.Indexable):
    """Search index for creatures."""
    
    # Creature-specific fields
    size = indexes.CharField()
    creature_type = indexes.CharField()
    challenge_rating = indexes.CharField()
    armor_class = indexes.CharField()
    hit_points = indexes.CharField()
    
    def get_model(self):
        from api_v2.models import Creature
        return Creature
    
    def prepare_size(self, obj):
        return obj.size.name if obj.size else ""
    
    def prepare_creature_type(self, obj):
        return obj.type.name if obj.type else ""
    
    def prepare_challenge_rating(self, obj):
        return obj.challenge_rating_text or ""
    
    def prepare_armor_class(self, obj):
        return str(obj.armor_class) if obj.armor_class else ""
    
    def prepare_hit_points(self, obj):
        return str(obj.hit_points) if obj.hit_points else ""


class ItemIndex(BaseSearchIndex, indexes.Indexable):
    """Search index for items."""
    
    # Item-specific fields
    item_type = indexes.CharField()
    rarity = indexes.CharField()
    requires_attunement = indexes.BooleanField()
    
    def get_model(self):
        from api_v2.models import Item
        return Item
    
    def prepare_item_type(self, obj):
        return obj.category.name if obj.category else ""
    
    def prepare_rarity(self, obj):
        return obj.rarity.name if obj.rarity else ""
    
    def prepare_requires_attunement(self, obj):
        return obj.requires_attunement or False


class BackgroundIndex(BaseSearchIndex, indexes.Indexable):
    """Search index for backgrounds."""
    
    def get_model(self):
        from api_v2.models import Background
        return Background


class ClassIndex(BaseSearchIndex, indexes.Indexable):
    """Search index for classes."""
    
    # Class-specific fields
    hit_die = indexes.CharField()
    
    def get_model(self):
        from api_v2.models import CharacterClass
        return CharacterClass
    
    def prepare_hit_die(self, obj):
        return str(obj.hit_dice) if hasattr(obj, 'hit_dice') and obj.hit_dice else ""


class SpeciesIndex(BaseSearchIndex, indexes.Indexable):
    """Search index for species (formerly races)."""
    
    def get_model(self):
        from api_v2.models import Species
        return Species


class FeatIndex(BaseSearchIndex, indexes.Indexable):
    """Search index for feats."""
    
    def get_model(self):
        from api_v2.models import Feat
        return Feat 