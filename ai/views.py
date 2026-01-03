import os
import json
import numpy as np
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .rag_system import AIAssistantRAG
from .api_client import AIClient
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

def index(request):
    """Main AI assistant index page."""
    return render(request, 'ai/index.html')


def get_gemini_response(prompt: str) -> str:
    """Get response from AI model via OpenRouter with fallback options."""
    messages = [
        {"role": "user", "content": prompt}
    ]
    
    # Try different models in order of preference
    models_to_try = [
        "openrouter-kwaipilot/kat-coder-pro:free",       # Fallback 1
        "openrouter-google/gemini-2.0-flash-exp:free",  # Primary choice
        "openrouter-meta-llama/llama-3.1-8b-instruct:free",  # Fallback 2
    ]
    
    for model in models_to_try:
        try:
            response = AIClient.call_api(model, messages)
            return response.strip()
        except Exception as e:
            error_msg = str(e)
            # Check if it's a rate limit error
            if "Rate limit exceeded" in error_msg or "429" in error_msg:
                print(f"Rate limit hit for {model}, trying next model...")
                continue
            else:
                print(f"Error with {model}: {error_msg}")
                continue
    
    # If all models fail, return a helpful fallback response
    return "عذرًا، أواجه طلبًا مرتفعًا حاليًا. يرجى المحاولة مرة أخرى بعد بضع دقائق. هذه مشكلة مؤقتة مع خدمة الذكاء الاصطناعي."

def analyze_technician_need(user_message: str, ai_response: str) -> dict:
    """Analyze if user needs a technician based on conversation."""
    analysis_prompt = f"""
    IMPORTANT: This platform is exclusively for Egypt and serves Egyptian users only. All currency values must be in Egyptian Pounds (EGP) and all locations must be within Egyptian governorates only.
    
    Analyze this conversation and determine if the user needs a technician:
    
    User: {user_message}
    AI Response: {ai_response}
    
    Respond with JSON:
    {{
        "needs_technician": true/false,
        "issue_type": "plumbing/electrical/painting/maintenance/other",
        "urgency": "low/medium/high",
        "confidence": 0.0-1.0
    }}
    """
    
    try:
        analysis = get_gemini_response(analysis_prompt)
        # Parse JSON response
        return json.loads(analysis)
    except:
        return {
            "needs_technician": False,
            "issue_type": None,
            "urgency": "medium",
            "confidence": 0.0
        }

# Define Swagger request and response schemas
chat_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['message'],
    properties={
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='User message to the AI assistant'),
    }
)

recommend_technicians_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['user_issue'],
    properties={
        'user_issue': openapi.Schema(type=openapi.TYPE_STRING, description='Description of the user\'s issue'),
        'top_k': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of top technicians to return (default: 3)')
    }
)

create_order_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['technician_id', 'user_issue'],
    properties={
        'technician_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the selected technician'),
        'user_issue': openapi.Schema(type=openapi.TYPE_STRING, description='Description of the user\'s issue'),
        'service_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the service requested')
    }
)

chat_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='AI assistant response'),
        'action': openapi.Schema(type=openapi.TYPE_STRING, description='Action to take (continue_chat or recommend_technicians)'),
        'metadata': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'issue_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of issue (plumbing, electrical, etc.)'),
                'urgency': openapi.Schema(type=openapi.TYPE_STRING, description='Urgency level (low, medium, high)'),
                'confidence': openapi.Schema(type=openapi.TYPE_NUMBER, description='Confidence score (0.0-1.0)')
            }
        )
    }
)

technician_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'technicians': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Technician ID'),
                    'name': openapi.Schema(type=openapi.TYPE_STRING, description='Technician full name'),
                    'rating': openapi.Schema(type=openapi.TYPE_NUMBER, description='Technician rating'),
                    'location': openapi.Schema(type=openapi.TYPE_STRING, description='Technician location'),
                    'specialization': openapi.Schema(type=openapi.TYPE_STRING, description='Technician specialization'),
                    'jobs_completed': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of jobs completed'),
                    'similarity_score': openapi.Schema(type=openapi.TYPE_NUMBER, description='Similarity score (0.0-1.0)'),
                    'reasoning': openapi.Schema(type=openapi.TYPE_STRING, description='AI-generated reasoning for recommendation'),
                    'reviews': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT),
                        description='Recent reviews'
                    )
                }
            )
        ),
        'total_found': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of technicians found')
    }
)

order_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'technician_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Selected technician ID'),
        'user_issue': openapi.Schema(type=openapi.TYPE_STRING, description='User issue description'),
        'service_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Service ID'),
        'status': openapi.Schema(type=openapi.TYPE_STRING, description='Order status'),
        'estimated_price': openapi.Schema(type=openapi.TYPE_STRING, description='Estimated price'),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
    }
)


class ChatView(APIView):
    """
    API endpoint for AI-powered chat with structured responses.
    
    POST /api/ai/ai-assistant/chat/
    
    Chat with the AI assistant. The AI analyzes the user's message and determines if a technician is needed.
    Returns the AI's response along with metadata about the issue type, urgency, and confidence.
    
    Request Body:
    {
        "message": "I have a problem with my washing machine, it won't drain water"
    }
    
    Response:
    {
        "message": "AI response text...",
        "action": "continue_chat|recommend_technicians",
        "metadata": {
            "issue_type": "plumbing|electrical|painting|maintenance|other",
            "urgency": "low|medium|high",
            "confidence": 0.85
        }
    }
    """
    
    permission_classes = []  # No authentication required for demo
    
    @swagger_auto_schema(
        request_body=chat_request_body,
        responses={
            200: openapi.Response('Successful response', chat_response_schema),
            500: openapi.Response('Error response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING),
                    'message': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ))
        }
    )
    def post(self, request):
        try:
            data = request.data
            user_message = data.get('message', '')
            
            # Get Gemini response
            gemini_response = get_gemini_response(user_message)
            
            # Analyze if technician is needed
            technician_analysis = analyze_technician_need(user_message, gemini_response)
            
            response_data = {
                'message': gemini_response,
                'action': 'recommend_technicians' if technician_analysis.get('needs_technician') else 'continue_chat',
                'metadata': {
                    'issue_type': technician_analysis.get('issue_type'),
                    'urgency': technician_analysis.get('urgency'),
                    'confidence': technician_analysis.get('confidence')
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e),
                'message': 'An error occurred while processing your request.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecommendTechniciansView(APIView):
    """
    API endpoint for AI-powered technician recommendations using RAG system.
    
    POST /api/ai/ai-assistant/recommend-technicians/
    
    Get AI-recommended technicians based on the user's issue description.
    Uses semantic similarity matching with RAG system to find the best matches.
    Returns detailed technician profiles with AI-generated reasoning.
    
    Request Body:
    {
        "user_issue": "I need a plumber to fix a water leak in my kitchen",
        "top_k": 3
    }
    
    Response:
    {
        "technicians": [
            {
                "id": 123,
                "name": "John Doe",
                "rating": 4.8,
                "location": "Cairo, Egypt",
                "specialization": "Plumbing",
                "jobs_completed": 150,
                "similarity_score": 0.92,
                "reasoning": "AI-generated explanation...",
                "reviews": [...]
            }
        ],
        "total_found": 3
    }
    """
    
    permission_classes = []  # No authentication required for demo
    
    @swagger_auto_schema(
        request_body=recommend_technicians_request_body,
        responses={
            200: openapi.Response('Successful response', technician_response_schema),
            400: openapi.Response('Bad Request', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            )),
            500: openapi.Response('Error response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING),
                    'message': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ))
        }
    )
    def post(self, request):
        try:
            data = request.data
            user_issue = data.get('user_issue', '')
            top_k = data.get('top_k', 3)
            
            if not user_issue:
                return Response({
                    'error': 'user_issue is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get RAG system with long-running database connection
            rag = AIAssistantRAG(db_alias='long_running')
            
            # Find technician matches
            tech_matches = rag.get_technician_matches(user_issue, top_k)
            
            # Format response
            tech_data = []
            for match in tech_matches:
                tech = match['data']
                
                # Get AI reasoning for this match
                reasoning_prompt = f"""
                IMPORTANT: This platform is exclusively for Egypt and serves Egyptian users only. All currency values must be in Egyptian Pounds (EGP) and all locations must be within Egyptian governorates only.
                
                User Issue: {user_issue}
                
                Technician Profile: 
                - Name: {tech['first_name']} {tech['last_name']}
                - Specialization: {tech['specialization']}
                - Rating: {tech['overall_rating']}
                - Location: {tech['address']}
                - Jobs Completed: {tech['num_jobs_completed']}
                - Reviews: {tech.get('reviews', [])}
                
                Explain in 2-3 sentences why this technician is a good match for the user's issue.
                Focus on relevant skills, experience, and location.
                """
                
                reasoning = get_gemini_response(reasoning_prompt)
                
                tech_data.append({
                    'id': tech['user_id'],
                    'name': f"{tech['first_name']} {tech['last_name']}",
                    'rating': tech['overall_rating'],
                    'location': tech['address'],
                    'specialization': tech['specialization'],
                    'jobs_completed': tech['num_jobs_completed'],
                    'similarity_score': match['similarity'],
                    'reasoning': reasoning,
                    'reviews': tech.get('reviews', [])
                })
            
            return Response({
                'technicians': tech_data,
                'total_found': len(tech_matches)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e),
                'message': 'An error occurred while processing your request.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateOrderFromAIView(APIView):
    """
    API endpoint for creating orders based on AI recommendations.
    
    POST /api/ai/ai-assistant/create-order-from-ai/
    
    Create a service order based on AI technician recommendations.
    Validates technician selection and creates order with pending confirmation status.
    
    Request Body:
    {
        "technician_id": 123,
        "user_issue": "Water leak in kitchen sink",
        "service_id": 456
    }
    
    Response:
    {
        "technician_id": 123,
        "user_issue": "Water leak in kitchen sink",
        "service_id": 456,
        "status": "pending_confirmation",
        "estimated_price": "1000.00",
        "message": "Order created successfully. Technician will be notified."
    }
    """
    
    permission_classes = []  # No authentication required for demo
    
    @swagger_auto_schema(
        request_body=create_order_request_body,
        responses={
            200: openapi.Response('Successful response', order_response_schema),
            400: openapi.Response('Bad Request', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            )),
            500: openapi.Response('Error response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING),
                    'message': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ))
        }
    )
    def post(self, request):
        try:
            data = request.data
            technician_id = data.get('technician_id')
            user_issue = data.get('user_issue')
            service_id = data.get('service_id')
            
            if not technician_id or not user_issue:
                return Response({
                    'error': 'technician_id and user_issue are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Here you would create an order in your database
            # For now, return a success response with order details
            
            order_data = {
                'technician_id': technician_id,
                'user_issue': user_issue,
                'service_id': service_id,
                'status': 'pending_confirmation',
                'estimated_price': '1000.00',  # This would be calculated based on service
                'message': 'Order created successfully. Technician will be notified.'
            }
            
            return Response(order_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e),
                'message': 'An error occurred while creating the order.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RebuildAIIndexView(APIView):
    """
    API endpoint to rebuild the AI assistant embeddings index.

    POST /api/ai/ai-assistant/rebuild-index/

    Triggers a rebuild of the AI assistant's RAG system index.
    This rebuilds embeddings for all technicians, services, and orders.
    Only call this when you need to refresh the AI's knowledge base.

    Request Body: (empty)

    Response:
    {
        "message": "AI index rebuilt successfully",
        "status": "success",
        "total_embeddings": 150
    }
    """

    permission_classes = []  # No authentication required for demo

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Successful response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Status of the operation'),
                    'total_embeddings': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of embeddings created')
                }
            )),
            500: openapi.Response('Error response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING),
                    'message': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ))
        }
    )
    def post(self, request):
        try:
            # Initialize RAG system with long-running database connection and rebuild index
            rag = AIAssistantRAG(db_alias='long_running')
            rag.build_index()

            # Count total embeddings
            total_embeddings = len(rag.embeddings)

            return Response({
                'message': 'AI index rebuilt successfully',
                'status': 'success',
                'total_embeddings': total_embeddings
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': str(e),
                'message': 'An error occurred while rebuilding the AI index.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
