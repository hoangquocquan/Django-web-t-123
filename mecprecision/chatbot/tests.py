"""Test cho Django Chatbot module."""

import json
import urllib.error
from unittest.mock import patch

from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse

from ai.models import AIConversation


class ChatbotModuleTest(TransactionTestCase):
    """Kiểm tra chatbot gọi AI service và trả JSON."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(AIConversation)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(AIConversation)
        super().tearDownClass()

    def setUp(self):
        AIConversation.objects.all().delete()

    def test_chatbot_api_returns_fallback_json(self):
        with patch("ai.services.call_ollama", side_effect=urllib.error.URLError("offline")):
            response = self.client.post(
                reverse("chatbot:api-message"),
                data=json.dumps({"message": "Có gia công CNC không?"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "fallback")
        self.assertEqual(AIConversation.objects.count(), 1)
