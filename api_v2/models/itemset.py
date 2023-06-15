"""A set of items."""

from django.db import models
from .abstracts import HasDescription, HasName, FromDocument
from .item import Item


class ItemSet(HasName, HasDescription, FromDocument):
    """A set of items to be referenced."""

    items = models.ManyToManyField(Item, through='ItemQuantity')


class ItemQuantity(models.Model):
    """The quantity of the item to be referenced."""

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    itemset = models.ForeignKey(ItemSet, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
