from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from .models import Review
from .serializers import ReviewSerializer
from api.permissions import IsAdminUser, IsClientUser, IsTechnicianUser, IsReviewOwnerOrAdmin, IsReviewTechnicianOrAdmin

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAdminUser | IsClientUser | IsTechnicianUser] # Only clients, technicians, and admins can create reviews
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (IsClientUser & IsReviewOwnerOrAdmin)] # Only admin or client owner can update/delete
        else: # list, retrieve
            self.permission_classes = [IsAdminUser | (IsClientUser & IsReviewOwnerOrAdmin) | (IsTechnicianUser & IsReviewTechnicianOrAdmin)] # Only authenticated users can view reviews
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.user_type.user_type_name == 'admin':
                return Review.objects.all()
            elif user.user_type.user_type_name == 'client':
                # Clients can see reviews they made or reviews for technicians they hired
                return Review.objects.filter(reviewer=user) | Review.objects.filter(technician__in=user.client_orders.values_list('technician_user', flat=True))
            elif user.user_type.user_type_name == 'technician':
                # Technicians can see reviews they received or reviews they made (as a client)
                return Review.objects.filter(technician=user) | Review.objects.filter(reviewer=user)
        return Review.objects.none() # Unauthenticated users cannot list/retrieve reviews

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create reviews.")

        if user.user_type.user_type_name == 'client':
            requested_client_user_id = self.request.data.get('reviewer')
            if requested_client_user_id and requested_client_user_id != user.user_id:
                raise PermissionDenied("Clients can only create reviews for themselves.")
            serializer.save(reviewer=user)
        elif user.user_type.user_type_name == 'technician':
            requested_reviewer_id = self.request.data.get('reviewer')
            if requested_reviewer_id and requested_reviewer_id != user.user_id:
                raise PermissionDenied("Technicians can only create reviews for themselves (as a client).")
            if 'technician' not in self.request.data or 'order' not in self.request.data:
                raise serializers.ValidationError({"detail": "Technician and order fields are required when a technician creates a review."})
            serializer.save(reviewer=user)
        elif user.user_type.user_type_name == 'admin':
            if 'reviewer' not in self.request.data or 'technician' not in self.request.data:
                raise serializers.ValidationError({"detail": "Reviewer and technician fields are required for admin users."})
            serializer.save()
        else:
            raise PermissionDenied("Only clients, technicians, and admins can create reviews.")
