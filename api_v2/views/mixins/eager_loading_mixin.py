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
    queryset = super().get_queryset()
    requested_fields = self.request.query_params.get('fields', '').split(',')
    filtered_select_fields = self.filter_fields(self.select_related_fields, requested_fields)
    filtered_prefetch_fields = self.filter_fields(self.prefetch_related_fields, requested_fields)

    return queryset \
      .select_related(*filtered_select_fields) \
      .prefetch_related(*filtered_prefetch_fields)

  def filter_fields(self, related_fields, requested_fields):
    """
    Filters'related_fields' according to whether they are included in 
    'requested_fields'. Used to remove fields from eager loading if they are
    not requested (and thus not returned by API), avoiding unnecessary DB calls
    """
    if not any(requested_fields):
      return related_fields
    return [
      related_field for related_field in related_fields
      if any(related_field == req or related_field.startswith(req + '__') for req in requested_fields)
    ]