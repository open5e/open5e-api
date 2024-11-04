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
            if child in self.fields.keys():
                # Get dynamic parameters for child serializer and update
                child_dynamic_params = self.get_or_create_dynamic_params(child)
                child_dynamic_params.update({child_dynamic_param: fields})

                # Overwrite existing params to remove 'fields' inherited from parent serializer
                self.fields[child]._context['dynamic_params'] = {
                    **child_dynamic_params,
                }

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

    def handle_depth_serialization(self, instance, representation):
        """
        Handles the serialization of fields based on the current depth 
        compared to the maximum allowed depth. This function modifies 
        the representation to include only URLs for nested serializers 
        when the maximum depth is reached.
        """
        max_depth = self._context.get("max_depth", 0)
        current_depth = self._context.get("current_depth", 0)

        # if we reach the maximum depth, nested serializers return their pk
        if current_depth >= max_depth:
            for field_name, field in self.fields.items():
                if isinstance(field, serializers.HyperlinkedModelSerializer):
                    nested_representation = representation.get(field_name)
                    if nested_representation and "url" in nested_representation:
                        representation[field_name] = nested_representation["url"]
        
        # otherwise, pass depth to children serializers
        else:
            for field_name, field in self.fields.items():
                if isinstance(field, GameContentSerializer):
                    nested_instance = getattr(instance, field_name)
                    nested_serializer = field.__class__(nested_instance, context={
                        **self._context,
                        "current_depth": current_depth + 1,
                        "max_depth": max_depth,
                    })
                    # Ensure dynamic params are specific to the child serializer
                    child_dynamic_params = self.get_or_create_dynamic_params(field_name)
                    nested_serializer._context['dynamic_params'] = child_dynamic_params
                    representation[field_name] = nested_serializer.data
                    
        return representation

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

        if dynamic_params := self.get_dynamic_params().copy():
            self.remove_unwanted_fields(dynamic_params)
            self.set_dynamic_params_for_children(dynamic_params)

        representation = super().to_representation(instance)

        representation = self.handle_depth_serialization(instance, representation)

        return representation


    class Meta:
        abstract = True