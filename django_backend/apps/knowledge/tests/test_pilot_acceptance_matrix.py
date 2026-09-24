"""Twenty controlled synthetic retrieval/citation acceptance cases for Phase 8B.1."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.foundation.models import FoundationPermission, FoundationRole, FoundationUser
from apps.knowledge.models import KnowledgePilotProgram, KnowledgeUserScope
from apps.knowledge.services.embedding_service import DevelopmentHashEmbeddingProvider
from apps.knowledge.services.governance import KnowledgeGovernanceService
from apps.knowledge.services.knowledge_indexer import KnowledgeIndexer
from apps.knowledge.services.knowledge_service import KnowledgeService
from apps.knowledge.services.pilot_governance import PilotGovernanceService
from apps.knowledge.services.search_service import KnowledgeSearchService


CASES = [
    ("sales", "product materials aluminum stainless", "product"),
    ("engineering", "product machining sus304 titanium", "product"),
    ("qc", "product materials nhom aluminum", "product"),
    ("sales", "san pham vat lieu stainless steel", "product"),
    ("sales", "capability cnc five axis precision", "capability"),
    ("engineering", "cnc tolerance milling turning", "capability"),
    ("qc", "capability do chinh xac precision", "capability"),
    ("engineering", "nang luc five axis milling", "capability"),
    ("sales", "rfq checklist drawing quantity", "rfq"),
    ("sales", "rfq material deadline tolerance", "rfq"),
    ("sales", "bao gia can drawing quantity", "rfq"),
    ("sales", "kiem tra rfq deadline", "rfq"),
    ("engineering", "engineering technical spindle fixture", "technical"),
    ("engineering", "technical geometry surface finish", "technical"),
    ("engineering", "ky thuat spindle geometry", "technical"),
    ("engineering", "engineering fixture surface", "technical"),
    ("qc", "quality qc inspection first article", "qc"),
    ("qc", "measurement calibration traceability", "qc"),
    ("qc", "quy trinh qc calibration", "qc"),
    ("qc", "kiem tra first article measurement", "qc"),
]


@pytest.fixture
def pilot_corpus(db):
    KnowledgePilotProgram.objects.create(
        name="FIRST_INTERNAL_AI_PILOT", status="RUNNING",
        planned_start=timezone.localdate(),
        planned_end=timezone.localdate() + timedelta(days=14),
    )
    read, _ = FoundationPermission.objects.get_or_create(
        code="knowledge:read", defaults={"module": "knowledge", "action": "read"},
    )
    write, _ = FoundationPermission.objects.get_or_create(
        code="knowledge:write", defaults={"module": "knowledge", "action": "write"},
    )
    admin_role, _ = FoundationRole.objects.get_or_create(name="admin")
    admin_role.permissions.add(write, read)
    author = FoundationUser.objects.create(email="matrix-author@example.invalid", full_name="Matrix Author", password_hash="!", role=admin_role)
    approver = FoundationUser.objects.create(email="matrix-approver@example.invalid", full_name="Matrix Approver", password_hash="!", role=admin_role)

    users = {}
    for key, department in [("sales", "SALES"), ("engineering", "ENGINEERING"), ("qc", "QC")]:
        role, _ = FoundationRole.objects.get_or_create(name=f"Matrix {department}")
        role.permissions.add(read)
        user = FoundationUser.objects.create(email=f"matrix-{key}@example.invalid", full_name=key, password_hash="!", role=role)
        KnowledgeUserScope.objects.create(
            user=user, department=department, pilot_enabled=True,
            approval_status="APPROVED", approved_at=timezone.now(),
            training_acknowledged_at=timezone.now(),
        )
        users[key] = user

    definitions = {
        "product": ("Pilot Product Materials", "public", "", "product materials vat lieu nhom aluminum stainless steel sus304 titanium machining san pham"),
        "capability": ("Pilot CNC Capability", "public", "", "capability nang luc cnc five axis precision do chinh xac tolerance milling turning"),
        "rfq": ("Pilot RFQ Guideline", "internal", "SALES", "rfq checklist bao gia kiem tra drawing quantity material deadline tolerance can"),
        "technical": ("Pilot Engineering FAQ", "internal", "ENGINEERING", "engineering technical ky thuat spindle fixture geometry surface finish"),
        "qc": ("Pilot QC Procedure", "internal", "QC", "quality qc quy trinh kiem tra inspection first article measurement calibration traceability"),
    }
    documents = {}
    governance = KnowledgeGovernanceService()
    for key, (title, level, department, content) in definitions.items():
        document = KnowledgeService().create_document(
            title=title, content=content, permission_level=level,
            department=department, created_by_email=author.email,
            owner_email=author.email,
            effective_date=timezone.now().date(),
        )
        governance.submit_review(document.id, actor=author)
        PilotGovernanceService().record_owner_review(document.id, actor=author)
        governance.approve(document.id, actor=approver, release_public=level == "public")
        PilotGovernanceService().record_quality_review(
            document.id, actor=approver, decision="APPROVED",
        )
        PilotGovernanceService().approve_document(document.id, actor=approver)
        KnowledgeIndexer(embedding_service=DevelopmentHashEmbeddingProvider()).reindex(document)
        documents[key] = document
    return users, documents


@pytest.mark.django_db
@pytest.mark.parametrize(("persona", "question", "expected"), CASES)
def test_controlled_pilot_question_has_authorized_versioned_citation(
    pilot_corpus, persona, question, expected,
):
    users, documents = pilot_corpus
    result = KnowledgeSearchService(
        embedding_service=DevelopmentHashEmbeddingProvider(),
    ).search(question, limit=3, user=users[persona])
    source_ids = [source["id"] for source in result["sources"]]
    assert documents[expected].id in source_ids
    source = next(item for item in result["sources"] if item["id"] == documents[expected].id)
    assert source["version"] == 1
    assert source["revision_id"]
    assert source["revision_date"]
    assert source["section"]
    forbidden = {
        doc.id for key, doc in documents.items()
        if doc.permission_level == "internal" and doc.department != users[persona].knowledge_scope.department
    }
    assert forbidden.isdisjoint(source_ids)
