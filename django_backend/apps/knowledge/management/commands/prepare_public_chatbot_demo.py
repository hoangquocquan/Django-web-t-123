"""Expose draft copies only inside the isolated public-chatbot demo database."""

from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.knowledge.models import KnowledgeDocument
from apps.knowledge.services.knowledge_indexer import KnowledgeIndexer


class Command(BaseCommand):
    """Prepare exactly one draft dataset for public-only end-to-end testing."""

    help = (
        "Mark copies of one public-chatbot draft dataset as public. This command "
        "refuses to run outside config.settings.public_chatbot_demo."
    )

    def add_arguments(self, parser):
        parser.add_argument("input_path")

    def handle(self, *args, **options):
        if not getattr(settings, "PUBLIC_CHATBOT_DEMO_ISOLATED", False):
            raise CommandError(
                "Refusing to prepare public copies outside the isolated chatbot demo."
            )

        input_path = Path(options["input_path"]).expanduser().resolve()
        try:
            payload = json.loads(input_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CommandError(f"Cannot read valid UTF-8 JSON: {exc}") from exc

        dataset = str(payload.get("dataset") or "").strip()
        documents = payload.get("documents")
        if not dataset or not isinstance(documents, list) or len(documents) != 5:
            raise CommandError("Expected one dataset containing exactly five documents.")
        keys = [str(item.get("key") or "").strip() for item in documents]
        if any(not key for key in keys) or len(set(keys)) != 5:
            raise CommandError("The five draft document keys must be non-empty and unique.")

        candidates = list(
            KnowledgeDocument.objects.filter(
                metadata__public_dataset=dataset,
                metadata__public_dataset_key__in=keys,
            ).order_by("id")
        )
        found_keys = {
            document.metadata.get("public_dataset_key") for document in candidates
        }
        if len(candidates) != 5 or found_keys != set(keys):
            raise CommandError(
                "The isolated database does not contain an exact copy of the draft dataset."
            )

        candidate_ids = {document.id for document in candidates}
        public_outside_dataset = KnowledgeDocument.objects.filter(
            permission_level="public"
        ).exclude(id__in=candidate_ids)
        if public_outside_dataset.exists():
            raise CommandError(
                "The isolated database already contains public documents outside the draft dataset."
            )

        indexer = KnowledgeIndexer()
        with transaction.atomic():
            for document in candidates:
                metadata = dict(document.metadata or {})
                metadata["public_review_status"] = "isolated_demo_copy_only"
                metadata["public_demo_source_permission"] = "internal"
                document.metadata = metadata
                document.permission_level = "public"
                document.save(update_fields=["metadata", "permission_level", "updated_at"])
                indexer.reindex(
                    document,
                    created_by_email="isolated-public-chatbot-demo@localhost.invalid",
                    change_note="Expose copied draft only in isolated verification database",
                )

        result = {
            "database": str(settings.DATABASES["default"]["NAME"]),
            "isolated": True,
            "dataset": dataset,
            "public_document_ids": sorted(candidate_ids),
            "public_document_count": KnowledgeDocument.objects.filter(
                permission_level="public"
            ).count(),
            "internal_document_count": KnowledgeDocument.objects.filter(
                permission_level="internal"
            ).count(),
        }
        self.stdout.write(json.dumps(result, ensure_ascii=True, indent=2))
