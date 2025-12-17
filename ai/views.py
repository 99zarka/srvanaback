from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .api_client import AIClient

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
