from django.conf import settings


def test_legacy_database_is_opt_in_by_default():
    """A clean environment must start without an ignored legacy SQLite file."""
    assert settings.LEGACY_DATABASE_ENABLED is False
    assert "legacy" not in settings.DATABASES
