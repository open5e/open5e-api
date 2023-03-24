from rest_framework.schemas.openapi import SchemaGenerator
from rest_framework.schemas.openapi import AutoSchema

# Adds additional metadata onto an OAS operation. If you want to augment any endpoints you add it here, and on the endpoint.
class CustomSchema(AutoSchema):
    def __init__(self, **kwargs):
        self.extra_info = {
            "summary": kwargs.pop("summary"),
            "tags": kwargs.pop("tags")
        }

        super().__init__(**kwargs)

    def get_operation(self, path, method):
        # add extra_info to the operation
        oldOperation = super().get_operation(path, method)
        oldOperation['summary'] = self.extra_info['summary'][path]
        oldOperation['tags'] = self.extra_info['tags']
        return oldOperation

# Adds additional metadata onto the OAS schema. If you need to manipulate any OAS fields that exist outside of a single operation, this is where you do it.
class Open5eSchemaGenerator(SchemaGenerator):
    def __init__(self, **kwargs):
        super().__init__(
            'Open 5e',
            None,
            'The Open5e API includes all monsters and spells from the SRD and other OGL sources as well as a search API, so you can easily access any part of the SRD from your app or website.'
        )

    def get_schema(self, *args, **kwargs):
        schema = super().get_schema(*args, **kwargs)
        schema['servers'] =[
			{
			"url": "https://api.open5e.com/",
			"description": "Open 5e"
			}
		]
        return schema
