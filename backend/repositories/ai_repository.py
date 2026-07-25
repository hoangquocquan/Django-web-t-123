from database.connection import execute_write, query_all


# Repository là lớp chỉ làm việc với database.
# File này không gọi Ollama và không xử lý nghiệp vụ AI.
# Nó chỉ lưu/lấy dữ liệu từ bảng ai_conversations.
def insert_ai_message(record):
    """Lưu một lượt hỏi/đáp AI vào database để admin xem lại lịch sử."""
    # Mỗi lần người dùng hỏi AI, service sẽ gọi hàm này để lưu cả câu hỏi và câu trả lời.
    return execute_write(
        """
        INSERT INTO ai_conversations (
          channel, user_message, assistant_message, model, provider, status, error
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record.get("channel", "public"),
            record["user_message"],
            record.get("assistant_message", ""),
            record.get("model", ""),
            record.get("provider", "ollama"),
            record.get("status", "ok"),
            record.get("error", ""),
        ),
    )


def list_recent_ai_messages(limit=20):
    """Lấy lịch sử AI gần nhất cho trang Admin AI."""
    # Trang Admin AI dùng hàm này để hiển thị bảng lịch sử hỏi đáp gần nhất.
    return query_all(
        """
        SELECT id, channel, user_message, assistant_message, model, provider, status, error, created_at
        FROM ai_conversations
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
