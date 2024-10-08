""" Serializer for the Rule model """

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class RuleSerializer(GameContentSerializer):
  class Meta:
    model = models.Rule
    fields = '__all__'

class RuleSetSerializer(GameContentSerializer):
  class Meta:
    model = models.RuleSet
    fields = ['name', 'key', 'document', 'desc', 'rules']