import requests

from approvaltests import verify_as_json, Options,  DiffReporter
from typing import Callable

API_BASE = f"http://localhost:8000"

class TestObjects:

    def _verify(self, endpoint: str, transformer: Callable[[dict], None] = None):
        response = requests.get(API_BASE + endpoint, allow_redirects=True, headers = {'Accept': 'application/json'}).json()
        if transformer:
            transformer(response)
        verify_as_json(response, options=Options().with_reporter(DiffReporter()))

    # /ITEMS ENDPOINT
    def test_item_example(self):
        path="/v2/items/srd_apparatus-of-the-crab/"
        self._verify(path)

    def test_item_melee_weapon_example(self):
        path="/v2/items/srd_shortsword/"
        self._verify(path)

    def test_item_ranged_weapon_example(self):
        path="/v2/items/srd_longbow/"
        self._verify(path)

    def test_item_armor_example(self):
        path="/v2/items/srd_splint-armor/"
        self._verify(path)

    # /ITEMSETS ENDPOINT
    def test_item_set_example(self):
        path="/v2/itemsets/arcane-focuses/"
        self._verify(path)

    # /ITEMCATEGORIES ENDPOINT
    def test_item_category_example(self):
        path="/v2/itemcategories/weapon/"
        self._verify(path)
