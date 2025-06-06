from rest_framework import serializers
from api_v2 import models
from .abstracts import GameContentSerializer
from .document import DocumentSummarySerializer

class ServiceSerializer(GameContentSerializer):
  key = serializers.ReadOnlyField()
  document = DocumentSummarySerializer()

  class Meta:
    model = models.Service
    fields = '__all__'