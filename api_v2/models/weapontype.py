"""The model for a type of weapon."""

from django.db import models
from django.core.validators import MinValueValidator

from .abstracts import HasName
from .document import FromDocument


class WeaponType(HasName, FromDocument):
    """
    This model represents types of weapons.

    This does not represent a weapon itself, because that would be an item.
    Only the unique attributes of a weapon are here. An item that is a weapon
    would link to this model instance.
    """

    damage_type = models.TextField(
        null=False,
        default='bludgeoning',
        help_text='The damage type dealt by attacks with the weapon.')

    damage_dice = models.TextField(
        null=True,
        help_text='The damage dice when used making an attack.')

    versatile_dice = models.TextField(
        null=True,
        help_text='The damage dice when attacking using versatile.')

    range_reach = models.IntegerField(
        null=False,
        default=5,
        validators=[MinValueValidator(0)],
        help_text='The range of the weapon when making a melee attack.')

    is_finesse = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is finesse.')

    is_thrown = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is thrown.')

    is_two_handed = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is two-handed.')

    is_versatile = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is versatile.')

    requires_ammunition = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon requires ammunition.')

    requires_loading = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon requires loading.')

    is_heavy = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is heavy.')

    is_light = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is light.')

    is_lance = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is a lance.')

    is_net = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is a net.')

    is_simple = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon category is simple.')

    is_improvised = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is improvised.')

    range_normal = models.IntegerField(
        null=True,
        validators=[MinValueValidator(0)],
        help_text='The normal range of a ranged weapon attack.')

    range_long = models.IntegerField(
        null=True,
        validators=[MinValueValidator(0)],
        help_text='The long range of a ranged weapon attack.')
    
    @property
    def is_martial(self):
        return not self.is_simple

    @property
    def is_melee(self):
        # Ammunition weapons can only be used as improvised melee weapons.
        return not self.ammunition

    @property
    def ranged_attack_possible(self):
        # Only ammunition or throw weapons can make ranged attacks.
        return self.ammunition or self.thrown 

    @property
    def range_melee(self):
        return self.range_reach
    
    @property
    def is_reach(self):
        # A weapon with a longer reach than the default has the reach property.
        return self.range_reach > 5 

    @property
    def properties(self):
        properties = []
        
        range_desc = "(range {}/{})".format(
            str(self.range_normal),
            str(self.range_long))

        versatile_desc = "({})".format(self.versatile_dice)

        if self.is_net or self.is_lance:
            properties.append("special")
        if self.is_finesse:
            properties.append("finesse")
        if self.requires_ammunition:
            properties.append("ammuntion {}".format(range_desc))
        if self.is_light:
            properties.append("light")
        if self.is_heavy:
            properties.append("heavy")
        if self.is_thrown:
            properties.append("thrown {}".format(range_desc))
        if self.requires_loading:
            properties.append("loading")
        if self.is_two_handed:
            properties.append("two-handed")
        if self.is_versatile:
            properties.append("versatile {}".format(versatile_desc))
        if self.is_reach:
            properties.append("reach")
       
        return properties
