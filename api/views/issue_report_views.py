from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from ..models.issue_reports import IssueReport
from ..serializers import IssueReportSerializer
from ..permissions import IsAdminUser, IsUserOwnerOrAdmin
from ..mixins import OwnerFilteredQuerysetMixin

class IssueReportViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
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
