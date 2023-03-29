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
    filename = models.CharField(max_length=255, unique=True, help_text='Input file name.')
    type = models.CharField(max_length=25, help_text='Type of file (maps to a model).')
    hash = models.CharField(max_length=255, help_text='md5 hash of the file contents.')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Date that this object was added to the database.')

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Manifests"

class Document(models.Model):
    slug = models.CharField(max_length=255, unique=True, default=uuid.uuid1)
    title = models.TextField(help_text='Title of the document.') # System Reference Document
    desc = models.TextField(help_text='Description of the document.')
    license = models.TextField(help_text='The license of the content within the document.') # Open Gaming License
    author = models.TextField(help_text='Author or authors.') # Mike Mearls, Jeremy Crawford, Chris Perkins, Rodney Thompson, Peter Lee, James Wyatt, Robert J. Schwalb, Bruce R. Cordell, Chris Sims, and Steve Townshend, based on original material by E. Gary Gygax and Dave Arneson.
    organization = models.TextField(help_text='Publishing organization.') # Wizards of the Coast
    version = models.TextField(help_text='Document version.') # 5.1
    url = models.URLField(help_text='URL reference to get the document.') # http://dnd.wizards.com/articles/features/systems-reference-document-srd
    copyright = models.TextField( null = True, help_text='Copyright statement.') # Copyright 2025 open5e
    created_at = models.DateTimeField(auto_now_add=True,help_text='Date that this object was added to the database.')
    license_url= models.TextField(default="http://open5e.com/legal", help_text='URL reference for the license.')

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Documents"

class GameContent(models.Model):
    slug = models.CharField(max_length=255, unique=True, default=uuid.uuid1, primary_key=True, help_text='Short name for the game content item.') # dispel-evil-and-good
    name = models.TextField(help_text='Name of the game content item.')
    desc = models.TextField(help_text='Description of the game content item. Markdown.')
    document = models.ForeignKey(Document, on_delete=models.CASCADE) # Like the System Reference Document
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

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
    class Meta:
        abstract=True

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "GameContents"

class Spell(GameContent):
    higher_level = models.TextField(help_text='What happens if you cast this at a higher level.')
    page = models.TextField(help_text='Page number reference for the document.')
    range = models.TextField(help_text='Text description of the range.')
    components = models.TextField(help_text='Single-character list of V, S, M for Verbal, Somatic, or Material based on the spell requirements.')
    material = models.TextField(help_text='Description of the material required.')
    ritual = models.TextField(help_text='"yes" or "no" based on whether or not a ritual is required.')
    duration = models.TextField(help_text='Description of the duration such as "instantaneous" or "Up to 1 minute"')
    concentration = models.TextField(help_text='"yes" or "no" based on whether the spell requires concentration.')
    casting_time = models.TextField(help_text='Amount of time it takes to cast the spell, such as "1 bonus action" or "4 hours".')
    level = models.TextField(help_text='Description of the level of the spell, such as "4th-level".')
    level_int = models.IntegerField(null=True, help_text='Integer representing the level of the spell. Cantrip is 0.')
    school = models.TextField(help_text='Representation of the school of magic, such as "illusion" or "evocation".')
    dnd_class = models.TextField('List of classes (comma separated) that can learn this spell.')
    archetype = models.TextField('Archetype that can learn this spell. If empty, assume all archetypes.')
    circles = models.TextField()
    route = models.TextField(default="spells/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Spells"

class Monster(GameContent):
    size = models.TextField()
    type = models.TextField()
    subtype = models.TextField()
    group = models.TextField(null=True)
    alignment = models.TextField()
    armor_class = models.IntegerField(default=12)
    armor_desc = models.TextField(null=True)
    hit_points = models.IntegerField(null=True)
    hit_dice = models.TextField()
    speed_json = models.TextField()
    def speed(self):
        return json.loads(self.speed_json)
    strength = models.IntegerField(null=True)
    dexterity = models.IntegerField(null=True)
    constitution = models.IntegerField(null=True)
    intelligence = models.IntegerField(null=True)
    wisdom = models.IntegerField(null=True)
    charisma = models.IntegerField(null=True)
    strength_save = models.IntegerField(null=True)
    dexterity_save = models.IntegerField(null=True)
    constitution_save = models.IntegerField(null=True)
    intelligence_save = models.IntegerField(null=True)
    wisdom_save = models.IntegerField(null=True)
    charisma_save = models.IntegerField(null=True)
    perception = models.IntegerField(null=True)
    skills_json = models.TextField()
    def skills(self):
        return json.loads(self.skills_json)
    damage_vulnerabilities = models.TextField()
    damage_resistances = models.TextField()
    damage_immunities = models.TextField()
    condition_immunities = models.TextField()
    senses = models.TextField()
    languages = models.TextField()
    challenge_rating = models.TextField(help_text='Monster challenge rating.')
    cr = models.FloatField(null=True)
    actions_json = models.TextField() #a list of actions in json text.
    def actions(self):
        return json.loads(self.actions_json)
    special_abilities_json = models.TextField() # A list of special abilities in json text.
    def special_abilities(self):
        return json.loads(self.special_abilities_json)
    reactions_json = models.TextField() # A list of reactions in json text.
    def reactions(self):
        return json.loads(self.reactions_json)
    legendary_desc = models.TextField()
    legendary_actions_json = models.TextField() # a list of legendary actions in json.
    def legendary_actions(self):
        return json.loads(self.legendary_actions_json)
    spells_json = models.TextField()
    spell_list = models.ManyToManyField(Spell, related_name='monsters', symmetrical=True, through="monsterSpell")
    route = models.TextField(default="monsters/")
    img_main = models.URLField(null=True)

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Monsters"

class MonsterSpell(models.Model):
    spell = models.ForeignKey(Spell, on_delete=models.CASCADE)
    monster = models.ForeignKey(Monster, on_delete=models.CASCADE)

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "MonsterSpells"

class CharClass(GameContent):
    hit_dice = models.TextField()
    hp_at_1st_level = models.TextField()
    hp_at_higher_levels = models.TextField()
    prof_armor = models.TextField()
    prof_weapons = models.TextField()
    prof_tools = models.TextField()
    prof_saving_throws = models.TextField()
    prof_skills = models.TextField()
    equipment = models.TextField()
    table = models.TextField()
    spellcasting_ability = models.TextField()
    subtypes_name = models.TextField()
    route = models.TextField(default="classes/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "CharClasses"

class Archetype(GameContent):
    char_class = models.ForeignKey(CharClass, related_name='archetypes', on_delete=models.CASCADE, null=True)
    route = models.TextField(default="archetypes/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Archetypes"

class Race(GameContent):
    asi_desc = models.TextField()
    asi_json = models.TextField()
    def asi(self):
        return json.loads(self.asi_json)
    age = models.TextField()
    alignment = models.TextField()
    size = models.TextField()
    speed_json = models.TextField()
    def speed(self):
        return json.loads(self.speed_json)
    speed_desc = models.TextField()
    languages = models.TextField()
    vision = models.TextField()
    traits = models.TextField()
    route = models.TextField(default="races/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Races"

class Subrace(GameContent):
    asi_desc = models.TextField()
    asi_json = models.TextField()
    def asi(self):
        return json.loads(self.asi_json)
    traits = models.TextField()
    parent_race = models.ForeignKey(Race, related_name='subraces', on_delete=models.CASCADE, null=True)
    route = models.TextField(default="subraces/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Subraces"

class Plane(GameContent):
    pass
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

class Feat(GameContent):
    prerequisite = models.TextField(null=True)
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
    skill_proficiencies = models.TextField(null=True)
    tool_proficiencies=models.TextField(null=True)
    languages = models.TextField(null=True)
    equipment = models.TextField()
    feature = models.TextField()
    feature_desc = models.TextField()
    suggested_characteristics = models.TextField()
    route = models.TextField(default="backgrounds/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Backgrounds"

class MagicItem(GameContent):
    type = models.TextField()
    rarity = models.TextField()
    requires_attunement = models.TextField()
    route = models.TextField(default="magicitems/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "MagicItems"

class Weapon(GameContent):
    category = models.TextField(help_text='Category of the weapon, such as "Martial Melee Weapons"')
    cost = models.TextField(help_text='Suggested cost of the weapon, such as "100 gp"')
    damage_dice = models.TextField(help_text='Dice string of the weapon damage, such as "1d8".')
    damage_type = models.TextField(help_text='Damage type of the weapon, such as "bludgeoning".')
    weight = models.TextField(help_text='Weight of the item, such as "1 lb.".')
    properties_json = models.TextField(help_text='List of properties that the weapon has.')
    def properties(self):
        if self.properties_json:
            return json.loads(self.properties_json)
    route = models.TextField(default="weapons/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Weapons"

class Armor(GameContent):
    category = models.TextField(help_text='Category of the armor, such as "Heavy Armor"')
    cost=models.TextField(help_text='Suggested cost of the weapon, such as "100 gp"')
    weight = models.TextField(help_text='Apparently an empty string.')
    stealth_disadvantage=models.BooleanField('Boolean representing whether wearing the armor results in stealth disadvantage for the wearer.')
    base_ac = models.IntegerField()
    plus_dex_mod = models.BooleanField(null=True)
    plus_con_mod = models.BooleanField(null=True)
    plus_wis_mod = models.BooleanField(null=True)
    plus_flat_mod = models.IntegerField(null=True) #Build a shield this way.
    plus_max = models.IntegerField(null=True)
    def ac_string(self):
        ac = str(self.base_ac)
        if self.plus_dex_mod: ac += (" + Dex modifier")
        if self.plus_con_mod: ac += (" + Con modifier")
        if self.plus_wis_mod: ac += (" + Wis modifier")
        if self.plus_flat_mod: ac += (" +"+str(self.plus_flat_mod))
        if self.plus_max: ac += (" (max 2)")
        return ac.strip()

    strength_requirement = models.IntegerField(null=True)

    route = models.TextField(default="armor/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Armors"
