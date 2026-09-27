"""Create or update a local-only AI demo Foundation user."""

from __future__ import annotations

import os

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.production_demo_seed.ownership import SAFE_EMAIL_DOMAIN
from apps.core.production_demo_seed.safety import allow_database, allow_environment
from apps.foundation.models import FoundationRole, FoundationUser, FoundationUserProfile
from apps.foundation.security import PasswordPolicy

DEMO_USER_MARKER = "Local AI Demo User"


class Command(BaseCommand):
    """Ensure a login-capable demo user without storing plaintext credentials."""

    help = (
        "Create or update a local demo Foundation user. The plaintext password "
        "must be supplied through MEC_AI_DEMO_PASSWORD and is never printed."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            default=os.getenv("MEC_AI_DEMO_EMAIL", "ai.demo@production-demo.invalid"),
            help="Demo user email. Defaults to MEC_AI_DEMO_EMAIL or a local invalid-domain address.",
        )
        parser.add_argument(
            "--role",
            default=os.getenv("MEC_AI_DEMO_ROLE", "Sales"),
            help="Foundation role to assign. Defaults to Sales.",
        )
    @transaction.atomic
    def handle(self, *args, **options):
        if not allow_environment() or not allow_database():
            raise CommandError("Demo user creation requires an explicitly allowed environment and database.")
        password = os.getenv("MEC_AI_DEMO_PASSWORD")
        if not password:
            raise CommandError("MEC_AI_DEMO_PASSWORD is required.")
        PasswordPolicy().validate(password)

        email = str(options["email"]).strip().casefold()
        if not email or not email.endswith(f"@{SAFE_EMAIL_DOMAIN}"):
            raise CommandError(f"Demo email must use @{SAFE_EMAIL_DOMAIN}.")
        try:
            role = FoundationRole.objects.get(name=options["role"], is_active=True)
        except FoundationRole.DoesNotExist as exc:
            raise CommandError(f"Active Foundation role not found: {options['role']}") from exc
        if role.permissions.filter(code="*:*").exists():
            raise CommandError("Wildcard permissions are not allowed for demo users.")

        user = FoundationUser.objects.filter(email=email).first()
        created = user is None
        if created:
            user = FoundationUser.objects.create(
                email=email,
                full_name=DEMO_USER_MARKER,
                password_hash=make_password(password),
                role=role,
                is_active=True,
            )
        elif user.full_name != DEMO_USER_MARKER or user.role_id != role.id:
            raise CommandError("Existing non-demo user collision; refusing to modify it.")
        fields = []
        if not created:
            user.password_hash = make_password(password)
            fields = ["password_hash", "updated_at"]
            user.save(update_fields=fields)
        FoundationUserProfile.objects.get_or_create(user=user)

        action = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Local AI demo user {action}: {email} (role={role.name}, password not printed)"
            )
        )
