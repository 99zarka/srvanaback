from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'technicianavailabilities', views.TechnicianAvailabilityViewSet, basename='technicianavailability')
router.register(r'technicianskills', views.TechnicianSkillViewSet, basename='technicianskill')
router.register(r'verificationdocuments', views.VerificationDocumentViewSet, basename='verificationdocument')

urlpatterns = router.urls + [
    path('earnings-summary/', views.EarningsSummaryAPIView.as_view(), name='technician_earnings_summary'),
    path('worker-summary/', views.WorkerSummaryAPIView.as_view(), name='technician_worker_summary'),
    path('monthly-performance/', views.MonthlyPerformanceAPIView.as_view(), name='technician_monthly_performance'),
]
