from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from orders.models import Order
from payments.models import Payment
from reviews.models import Review
from users.models import User
from issue_reports.models import IssueReport
from transactions.models import Transaction
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from api.permissions import IsAdminUser
from decimal import Decimal # Import Decimal for financial calculations
import calendar

class ClientSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        client_user = request.user
        
        # Refresh user balances from database to ensure they are current
        client_user.refresh_from_db()

        # Active Orders (pending, in progress, accepted, or awaiting client escrow confirmation)
        active_orders_count = Order.objects.filter(
            client_user=client_user,
            order_status__in=['OPEN', 'ACCEPTED', 'IN_PROGRESS', 'AWAITING_CLIENT_ESCROW_CONFIRMATION', 'AWAITING_RELEASE']
        ).count()

        # Completed Orders
        completed_orders_count = Order.objects.filter(
            client_user=client_user,
            order_status='COMPLETED'
        ).count()

        # Total Spent (money that reached technicians via escrow release or dispute payout)
        total_spent = Transaction.objects.filter(
            source_user=client_user,
            transaction_type__in=['ESCROW_RELEASE', 'DISPUTE_PAYOUT']
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')

        # Average Rating (from reviews given to technicians by this client)
        # This aggregates ratings given *by* this client.
        client_given_reviews_avg_rating = Review.objects.filter(
            reviewer=client_user
        ).aggregate(Avg('rating'))['rating__avg'] or Decimal('0.00')

        return Response({
            'available_balance': client_user.available_balance,
            'in_escrow_balance': client_user.in_escrow_balance,
            'pending_balance': client_user.pending_balance,
            'active_orders': active_orders_count,
            'completed_orders': completed_orders_count,
            'total_spent': total_spent,
            'average_rating_given': round(client_given_reviews_avg_rating, 2)
        }, status=status.HTTP_200_OK)

class AdminSummaryAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        if not request.user.user_type.user_type_name == 'admin':
            return Response({"detail": "You are not authorized to view admin summary."},
                            status=status.HTTP_403_FORBIDDEN)

        # Get current month and previous month for comparison
        now = timezone.now()
        current_month = now.month
        current_year = now.year
        
        # Calculate previous month and year
        if current_month == 1:
            previous_month = 12
            previous_year = current_year - 1
        else:
            previous_month = current_month - 1
            previous_year = current_year

        # Total users
        total_users = User.objects.count()

        # Active workers (technicians)
        active_workers = User.objects.filter(user_type__user_type_name='technician').count()

        # Services completed
        services_completed = Order.objects.filter(order_status='COMPLETED').count()

        # Total revenue (sum of completed orders' final_price)
        total_revenue = Order.objects.filter(
            order_status='COMPLETED'
        ).aggregate(Sum('final_price'))['final_price__sum'] or Decimal('0.00')

        # Total issue reports
        total_issue_reports = IssueReport.objects.count()

        # Open issue reports
        open_issues = IssueReport.objects.filter(status='open').count()

        # Calculate month-over-month changes
        change_data = self.calculate_monthly_changes(current_month, current_year, previous_month, previous_year)

        return Response({
            'total_users': total_users,
            'active_workers': active_workers,
            'services_completed': services_completed,
            'total_revenue': total_revenue,
            'total_issue_reports': total_issue_reports,
            'open_issues': open_issues,
            'change_data': change_data
        }, status=status.HTTP_200_OK)

    def calculate_monthly_changes(self, current_month, current_year, previous_month, previous_year):
        """Calculate month-over-month percentage changes for key metrics."""
        
        # Calculate date ranges for current and previous month
        current_month_start = timezone.datetime(current_year, current_month, 1, tzinfo=timezone.get_current_timezone())
        if current_month == 12:
            current_month_end = timezone.datetime(current_year + 1, 1, 1, tzinfo=timezone.get_current_timezone())
        else:
            current_month_end = timezone.datetime(current_year, current_month + 1, 1, tzinfo=timezone.get_current_timezone())
        
        previous_month_start = timezone.datetime(previous_year, previous_month, 1, tzinfo=timezone.get_current_timezone())
        if previous_month == 12:
            previous_month_end = timezone.datetime(previous_year + 1, 1, 1, tzinfo=timezone.get_current_timezone())
        else:
            previous_month_end = timezone.datetime(previous_year, previous_month + 1, 1, tzinfo=timezone.get_current_timezone())

        # Current month metrics
        current_users = User.objects.filter(registration_date__gte=current_month_start, registration_date__lt=current_month_end).count()
        current_workers = User.objects.filter(
            user_type__user_type_name='technician',
            registration_date__gte=current_month_start, 
            registration_date__lt=current_month_end
        ).count()
        current_services = Order.objects.filter(
            order_status='COMPLETED',
            job_completion_timestamp__gte=current_month_start,
            job_completion_timestamp__lt=current_month_end
        ).count()
        current_revenue = Order.objects.filter(
            order_status='COMPLETED',
            job_completion_timestamp__gte=current_month_start,
            job_completion_timestamp__lt=current_month_end
        ).aggregate(Sum('final_price'))['final_price__sum'] or Decimal('0.00')

        # Previous month metrics
        previous_users = User.objects.filter(registration_date__gte=previous_month_start, registration_date__lt=previous_month_end).count()
        previous_workers = User.objects.filter(
            user_type__user_type_name='technician',
            registration_date__gte=previous_month_start, 
            registration_date__lt=previous_month_end
        ).count()
        previous_services = Order.objects.filter(
            order_status='COMPLETED',
            job_completion_timestamp__gte=previous_month_start,
            job_completion_timestamp__lt=previous_month_end
        ).count()
        previous_revenue = Order.objects.filter(
            order_status='COMPLETED',
            job_completion_timestamp__gte=previous_month_start,
            job_completion_timestamp__lt=previous_month_end
        ).aggregate(Sum('final_price'))['final_price__sum'] or Decimal('0.00')

        # Helper function to calculate percentage change
        def calculate_percentage_change(current, previous):
            if previous == 0:
                if current == 0:
                    return "0.0%"
                else:
                    return f"+{current * 100:.1f}%"
            else:
                change = ((current - previous) / previous) * 100
                if change >= 0:
                    return f"+{change:.1f}%"
                else:
                    return f"{change:.1f}%"

        return {
            'total_users_change': calculate_percentage_change(current_users, previous_users),
            'active_workers_change': calculate_percentage_change(current_workers, previous_workers),
            'services_completed_change': calculate_percentage_change(current_services, previous_services),
            'total_revenue_change': calculate_percentage_change(current_revenue, previous_revenue)
        }
