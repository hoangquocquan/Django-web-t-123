from database.connection import execute_write, query_one


# Repository này chỉ làm việc với bảng cache bản dịch AI.
# Service sẽ quyết định dịch nội dung nào, còn repository chỉ lưu và lấy dữ liệu SQLite.
def get_cached_translation(source_hash, target_language, model):
    """Lấy bản dịch đã lưu trong cache nếu trước đó AI đã dịch rồi."""
    return query_one(
        """
        SELECT translated_text, status
        FROM ai_translation_cache
        WHERE source_hash = ? AND target_language = ? AND model = ? AND status = 'ok'
        """,
        (source_hash, target_language, model),
    )


def save_cached_translation(record):
    """Lưu bản dịch vào cache để lần sau mở trang nhanh hơn."""
    return execute_write(
        """
        INSERT INTO ai_translation_cache (
          source_hash, source_text, target_language, translated_text, provider, model, status, error, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(source_hash, target_language, model)
        DO UPDATE SET
          translated_text = excluded.translated_text,
          provider = excluded.provider,
          status = excluded.status,
          error = excluded.error,
          updated_at = CURRENT_TIMESTAMP
        """,
        (
            record["source_hash"],
            record["source_text"],
            record["target_language"],
            record["translated_text"],
            record.get("provider", "ollama"),
            record.get("model", ""),
            record.get("status", "ok"),
            record.get("error", ""),
        ),
    )
