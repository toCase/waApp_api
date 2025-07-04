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

class StaffShortSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()

class StaffScheduleSerializer(serializers.Serializer):
    staff = StaffShortSerializer()
    days = serializers.ListField(child=serializers.IntegerField())

class WorkslotListSerializer(serializers.ModelSerializer):
    appointment_id = serializers.SerializerMethodField()
    client_id = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    appointment_note  = serializers.SerializerMethodField()
    appointment_status = serializers.SerializerMethodField()
    appointment_rating = serializers.SerializerMethodField()

    class Meta:
        model = WorkSlot
        fields = [
            'id',
            'start_time',
            'end_time',
            'is_blocked',
            'appointment_id',
            'client_id',
            'client_name',
            'appointment_note',
            'appointment_status',
            'appointment_rating'
        ]

    def get_appointment_id(self, obj):
        return obj.appointment.id if hasattr(obj, 'appointment') else None

    def get_client_id(self, obj):
        if hasattr(obj, 'appointment') and obj.appointment.client:
            return obj.appointment.client.id
        return None

    def get_client_name(self, obj):
        if hasattr(obj, 'appointment') and obj.appointment.client:
            return obj.appointment.client.name
        return None

    def get_appointment_note(self, obj):
        return obj.appointment.notes if hasattr(obj, 'appointment') else None

    def get_appointment_status(self, obj):
        return obj.appointment.status if hasattr(obj, 'appointment') else None

    def get_appointment_rating(self, obj):
        return obj.appointment.rating if hasattr(obj, 'appointment') else None