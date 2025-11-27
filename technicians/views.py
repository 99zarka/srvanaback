from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Avg
from datetime import timedelta, datetime
from django.utils import timezone
import cloudinary.uploader

from .models import TechnicianAvailability, TechnicianSkill, VerificationDocument
from .serializers import TechnicianAvailabilitySerializer, TechnicianSkillSerializer, VerificationDocumentSerializer
from api.permissions import IsAdminUser, IsTechnicianUser, IsTechnicianOwnerOrAdmin, IsAuthenticatedOrReadOnly, IsClientOrTechnicianUser
from rest_framework.views import APIView
from api.mixins import OwnerFilteredQuerysetMixin
from orders.models import Order
from reviews.models import Review
from users.models import User, UserType
from notifications.models import Notification
from users.serializers.user_serializers import UserSerializer


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
    owner_field = 'technician_user' # Set owner_field for OwnerFilteredQuerysetMixin

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
        else: # list, retrieve
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        queryset = TechnicianAvailability.objects.all()

        if self.action == 'list':
            if user.is_authenticated:
                if user.user_type.user_type_name == 'client':
                    return queryset # Clients see all availabilities
                elif user.user_type.user_type_name == 'technician':
                    return queryset.filter(technician_user=user) # Technicians see their own
                elif user.user_type.user_type_name == 'admin':
                    return queryset # Admins see all
            else:
                # If unauthenticated, check if read-only permissions allow listing all.
                if any(isinstance(perm, permissions.AllowAny) or isinstance(perm, IsAuthenticatedOrReadOnly) for perm in self.get_permissions()):
                    return queryset
                return queryset.none()
        
        # For detail actions (retrieve, update, destroy), filter for technicians to ensure 404 for unauthorized access
        if user.is_authenticated and user.user_type.user_type_name == 'technician':
            return queryset.filter(technician_user=user)

        return queryset


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

    def get_queryset(self):
        user = self.request.user
        queryset = TechnicianSkill.objects.all()

        if self.action == 'list':
            if user.is_authenticated:
                if user.user_type.user_type_name == 'admin':
                    return queryset # Admin sees all
                elif user.user_type.user_type_name == 'technician':
                    return queryset.filter(technician_user=user) # Technician sees their own
                elif user.user_type.user_type_name == 'client':
                    return queryset # Client sees all
            else: # Unauthenticated users
                if any(isinstance(perm, permissions.AllowAny) or isinstance(perm, IsAuthenticatedOrReadOnly) for perm in self.get_permissions()):
                    return queryset # Allow if read-only permission is set
                return queryset.none()
        
        # For detail actions, filter for technicians to ensure 404 for unauthorized access
        if user.is_authenticated and user.user_type.user_type_name == 'technician':
            return queryset.filter(technician_user=user)

        return queryset

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
    Body: {"technician_user": 1, "document_type": "ID Card", "document_number": "12345", "document_image_url": "http://..."}

    update:
    Update an existing verification document. Technicians can only update their own.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: PUT /api/technicians/verification_documents/{id}/

    partial_update:
    Partially update an existing verification document. Technicians can only update their own.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: PATCH /api/technicians/verification_documents/{id}/

    destroy:
    Delete a verification document. Technicians can only delete their own.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: DELETE /api/technicians/verification_documents/{id}/
    """
    queryset = VerificationDocument.objects.all()
    serializer_class = VerificationDocumentSerializer
    owner_field = 'technician_user'

    def get_permissions(self):
        if self.action in ['approve', 'reject']:
            self.permission_classes = [IsAdminUser]
        elif self.action == 'create':
            self.permission_classes = [IsAdminUser | IsClientOrTechnicianUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
        else: # list, retrieve
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        base_queryset = super(OwnerFilteredQuerysetMixin, self).get_queryset()

        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            # For detail actions, always return the full queryset.
            # Object-level permissions will handle access control (403 if forbidden).
            return base_queryset
        
        if user.is_authenticated and user.user_type.user_type_name == 'admin':
            return base_queryset # Admin sees all for list actions
        elif user.is_authenticated:
            return self.get_filtered_queryset(user, base_queryset) # Authenticated non-admin users get filtered for list actions
        else: # User is not authenticated
            return base_queryset.none()

    def get_filtered_queryset(self, user, base_queryset):
        if user.user_type.user_type_name == 'technician':
            return base_queryset.filter(technician_user=user)
        elif user.user_type.user_type_name == 'admin':
            return base_queryset # Admins can see all verification documents
        return base_queryset.none()

    def create(self, request, *args, **kwargs):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create verification documents.")

        # Determine target user
        technician_user = user
        if user.user_type.user_type_name == 'admin':
            requested_id = request.data.get('technician_user')
            if requested_id:
                try:
                    technician_user = User.objects.get(user_id=requested_id)
                except User.DoesNotExist:
                    raise serializers.ValidationError({"technician_user": "User not found."})
            else:
                raise serializers.ValidationError({"technician_user": "This field is required for admin users."})
        elif user.user_type.user_type_name not in ['technician', 'client']:
            raise PermissionDenied("Only clients, technicians and admins can create verification documents.")
        
        # For non-admins, ensure they are creating for themselves
        requested_technician_user_id = request.data.get('technician_user')
        if user.user_type.user_type_name != 'admin' and requested_technician_user_id and str(requested_technician_user_id) != str(user.user_id):
             raise PermissionDenied("Users can only create verification documents for themselves.")

        # Handle file uploads and document creation
        documents_created = []
        files = request.FILES
        
        # Mapping frontend file names to document types
        file_types = {
            'id_document': 'ID Card',
            'certificate_document': 'Certificate',
            'portfolio_document': 'Portfolio'
        }
        
        # Check if any standard document fields are present (fallback to standard serializer behavior)
        if 'document_type' in request.data and 'document_url' in request.data:
             return super().create(request, *args, **kwargs)

        # Process specific file uploads from frontend
        has_files = False
        for field_name, doc_type in file_types.items():
            if field_name in files:
                has_files = True
                file_obj = files[field_name]
                try:
                    # Upload to cloudinary
                    upload_result = cloudinary.uploader.upload(file_obj)
                    doc_url = upload_result['secure_url']
                    
                    # Create document
                    doc = VerificationDocument.objects.create(
                        technician_user=technician_user,
                        document_type=doc_type,
                        document_url=doc_url,
                        upload_date=timezone.now().date(),
                        verification_status='Pending'
                    )
                    documents_created.append(doc)
                except Exception as e:
                    return Response({'error': f"Failed to upload {doc_type}: {str(e)}"}, status=400)
        
        if not has_files:
             # If no files provided and not standard format, return error
             return Response({'error': 'No documents provided. Please upload id_document, certificate_document, or portfolio_document.'}, status=400)

        # Update user profile with extra fields if provided
        if 'address' in request.data:
            technician_user.address = request.data['address']
        
        # Store extra fields in newly added User model fields
        if 'description' in request.data:
            technician_user.bio = request.data['description']
        
        if 'specialization' in request.data:
            technician_user.specialization = request.data['specialization']
            
        if 'skills' in request.data:
            technician_user.skills_text = request.data['skills']
            
        if 'experience_years' in request.data:
            try:
                technician_user.experience_years = int(request.data['experience_years'])
            except (ValueError, TypeError):
                pass # Handle invalid integer
                
        if 'hourly_rate' in request.data:
            try:
                technician_user.hourly_rate = float(request.data['hourly_rate'])
            except (ValueError, TypeError):
                pass # Handle invalid decimal
        
        technician_user.save()

        # Update verification status to Pending if it was something else
        if technician_user.verification_status != 'Verified':
            technician_user.verification_status = 'Pending'
            technician_user.save()

        # Return the first created document serialized
        if documents_created:
            serializer = self.get_serializer(documents_created[0])
            return Response(serializer.data, status=201)
            
        return Response({'error': 'Failed to create documents.'}, status=400)

    def perform_create(self, serializer):
        # Kept for standard create calls (fallback)
        user = self.request.user
        if user.user_type.user_type_name in ['technician', 'client']:
            serializer.save(technician_user=user)
        elif user.user_type.user_type_name == 'admin':
            serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """
        Approve a verification document (Admin only).
        
        Usage: POST /api/technicians/verification_documents/{id}/approve/
        """
        verification_doc = self.get_object()
        
        # Check if already approved
        if verification_doc.verification_status == 'Approved':
            return Response(
                {"error": "Document is already approved"}, 
                status=400
            )
        
        # Update document status
        verification_doc.verification_status = 'Approved'
        verification_doc.rejection_reason = None  # Clear any previous rejection reason
        verification_doc.save()
        
        # Update user verification status
        technician_user = verification_doc.technician_user
        technician_user.verification_status = 'Verified'
        
        # Update user type to technician upon approval
        try:
            technician_type = UserType.objects.get(user_type_name='technician')
            technician_user.user_type = technician_type
        except UserType.DoesNotExist:
            # Fallback or log error if 'technician' type is missing, though it should exist
            pass
            
        technician_user.save()
        
        # Create notification for the technician
        Notification.objects.create(
            user=technician_user,
            title="Verification Approved",
            message="Your verification documents have been approved. You can now start receiving service requests!",
            is_read=False
        )
        
        serializer = self.get_serializer(verification_doc)
        return Response({
            "message": "Verification document approved successfully",
            "verification_document": serializer.data,
            "user_verification_status": technician_user.verification_status
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """
        Reject a verification document (Admin only).
        
        Usage: POST /api/technicians/verification_documents/{id}/reject/
        Body: {"rejection_reason": "Missing required documents"}
        """
        verification_doc = self.get_object()
        rejection_reason = request.data.get('rejection_reason', '')
        
        if not rejection_reason:
            return Response(
                {"error": "Rejection reason is required"}, 
                status=400
            )
        
        # Check if already approved
        if verification_doc.verification_status == 'Approved':
            return Response(
                {"error": "Document is already approved"}, 
                status=400
            )
        
        # Update document status
        verification_doc.verification_status = 'Rejected'
        verification_doc.rejection_reason = rejection_reason
        verification_doc.save()
        
        # Update user verification status (keep as pending for resubmission)
        technician_user = verification_doc.technician_user
        technician_user.verification_status = 'Pending'
        technician_user.save()
        
        # Create notification for the technician
        Notification.objects.create(
            user=technician_user,
            title="Verification Rejected",
            message=f"Your verification documents have been rejected. Reason: {rejection_reason}. Please resubmit with the required corrections.",
            is_read=False
        )
        
        serializer = self.get_serializer(verification_doc)
        return Response({
            "message": "Verification document rejected successfully",
            "verification_document": serializer.data,
            "user_verification_status": technician_user.verification_status,
            "rejection_reason": rejection_reason
        })
