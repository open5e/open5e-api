"""Abstract serializers."""
from rest_framework import serializers

from api_v2 import models

class GameContentSerializer(serializers.HyperlinkedModelSerializer):  

    def remove_unwanted_fields(self, dynamic_params):
        """
        Takes the value of the 'fields', a string of comma-separated values, 
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
        """
        Passes nested dynamic params to child serializer.
        """
        for param, fields in dynamic_params.items():
            child, child_dynamic_param = self.split_param(param)
            if child in set(self.fields.keys()):
                dynamic_params = self.get_or_create_dynamic_params(child)
                dynamic_params.update({child_dynamic_param: fields})

    @staticmethod
    def is_param_dynamic(p):
        return p.endswith("fields")

    def get_dynamic_params_for_root(self, request):
        query_params = request.query_params.items()
        return {k: v for k, v in query_params if self.is_param_dynamic(k)}

    def get_dynamic_params(self):
        if isinstance(self.parent, serializers.ListSerializer):
            return self.parent._context.get("dynamic_params", {})
        return self._context.get("dynamic_params", {})

    def __init__(self, *args, **kwargs):
        request = kwargs.get("context", {}).get("request")
        super().__init__(*args, **kwargs)

        if request:
            self._context["max_depth"] = int(request.query_params.get("depth", 0))
            dynamic_params = self.get_dynamic_params_for_root(request)
            self._context.update({"dynamic_params": dynamic_params})

    def to_representation(self, instance):
        max_depth = self._context.get("max_depth", 0)
        current_depth = self._context.get("current_depth", 0)

        # Process dynamic parameters for filtering fields
        if dynamic_params := self.get_dynamic_params().copy():
            self.remove_unwanted_fields(dynamic_params)
            self.set_dynamic_params_for_children(dynamic_params)

        # Collect only the fields that need to be included in the representation
        representation = super().to_representation(instance)

        if current_depth >= max_depth:
            # Remove fields that are HyperlinkedModelSerializers (nested fields)
            for field_name, field in self.fields.items():
                if isinstance(field, serializers.HyperlinkedModelSerializer):
                    # Check if the nested field has a 'url' attribute in the representation
                    nested_representation = representation.get(field_name)
                    if nested_representation and "url" in nested_representation:
                        # Replace the entire nested structure with the URL field
                        representation[field_name] = nested_representation["url"]
        else:
            # Update depth level in children
            for field_name, field in self.fields.items():
                if isinstance(field, GameContentSerializer):
                    field._context["current_depth"] = current_depth + 1

        return representation

    class Meta:
        abstract = True