from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.viewsets import ReadOnlyModelViewSet

class CacheMixin:
  @method_decorator(cache_page(None))
  def dispatch(self, request, *args, **kwargs):
    return super().dispatch(request, *args, **kwargs)