"""Focused security tests for PROD-03 authentication and upload controls."""

import io
import zipfile
from datetime import timedelta

import pytest
from apps.common.security import validate_safe_url
from apps.foundation.models import FoundationAuthToken, FoundationLoginAttempt
from apps.foundation.security import privacy_hash
from apps.foundation.services import (
    FoundationAuthService,
    FoundationTwoFactorService,
    FoundationUserService,
)
from apps.knowledge.models import KnowledgeDocument
from apps.knowledge.services.upload_security import (
    UploadSecurityService,
    stored_file_cleanup,
)
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone

PASSWORD = "SecurePass123!"


@pytest.fixture
def admin_role(db):
    """Return the seeded admin role."""
    from apps.foundation.models import FoundationRole

    return FoundationRole.objects.get(name="admin")


@pytest.fixture
def foundation_user(admin_role):
    """Create one strongly protected foundation user."""
    return FoundationUserService().create_user(
        email="prod03-security@example.com",
        full_name="PROD-03 Security",
        password=PASSWORD,
        role_name=admin_role.name,
    )


@pytest.mark.django_db
def test_password_policy_rejects_weak_password(admin_role):
    """Weak account credentials fail before a user row is created."""
    with pytest.raises(ValidationError):
        FoundationUserService().create_user(
            email="weak@example.com",
            full_name="Weak User",
            password="password",
            role_name=admin_role.name,
        )


@pytest.mark.django_db
@override_settings(AUTH_LOGIN_MAX_FAILURES=3, AUTH_LOGIN_WINDOW_SECONDS=900)
def test_repeated_login_failures_lock_account_without_storing_email(foundation_user):
    """Repeated password failures are audited with hashes and then blocked."""
    service = FoundationAuthService()
    for _attempt in range(3):
        with pytest.raises(PermissionDenied, match="Invalid credentials"):
            service.login(
                foundation_user.email, "WrongPass123!", remote_addr="203.0.113.10"
            )
    with pytest.raises(PermissionDenied, match="temporarily locked"):
        service.login(foundation_user.email, PASSWORD, remote_addr="203.0.113.10")
    attempts = FoundationLoginAttempt.objects.all()
    assert attempts.count() == 4
    assert attempts.first().email_hash == privacy_hash(foundation_user.email)
    assert all(attempt.email_hash != foundation_user.email for attempt in attempts)


@pytest.mark.django_db
def test_token_rotation_revocation_expiry_and_cleanup(foundation_user):
    """Rotating a token invalidates the old token and cleanup removes stale metadata."""
    service = FoundationAuthService()
    old_raw, old_row = service.login(foundation_user.email, PASSWORD)
    new_raw, _new_row = service.rotate_token(old_raw)
    old_row.refresh_from_db()
    assert old_row.revoked_at is not None
    with pytest.raises(PermissionDenied):
        service.authenticate_token(old_raw)
    assert service.authenticate_token(new_raw) == foundation_user

    FoundationAuthToken.objects.filter(id=old_row.id).update(
        revoked_at=timezone.now() - timedelta(days=40),
        expires_at=timezone.now() - timedelta(days=40),
    )
    assert service.cleanup_tokens(retention_days=30) >= 1


@pytest.mark.django_db
def test_two_factor_challenge_is_one_time_and_fail_closed(foundation_user):
    """A 2FA code can be consumed once and a wrong code never authenticates."""
    service = FoundationTwoFactorService()
    challenge_id, code, _challenge = service.create_challenge(foundation_user)
    with pytest.raises(PermissionDenied, match="Invalid two-factor code"):
        service.verify_challenge(
            challenge_id, "000000" if code != "000000" else "999999"
        )
    assert service.verify_challenge(challenge_id, code) == foundation_user
    with pytest.raises(PermissionDenied, match="Invalid or expired"):
        service.verify_challenge(challenge_id, code)


def _docx_bytes(content="safe"):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", f"<document>{content}</document>")
    return stream.getvalue()


def test_upload_rejects_fake_signature_mime_oversize_and_malware():
    """Extension, MIME, byte limit, and malware gates all fail closed."""
    service = UploadSecurityService()
    with pytest.raises(ValidationError, match="signature"):
        service.validate(
            SimpleUploadedFile("fake.pdf", b"not a pdf", content_type="application/pdf")
        )
    with pytest.raises(ValidationError, match="MIME"):
        service.validate(
            SimpleUploadedFile("fake.pdf", b"%PDF-safe", content_type="image/png")
        )
    with (
        override_settings(UPLOAD_MAX_BYTES=4),
        pytest.raises(ValidationError, match="too large"),
    ):
        service.validate(
            SimpleUploadedFile("large.txt", b"12345", content_type="text/plain")
        )
    with pytest.raises(ValidationError, match="malware"):
        service.validate(
            SimpleUploadedFile(
                "eicar.txt",
                b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE",
                content_type="text/plain",
            )
        )


def test_upload_rejects_zip_bomb_and_archive_traversal():
    """DOCX extraction cannot expand excessive or path-traversing archives."""
    bomb = _docx_bytes("A" * 20000)
    upload = SimpleUploadedFile(
        "bomb.docx",
        bomb,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    with (
        override_settings(UPLOAD_ARCHIVE_MAX_RATIO=2),
        pytest.raises(ValidationError, match="expansion"),
    ):
        UploadSecurityService().validate(upload)

    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("word/document.xml", "safe")
        archive.writestr("../escape.txt", "unsafe")
    traversal = SimpleUploadedFile(
        "traversal.docx",
        stream.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    with pytest.raises(ValidationError, match="Unsafe archive"):
        UploadSecurityService().validate(traversal)


def test_url_validator_blocks_unsafe_schemes_private_and_unknown_hosts():
    """Outbound URL inputs cannot use executable schemes or SSRF targets."""
    with pytest.raises(ValidationError):
        validate_safe_url("javascript:alert(1)")
    with pytest.raises(ValidationError, match="Private"):
        validate_safe_url("http://127.0.0.1/internal", allowed_hosts=["127.0.0.1"])
    with pytest.raises(ValidationError, match="allowlisted"):
        validate_safe_url("https://unknown.example/file", allowed_hosts=["cdn.example"])
    assert validate_safe_url("/media/avatar.png") == "/media/avatar.png"
    assert validate_safe_url(
        "https://cdn.example/file", allowed_hosts=["cdn.example"]
    ).startswith("https://")


@pytest.mark.django_db
def test_api_authentication_rotation_and_security_headers(client, foundation_user):
    """Anonymous access fails, rotation revokes old auth, and headers are present."""
    denied = client.get("/api/v1/foundation/users/")
    assert denied.status_code == 403
    raw_token, _token = FoundationAuthService().login(foundation_user.email, PASSWORD)
    headers = {"HTTP_AUTHORIZATION": f"Bearer {raw_token}"}
    response = client.post("/api/v1/foundation/auth/rotate/", **headers)
    assert response.status_code == 200
    replacement = response.json()["data"]["token"]
    assert client.get("/api/v1/foundation/users/", **headers).status_code == 401
    allowed = client.get(
        "/api/v1/foundation/users/",
        HTTP_AUTHORIZATION=f"Bearer {replacement}",
    )
    assert allowed.status_code == 200
    assert "default-src 'self'" in allowed["Content-Security-Policy"]
    assert allowed["X-Content-Type-Options"] == "nosniff"


@pytest.mark.django_db
def test_knowledge_upload_api_rejects_fake_pdf(client, foundation_user):
    """The document API returns a controlled 400 for a forged upload."""
    raw_token, _token = FoundationAuthService().login(foundation_user.email, PASSWORD)
    response = client.post(
        "/api/v1/knowledge/documents/",
        {
            "title": "Forged",
            "file": SimpleUploadedFile(
                "fake.pdf", b"fake", content_type="application/pdf"
            ),
        },
        HTTP_AUTHORIZATION=f"Bearer {raw_token}",
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unsafe_upload"


@pytest.mark.django_db
def test_private_download_requires_auth_and_hides_storage_path(
    client, foundation_user, tmp_path
):
    """Private source files are streamed only after knowledge permission checks."""
    with override_settings(MEDIA_ROOT=tmp_path):
        source_path = default_storage.save(
            "knowledge/uploads/private.txt",
            io.BytesIO(b"private CNC document"),
        )
        document = KnowledgeDocument.objects.create(
            title="Private CNC",
            content="private CNC document",
            source_type="txt",
            source_path=source_path,
            permission_level="restricted",
        )
        assert (
            client.get(
                f"/api/v1/knowledge/documents/{document.id}/download/"
            ).status_code
            == 403
        )
        token, _token = FoundationAuthService().login(foundation_user.email, PASSWORD)
        response = client.get(
            f"/api/v1/knowledge/documents/{document.id}/download/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        assert response.status_code == 200
        assert b"".join(response.streaming_content) == b"private CNC document"
        assert "attachment" in response["Content-Disposition"]
        assert str(tmp_path) not in response["Content-Disposition"]


def test_stored_file_cleanup_removes_partial_upload(tmp_path):
    """A downstream failure cannot leave an orphaned uploaded file behind."""
    with override_settings(MEDIA_ROOT=tmp_path):
        source_path = default_storage.save(
            "knowledge/uploads/partial.txt",
            io.BytesIO(b"partial"),
        )
        with (
            pytest.raises(RuntimeError, match="database failed"),
            stored_file_cleanup(source_path),
        ):
            raise RuntimeError("database failed")
        assert not default_storage.exists(source_path)
