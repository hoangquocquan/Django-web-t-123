"""Seed the bounded fictional master data required by Phase 6B browser E2E."""

from __future__ import annotations

import sys

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.business_core.models import (
    BusinessCustomer,
    BusinessMaterial,
    BusinessProduct,
)
from apps.foundation.models import (
    FoundationLoginAttempt,
    FoundationRole,
    FoundationUser,
    FoundationUserProfile,
)
from apps.foundation.security import privacy_hash

FIXTURE_USERS = {
    "Admin": "phase6b.admin@example.invalid",
    "Sales": "phase6b.sales@example.invalid",
    "Manager": "phase6b.manager@example.invalid",
}
CUSTOMER_CODE = "CUS-PHASE6B-E2E"
MATERIAL_CODE = "MAT-PHASE6B-E2E"
PART_CODE = "PART-PHASE6B-E2E"


class Command(BaseCommand):
    help = (
        "Create idempotent fictional Phase 6B users and canonical selector master data."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--password-stdin",
            action="store_true",
            help="Read the shared local-only E2E password from stdin without echoing it.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["password_stdin"]:
            raise CommandError(
                "--password-stdin is required; credentials are never accepted as arguments."
            )
        password = sys.stdin.readline().rstrip("\r\n")
        if len(password) < 12:
            raise CommandError(
                "Phase 6B fixture password must contain at least 12 characters."
            )

        users = {}
        fixture_email_hashes = [privacy_hash(email) for email in FIXTURE_USERS.values()]
        FoundationLoginAttempt.objects.filter(
            email_hash__in=fixture_email_hashes,
            success=False,
        ).delete()
        for role_name, email in FIXTURE_USERS.items():
            try:
                role = FoundationRole.objects.get(name=role_name, is_active=True)
            except FoundationRole.DoesNotExist as exc:
                raise CommandError(
                    f"Required active role is unavailable: {role_name}"
                ) from exc
            user, _created = FoundationUser.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": f"Phase 6B {role_name}",
                    "password_hash": make_password(password),
                    "role": role,
                    "is_active": True,
                },
            )
            user.full_name = f"Phase 6B {role_name}"
            user.password_hash = make_password(password)
            user.role = role
            user.is_active = True
            user.save(
                update_fields=[
                    "full_name",
                    "password_hash",
                    "role",
                    "is_active",
                    "updated_at",
                ]
            )
            FoundationUserProfile.objects.get_or_create(
                user=user,
                defaults={"language": "vi", "timezone": "Asia/Tokyo"},
            )
            users[role_name] = user

        customer, _created = BusinessCustomer.objects.update_or_create(
            customer_code=CUSTOMER_CODE,
            defaults={
                "data_contract": "MVP_V1",
                "company_name": "Phase 6B Fictional Robotics",
                "contact_name": "Fictional Buyer",
                "email": "buyer.phase6b@example.invalid",
                "phone": "",
                "country": "Japan",
                "status": "ACTIVE",
                "notes": "phase6b_e2e_fixture=true",
                "created_by": users["Sales"],
                "updated_by": users["Sales"],
            },
        )
        material, _created = BusinessMaterial.objects.update_or_create(
            material_code=MATERIAL_CODE,
            defaults={
                "data_contract": "MVP_V1",
                "name": "Phase 6B Fictional SUS304",
                "standard": "JIS",
                "grade": "304",
                "description": "phase6b_e2e_fixture=true",
                "is_active": True,
                "created_by": users["Admin"],
                "updated_by": users["Admin"],
            },
        )
        part, _created = BusinessProduct.objects.update_or_create(
            part_code=PART_CODE,
            defaults={
                "data_contract": "MVP_V1",
                "name": "Phase 6B Fictional Precision Bracket",
                "slug": "phase6b-e2e-precision-bracket",
                "revision": "A",
                "unit": "PCS",
                "default_material": material,
                "tolerance": "±0.010 mm",
                "technical_requirements": "Deburr and inspect; phase6b_e2e_fixture=true",
                "is_active": True,
                "created_by": users["Admin"],
                "updated_by": users["Admin"],
            },
        )
        self.stdout.write(
            self.style.SUCCESS(
                "PHASE6B_FIXTURE_READY "
                f"users={len(users)} customer_id={customer.pk} material_id={material.pk} part_id={part.pk}"
            )
        )
