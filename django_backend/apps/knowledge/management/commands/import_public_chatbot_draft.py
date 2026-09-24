"""Import a reviewed chatbot draft as internal-only knowledge documents."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.knowledge.models import KnowledgeDocument
from apps.knowledge.services.knowledge_indexer import KnowledgeIndexer


class Command(BaseCommand):
    """Stage public-chatbot candidate documents without publishing them."""

    help = (
        "Import a public-chatbot JSON draft idempotently. Every imported "
        "document is forced to permission_level=internal."
    )

    def add_arguments(self, parser):
        parser.add_argument("input_path")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument(
            "--created-by",
            default="ai.demo@production-demo.invalid",
        )

    def handle(self, *args, **options):
        input_path = Path(options["input_path"]).expanduser().resolve()
        payload = self._load_payload(input_path)
        dataset = self._required_text(payload, "dataset", "dataset")
        documents = payload.get("documents")
        if not isinstance(documents, list) or not documents:
            raise CommandError("JSON must contain a non-empty documents array.")

        normalized = [self._validate_document(item, index) for index, item in enumerate(documents)]
        keys = [item["key"] for item in normalized]
        if len(keys) != len(set(keys)):
            raise CommandError("Document keys must be unique within the JSON file.")

        counts = {"created": 0, "updated": 0, "unchanged": 0}
        imported = []
        for item in normalized:
            existing = KnowledgeDocument.objects.filter(
                metadata__public_dataset_key=item["key"]
            )
            if existing.count() > 1:
                raise CommandError(
                    f"More than one document uses public_dataset_key={item['key']}."
                )
            document = existing.first()
            action = "created" if document is None else "unchanged"
            metadata = {
                "public_dataset": dataset,
                "public_dataset_key": item["key"],
                "public_review_status": "pending_owner_review",
                "review_points": item["review_points"],
                "source_file": input_path.name,
            }
            values = {
                "title": item["title"],
                "description": item["description"],
                "content": item["content"],
                "source_type": item["source_type"],
                "source_path": "",
                "permission_level": "internal",
                "created_by_email": options["created_by"],
                "metadata": metadata,
            }
            if document is not None and any(
                getattr(document, field) != value for field, value in values.items()
            ):
                action = "updated"

            if not options["dry_run"]:
                with transaction.atomic():
                    if document is None:
                        document = KnowledgeDocument.objects.create(**values)
                    else:
                        for field, value in values.items():
                            setattr(document, field, value)
                        if action == "updated":
                            document.version += 1
                        document.save()
                    indexer = KnowledgeIndexer()
                    if action != "unchanged" or indexer.needs_reindex(document):
                        indexer.reindex(
                            document,
                            created_by_email=options["created_by"],
                            change_note="Stage public chatbot draft as internal",
                        )

            counts[action] += 1
            imported.append(
                {
                    "key": item["key"],
                    "title": item["title"],
                    "action": action,
                    "permission_level": "internal",
                    "review_points": item["review_points"],
                }
            )

        result = {
            "dataset": dataset,
            "dry_run": options["dry_run"],
            "forced_permission_level": "internal",
            "counts": counts,
            "documents": imported,
        }
        self.stdout.write(json.dumps(result, ensure_ascii=True, indent=2))

    def _load_payload(self, input_path):
        if not input_path.is_file():
            raise CommandError(f"JSON file does not exist: {input_path}")
        if input_path.stat().st_size > 5 * 1024 * 1024:
            raise CommandError("JSON file exceeds the 5 MiB staging limit.")
        try:
            payload = json.loads(input_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CommandError(f"Cannot read valid UTF-8 JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise CommandError("Top-level JSON value must be an object.")
        return payload

    def _validate_document(self, item, index):
        if not isinstance(item, dict):
            raise CommandError(f"documents[{index}] must be an object.")
        review_points = item.get("review_points", [])
        if not isinstance(review_points, list) or not all(
            isinstance(point, str) for point in review_points
        ):
            raise CommandError(f"documents[{index}].review_points must be a string array.")
        return {
            "key": self._required_text(item, "key", f"documents[{index}].key"),
            "title": self._required_text(item, "title", f"documents[{index}].title"),
            "description": str(item.get("description") or "").strip(),
            "content": self._required_text(item, "content", f"documents[{index}].content"),
            "source_type": str(item.get("source_type") or "text").strip()[:32],
            "review_points": [point.strip() for point in review_points if point.strip()],
        }

    @staticmethod
    def _required_text(mapping, key, label):
        value = mapping.get(key)
        if not isinstance(value, str) or not value.strip():
            raise CommandError(f"{label} must be a non-empty string.")
        return value.strip()
