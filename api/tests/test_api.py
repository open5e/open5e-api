import requests

from approvaltests import verify_as_json, Options,  DiffReporter

API_BASE = f"http://localhost:8000"

class TestAPIRoot:
    """Test cases for testing the / root of the API."""

    def _verify(self, endpoint: str):
        response = requests.get(API_BASE + endpoint, allow_redirects=True, headers = {'Accept': 'application/json'}).json()

        verify_as_json(response, options=Options().with_reporter(DiffReporter()))

    def test_root(self):
        self._verify(f"/")

    # specific tests like these should be aimed at spots where there have been bugs before, to prevent regression.
    def test_magic_missile(self):
        self._verify(f"/spells/magic-missile/")

    # enpoint tests ensure the basic structure and count of the objects does not change by accident
    def test_monsters(self):
        self._verify(f"/monsters/")
