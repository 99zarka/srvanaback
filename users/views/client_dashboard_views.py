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

        return Response({
            'total_users': total_users,
            'active_workers': active_workers,
            'services_completed': services_completed,
            'total_revenue': total_revenue,
            'total_issue_reports': total_issue_reports,
            'open_issues': open_issues
        }, status=status.HTTP_200_OK)
