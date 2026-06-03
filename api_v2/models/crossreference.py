"""The model for a CrossReference."""

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify

from .document import Document
from api_v2.url_utils import get_reference_url, get_source_url


def _crossreference_key_for(source_object_key, anchor, reference_object_key):
    """Return deterministic key for a CrossReference. Used by model and migration."""
    slug = slugify(anchor)[:80] if anchor else ""
    return f"{source_object_key}_{slug}_{reference_object_key}"


class CrossReference(models.Model):
    """
    A cross reference from a span of text in one object's description to another object.

    The source is the object that contains the description. The reference is the object 
    being linked to. document is always the source object's document.
    """

    key = models.CharField(
        primary_key=True,
        max_length=300,
        help_text="Deterministic key: source_object_key_slugified_anchor_reference_object_key.",
    )

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        help_text="Document the source object belongs to (denormalized for filtering).",
    )

    # Source: the object that has the description
    source_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="crossreferences_as_source",
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
        related_name="crossreferences_as_reference",
        help_text="The model of the object this CrossReference points to.",
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

    @staticmethod
    def key_for(source_object_key, anchor, reference_object_key):
        """Return the deterministic primary key for this (source, anchor, reference)."""
        return _crossreference_key_for(source_object_key, anchor, reference_object_key)

    def reference_api_url(self, request=None):
        """Return the v2 API URL for the object this CrossReference points to (the reference)."""
        return get_reference_url(self, request) or ""

    def source_api_url(self, request=None):
        """Return the v2 API URL for the object that contains this link (the source)."""
        return get_source_url(self, request) or ""

    class Meta:
        verbose_name_plural = "crossreferences"
        ordering = ["source_content_type", "source_object_key", "key"]
        indexes = [
            models.Index(fields=["document"]),
            models.Index(fields=["source_content_type", "source_object_key"]),
            models.Index(fields=["reference_content_type", "reference_object_key"]),
        ]
