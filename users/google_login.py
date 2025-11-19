from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User, UserType
from users.serializers.user_serializers import UserSerializer # Import UserSerializer
from django.contrib.auth import authenticate

class GoogleLoginView(APIView):
    def post(self, request):
        id_token_str = request.data.get('id_token')

        if not id_token_str:
            return Response({'error': 'ID token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Specify the CLIENT_ID of the app that accesses the backend:
            client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
            
            # Verify the ID token with a clock skew tolerance of 1 day (86400 seconds)
            idinfo = id_token.verify_oauth2_token(id_token_str, requests.Request(), client_id, clock_skew_in_seconds=86400)

            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            # ID token is valid. Get the user's Google Account ID and profile information.
            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')

            # Ensure a default user type exists or create it
            default_user_type, _ = UserType.objects.get_or_create(user_type_name='client')

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'user_type': default_user_type, # Assign default user type
                }
            )

            if created:
                user.set_unusable_password() # Google authenticated users don't need a password
                user.save() # Save is needed if defaults were used to set non-email fields
            else:
                # If user already exists, ensure first_name and last_name are updated if available
                # This handles cases where a user might log in with Google for the first time
                # after having an account created manually or through another social provider
                if user.first_name == '' and first_name:
                    user.first_name = first_name
                if user.last_name == '' and last_name:
                    user.last_name = last_name
                # Ensure user_type is set if it somehow got unset or wasn't set on creation
                if not user.user_type:
                    user.user_type = default_user_type
                user.save() # Save any updates to existing user
            
            # Authenticate the user to get Django's user object
            # Note: For social logins, you might need a custom authentication backend
            # For simplicity, we'll assume the user is "authenticated" if found/created
            # and directly generate tokens.
            
            refresh = RefreshToken.for_user(user)
            user_data = UserSerializer(user).data # Serialize user data
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': user_data, # Include user data in the response
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            # Invalid token
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'An unexpected error occurred: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
