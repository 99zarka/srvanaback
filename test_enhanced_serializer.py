#!/usr/bin/env python3
"""
Test script to verify the enhanced AIConversationMessageSerializer works correctly.
This script tests the serializer with sample data to ensure it returns the expected structured JSON.
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

from chat.serializers import AIConversationMessageSerializer
from chat.models import AIConversationMessage
from ai.generate_proposal_view import extract_json_from_response, validate_and_normalize_response
import json

def test_enhanced_serializer():
    """Test the enhanced AIConversationMessageSerializer"""
    
    # Sample AI response data (the expected JSON format)
    sample_ai_response = '''{
  "reply": "عذرًا، لكن سؤالك حول مستويات التضخم لا يتعلق بخدمات الصيانة والإصلاح التي نوفرها على منصتنا. نحن متخصصون في مساعدتك في العثور على أفضل الفنيين لخدمات منزلك مثل السباكة، الكهرباء، النجارة، وغيرها من الخدمات المنزلية في مصر.",
  "is_irrelevant": true,
  "project_data": null,
  "offer_data": null,
  "technician_recommendations": [],
  "show_post_project": false,
  "show_direct_hire": false,
  "can_edit": false
}'''

    # Create a mock AIConversationMessage instance
    class MockAIConversationMessage:
        def __init__(self, content, role='assistant'):
            self.content = content
            self.role = role
            self.id = 1
            self.conversation = None
            self.image_url = None
            self.file_url = None
            self.timestamp = "2024-01-09T19:00:00Z"

    print("Testing Enhanced AIConversationMessageSerializer...")
    print("=" * 60)
    
    # Test 1: Test with valid JSON response
    print("\nTest 1: Valid JSON response")
    mock_message = MockAIConversationMessage(sample_ai_response, 'assistant')
    serializer = AIConversationMessageSerializer(mock_message)
    result = serializer.data
    
    print(f"Input content: {sample_ai_response[:100]}...")
    print(f"Serialized data keys: {list(result.keys())}")
    
    # Check if all expected fields are present
    expected_fields = ['parsed_content', 'reply', 'is_irrelevant', 'project_data', 
                      'offer_data', 'technician_recommendations', 'show_post_project', 
                      'show_direct_hire', 'can_edit']
    
    missing_fields = [field for field in expected_fields if field not in result]
    if missing_fields:
        print(f"❌ FAIL - Missing fields: {missing_fields}")
    else:
        print("✅ PASS - All expected fields present")
    
    # Check parsed_content structure
    if 'parsed_content' in result:
        parsed = result['parsed_content']
        print(f"Parsed content keys: {list(parsed.keys())}")
        
        # Verify key fields
        if parsed.get('is_irrelevant') == True:
            print("✅ PASS - is_irrelevant field correct")
        else:
            print("❌ FAIL - is_irrelevant field incorrect")
        
        if parsed.get('reply') and "مستويات التضخم" in parsed['reply']:
            print("✅ PASS - reply field contains expected content")
        else:
            print("❌ FAIL - reply field incorrect")
    
    # Test 2: Test with non-assistant message
    print("\nTest 2: Non-assistant message")
    mock_user_message = MockAIConversationMessage("I need a plumber", 'user')
    user_serializer = AIConversationMessageSerializer(mock_user_message)
    user_result = user_serializer.data
    
    print(f"Input content: {mock_user_message.content}")
    print(f"Serialized data keys: {list(user_result.keys())}")
    
    if user_result.get('is_irrelevant') == False:
        print("✅ PASS - Non-assistant message handled correctly")
    else:
        print("❌ FAIL - Non-assistant message not handled correctly")
    
    # Test 3: Test with malformed JSON
    print("\nTest 3: Malformed JSON response")
    malformed_response = "This is not JSON at all"
    mock_malformed = MockAIConversationMessage(malformed_response, 'assistant')
    malformed_serializer = AIConversationMessageSerializer(mock_malformed)
    malformed_result = malformed_serializer.data
    
    print(f"Input content: {malformed_response}")
    print(f"Serialized data keys: {list(malformed_result.keys())}")
    
    if malformed_result.get('parsed_content', {}).get('reply') == malformed_response:
        print("✅ PASS - Malformed JSON handled with fallback")
    else:
        print("❌ FAIL - Malformed JSON not handled correctly")
    
    # Test 4: Test individual field methods
    print("\nTest 4: Individual field methods")
    individual_serializer = AIConversationMessageSerializer(mock_message)
    
    reply = individual_serializer.get_reply(mock_message)
    is_irrelevant = individual_serializer.get_is_irrelevant(mock_message)
    project_data = individual_serializer.get_project_data(mock_message)
    
    print(f"get_reply(): {reply[:50]}...")
    print(f"get_is_irrelevant(): {is_irrelevant}")
    print(f"get_project_data(): {project_data}")
    
    if reply and is_irrelevant == True and project_data is None:
        print("✅ PASS - Individual field methods work correctly")
    else:
        print("❌ FAIL - Individual field methods incorrect")
    
    print("\n" + "=" * 60)
    print("Enhanced serializer test completed!")

def test_json_parsing_functions():
    """Test the JSON parsing functions directly"""
    print("\nTesting JSON parsing functions directly...")
    print("=" * 60)
    
    sample_response = '''{
  "reply": "عذرًا، لكن سؤالك حول مستويات التضخم لا يتعلق بخدمات الصيانة والإصلاح التي نوفرها على منصتنا. نحن متخصصون في مساعدتك في العثور على أفضل الفنيين لخدمات منزلك مثل السباكة، الكهرباء، النجارة، وغيرها من الخدمات المنزلية في مصر.",
  "is_irrelevant": true,
  "project_data": null,
  "offer_data": null,
  "technician_recommendations": [],
  "show_post_project": false,
  "show_direct_hire": false,
  "can_edit": false
}'''
    
    try:
        # Test extraction
        extracted = extract_json_from_response(sample_response)
        print(f"Extracted JSON: {'Yes' if extracted else 'No'}")
        
        if extracted:
            print(f"Extracted keys: {list(extracted.keys())}")
        
        # Test validation and normalization
        normalized = validate_and_normalize_response(extracted, sample_response)
        print(f"Normalized keys: {list(normalized.keys())}")
        
        if normalized.get('is_irrelevant') == True:
            print("✅ PASS - JSON parsing functions work correctly")
        else:
            print("❌ FAIL - JSON parsing functions incorrect")
            
    except Exception as e:
        print(f"❌ ERROR in JSON parsing functions: {e}")

if __name__ == "__main__":
    test_json_parsing_functions()
    test_enhanced_serializer()
