"""Serializer for the BackgroundBenefit and Background models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class BackgroundBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BackgroundBenefit
        fields = ['name','desc','type']


class BackgroundSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    benefits = BackgroundBenefitSerializer(
        many=True
    )

    class Meta:
        model = models.Background
        fields = '__all__'
