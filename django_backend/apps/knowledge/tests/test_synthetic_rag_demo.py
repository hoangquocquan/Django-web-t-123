"""Safety and idempotency tests for the bounded synthetic RAG dataset."""

from __future__ import annotations

import csv

import pytest

from apps.business_core.models import BusinessProduct
from apps.knowledge.models import KnowledgeDocument
from apps.knowledge.services.access_policy import KnowledgeAccessPolicy
from apps.knowledge.services.synthetic_rag_demo import (
    DATASET_ID, REQUIRED_HEADERS, build_test_questions,
    create_and_index_knowledge, import_products, validate_source,
)


def synthetic_row(code="SYN-RAG-0001"):
    row = {header: "" for header in REQUIRED_HEADERS}
    row.update({
        "Source System *": "RAG_SYNTHETIC_DEMO_V1",
        "Source Record ID *": code,
        "Source Revision": "1",
        "Part Code *": code,
        "Product Name *": "[SYNTHETIC DEMO] Test Bracket",
        "Revision": "A",
        "Unit *": "PCS",
        "Category Code *": "SYN-CAT-01",
        "Public Title *": "[SYNTHETIC DEMO] Test Bracket",
        "Public Description *": "[SYNTHETIC / NOT REAL COMPANY DATA] Fictional bracket.",
        "Material Code": "SYN-MAT-01",
        "Material Grade": "6061-T6",
        "Manufacturing Process": "CNC milling",
        "Public Specification 1 - Label": "Tolerance",
        "Public Specification 1 - Value": "±0.05 mm",
        "Application": "Test fixture",
        "Industry": "Technical demo",
        "Publication Approved? (YES/NO)": "NO",
        "Dataset ID *": DATASET_ID,
        "Source Type *": "SYNTHETIC",
        "Synthetic *": "TRUE",
        "Production Eligible *": "FALSE",
        "Authoritative *": "FALSE",
        "Created For *": "technical_rag_demo",
    })
    return row


def write_csv(path, rows):
    headers = sorted(set(REQUIRED_HEADERS) | {"Source Revision", "Public Specification 1 - Label", "Public Specification 1 - Value"})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def test_validation_rejects_non_synthetic_provenance_and_formula(tmp_path):
    row = synthetic_row()
    row["Authoritative *"] = "TRUE"
    row["Application"] = "=HYPERLINK(\"https://invalid\")"
    path = tmp_path / "unsafe.csv"
    write_csv(path, [row])

    result = validate_source(path)

    assert result.valid == 0
    assert result.rejected == 1
    assert any("Authoritative" in error and "formula-like" in error for error in result.errors)


@pytest.mark.django_db
def test_synthetic_product_import_is_idempotent_and_stays_non_public():
    row = synthetic_row()

    first = import_products([row])
    second = import_products([row])

    product = BusinessProduct.objects.get(part_code="SYN-RAG-0001")
    assert first["created"] == 1 and second["existing"] == 1
    assert product.status == "synthetic_demo"
    assert product.sku == DATASET_ID
    assert "authoritative=false" in product.description
    assert product.status == "synthetic_demo"


@pytest.mark.django_db
def test_synthetic_knowledge_is_internal_indexed_and_publicly_ineligible(settings):
    settings.KNOWLEDGE_EMBEDDING_PROVIDER = "development-hash"
    row = synthetic_row()
    imported = import_products([row])

    result = create_and_index_knowledge([row], imported["product_ids"])

    document = KnowledgeDocument.objects.get(metadata__dataset_id=DATASET_ID)
    assert result["indexed"] == 1
    assert document.metadata["synthetic"] is True
    assert document.metadata["production_eligible"] is False
    assert document.permission_level == "internal"
    assert document.ai_public_approved is False
    assert document.pilot_corpus_approved is False
    assert document.chunks.count() == document.chunks.filter(embedding__isnull=False).count() >= 1
    assert not KnowledgeAccessPolicy().eligible_documents(None).filter(pk=document.pk).exists()


def test_question_set_is_bounded_and_has_twenty_percent_unknowns():
    rows = [synthetic_row(f"SYN-RAG-{index:04d}") for index in range(1, 26)]

    questions = build_test_questions(rows)

    assert len(questions) == 40
    assert sum(item["allowed_unknown_behavior"] for item in questions) == 8
    assert all("expected_citation" in item for item in questions)
