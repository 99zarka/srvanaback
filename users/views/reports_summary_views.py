from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from orders.models import Order
from payments.models import Payment
from reviews.models import Review
from users.models import User, UserType
from issue_reports.models import IssueReport
from api.permissions import IsAdminUser

class ReportsSummaryAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        if not request.user.user_type.user_type_name == 'admin':
            return Response({"detail": "You are not authorized to view reports summary."},
                            status=status.HTTP_403_FORBIDDEN)

        today = timezone.now().date()
        start_of_month = today.replace(day=1)

        # Current month revenue and services - FIXED: Use 'COMPLETED' status
        monthly_revenue = Order.objects.filter(
            order_status='COMPLETED',
            creation_timestamp__gte=start_of_month
        ).aggregate(Sum('final_price'))['final_price__sum'] or 0.00

        monthly_services = Order.objects.filter(
            order_status='COMPLETED',
            creation_timestamp__gte=start_of_month
        ).count()

        # Previous month for comparison
        prev_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
        prev_month_revenue = Order.objects.filter(
            order_status='COMPLETED',
            creation_timestamp__gte=prev_month_start,
            creation_timestamp__lt=start_of_month
        ).aggregate(Sum('final_price'))['final_price__sum'] or 0.00

        prev_month_services = Order.objects.filter(
            order_status='COMPLETED',
            creation_timestamp__gte=prev_month_start,
            creation_timestamp__lt=start_of_month
        ).count()

        # Calculate percentage changes
        revenue_change = self._calculate_percentage_change(prev_month_revenue, monthly_revenue)
        services_change = self._calculate_percentage_change(prev_month_services, monthly_services)

        # New users this month - FIXED: Use correct date field
        new_users_month = User.objects.filter(
            registration_date__gte=start_of_month
        ).count()

        prev_month_users = User.objects.filter(
            registration_date__gte=prev_month_start,
            registration_date__lt=start_of_month
        ).count()

        users_change = self._calculate_percentage_change(prev_month_users, new_users_month)

        # Issue reports analytics
        total_issue_reports = IssueReport.objects.count()
        open_issues = IssueReport.objects.filter(status='open').count()
        resolved_issues = IssueReport.objects.filter(status='resolved').count()

        # FIXED: Add missing fields that frontend expects
        # Total users (all users)
        total_users = User.objects.count()
        
        # Active workers (technicians with active status)
        try:
            worker_type = UserType.objects.get(user_type_name='technician')
            active_workers = User.objects.filter(
                user_type=worker_type,
                is_active=True
            ).count()
        except UserType.DoesNotExist:
            active_workers = 0
        
        # Services completed (same as monthly_services but for all time)
        services_completed = Order.objects.filter(order_status='COMPLETED').count()

        return Response({
            # Original fields
            'total_revenue': round(monthly_revenue, 2),
            'revenue_change_percentage': f"+{revenue_change}%" if revenue_change >= 0 else f"{revenue_change}%",
            'completed_services': monthly_services,
            'completed_services_change_percentage': f"+{services_change}%" if services_change >= 0 else f"{services_change}%",
            'new_users': new_users_month,
            'new_users_change_percentage': f"+{users_change}%" if users_change >= 0 else f"{users_change}%",
            'total_issue_reports': total_issue_reports,
            'open_issues': open_issues,
            'resolved_issues': resolved_issues,
            
            # FIXED: Add missing fields that frontend expects
            'total_users': total_users,
            'active_workers': active_workers,
            'services_completed': services_completed
        }, status=status.HTTP_200_OK)

    def _calculate_percentage_change(self, old_value, new_value):
        """Calculate percentage change between two values"""
        try:
            if old_value == 0:
                return 100 if new_value > 0 else 0
            return round(((new_value - old_value) / old_value) * 100, 2)
        except (ZeroDivisionError, TypeError):
            return 0
