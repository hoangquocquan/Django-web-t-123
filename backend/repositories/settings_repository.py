from database.connection import get_connection, query_all


def list_settings():
    return query_all("SELECT setting_key, setting_value FROM system_settings")


def save_settings(settings):
    with get_connection() as connection:
        for key, value in settings.items():
            connection.execute(
                """
                INSERT INTO system_settings (setting_key, setting_value)
                VALUES (?, ?)
                ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
                """,
                (key, value),
            )
        connection.commit()

