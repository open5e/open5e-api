

from django.db import models
from api.models import GameContent

class ArmorType(GameContent):

    light = models.BooleanField(
        null=False,
        default=False,
        help_text='If the armor is light.')

    medium = models.BooleanField(
        null=False,
        default=False,
        help_text='If the armor is medium.')

    heavy = models.BooleanField(
        null=False,
        default=False,
        help_text='If the armor is heavy.')

    stealth_disadvantage = models.BooleanField(
        null=False,
        default=False,
        help_text='If the armor results in disadvantage on stealth checks.')

    strength = models.IntegerField(
        null=True,
        help_text='Strength score required to wear the armor without penalty.'
    )

    def strength_display(self):
        return strength_display

    ac_base = models.IntegerField(
        null=False,
        help_text='Integer representing the flat armor class without modifiers.'
    )

    ac_add_dexmod = models.BooleanField(
        null=False,
        default=False,
        help_text='If the final armor class takes the dexterity modifier into account.')

    ac_cap_dexmod = models.IntegerField(
        null=True,
        help_text='Integer representing the maximum of the added dexterity modifier.'
    )

    def ac_display(self):
        return ac