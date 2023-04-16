from django.core.exceptions import ValidationError


def spell_school_validator(value):
    '''A validator for spell schools strings. Input must be lowercase.'''
    options = [
        'abjuration',
        'conjuration',
        'divination',
        'enchantment',
        'evocation',
        'illusion',
        'necromancy',
        'transmutation'
    ]
    if value not in options:
        raise ValidationError('Spell school {} not in valid school options. Value must be lowercase.'.format(value))


def damage_type_validator(value):
    '''A validator for damage types for spells. Input must be lowercase.'''
    options = [
        'acid',
        'cold',
        'fire',
        'force',
        'lightning',
        'necrotic',
        'poison',
        'psychic',
        'radiant',
        'thunder'
    ]
    if value not in options:
        raise ValidationError('Spell damage type {} not in valid options. Value must be lowercase.'.format(value))


def area_of_effect_shape_validator(value):
    '''A validator for spell area of effects. Input must be lowercase.'''
    options = [
        'cone',
        'cube',
        'cylinder',
        'line',
        'sphere'
    ]
    if value not in options:
        raise ValidationError('Spell area of effect {} not in valid options. Value must be lowercase.'.format(value))