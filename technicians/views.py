from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from .models import TechnicianAvailability, TechnicianSkill, VerificationDocument
from .serializers import TechnicianAvailabilitySerializer, TechnicianSkillSerializer, VerificationDocumentSerializer
from api.permissions import IsAdminUser, IsTechnicianUser, IsTechnicianOwnerOrAdmin, IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Avg
from datetime import timedelta, datetime
from django.utils import timezone
from api.mixins import OwnerFilteredQuerysetMixin
from orders.models import Order
from reviews.models import Review # Added import for Review model

class TechnicianAvailabilityViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Technician Availability to be viewed or edited.

    list:
    Return a list of technician availabilities. Technicians see their own, clients see all.
    Permissions: Authenticated Technician User (owner), Authenticated Client User, or Admin User.
    Usage: GET /api/technicians/availability/

    retrieve:
    Return a specific technician availability by ID.
    Permissions: Authenticated Technician User (owner), Authenticated Client User, or Admin User.
    Usage: GET /api/technicians/availability/{id}/

    create:
    Create new technician availability. Technicians can only create for themselves.
    Permissions: Authenticated Technician User or Admin User.
    Usage: POST /api/technicians/availability/
    Body: {"technician_user": 1, "date": "2025-12-01", "start_time": "09:00:00", "end_time": "17:00:00"}

    update:
    Update existing technician availability. Technicians can only update their own.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: PUT /api/technicians/availability/{id}/
    Body: {"end_time": "18:00:00"}

    partial_update:
    Partially update existing technician availability. Technicians can only update their own.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: PATCH /api/technicians/availability/{id}/
    Body: {"start_time": "10:00:00"}

    destroy:
    Delete technician availability. Technicians can only delete their own.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: DELETE /api/technicians/availability/{id}/
    """
    queryset = TechnicianAvailability.objects.all()
    serializer_class = TechnicianAvailabilitySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
        else: # list, retrieve
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        # Get the initial queryset from the ModelViewSet (skipping OwnerFilteredQuerysetMixin's get_queryset)
        base_queryset = super(OwnerFilteredQuerysetMixin, self).get_queryset()

        if user.is_authenticated and user.user_type.user_type_name == 'admin':
            return base_queryset
        elif user.is_authenticated:
            # Authenticated non-admin technicians can only see their own availability for all actions.
            # Clients can view all availability.
            if user.user_type.user_type_name == 'technician':
                return base_queryset.filter(technician_user=user)
            elif user.user_type.user_type_name == 'client':
                return base_queryset # Clients can view all availability
        else: # User is not authenticated
            # Check if any permission allows unauthenticated read access for list/retrieve actions
            has_read_only_permission = any(isinstance(perm, permissions.AllowAny) or isinstance(perm, IsAuthenticatedOrReadOnly) for perm in self.get_permissions())
            if has_read_only_permission and self.action in ['list', 'retrieve']:
                return base_queryset # Allow unauthenticated read access for list/retrieve
        return base_queryset.none()

class TechnicianSkillViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Technician Skills to be viewed or edited.

    list:
    Return a list of technician skills. Technicians see their own, clients see all.
    Permissions: Authenticated Technician User (owner), Authenticated Client User, or Admin User.
    Usage: GET /api/technicians/skills/

    retrieve:
    Return a specific technician skill by ID.
    Permissions: Authenticated Technician User (owner), Authenticated Client User, or Admin User.
    Usage: GET /api/technicians/skills/{id}/

    create:
    Create a new technician skill. Technicians can only create skills for themselves.
    Permissions: Authenticated Technician User or Admin User.
    Usage: POST /api/technicians/skills/
    Body: {"technician_user": 1, "service": 1, "experience_years": 5}

    update:
    Update an existing technician skill. Technicians can only update their own.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: PUT /api/technicians/skills/{id}/
    Body: {"experience_years": 7}

    partial_update:
    Partially update an existing technician skill. Technicians can only update their own.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: PATCH /api/technicians/skills/{id}/
    Body: {"experience_years": 6}

    destroy:
    Delete a technician skill. Technicians can only delete their own.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: DELETE /api/technicians/skills/{id}/
    """
    queryset = TechnicianSkill.objects.all()
    serializer_class = TechnicianSkillSerializer
    owner_field = 'technician_user'

    def get_permissions(self):
        if self.action == 'create':
            user = self.request.user
            if user.is_authenticated and user.user_type.user_type_name == 'technician':
                requested_technician_user_id = self.request.data.get('technician_user')
                if requested_technician_user_id and requested_technician_user_id != user.user_id:
                    raise PermissionDenied("Technicians can only create skills for themselves.")
            self.permission_classes = [IsAdminUser | IsTechnicianUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
        else: # list, retrieve
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

    def get_filtered_queryset(self, user, base_queryset):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            # For these actions, return the full queryset and let object-level permissions handle access
            return base_queryset
        elif self.action == 'list':
            if user.user_type.user_type_name == 'technician':
                return base_queryset.filter(technician_user=user)
            elif user.user_type.user_type_name == 'client':
                return base_queryset # Clients can see all skills
        return base_queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create skills.")

        if user.user_type.user_type_name == 'technician':
            serializer.save(technician_user=user)
        elif user.user_type.user_type_name == 'admin':
            if 'technician_user' not in self.request.data:
                raise serializers.ValidationError({"technician_user": "This field is required for admin users."})
            serializer.save()
        else:
            raise PermissionDenied("Only technicians and admins can create skills.")

class EarningsSummaryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTechnicianUser]

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or user.user_type.user_type_name != 'technician':
            raise PermissionDenied("Only authenticated technicians can view earnings summaries.")

        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

        # Total earnings
        total_earnings = Order.objects.filter(
            technician_user=user,
            order_status='completed'
        ).aggregate(
            total=Sum('final_price')
        )['total'] or 0.00

        # Weekly earnings
        weekly_earnings = Order.objects.filter(
            technician_user=user,
            order_status='completed',
            job_completion_timestamp__isnull=False,
            job_completion_timestamp__gte=start_of_week
        ).aggregate(
            total=Sum('final_price')
        )['total'] or 0.00

        # Monthly earnings
        monthly_earnings = Order.objects.filter(
            technician_user=user,
            order_status='completed',
            job_completion_timestamp__isnull=False,
            job_completion_timestamp__gte=start_of_month
        ).aggregate(
            total=Sum('final_price')
        )['total'] or 0.00

        # Number of completed orders
        completed_orders_count = Order.objects.filter(
            technician_user=user,
            order_status='completed'
        ).count()

        # Number of pending orders
        pending_orders_count = Order.objects.filter(
            technician_user=user,
            order_status='pending'
        ).count()

        # Pending earnings (sum of final_price from pending orders)
        pending_earnings = Order.objects.filter(
            technician_user=user,
            order_status='pending'
        ).aggregate(
            total=Sum('final_price')
        )['total'] or 0.00

        data = {
            'total_earnings': total_earnings,
            'weekly_earnings': weekly_earnings,
            'this_month_earnings': monthly_earnings,
            'completed_orders_count': completed_orders_count,
            'pending_orders_count': pending_orders_count,
            'pending_earnings': pending_earnings,
        }
        return Response(data)

class WorkerSummaryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or user.user_type.user_type_name not in ['technician', 'admin']:
            raise PermissionDenied("Only authenticated technicians and admins can view worker summaries.")

        # Calculate active tasks (e.g., in_progress, pending, accepted)
        active_tasks = Order.objects.filter(
            technician_user=user,
            order_status__in=['pending', 'accepted', 'in_progress']
        ).count()

        # Calculate completed tasks
        completed_tasks = Order.objects.filter(
            technician_user=user,
            order_status='completed'
        ).count()

        # Calculate total earnings (sum of final_price from completed orders)
        total_earnings = Order.objects.filter(
            technician_user=user,
            order_status='completed'
        ).aggregate(total=Sum('final_price'))['total'] or 0.00

        # Calculate average rating (from reviews where this technician is the subject)
        average_rating = Review.objects.filter(
            technician=user
        ).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0.00

        data = {
            'active_tasks': active_tasks,
            'completed_tasks': completed_tasks,
            'total_earnings': total_earnings,
            'average_rating': round(average_rating, 2),
        }
        return Response(data)

class MonthlyPerformanceAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTechnicianUser]

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or user.user_type.user_type_name != 'technician':
            raise PermissionDenied("Only authenticated technicians can view monthly performance.")

        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        
        # Get start and end of current month with proper timezone awareness
        start_of_month_datetime = timezone.make_aware(
            datetime.combine(start_of_month, datetime.min.time())
        )
        end_of_month_datetime = timezone.make_aware(
            datetime.combine(
                (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
                datetime.max.time()
            )
        )

        # Completed tasks this month
        completed_tasks_month = Order.objects.filter(
            technician_user=user,
            order_status='completed',
            job_completion_timestamp__gte=start_of_month_datetime,
            job_completion_timestamp__lte=end_of_month_datetime
        ).count()

        # Earnings this month
        earnings_month = Order.objects.filter(
            technician_user=user,
            order_status='completed',
            job_completion_timestamp__gte=start_of_month_datetime,
            job_completion_timestamp__lte=end_of_month_datetime
        ).aggregate(
            total=Sum('final_price')
        )['total'] or 0.00

        # Average rating this month - only reviews created in the current month
        average_rating_month = Review.objects.filter(
            technician=user,
            created_at__gte=start_of_month_datetime,
            created_at__lte=end_of_month_datetime
        ).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0.00

        data = {
            'completed_tasks_month': completed_tasks_month,
            'earnings_month': earnings_month,
            'average_rating_month': round(average_rating_month, 2),
        }
        return Response(data)

class WorkerReviewsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTechnicianUser]

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or user.user_type.user_type_name != 'technician':
            raise PermissionDenied("Only authenticated technicians can view worker reviews.")

        # Get reviews for this technician
        reviews = Review.objects.filter(technician=user).order_by('-created_at')

        # Calculate average rating
        average_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0.00

        # Paginate results
        page_size = 10
        page = int(request.GET.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size

        paginated_reviews = reviews[start:end]

        from reviews.serializers import ReviewSerializer
        serializer = ReviewSerializer(paginated_reviews, many=True)

        data = {
            'results': serializer.data,
            'average_rating': round(average_rating, 2),
            'count': reviews.count()
        }
        return Response(data)

class VerificationDocumentViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Verification Documents to be viewed or edited.

    list:
    Return a list of verification documents for the authenticated technician. Admins see all.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: GET /api/technicians/verification_documents/

    retrieve:
    Return a specific verification document by ID.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: GET /api/technicians/verification_documents/{id}/

    create:
    Create a new verification document. Technicians can only create for themselves.
    Permissions: Authenticated Technician User or Admin User.
    Usage: POST /api/technicians/verification_documents/
    Body: {"technician_user": 1, "document_type": "ID Card", "document_number": "12345", "status": "Pending"}

    update:
    Update an existing verification document. Technicians can only update their own.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: PUT /api/technicians/verification_documents/{id}/
    Body: {"status": "Approved"}

    partial_update:
    Partially update an existing verification document. Technicians can only update their own.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: PATCH /api/technicians/verification_documents/{id}/
    Body: {"status": "Rejected"}

    destroy:
    Delete a verification document. Technicians can only delete their own.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: DELETE /api/technicians/verification_documents/{id}/
    """
    queryset = VerificationDocument.objects.all()
    serializer_class = VerificationDocumentSerializer
    owner_field = 'technician_user'

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAdminUser | IsTechnicianUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
        else: # list, retrieve
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
        return super().get_permissions()

    def get_filtered_queryset(self, user, base_queryset):
        if user.user_type.user_type_name == 'technician':
            return base_queryset.filter(technician_user=user)
        return base_queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create verification documents.")

        if user.user_type.user_type_name == 'technician':
            requested_technician_user_id = self.request.data.get('technician_user')
            if requested_technician_user_id and requested_technician_user_id != user.user_id:
                raise PermissionDenied("Technicians can only create verification documents for themselves.")
            serializer.save(technician_user=user)
        elif user.user_type.user_type_name == 'admin':
            if 'technician_user' not in self.request.data:
                raise serializers.ValidationError({"technician_user": "This field is required for admin users."})
            serializer.save()
        else:
            raise PermissionDenied("Only technicians and admins can create verification documents.")
