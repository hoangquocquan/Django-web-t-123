"""Service layer cho Chatbot public.

Chatbot không tự gọi Ollama trực tiếp. Nó gọi `ai.services.ask_ai()` để dùng chung
business context, fallback và lịch sử hội thoại.
"""

from ai.services import ask_ai


def send_chatbot_message(message, model=None):
    """Gửi câu hỏi từ chatbot public sang AI service."""
    return ask_ai(message, channel="chatbot_public", model=model)
