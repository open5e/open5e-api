"""Serializer for the BackgroundBenefit and Background models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class BenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Benefit
        fields = ['name','desc','type']


class BackgroundSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    benefits = BenefitSerializer(
        many=True
    )

    class Meta:
        model = models.Background
        fields = '__all__'
