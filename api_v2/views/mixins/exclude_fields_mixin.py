class ExcludeFieldsMixin:
  def get_serializer_class(self):

    # Handle other mixins that might also override get_serializer_class
    if hasattr(super(), 'get_serializer_class'):
      serializer_class = super().get_serializer_class()
    else:
      serializer_class = getattr(self, 'serializer_class')

    # just return the regular serializer if there is no request
    if not hasattr(self, 'request') or not hasattr(self.request, 'query_params'):
      return serializer_class

    exclude_fields = self.request.query_params.get('exclude', '').split(',')

    if not exclude_fields:
      return serializer_class
    
    # create a new serializer with 'exclude_fields' removed and return it
    class DynamicSerializer(serializer_class):
      def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        excluded_fields = []
        for field in exclude_fields:
          if field in self.fields:
            self.fields.pop(field)
            excluded_fields.append(field)

    return DynamicSerializer
    
