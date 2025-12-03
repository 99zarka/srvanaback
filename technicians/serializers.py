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
    # technician_user = UserSerializer(read_only=True) # Removed to allow setting technician_user during creation

    class Meta:
        model = VerificationDocument
        fields = '__all__'
        # Ensure technician_user is explicitly writable if not using default behavior
        # extra_kwargs = {'technician_user': {'required': True, 'allow_null': False}}
