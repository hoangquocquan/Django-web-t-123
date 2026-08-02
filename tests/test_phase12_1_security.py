import importlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.accounts.services.auth_compatibility_service import PermissionMatrix
from apps.api.permissions import ReadOnlyApiPermission
from apps.api.serializers.auth import profile_to_dict

from scripts.phase12_1_dependency_audit import build_audit

SECURITY_DOCUMENTS = [
    PROJECT_ROOT / "docs" / "reviews" / "PHASE_12.1_SECURITY_ASSESSMENT.md",
    PROJECT_ROOT / "docs" / "security" / "AUTHENTICATION_HARDENING.md",
    PROJECT_ROOT / "docs" / "security" / "AUTHORIZATION_MODEL.md",
    PROJECT_ROOT / "docs" / "security" / "SECRETS_MANAGEMENT_POLICY.md",
    PROJECT_ROOT / "docs" / "security" / "SECURITY_CONFIGURATION_CHECKLIST.md",
    PROJECT_ROOT / "docs" / "reviews" / "PHASE_12.1_SECURITY_HARDENING_REPORT.md",
]


class DummyRequest:
    def __init__(self, method):
        self.method = method


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def test_security_documents_exist():
    for document in SECURITY_DOCUMENTS:
        assert document.exists(), f"Missing security document: {document}"
        assert document.stat().st_size > 0


def test_authentication_protection():
    payload = json.dumps(
        profile_to_dict(
            {
                "id": 1,
                "full_name": "Admin",
                "email": "admin@example.com",
                "role": "admin",
                "is_active": True,
                "two_factor_enabled": True,
                "password_hash": "secret-hash",
                "session_id": "secret-session",
                "reset_token": "secret-token",
            }
        )
    ).lower()

    assert "password_hash" not in payload
    assert "session_id" not in payload
    assert "reset_token" not in payload


def test_permission_checks_block_unsafe_methods():
    permission = ReadOnlyApiPermission()

    assert permission.has_permission(DummyRequest("GET"), None) is True
    assert permission.has_permission(DummyRequest("HEAD"), None) is True
    assert permission.has_permission(DummyRequest("POST"), None) is False
    assert permission.has_permission(DummyRequest("DELETE"), None) is False


def test_authorization_matrix_boundaries():
    matrix = PermissionMatrix()

    assert matrix.has_permission("admin", "settings", "write") is True
    assert matrix.has_permission("editor", "products", "write") is True
    assert matrix.has_permission("editor", "settings", "write") is False
    assert matrix.has_permission("viewer", "products", "read") is True
    assert matrix.has_permission("viewer", "products", "write") is False
    assert matrix.has_permission("unknown", "products", "read") is False


def test_secret_exposure_detection_policy():
    gitignore = read_text(PROJECT_ROOT / ".gitignore")
    secrets_policy = read_text(
        PROJECT_ROOT / "docs" / "security" / "SECRETS_MANAGEMENT_POLICY.md"
    )

    assert ".env" in gitignore
    assert ".env.*" in gitignore
    assert "Do not log" in secrets_policy
    assert "password hashes" in secrets_policy
    assert "session IDs" in secrets_policy


def test_security_configuration_validation(monkeypatch):
    from config.settings import base

    monkeypatch.setenv("SECRET_KEY", "phase12-test-key-not-for-runtime")
    monkeypatch.setenv("ALLOWED_HOSTS", "example.test")
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://user:password@database:5432/mecprecision"
    )
    monkeypatch.setenv("REDIS_URL", "redis://:password@redis:6379/0")
    production = importlib.import_module("config.settings.production")

    assert production.DEBUG is False
    assert production.SECURE_SSL_REDIRECT is True
    assert production.SESSION_COOKIE_SECURE is True
    assert production.CSRF_COOKIE_SECURE is True
    assert production.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert production.X_FRAME_OPTIONS == "DENY"
    assert production.SECURE_HSTS_SECONDS >= 31536000
    assert "whitenoise.middleware.WhiteNoiseMiddleware" not in base.MIDDLEWARE


def test_dependency_audit_reports_unpinned_dependencies():
    audit = build_audit()

    assert audit["dependency_count"] > 0
    assert audit["cve_scan_status"] == "NOT_RUN_NETWORK_DISABLED"
    assert audit["status"] in {
        "DEPENDENCY_AUDIT_COMPLETE",
        "DEPENDENCY_AUDIT_COMPLETE_WITH_WARNINGS",
    }
    assert any(item["package"] == "django" for item in audit["dependencies"])
