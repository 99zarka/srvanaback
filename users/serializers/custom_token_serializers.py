from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from users.serializers.user_serializers import UserSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        # ... add any other user fields you want in the token
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user # The user is available after super().validate()
        if user:
            user_data = UserSerializer(user).data
            data['user'] = user_data
        return data
