#!/usr/bin/env python3
"""
Test script to verify the enhanced JSON parsing and validation logic.
This script tests various scenarios including malformed JSON responses.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'srvana.settings')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status
import json
import re

def test_json_parsing_scenarios():
    """Test various JSON parsing scenarios"""
    
    # Test cases with different response formats
    test_cases = [
        {
            "name": "Valid JSON response",
            "response": '''{
  "reply": "I can help you find a plumber in Cairo.",
  "is_irrelevant": false,
  "project_data": {
    "service_id": 1,
    "problem_description": "Leaking kitchen sink",
    "requested_location": "Cairo, Downtown",
    "scheduled_date": "2024-01-15",
    "scheduled_time_start": "09:00",
    "scheduled_time_end": "17:00",
    "order_type": "service_request",
    "expected_price": 500
  },
  "offer_data": null,
  "technician_recommendations": [],
  "show_post_project": true,
  "show_direct_hire": false,
  "can_edit": true
}''',
            "expected_valid": True
        },
        {
            "name": "JSON with additional text before",
            "response": '''Here is my response:
{
  "reply": "I can help you find a plumber in Cairo.",
  "is_irrelevant": false,
  "project_data": null,
  "offer_data": null,
  "technician_recommendations": [],
  "show_post_project": false,
  "show_direct_hire": false,
  "can_edit": false
}
This is the end of my response.''',
            "expected_valid": True
        },
        {
            "name": "JSON in code block",
            "response": '''Here is the JSON response:
```json
{
  "reply": "I can help you find a plumber in Cairo.",
  "is_irrelevant": false,
  "project_data": null,
  "offer_data": null,
  "technician_recommendations": [],
  "show_post_project": false,
  "show_direct_hire": false,
  "can_edit": false
}
```
Please let me know if you need anything else.''',
            "expected_valid": True
        },
        {
            "name": "Malformed JSON",
            "response": '''{
  "reply": "I can help you find a plumber in Cairo.",
  "is_irrelevant": false,
  "project_data": {
    "service_id": 1,
    "problem_description": "Leaking kitchen sink",
    "requested_location": "Cairo, Downtown",
    "scheduled_date": "2024-01-15",
    "scheduled_time_start": "09:00",
    "scheduled_time_end": "17:00",
    "order_type": "service_request",
    "expected_price": 500
  },
  "offer_data": null,
  "technician_recommendations": [],
  "show_post_project": true,
  "show_direct_hire": false,
  "can_edit": true
''',  # Missing closing brace
            "expected_valid": True  # Should still work with fallback
        },
        {
            "name": "Non-JSON response",
            "response": "I'm sorry, but I can't help you with that request. Please contact customer support for assistance.",
            "expected_valid": True  # Should create minimal valid JSON
        },
        {
            "name": "Empty response",
            "response": "",
            "expected_valid": True  # Should create minimal valid JSON
        }
    ]
    
    print("Testing enhanced JSON parsing logic...")
    print("=" * 60)
    
    # Import the functions from the generate_proposal_view module
    from ai.generate_proposal_view import extract_json_from_response, validate_and_normalize_response
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print(f"Expected Valid: {test_case['expected_valid']}")
        
        try:
            # Test JSON extraction
            extracted_json = extract_json_from_response(test_case['response'])
            print(f"Extracted JSON: {'Yes' if extracted_json else 'No'}")
            
            # Test validation and normalization
            normalized_response = validate_and_normalize_response(extracted_json, test_case['response'])
            
            # Check if response has required fields
            required_fields = ['reply', 'is_irrelevant', 'project_data', 'offer_data', 
                             'technician_recommendations', 'show_post_project', 
                             'show_direct_hire', 'can_edit']
            
            has_all_fields = all(field in normalized_response for field in required_fields)
            print(f"Has all required fields: {has_all_fields}")
            
            # Check field types
            field_types_correct = True
            if has_all_fields:
                field_types_correct = (
                    isinstance(normalized_response['reply'], str) and
                    isinstance(normalized_response['is_irrelevant'], bool) and
                    isinstance(normalized_response['technician_recommendations'], list) and
                    isinstance(normalized_response['show_post_project'], bool) and
                    isinstance(normalized_response['show_direct_hire'], bool) and
                    isinstance(normalized_response['can_edit'], bool)
                )
            print(f"Field types correct: {field_types_correct}")
            
            # Check if reply has content
            reply_has_content = bool(normalized_response['reply'])
            print(f"Reply has content: {reply_has_content}")
            
            # Overall validation
            is_valid = has_all_fields and field_types_correct and reply_has_content
            print(f"Overall validation: {'✅ PASS' if is_valid == test_case['expected_valid'] else '❌ FAIL'}")
            
            # Print sample of normalized response
            print(f"Sample response: {json.dumps(normalized_response, indent=2)[:200]}...")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("JSON parsing test completed!")

def test_api_integration():
    """Test the actual API endpoint with various inputs"""
    client = APIClient()
    
    test_inputs = [
        {
            "name": "Service request",
            "input": "I need a plumber to fix a leak in my kitchen",
            "expected_irrelevant": False
        },
        {
            "name": "Irrelevant question",
            "input": "What is the capital of France?",
            "expected_irrelevant": True
        }
    ]
    
    print("\nTesting API integration...")
    print("=" * 60)
    
    for test_case in test_inputs:
        print(f"\nTest: {test_case['name']}")
        print(f"Input: {test_case['input']}")
        
        try:
            response = client.post('/api/ai/ai-chat/', {
                'prompt': test_case['input'],
                'start_new': True
            }, format='json')
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response has required fields
                required_fields = ['reply', 'is_irrelevant', 'project_data', 'offer_data', 
                                 'technician_recommendations', 'show_post_project', 
                                 'show_direct_hire', 'can_edit']
                
                has_all_fields = all(field in data for field in required_fields)
                print(f"Has all required fields: {has_all_fields}")
                
                # Check field types
                field_types_correct = (
                    isinstance(data['reply'], str) and
                    isinstance(data['is_irrelevant'], bool) and
                    isinstance(data['technician_recommendations'], list) and
                    isinstance(data['show_post_project'], bool) and
                    isinstance(data['show_direct_hire'], bool) and
                    isinstance(data['can_edit'], bool)
                )
                print(f"Field types correct: {field_types_correct}")
                
                # Check is_irrelevant field
                is_irrelevant = data.get('is_irrelevant', False)
                print(f"Is Irrelevant: {is_irrelevant}")
                print(f"Expected Irrelevant: {test_case['expected_irrelevant']}")
                
                if is_irrelevant == test_case['expected_irrelevant']:
                    print("✅ PASS - is_irrelevant field correct")
                else:
                    print("❌ FAIL - is_irrelevant field incorrect")
                
                if has_all_fields and field_types_correct:
                    print("✅ PASS - JSON structure valid")
                else:
                    print("❌ FAIL - JSON structure invalid")
                    
            else:
                print(f"❌ FAIL - HTTP {response.status_code}: {response.content}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("API integration test completed!")

if __name__ == "__main__":
    test_json_parsing_scenarios()
    test_api_integration()
