from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from users.models import User
from users.serializers.user_serializers import PublicUserSerializer

class PublicUserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class PublicUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A public API endpoint that allows listing and retrieving users (technicians) with filtering.
    """
    queryset = User.objects.all().order_by('user_id')
    serializer_class = PublicUserSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = PublicUserPagination

    def get_queryset(self):
        queryset = self.queryset.order_by('user_id') # Default ordering

        user_type_param = self.request.query_params.get('user_type')
        if user_type_param:
            # Filter by user_type name (case-insensitive)
            queryset = queryset.filter(user_type__user_type_name__iexact=user_type_param)

        # Apply technician-specific filters only if user_type is specifically 'technician'
        if user_type_param and user_type_param.lower() == 'technician':
            # Reorder for technicians based on rating and jobs
            queryset = queryset.order_by('-overall_rating', '-num_jobs_completed')

            specialization = self.request.query_params.get('specialization')
            if specialization and specialization != 'all':
                queryset = queryset.filter(specialization__icontains=specialization)

            location = self.request.query_params.get('location')
            if location:
                queryset = queryset.filter(address__icontains=location)

            rating = self.request.query_params.get('min_rating')
            if rating and rating != 'all':
                try:
                    min_rating = float(rating)
                    queryset = queryset.filter(overall_rating__gte=min_rating)
                except ValueError:
                    pass
        
        return queryset
