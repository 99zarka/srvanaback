from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .api_client import AIClient
from orders.models import Order
from users.models import User
from chat.models import AIConversation, AIConversationMessage
from django.shortcuts import get_object_or_404
from chat.serializers import AIConversationMessageSerializer
from ai.rag_system import AIAssistantRAG # Import AIAssistantRAG

# This can be moved to a settings file
AI_CHAT_MODEL = "openrouter-x-ai/grok-code-fast-1"

class ChatHistoryView(APIView):
    """
    Retrieves the chat history for the current active conversation.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Get the message history for the current active conversation. Supports both authenticated and anonymous users. Returns messages ordered by timestamp.",
        responses={
            200: openapi.Response('A list of messages in the conversation.', AIConversationMessageSerializer(many=True)),
        }
    )
    def get(self, request, *args, **kwargs):
        conversation = None
        if request.user.is_authenticated:
            conversation = AIConversation.objects.filter(user=request.user, is_active=True).first()
        else:
            session_convo_id = request.session.get('ai_conversation_id')
            if session_convo_id:
                conversation = AIConversation.objects.filter(id=session_convo_id, is_active=True).first()

        if not conversation:
            return Response([], status=status.HTTP_200_OK)

        messages = conversation.messages.all().order_by('timestamp')
        serializer = AIConversationMessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    operation_description="Send a message to the AI assistant. Handles both authenticated and anonymous users. Supports text, image, and file inputs. Uses RAG system for enhanced responses with technician recommendations and project data extraction.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'prompt': openapi.Schema(type=openapi.TYPE_STRING, description='The user message to send.'),
            'image_url': openapi.Schema(type=openapi.TYPE_STRING, description='(Optional) URL of an image to include.'),
            'file_url': openapi.Schema(type=openapi.TYPE_STRING, description='(Optional) URL of a file to include.'),
            'start_new': openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                description='(Optional) Set to true to discard the current conversation and start a new one.',
                default=False
            ),
        },
        required=['prompt']
    ),
    responses={
        200: openapi.Response(
            description='Enhanced AI response with project data and technician recommendations',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'reply': openapi.Schema(type=openapi.TYPE_STRING, description='AI response text'),
                    'project_data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'service_type': openapi.Schema(type=openapi.TYPE_STRING),
                            'location': openapi.Schema(type=openapi.TYPE_STRING),
                            'problem_description': openapi.Schema(type=openapi.TYPE_STRING),
                            'budget_range': openapi.Schema(type=openapi.TYPE_STRING),
                            'urgency': openapi.Schema(type=openapi.TYPE_STRING),
                            'scheduled_date': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                            'scheduled_time': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
                        }
                    ),
                    'technician_recommendations': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'rating': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'specialization': openapi.Schema(type=openapi.TYPE_STRING),
                                'location': openapi.Schema(type=openapi.TYPE_STRING),
                                'experience_years': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'reasoning': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    ),
                    'show_post_project': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'show_direct_hire': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'can_edit': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                }
            )
        ),
        400: openapi.Response('{"error": "Prompt is required."}'),
        500: openapi.Response('{"error": "Internal server error details"}')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def chat(request):
    """
    Handles chat interactions with the AI assistant for both authenticated and anonymous users.
    Enhanced to provide project data extraction and technician recommendations.
    """
    prompt = request.data.get('prompt')
    start_new = request.data.get('start_new', False) # Moved up for conditional check

    if not prompt and not start_new: # Only require prompt if not starting a new conversation
        return Response({"error": "Prompt is required."}, status=status.HTTP_400_BAD_REQUEST)

    image_url = request.data.get('image_url')
    file_url = request.data.get('file_url')
    start_new = request.data.get('start_new', False)
    
    user = request.user if request.user.is_authenticated else None
    conversation = None

    # --- Conversation Management ---
    if start_new:
        if user:
            AIConversation.objects.filter(user=user, is_active=True).update(is_active=False)
        elif 'ai_conversation_id' in request.session:
            try:
                old_convo = AIConversation.objects.get(id=request.session['ai_conversation_id'])
                old_convo.discard()
            except AIConversation.DoesNotExist:
                pass # Session had an invalid ID
            del request.session['ai_conversation_id']
    else:
        if user:
            conversation = AIConversation.objects.filter(user=user, is_active=True).first()
        elif 'ai_conversation_id' in request.session:
            try:
                conversation = AIConversation.objects.get(id=request.session['ai_conversation_id'], is_active=True)
            except AIConversation.DoesNotExist:
                del request.session['ai_conversation_id'] # Clean up invalid session ID

    if not conversation:
        conversation = AIConversation.objects.create(user=user)
        if not user:
            request.session['ai_conversation_id'] = conversation.id

    # --- Message Handling ---
    # Only create user message if there's actual content to send
    user_message = None
    if prompt or image_url or file_url:
        user_message = AIConversationMessage.objects.create(
            conversation=conversation,
            role='user',
            content=prompt,
            image_url=image_url,
            file_url=file_url
        )

    history = conversation.get_history()
    image_urls_list = [image_url] if image_url else None
    file_urls_list = [file_url] if file_url else None

    # --- RAG Integration ---
    rag_system = AIAssistantRAG()
    technician_matches = rag_system.get_technician_matches(prompt, 100)
    general_matches = rag_system.find_matches(prompt, 15)
    relevant_context = technician_matches + general_matches
    
    # --- Enhanced AI Client Call ---
    # Only call AI if there's actual content to process
    if prompt or image_url or file_url:
        model_to_use = AI_CHAT_MODEL
        if image_url or file_url:
            model_to_use = "gemini-2.5-flash"

        try:
            # Enhanced prompt for structured response
            enhanced_prompt = f"""You are Srvana Assistant, an expert in a services marketplace exclusively for Egypt.

Based on the user's message and conversation history, perform these tasks:

1. Provide a helpful response to the user's query
2. Extract project requirements if applicable for API integration:
   - Service type (plumbing, electrical, painting, etc.) - map to service_id if possible
   - Location (governorate and detailed address) - format as "governorate, detailed_address"
   - Problem description
   - Budget range (if mentioned) - extract numeric value
   - Preferred timing (date and time range)

IMPORTANT: If the user wants to create a project, ensure ALL required fields are complete and not null. If critical information is missing, ask the user specific questions to gather the missing data before proceeding with project creation. Do not leave any critical fields as null if the user has provided the information or if it can be reasonably inferred from the conversation.

3. If a technician is needed, use the provided context to recommend suitable technicians
4. Return the response in this JSON format for direct API integration:

{{
  "reply": "Your response here",
  "project_data": {{
    "service_id": service_id_number_or_null,
    "problem_description": "extracted problem description",
    "requested_location": "governorate, detailed_address",
    "scheduled_date": "YYYY-MM-DD format or null",
    "scheduled_time_start": "HH:MM format or null",
    "scheduled_time_end": "HH:MM format or null",
    "order_type": "service_request",
    "expected_price": numeric_value_or_null
  }},
  "offer_data": {{
    "client_agreed_price": numeric_value_or_null,
    "offer_description": "optional message",
    "order": {{
      "service": service_id_number_or_null,
      "problem_description": "extracted problem description",
      "requested_location": "governorate, detailed_address",
      "scheduled_date": "YYYY-MM-DD format or null",
      "scheduled_time_start": "HH:MM format or null",
      "scheduled_time_end": "HH:MM format or null",
      "order_type": "direct_hire"
    }}
  }},
  "technician_recommendations": [
    {{
      "id": technician_id,
      "name": "technician name",
      "rating": rating,
      "specialization": "technician specialization",
      "location": "technician location",
      "experience_years": experience,
      "reasoning": "why this technician is a good match"
    }}
  ],
  "show_post_project": true_or_false,
  "show_direct_hire": true_or_false,
  "can_edit": true_or_false
}}

IMPORTANT: This platform is exclusively for Egypt and serves Egyptian users only. All currency values must be in Egyptian Pounds (EGP) and all locations must be within Egyptian governorates only. Return API-ready JSON structure for direct form submission.

User Message: {prompt}

Context: {relevant_context}

Return ONLY the JSON response, no additional text before or after."""

            ai_response = AIClient.call_llm(
                model=model_to_use,
                prompt=enhanced_prompt,
                history=history,
                context=relevant_context, # Pass the retrieved context
                image_urls=image_urls_list,
                file_urls=file_urls_list,
                system_message="You are Srvana Assistant, an expert in a services marketplace exclusively for Egypt. Provide concise, helpful, and friendly responses in Arabic. All currency references must be in Egyptian Pounds (EGP) and all locations must be within Egyptian governorates only."
            )

            # --- Save AI Response ---
            AIConversationMessage.objects.create(
                conversation=conversation,
                role='assistant',
                content=ai_response
            )

            # Parse the JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                try:
                    response_data = json.loads(json_str)
                except json.JSONDecodeError:
                    # Fallback to simple response if JSON parsing fails
                    response_data = {"reply": ai_response}
            else:
                # Fallback to simple response if no JSON found
                response_data = {"reply": ai_response}

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            error_message = f"An error occurred while communicating with the AI: {str(e)}"
            # Log the error for debugging
            print(f"Error during AI chat (Conv ID: {conversation.id}): {error_message}")
            return Response({"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        # No content to process, just return success without AI response
        return Response({"reply": ""}, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    operation_description="Health check endpoint for AI service. Returns a simple status message to verify the AI service is operational.",
    responses={200: openapi.Response('{"message": "AI chat service is running."}')}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def index(request):
    """Health check endpoint"""
    return Response({"message": "AI chat service is running."})

# ... (generate_proposal view remains the same)
@swagger_auto_schema(
    method='post',
    operation_description="Generate AI-powered proposal for a project. Creates a professional proposal in Arabic based on project requirements and technician profile. Uses openrouter-kwaipilot/kat-coder-pro:free model. Returns response in JSON format with proposal text and suggested price.",
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
                    'proposal': openapi.Schema(type=openapi.TYPE_STRING, description='Generated proposal text in Arabic (max 100 words)'),
                    'price': openapi.Schema(type=openapi.TYPE_NUMBER, description='Suggested price in Egyptian Pounds (EGP)')
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
        prompt = f"""You are an expert consultant helping technicians create professional project proposals in Arabic. Generate a compelling proposal in Arabic (not more than 100 words) and suggest an appropriate price based on the project requirements and technician profile. The proposal should be concise, professional, and highlight the technician's qualifications and approach to the project. Also provide a competitive price suggestion based on the project complexity and technician's experience level. Return the response in the following JSON format: {{"proposal": "Arabic proposal text (max 100 words)", "price": suggested_price_number}}

IMPORTANT: This platform is exclusively for Egypt and serves Egyptian users only. All currency values must be in Egyptian Pounds (EGP) and all locations must be within Egyptian governorates only.

PROJECT DETAILS IN ARABIC:
- Service: {project_context['service_name']}
- Problem Description: {project_context['problem_description']}
- Location: {project_context['location']} (Must be within Egypt)
- Scheduled Date: {project_context['scheduled_date']}
- Scheduled Time: {project_context['scheduled_time']}
- Expected Price: {project_context['expected_price']} EGP
- Order Status: {project_context['order_status']}

TECHNICIAN PROFILE IN ARABIC:
- Name: {technician_context['first_name']} {technician_context['last_name']}
- Specialization: {technician_context['specialization']}
- Skills: {technician_context['skills']}
- Experience Years: {technician_context['experience_years']}
- Hourly Rate: {technician_context['hourly_rate']} EGP
- Overall Rating: {technician_context['overall_rating']}
- Jobs Completed: {technician_context['num_jobs_completed']}

Please provide a concise, professional proposal in Arabic (maximum 100 words) that showcases the technician's expertise and addresses the project requirements, along with a suggested price that reflects the technician's experience and market rates. The proposal should be in Arabic language only, maximum 100 words, professional and convincing. All prices must be in Egyptian Pounds (EGP) and all references must be to Egyptian locations only."""

        # Use the AI client to generate the proposal
        model = "openrouter-kwaipilot/kat-coder-pro:free"
        response_content = AIClient.call_llm(model, prompt)

        # Parse the response to extract proposal and price
        import json
        import re
        
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            try:
                result = json.loads(json_str)
                proposal = result.get('proposal', response_content)
                price = result.get('price', 0)
            except json.JSONDecodeError:
                proposal = response_content
                price = 0
        else:
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
