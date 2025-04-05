"""The model for an image with metadata."""


from django.db import models
from django.templatetags.static import static

from .abstracts import HasName
from .document import FromDocument
from .enums import IMAGE_TYPES

class Image(HasName, FromDocument):
    """This is the model related to image metadata."""

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

    def __str__(self):
        return (self.document.name + " - " + self.name)

    def file_url(self):
        return static(self.file_path)


class HasIcon(models.Model):
    """The model inherited for defining an icon for another object type."""
    icon = models.ForeignKey(Image, 
                            blank=True,
                            null=True,
                            on_delete=models.CASCADE)

    class Meta:
        abstract = True
