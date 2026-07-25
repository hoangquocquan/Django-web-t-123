from repositories import settings_repository


DEFAULT_SETTINGS = {
    "site_name": "MecPrecision VIETNAM",
    "company_name": "MecPrecision VIETNAM",
    "logo_url": "",
    "favicon_url": "",
    "contact_email": "sales@mecprecision.vn",
    "hotline": "0900 000 000",
    "address": "Khu công nghiệp, TP. Hồ Chí Minh, Việt Nam",
    "smtp_host": "",
    "smtp_port": "587",
    "smtp_username": "",
    "smtp_from_email": "",
    "google_analytics_id": "",
    "facebook_url": "",
    "linkedin_url": "",
    "youtube_url": "",
    "language": "vi",
    "timezone": "Asia/Ho_Chi_Minh",
    "ip_whitelist": "",
    "password_min_length": "8",
    "password_require_uppercase": "0",
    "password_require_digit": "1",
    "captcha_enabled": "1",
}


def get_system_settings():
    settings = DEFAULT_SETTINGS.copy()
    for row in settings_repository.list_settings():
        settings[row["setting_key"]] = row["setting_value"]
    return settings


def save_system_settings(payload):
    allowed_keys = set(DEFAULT_SETTINGS)
    settings = {
        key: str(payload.get(key, "")).strip()
        for key in allowed_keys
    }
    for checkbox_key in ("password_require_uppercase", "password_require_digit", "captcha_enabled"):
        settings[checkbox_key] = "1" if payload.get(checkbox_key) else "0"
    settings_repository.save_settings(settings)
    return get_system_settings()
