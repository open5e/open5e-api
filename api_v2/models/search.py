from django.db import models


class SearchResult(models.Model):
    """ The Search Result object model"""

    document_pk = models.CharField(max_length=255)
    object_pk = models.CharField(max_length=255)
    object_name = models.CharField(max_length=100)
    object_model = models.CharField(max_length=255)
    schema_version = models.CharField(max_length=100)

    rank = models.DecimalField(max_digits=10, decimal_places=4, null=True, default=None)
    text = models.TextField(null=True, default=None)
    highlighted = models.TextField(null=True, default=None)
