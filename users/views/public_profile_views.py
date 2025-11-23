from rest_framework import generics, permissions
from users.models import User
from users.serializers.user_serializers import PublicUserSerializer # Import PublicUserSerializer

class PublicProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = PublicUserSerializer # Use the PublicUserSerializer
    permission_classes = [permissions.AllowAny] # Allow any user to view profiles

    def get_object(self):
        # This will retrieve the user based on the 'pk' URL parameter
        return super().get_object()
