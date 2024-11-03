"""Abstract serializers."""
from rest_framework import serializers

from api_v2 import models


class GameContentSerializer(serializers.HyperlinkedModelSerializer):  

    def remove_unwanted_fields(self, dynamic_params):
        """
        Takes the value of the 'fields', a string of comma-seperated values, 
        and removes all other fields from the serializer
        """
        if fields_to_keep := dynamic_params.pop("fields", None):
            fields_to_keep = set(fields_to_keep.split(","))
            all_fields = set(self.fields.keys())
            for field in all_fields - fields_to_keep:
                self.fields.pop(field, None)

    def get_or_create_dynamic_params(self, child):
        """
        Creates dynamic params on the serializer context if it doesn't already
        exist, then returns the dynamic parameters
        """
        if "dynamic_params" not in self.fields[child]._context:
            self.fields[child]._context.update({"dynamic_params": {}})
        return self.fields[child]._context["dynamic_params"]

    @staticmethod
    def split_param(dynamic_param):
        crumbs = dynamic_param.split("__")
        return crumbs[0], "__".join(crumbs[1:]) if len(crumbs) > 1 else None

    def set_dynamic_params_for_children(self, dynamic_params):
        for param, fields in dynamic_params.items():
            child, child_dynamic_param = self.split_param(param)
            if child in set(self.fields.keys()):
                dynamic_params = self.get_or_create_dynamic_params(child)
                dynamic_params.update({child_dynamic_param: fields})

    @staticmethod
    def is_param_dynamic(p):
        """
        Currently only the 'fields' query param is supported
        """
        return p.endswith("fields")

    def get_dynamic_params_for_root(self, request):
        query_params = request.query_params.items()
        return {k: v for k, v in query_params if self.is_param_dynamic(k)}

    def get_dynamic_params(self):
        """
        When dynamic params get passed down in set_context_for_children
        If the child is a subclass of ListSerializer (has many=True)
        The context must be fetched from ListSerializer Class
        """
        if isinstance(self.parent, serializers.ListSerializer):
            return self.parent._context.get("dynamic_params", {})
        return self._context.get("dynamic_params", {})

    def __init__(self, *args, **kwargs):
        request = kwargs.get("context", {}).get("request")
        super().__init__(*args, **kwargs)

        # "request" doesn't exist on the child serializers, or when generating OAS spec
        is_root = bool(request)
        if is_root:
            if request.method != "GET":
                return

            if depth:= request.query_params.get('depth'):
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

            # 
            dynamic_params = self.get_dynamic_params_for_root(request)
            self._context.update({"dynamic_params": dynamic_params})
    
    def to_representation(self, *args, **kwargs):
        if dynamic_params := self.get_dynamic_params().copy():
            self.remove_unwanted_fields(dynamic_params)
            self.set_dynamic_params_for_children(dynamic_params)

        return super().to_representation(*args, **kwargs)

    class Meta:
        abstract = True