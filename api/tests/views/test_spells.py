"""Tests for the spells endpoint."""
import pytest
from rest_framework import status
from django.test import Client

from api.models import Spell


@pytest.mark.django_db
class TestSpellsView:
    @staticmethod
    def test_spell_view_200(client: Client, spell: Spell):
        url = "/spells/"
        response = client.get(url)

        # Confirm that the response is a 200
        assert response.status_code == status.HTTP_200_OK

        # Confirm the length of the results returned on the response
        assert len(response.json()["results"]) == 1


@pytest.fixture
def spell(document):
    data = {
        "slug": "ray-of-sickness",
        "name": "Ray of Sickness",
        "desc": "A ray of green light appears at your fingertip, arcing towards a target within range.\n\nMake a ranged spell attack against the target. On a hit, the target takes 2d8 poison damage and must make a Constitution saving throw. On a failed save, it is also poisoned until the end of your next turn.\n\n*(This Open5e spell replaces a like-named non-SRD spell from an official source.*",
        "document": document,
        "created_at": "2023-05-17 14:25:56.609742",
        "page_no": None,
        "page": "",
        "spell_level": 1,
        "dnd_class": "Sorcerer, Wizard",
        "school": "Necromancy",
        "casting_time": "1 action",
        "range": "60 feet",
        "target_range_sort": 60,
        "requires_verbal_components": True,
        "requires_somatic_components": True,
        "requires_material_components": False,
        "material": "",
        "higher_level": "When you cast this spell using a spell slot of 2nd level or higher, the damage increases by 1d8 for each slot level above 1st.",
        "can_be_cast_as_ritual": False,
        "duration": "Instantaneous",
        "requires_concentration": False,
        "archetype": "",
        "circles": "",
        "route": "spells/",
    }
    _spell = Spell.objects.create(**data)
    return _spell
