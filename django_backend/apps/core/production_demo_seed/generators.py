"""Deterministic fictional data factories for TEST seed."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from .ownership import marker_text, owned_email, prefixed
from .profiles import FIXED_RANDOM_SEED


@dataclass(frozen=True)
class SeedFactories:
    """Deterministic data factories."""

    seed: int = FIXED_RANDOM_SEED

    def __post_init__(self):
        object.__setattr__(self, "random", random.Random(self.seed))

    def customer(self, index: int) -> dict:
        industries = ["Automotive", "Industrial Equipment", "Electronics", "Medical Fixture"]
        return {
            "company_name": prefixed("Fictional Precision Buyer", index),
            "contact_name": f"Demo Buyer {index}",
            "email": owned_email(f"buyer{index:02d}"),
            "phone": f"+8400000{index:04d}",
            "country": "Vietnam",
            "status": "ACTIVE",
            "notes": marker_text(f"industry={industries[index % len(industries)]}"),
        }

    def material(self, index: int) -> dict:
        names = ["SUS304", "S45C", "A6061", "SKD11", "POM", "C3604"]
        name = names[index % len(names)]
        return {
            "name": f"{name} Demo Lot {index}",
            "standard": "JIS",
            "grade": name,
            "description": marker_text("production-like material catalog"),
            "is_active": True,
        }

    def part(self, index: int, material_id: int) -> dict:
        families = ["shaft", "bracket", "fixture plate", "spacer", "housing"]
        family = families[index % len(families)]
        return {
            "name": prefixed(f"Precision {family}", index),
            "revision": chr(ord("A") + (index % 3)),
            "unit": "PCS",
            "default_material_id": material_id,
            "tolerance": "±0.01 mm" if index % 4 == 0 else "±0.05 mm",
            "technical_requirements": marker_text("CNC machining and inspection required"),
        }

    def rfq_payload(self, index: int, customer_id: int, sales_user_id: int) -> dict:
        today = timezone.localdate()
        due_days = 5 + (index % 10)
        return {
            "customer_id": customer_id,
            "project_name": prefixed("RFQ Demo Project", index),
            "notes": marker_text("canonical RFQ lifecycle test data"),
            "quote_due_at": today + timedelta(days=due_days),
            "required_delivery_date": today + timedelta(days=due_days + 25 + (index % 12)),
            "assigned_to_id": sales_user_id,
        }

    def rfq_line(self, index: int, part_id: int, material_id: int, delivery_date) -> dict:
        return {
            "part_id": part_id,
            "material_id": material_id,
            "description": f"Fictional machined component line {index}",
            "quantity": Decimal(str(1 + (index % 9))).quantize(Decimal("0.0001")),
            "unit": "PCS",
            "required_delivery_date": delivery_date,
            "tolerance": "±0.01 mm" if index % 4 == 0 else "±0.05 mm",
            "technical_notes": "Inspect critical dimensions and deburr all edges.",
            "drawing_required": index % 11 == 0,
        }

    def quotation_payload(self, index: int, line_ids: list[int]) -> dict:
        today = timezone.localdate()
        return {
            "currency": "USD",
            "valid_from": today,
            "valid_until": today + timedelta(days=14),
            "discount_total": "0",
            "tax_amount": "0",
            "terms": marker_text("Net 30; human approval required"),
            "lines": [
                {
                    "source_rfq_line_id": line_id,
                    "unit_price": str(12 + index + offset),
                    "discount": "0",
                }
                for offset, line_id in enumerate(line_ids)
            ],
        }

    def knowledge_document(self, index: int) -> dict:
        topics = [
            (
                "RFQ intake checklist",
                "RFQ drawing requirement checklist: customer drawings, STEP files, revision, tolerance, material, quantity, quote due date, and required delivery date must be captured before review.",
            ),
            (
                "CNC milling capability",
                "CNC first article inspection capability: first article inspection, dimensional report, tolerance evidence, deburring, and machining capability notes are reviewed before customer delivery.",
            ),
            (
                "Quotation approval policy",
                "Quotation approval policy: pricing, SUS304 quotation requirements, margin, payment terms, validity, discount, and human manager approval are required before sending quotations.",
            ),
            (
                "FAI inspection workflow",
                "First article inspection workflow: CNC first article inspection requires drawing ballooning, measurement evidence, nonconformance notes, and quality manager sign-off.",
            ),
            (
                "Material certificate handling",
                "SUS304 quotation requirements and material certificate handling: SUS304, S45C, A6061, SKD11, POM, and C3604 requests need certificate status and traceability notes.",
            ),
            (
                "AI assistant human approval rules",
                "Order delivery procedure and AI approval rules: delivery commitments, order progress, hold reasons, cancellation reasons, and email drafts remain advisory until a human approves them.",
            ),
        ]
        topic, scenario = topics[index % len(topics)]
        body = (
            f"{topic}. {scenario} This is fictional production-demo knowledge for {marker_text()}. "
            "The assistant must cite sources, avoid autonomous business actions, and ask a human "
            "to approve emails, CRM changes, quotation decisions, and order actions. "
            "RFQ records require drawings or reviewer confirmation, material evidence, tolerance, "
            "technical notes, and clear due dates. "
        )
        return {
            "title": prefixed(topic, index),
            "content": body * 8,
            "description": marker_text("RAG TEST fixture"),
            "category_name": "Production Demo Knowledge",
            "permission_level": "internal",
            "department": "MANAGEMENT",
            "owner_email": owned_email("admin.2"),
            "effective_date": timezone.localdate(),
            "created_by_email": owned_email("knowledge.owner"),
            "metadata": {"dataset": "production_demo_v1", "profile": "TEST", "case": index},
        }
