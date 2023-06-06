

from django.db import models
from api.models import GameContent

class WeaponType(GameContent):

#"range":{"normal":30,"long":120}

#"damage":{"dice":"","type":""}

    def properties_display(self):
        # Append in order
        special
        finesse
        ammunition / range
        light
        heavy
        thrown
        loading
        two-handed
        versatile
        reach
        
        # capitalize first letter
        
        # return a dash if nothing

        return properties_list

    light = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is light.')

    finesse = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is finesse.')

    thrown = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is thrown.')

    two-handed = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is two-handed.')

    versatile = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is versatile.')

    ammunition = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon requires ammunition.')

    loading = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon requires loading.')

    heavy = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is heavy.')

    light = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is light.')

    reach = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon grants reach.')

    lance = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is a lance.')

    net = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is a net.')

    simple = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon category is simple.')

    martial = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is category is martial.')

    silvered = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon has been silvered.')

    improvised = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is improvised.')
