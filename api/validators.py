from django.core.exceptions import ValidationError

def spell_school_validator(value):
    school_options = [
        'abjuration',
        'conjuration',
        'divination',
        'enchantment',
        'evocation',
        'illusion',
        'necromancy',
        'transmutation'
    ]
    if value not in school_options:
        raise ValidationError('Spell school {} not in valid school options. Value must be lowercase.'.format(value))