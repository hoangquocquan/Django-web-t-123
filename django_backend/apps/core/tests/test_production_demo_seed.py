"""Focused tests for production-like TEST seed Milestone 1."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from apps.business_core.models import (
    BusinessCustomer,
    BusinessMaterial,
    BusinessProduct,
)
from apps.core.production_demo_seed.ai_eval_cases import load_ai_eval_cases
from apps.core.production_demo_seed.profiles import DATASET_MARKER
from apps.core.production_demo_seed.validators import assert_no_deliverable_seed_pii
from apps.foundation.models import FoundationRole, FoundationUser
from apps.knowledge.models import KnowledgeChunk, KnowledgeDocument
from apps.knowledge.services.embedding_service import DevelopmentHashEmbeddingProvider
from apps.knowledge.services.knowledge_service import KnowledgeService
from apps.knowledge.services.runtime_health import KnowledgeRuntimeHealthService
from apps.knowledge.services.search_service import KnowledgeSearchService
from apps.sales.models import SalesQuotation, SalesRfq
from apps.transaction_domain.models import OrderProgressEvent, TransactionOrder
from django.core.files.storage import storages
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.fixture
def seed_media(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    settings.STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}}
    settings.RFQ_DOCUMENT_MAX_BYTES = 2048
    settings.DEMO_TOOLING_ENVIRONMENT = "TEST"
    settings.DEMO_TOOLING_DATABASE_ALLOWLIST = [
        {"engine": "sqlite", "path": settings.DATABASES["default"]["NAME"]}
    ]
    storages._storages.clear()
    yield tmp_path
    storages._storages.clear()


def run_seed_apply(monkeypatch, seed_media, profile="TEST"):
    monkeypatch.setenv("PRODUCTION_DEMO_SEED_ALLOWED", "true")
    output = io.StringIO()
    call_command("seed_production_demo", "--profile", profile, "--apply", stdout=output)
    return output.getvalue()


def seed_report_from_output(output):
    return json.loads(output.split("\nProduction-demo", 1)[0])


@pytest.mark.django_db
def test_seed_apply_refuses_without_environment_gate(seed_media):
    with pytest.raises(CommandError, match="PRODUCTION_DEMO_SEED_ALLOWED=true"):
        call_command("seed_production_demo", "--profile", "TEST", "--apply")


@pytest.mark.django_db
def test_seed_dry_run_performs_zero_writes():
    before = BusinessCustomer.objects.count()
    output = io.StringIO()
    call_command("seed_production_demo", "--profile", "TEST", "--dry-run", stdout=output)
    assert "Dry-run only" in output.getvalue()
    assert BusinessCustomer.objects.count() == before


@pytest.mark.django_db
def test_seed_apply_creates_owned_records_and_safe_pii(monkeypatch, seed_media):
    run_seed_apply(monkeypatch, seed_media)
    assert BusinessCustomer.objects.filter(notes__contains=DATASET_MARKER).count() == 12
    assert BusinessMaterial.objects.filter(description__contains=DATASET_MARKER).count() == 12
    assert BusinessProduct.objects.filter(technical_requirements__contains=DATASET_MARKER).count() == 30
    assert FoundationUser.objects.filter(email__endswith="@production-demo.invalid").count() == 6
    assert_no_deliverable_seed_pii()


@pytest.mark.django_db
def test_seed_rerun_is_idempotent(monkeypatch, seed_media):
    run_seed_apply(monkeypatch, seed_media)
    counts = {
        "customers": BusinessCustomer.objects.filter(notes__contains=DATASET_MARKER).count(),
        "materials": BusinessMaterial.objects.filter(description__contains=DATASET_MARKER).count(),
        "parts": BusinessProduct.objects.filter(technical_requirements__contains=DATASET_MARKER).count(),
        "rfqs": SalesRfq.objects.filter(notes__contains=DATASET_MARKER).count(),
        "quotations": SalesQuotation.objects.filter(idempotency_key__startswith="pdv1-quote").count(),
        "orders": TransactionOrder.objects.filter(idempotency_key__startswith="pdv1-order").count(),
        "knowledge": KnowledgeDocument.objects.filter(metadata__dataset=DATASET_MARKER).count(),
    }
    run_seed_apply(monkeypatch, seed_media)
    assert BusinessCustomer.objects.filter(notes__contains=DATASET_MARKER).count() == counts["customers"]
    assert BusinessMaterial.objects.filter(description__contains=DATASET_MARKER).count() == counts["materials"]
    assert BusinessProduct.objects.filter(technical_requirements__contains=DATASET_MARKER).count() == counts["parts"]
    assert SalesRfq.objects.filter(notes__contains=DATASET_MARKER).count() == counts["rfqs"]
    assert SalesQuotation.objects.filter(idempotency_key__startswith="pdv1-quote").count() == counts["quotations"]
    assert TransactionOrder.objects.filter(idempotency_key__startswith="pdv1-order").count() == counts["orders"]
    assert KnowledgeDocument.objects.filter(metadata__dataset=DATASET_MARKER).count() == counts["knowledge"]


@pytest.mark.django_db
def test_seed_knowledge_uses_governed_approval_and_stable_revisions(monkeypatch, seed_media):
    run_seed_apply(monkeypatch, seed_media)
    documents = list(
        KnowledgeDocument.objects.filter(metadata__dataset=DATASET_MARKER).order_by("id")
    )
    assert len(documents) == 12
    assert all(document.status == "INDEXED" for document in documents)
    assert all(document.approved_version == document.version for document in documents)
    assert all(document.approved_at and document.approval_hash for document in documents)
    assert all(document.owner_reviewed_at and document.owner_review_hash for document in documents)
    assert all(document.owner_reviewed_by_email == document.owner_email for document in documents)
    assert all(document.department == "MANAGEMENT" for document in documents)
    assert all(not document.ai_public_approved for document in documents)
    assert all(document.chunks.exists() for document in documents)
    versions_before = {document.id: document.version for document in documents}

    run_seed_apply(monkeypatch, seed_media)

    assert {
        document.id: document.version
        for document in KnowledgeDocument.objects.filter(metadata__dataset=DATASET_MARKER)
    } == versions_before


@pytest.mark.django_db
def test_phase6b_fixture_like_records_remain_untouched(monkeypatch, seed_media):
    role = FoundationRole.objects.create(name="Phase6B Owner")
    user = FoundationUser.objects.create(
        email="phase6b-owner@example.invalid",
        full_name="Phase6B Owner",
        password_hash="!",
        role=role,
    )
    fixture = BusinessCustomer.objects.create(
        data_contract="MVP_V1",
        customer_code="CUS-PHASE6B-E2E",
        company_name="Phase 6B Fixture Customer",
        email="phase6b.fixture@example.invalid",
        status="ACTIVE",
        notes="phase6b original note",
        created_by=user,
        updated_by=user,
    )
    run_seed_apply(monkeypatch, seed_media)
    fixture.refresh_from_db()
    assert fixture.notes == "phase6b original note"
    assert fixture.company_name == "Phase 6B Fixture Customer"


def test_seed_source_does_not_hardcode_credentials_or_tokens():
    root = Path(__file__).resolve().parents[1] / "production_demo_seed"
    command = Path(__file__).resolve().parents[1] / "management" / "commands" / "seed_production_demo.py"
    source = "\n".join(path.read_text(encoding="utf-8") for path in list(root.glob("*.py")) + [command])
    forbidden = ["Demo12345", "password=", "token=", "secret="]
    assert not any(item in source for item in forbidden)
    assert "make_password(None)" in source


@pytest.mark.django_db
def test_representative_lifecycles_are_present(monkeypatch, seed_media):
    run_seed_apply(monkeypatch, seed_media)
    assert {"DRAFT", "SUBMITTED", "UNDER_REVIEW", "NEEDS_INFORMATION", "READY_TO_QUOTE", "CLOSED"}.issubset(
        set(SalesRfq.objects.filter(notes__contains=DATASET_MARKER).values_list("status", flat=True))
    )
    quotation_statuses = set(SalesQuotation.objects.filter(idempotency_key__startswith="pdv1-quote").values_list("workflow_status", flat=True))
    assert {"DRAFT", "PENDING_APPROVAL", "APPROVED", "SENT", "REJECTED", "SUPERSEDED", "ACCEPTED", "DECLINED"}.issubset(quotation_statuses)
    order_statuses = set(TransactionOrder.objects.filter(idempotency_key__startswith="pdv1-order").values_list("workflow_status", flat=True))
    assert {"CONFIRMED", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED"}.issubset(order_statuses)
    assert OrderProgressEvent.objects.filter(order__idempotency_key__startswith="pdv1-order").exists()


@pytest.mark.django_db
def test_knowledge_indexing_and_ai_eval_fixtures_are_not_pilot_published(monkeypatch, seed_media):
    run_seed_apply(monkeypatch, seed_media)
    assert KnowledgeDocument.objects.filter(metadata__dataset=DATASET_MARKER).count() == 12
    assert KnowledgeChunk.objects.filter(document__metadata__dataset=DATASET_MARKER).exists()
    result = KnowledgeSearchService(embedding_service=DevelopmentHashEmbeddingProvider()).search(
        "RFQ drawing human approval", limit=3, user=FoundationUser.objects.get(email="sales@production-demo.invalid")
    )
    assert result["sources"] == []
    assert not KnowledgeDocument.objects.filter(
        metadata__dataset=DATASET_MARKER, pilot_corpus_approved=True,
    ).exists()
    cases = load_ai_eval_cases("TEST")
    assert len(cases) == 20
    assert all(case["expected_behavior"] for case in cases)


@pytest.mark.django_db
def test_ai_eval_case_counts_are_profile_specific():
    assert len(load_ai_eval_cases("TEST")) == 20
    assert len(load_ai_eval_cases("SMALL")) == 60
    assert len(load_ai_eval_cases("FULL")) == 150


@pytest.mark.django_db
def test_rag_retrieval_denies_seeded_sources_without_pilot_publication(monkeypatch, seed_media, settings):
    settings.KNOWLEDGE_MIN_RELEVANCE_SCORE = 0.33
    run_seed_apply(monkeypatch, seed_media)
    user = FoundationUser.objects.get(email="sales@production-demo.invalid")
    service = KnowledgeSearchService(embedding_service=DevelopmentHashEmbeddingProvider())
    queries = [
        "CNC first article inspection",
        "SUS304 quotation requirements",
        "RFQ drawing requirement",
        "quotation approval policy",
        "order delivery procedure",
    ]
    for query in queries:
        result = service.search(query, limit=5, user=user)
        assert result["sources"] == [], query
        assert result["confidence"] == 0

    for query in ["medical diagnosis cancer", "football world cup"]:
        result = service.search(query, limit=5, user=user)
        assert result["sources"] == []
        assert result["confidence"] == 0


@pytest.mark.django_db
def test_knowledge_runtime_health_reports_embedding_compatibility(monkeypatch, seed_media):
    run_seed_apply(monkeypatch, seed_media)
    health = KnowledgeRuntimeHealthService(
        embedding_provider=DevelopmentHashEmbeddingProvider(),
        ollama_health=type("FakeOllama", (), {"check": lambda self: {"model_available": True}})(),
    ).check()
    assert health["index"]["incompatible_embedding_signatures"] == []
    assert health["index"]["active_embedding_signature"]["provider"] == "development-hash-fallback"


@pytest.mark.django_db
def test_knowledge_draft_visibility_is_fail_closed_for_admin_role_casing():
    upper_role, _ = FoundationRole.objects.get_or_create(name="Admin")
    lower_role, _ = FoundationRole.objects.get_or_create(name="admin")
    upper = FoundationUser.objects.create(email="upper-admin@example.invalid", full_name="Upper", password_hash="!", role=upper_role)
    lower = FoundationUser.objects.create(email="lower-admin@example.invalid", full_name="Lower", password_hash="!", role=lower_role)
    service = KnowledgeService(embedding_service=DevelopmentHashEmbeddingProvider())
    service.create_document(
        title="[PDV1] Restricted Role Casing Probe",
        content="Restricted role casing probe.",
        permission_level="restricted",
        metadata={"dataset": DATASET_MARKER},
    )
    assert service.list_documents(user=lower).count() == 0
    assert service.list_documents(user=upper).count() == 0


@pytest.mark.django_db
def test_small_profile_apply_history_and_idempotency(monkeypatch, seed_media):
    output = run_seed_apply(monkeypatch, seed_media, profile="SMALL")
    assert seed_report_from_output(output)["counts"]["actual_ai_eval_cases"] == 60
    first_counts = {
        "customers": BusinessCustomer.objects.filter(notes__contains=DATASET_MARKER).count(),
        "materials": BusinessMaterial.objects.filter(description__contains=DATASET_MARKER).count(),
        "parts": BusinessProduct.objects.filter(technical_requirements__contains=DATASET_MARKER).count(),
        "rfqs": SalesRfq.objects.filter(notes__contains=DATASET_MARKER).count(),
        "quotations": SalesQuotation.objects.filter(idempotency_key__startswith="pdv1-quote").count(),
        "orders": TransactionOrder.objects.filter(idempotency_key__startswith="pdv1-order").count(),
        "knowledge": KnowledgeDocument.objects.filter(metadata__dataset=DATASET_MARKER).count(),
    }
    assert first_counts["customers"] == 60
    assert first_counts["materials"] == 35
    assert first_counts["parts"] == 150
    assert first_counts["rfqs"] == 300
    assert first_counts["quotations"] >= 200
    assert first_counts["orders"] >= 90
    assert first_counts["knowledge"] == 60
    for order in TransactionOrder.objects.filter(idempotency_key__startswith="pdv1-order").select_related("source_quotation__rfq")[:10]:
        assert order.source_quotation.rfq.created_at <= order.source_quotation.created_at <= order.ordered_at
        if order.workflow_status == "COMPLETED":
            assert order.progress_percent == 100
    run_seed_apply(monkeypatch, seed_media, profile="SMALL")
    assert BusinessCustomer.objects.filter(notes__contains=DATASET_MARKER).count() == first_counts["customers"]
    assert BusinessMaterial.objects.filter(description__contains=DATASET_MARKER).count() == first_counts["materials"]
    assert BusinessProduct.objects.filter(technical_requirements__contains=DATASET_MARKER).count() == first_counts["parts"]
    assert SalesRfq.objects.filter(notes__contains=DATASET_MARKER).count() == first_counts["rfqs"]
    assert SalesQuotation.objects.filter(idempotency_key__startswith="pdv1-quote").count() == first_counts["quotations"]
    assert TransactionOrder.objects.filter(idempotency_key__startswith="pdv1-order").count() == first_counts["orders"]
    assert KnowledgeDocument.objects.filter(metadata__dataset=DATASET_MARKER).count() == first_counts["knowledge"]


@pytest.mark.django_db
def test_full_profile_dry_run_is_explicit():
    output = io.StringIO()
    with pytest.raises(ValueError, match="FULL is disabled"):
        call_command("seed_production_demo", "--profile", "FULL", "--dry-run", stdout=output)
    assert BusinessCustomer.objects.count() == 0


@pytest.mark.django_db
def test_full_profile_apply_history_and_idempotency(monkeypatch, seed_media):
    with pytest.raises(ValueError, match="FULL is disabled"):
        run_seed_apply(monkeypatch, seed_media, profile="FULL")
