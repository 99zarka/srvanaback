from django.urls import path
from . import views
from . import generate_proposal_view

app_name = 'ai'

urlpatterns = [
    path('', views.index, name='index'),
    path('chat/', generate_proposal_view.chat, name='chat'),
    path('generate-proposal/', generate_proposal_view.generate_proposal, name='generate_proposal'),
    # New AI Assistant endpoints
    path('ai-assistant/chat/', views.ChatView.as_view(), name='ai_assistant_chat'),
    path('ai-assistant/recommend-technicians/', views.RecommendTechniciansView.as_view(), name='ai_assistant_recommend_technicians'),
    path('ai-assistant/create-order-from-ai/', views.CreateOrderFromAIView.as_view(), name='ai_assistant_create_order'),
]
