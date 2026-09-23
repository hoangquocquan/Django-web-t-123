"""Launch and suspension gate for the first real internal AI pilot."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.foundation.services import FoundationPermissionService
from apps.knowledge.models import (
    KnowledgeAuditEvent, KnowledgeDocument, KnowledgePilotProgram,
    KnowledgeUserScope,
)


PILOT_NAME = "FIRST_INTERNAL_AI_PILOT"


class PilotProgramService:
    """Keep internal AI unavailable until all real launch prerequisites pass."""

    def _require_admin_writer(self, actor):
        FoundationPermissionService().require_permission(actor, "knowledge", "write")
        if getattr(getattr(actor, "role", None), "name", "").lower() != "admin":
            raise PermissionDenied("Pilot launch requires an admin approver.")

    def get_or_create(self):
        return KnowledgePilotProgram.objects.get_or_create(name=PILOT_NAME)[0]

    def is_running(self):
        today = timezone.localdate()
        return KnowledgePilotProgram.objects.filter(
            name=PILOT_NAME, status="RUNNING",
            planned_start__lte=today, planned_end__gte=today,
        ).exists()

    def readiness(self):
        now = timezone.now()
        corpus_count = KnowledgeDocument.objects.filter(
            pilot_corpus_approved=True, status="INDEXED", active_version=True,
        ).count()
        active_scopes = KnowledgeUserScope.objects.filter(
            pilot_enabled=True, approval_status="APPROVED", approved_at__isnull=False,
            training_acknowledged_at__isnull=False,
        ).filter(Q(expires_at__isnull=True) | Q(expires_at__gte=now))
        departments = {
            department: active_scopes.filter(department=department).count()
            for department in ("SALES", "ENGINEERING", "QC", "MANAGEMENT")
        }
        minimum = int(getattr(settings, "AI_PILOT_CORPUS_MIN_DOCUMENTS", 50))
        maximum = int(getattr(settings, "AI_PILOT_CORPUS_MAX_DOCUMENTS", 100))
        return {
            "corpus_count": corpus_count,
            "corpus_ready": minimum <= corpus_count <= maximum,
            "corpus_minimum": minimum,
            "corpus_maximum": maximum,
            "department_user_counts": departments,
            "users_ready": (
                1 <= departments["SALES"] <= 2
                and departments["ENGINEERING"] == 1
                and departments["QC"] == 1
                and departments["MANAGEMENT"] == 1
            ),
        }

    @transaction.atomic
    def launch(self, *, actor, planned_start, planned_end):
        self._require_admin_writer(actor)
        duration = (planned_end - planned_start).days
        if duration < 14 or duration > 28:
            raise ValidationError("Pilot duration must be between 2 and 4 weeks.")
        if not (planned_start <= timezone.localdate() <= planned_end):
            raise ValidationError("The current date must fall inside the pilot window.")
        readiness = self.readiness()
        if not readiness["corpus_ready"] or not readiness["users_ready"]:
            raise ValidationError("Real corpus and bounded pilot cohort are not ready.")
        program = self.get_or_create()
        program.status = "RUNNING"
        program.planned_start = planned_start
        program.planned_end = planned_end
        program.launched_at = timezone.now()
        program.approved_by = actor
        program.save()
        KnowledgeAuditEvent.objects.create(
            event="pilot_launched", actor_id=actor.id, decision="allowed", source_ids=[],
        )
        return program

    @transaction.atomic
    def suspend(self, *, actor):
        self._require_admin_writer(actor)
        program = self.get_or_create()
        program.status = "SUSPENDED"
        program.save(update_fields=["status", "updated_at"])
        KnowledgeAuditEvent.objects.create(
            event="pilot_suspended", actor_id=actor.id, decision="allowed", source_ids=[],
        )
        return program


