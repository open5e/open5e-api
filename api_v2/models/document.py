from django.db import models
from django.urls import reverse
from django.apps import apps


from .abstracts import HasName, HasDescription
from .abstracts import key_field, distance_unit_field

from api_v2 import models as v2_models

class Document(HasName, HasDescription):

    key = key_field()

    type = models.TextField(
        choices=[
            ("SOURCE", "Source"),
            ("MISC", "Miscellaneous")
        ],
        help_text='Whether this Document is a published data source, or general resources',
        default="SOURCE",
    )

    licenses = models.ManyToManyField(
        "License",
        help_text="Licenses that the content has been released under.")

    publisher = models.ForeignKey(
        "Publisher",
        on_delete=models.CASCADE,
        help_text="Publisher which has written the game content document.")

    gamesystem = models.ForeignKey(
        "GameSystem",
        on_delete=models.CASCADE,
        help_text="The document's game system that it was published for."
    )

    author = models.TextField(
        help_text='Author or authors.')

    display_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Display name for the document, used for presentation purposes.")

    publication_date = models.DateTimeField(
        help_text="Date of publication, or null if unknown."
    )

    permalink = models.URLField(
        help_text="Link to the document."
    )

    distance_unit = distance_unit_field()
    weight_unit = distance_unit_field()

    @property
    def display_name_or_name(self):
        """Returns display_name if it exists and is not blank, otherwise returns name."""
        if self.display_name and self.display_name.strip():
            return self.display_name
        return self.name

    @property
    def stats(self):
        stats = []
        for model in apps.get_models():
            # Filter out api_v1.
            if model._meta.app_label != 'api_v2': continue

            SKIPPED_MODEL_NAMES = [
                'Document',
                'GameSystem',
                'License',
                'Publisher',
                'SearchResult']
            if model.__name__ in SKIPPED_MODEL_NAMES: continue

            CHILD_MODEL_NAMES = [
                'SpeciesTrait',
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
            stats.append(stat)

        return stats

    def is_crossreference_source(self):
        return False


class License(HasName, HasDescription):
    key = models.CharField(
        primary_key=True,
        max_length=100,
        help_text="Unique key for the License."
    )

    def is_crossreference_source(self):
        return False


class Publisher(HasName):
    key = models.CharField(
        primary_key=True,
        max_length=100,
        help_text="Unique key for the publishing organization."
    )


class GameSystem(HasName, HasDescription):
    key = models.CharField(
        primary_key=True,
        max_length=100,
        help_text="Unique key for the gamesystem the document was published for."
    )

    content_prefix = models.CharField(
        max_length=10,
        blank=True,
        help_text="Short code prepended to content keys."
    )

    def is_crossreference_source(self):
        return False


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
        return

    class Meta:
        abstract = True