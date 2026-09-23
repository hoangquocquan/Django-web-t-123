"""Run the bounded local-only synthetic Product/RAG demo workflow."""

from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from apps.knowledge.services.synthetic_rag_demo import (
    MAX_ROWS, create_and_index_knowledge, evaluate_retrieval,
    import_products, validate_source,
)


class Command(BaseCommand):
    help = "Validate or apply the bounded synthetic technical-RAG dataset; dry-run is default."

    def add_arguments(self, parser):
        parser.add_argument("source")
        parser.add_argument("--max-rows", type=int, default=MAX_ROWS)
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--index", action="store_true")
        parser.add_argument("--evaluate", action="store_true")
        parser.add_argument("--report", default="")

    def handle(self, *args, **options):
        if options["max_rows"] < 1 or options["max_rows"] > MAX_ROWS:
            raise CommandError(f"--max-rows must be between 1 and {MAX_ROWS}.")
        if (options["index"] or options["evaluate"]) and not options["apply"]:
            raise CommandError("--index and --evaluate require --apply.")
        if options["apply"]:
            if not settings.DEBUG or connection.vendor != "sqlite":
                raise CommandError("Synthetic writes are allowed only in DEBUG SQLite local/development.")
            db_name = str(settings.DATABASES["default"]["NAME"])
            if Path(db_name).resolve() != (Path(settings.BASE_DIR) / "db.sqlite3").resolve():
                raise CommandError("Refusing synthetic write outside the expected local development database.")

        validation = validate_source(options["source"], options["max_rows"])
        report = {
            "mode": "apply" if options["apply"] else "dry-run",
            "source_rows": validation.valid + validation.rejected,
            "valid": validation.valid,
            "warnings": validation.warnings,
            "rejected": validation.rejected,
            "duplicates": validation.duplicates,
            "validation_errors": validation.errors,
            "written": 0,
            "conflicts": 0,
        }
        if validation.rejected:
            self._emit(report, options["report"])
            raise CommandError("Synthetic dataset validation failed.")

        if options["apply"]:
            imported = import_products(validation.rows)
            report["import"] = imported
            report["written"] = imported["created"]
            report["conflicts"] = imported["conflicts"]
            if imported["conflicts"]:
                self._emit(report, options["report"])
                raise CommandError("Synthetic Product import conflicts detected.")
            if options["index"]:
                knowledge = create_and_index_knowledge(validation.rows, imported["product_ids"])
                report["knowledge"] = knowledge
                report["conflicts"] += knowledge["conflicts"]
                if knowledge["conflicts"]:
                    self._emit(report, options["report"])
                    raise CommandError("Synthetic Knowledge conflicts detected.")
            if options["evaluate"]:
                report["evaluation"] = evaluate_retrieval(validation.rows)

        self._emit(report, options["report"])
        self.stdout.write(self.style.SUCCESS(json.dumps(report, ensure_ascii=False, default=str)))

    def _emit(self, report, path):
        if path:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

