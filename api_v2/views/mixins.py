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
  
  ## Example
  ```
    # EagerLoadingMixin inhertired before base-case
    class CreatureViewSet(EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
      queryset = models.Creature.objects.all().order_by('pk')
      serializer_class = serializers.CreatureSerializer
      filterset_class = CreatureFilterSet

      # ForeignKey relations to optimise with select_related()
      select_related_fields = []
      # ManyToMany / reverse relations to optimise with prefetch_related()
      prefetch_related_fields = []
  ```
  """

  # Override these lists in child views 
  select_related_fields = [] # ForeignKeys to optimise
  prefetch_related_fields = [] # ManyToMany & reverse relationships to prefetch

  def get_queryset(self):
    """Override DRF's default get_queryset() method to apply eager loading"""
    queryset = super().get_queryset()
    request = self.request

    # Get query parameters
    requested_fields = request.query_params.get('fields', '')
    depth = int(request.query_params.get('depth', 0))

    if requested_fields:
      requested_fields = set(requested_fields.split(','))
    else:
      # If no fields requested, apply all opitmisations
      requested_fields = set(self.select_related_fields + self.prefetch_related_fields)

    # Filter fields based on on which have been requested
    select_fields = [field for field in self.select_related_fields if field in requested_fields]
    prefetch_fields = [field for field in self.prefetch_related_fields if field in requested_fields]
    
    # Apply optimisations
    if select_fields:
      queryset = queryset.select_related(*select_fields)
    if prefetch_fields:
      queryset = queryset.prefetch_related(*prefetch_fields)

    return queryset