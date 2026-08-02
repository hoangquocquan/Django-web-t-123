"""Django command for validating the local demo database without writing to it."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.core.demo_database_validation import collect_demo_database_validation


class Command(BaseCommand):
    """Print and optionally persist the read-only demo database validation result."""

    help = "Validate demo database counts, integrity, and representative query performance."

    def add_arguments(self, parser):
        parser.add_argument("--json-output", type=Path, default=None)

    def handle(self, *args, **options):
        result = collect_demo_database_validation()
        output = json.dumps(result, ensure_ascii=False, indent=2, default=str)
        output_path = options.get("json_output")
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output + "\n", encoding="utf-8")

        self.stdout.write(output)
        if result["decision"] == "DEMO_DATABASE_VALIDATION_FAILED":
            raise CommandError(
                "Demo database validation found blocking issues. Review the JSON output."
            )
        self.stdout.write(self.style.SUCCESS(result["decision"]))
