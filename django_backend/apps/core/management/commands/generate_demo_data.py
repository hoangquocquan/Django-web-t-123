"""Generate fictional enterprise demo data for local MEC platform testing."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand

from apps.core.management.commands.demo_data import DemoCounts, DemoDataGenerator


class Command(BaseCommand):
    """Create a complete local demo dataset without using real customer data."""

    help = "Generate fictional MEC Precision demo data for CRM, Sales, Orders, Knowledge, and AI testing."

    def add_arguments(self, parser):
        """Expose volume controls for local testing and full demo generation."""
        parser.add_argument("--customers", type=int, default=500)
        parser.add_argument("--products", type=int, default=200)
        parser.add_argument("--leads", type=int, default=1000)
        parser.add_argument("--activities", type=int, default=5000)
        parser.add_argument("--opportunities", type=int, default=300)
        parser.add_argument("--quotations", type=int, default=500)
        parser.add_argument("--orders", type=int, default=200)
        parser.add_argument("--documents", type=int, default=100)
        parser.add_argument("--seed", type=int, default=2026)
        parser.add_argument("--no-clean", action="store_true", help="Do not clear existing demo data before generation.")
        parser.add_argument("--small", action="store_true", help="Generate a compact dataset for quick local validation.")

    def handle(self, *args, **options):
        """Run the generator and print a JSON summary."""
        if options["small"]:
            counts = DemoCounts(customers=12, products=10, leads=18, activities=30, opportunities=8, quotations=10, orders=6, documents=5)
        else:
            counts = DemoCounts(
                customers=options["customers"],
                products=options["products"],
                leads=options["leads"],
                activities=options["activities"],
                opportunities=options["opportunities"],
                quotations=options["quotations"],
                orders=options["orders"],
                documents=options["documents"],
            )
        summary = DemoDataGenerator(counts=counts, seed=options["seed"]).generate(clean=not options["no_clean"])
        self.stdout.write(json.dumps(summary, indent=2, ensure_ascii=False))
        self.stdout.write(self.style.SUCCESS("MEC demo data generated successfully."))
