"""URL của module Chatbot."""

from django.urls import path

from . import views

app_name = "chatbot"

urlpatterns = [
    path("", views.chatbot_home, name="home"),
    path("api/message/", views.chatbot_message_api, name="api-message"),
]
