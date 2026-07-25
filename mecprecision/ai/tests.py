"""Test cho Django AI module.

Các test này không phụ thuộc Ollama thật. Ta cố ý ép `call_ollama` báo lỗi
để kiểm tra fallback demo và việc lưu lịch sử vào database.
"""

import json
import urllib.error
from unittest.mock import patch

from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse

from .models import AIConversation, AITranslationCache, SystemSetting
from .services import ask_ai, generate_product_content, translate_text


class AIModuleTest(TransactionTestCase):
    """Kiểm tra service và API của module AI."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(AIConversation)
            schema_editor.create_model(AITranslationCache)
            schema_editor.create_model(SystemSetting)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(SystemSetting)
            schema_editor.delete_model(AITranslationCache)
            schema_editor.delete_model(AIConversation)
        super().tearDownClass()

    def setUp(self):
        AITranslationCache.objects.all().delete()
        AIConversation.objects.all().delete()
        SystemSetting.objects.all().delete()

    def test_ask_ai_uses_fallback_when_ollama_is_down(self):
        with patch("ai.services.call_ollama", side_effect=urllib.error.URLError("offline")):
            result = ask_ai("MecPrecision có gia công CNC không?")

        self.assertEqual(result["status"], "fallback")
        self.assertEqual(AIConversation.objects.count(), 1)
        self.assertIn("MecPrecision có gia công CNC không?", result["answer"])

    def test_translate_text_creates_cache(self):
        with patch("ai.services.call_ollama", return_value="Precision machining"):
            first = translate_text("Gia công chính xác", "English")
            second = translate_text("Gia công chính xác", "English")

        self.assertEqual(first["status"], "ok")
        self.assertEqual(second["status"], "cached")
        self.assertEqual(AITranslationCache.objects.count(), 1)

    def test_generate_product_content_returns_fields_when_fallback(self):
        with patch("ai.services.call_ollama", side_effect=urllib.error.URLError("offline")):
            result = generate_product_content({"name": "Trục CNC H-Series", "category_name": "Trục chính xác"})

        self.assertEqual(result["status"], "fallback")
        self.assertIn("seo_title", result["fields"])
        self.assertIn("schema_json", result["fields"])

    def test_chat_api_returns_json(self):
        with patch("ai.services.call_ollama", side_effect=urllib.error.URLError("offline")):
            response = self.client.post(
                reverse("ai:api-chat"),
                data=json.dumps({"message": "Bên bạn có nhận bản vẽ PDF không?"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "fallback")
