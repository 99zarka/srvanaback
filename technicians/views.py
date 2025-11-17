from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from .models import TechnicianAvailability, TechnicianSkill, VerificationDocument
from .serializers import TechnicianAvailabilitySerializer, TechnicianSkillSerializer, VerificationDocumentSerializer
from api.permissions import IsAdminUser, IsTechnicianUser, IsTechnicianOwnerOrAdmin, IsAuthenticatedOrReadOnly
from api.mixins import OwnerFilteredQuerysetMixin

class TechnicianAvailabilityViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
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
