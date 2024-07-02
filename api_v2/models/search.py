""" The Search Result object model"""
from django.db import models


class SearchResult(models.Model):
    """ The Search Result object model. This model is used to build the 
    originally loaded table which is then separately used to build the search
    index. That table is then deleted.
    This process is defined in /api_v2/management/commands/buildindex.py"""

    document_pk = models.CharField(max_length=255)
    object_pk = models.CharField(max_length=255)
    object_name = models.CharField(max_length=100)
    object_model = models.CharField(max_length=255)
    schema_version = models.CharField(max_length=100)

    rank = models.DecimalField(max_digits=10, decimal_places=4, null=True, default=None)
    text = models.TextField(null=True, default=None)
    highlighted = models.TextField(null=True, default=None)
