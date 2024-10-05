
import json

from django.db import models

from .models import GameContent
from .spell import Spell


class Monster(GameContent):
    size = models.TextField(help_text='Monster size category.')
    type = models.TextField(
        help_text='The type of the monster, such as "aberration"')
    subtype = models.TextField(
        help_text='If applicable, the subtype of the monster, such as "shapechanger"')
    group = models.TextField(
        null=True,
        help_text='Used to group similar creatures at different stages. "Green Dragon"')
    alignment = models.TextField(
        help_text='Short description of the creature alignment, such as "lawful good"')
    armor_class = models.IntegerField(
        default=12, help_text='Integer representing the armor class.')
    armor_desc = models.TextField(
        null=True, help_text='Description of the armor or armor type.')
    hit_points = models.IntegerField(
        null=True, help_text='Integer of the hit points.')
    hit_dice = models.TextField(
        help_text='Dice string representing a way to calculate hit points.')
    speed_json = models.TextField()

    def speed(self):
        return json.loads(self.speed_json)

    environments_json = models.TextField(
        null=True,
        help_text='String list of environments that the monster can be found in.')

    def environments(self):
        return json.loads(self.environments_json or "[]")

    strength = models.IntegerField(
        null=True, help_text='Integer representing the strength score.')
    dexterity = models.IntegerField(
        null=True, help_text='Integer represeting the dexterity score.')
    constitution = models.IntegerField(
        null=True, help_text='Integer representing the constitution score.')
    intelligence = models.IntegerField(
        null=True, help_text='Integer representing the intelligence score.')
    wisdom = models.IntegerField(
        null=True, help_text='Integer representing the wisdom score.')
    charisma = models.IntegerField(
        null=True, help_text='Integer representing the charisma score.')
    strength_save = models.IntegerField(
        null=True, help_text='Integer representing the strength save.')
    dexterity_save = models.IntegerField(
        null=True, help_text='Integer representing the dexterity save.')
    constitution_save = models.IntegerField(
        null=True, help_text='Integer representing the constitution save.')
    intelligence_save = models.IntegerField(
        null=True, help_text='Integer representing the intelligence save')
    wisdom_save = models.IntegerField(
        null=True, help_text='Integer representing the wisdom save.')
    charisma_save = models.IntegerField(
        null=True, help_text='Integer representing the charisma save.')
    perception = models.IntegerField(
        null=True, help_text='Integer representing the passive perception score.')
    skills_json = models.TextField()

    def skills(self):
        return json.loads(self.skills_json or "{}")
    damage_vulnerabilities = models.TextField(
        help_text='Comma separated list of damage types the monster is vulnerable to.')
    damage_resistances = models.TextField(
        help_text='Comma separated list of damage types the monster is resistant to.')
    damage_immunities = models.TextField(
        help_text='Comma separated list of damage types the monster is immune to.')
    condition_immunities = models.TextField(
        help_text='Comma separated list of conditions the monster is immune to.')
    senses = models.TextField(
        'Comma separated list of senses, such as "blindsight 60ft."')
    languages = models.TextField(
        'Comma separated list of languages that the monster speaks.')
    challenge_rating = models.TextField(help_text='Monster challenge rating.')
    cr = models.FloatField(
        null=True,
        help_text='Monster challenge rating as a float.')
    actions_json = models.TextField()  # a list of actions in json text.

    def actions(self):
        return json.loads(self.actions_json or "[]")
    
    bonus_actions_json = models.TextField(default=None, null=True)
    
    def bonus_actions(self):
        return json.loads(self.bonus_actions_json or "[]")
    
    # A list of special abilities in json text.
    special_abilities_json = models.TextField()

    def special_abilities(self):
        return json.loads(self.special_abilities_json or "[]")
    reactions_json = models.TextField(null=True)  # A list of reactions in json text.

    def reactions(self):
        return json.loads(self.reactions_json or "[]")
    legendary_desc = models.TextField(null=True)
    # a list of legendary actions in json.
    legendary_actions_json = models.TextField(null=True)

    def legendary_actions(self):
        return json.loads(self.legendary_actions_json or "[]")
    spells_json = models.TextField()
    spell_list = models.ManyToManyField(
        Spell,
        symmetrical=True,
        through="monsterSpell")
    route = models.TextField(default="monsters/")
    img_main = models.URLField(null=True)

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Monsters"

    def search_result_extra_fields(self):
        return {
            "armor_class":self.armor_class,
            "hit_points":self.hit_points,
            "hit_dice":self.hit_dice,
            "strength":self.strength,
            "dexterity":self.dexterity,
            "constitution":self.constitution,
            "intelligence":self.intelligence,
            "wisdom":self.wisdom,
            "charisma":self.charisma,
            "challenge_rating":self.challenge_rating,
            "cr":self.cr
              }

    def as_v2_creature(self):
        from api_v2.models import Creature, Document, DamageType
        from scripts.data_manipulation import v1_to_v2_data
        creature = Creature()
        creature.key = v1_to_v2_data.get_v2_key_from_v1_obj(self)
        creature.document = Document.objects.get(key=v1_to_v2_data.get_v2_doc_from_v1_obj(v1_obj=self))
        creature.name = self.name
        creature.size = v1_to_v2_data.get_v2_size_from_v1_obj(self)
        creature.type = v1_to_v2_data.get_v2_type_from_v1_obj(self)
        creature.alignment = v1_to_v2_data.get_alignment(self)
        creature.category = "Monsters"
        creature.armor_class = self.armor_class
        creature.hit_points = self.hit_points
        creature.passive_perception = v1_to_v2_data.get_passive_perception(self)
        creature.hit_dice = self.hit_dice
        creature.normal_sight_range = v1_to_v2_data.get_senses(self)['normal']
        creature.darkvision_range = v1_to_v2_data.get_senses(self)['darkvision']
        creature.truesight_range = v1_to_v2_data.get_senses(self)['truesight']
        creature.blindsight_range = v1_to_v2_data.get_senses(self)['blindsight']
        creature.tremorsense_range = v1_to_v2_data.get_senses(self)['tremorsense']
        # Languages


        v1_to_v2_data.copy_v2_speed_from_v1_creature(v1_obj=self, v2_obj=creature)

        v1_to_v2_data.copy_v2_scores_from_v1_creature(self, creature)

        v1_to_v2_data.copy_v2_throws_from_v1_creature(self, creature)

        v1_to_v2_data.copy_v2_skills_from_v1_creature(self, creature)



        return creature


class MonsterSpell(models.Model):
    spell = models.ForeignKey(Spell, on_delete=models.CASCADE)
    monster = models.ForeignKey(Monster, on_delete=models.CASCADE)

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "MonsterSpells"