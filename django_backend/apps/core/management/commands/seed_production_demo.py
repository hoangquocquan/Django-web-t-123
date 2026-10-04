"""Create synthetic demo data in explicitly allowlisted non-production environments."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from apps.core.production_demo_seed.lifecycle import ProductionDemoSeedOrchestrator
from apps.core.production_demo_seed.profiles import get_profile
from apps.core.production_demo_seed.safety import evaluate_safety


class Command(BaseCommand):
    help = "Dry-run or apply synthetic TEST/SMALL demo profiles; FULL is disabled."

    def add_arguments(self, parser):
        parser.add_argument("--profile", default="TEST", help="Enabled profiles: TEST, SMALL")
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument("--dry-run", action="store_true", help="Plan only; perform zero writes.")
        mode.add_argument("--apply", action="store_true", help="Apply seed after fail-closed safety gates.")

    def handle(self, *args, **options):
        profile = get_profile(options["profile"])
        apply = bool(options.get("apply"))
        dry_run = not apply
        safety = evaluate_safety(apply=apply)
        if not safety.allowed:
            raise CommandError("; ".join(safety.reasons))

        report = ProductionDemoSeedOrchestrator(profile, dry_run=dry_run).run()
        self.stdout.write(json.dumps(report.as_dict(), indent=2, sort_keys=True))
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run only: zero database writes performed."))
        else:
            self.stdout.write(self.style.SUCCESS("Production-demo TEST seed applied."))
