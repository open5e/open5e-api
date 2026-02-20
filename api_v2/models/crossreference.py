"""The model for a Crossreference."""

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from .document import Document
from api_v2.url_utils import get_reference_url, get_source_url


class CrossReference(models.Model):
    """
    A cross reference from a span of text in one object's description to another object.

    The source is the object that contains the description. The reference is the object 
    being linked to. document is always the source object's document.
    """

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        help_text="Document the source object belongs to (denormalized for filtering).",
    )

    # Source: the object that with the description
    source_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="Crossreferences_as_source",
        help_text="The model of the object that contains the description.",
    )
    source_object_key = models.CharField(
        max_length=100,
        help_text="Primary key of the source object (e.g. item key, spell key).",
    )
    source = GenericForeignKey("source_content_type", "source_object_key")

    # reference: the object being linked to
    reference_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="Crossreferences_as_reference",
        help_text="The model of the object this Crossreference points to.",
    )
    reference_object_key = models.CharField(
        max_length=100,
        help_text="Primary key of the reference object.",
    )
    reference = GenericForeignKey("reference_content_type", "reference_object_key")

    anchor = models.CharField(
        max_length=100,
        help_text="The text in the source's description to highlight and link to the reference.",
    )

    def reference_api_url(self, request=None):
        """Return the v2 API URL for the object this CrossReference points to (the reference)."""
        return get_reference_url(self, request) or ""

    def source_api_url(self, request=None):
        """Return the v2 API URL for the object that contains this link (the source)."""
        return get_source_url(self, request) or ""

    class Meta:
        verbose_name_plural = "crossreferences"
        ordering = ["source_content_type", "source_object_key", "id"]
        indexes = [
            models.Index(fields=["document"]),
            models.Index(fields=["source_content_type", "source_object_key"]),
            models.Index(fields=["reference_content_type", "reference_object_key"]),
        ]
