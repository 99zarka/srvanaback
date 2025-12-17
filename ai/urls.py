from django.urls import path
from . import views

app_name = 'ai'

urlpatterns = [
    path('', views.index, name='index'),
    path('chat/', views.chat, name='chat'),
    path('generate-proposal/', views.generate_proposal, name='generate_proposal'),
]
