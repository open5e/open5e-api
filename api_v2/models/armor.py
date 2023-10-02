"""The model for a type of armor."""


from django.db import models
from .abstracts import HasName
from .document import FromDocument


class Armor(HasName, FromDocument):
    """
    This is the model for an armor.

    This does not represent the armor set itself, because that would be an
    item. Only the unique attributes of a type of armor are here. An item
    that is armor would link to this model instance.
    """

    grants_stealth_disadvantage = models.BooleanField(
        null=False,
        default=False,
        help_text='If the armor results in disadvantage on stealth checks.')

    strength_score_required = models.IntegerField(
        blank=True,
        null=True,
        help_text='Strength score required to wear the armor without penalty.')

    ac_base = models.IntegerField(
        null=False,
        help_text='Integer representing the armor class without modifiers.')

    ac_add_dexmod = models.BooleanField(
        null=False,
        default=False,
        help_text='If the final armor class includes dexterity modifier.')

    ac_cap_dexmod = models.IntegerField(
        blank=True,
        null=True,
        help_text='Integer representing the dexterity modifier cap.')

    @property
    def ac_display(self):
        """Display text for armor class."""
        ac_string = str(self.ac_base)

        if self.ac_add_dexmod:
            ac_string += " + Dex modifier"

        if self.ac_cap_dexmod is not None:
            ac_string += " (max {})".format(self.ac_cap_dexmod)

        return ac_string

    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "armor"
