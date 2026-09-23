"""Content-free metrics for controlled pilot operations."""

from __future__ import annotations

from collections import Counter

from django.db.models import Count

from apps.knowledge.models import (
    KnowledgeAssistantFeedback, KnowledgeAuditEvent, KnowledgeGapReview,
    KnowledgeHumanEvaluation,
)


class PilotMonitoringService:
    """Aggregate operational and quality metadata without answer text."""

    def snapshot(self):
        query_events = KnowledgeAuditEvent.objects.filter(event="query")
        source_counter = Counter()
        for source_ids in query_events.values_list("source_ids", flat=True):
            source_counter.update(source_ids or [])
        feedback = {
            row["category"]: row["count"]
            for row in KnowledgeAssistantFeedback.objects.values("category")
            .annotate(count=Count("id"))
            .order_by("category")
        }
        ratings = {
            row["rating"]: row["count"]
            for row in KnowledgeHumanEvaluation.objects.values("rating")
            .annotate(count=Count("id"))
            .order_by("rating")
        }
        evaluations = KnowledgeHumanEvaluation.objects.all()
        evaluation_total = evaluations.count()
        feedback_total = KnowledgeAssistantFeedback.objects.count()
        successful_retrieval = query_events.filter(decision="allowed").count()
        gaps = {
            row["category"]: row["count"]
            for row in KnowledgeGapReview.objects.values("category")
            .annotate(count=Count("id"))
            .order_by("category")
        }
        return {
            "queries": query_events.count(),
            "successful_retrieval": successful_retrieval,
            "failed_retrieval": query_events.filter(decision="denied").count(),
            "permission_denied": KnowledgeAuditEvent.objects.filter(decision="denied").exclude(event="query").count(),
            "top_document_ids": [
                {"document_id": document_id, "uses": uses}
                for document_id, uses in source_counter.most_common(10)
            ],
            "feedback": feedback,
            "human_evaluation": {
                "total": evaluation_total,
                "ratings": ratings,
                "hallucinations": evaluations.filter(hallucination=True).count(),
                "missing_information": evaluations.filter(missing_information=True).count(),
                "invalid_citations": evaluations.filter(citation_valid=False).count(),
                "permission_failures": evaluations.filter(permission_correct=False).count(),
                "citation_coverage": (
                    evaluations.filter(citation_valid=True).count() / evaluation_total
                    if evaluation_total else None
                ),
                "correctness_rate": (
                    evaluations.filter(rating="CORRECT").count() / evaluation_total
                    if evaluation_total else None
                ),
            },
            "user_satisfaction": (
                KnowledgeAssistantFeedback.objects.filter(category="HELPFUL").count() / feedback_total
                if feedback_total else None
            ),
            "knowledge_gaps": gaps,
        }


