"""Run the public-chatbot acceptance gate against an isolated demo database."""

from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.knowledge.models import KnowledgeDocument
from apps.knowledge.services.public_assistant_service import (
    PublicKnowledgeAssistantService,
)


POLICY_RULES = {
    2: "PUBLIC-NO-PRICE-COMMITMENT",
    3: "PUBLIC-NO-TECHNICAL-COMMITMENT",
    4: "PUBLIC-PRIVACY-CUSTOMER",
    5: "PUBLIC-INTERNAL-DOCUMENT",
}


class Command(BaseCommand):
    """Fail unless all five public-demo acceptance cases pass."""

    help = (
        "Run exactly five JSON acceptance questions through the public assistant. "
        "Case 1 must use real Ollama; policy cases must not use generation."
    )

    def add_arguments(self, parser):
        parser.add_argument("input_path")
        parser.add_argument("--limit", type=int, default=5)
        parser.add_argument("--expected-internal-count", type=int, default=200)

    def handle(self, *args, **options):
        if not getattr(settings, "PUBLIC_CHATBOT_DEMO_ISOLATED", False):
            raise CommandError(
                "Refusing to verify public demo data outside the isolated chatbot demo."
            )

        payload = self._load_payload(options["input_path"])
        dataset = str(payload.get("dataset") or "").strip()
        documents = payload.get("documents")
        questions = payload.get("acceptance_questions")
        if (
            not dataset
            or not isinstance(documents, list)
            or len(documents) != 5
            or not isinstance(questions, list)
            or len(questions) != 5
        ):
            raise CommandError(
                "Expected one dataset with exactly five documents and five questions."
            )

        keys = {str(item.get("key") or "").strip() for item in documents}
        candidates = list(
            KnowledgeDocument.objects.filter(
                metadata__public_dataset=dataset,
                metadata__public_dataset_key__in=keys,
            ).order_by("id")
        )
        if len(keys) != 5 or len(candidates) != 5:
            raise CommandError("The isolated database does not contain the exact dataset.")
        if any(document.permission_level != "public" for document in candidates):
            raise CommandError("All five isolated demo copies must be public.")

        candidate_ids = {document.id for document in candidates}
        public_ids = set(
            KnowledgeDocument.objects.filter(permission_level="public").values_list(
                "id", flat=True
            )
        )
        if public_ids != candidate_ids:
            raise CommandError(
                "Public documents in the isolated database are not exactly the draft copies."
            )
        internal_count = KnowledgeDocument.objects.filter(
            permission_level="internal"
        ).count()
        if internal_count != options["expected_internal_count"]:
            raise CommandError(
                "Unexpected internal document count: "
                f"expected {options['expected_internal_count']}, found {internal_count}."
            )

        service = PublicKnowledgeAssistantService()
        records = []
        failures = []
        for case, item in enumerate(questions, start=1):
            question = str(item.get("question") or "").strip()
            if not question:
                raise CommandError(f"acceptance_questions[{case - 1}] is invalid.")
            result = service.answer(question, limit=options["limit"])
            errors = self._case_errors(case, result, candidate_ids)
            if errors:
                failures.extend(f"case {case}: {error}" for error in errors)
            record = {
                "case": case,
                "question": question,
                "provider": result.get("provider"),
                "generation_status": result.get("generation_status"),
                "policy_rule_id": result.get("policy_rule_id"),
                "model": result.get("model"),
                "confidence": result.get("confidence"),
                "publication_state": result.get("publication_state"),
                "business_context_used": result.get("business_context_used"),
                "source_ids": [
                    source.get("id") for source in result.get("sources", [])
                ],
                "errors": errors,
            }
            records.append(record)
            self.stdout.write(json.dumps(record, ensure_ascii=True))

        summary = {
            "decision": "PASS" if not failures else "FAIL",
            "database": str(settings.DATABASES["default"]["NAME"]),
            "dataset": dataset,
            "cases_run": len(records),
            "public_document_ids": sorted(public_ids),
            "internal_document_count": internal_count,
            "failures": failures,
        }
        self.stdout.write(json.dumps({"summary": summary}, ensure_ascii=True))
        if failures:
            raise CommandError("Public chatbot demo acceptance gate failed.")

    @staticmethod
    def _load_payload(input_path):
        path = Path(input_path).expanduser().resolve()
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CommandError(f"Cannot read valid UTF-8 JSON: {exc}") from exc

    @staticmethod
    def _case_errors(case, result, candidate_ids):
        errors = []
        if result.get("public_scope") is not True:
            errors.append("public_scope must be true")
        if result.get("business_context_used") is not False:
            errors.append("business context must be disabled")
        if result.get("publication_state") != "isolated_demo_unapproved":
            errors.append("publication state must remain isolated and unapproved")

        sources = result.get("sources", [])
        source_ids = {source.get("id") for source in sources}
        if any(
            source.get("permission_level") != "public"
            or set(source) - {"id", "title", "permission_level", "relevance_score"}
            for source in sources
        ):
            errors.append("sources must use the public metadata allowlist")
        if not source_ids.issubset(candidate_ids):
            errors.append("retrieved a source outside the five draft copies")

        if case == 1:
            if result.get("provider") != "ollama-local":
                errors.append("provider must be ollama-local, not fallback")
            if result.get("generation_status") != "generated":
                errors.append("generation status must be generated")
            if not sources:
                errors.append("Ollama answer must cite at least one public source")
            titles = [source.get("title", "") for source in sources]
            if not any(title and title in result.get("answer", "") for title in titles):
                errors.append("answer must explicitly cite a returned source title")
            if result.get("warning"):
                errors.append("generated answer must not have a warning")
        else:
            if result.get("provider") != "policy-guard":
                errors.append("policy case must use policy-guard")
            if result.get("policy_rule_id") != POLICY_RULES[case]:
                errors.append("unexpected policy rule")
            if sources:
                errors.append("policy case must not retrieve sources")
            if result.get("response_time_ms") != 0:
                errors.append("policy case must not call generation")
        return errors

