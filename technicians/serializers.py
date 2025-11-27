from rest_framework import serializers
from .models import TechnicianAvailability, TechnicianSkill, VerificationDocument
from users.serializers.user_serializers import UserSerializer

class TechnicianAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicianAvailability
        fields = '__all__'

class TechnicianSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicianSkill
        fields = '__all__'

class VerificationDocumentSerializer(serializers.ModelSerializer):
    technician_user = UserSerializer(read_only=True)

    class Meta:
        model = VerificationDocument
        fields = '__all__'
