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
    filename = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=25)
    hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Manifests"

class Document(models.Model):
    slug = models.CharField(max_length=255, unique=True, default=uuid.uuid1)
    title = models.TextField() # System Reference Document
    desc = models.TextField() 
    license = models.TextField() # Open Gaming License
    author = models.TextField() # Mike Mearls, Jeremy Crawford, Chris Perkins, Rodney Thompson, Peter Lee, James Wyatt, Robert J. Schwalb, Bruce R. Cordell, Chris Sims, and Steve Townshend, based on original material by E. Gary Gygax and Dave Arneson.
    organization = models.TextField() # Wizards of the Coast
    version = models.TextField() # 5.1
    url = models.URLField() # http://dnd.wizards.com/articles/features/systems-reference-document-srd
    copyright = models.TextField( null = True ) # Copyright 2025 open5e
    created_at = models.DateTimeField(auto_now_add=True)
    license_url= models.TextField(default="http://open5e.com/legal")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Documents"

class GameContent(models.Model):
    slug = models.CharField(max_length=255, unique=True, default=uuid.uuid1, primary_key=True) # dispel-evil-and-good
    name = models.TextField()
    desc = models.TextField()
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
    higher_level = models.TextField()
    page = models.TextField()
    range = models.TextField()
    components = models.TextField()
    material = models.TextField()
    ritual = models.TextField()
    duration = models.TextField()
    concentration = models.TextField()
    casting_time = models.TextField()
    level = models.TextField()
    level_int = models.IntegerField(null=True)
    school = models.TextField()
    dnd_class = models.TextField()
    archetype = models.TextField()
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
    challenge_rating = models.TextField()
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
        
    prerequisite = models.TextField()
    route = models.TextField(default="conditions/") 

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
    category = models.TextField()
    cost = models.TextField()
    damage_dice = models.TextField()
    damage_type = models.TextField()
    weight = models.TextField()
    properties_json = models.TextField()
    def properties(self):
        if self.properties_json:
            return json.loads(self.properties_json)
    route = models.TextField(default="weapons/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Weapons"

class Armor(GameContent):
    category = models.TextField()
    cost=models.TextField()
    weight = models.TextField()
    stealth_disadvantage=models.BooleanField()
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
