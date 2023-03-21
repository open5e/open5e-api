from rest_framework.test import APITestCase

# Create your tests here.

class APIRootTest(APITestCase):
    def test_get_root_headers(self):
        response = self.client.get(f'/?format=json')
        # Assert basic headers
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['allow'],'GET, HEAD, OPTIONS')
        self.assertEqual(response.headers['content-type'],'application/json')
        self.assertEqual(response.headers['X-Frame-Options'],'DENY')
        self.assertEqual(response.headers['X-Content-Type-Options'],'nosniff')
        self.assertEqual(response.headers['Referrer-Policy'],'same-origin')
        
    def test_get_root_list(self):
        response = self.client.get(f'/?format=json')
        # Check the response for each of the known endpoints. Two results, one for the name, one for the link.
        self.assertContains(response,'manifest',count=2)
        self.assertContains(response,'spells',count=2)
        self.assertContains(response,'monsters',count=2)
        self.assertContains(response,'documents',count=2)
        self.assertContains(response,'backgrounds',count=2)
        self.assertContains(response,'planes',count=2)
        self.assertContains(response,'sections',count=2)
        self.assertContains(response,'feats',count=2)
        self.assertContains(response,'conditions',count=2)
        self.assertContains(response,'races',count=2)
        self.assertContains(response,'classes',count=2)
        self.assertContains(response,'magicitems',count=2)
        self.assertContains(response,'weapons',count=2)
        self.assertContains(response,'armor',count=2)
        self.assertContains(response,'search',count=2)

    def test_options_root_data(self):
        # Testing the actual content of the response data.
        response = self.client.get(f'/?format=json', REQUEST_METHOD='OPTIONS')
        self.assertEqual(response.json()['name'],'Api Root')
        self.assertEqual(response.json()['description'],'The default basic root view for DefaultRouter')
        self.assertEqual(response.json()['renders'],["application/json","text/html"])
        self.assertEqual(response.json()['parses'],["application/json","application/x-www-form-urlencoded","multipart/form-data"])

class ManifestTestCase(APITestCase):
    def setUp(self):
        from api.management.commands.importer import Importer
        from pathlib import Path
        filepath = 'test_filepath'
        filehash = 'test_hash'
        i = Importer([])
        i.import_manifest(Path(filepath), filehash)

    def test_get_manifest_data(self):
        response = self.client.get(f'/manifest/?format=json')
        # Confirm the basic elements show up.
        self.assertContains(response,'count',count=1)
        self.assertContains(response,'next',count=1)
        self.assertContains(response,'previous',count=1)
        self.assertContains(response,'results',count=1)

        # Confirm the values appear as expected.
        self.assertEqual(response.json()['count'],1)
        self.assertEqual(response.json()['results'][0]['filename'],'test_filepath')
        self.assertEqual(response.json()['results'][0]['type'],'test_filepath')
        self.assertEqual(response.json()['results'][0]['hash'],'test_hash')
        self.assertContains(response,'created_at', count=1)
        
    def test_options_manifest_data(self):
        response = self.client.get(f'/manifest/?format=json', REQUEST_METHOD='OPTIONS')
        self.assertEqual(response.json()['name'],'Manifest List')
        self.assertIn('API endpoint that allows viewing of Manifests.',response.json()['description'])
        self.assertEqual(response.json()['renders'],["application/json","text/html"])
        self.assertEqual(response.json()['parses'],["application/json","application/x-www-form-urlencoded","multipart/form-data"])

