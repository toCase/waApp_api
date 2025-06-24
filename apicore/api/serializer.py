from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class StaffSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Staff
        fields = [
            'id',
            'user',
            'user_id',
            'title',
            'position',
            'link',
            'bg_color',
            'fg_color',
            'description',
            'is_active',
        ]

class ScheduleSerializer(serializers.ModelSerializer):
    intervals_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ScheduleTemplate
        fields = '__all__'

class IntervalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateInterval
        fields = ['id', 'start_time', 'end_time', 'slot_size']