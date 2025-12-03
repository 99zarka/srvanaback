#!/usr/bin/env python
"""
Simple script to test the service ordering endpoints
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'srvana.test_settings')
django.setup()

from django.test import RequestFactory
from rest_framework.test import APITestCase
from orders.views import OrderViewSet
from users.views.user_views import UserViewSet

def test_endpoint_availability():
    """Test that all required endpoints are available"""
    print("Testing endpoint availability...")
    
    # Test OrderViewSet endpoints
    order_view = OrderViewSet()
    order_factory = RequestFactory()
    
    # Test available_for_offer action
    request = order_factory.get('/api/orders/available-for-offer/')
    order_view.request = request
    order_view.format_kwarg = 'json'
    
    # Test that the action exists
    assert hasattr(order_view, 'available_for_offer'), "available_for_offer action not found"
    print("✓ OrderViewSet.available_for_offer action found")
    
    # Test offers action
    request = order_factory.get('/api/orders/1/offers/')
    order_view.request = request
    order_view.kwargs = {'order_id': '1'}
    
    assert hasattr(order_view, 'offers'), "offers action not found"
    print("✓ OrderViewSet.offers action found")
    
    # Test accept_offer action
    request = order_factory.post('/api/orders/1/accept-offer/1/')
    order_view.request = request
    order_view.kwargs = {'order_id': '1', 'offer_id': '1'}
    
    assert hasattr(order_view, 'accept_offer'), "accept_offer action not found"
    print("✓ OrderViewSet.accept_offer action found")
    
    # Test UserViewSet endpoints
    user_view = UserViewSet()
    user_factory = RequestFactory()
    
    # Test technicians action
    request = user_factory.get('/api/users/technicians/')
    user_view.request = request
    user_view.format_kwarg = 'json'
    
    assert hasattr(user_view, 'technicians'), "technicians action not found"
    print("✓ UserViewSet.technicians action found")
    
    # Test technician_detail action
    request = user_factory.get('/api/users/technician-detail/1/')
    user_view.request = request
    user_view.kwargs = {'pk': '1'}
    
    assert hasattr(user_view, 'technician_detail'), "technician_detail action not found"
    print("✓ UserViewSet.technician_detail action found")
    
    print("\n✅ All required endpoints are implemented!")

if __name__ == '__main__':
    test_endpoint_availability()
