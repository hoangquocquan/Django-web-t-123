"""Canonical and public AI assistant integration boundaries."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.ai.models import AIRequestLog
from apps.ai.services.policy_service import AIPolicyContext
from apps.ai.services.rate_limit_service import AIRateLimiter
from apps.foundation.models import FoundationAuthToken, FoundationRole, FoundationUser
from apps.foundation.services import FoundationAuthService
from apps.knowledge.services.assistant_service import PublicKnowledgeAssistantService
from apps.knowledge.services.rag_pipeline import AIRequestLogService


def _user_session(role_name, suffix):
    role = FoundationRole.objects.get(name=role_name, is_active=True)
    user = FoundationUser.objects.create(
        email=f"{suffix}@canonical-ai.invalid",
        full_name=f"Canonical AI {suffix}",
        password_hash="test-only",
        role=role,
    )
    raw_token = f"canonical-ai-{suffix}-token"
    FoundationAuthToken.objects.create(
        user=user,
        token_hash=FoundationAuthService.hash_token(raw_token),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    return user, raw_token


def _auth(raw_token):
    return {"HTTP_AUTHORIZATION": f"Bearer {raw_token}"}


@pytest.mark.django_db
def test_sales_ai_is_canonical_advisory_and_sales_authorized(client, monkeypatch):
    user, token = _user_session("Sales", "sales")
    observed = {}

    class FakeSalesAssistant:
        def handle(self, *, action, payload, user):
            observed.update(action=action, payload=payload, user=user)
            return {
                "action": action,
                "recommendations": ["Review the RFQ"],
                "human_approval_required": True,
                "autonomous_action": False,
            }

    monkeypatch.setattr(
        "apps.api.views.canonical_ai.SalesAssistantService",
        FakeSalesAssistant,
    )
    response = client.post(
        "/api/v1/canonical/ai/sales-assistant/",
        {
            "action": "lead_analysis",
            "payload": {
                "company": "Fictional Robotics",
                "contact_person": "Fictional Buyer",
            },
        },
        content_type="application/json",
        **_auth(token),
    )

    assert response.status_code == 200, response.json()
    assert observed["user"] == user
    assert observed["action"] == "lead_analysis"
    assert response.json()["data"]["human_approval_required"] is True
    assert response.json()["data"]["autonomous_action"] is False


@pytest.mark.django_db
def test_manager_cannot_use_sales_ai_but_can_use_internal_knowledge(client, monkeypatch):
    user, token = _user_session("Manager", "manager")

    denied = client.post(
        "/api/v1/canonical/ai/sales-assistant/",
        {"action": "weekly_recommendation", "payload": {}},
        content_type="application/json",
        **_auth(token),
    )
    assert denied.status_code == 403

    class FakeKnowledgeAssistant:
        def answer(self, question, *, user, limit):
            return {
                "answer": "Source-grounded answer",
                "sources": [{"id": 1, "title": "Quality procedure"}],
                "confidence": 0.9,
                "warning": "",
            }

    monkeypatch.setattr(
        "apps.api.views.canonical_ai.KnowledgeAssistantService",
        FakeKnowledgeAssistant,
    )
    response = client.post(
        "/api/v1/canonical/ai/knowledge-assistant/",
        {"question": "What is the inspection process?", "limit": 3},
        content_type="application/json",
        **_auth(token),
    )

    assert response.status_code == 200, response.json()
    assert response.json()["data"]["sources"][0]["title"] == "Quality procedure"


@pytest.mark.django_db
def test_public_ai_needs_no_token_and_uses_public_facade(client, monkeypatch):
    class FakePublicAssistant:
        def answer(self, question, limit):
            assert limit == 3
            return {
                "answer": f"Public answer for: {question}",
                "sources": [],
                "scope": "public_knowledge_only",
                "contact_recommended": True,
            }

    monkeypatch.setattr(
        "apps.api.views.public_ai.PublicKnowledgeAssistantService",
        FakePublicAssistant,
    )
    response = client.post(
        "/api/v1/public/ai/assistant/",
        {"question": "Can you machine SUS304?"},
        content_type="application/json",
    )

    assert response.status_code == 200, response.json()
    assert response.json()["data"]["scope"] == "public_knowledge_only"
    assert response.json()["data"]["contact_recommended"] is True


def test_public_ai_facade_removes_private_source_metadata():
    class FakeAssistant:
        def answer(self, question, user, limit):
            assert user is None
            return {
                "answer": "Public facts only",
                "sources": [
                    {
                        "id": 7,
                        "title": "Public capability",
                        "description": "CNC capability",
                        "category": "Capability",
                        "relevance_score": 0.8,
                        "source_path": "/private/server/path.pdf",
                        "created_by_email": "employee@example.invalid",
                        "metadata": {"internal": True},
                    }
                ],
            }

    result = PublicKnowledgeAssistantService(assistant=FakeAssistant()).answer(
        "What can you make?"
    )

    assert result["scope"] == "public_knowledge_only"
    assert result["contact_recommended"] is False
    assert result["sources"] == [
        {
            "id": 7,
            "title": "Public capability",
            "description": "CNC capability",
            "category": "Capability",
            "relevance_score": 0.8,
        }
    ]


def test_public_rate_limit_is_isolated_by_client_ip():
    class CountingBackend:
        backend_name = "test"

        def __init__(self):
            self.counts = {}

        def increment(self, key, window_seconds):
            del window_seconds
            self.counts[key] = self.counts.get(key, 0) + 1
            return self.counts[key]

    limiter = AIRateLimiter(backend=CountingBackend(), default_limit=1)
    context = AIPolicyContext(endpoint="public/ai/assistant", action="chat")

    first = limiter.enforce(context=context, ip_address="192.0.2.10")
    second = limiter.enforce(context=context, ip_address="192.0.2.11")

    assert all(item.allowed for item in first)
    assert all(item.allowed for item in second)


@pytest.mark.django_db
def test_anonymous_ai_log_hashes_question_without_storing_preview():
    AIRequestLogService().log(
        user=None,
        question="Contact me at public-user@example.invalid",
        retrieval={"sources": []},
        model="test-model",
        response_time_ms=1,
        confidence=0,
        warning="",
        status="fallback",
    )

    log = AIRequestLog.objects.get()
    assert log.question_hash
    assert log.question_preview == ""
