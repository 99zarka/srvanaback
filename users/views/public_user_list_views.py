from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from users.models import User
from users.serializers.user_serializers import PublicUserSerializer
from django.db.models import Q, F, Case, When, Value, FloatField, DecimalField
from django.db.models.functions import Coalesce

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

            # Handle sorting
            sort_by = self.request.query_params.get('sort_by')
            if sort_by == 'rating':
                # Sort by rating descending, treating NULL as 0 to put them at the end
                # Use DecimalField output_field to match the overall_rating field type
                queryset = queryset.annotate(
                    effective_rating=Coalesce('overall_rating', Value(0.0), output_field=DecimalField())
                ).order_by('-effective_rating', '-num_jobs_completed')
            elif sort_by == 'jobs':
                # Sort by jobs completed descending, put NULL values at the end
                queryset = queryset.order_by('-num_jobs_completed', '-overall_rating')
            elif sort_by == 'name':
                queryset = queryset.order_by('first_name', 'last_name')
            else:
                # Default ordering for technicians - treat NULL as 0 for consistent sorting
                queryset = queryset.annotate(
                    effective_rating=Coalesce('overall_rating', Value(0.0), output_field=DecimalField())
                ).order_by('-effective_rating', '-num_jobs_completed')
        
        return queryset
