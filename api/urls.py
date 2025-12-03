from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import client_dashboard_views, reports_summary_views
from technicians.views import EarningsSummaryAPIView, WorkerSummaryAPIView, MonthlyPerformanceAPIView, WorkerReviewsAPIView
from reviews.views import ReviewViewSet, WorkerReviewsViewSet
from orders.views import OrderViewSet, WorkerTasksViewSet
from payments.views import PaymentViewSet
from services.views import ServiceViewSet
from issue_reports.views import IssueReportViewSet
from users.views import UserViewSet, PublicUserViewSet

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    # Include router URLs for users
    path('', include(router.urls)),
    
    # Public users list (paginated)
    path('users/public/', PublicUserViewSet.as_view({'get': 'list'}), name='users_public_all'),

    # Dashboard endpoints - using named routes
    path('dashboard/technician/earnings-summary/', EarningsSummaryAPIView.as_view(), name='technician_earnings_summary'),
    path('dashboard/technician/worker-summary/', WorkerSummaryAPIView.as_view(), name='technician_worker_summary'),
    path('dashboard/technician/monthly-performance/', MonthlyPerformanceAPIView.as_view(), name='technician_monthly_performance'),
    path('dashboard/technician/worker-reviews/', WorkerReviewsAPIView.as_view(), name='reviews-worker-reviews'),
    path('dashboard/client/client-summary/', client_dashboard_views.ClientSummaryAPIView.as_view(), name='client_summary'),
    path('dashboard/admin/admin-summary/', client_dashboard_views.AdminSummaryAPIView.as_view(), name='admin_summary'),
    path('dashboard/admin/reports-summary/', reports_summary_views.ReportsSummaryAPIView.as_view(), name='reports_summary'),
    
    # Existing endpoints that tests expect
    path('reviews/', ReviewViewSet.as_view({'get': 'list'}), name='review-list'),
    path('payments/', PaymentViewSet.as_view({'get': 'list'}), name='payment-list'),
    path('services/', ServiceViewSet.as_view({'get': 'list'}), name='service-list'),
    path('issue-reports/', IssueReportViewSet.as_view({'get': 'list'}), name='issuereport-list'),
    
    # New worker-specific endpoints to fix 404 errors
    path('orders/worker-tasks/', WorkerTasksViewSet.as_view({'get': 'list'}), name='worker-tasks-list'),
    path('reviews/worker-reviews/', WorkerReviewsViewSet.as_view({'get': 'list'}), name='worker-reviews-list'),
    
    # Technician-specific endpoints (direct routes for frontend)
    path('technicians/monthly-performance/', MonthlyPerformanceAPIView.as_view(), name='technicians_monthly_performance'),
]
