from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User
from django.contrib.auth import authenticate

class GoogleLoginView(APIView):
    def post(self, request):
        id_token_str = request.data.get('id_token')

        if not id_token_str:
            return Response({'error': 'ID token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Specify the CLIENT_ID of the app that accesses the backend:
            client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
            
            # Verify the ID token
            idinfo = id_token.verify_oauth2_token(id_token_str, requests.Request(), client_id)

            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            # ID token is valid. Get the user's Google Account ID and profile information.
            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')

            user, created = User.objects.get_or_create(email=email)

            if created:
                user.first_name = first_name
                user.last_name = last_name
                user.set_unusable_password() # Google authenticated users don't need a password
                user.save()
            
            # Authenticate the user to get Django's user object
            # Note: For social logins, you might need a custom authentication backend
            # For simplicity, we'll assume the user is "authenticated" if found/created
            # and directly generate tokens.
            
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            # Invalid token
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'An unexpected error occurred: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
