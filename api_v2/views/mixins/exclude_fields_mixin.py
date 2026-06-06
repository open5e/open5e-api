class ExcludeFieldsMixin:
  """
  This Mixin supports dynamically excluding returned fields of serializers that
  inherit from it via the `?exclude` query parameter. 
  
  Syntactically similar to the default `?field` DRF query parameter. Nested 
  fields are similarly excluded via the '__' operator (see Examples).
  
  ## Usage
  1. Make sure your ViewSet inherits from `ExcludeFieldsMixin` before its base
  class (ie. ReadOnlyModelViewSet).
  2. Pass exclude params in the request query string to remove fields from the response.

  # Exclude top-level fields
  GET /v2/creatures/?exclude=traits,actions

  # Exclude nested fields
  GET /v2/creatures/?actions__exclude=attacks
  """

  def get_serializer_class(self):

    # Handle other mixins that might also override get_serializer_class
    if hasattr(super(), 'get_serializer_class'):
      serializer_class = super().get_serializer_class()
    else:
      serializer_class = getattr(self, 'serializer_class')

    # Return base serializer if there is no request. This stops calculation of
    # excluded fields for nested serializers, avoiding unnecessary computing.
    if not hasattr(self, 'request') or not hasattr(self.request, 'query_params'):
      return serializer_class

    # Iterates over params, scans for any 'exclude' or '<field>_exclude' keys 
    # and builds a dict mapping API field paths to lists of field to remove from each
    # e.g. '?exclude=id&document__exclude=permalink' becomes:
    # { '': ['id'], 'document': ['permalink'] }
    fields_to_exclude = {}
    for key, value in self.request.query_params.items():
      if key == 'exclude':
        fields_to_exclude[''] = value.split(',')
      elif key.endswith('__exclude'):
        fields_to_exclude[key.removesuffix('__exclude')] = value.split(',')

    if not fields_to_exclude:
      return serializer_class

    # Walks the serializer tree removing fields at each level flagged for removal.
    # 'path' tracks where we are in the tree, which we use as a key to index into 
    # 'fields_to_exclude' to check which fields to remove. We then recurse into 
    # nested serializers and apply the same logic.
    def strip_excluded_fields(fields, path=''):
      for excluded_field in fields_to_exclude.get(path, []):
        fields.pop(excluded_field, None)
      for field_name, field in fields.items():
        nested_serializer = getattr(field, 'child', field)
        if hasattr(nested_serializer, 'fields'):
          nested_path = f'{path}__{field_name}' if path else field_name
          strip_excluded_fields(nested_serializer.fields, nested_path)

    class DynamicSerializer(serializer_class):
      def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        strip_excluded_fields(self.fields)

    return DynamicSerializer
