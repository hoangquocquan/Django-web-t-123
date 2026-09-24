import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from apps.foundation.models import FoundationUser
from apps.foundation.services import FoundationUserService
from apps.knowledge.models import KnowledgeDocument
from apps.knowledge.services.document_intelligence import DocumentIntelligenceService


@pytest.fixture
def knowledge_admin():
    """Tao admin co quyen doc/ghi knowledge."""
    existing = FoundationUser.objects.filter(email="doc-ai-admin@example.com").first()
    if existing:
        return existing
    return FoundationUserService().create_user(
        email="doc-ai-admin@example.com",
        full_name="Document AI Admin",
        password="SecurePass123!",
        role_name="admin",
    )


def login(client, user):
    """Dang nhap de test UI upload tai lieu."""
    return client.post("/admin/login/", data={"email": user.email, "password": "SecurePass123!"}, follow=True)


@pytest.mark.django_db
def test_document_intelligence_ingests_txt_and_adds_metadata(tmp_path, knowledge_admin):
    with override_settings(MEDIA_ROOT=tmp_path):
        upload = SimpleUploadedFile(
            "cnc-spec.txt",
            b"CNC shaft specification tolerance inspection quality procedure",
            content_type="text/plain",
        )
        result = DocumentIntelligenceService().ingest_uploaded_document(
            upload,
            title="CNC Shaft Spec",
            created_by_email=knowledge_admin.email,
        )

    document = result.document
    metadata = document.metadata["document_intelligence"]

    assert document.title == "CNC Shaft Spec"
    assert metadata["classification"] in {"technical", "quality"}
    assert metadata["human_approval_required"] is True
    assert document.status == "DRAFT"
    assert not document.chunks.exists()
    assert result.citations == []


@pytest.mark.django_db
def test_document_intelligence_answer_has_sources(tmp_path, knowledge_admin):
    with override_settings(MEDIA_ROOT=tmp_path):
        upload = SimpleUploadedFile("quality.txt", b"Quality inspection procedure for CNC fixture.", content_type="text/plain")
        DocumentIntelligenceService().ingest_uploaded_document(upload, title="Quality Procedure")

    answer = DocumentIntelligenceService().answer_with_sources("inspection CNC fixture", user=knowledge_admin)

    assert answer["human_approval_required"] is True
    assert "confidence" in answer
    assert isinstance(answer["sources"], list)


@pytest.mark.django_db
def test_document_intelligence_ui_upload_and_search(client, tmp_path, knowledge_admin):
    login(client, knowledge_admin)
    with override_settings(MEDIA_ROOT=tmp_path):
        response = client.post(
            "/business/documents/",
            data={
                "mode": "upload",
                "title": "Fixture Catalogue",
                "document": SimpleUploadedFile("fixture.txt", b"Fixture catalogue product CNC", content_type="text/plain"),
            },
            follow=True,
        )
        search_response = client.post(
            "/business/documents/",
            data={"mode": "search", "question": "fixture product"},
            follow=True,
        )

    assert response.status_code == 200
    assert b"Fixture Catalogue" in response.content
    assert search_response.status_code == 200
    assert KnowledgeDocument.objects.filter(title="Fixture Catalogue").exists()

