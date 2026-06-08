class EagerLoadingMixin:
  """
  Mixin to apply eager loading optimisations to a ViewSet.
  
  Handles the running of `select_related()` (for ForeignKey fields) and 
  `prefetch_related()` (from ManyToMany/reverse relationships) queryset methods
  to allow developers to solve N+1 problems on Open5e endpoints.
  
  ## Usage
  1. Make sure your ViewSet inherits from `EagerLoadingMixin` before its base
  class (ie. ReadOnlyModelViewSet).
  2. Re-define `select_related_fields` and `prefetch_related_fields` lists on 
  the child ViewSet to specify relationships to select related / pre-fetch.
  
  ## Usage Example
  ```
    class CreatureViewSet(EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
      queryset = models.Creature.objects.all().order_by('pk')
      serializer_class = serializers.CreatureSerializer
      filterset_class = CreatureFilterSet
      select_related_fields = []   # ForeignKey relations to optimise with select_related()      
      prefetch_related_fields = [] # ManyToMany/reverse relations to optimise with prefetch_related()
  ```
  """

  # Override these lists in child views 
  select_related_fields = []
  prefetch_related_fields = []

  def get_queryset(self):
    """
    Builds the queryset with optimised eager loading based on the requested and excluded fields.
    """
    queryset = super().get_queryset()

    # Check fields included or excluded via query parameter. We use this data 
    # so that we only eagerly load fields actually returned by the API.
    requested_fields = self.parse_requested_fields()
    excluded_fields = self.parse_excluded_fields()
    
    filtered_select_fields = self.filter_fields(self.select_related_fields, requested_fields, excluded_fields)
    filtered_prefetch_fields = self.filter_fields(self.prefetch_related_fields, requested_fields, excluded_fields)

    return queryset \
      .select_related(*filtered_select_fields) \
      .prefetch_related(*filtered_prefetch_fields)
    
  def parse_requested_fields(self):
    """
    Parses the 'fields' query param into a list of requested field paths.
    """
    requested_fields = self.request.query_params.get('fields', '')
    requested_fields = requested_fields.split(',')
    requested_fields = [field for field in requested_fields if field]
    return requested_fields

  def parse_excluded_fields(self):
    """
    Parses 'exclude' query params into a flat list of field paths for use in eager loading
    """
    excluded_fields = []
    for key, value in self.request.query_params.items():
      if key == 'exclude':
        excluded_fields += value.split(',')
      elif key.endswith('__exclude'):
        prefix = key.removesuffix('__exclude')
        excluded_fields += [f'{prefix}__{field}' for field in value.split(',')]
    return excluded_fields

  def filter_fields(self, related_fields, requested_fields=None, excluded_fields=None):
    """
    Filters 'related_fields' according to whether they are included in 
    'requested_fields' or 'excluded_fields'. Used to remove fields from eager 
    loading if they are not returned by API call to avoid unnecessary DB calls
    """
    # avoids mutable default argument issues: set to empty list if param missing
    requested_fields = requested_fields or []
    excluded_fields = excluded_fields or []

    def field_matches(field, targets):
      # Returns True if 'field' equals any 'target', or is a child path of one
      return any(field == target or field.startswith(target + '__') for target in targets)

    if requested_fields:
      related_fields = [
        related_field for related_field in related_fields
        if field_matches(related_field, requested_fields)
      ]

    if excluded_fields:
      related_fields = [
        related_field for related_field in related_fields
        if not field_matches(related_field, excluded_fields)
      ]

    return related_fields
