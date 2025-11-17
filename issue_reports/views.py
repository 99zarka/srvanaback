from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import IssueReport
from .serializers import IssueReportSerializer
from api.permissions import IsAdminUser, IsUserOwnerOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin

class IssueReportViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Issue Reports to be viewed or edited.

    list:
    Return a list of issue reports for the authenticated user.
    Permissions: Authenticated User (reporter) or Admin User.
    Usage: GET /api/issue_reports/

    retrieve:
    Return a specific issue report by ID.
    Permissions: Authenticated User (reporter) or Admin User.
    Usage: GET /api/issue_reports/{id}/

    create:
    Create a new issue report. The authenticated user will be set as the reporter.
    Permissions: Authenticated User or Admin User.
    Usage: POST /api/issue_reports/
    Body: {"title": "Bug in service booking", "description": "The booking process fails at step 3."}

    update:
    Update an existing issue report.
    Permissions: Authenticated User (reporter) or Admin User.
    Usage: PUT /api/issue_reports/{id}/
    Body: {"status": "Resolved"}

    partial_update:
    Partially update an existing issue report.
    Permissions: Authenticated User (reporter) or Admin User.
    Usage: PATCH /api/issue_reports/{id}/
    Body: {"description": "Updated description of the bug."}

    destroy:
    Delete an issue report.
    Permissions: Authenticated User (reporter) or Admin User.
    Usage: DELETE /api/issue_reports/{id}/
    """
    queryset = IssueReport.objects.all()
    serializer_class = IssueReportSerializer
    permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsUserOwnerOrAdmin)]
    owner_field = 'reporter'

    def get_filtered_queryset(self, user, base_queryset):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            # For these actions, return the full queryset and let object-level permissions handle access
            return base_queryset
        # For 'list' action, filter by owner
        return super().get_filtered_queryset(user, base_queryset)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create issue reports.")
        serializer.save(reporter=user)
