"""Viewset and Filterset for the CharacterClass Serializers."""
from rest_framework import viewsets

from api_v2 import models
from api_v2 import serializers



class CharacterClassViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of backgrounds.
    retrieve: API endpoint for returning a particular background.
    """
    queryset = models.CharacterClass.objects.all().order_by('pk')
    serializer_class = serializers.CharacterClassSerializer

