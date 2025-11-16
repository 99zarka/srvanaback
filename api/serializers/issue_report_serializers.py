from rest_framework import serializers
from ..models.issue_reports import IssueReport

class IssueReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueReport
        fields = '__all__'
