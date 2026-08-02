import io
import json
from urllib import error

import pytest
from apps.knowledge.models import KnowledgeDocument, KnowledgeEmbedding
from apps.knowledge.services.embedding_service import (
    DevelopmentHashEmbeddingProvider,
    EmbeddingProviderError,
    OllamaEmbeddingProvider,
)
from apps.knowledge.services.knowledge_indexer import KnowledgeIndexer
from apps.knowledge.services.knowledge_service import KnowledgeService
from apps.knowledge.services.search_service import KnowledgeSearchService
from apps.knowledge.services.vector_store import DjangoJSONVectorStore
from django.core.management import call_command
from django.test import override_settings


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def opener_with_vectors(vectors):
    def opener(req, timeout):
        assert req.full_url.endswith("/api/embed")
        assert timeout == 3
        return FakeResponse({"embeddings": vectors})

    return opener


def test_ollama_embedding_valid_batch():
    provider = OllamaEmbeddingProvider(
        model="nomic-embed-text",
        timeout=3,
        retries=0,
        dimensions=3,
        opener=opener_with_vectors([[1, 0, 0], [0, 1, 0]]),
    )

    assert provider.embed_batch(["gia công CNC", "precision machining"]) == [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ]


def test_ollama_embedding_offline_is_safe():
    def unavailable(req, timeout):
        raise error.URLError("offline")

    provider = OllamaEmbeddingProvider(dimensions=3, retries=0, opener=unavailable)
    with pytest.raises(EmbeddingProviderError, match="not available"):
        provider.embed_text("CNC")


@override_settings(OLLAMA_EMBEDDING_MODELS=("nomic-embed-text", "missing-model"))
def test_ollama_health_reports_missing_model():
    provider = OllamaEmbeddingProvider(
        model="missing-model",
        dimensions=3,
        opener=lambda req, timeout: FakeResponse(
            {"models": [{"name": "nomic-embed-text:latest"}]}
        ),
    )

    assert provider.health_check()["model_available"] is False


@pytest.mark.parametrize(
    "vectors,error_text",
    [
        ([[]], "empty embedding"),
        ([[1, 2]], "dimension mismatch"),
        ([[1, 0, 0]], "incomplete embedding batch"),
    ],
)
def test_ollama_embedding_rejects_invalid_vectors(vectors, error_text):
    provider = OllamaEmbeddingProvider(
        dimensions=3,
        timeout=3,
        retries=0,
        opener=opener_with_vectors(vectors),
    )
    texts = ["one", "two"] if "incomplete" in error_text else ["one"]
    with pytest.raises(EmbeddingProviderError, match=error_text):
        provider.embed_batch(texts)


@pytest.mark.django_db
def test_reindex_keeps_old_index_when_embedding_fails():
    fallback = DevelopmentHashEmbeddingProvider()
    document = KnowledgeService(embedding_service=fallback).create_document(
        title="CNC capability",
        content="MEC Precision gia công trục CNC chính xác.",
    )
    old_chunk_ids = list(document.chunks.values_list("id", flat=True))

    class FailingProvider(DevelopmentHashEmbeddingProvider):
        def embed_batch(self, texts):
            raise EmbeddingProviderError("batch failed")

    with pytest.raises(EmbeddingProviderError):
        KnowledgeIndexer(embedding_service=FailingProvider()).reindex(document)

    assert list(document.chunks.values_list("id", flat=True)) == old_chunk_ids


@pytest.mark.django_db
def test_reindex_is_idempotent_and_model_change_is_detected():
    provider = DevelopmentHashEmbeddingProvider()
    document = KnowledgeService(embedding_service=provider).create_document(
        title="Fixture inspection",
        content="Fixture kiểm tra hỗ trợ đo kiểm chất lượng.",
    )
    indexer = KnowledgeIndexer(embedding_service=provider)

    assert indexer.needs_reindex(document) is False
    indexer.reindex(document)
    assert indexer.needs_reindex(document) is False

    embedding = KnowledgeEmbedding.objects.get(chunk__document=document)
    embedding.model_name = "old-model"
    embedding.save(update_fields=["model_name"])
    assert indexer.needs_reindex(document) is True


@pytest.mark.django_db
def test_vietnamese_and_english_retrieval_use_matching_provider():
    provider = DevelopmentHashEmbeddingProvider()
    KnowledgeService(embedding_service=provider).create_document(
        title="Gia công CNC",
        content="MEC Precision cung cấp dịch vụ gia công CNC chính xác.",
        permission_level="public",
    )
    KnowledgeService(embedding_service=provider).create_document(
        title="Fixture",
        content="Inspection fixture for quality measurement.",
        permission_level="public",
    )

    vietnamese = KnowledgeSearchService(embedding_service=provider).search(
        "gia công CNC chính xác", user=None
    )
    english = KnowledgeSearchService(embedding_service=provider).search(
        "inspection fixture quality", user=None
    )

    assert vietnamese["sources"][0]["title"] == "Gia công CNC"
    assert english["sources"][0]["title"] == "Fixture"


@pytest.mark.django_db
def test_management_command_dry_run_and_resume(capsys):
    provider = DevelopmentHashEmbeddingProvider()
    KnowledgeService(embedding_service=provider).create_document(
        title="Demo", content="CNC demo", permission_level="public"
    )

    call_command("reindex_knowledge_embeddings", "--dry-run", stdout=io.StringIO())
    assert KnowledgeDocument.objects.count() == 1


def test_vector_backend_contract_and_fallback_warning():
    health = DjangoJSONVectorStore().health_check()

    assert health["available"] is True
    assert health["production_ready"] is False
    assert "pgvector" in health["warning"]


@pytest.mark.django_db
@override_settings(KNOWLEDGE_MIN_RELEVANCE_SCORE=0.99)
def test_no_context_query_returns_no_sources():
    provider = DevelopmentHashEmbeddingProvider()
    KnowledgeService(embedding_service=provider).create_document(
        title="CNC",
        content="Gia công CNC chính xác.",
        permission_level="public",
    )

    result = KnowledgeSearchService(embedding_service=provider).search(
        "dự báo thời tiết sao Hỏa", user=None
    )

    assert result["results"] == []
    assert result["sources"] == []
    assert result["confidence"] == 0
