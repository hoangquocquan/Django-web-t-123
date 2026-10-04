"""Run staged chatbot acceptance questions against draft-only documents."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.knowledge.models import KnowledgeChunk, KnowledgeDocument
from apps.knowledge.services.assistant_service import KnowledgeAssistantService
from apps.knowledge.services.embedding_service import get_embedding_provider
from apps.knowledge.services.knowledge_service import search_result_to_dict
from apps.knowledge.services.search_service import KnowledgeSearchService
from apps.knowledge.services.vector_store import DjangoJSONVectorStore


class DraftDatasetSearchService:
    """Search only one staged dataset, regardless of other internal documents."""

    def __init__(self, dataset):
        self.dataset = dataset
        self.embedding_service = get_embedding_provider()
        self.vector_store = DjangoJSONVectorStore()
        self.formatter = KnowledgeSearchService(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
        )

    def search(self, query, limit=5, user=None):
        del user
        query_vector = self.embedding_service.embed(query)
        readable = list(
            KnowledgeChunk.objects.select_related(
                "document", "embedding", "document__category"
            ).filter(
                document__metadata__public_dataset=self.dataset,
                document__permission_level="internal",
            )
        )
        vector_results = self.vector_store.search(
            query_vector=query_vector,
            queryset=readable,
            limit=max(limit, 100),
            provider=self.embedding_service,
        )
        results = self.formatter._rerank_with_lexical_overlap(
            query, readable, vector_results, limit
        )
        return {
            "results": [search_result_to_dict(result) for result in results],
            "sources": self.formatter.sources_from_results(results),
            "confidence": self.formatter.confidence(results),
        }


class Command(BaseCommand):
    """Exercise JSON acceptance questions without publishing the draft."""

    help = "Run draft acceptance questions using only staged internal documents."

    def add_arguments(self, parser):
        parser.add_argument("input_path")
        parser.add_argument("--limit", type=int, default=5)

    def handle(self, *args, **options):
        input_path = Path(options["input_path"]).expanduser().resolve()
        try:
            payload = json.loads(input_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CommandError(f"Cannot read valid UTF-8 JSON: {exc}") from exc
        dataset = str(payload.get("dataset") or "").strip()
        questions = payload.get("acceptance_questions")
        if not dataset or not isinstance(questions, list) or len(questions) != 5:
            raise CommandError("Expected a dataset and exactly five acceptance questions.")

        staged = KnowledgeDocument.objects.filter(metadata__public_dataset=dataset)
        if staged.count() != len(payload.get("documents") or []):
            raise CommandError("The complete draft dataset has not been imported.")
        if staged.exclude(permission_level="internal").exists():
            raise CommandError("Draft verification requires every staged document to remain internal.")

        service = KnowledgeAssistantService(
            search_service=DraftDatasetSearchService(dataset)
        )
        candidate_ids = set(staged.values_list("id", flat=True))
        results = []
        for index, item in enumerate(questions, start=1):
            if not isinstance(item, dict) or not str(item.get("question") or "").strip():
                raise CommandError(f"acceptance_questions[{index - 1}] is invalid.")
            question = str(item["question"]).strip()
            answer = service.answer(question, user=None, limit=options["limit"])
            source_ids = {
                source.get("id") for source in answer.get("sources", [])
            }
            anonymous = KnowledgeSearchService().search(question, limit=10, user=None)
            public_exposed_candidate_ids = sorted(
                candidate_ids.intersection(
                    source.get("id") for source in anonymous.get("sources", [])
                )
            )
            record = {
                "case": index,
                "question": question,
                "expected": str(item.get("expected") or ""),
                "answer": answer.get("answer", ""),
                "provider": answer.get("provider"),
                "generation_status": answer.get("generation_status"),
                "confidence": answer.get("confidence"),
                "warning": answer.get("warning", ""),
                "sources": [
                    {
                        "id": source.get("id"),
                        "title": source.get("title"),
                        "relevance_score": source.get("relevance_score"),
                    }
                    for source in answer.get("sources", [])
                ],
                "sources_are_draft_only": source_ids.issubset(candidate_ids),
                "candidate_visible_anonymously": bool(public_exposed_candidate_ids),
            }
            results.append(record)
            self.stdout.write(json.dumps(record, ensure_ascii=True))

        summary = {
            "dataset": dataset,
            "cases_run": len(results),
            "all_sources_draft_only": all(
                item["sources_are_draft_only"] for item in results
            ),
            "any_candidate_visible_anonymously": any(
                item["candidate_visible_anonymously"] for item in results
            ),
            "public_document_count": KnowledgeDocument.objects.filter(
                permission_level="public"
            ).count(),
            "staged_document_count": staged.count(),
            "staged_permission_levels": sorted(
                set(staged.values_list("permission_level", flat=True))
            ),
        }
        self.stdout.write(json.dumps({"summary": summary}, ensure_ascii=True))
