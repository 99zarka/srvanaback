from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from .models import Review
from .serializers import ReviewSerializer
from api.permissions import IsAdminUser, IsClientUser, IsTechnicianUser, IsReviewOwnerOrAdmin, IsReviewTechnicianOrAdmin
from notifications.models import Notification

class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Reviews to be viewed or edited.

    list:
    Return a list of reviews. Clients see reviews they made or for technicians they hired. Technicians see reviews they received or made. Admins see all.
    Permissions: Authenticated User (client/technician owner) or Admin User.
    Usage: GET /api/reviews/

    retrieve:
    Return a specific review by ID.
    Permissions: Authenticated User (client/technician owner) or Admin User.
    Usage: GET /api/reviews/{id}/

    create:
    Create a new review.
    Permissions: Authenticated Client User, Technician User, or Admin User.
    Usage: POST /api/reviews/
    Body: {"reviewer": 1, "technician": 2, "order": 1, "rating": 5, "comment": "Great service!"}

    update:
    Update an existing review.
    Permissions: Authenticated Client User (owner) or Admin User.
    Usage: PUT /api/reviews/{id}/
    Body: {"rating": 4}

    partial_update:
    Partially update an existing review.
    Permissions: Authenticated Client User (owner) or Admin User.
    Usage: PATCH /api/reviews/{id}/
    Body: {"comment": "Service was good, but a bit slow."}

    destroy:
    Delete a review.
    Permissions: Authenticated Client User (owner) or Admin User.
    Usage: DELETE /api/reviews/{id}/
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAdminUser | IsClientUser | IsTechnicianUser] # Only clients, technicians, and admins can create reviews
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (IsClientUser & IsReviewOwnerOrAdmin)] # Only admin or client owner can update/delete
        else: # list, retrieve
            # Add permissions.IsAuthenticated to ensure unauthenticated users get 401
            self.permission_classes = [permissions.IsAuthenticated, IsAdminUser | (IsClientUser & IsReviewOwnerOrAdmin) | (IsTechnicianUser & IsReviewTechnicianOrAdmin)] # Only authenticated users can view reviews
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

        # Save the review first to get the review instance
        review = serializer.save(reviewer=user)

        # Send notification to the technician who received the review
        if review.technician and review.technician != user:  # Don't notify if reviewer and technician are the same user
            try:
                Notification.objects.create(
                    user=review.technician,
                    notification_type='review',
                    title='لقد تلقيت مراجعة جديدة',
                    message=f'لقد تلقت مراجعة جديدة من {user.get_full_name()} بتصنيف {review.rating}/5.',
                    related_review=review,
                    related_order=review.order
                )
            except Exception:
                # Log the error but don't fail the review creation
                pass

        # Send notification to the client who placed the order (if different from reviewer)
        if (review.order.client_user and 
            review.order.client_user != user and 
            review.order.client_user != review.technician):
            try:
                Notification.objects.create(
                    user=review.order.client_user,
                    notification_type='review',
                    title='تم إنشاء مراجعة لطلبك',
                    message=f'تم إنشاء مراجعة لطلبك من قبل {user.get_full_name()} بتصنيف {review.rating}/5.',
                    related_review=review,
                    related_order=review.order
                )
            except Exception:
                # Log the error but don't fail the review creation
                pass

        # Update technician's statistics after review is created
        if review.technician:
            review.technician.update_stats()

class WorkerReviewsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows technicians to view reviews they have received.

    list:
    Return a list of reviews received by the authenticated technician.
    Permissions: Authenticated Technician User only.
    Usage: GET /api/reviews/worker-reviews/

    retrieve:
    Return a specific review received by the authenticated technician.
    Permissions: Authenticated Technician User only.
    Usage: GET /api/reviews/worker-reviews/{review_id}/
    """
    serializer_class = ReviewSerializer

    def get_permissions(self):
        self.permission_classes = [IsTechnicianUser]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Review.objects.none()

        # Only technicians can access this endpoint
        if user.user_type.user_type_name != 'technician':
            return Review.objects.none()

        # Return reviews where this technician is the one being reviewed
        return Review.objects.filter(technician=user).order_by('-created_at')
