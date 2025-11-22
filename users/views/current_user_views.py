from rest_framework import generics, permissions
from users.models import User
from users.serializers.user_serializers import UserSerializer

class CurrentUserView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
