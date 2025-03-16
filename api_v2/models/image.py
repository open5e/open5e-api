"""The model for an image with metadata."""


from django.db import models
from .abstracts import HasName
from .document import FromDocument
from .enums import IMAGE_TYPES

class Image(HasName, FromDocument):
    """This is the model related to image metadata."""

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
