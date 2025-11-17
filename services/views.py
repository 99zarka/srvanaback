from rest_framework import viewsets
from services.models import ServiceCategory, Service
from services.serializers import ServiceCategorySerializer, ServiceSerializer
from api.permissions import IsAdminUser, IsAuthenticatedOrReadOnly

class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Service Categories to be viewed or edited.

    list:
    Return a list of all service categories.
    Permissions: Authenticated or Read-Only.
    Usage: GET /api/services/categories/

    retrieve:
    Return a specific service category by ID.
    Permissions: Authenticated or Read-Only.
    Usage: GET /api/services/categories/{id}/

    create:
    Create a new service category.
    Permissions: Admin User.
    Usage: POST /api/services/categories/
    Body: {"name": "Plumbing", "description": "Services related to plumbing."}

    update:
    Update an existing service category.
    Permissions: Admin User.
    Usage: PUT /api/services/categories/{id}/
    Body: {"name": "Electrical"}

    partial_update:
    Partially update an existing service category.
    Permissions: Admin User.
    Usage: PATCH /api/services/categories/{id}/
    Body: {"description": "Updated description."}

    destroy:
    Delete a service category.
    Permissions: Admin User.
    Usage: DELETE /api/services/categories/{id}/
    """
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        else: # list, retrieve
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

class ServiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Services to be viewed or edited.

    list:
    Return a list of all services.
    Permissions: Authenticated or Read-Only.
    Usage: GET /api/services/

    retrieve:
    Return a specific service by ID.
    Permissions: Authenticated or Read-Only.
    Usage: GET /api/services/{id}/

    create:
    Create a new service.
    Permissions: Admin User.
    Usage: POST /api/services/
    Body: {"category": 1, "name": "Faucet Repair", "description": "Repair of leaky faucets.", "price": 75.00}

    update:
    Update an existing service.
    Permissions: Admin User.
    Usage: PUT /api/services/{id}/
    Body: {"price": 85.00}

    partial_update:
    Partially update an existing service.
    Permissions: Admin User.
    Usage: PATCH /api/services/{id}/
    Body: {"description": "Repair and replacement of faucets."}

    destroy:
    Delete a service.
    Permissions: Admin User.
    Usage: DELETE /api/services/{id}/
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        else: # list, retrieve
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()
