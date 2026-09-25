"""Fail-closed knowledge-source boundary for AI Sales."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from apps.knowledge.models import KnowledgeDocument
from apps.knowledge.services.synthetic_rag_demo import SyntheticRagWebDemoService


class AISalesKnowledgeSourceService:
    """Keep synthetic RAG active until governed production knowledge is approved."""

    synthetic_source = "governed_synthetic"

    def build(self):
        source = str(
            getattr(settings, "AI_SALES_KNOWLEDGE_SOURCE", self.synthetic_source)
        ).strip()
        if source != self.synthetic_source:
            raise ImproperlyConfigured(
                "AI Sales production knowledge is not enabled; use governed_synthetic."
            )
        return SyntheticRagWebDemoService()

    @staticmethod
    def production_readiness():
        """Return content-free readiness counts; never treat them as release approval."""
        governed = KnowledgeDocument.objects.filter(
            status__in=["APPROVED", "INDEXED"],
            active_version=True,
            approved_at__isnull=False,
        ).exclude(approval_hash="")
        indexed = governed.filter(status="INDEXED").count()
        sales_scoped = governed.filter(
            permission_level__in=["internal", "restricted"],
            department="SALES",
            pilot_corpus_approved=True,
        ).count()
        return {
            "configured_source": AISalesKnowledgeSourceService.synthetic_source,
            "governed_document_count": governed.count(),
            "indexed_document_count": indexed,
            "sales_scoped_document_count": sales_scoped,
            "production_source_enabled": False,
            "human_release_approval_required": True,
        }
