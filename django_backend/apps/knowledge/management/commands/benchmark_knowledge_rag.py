"""Run a small bilingual, citation-aware RAG retrieval benchmark."""

from django.core.management.base import BaseCommand, CommandError

from apps.foundation.models import FoundationUser
from apps.knowledge.services.search_service import KnowledgeSearchService


class Command(BaseCommand):
    help = "Validate Vietnamese/English retrieval and source citations."

    CASES = (
        ("vi", "MEC Precision có năng lực gia công CNC nào?"),
        ("en", "What CNC machining capabilities does MEC Precision provide?"),
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-email",
            required=True,
            help="Existing authorized Foundation user used for document-level filtering.",
        )

    def handle(self, *args, **options):
        try:
            user = FoundationUser.objects.select_related("role").get(
                email=options["user_email"], is_active=True
            )
        except FoundationUser.DoesNotExist as exc:
            raise CommandError("Authorized benchmark user does not exist.") from exc
        failures = []
        for language, query in self.CASES:
            result = KnowledgeSearchService().search(query, limit=3, user=user)
            sources = result.get("sources") or []
            valid_sources = all(
                source.get("id") and source.get("title") for source in sources
            )
            if not sources or not valid_sources:
                failures.append(language)
            self.stdout.write(
                f"{language}: sources={len(sources)} confidence={result.get('confidence', 0)}"
            )
        if failures:
            raise CommandError(f"RAG benchmark failed for: {', '.join(failures)}")
        self.stdout.write(self.style.SUCCESS("BILINGUAL_RAG_BENCHMARK_PASS"))
