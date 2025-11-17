from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from .models import TechnicianAvailability, TechnicianSkill, VerificationDocument
from .serializers import TechnicianAvailabilitySerializer, TechnicianSkillSerializer, VerificationDocumentSerializer
from api.permissions import IsAdminUser, IsTechnicianUser, IsTechnicianOwnerOrAdmin, IsAuthenticatedOrReadOnly
from api.mixins import OwnerFilteredQuerysetMixin

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
