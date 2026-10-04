"""Reindex knowledge embeddings bằng provider được cấu hình."""

from django.core.management.base import BaseCommand, CommandError

from apps.knowledge.models import KnowledgeDocument
from apps.knowledge.services.access_policy import KnowledgeAccessPolicy
from apps.knowledge.services.knowledge_indexer import KnowledgeIndexer


class Command(BaseCommand):
    help = "Reindex toàn bộ hoặc một tài liệu mà không xóa index cũ trước khi embedding thành công."

    def add_arguments(self, parser):
        parser.add_argument("--document-id", type=int)
        parser.add_argument("--batch-size", type=int, default=20)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--resume", action="store_true")

    def handle(self, *args, **options):
        queryset = KnowledgeDocument.objects.order_by("id")
        if options["document_id"]:
            queryset = queryset.filter(id=options["document_id"])
            if not queryset.exists():
                raise CommandError("Knowledge document does not exist.")

        indexer = KnowledgeIndexer()
        policy = KnowledgeAccessPolicy()
        processed = skipped = failed = 0
        errors = []
        for document in queryset.iterator(chunk_size=max(1, options["batch_size"])):
            if not policy.can_index(document):
                skipped += 1
                continue
            if options["resume"] and not indexer.needs_reindex(document):
                skipped += 1
                continue
            if options["dry_run"]:
                processed += 1
                continue
            try:
                indexer.reindex(document, change_note="AI-01 semantic embedding reindex")
                processed += 1
            except Exception as exc:  # Management command must continue and report each failed document.
                failed += 1
                errors.append({"document_id": document.id, "error": str(exc)})

        self.stdout.write(
            self.style.SUCCESS(
                f"reindex complete: processed={processed} skipped={skipped} failed={failed} dry_run={options['dry_run']}"
            )
        )
        for item in errors:
            self.stderr.write(f"document={item['document_id']} error={item['error']}")
        if failed:
            raise CommandError(f"{failed} document(s) failed to reindex.")
