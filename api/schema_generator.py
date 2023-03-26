from rest_framework.schemas.openapi import SchemaGenerator
from rest_framework.schemas.openapi import AutoSchema

# Adds additional metadata onto an OAS operation. Attach this to your view and provide the necessary constructor args.
class CustomSchema(AutoSchema):
    def __init__(self, **kwargs):
        self.extra_info = {}

        if 'query' in kwargs:
            self.extra_info['query'] = kwargs.pop("query")

        if 'summary' in kwargs:
            self.extra_info['summary'] = kwargs.pop("summary")

        if 'tags' in kwargs:
            self.extra_info['tags'] = kwargs.pop("tags")

        super().__init__(**kwargs)

    def get_operation(self, path, method):
        oldOperation = super().get_operation(path, method)

        # I can't find a version of DRF that support summaries
        oldOperation['summary'] = self.extra_info['summary'][path]

        # Future versions of DRF support tags
        oldOperation['tags'] = self.extra_info['tags']

        # I can't find any way to improve the documentation of query params, so we do it here.
        if 'query' in self.extra_info:
            fix_query_params(oldOperation, self.extra_info['query'])

        return oldOperation

# Iterates over the operations query params and adds the description as defined in the schema view
def fix_query_params(operation, query_params):
    if not query_params:
        return

    for param in operation['parameters']:
        if param['in'] == 'query' and param['name'] in query_params:
            param['description'] = query_params[param['name']]

# Adds additional metadata onto the OAS schema. If you need to manipulate any OAS fields that exist outside of a single operation, this is where you do it.
class Open5eSchemaGenerator(SchemaGenerator):
    def __init__(self, **kwargs):
        super().__init__(
            'Open5e',
            None,
            'The Open5e API includes all monsters and spells from the SRD and other OGL sources as well as a search API, so you can access any part of the SRD from your app or website.'
        )

    def get_schema(self, *args, **kwargs):
        schema = super().get_schema(*args, **kwargs)
        schema['servers'] =[
            {
            "url": "https://api.open5e.com/",
            "description": "Open5e"
            }
        ]
        # This isn't a real endpoint, so we remove it from the schema
        schema['paths'].pop('/search/{id}/')
        return schema
