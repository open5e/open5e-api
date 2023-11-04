"""Abstract serializers."""
from rest_framework import serializers

from api_v2 import models


class GameContentSerializer(serializers.HyperlinkedModelSerializer):

    # Adding dynamic "fields" qs parameter.
    def __init__(self, *args, **kwargs):
        # Add default fields variable.

        # Instantiate the superclass normally
        super(GameContentSerializer, self).__init__(*args, **kwargs)

        # The request doesn't exist when generating an OAS file, so we have to check that first
        if self.context['request']:
            fields = self.context['request'].query_params.get('fields')
            if fields:
                fields = fields.split(',')
                # Drop any fields that are not specified in the `fields` argument.
                allowed = set(fields)
                existing = set(self.fields.keys())
                for field_name in existing - allowed:
                    self.fields.pop(field_name)

            depth = self.context['request'].query_params.get('depth')
            if depth:
                try:
                    depth_value = int(depth)
                    if depth_value > 0 and depth_value < 3:
                        # This value going above 1 could cause performance issues.
                        # Limited to 1 and 2 for now.
                        self.Meta.depth = depth_value
                        # Depth does not reset by default on subsequent requests with malformed urls.
                    else:
                        self.Meta.depth = 0
                except ValueError:
                    pass  # it was not castable to an int.
            else:
                self.Meta.depth = 0 #The default.

    class Meta:
        abstract = True
