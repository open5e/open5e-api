"""Abstract serializers."""
from rest_framework import serializers

from api_v2 import models


class GameContentSerializer(serializers.HyperlinkedModelSerializer):

    def remove_unwanted_fields(self, fields_to_keep):
        fields_to_keep = set(fields_to_keep.split(","))
        all_fields = set(self.fields.keys())
        for field in all_fields - fields_to_keep:
            self.fields.pop(field, None)
    

    # Adding dynamic "fields" qs parameter.
    def __init__(self, *args, **kwargs):

        request = kwargs.get("context", {}).get("request")
        # Instantiate the superclass normally
        super(GameContentSerializer, self).__init__(*args, **kwargs)

        # request only exists on root, not on nested queries or when generating OAS file
        is_root = bool(request)

        if is_root:
            fields = request.query_params.get('fields')
            if fields:
                self.remove_unwanted_fields(fields)

            depth = request.query_params.get('depth')
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
