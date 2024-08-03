from django.db import models
from django.urls import reverse
from django.apps import apps


from .abstracts import HasName, HasDescription
from .abstracts import key_field, distance_unit_field

from api_v2 import models as v2_models

class Document(HasName, HasDescription):

    key = key_field()

    licenses = models.ManyToManyField(
        "License",
        help_text="Licenses that the content has been released under.")

    publisher = models.ForeignKey(
        "Publisher",
        on_delete=models.CASCADE,
        help_text="Publisher which has written the game content document.")

    ruleset = models.ForeignKey(
        "Ruleset",
        on_delete=models.CASCADE,
        help_text="The document's game system that it was published for."
    )

    author = models.TextField(
        help_text='Author or authors.')

    published_at = models.DateTimeField(
        help_text="Date of publication, or null if unknown."
    )

    permalink = models.URLField(
        help_text="Link to the document."
    )

    stats_expected = models.JSONField(
        null=True,
        blank=True,
        help_text="JSON representation of expected object counts."
    )

    distance_unit = distance_unit_field()

    @property
    def stats(self):
        stats = []
        for model in apps.get_models():
            # Filter out api_v1.
            if model._meta.app_label != 'api_v2': continue

            SKIPPED_MODEL_NAMES = [
                'Document',
                'Ruleset',
                'License',
                'Publisher',
                'SearchResult']
            if model.__name__ in SKIPPED_MODEL_NAMES: continue

            CHILD_MODEL_NAMES = [
                'RaceTrait',
                'ClassFeatureItem',
                'FeatBenefit', 
                'BackgroundBenefit',
                'CreatureAction',
                'CreatureActionAttack',
                'CreatureTrait',
                'SpellCastingOption',
                'ItemRarity']
            if model.__name__ in CHILD_MODEL_NAMES: continue

            actual_object_count = model.objects.filter(document=self.key).count()

            stat = {}
            stat['name'] = model.__name__.lower()
            stat['actual_count'] = actual_object_count
            try:
                stat['expected_count'] = self.stats_expected.get(model.__name__.lower())
            except:
                stat['expected_count'] = None
            stats.append(stat)

        return stats


class License(HasName, HasDescription):
    key = models.CharField(
        primary_key=True,
        max_length=100,
        help_text="Unique key for the License."
    )


class Publisher(HasName):
    key = models.CharField(
        primary_key=True,
        max_length=100,
        help_text="Unique key for the publishing organization."
    )


class Ruleset(HasName, HasDescription):
    key = models.CharField(
        primary_key=True,
        max_length=100,
        help_text="Unique key for the ruleset the document was published for."
    )

    content_prefix = models.CharField(
        max_length=10,
        blank=True,
        help_text="Short code prepended to content keys."
    )


class FromDocument(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)

    key = models.CharField(
        primary_key=True,
        max_length=100,
        help_text="Unique key for the Item.")

    def as_text(self):
        return "{}\n\n{}".format(self.name, self.desc)

    def get_absolute_url(self):
        return reverse(self.__name__, kwargs={"pk": self.pk})

    def search_result_extra_fields(self):
        return {
            "school":self.school.key,
        }

    class Meta:
        abstract = True