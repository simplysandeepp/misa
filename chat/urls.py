from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('chat/', views.chat_api, name='chat_api'),
    path('chat/clear/', views.clear_chat, name='clear_chat'),
]
