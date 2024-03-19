from django.db import models

# Custom Model Fields
## https://docs.djangoproject.com/en/3.2/howto/custom-model-fields/
## Custom Manager
## https://github.com/shangxiao/django-virtual-table-model-demo/blob/master/foo/models.py

## Most fields are standard types.
## "text" field is going to be a custom model field.


## https://charlesleifer.com/blog/using-sqlite-full-text-search-with-python/

# Mapped to FTS5 columns
## https://sqlite.org/fts5.html

# V1 Fields:
# text name route slug document_slug document_title
# Also model specific fields.

# TOTAL:
'''        fields = ['name',
            'text',
            'route',
            'slug',
            'level',
            'school',
            'dnd_class',
            'ritual',
            'armor_class',
            'hit_points',
            'hit_dice',
            'challenge_rating',
            'strength',
            'dexterity',
            'constitution',
            'intelligence',
            'wisdom',
            'charisma',
            'rarity',
            'type',
            'source',
            'requires_attunement',
            'document_slug',
            'document_title',
            'parent',
        ]'''


## Implementation Plan

# Create a v1 index (distinct from v2 data). - This is a management command that is intended to be run AFTER data is loaded.
# It will include: text, route, slug, document_slug
# Fill it with some basic data (how about feats)

# Create a virtual table class for the index. - implement as_sql
# Create a manager for the index. Implement get_queryset
# Create a model.- class Meta managed=False

# Test the ability to get data from that manager 
#Search terms:
#"deflector"
#"proficient"
#"advantage"
#"heralds"

class SearchIndexVirtualTable:
    table_name = 'searchindex'
    table_alias = 'searchindex'
    join_type = None
    parent_alias = None
    filtered_relation = None

    def as_sql(self, compiler, connection):
        #TODO: Test out filters here
        return "searchindex WHERE text MATCH 'Amulet'", []


class SearchResultManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        qs.query.join(SearchIndexVirtualTable())
        return qs


class SearchResult(models.Model):
    # TODO Add finalized columns here.
    objects = SearchResultManager()

    text = models.TextField()
    route = models.TextField()
    slug = models.CharField(max_length=255, unique=True)
    document_slug = models.CharField(max_length=255, unique=True)


    class Meta:
        managed=False