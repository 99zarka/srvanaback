from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from users.models import User
from users.serializers import UserRegistrationSerializer, UserSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens for the newly registered user
        token_serializer = TokenObtainPairSerializer(data={
            'email': request.data['email'],
            'password': request.data['password']
        })
        token_serializer.is_valid(raise_exception=True)
        tokens = token_serializer.validated_data

        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "message": "User Created Successfully.",
            "tokens": tokens
        }, status=status.HTTP_201_CREATED)
