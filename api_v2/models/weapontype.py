"""The model for a type of weapon."""

from django.db import models
from django.core.validators import MinValueValidator

from api.models import GameContent


class WeaponType(GameContent):
    """
    This model represents types of weapons.

    This does not represent a weapon itself, because that would be an item.
    Only the unique attributes of a weapon are here. An item that is a weapon
    would link to this model instance.
    """

    damage_type = models.TextField(
        null=False,
        default='bludgeoning',
#        validators=[damage_type_validator],
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

    is_martial = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is category is martial.')

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

    def melee_attack_possible(self):
        # All weapons can be used to make a melee attack.
        return True 

    def melee_attack_is_improvised(self):
        # Ammunition weapons can only be used as improvised melee weapons.
        return self.ammunition 

    def ranged_attack_possible(self):
        # Only ammunition or throw weapons can make ranged attacks.
        return self.ammunition or self.thrown 

    def range_melee(self):
        return self.range_reach
    
    def is_reach(self):
        # A weapon with a longer reach than the default has the reach property.
        return self.range_reach > 5 

    def properties_display(self):
        properties = []
        
        range_desc = "(range {}/{})".format(
            str(self.range_normal()),
            str(self.range_long()))

        versatile_desc = "({})".format(self.versatile_dice)

        if self.special:
            properties.append("special")
        if self.finesse:
            properties.append("finesse")
        if self.ammunition:
            properties.append("ammuntion {}".format(range_desc))
        if self.light:
            properties.append("light")
        if self.heavy:
            properties.append("heavy")
        if self.thrown:
            properties.append("thrown {}".format(range_desc))
        if self.loading:
            properties.append("loading")
        if self.two-handed:
            properties.append("two-handed")
        if self.versatile:
            properties.append("versatile {}".format(versatile_desc))
        if self.reach:
            properties.append("reach")

        if len(properties) > 0:
            # Capitalize the first letter of the first property.
            properties[0][0] = properties[0][0].upper()
            return properties

        else:
            return ["-"]
