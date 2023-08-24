from django.db.models.query import InstanceCheckMeta
from rest_framework.serializers import ModelSerializer
from . import models
from .models import Training
# from accounts.models import User, Company
from rest_framework.serializers import SerializerMethodField
from rest_framework.serializers import PrimaryKeyRelatedField
from rest_framework.serializers import ValidationError
from rest_framework.response import Response
from rest_framework import serializers

from .serializers import *

from django.utils import timezone




class registerincidentSerializer(ModelSerializer):

    class Meta:
        model = Training
        fields = [
            'title',
            'description',
            'period_date',
        ]


    def create(self, validated_data):
            return Training.objects.create(**validated_data)

    # def update(self, instance, validated_data):
    #         instance.title = validated_data.get('title', instance.register_title)
    #         instance.text = validated_data.get('text', instance.text)

    #         if validated_data.get('period_date', instance.period_date2):
    #             print("うごている？", validated_data.get('period_date', instance.period_date))
    #             period_date = validated_data.get('period_date', instance.period_date2)
    #             # period_date.strftime('%Y-%m%d %H:%M:%S')
    #             period_date.strftime('%Y-%m%d')
    #             print("うごいている？２", period_date)
    #             instance.period_date = period_date

    #         instance.save()

    #         return instance
