from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .api_client import AIClient
from orders.models import Order, ProjectOffer
from users.models import User
from django.shortcuts import get_object_or_404

@swagger_auto_schema(
    method='get',
    operation_description="Health check endpoint for AI service",
    responses={200: openapi.Response('{"message": "AI chat service is running."}')}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def index(request):
    """Health check endpoint"""
    return Response({"message": "AI chat service is running."})

@swagger_auto_schema(
    method='post',
    operation_description="AI Chat endpoint - sends messages to AI model and returns response",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'model': openapi.Schema(type=openapi.TYPE_STRING, description='AI model name (e.g., openrouter-model-name)'),
            'messages': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'role': openapi.Schema(type=openapi.TYPE_STRING, enum=['user', 'assistant']),
                        'content': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                description='Chat history as array of message objects'
            )
        },
        required=['model', 'messages']
    ),
    responses={
        200: openapi.Response('{"reply": "AI-generated response"}'),
        400: openapi.Response('{"error": "Model and messages are required."}'),
        500: openapi.Response('{"error": "Error message"}')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def chat(request):
    """
    Chat endpoint that handles AI model requests
    Expected payload: {"model": "openrouter-model-name", "messages": [{"role": "user", "content": "message"}]}
    """
    data = request.data
    model = data.get('model')
    messages = data.get('messages') # Chat history

    if not model or not messages:
        return Response(
            {"error": "Model and messages are required."}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        response_content = AIClient.call_api(model, messages)
        return Response({"reply": response_content})
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Generate AI-powered proposal for a project",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'order_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Project order ID'),
            'technician_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Technician user ID')
        },
        required=['order_id', 'technician_id']
    ),
    responses={
        200: openapi.Response(
            description='AI-generated proposal and price',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'proposal': openapi.Schema(type=openapi.TYPE_STRING, description='Generated proposal text'),
                    'price': openapi.Schema(type=openapi.TYPE_NUMBER, description='Suggested price')
                }
            )
        ),
        400: openapi.Response('{"error": "Order ID and Technician ID are required."}'),
        404: openapi.Response('{"error": "Order or Technician not found."}'),
        500: openapi.Response('{"error": "Error message"}')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def generate_proposal(request):
    """
    Generate AI-powered proposal for a project based on project details and technician profile
    Uses openrouter-x-ai/grok-code-fast-1 model
    """
    data = request.data
    order_id = data.get('order_id')
    technician_id = data.get('technician_id')

    if not order_id or not technician_id:
        return Response(
            {"error": "Order ID and Technician ID are required."}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Fetch order and technician data
        order = get_object_or_404(Order, order_id=order_id)
        technician = get_object_or_404(User, user_id=technician_id)

        # Prepare context for AI
        project_context = {
            'service_name': order.service.arabic_name if hasattr(order.service, 'arabic_name') else order.service.name if hasattr(order.service, 'name') else 'Unknown Service',
            'problem_description': order.problem_description,
            'location': order.requested_location,
            'scheduled_date': order.scheduled_date,
            'scheduled_time': f"{order.scheduled_time_start} - {order.scheduled_time_end}",
            'expected_price': order.expected_price,
            'order_status': order.order_status
        }

        technician_context = {
            'first_name': technician.first_name,
            'last_name': technician.last_name,
            'specialization': technician.specialization,
            'skills': technician.skills_text,
            'experience_years': technician.experience_years,
            'hourly_rate': technician.hourly_rate,
            'overall_rating': float(technician.overall_rating) if technician.overall_rating else None,
            'num_jobs_completed': technician.num_jobs_completed
        }

        # Create detailed prompt for AI
        prompt = f"""You are an expert consultant helping technicians create professional project proposals in Arabic. Generate a compelling proposal in Arabic (not more than 100 words) and suggest an appropriate price based on the project requirements and technician profile. The proposal should be concise, professional, and highlight the technician's qualifications and approach to the project. Also provide a competitive price suggestion based on the project complexity and technician's experience level. Return the response in the following JSON format: {{\"proposal\": \"Arabic proposal text (max 100 words)\", \"price\": suggested_price_number}}

PROJECT DETAILS IN ARABIC:
- Service: {project_context['service_name']}
- Problem Description: {project_context['problem_description']}
- Location: {project_context['location']}
- Scheduled Date: {project_context['scheduled_date']}
- Scheduled Time: {project_context['scheduled_time']}
- Expected Price: {project_context['expected_price']}
- Order Status: {project_context['order_status']}

TECHNICIAN PROFILE IN ARABIC:
- Name: {technician_context['first_name']} {technician_context['last_name']}
- Specialization: {technician_context['specialization']}
- Skills: {technician_context['skills']}
- Experience Years: {technician_context['experience_years']}
- Hourly Rate: {technician_context['hourly_rate']}
- Overall Rating: {technician_context['overall_rating']}
- Jobs Completed: {technician_context['num_jobs_completed']}

Please provide a concise, professional proposal in Arabic (maximum 100 words) that showcases the technician's expertise and addresses the project requirements, along with a suggested price that reflects the technician's experience and market rates. The proposal should be in Arabic language only, maximum 100 words, professional and convincing."""

        # Use the AI client to generate the proposal
        messages = [{"role": "user", "content": prompt}]
        model = "openrouter-x-ai/grok-code-fast-1"
        response_content = AIClient.call_api(model, messages)

        # Parse the response to extract proposal and price
        import json
        import re
        
        # Try to parse JSON from the response
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            try:
                result = json.loads(json_str)
                proposal = result.get('proposal', response_content)
                price = result.get('price', 0)
            except json.JSONDecodeError:
                # If JSON parsing fails, return the full response as proposal with 0 price
                proposal = response_content
                price = 0
        else:
            # If no JSON found, return the full response as proposal with 0 price
            proposal = response_content
            price = 0

        return Response({
            "proposal": proposal,
            "price": price
        })
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
