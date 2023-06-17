from django.db import models
from django.urls import reverse

from .abstracts import HasName, HasDescription


class Document(HasName, HasDescription):

    key = models.CharField(
        primary_key=True,
        max_length=100,
        help_text="Unique key for the Document."
    )

    license = models.ForeignKey(
        "License",
        on_delete=models.CASCADE,
        help_text="License that the content was released under.")

    organization = models.ForeignKey(
        "Organization",
        on_delete=models.CASCADE,
        help_text="Organization which has written the game content document.")

    author = models.TextField(
        help_text='Author or authors.')

    published_at = models.DateTimeField(
        help_text="Date of publication, or null if unknown."
    )

    permalink = models.URLField(
        help_text="Link to the document."
    )


class License(HasName, HasDescription):
    key = models.CharField(
        primary_key=True,
        max_length=100,
        help_text="Unique key for the License."
    )
    pass


class Organization(HasName):
    key = models.CharField(
        primary_key=True,
        max_length=100,
        help_text="Unique key for the Organization."
    )
    pass


class FromDocument(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)

    key = models.CharField(
        primary_key=True,
        max_length=100,
        help_text="Unique key for the Item.")

    def get_absolute_url(self):
        return reverse(self.__name__, kwargs={"pk": self.pk})

    class Meta:
        abstract = True