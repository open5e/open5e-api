from django import models
from api_v2.models import HasName, FromDocument
from api_v2.models.enums import IMAGE_TYPES

class Image(HasName, FromDocument):
    """This is the definition of an icon."""

    keywords = models.TextField(
        help_text='List of keywords, to be used by the search index.')

    file_path = models.TextField(
        help_text='Relative path of the file, to be used in static file resolution.'
    )

    type = models.CharField(
        blank=True,
        null=True,
        max_length=20,
        choices=IMAGE_TYPES,
        help_text='What type image this is, such as icon or illustration.'
    )


    def file_url(self):
        return "1"

    class Meta:
        abstract = True
