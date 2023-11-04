import requests

from approvaltests import verify_as_json, Options,  DiffReporter


class TestAPIRoot:
    """Test cases for testing the / root of the API."""

    def _verify(self, endpoint: str):
        response = requests.get(endpoint, allow_redirects=True, headers = {'Accept': 'application/json'}).json()

        verify_as_json(response, options=Options().with_reporter(DiffReporter()))

    def test_root(self):
        self._verify(f"http://localhost:8000/")

    def test_magic_missile(self):
        self._verify(f"http://localhost:8000/spells/magic-missile/")

    def test_monsters(self):
        self._verify(f"http://localhost:8000/monsters/")
