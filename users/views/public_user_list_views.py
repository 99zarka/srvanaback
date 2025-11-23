from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from users.models import User
from users.serializers.user_serializers import PublicUserSerializer

class PublicUserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class PublicUserListView(generics.ListAPIView):
    queryset = User.objects.all().order_by('user_id') # Order by user_id for consistent pagination
    serializer_class = PublicUserSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = PublicUserPagination
