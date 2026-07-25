"""Test cho Django Accounts/Auth module."""

import json

from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse

from .models import AdminActivityLog, AdminSession, AdminTwoFactorChallenge, AdminUser, AuthEmailOutbox, LoginAttempt, PasswordResetToken
from .services import hash_password, login_admin, request_password_reset, reset_password_with_token, verify_password


class AccountsModuleTest(TransactionTestCase):
    """Kiểm tra login, session và reset password."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(AdminUser)
            schema_editor.create_model(AdminSession)
            schema_editor.create_model(LoginAttempt)
            schema_editor.create_model(PasswordResetToken)
            schema_editor.create_model(AdminTwoFactorChallenge)
            schema_editor.create_model(AuthEmailOutbox)
            schema_editor.create_model(AdminActivityLog)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(AdminActivityLog)
            schema_editor.delete_model(AuthEmailOutbox)
            schema_editor.delete_model(AdminTwoFactorChallenge)
            schema_editor.delete_model(PasswordResetToken)
            schema_editor.delete_model(LoginAttempt)
            schema_editor.delete_model(AdminSession)
            schema_editor.delete_model(AdminUser)
        super().tearDownClass()

    def setUp(self):
        AdminActivityLog.objects.all().delete()
        AuthEmailOutbox.objects.all().delete()
        AdminTwoFactorChallenge.objects.all().delete()
        PasswordResetToken.objects.all().delete()
        LoginAttempt.objects.all().delete()
        AdminSession.objects.all().delete()
        AdminUser.objects.all().delete()
        self.admin = AdminUser.objects.create(
            full_name="Admin Demo",
            email="admin@example.com",
            password_hash=hash_password("Password123"),
            role=AdminUser.ROLE_ADMIN,
            is_active=True,
        )

    def test_verify_password_matches_hash(self):
        self.assertTrue(verify_password("Password123", self.admin.password_hash))

    def test_login_admin_creates_session(self):
        session = login_admin("admin@example.com", "Password123")

        self.assertEqual(session.admin_id, self.admin.id)
        self.assertEqual(AdminSession.objects.count(), 1)

    def test_password_reset_flow_changes_password(self):
        reset_link = request_password_reset("admin@example.com", "http://local")
        token = reset_link.split("token=", 1)[1]
        reset_password_with_token(token, "NewPassword123")
        self.admin.refresh_from_db()

        self.assertTrue(verify_password("NewPassword123", self.admin.password_hash))

    def test_login_api_returns_json(self):
        response = self.client.post(
            reverse("accounts:api-login"),
            data=json.dumps({"email": "admin@example.com", "password": "Password123"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["email"], "admin@example.com")
