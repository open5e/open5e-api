class EagerLoadingMixin:
  """
  Mixin to apply eager loading optimisations to a ViewSet.
  
  Dynamically applies `selected_related()` for ForeignKey fields and 
  `prefetch_related()` from ManyToMany/reverse relationships. This improves 
  query efficiency and prevents N+1 problems
  
  ## Usage
  1. Make sure your ViewSet inherits from `EagerLoadingMixin` before its base
  class (ie. ReadOnlyModelViewSet).
  2. Re-define `select_related_fields` and `prefetch_related_fields` lists on 
  the child ViewSet to specify relationships to optimise.
  
  ## Usage Example
  ```
    # EagerLoadingMixin inhertired before base-case
    class CreatureViewSet(EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
      queryset = models.Creature.objects.all().order_by('pk')
      serializer_class = serializers.CreatureSerializer
      filterset_class = CreatureFilterSet

      select_related_fields = []   # ForeignKey relations to optimise with select_related()      
      prefetch_related_fields = [] # ManyToMany/reverse relations to optimise with prefetch_related()
  ```
  """

  # Override these lists in child views 
  select_related_fields = [] # ForeignKeys to optimise
  prefetch_related_fields = [] # ManyToMany & reverse relationships to prefetch

  def get_queryset(self):
    """Override DRF's default get_queryset() method to apply eager loading"""
    queryset = super().get_queryset()

    # Get query parameters from request
    requested_fields = self.request.query_params.get('fields', '').split(',')
    depth = int(self.request.query_params.get('depth', 0))

    # if no fields are passed via query param, select/prefetch all fields defined on the view
    if not requested_fields:
      queryset = queryset.select_related(*self.select_related_fields)
      queryset = queryset.prefetch_related(*self.prefetch_related_fields)
      return queryset
    
    # filter selected fields against fields requested by user via query params 
    # this stops Django prefetching data that isn't even returned by this view
    select_fields = []
    for field_to_select in self.select_related_fields:
      if any(field_in_request in field_to_select for field_in_request in requested_fields):
        select_fields.append(field_to_select)
    
    # filter prefetch fields against fields requested by user via query params
    # this stops Django prefetching data that isn't even returned by this view
    prefetch_fields = []
    for field_to_prefetch in self.prefetch_related_fields:
      if any(field_in_request in field_to_prefetch for field_in_request in requested_fields):
        prefetch_fields.append(field_to_prefetch)

    # Apply filtered optimisations
    queryset = queryset.select_related(*select_fields)
    queryset = queryset.prefetch_related(*prefetch_fields)
    return queryset