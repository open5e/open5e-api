import json
import uuid

from django.db import models


class Manifest(models.Model):
    """A Manifest contains a hash based on the contents of a file.

    This is intended for folks who process and store content from our API.
    When they download content, they also download the corresponding manifest.
    Periodically, they check back in to see whether any manifests have changed.
    If so, then they know to re-download that source.
    """
    
    filename = models.CharField(
        max_length=255,
        unique=True,
        help_text='Input file name.')
    type = models.CharField(
        max_length=25,
        help_text='Type of file (maps to a model).')
    hash = models.CharField(max_length=255,
                            help_text='md5 hash of the file contents.')
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Date that this object was added to the database.')

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Manifests"


class Document(models.Model):
    slug = models.CharField(max_length=255, unique=True, default=uuid.uuid1)
    # System Reference Document
    title = models.TextField(help_text='Title of the document.')
    desc = models.TextField(help_text='Description of the document.')
    license = models.TextField(
        help_text='The license of the content within the document.')  # Open Gaming License
    # Mike Mearls, Jeremy Crawford, Chris Perkins, Rodney Thompson, Peter Lee,
    # James Wyatt, Robert J. Schwalb, Bruce R. Cordell, Chris Sims, and Steve
    # Townshend, based on original material by E. Gary Gygax and Dave Arneson.
    author = models.TextField(help_text='Author or authors.')
    organization = models.TextField(
        help_text='Publishing organization.')  # Wizards of the Coast
    version = models.TextField(help_text='Document version.')  # 5.1
    # http://dnd.wizards.com/articles/features/systems-reference-document-srd
    url = models.URLField(help_text='URL reference to get the document.')
    copyright = models.TextField(
        null=True, help_text='Copyright statement.')  # Copyright 2025 open5e
    #created_at = models.DateTimeField(
    #    auto_now_add=True,
    #    help_text='Date that this object was added to the database.')
    license_url = models.TextField(
        default="http://open5e.com/legal",
        help_text='URL reference for the license.')

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Documents"


class GameContent(models.Model):
    slug = models.CharField(
        max_length=255,
        unique=True,
        default=uuid.uuid1,
        primary_key=True,
        help_text='Short name for the game content item.')  # dispel-evil-and-good
    name = models.TextField(help_text='Name of the game content item.')
    desc = models.TextField(
        help_text='Description of the game content item. Markdown.')
    # Like the System Reference Document
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    #created_at = models.DateTimeField(auto_now_add=True, editable=False)

    # If the source is a physical book (possibly with a digital version),
    # then page_no is the page number in the physical book, even if the PDF
    # page number is different due to additional cover pages.
    # If the source is only digital, then of course just the PDF page number.
    # This field may be hard to populate across-the-board, so leave as None
    # unless explicitly populated.
    page_no = models.IntegerField(null=True)

    def document__slug(self):
        return self.document.slug

    def document__title(self):
        return self.document.title

    def document__license_url(self):
        return self.document.license_url

    def document__url(self):
        return self.document.url

    class Meta:
        abstract = True

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "GameContents"


class CharClass(GameContent):
    hit_dice = models.TextField(
        help_text='Description of dice for each level such as "1d12 per barbarian level"')
    hp_at_1st_level = models.TextField(
        help_text='Description of the Hit Points at level 1, such as "12 + your Constitution modifier"')
    hp_at_higher_levels = models.TextField(
        help_text='Desciption of increases in Hit Points per level.')
    prof_armor = models.TextField(
        help_text='Comma-separated list of armor types that the class is proficient with.')
    prof_weapons = models.TextField(
        help_text='Comma-separated list of weapons that the class is proficient with.')
    prof_tools = models.TextField(
        help_text='Description of tools the class is proficient with.')
    prof_saving_throws = models.TextField(
        help_text='Comma separated list of saving throw abilities that the class is proficient with.')
    prof_skills = models.TextField(
        help_text='Description of the skills that the class is proficient with.')
    equipment = models.TextField(
        help_text='Markdown description of starting equipment.')
    table = models.TextField(
        help_text='Table describing class growth by level.')
    spellcasting_ability = models.TextField(
        help_text='Ability used for casting spells.')
    subtypes_name = models.TextField(
        help_text='Preferred name for class subtypes, such as "Domains" (for Cleric).')
    route = models.TextField(default="classes/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "CharClasses"


class Archetype(GameContent):
    char_class = models.ForeignKey(
        CharClass,
        related_name='archetypes',
        on_delete=models.CASCADE,
        null=True)
    route = models.TextField(default="archetypes/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Archetypes"


class Race(GameContent):
    asi_desc = models.TextField(
        help_text='Markdown description of ability score changes for this race.')
    asi_json = models.TextField()

    def asi(self):
        return json.loads(self.asi_json)
    age = models.TextField(
        help_text='Markdown description of how this race ages.')
    alignment = models.TextField(
        help_text='Markdown description of the alignment tendencies of the race.')
    size = models.TextField(
        help_text='Markdown description of the size category of the race.')
    size_raw = models.TextField(
        help_text='Size Category.', default="Medium")
    speed_json = models.TextField()

    def speed(self):
        return json.loads(self.speed_json)
    speed_desc = models.TextField(
        help_text='Markdown description of the speed of the race.')
    languages = models.TextField(
        help_text='Markdown description of the languages known by the race.')
    vision = models.TextField(
        help_text='Markdown description of any vision features the race has.')
    traits = models.TextField(
        help_text='Markdown description of special traits thr race has.')
    route = models.TextField(default="races/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Races"


class Subrace(GameContent):
    asi_desc = models.TextField(
        help_text='Markdown description of ability score changes for this subrace.')
    asi_json = models.TextField()

    def asi(self):
        return json.loads(self.asi_json)
    traits = models.TextField(
        help_text='Markdown description of special traits thr race has.')
    parent_race = models.ForeignKey(
        Race,
        related_name='subraces',
        on_delete=models.CASCADE,
        null=True)
    route = models.TextField(default="subraces/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Subraces"


class Plane(GameContent):
    parent = models.TextField(null=True)
    route = models.TextField(default="planes/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Planes"


class Section(GameContent):
    parent = models.TextField(null=True)
    route = models.TextField(default="sections/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Sections"

    def search_result_extra_fields(self):
        return {
            "parent":self.parent}




class Feat(GameContent):
    prerequisite = models.TextField(
        null=True, help_text='Description of a prerequisite for the character.')
    # desc
    route = models.TextField(default="feats/")
    effects_desc_json = models.TextField()

    def effects_desc(self):
        if self.effects_desc_json:
            return json.loads(self.effects_desc_json)

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Feats"


class Condition(GameContent):
    pass
    route = models.TextField(default="conditions/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Conditions"


class Background(GameContent):
    skill_proficiencies = models.TextField(
        null=True,
        help_text='Description of the skills that the background provides proficiency with.')
    tool_proficiencies = models.TextField(
        null=True,
        help_text='Description of the tools that the background provides is proficiency with.')
    languages = models.TextField(
        null=True,
        help_text='Description of the languages that the background provides knowledge of.')
    equipment = models.TextField(
        help_text='Markdown description of equipment held by characters with this background.')
    feature = models.TextField(
        help_text='Title of a feature this background grants.')
    feature_desc = models.TextField(
        help_text='Description of the related background feature.')
    suggested_characteristics = models.TextField(
        help_text='Currently not implemented.')
    route = models.TextField(default="backgrounds/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Backgrounds"


class MagicItem(GameContent):
    type = models.TextField(
        help_text='Description of the item type, such as "Armor (light)".')
    rarity = models.TextField(
        help_text='Description of the rarity, such as "rare".')
    requires_attunement = models.TextField(
        'The word "requires attunement" or blank.')
    route = models.TextField(default="magicitems/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "MagicItems"
    
    def search_result_extra_fields(self):
        return {
            "type":self.type,
            "rarity":self.rarity,
            "requires_attunement":self.requires_attunement}



class Weapon(GameContent):
    category = models.TextField(
        help_text='Category of the weapon, such as "Martial Melee Weapons"')
    cost = models.TextField(
        help_text='Suggested cost of the weapon, such as "100 gp"')
    damage_dice = models.TextField(
        help_text='Dice string of the weapon damage, such as "1d8".')
    damage_type = models.TextField(
        help_text='Damage type of the weapon, such as "bludgeoning".')
    weight = models.TextField(help_text='Weight of the item, such as "1 lb.".')
    properties_json = models.TextField(
        help_text='List of properties that the weapon has.')

    def properties(self):
        if self.properties_json:
            return json.loads(self.properties_json)
    route = models.TextField(default="weapons/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Weapons"


class Armor(GameContent):
    category = models.TextField(
        help_text='Category of the armor, such as "Heavy Armor"')
    cost = models.TextField(
        help_text='Suggested cost of the weapon, such as "100 gp"')
    weight = models.TextField(help_text='Apparently an empty string.')
    stealth_disadvantage = models.BooleanField(
        'Boolean representing whether wearing the armor results in stealth disadvantage for the wearer.')
    base_ac = models.IntegerField()
    plus_dex_mod = models.BooleanField(default=False)
    plus_con_mod = models.BooleanField(default=False)
    plus_wis_mod = models.BooleanField(default=False)
    plus_flat_mod = models.IntegerField(default=False)  # Build a shield this way.
    plus_max = models.IntegerField(default=0)

    def ac_string(self):
        ac = str(self.base_ac)
        if self.plus_dex_mod:
            ac += (" + Dex modifier")
        if self.plus_con_mod:
            ac += (" + Con modifier")
        if self.plus_wis_mod:
            ac += (" + Wis modifier")
        if self.plus_flat_mod:
            ac += (" +" + str(self.plus_flat_mod))
        if self.plus_max:
            ac += (" (max 2)")
        return ac.strip()

    strength_requirement = models.IntegerField(null=True)

    route = models.TextField(default="armor/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Armors"
