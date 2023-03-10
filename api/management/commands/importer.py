import enum
import json
import pathlib
from typing import Callable, Dict, List, NamedTuple, Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import models as django_models
from django.template.defaultfilters import slugify
from fractions import Fraction

from api import models

# MONSTERS_IMG_DIR is the path in this repo for static monster images.
MONSTERS_IMG_DIR = pathlib.Path('.', 'static', 'img', 'monsters').absolute()


class ImportSpec(NamedTuple):
    """Helper class to specify how to import a type of model."""
    # model_class is the type of model to create.
    model_class: django_models.Model
    # import_func is the function that creates a model based on JSON.
    # It should take the model JSON as its first argument, and options as its
    # second argument, and return an ImportResult specifying whether a model
    # was skipped, added, or updated.
    import_func: Callable[[Dict, Dict], "ImportResult"]


class ImportResult(enum.Enum):
    """What happened from a single import. Was a model added? Skipped?"""
    UNSPECIFIED = 0
    ADDED = 1
    SKIPPED = 2
    UPDATED = 3


class Importer:
    
    def __init__(self):
      self._last_document_imported: Optional[models.Document] = None

    def update_monster(self, monster, spell):
        # print(spell) # useful for debugging new lists
        db_monster = models.Monster.objects.get(slug=monster)
        db_spell = models.Spell.objects.get(slug=slugify(spell))
        models.MonsterSpell.objects.create(spell=db_spell, monster=db_monster)  # <----- Create m2m relation

    def ManifestImporter(self, options, filepath: str, filehash: str) -> None:
        skipped, added, updated = (0, 0, 0)

        new = False
        exists = False

        if models.Manifest.objects.filter(filename=str(filepath)).exists():
            i = models.Manifest.objects.get(filename=str(filepath))
            exists = True
        else:
            i = models.Manifest()
            new = True

        i.filename = str(filepath)
        i.hash = filehash
        i.type = filepath.stem
        i.save()

        if new: added += 1
        else: updated += 1

    def DocumentImporter(self, options, json_object):
        skipped, added, updated = (0, 0, 0)
        if bool(options['flush']): models.Document.objects.all().delete()

        for o in json_object:
            new = False
            exists = False
            # Setting up the object.
            if models.Document.objects.filter(slug=slugify(o['slug'])).exists():
                i = models.Document.objects.get(slug=slugify(o['slug']))
                exists = True
            else:
                i = models.Document()
                new = True
            # Adding the data to the created object.
            i.title = o['title']
            i.slug = slugify(o['slug'])
            i.desc = o['desc']
            i.author = o['author']
            i.license = o['license']
            i.version = o['version']
            i.url = o['url']
            i.copyright = o['copyright']
            if bool(options['testrun']) or (exists and options['append']):
               skipped += 1
            else:
                i.save()
                if new: added += 1
                else: updated += 1
        self._last_document_imported = i
        return _completion_message('Document', added, updated, skipped)

    def BackgroundImporter(self, options, json_object):
        skipped, added, updated = (0, 0, 0)
        if bool(options['flush']): models.Background.objects.all().delete()

        for o in json_object:
            new = False
            exists = False
            if models.Background.objects.filter(slug=slugify(o['name'])).exists():
                i = models.Background.objects.get(slug=slugify(o['name']))
                exists = True
            else:
                i = models.Background(document = self._last_document_imported)
                new = True
            if 'name' in o:
                i.name = o['name']
                i.slug = slugify(o['name'])
            if 'desc' in o:
                i.desc = o['desc']
            if 'skill-proficiencies' in o:
                i.skill_proficiencies = o['skill-proficiencies']
            if 'tool-proficiencies' in o:
                i.tool_proficiencies = o['tool-proficiencies']
            if 'languages' in o:
                i.languages = o['languages']
            if 'equipment' in o:
                i.equipment = o['equipment']
            if 'feature-name' in o:
                i.feature = o['feature-name']
            if 'feature-desc' in o:
                i.feature_desc = o['feature-desc']
            if 'suggested-characteristics' in o:
                i.suggested_characteristics = o['suggested-characteristics']
            if bool(options['testrun']) or (exists and options['append']):
               skipped += 1
            else:
                i.save()
                if new: added += 1
                else: updated += 1

        return _completion_message('Backgrounds', added, updated, skipped)

    def ClassImporter(self, options, json_object):
        skipped, added, updated = (0, 0, 0)
        if bool(options['flush']): models.Archetype.objects.all().delete()
        if bool(options['flush']): models.CharClass.objects.all().delete()

        for o in json_object:
            new = False
            exists = False
            if models.CharClass.objects.filter(slug=slugify(o['name'])).exists():
                i = models.CharClass.objects.get(slug=slugify(o['name']))
                exists = True
            else:
                i = models.CharClass(document = self._last_document_imported)
                new = True
            if 'name' in o:
                i.name = o['name']
                i.slug = slugify(o['name'])
            if 'subtypes-name' in o:
                i.subtypes_name = o['subtypes-name']
            if 'hit-dice' in o['features']:
                i.hit_dice = o['features']['hit-dice']
            if 'hp-at-1st-level' in o['features']:
                i.hp_at_1st_level = o['features']['hp-at-1st-level']
            if 'hp-at-higher-levels' in o['features']:
                i.hp_at_higher_levels = o['features']['hp-at-higher-levels']
            if 'prof-armor' in o['features']:
                i.prof_armor = o['features']['prof-armor']
            if 'prof-weapons' in o['features']:
                i.prof_weapons = o['features']['prof-weapons']
            if 'prof-tools' in o['features']:
                i.prof_tools = o['features']['prof-tools']
            if 'prof-saving-throws' in o['features']:
                i.prof_saving_throws = o['features']['prof-saving-throws']
            if 'prof-skills' in o['features']:
                i.prof_skills = o['features']['prof-skills']
            if 'equipment' in o['features']:
                i.equipment = o['features']['equipment']
            if 'table' in o['features']:
                i.table = o['features']['table']
            if 'spellcasting-ability' in o['features']:
                i.spellcasting_ability = o['features']['spellcasting-ability']
            if 'desc' in o['features']:
                i.desc = o['features']['desc']
            if bool(options['testrun']) or (exists and options['append']):
               skipped += 1
            else:
                i.save()
                if 'subtypes' in o:
                    self.ArchetypeImporter(options, o['subtypes'], i)
                if new: added += 1
                else: updated += 1

        return _completion_message('Classes', added, updated, skipped)

    def ArchetypeImporter(self, options, json_object, char_class):
        skipped, added, updated = (0, 0, 0)

        for o in json_object:
            new = False
            exists = False
            if models.Archetype.objects.filter(slug=slugify(o['name'])).exists():
                i = models.Archetype.objects.get(slug=slugify(o['name']))
                exists = True
            else:
                i = models.Archetype(document = self._last_document_imported, char_class=char_class)
                if 'name' in o:
                    i.name = o['name']
                    i.slug = slugify(o['name'])
                if 'desc' in o:
                    i.desc = o['desc']          
                if bool(options['testrun']) or (exists and options['append']):
                    skipped += 1
                else:
                    i.save()
                if new: added += 1
                else: updated += 1
        return _completion_message('Archetypes', added, updated, skipped)

    def ConditionImporter(self, options, json_object):
        skipped, added, updated = (0, 0, 0)
        if bool(options['flush']): models.Condition.objects.all().delete()

        for o in json_object:
            new = False
            exists = False
            if models.Condition.objects.filter(slug=slugify(o['name'])).exists():
                i = models.Condition.objects.get(slug=slugify(o['name']))
                exists = True
            else:
                i = models.Condition(document = self._last_document_imported)
                new = True
            if 'name' in o:
                i.name = o['name']
                i.slug = slugify(o['name'])
            if 'desc' in o:
                i.desc = o['desc']
            if bool(options['testrun']) or (exists and options['append']):
               skipped += 1
            else:
                i.save()
                if new: added += 1
                else: updated += 1

        return _completion_message('Conditions', added, updated, skipped)

    def import_models_from_json(
        self,
        import_spec: ImportSpec,
        models_json: List[Dict],
        options: Dict[str, bool]
    ) -> str:
        """Import a list of models from a source JSON file."""
        skipped, added, updated = (0, 0, 0)
        if options['flush']:
            import_spec.model_class.objects.all().delete()
        for model_json in models_json:
            import_result = import_spec.import_func(model_json, options)
            if import_result is ImportResult.SKIPPED:
                skipped += 1
            elif import_result is ImportResult.ADDED:
                added += 1
            elif import_result is ImportResult.UPDATED:
                updated += 1
            else:
                raise ValueError(f'Unexpected ImportResult: {import_result}')
        return _completion_message(
            import_spec.model_class.plural_str(), added, updated, skipped)

    def import_feat(self, feat_json, options) -> ImportResult:
        new = False
        exists = False
        if models.Feat.objects.filter(slug=slugify(feat_json['name'])).exists():
            i = models.Feat.objects.get(slug=slugify(feat_json['name']))
            exists = True
        else:
            i = models.Feat(document = self._last_document_imported)
            new = True
        if 'name' in feat_json:
            i.name = feat_json['name']
            i.slug = slugify(feat_json['name'])
        if 'desc' in feat_json:
            i.desc = feat_json['desc']
        if 'prerequisite' in feat_json:
            i.prerequisite = feat_json['prerequisite']
        result = _determine_import_result(options, new, exists)
        if result is not ImportResult.SKIPPED:
            i.save()
        return result

    def import_magic_item(self, magic_item_json, options) -> ImportResult:
        new = False
        exists = False
        if models.MagicItem.objects.filter(slug=slugify(magic_item_json['name'])).exists():
            i = models.MagicItem.objects.get(slug=slugify(magic_item_json['name']))
            exists = True
        else:
            i = models.MagicItem(document = self._last_document_imported)
            new = True
        if 'name' in magic_item_json:
            i.name = magic_item_json['name']
            i.slug = slugify(magic_item_json['name'])
        if 'desc' in magic_item_json:
            i.desc = magic_item_json['desc']
        if 'type' in magic_item_json:
            i.type = magic_item_json['type']
        if 'rarity' in magic_item_json:
            i.rarity = magic_item_json['rarity']
        if 'requires-attunement' in magic_item_json:
            i.requires_attunement = magic_item_json['requires-attunement']
        result = _determine_import_result(options, new, exists)
        if result is not ImportResult.SKIPPED:
            i.save()
        return result

    def import_monster(self, monster_json, options) -> ImportResult:
        new = False
        exists = False
        slug_name = slugify(['name'])
        if models.Monster.objects.filter(slug=slugify(monster_json['name'])).exists():
            i = models.Monster.objects.get(slug=slugify(monster_json['name']))
            exists = True
        else:
            i = models.Monster(document = self._last_document_imported)
            new = True
        if 'name' in monster_json:
            i.name = monster_json['name']
            i.slug = slugify(monster_json['name'])
        img_file = MONSTERS_IMG_DIR / f"{slugify(monster_json['name'])}.png"
        if img_file.exists():
            i.img_main = img_file
        if 'size' in monster_json:
            i.size = monster_json['size']
        if 'type' in monster_json:
            i.type = monster_json['type']
        if 'subtype' in monster_json:
            i.subtype = monster_json['subtype']
        if 'group' in monster_json:
            i.group = monster_json['group']
        if 'alignment' in monster_json:
            i.alignment = monster_json['alignment']
        if 'armor_class' in monster_json:
            i.armor_class = monster_json['armor_class']
        if 'armor_desc' in monster_json:
            i.armor_desc = monster_json['armor_desc']
        if 'hit_points' in monster_json:
            i.hit_points = monster_json['hit_points']
        if 'hit_dice' in monster_json:
            i.hit_dice = monster_json['hit_dice']
        if 'speed' in monster_json:
            i.speed_json = json.dumps(monster_json['speed_json'])
        if 'strength' in monster_json:
            i.strength = monster_json['strength']
        if 'dexterity' in monster_json:
            i.dexterity = monster_json['dexterity']
        if 'constitution' in monster_json:
            i.constitution = monster_json['constitution']
        if 'intelligence' in monster_json:
            i.intelligence = monster_json['intelligence']
        if 'wisdom' in monster_json:
            i.wisdom = monster_json['wisdom']
        if 'charisma' in monster_json:
            i.charisma = monster_json['charisma']
        if 'strength_save' in monster_json:
            i.strength_save = monster_json['strength_save']
        if 'dexterity_save' in monster_json:
            i.dexterity_save = monster_json['dexterity_save']
        if 'constitution_save' in monster_json:
            i.constitution_save = monster_json['constitution_save']
        if 'intelligence_save' in monster_json:
            i.intelligence_save = monster_json['intelligence_save']
        if 'wisdom_save' in monster_json:
            i.wisdom_save = monster_json['wisdom_save']
        if 'charisma_save' in monster_json:
            i.charisma_save = monster_json['charisma_save']
        # SKILLS START HERE
        skills = {}
        if 'acrobatics' in monster_json:
            skills['acrobatics'] = monster_json['acrobatics']
        if 'animal handling' in monster_json:
            skills['animal_handling'] = monster_json['animal handling']
        if 'arcana' in monster_json:
            skills['arcana'] = monster_json['arcana']
        if 'athletics' in monster_json:
            skills['athletics'] = monster_json['athletics']
        if 'deception' in monster_json:
            skills['deception'] = monster_json['deception']
        if 'history' in monster_json:
            skills['history'] = monster_json['history']
        if 'insight' in monster_json:
            skills['insight'] = monster_json['insight']
        if 'intimidation' in monster_json:
            skills['intimidation'] = monster_json['intimidation']
        if 'investigation' in monster_json:
            skills['investigation'] = monster_json['investigation']
        if 'medicine' in monster_json:
            skills['medicine'] = monster_json['medicine']
        if 'nature' in monster_json:
            skills['nature'] = monster_json['nature']
        if 'perception' in monster_json:
            skills['perception'] = monster_json['perception']
        if 'performance' in monster_json:
            skills['performance'] = monster_json['performance']
        if 'perception' in monster_json:
            i.perception = monster_json['perception']
            skills['perception'] = monster_json['perception']
        if 'persuasion' in monster_json:
            skills['persuasion'] = monster_json['persuasion']
        if 'religion' in monster_json:
            skills['religion'] = monster_json['religion']
        if 'sleight of hand' in monster_json:
            skills['sleight_of_hand'] = monster_json['sleight of hand']
        if 'stealth' in monster_json:
            skills['stealth'] = monster_json['stealth']
        if 'survival' in monster_json:
            skills['survival'] = monster_json['survival']
        i.skills_json = json.dumps(skills)
        # END OF SKILLS  
        if 'damage_vulnerabilities' in monster_json:
            i.damage_vulnerabilities = monster_json['damage_vulnerabilities']
        if 'damage_resistances' in monster_json:
            i.damage_resistances = monster_json['damage_resistances']
        if 'damage_immunities' in monster_json:
            i.damage_immunities = monster_json['damage_immunities']
        if 'condition_immunities' in monster_json:
            i.condition_immunities = monster_json['condition_immunities']
        if 'senses' in monster_json:
            i.senses = monster_json['senses']
        if 'languages' in monster_json:
            i.languages = monster_json['languages']
        if 'challenge_rating' in monster_json:
            i.challenge_rating = monster_json['challenge_rating']
            i.cr = float(Fraction(i.challenge_rating))
        if 'actions' in monster_json:
            for idx, z in enumerate(monster_json['actions']):
                if 'attack_bonus' in z:
                    if z['attack_bonus'] == 0 and 'damage_dice' not in z:
                        del z['attack_bonus']
                monster_json['actions'][idx] = z
            i.actions_json = json.dumps(monster_json['actions'])
        else:
            i.actions_json = json.dumps("")
        if 'special_abilities' in monster_json:
            for idx, z in enumerate(monster_json['special_abilities']):
                if 'attack_bonus' in z:
                    if z['attack_bonus'] == 0 and 'damage_dice' not in z:
                        del z['attack_bonus']
                monster_json['special_abilities'][idx] = z
            i.special_abilities_json = json.dumps(monster_json['special_abilities'])
        else:
            i.special_abilities_json = json.dumps("")
        if 'reactions' in monster_json:
            for idx, z in enumerate(monster_json['reactions']):
                if 'attack_bonus' in z:
                    if z['attack_bonus'] == 0 and 'damage_dice' not in z:
                        del z['attack_bonus']
                monster_json['reactions'][idx] = z
            i.reactions_json = json.dumps(monster_json['reactions'])
        else:
            i.reactions_json = json.dumps("")
        if 'legendary_desc' in monster_json:
            i.legendary_desc = monster_json['legendary_desc']
        # import spells array
        if 'spells' in monster_json:
            i.spells_json = json.dumps(monster_json['spells'])
        else:
            i.spells_json=json.dumps("")
        # import legendary actions array
        if 'legendary_actions' in monster_json:
            for idx, z in enumerate(monster_json['legendary_actions']):
                if 'attack_bonus' in z:
                    if z['attack_bonus'] == 0 and 'damage_dice' not in z:
                        del z['attack_bonus']
                monster_json['legendary_actions'][idx] = z
            i.legendary_actions_json = json.dumps(monster_json['legendary_actions'])
        else:
            i.legendary_actions_json = json.dumps("")
        result = _determine_import_result(options, new, exists)
        if result is not ImportResult.SKIPPED:
            i.save()
            if 'spells' in monster_json:
                for spell in monster_json['spells']:
                    self.update_monster(i.slug, spell)
        return result

    def import_plane(self, plane_json, options) -> ImportResult:
        new = False
        exists = False
        if models.Plane.objects.filter(slug=slugify(plane_json['name'])).exists():
            i = models.Plane.objects.get(slug=slugify(plane_json['name']))
            exists = True
        else:
            i = models.Plane(document = self._last_document_imported)
            new = True
        if 'name' in plane_json:
            i.name = plane_json['name']
            i.slug = slugify(plane_json['name'])
        if 'desc' in plane_json:
            i.desc = plane_json['desc']
        result = _determine_import_result(options, new, exists)
        if result is not ImportResult.SKIPPED:
            i.save()
        return result

    def RaceImporter(self, options, json_object):
        skipped, added, updated = (0, 0, 0)
        if bool(options['flush']): models.Subrace.objects.all().delete()
        if bool(options['flush']): models.Race.objects.all().delete()

        for o in json_object:
            new = False
            exists = False
            if models.Race.objects.filter(slug=slugify(o['name'])).exists():
                i = models.Race.objects.get(slug=slugify(o['name']))
                exists = True
            else:
                i = models.Race(document = self._last_document_imported)
                new = True
            if 'name' in o:
                i.name = o['name']
                i.slug = slugify(o['name'])
            if 'desc' in o:
                i.desc = o['desc']
            if 'asi-desc' in o:
                i.asi_desc = o['asi-desc']
            if 'asi' in o:
                i.asi_json = json.dumps(o['asi']) # convert the asi json object into a string for storage.
            if 'age' in o:
                i.age = o['age']
            if 'alignment' in o:
                i.alignment = o['alignment']
            if 'size' in o:
                i.size = o['size']
            if 'speed'in o:
                i.speed_json = json.dumps(o['speed']) # conver the speed object into a string for db storage.
            if 'speed-desc' in o:
                i.speed_desc = o['speed-desc']
            if 'languages' in o:
                i.languages = o['languages']
            if 'vision' in o:
                i.vision = o['vision']
            if 'traits' in o:
                i.traits = o['traits']
                                
            if bool(options['testrun']) or (exists and options['append']):
               skipped += 1
            else:
                i.save()
                if 'subtypes' in o:
                    self.SubraceImporter(options, o['subtypes'], i)
                if new: added += 1
                else: updated += 1

        return _completion_message('Races', added, updated, skipped)
        
    def SubraceImporter(self, options, json_object, parent_race):
        skipped, added, updated = (0, 0, 0)
        #if bool(options['flush']): Subrace.objects.all().delete()
        for o in json_object:
            new = False
            exists = False
            if models.Subrace.objects.filter(slug=slugify(o['name'])).exists():
                i = models.Subrace.objects.get(slug=slugify(o['name']))
                exists = True
            else:
                i = models.Subrace(document = self._last_document_imported, parent_race=parent_race)
                new = True
                if 'name' in o:
                    i.name = o['name']
                    i.slug = slugify(o['name'])
                if 'desc' in o:
                    i.desc = o['desc']
                if 'asi-desc' in o:
                    i.asi_desc = o['asi-desc']
                if 'asi' in o:
                    i.asi_json = json.dumps(o['asi'])
                if 'traits' in o:
                    i.traits = o['traits']    
                if bool(options['testrun']) or (exists and options['append']):
                    skipped += 1
                else:
                    i.save()
                if new: added += 1
                else: updated += 1

        return _completion_message('Subraces', added, updated, skipped)

    def import_section(self, section_json, options) -> ImportResult:
        new = False
        exists = False
        if models.Section.objects.filter(slug=slugify(section_json['name'])).exists():
            i = models.Section.objects.get(slug=slugify(section_json['name']))
            exists = True
        else:
            i = models.Section(document = self._last_document_imported)
            new = True
        if 'name' in section_json:
            i.name = section_json['name']
            i.slug = slugify(section_json['name'])
        if 'desc' in section_json:
            i.desc = section_json['desc']
        if 'parent' in section_json:
            i.parent = section_json['parent']
        result = _determine_import_result(options, new, exists)
        if result is not ImportResult.SKIPPED:
            i.save()
        return result

    def import_spell(self, spell_json, options) -> ImportResult:
        new = False
        exists = False
        if models.Spell.objects.filter(slug=slugify(spell_json['name'])).exists():
            i = models.Spell.objects.get(slug=slugify(spell_json['name']))
            exists = True
        else:
            i = models.Spell(document = self._last_document_imported)
            new = True
        if 'name' in spell_json:
            i.name = spell_json['name']
            i.slug = slugify(spell_json['name'])
        if 'desc' in spell_json:
            i.desc = spell_json['desc']
        if 'higher_level' in spell_json:
            i.higher_level = spell_json['higher_level']
        if 'page' in spell_json:
            i.page = spell_json['page']
        if 'range' in spell_json:
            i.range = spell_json['range']
        if 'components' in spell_json:
            i.components = spell_json['components']
        if 'material' in spell_json:
            i.material = spell_json['material']
        if 'ritual' in spell_json:
            i.ritual = spell_json['ritual']
        if 'duration' in spell_json:
            i.duration = spell_json['duration']
        if 'concentration' in spell_json:
            i.concentration = spell_json['concentration']
        if 'casting_time' in spell_json:
            i.casting_time = spell_json['casting_time']
        if 'level' in spell_json:
            i.level = spell_json['level']
        if 'level_int' in spell_json:
            i.level_int = spell_json['level_int']
        if 'school' in spell_json:
            i.school = spell_json['school']
        if 'class' in spell_json:
            i.dnd_class = spell_json['class']
        if 'archetype' in spell_json:
            i.archetype = spell_json['archetype']
        if 'circles' in spell_json:
            i.circles = spell_json['circles']
        result = _determine_import_result(options, new, exists)
        if result is not ImportResult.SKIPPED:
            i.save()
        return result

    def import_weapon(self, weapon_json, options) -> ImportResult:
        new = False
        exists = False
        if models.Weapon.objects.filter(slug=slugify(weapon_json['name'])).exists():
            i = models.Weapon.objects.get(slug=slugify(weapon_json['name']))
            exists = True
        else:
            i = models.Weapon(document = self._last_document_imported)
            new = True
        if 'name' in weapon_json:
            i.name = weapon_json['name']
            i.slug = slugify(weapon_json['name'])
        if 'category' in weapon_json:
            i.category = weapon_json['category']
        if 'cost' in weapon_json:
            i.cost = weapon_json['cost']
        if 'damage_dice' in weapon_json:
            i.damage_dice = weapon_json['damage_dice']
        if 'damage_type' in weapon_json:
            i.damage_type = weapon_json['damage_type']
        if 'weight' in weapon_json:
            i.weight = weapon_json['weight']
        if 'properties' in weapon_json:
            i.properties_json = json.dumps(weapon_json['properties'])
        result = _determine_import_result(options, new, exists)
        if result is not ImportResult.SKIPPED:
            i.save()
        return result

    def import_armor(self, armor_json, options) -> ImportResult:
        new = False
        exists = False
        if models.Armor.objects.filter(slug=slugify(armor_json['name'])).exists():
            i = models.Armor.objects.get(slug=slugify(armor_json['name']))
            exists = True
        else:
            i = models.Armor(document = self._last_document_imported)
            new = True
        if 'name' in armor_json:
            i.name = armor_json['name']
            i.slug = slugify(armor_json['name'])
        if 'category' in armor_json:
            i.category = armor_json['category']
        if 'cost' in armor_json:
            i.cost = armor_json['cost']
        if 'stealth_disadvantage' in armor_json:
            i.stealth_disadvantage = armor_json['stealth_disadvantage']
        if 'base_ac' in armor_json:
            i.base_ac = armor_json['base_ac']
        if 'plus_dex_mod' in armor_json:
            i.plus_dex_mod = armor_json['plus_dex_mod']
        if 'plus_con_mod' in armor_json:
            i.plus_con_mod = armor_json['plus_con_mod']
        if 'plus_wis_mod' in armor_json:
            i.plus_wis_mod = armor_json['plus_wis_mod']
        if 'plus_flat_mod' in armor_json:
            i.plus_flat_mod = armor_json['plus_flat_mod']
        if 'plus_max' in armor_json:
            i.plus_max = armor_json['plus_max']
        if 'strength_requirement' in armor_json:
            i.strength_requirement = armor_json['strength_requirement']
        result = _determine_import_result(options, new, exists)
        if result is not ImportResult.SKIPPED:
            i.save()
        return result

def _completion_message(
    object_type: str,
    added: int,
    updated: int,
    skipped: int,
) -> str:
    """Return a string describing a completed batch of imports."""
    message = f'Completed loading {object_type}.  '
    message = message.ljust(36)
    message += f'Added:{added}'
    message = message.ljust(48)
    message += f'Updated:{updated}'
    message = message.ljust(60)
    message += f'Skipped:{skipped}'
    return message

def _determine_import_result(
    options: Dict[str, bool],
    new: bool,
    exists: bool,
) -> ImportResult:
    """Check whether an import resulted in a skip, an add, or an update."""
    if options['testrun'] or (exists and options['append']):
        return ImportResult.SKIPPED
    elif new:
        return ImportResult.ADDED
    else:
        return ImportResult.UPDATED
