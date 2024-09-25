""" Serializer for the Rule model """

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class RuleSerializer(serializers.ModelSerializer):
  class Meta:
    model = models.Rule
    fields = '__all__'