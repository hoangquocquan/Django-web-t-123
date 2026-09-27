"""Lifecycle orchestration for production-demo TEST seed."""

from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction

from apps.api.services.canonical_command_service import (
    MasterDataCommandService,
    OrderProgressCommandService,
    QuotationCommandService,
    RfqCommandService,
    RfqDocumentSecurityService,
)
from apps.business_core.models import (
    BusinessCustomer,
    BusinessMaterial,
    BusinessProduct,
    InventoryItem,
    InventoryTransaction,
    InventoryWarehouse,
)
from apps.crm.models import (
    CrmCustomerProfile,
    CrmInteraction,
    CrmNote,
    CrmTask,
    CrmTimelineEvent,
)
from apps.foundation.models import (
    FoundationPermission,
    FoundationRole,
    FoundationUser,
    FoundationUserProfile,
)
from apps.knowledge.models import DocumentVersion, KnowledgeDocument
from apps.knowledge.services.access_policy import KnowledgeAccessPolicy, content_hash
from apps.knowledge.services.embedding_service import DevelopmentHashEmbeddingProvider
from apps.knowledge.services.governance import KnowledgeGovernanceService
from apps.knowledge.services.knowledge_indexer import KnowledgeIndexer
from apps.knowledge.services.knowledge_service import KnowledgeService
from apps.knowledge.services.pilot_governance import PilotGovernanceService
from apps.sales.models import (
    SalesActivity,
    SalesFollowUp,
    SalesLead,
    SalesOpportunity,
    SalesQuotation,
    SalesRfq,
)
from apps.transaction_domain.models import TransactionOrder

from .ai_eval_cases import load_ai_eval_cases
from .generators import SeedFactories
from .historical import HistoricalTimestampBackfiller
from .ownership import idempotency_key, marker_text, owned_email, prefixed
from .profiles import DATASET_MARKER, DATASET_PREFIX, SeedProfile
from .report import SeedRunReport
from .validators import assert_no_deliverable_seed_pii, owned_business_counts

REQUIRED_PERMISSIONS = {
    "Admin": {
        "customer:view", "customer:create", "customer:change", "customer:archive",
        "part:view", "part:manage", "part:archive",
        "material:view", "material:manage", "material:archive",
        "rfq:view", "rfq:create", "rfq:change", "rfq:archive",
        "rfq:document_upload", "rfq:document_download",
        "quotation:view", "quotation:create_revision", "quotation:change",
        "order:view", "knowledge:read", "knowledge:write", "ai_sales:read",
    },
    "Sales": {
        "customer:view", "customer:create", "customer:change", "customer:archive",
        "part:view", "material:view",
        "rfq:view", "rfq:create", "rfq:change", "rfq:archive", "rfq:submit",
        "rfq:document_upload", "rfq:document_download",
        "quotation:view", "quotation:create_revision", "quotation:change",
        "quotation:archive", "quotation:submit", "quotation:send",
        "quotation:record_customer_decision", "quotation:convert",
        "order:view", "sales:read", "crm:read", "knowledge:read", "ai_sales:read",
    },
    "Manager": {
        "customer:view", "part:view", "material:view",
        "rfq:view", "rfq:review", "rfq:document_download",
        "quotation:view", "quotation:approve", "quotation:reject",
        "order:view", "order:progress", "order:hold", "order:resume",
        "order:complete", "order:cancel", "audit:view",
        "sales:read", "crm:read", "knowledge:read", "ai_sales:read",
    },
}


@dataclass
class SeedContext:
    """Objects created/reused during one seed run."""

    users: dict[str, FoundationUser]
    customers: list[BusinessCustomer]
    materials: list[BusinessMaterial]
    parts: list[BusinessProduct]
    rfqs: list[SalesRfq]
    quotations: list[SalesQuotation]
    orders: list[TransactionOrder]


class ProductionDemoSeedOrchestrator:
    """Create TEST profile data through canonical lifecycle paths."""

    def __init__(self, profile: SeedProfile, *, dry_run: bool = True):
        self.profile = profile
        self.dry_run = dry_run
        self.factories = SeedFactories()
        self.report = SeedRunReport(profile=profile.name, dry_run=dry_run)

    def run(self) -> SeedRunReport:
        """Run the seed or dry-run plan."""

        started = time.perf_counter()
        self.report.omitted_states.extend(
            [
                "RFQ QUOTED omitted: no confirmed canonical transition in inspected source.",
                "Quotation EXPIRED omitted: no exposed canonical expire command in V1 source.",
            ]
        )
        if self.dry_run:
            self._dry_run_counts()
            return self.report
        with transaction.atomic():
            context = self._apply()
            self._validate(context)
        self.report.counts["runtime_total_ms"] = int((time.perf_counter() - started) * 1000)
        self.report.applied = True
        return self.report

    def _dry_run_counts(self) -> None:
        self.report.counts.update(
            {
                "planned_users": self.profile.users,
                "planned_customers": self.profile.customers,
                "planned_materials": self.profile.materials,
                "planned_parts": self.profile.parts,
                "planned_warehouses": self.profile.warehouses,
                "planned_inventory_items": self.profile.inventory_items,
                "planned_inventory_transactions": self.profile.inventory_transactions,
                "planned_leads": self.profile.leads,
                "planned_opportunities": self.profile.opportunities,
                "planned_crm_activities": self.profile.crm_activities,
                "planned_rfqs": self.profile.rfqs,
                "planned_quotation_revisions": self.profile.quotation_revisions,
                "planned_orders": self.profile.orders,
                "planned_knowledge_documents": self.profile.knowledge_documents,
                "planned_ai_eval_cases": self.profile.ai_eval_cases,
            }
        )

    def _apply(self) -> SeedContext:
        users = self._ensure_users()
        t0 = time.perf_counter()
        customers = self._ensure_customers(users["sales"])
        materials = self._ensure_materials(users["admin"])
        parts = self._ensure_parts(users["admin"], materials)
        self.report.counts["runtime_master_data_ms"] = int((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter()
        self._ensure_inventory(parts)
        self._ensure_crm_sales(users, customers)
        self.report.counts["runtime_pipeline_inventory_ms"] = int((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter()
        rfqs = self._ensure_rfqs(users, customers, materials, parts)
        quotations = self._ensure_quotations(users, rfqs)
        orders = self._ensure_orders(users, quotations)
        self.report.counts["runtime_lifecycle_ms"] = int((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter()
        self._ensure_knowledge(users)
        self.report.counts["runtime_knowledge_ms"] = int((time.perf_counter() - t0) * 1000)
        self._ensure_ai_eval_cases()
        if self.profile.historical_months:
            t0 = time.perf_counter()
            result = HistoricalTimestampBackfiller(months=self.profile.historical_months).apply()
            self.report.counts["runtime_historical_ms"] = int((time.perf_counter() - t0) * 1000)
            for model_name, count in result.touched.items():
                self.report.counts[f"historical_{model_name}"] = count
            self.report.warnings.append(
                "Historical backfill used seed-only approved timestamp fields for dataset-owned records."
            )
        return SeedContext(users, customers, materials, parts, rfqs, quotations, orders)

    def _permission(self, code: str) -> FoundationPermission:
        module, action = code.split(":", 1)
        permission, created = FoundationPermission.objects.get_or_create(
            code=code,
            defaults={
                "module": module,
                "action": action,
                "description": f"Production demo permission {code}",
            },
        )
        if created:
            self.report.bump("permissions_created")
        return permission

    def _ensure_role(self, name: str) -> FoundationRole:
        role, created = FoundationRole.objects.get_or_create(
            name=name,
            defaults={"description": f"Production demo compatible {name} role"},
        )
        if not role.is_active:
            role.is_active = True
            role.save(update_fields=["is_active"])
        if created:
            self.report.bump("roles_created")
        for code in sorted(REQUIRED_PERMISSIONS[name]):
            role.permissions.add(self._permission(code))
        return role

    def _ensure_users(self) -> dict[str, FoundationUser]:
        role_by_name = {name: self._ensure_role(name) for name in REQUIRED_PERMISSIONS}
        specs = [
            ("admin", "Admin"),
            ("sales", "Sales"),
            ("manager", "Manager"),
            ("sales.2", "Sales"),
            ("manager.2", "Manager"),
            ("admin.2", "Admin"),
            ("sales.3", "Sales"),
            ("sales.4", "Sales"),
            ("sales.5", "Sales"),
            ("manager.3", "Manager"),
            ("admin.3", "Admin"),
            ("sales.6", "Sales"),
        ]
        if self.profile.users > len(specs):
            for index in range(len(specs) + 1, self.profile.users + 1):
                if index % 6 == 0:
                    role_name = "Admin"
                elif index % 4 == 0:
                    role_name = "Manager"
                else:
                    role_name = "Sales"
                specs.append((f"{role_name.casefold()}.{index}", role_name))
        users = {}
        for local, role_name in specs[: self.profile.users]:
            email = owned_email(local)
            user, created = FoundationUser.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": prefixed(f"{role_name} User", local),
                    "password_hash": make_password(None),
                    "role": role_by_name[role_name],
                    "is_active": True,
                },
            )
            if not created and user.role_id != role_by_name[role_name].pk:
                user.role = role_by_name[role_name]
                user.save(update_fields=["role", "updated_at"])
            FoundationUserProfile.objects.get_or_create(user=user)
            self.report.bump("users_created" if created else "users_reused")
            users[local.replace(".", "_")] = user
        return users

    def _ensure_customers(self, actor: FoundationUser) -> list[BusinessCustomer]:
        customers = []
        for index in range(1, self.profile.customers + 1):
            data = self.factories.customer(index)
            existing = BusinessCustomer.objects.filter(
                company_name=data["company_name"], notes__contains=DATASET_MARKER
            ).first()
            if existing:
                self.report.reuse("customers")
                customers.append(existing)
                continue
            customer = MasterDataCommandService.create_customer(actor, data)
            self.report.bump("customers")
            customers.append(customer)
        return customers

    def _ensure_materials(self, actor: FoundationUser) -> list[BusinessMaterial]:
        materials = []
        for index in range(1, self.profile.materials + 1):
            data = self.factories.material(index)
            existing = BusinessMaterial.objects.filter(
                name=data["name"], description__contains=DATASET_MARKER
            ).first()
            if existing:
                self.report.reuse("materials")
                materials.append(existing)
                continue
            material = MasterDataCommandService.create_material(actor, data)
            self.report.bump("materials")
            materials.append(material)
        return materials

    def _ensure_parts(self, actor: FoundationUser, materials: list[BusinessMaterial]) -> list[BusinessProduct]:
        parts = []
        for index in range(1, self.profile.parts + 1):
            material = materials[(index - 1) % len(materials)]
            data = self.factories.part(index, material.pk)
            existing = BusinessProduct.objects.filter(
                name=data["name"], technical_requirements__contains=DATASET_MARKER
            ).first()
            if existing:
                self.report.reuse("parts")
                parts.append(existing)
                continue
            part = MasterDataCommandService.create_part(actor, data)
            self.report.bump("parts")
            parts.append(part)
        return parts

    def _ensure_inventory(self, parts: list[BusinessProduct]) -> None:
        warehouses = []
        for index in range(1, self.profile.warehouses + 1):
            warehouse, created = InventoryWarehouse.objects.get_or_create(
                code=f"{DATASET_PREFIX}-WH-{index}",
                defaults={
                    "name": prefixed("Warehouse", index),
                    "location": marker_text("fictional warehouse"),
                    "is_active": True,
                },
            )
            self.report.bump("warehouses" if created else "warehouses_reused")
            warehouses.append(warehouse)
        target_items = self.profile.inventory_items or len(parts)
        for index in range(1, target_items + 1):
            part = parts[(index - 1) % len(parts)]
            warehouse = warehouses[((index - 1) // len(parts)) % len(warehouses)]
            item, created = InventoryItem.objects.get_or_create(
                product=part,
                warehouse=warehouse,
                defaults={
                    "quantity": Decimal(str(25 + index)),
                    "reserved_quantity": Decimal(str(index % 5)),
                    "reorder_point": Decimal(10),
                },
            )
            base_transactions = max(1, self.profile.inventory_transactions // max(1, target_items))
            remainder_transactions = max(0, self.profile.inventory_transactions - (base_transactions * target_items))
            tx_count = base_transactions + (1 if index <= remainder_transactions else 0)
            for tx_index in range(1, tx_count + 1):
                reference = f"{DATASET_PREFIX}-INV-{index}-{tx_index}"
                _transaction, tx_created = InventoryTransaction.objects.get_or_create(
                    reference=reference,
                    defaults={
                        "item": item,
                        "transaction_type": "IN" if tx_index == 1 else "ADJUST",
                        "quantity_delta": item.quantity if tx_index == 1 else Decimal(str(tx_index % 7)),
                        "reason": marker_text("production-demo stock movement"),
                    },
                )
                if tx_created:
                    self.report.bump("inventory_transactions")
            if created:
                self.report.bump("inventory_items")
            else:
                self.report.bump("inventory_items_reused")

    def _ensure_crm_sales(self, users: dict[str, FoundationUser], customers: list[BusinessCustomer]) -> None:
        if not self.profile.leads:
            return
        statuses = ["new", "contacted", "meeting", "quotation", "negotiation", "won", "lost"]
        priorities = ["high", "medium", "medium", "low"]
        industries = ["Automotive", "Industrial Equipment", "Electronics", "Medical Fixture", "Factory Automation"]
        for index, customer in enumerate(customers, start=1):
            _profile, created = CrmCustomerProfile.objects.get_or_create(
                customer=customer,
                defaults={
                    "segment": "strategic" if index <= 8 else ("repeat" if index <= 24 else "standard"),
                    "lifecycle_stage": "active" if index <= 40 else "nurture",
                    "preferred_contact_method": "email",
                    "assigned_owner": users["sales"],
                    "summary": marker_text("SMALL CRM profile"),
                },
            )
            self.report.bump("crm_profiles" if created else "crm_profiles_reused")
            for kind, model, kwargs in [
                ("crm_interactions", CrmInteraction, {"interaction_type": "email", "subject": prefixed("Customer check-in", index), "content": marker_text("SMALL interaction"), "created_by": users["sales"].email}),
                ("crm_notes", CrmNote, {"note": marker_text("SMALL account note"), "created_by": users["sales"].email}),
                ("crm_tasks", CrmTask, {"title": prefixed("Follow up account", index), "due_date": "2026-09-30", "status": "open" if index % 4 else "done", "owner": users["sales"]}),
                ("crm_timeline_events", CrmTimelineEvent, {"event_type": "seed", "title": prefixed("Timeline event", index), "payload": {"dataset": DATASET_MARKER, "profile": self.profile.name}}),
            ]:
                _obj, obj_created = model.objects.get_or_create(customer=customer, **kwargs)
                self.report.bump(kind if obj_created else f"{kind}_reused")

        leads = []
        for index in range(1, self.profile.leads + 1):
            company = prefixed("Sales Lead", index)
            lead, created = SalesLead.objects.get_or_create(
                company=company,
                defaults={
                    "lead_source": ["Website", "Referral", "Trade Event", "Partner"][index % 4],
                    "contact_person": f"Demo Lead Contact {index}",
                    "email": owned_email(f"lead{index:03d}"),
                    "phone": f"+8400001{index:04d}",
                    "industry": industries[index % len(industries)],
                    "status": statuses[index % len(statuses)],
                    "priority": priorities[index % len(priorities)],
                    "owner": users["sales"],
                    "notes": marker_text("SMALL sales lead"),
                },
            )
            self.report.bump("leads" if created else "leads_reused")
            leads.append(lead)

        for index in range(1, self.profile.opportunities + 1):
            lead = leads[(index - 1) % len(leads)]
            customer = customers[(index - 1) % len(customers)]
            _opportunity, created = SalesOpportunity.objects.get_or_create(
                title=prefixed("Opportunity", index),
                defaults={
                    "lead": lead,
                    "customer": customer,
                    "value": Decimal(str(1500 + (index * 137) % 25000)),
                    "probability": [15, 30, 45, 60, 75, 90][index % 6],
                    "expected_close_date": "2026-10-15",
                    "sales_owner": users["sales"],
                    "status": ["open", "proposal", "negotiation", "won", "lost"][index % 5],
                    "notes": marker_text("SMALL sales opportunity"),
                },
            )
            self.report.bump("opportunities" if created else "opportunities_reused")

        target = self.profile.crm_activities
        for index in range(1, target + 1):
            lead = leads[(index - 1) % len(leads)]
            customer = customers[(index - 1) % len(customers)]
            _activity, created = SalesActivity.objects.get_or_create(
                lead=lead,
                subject=prefixed("Sales activity", index),
                defaults={
                    "customer": customer,
                    "activity_type": ["note", "call", "email", "meeting"][index % 4],
                    "content": marker_text("SMALL sales activity"),
                    "created_by": users["sales"].email,
                },
            )
            self.report.bump("sales_activities" if created else "sales_activities_reused")
            if index <= target // 2:
                _follow, follow_created = SalesFollowUp.objects.get_or_create(
                    lead=lead,
                    title=prefixed("Sales follow-up", index),
                    defaults={
                        "customer": customer,
                        "due_date": "2026-10-01",
                        "status": "open" if index % 3 else "done",
                        "owner": users["sales"],
                        "note": marker_text("SMALL follow-up"),
                    },
                )
                self.report.bump("sales_followups" if follow_created else "sales_followups_reused")

    def _ensure_rfqs(
        self,
        users: dict[str, FoundationUser],
        customers: list[BusinessCustomer],
        materials: list[BusinessMaterial],
        parts: list[BusinessProduct],
    ) -> list[SalesRfq]:
        rfqs = []
        for index in range(1, self.profile.rfqs + 1):
            key = idempotency_key("rfq", index)
            data = self.factories.rfq_payload(
                index,
                customers[(index - 1) % len(customers)].pk,
                users["sales"].pk,
            )
            rfq, created = RfqCommandService.create(users["sales"], data, key)
            if created:
                self.report.bump("rfqs")
            else:
                self.report.reuse("rfqs")
            if not rfq.lines.exists():
                if self.profile.name == "FULL":
                    line_count = 4 if index % 3 == 0 else 3
                elif self.profile.name == "SMALL":
                    line_count = 3
                else:
                    line_count = 1
                for line_offset in range(line_count):
                    line_payload = self.factories.rfq_line(
                        index + line_offset,
                        parts[(index + line_offset - 1) % len(parts)].pk,
                        materials[(index + line_offset - 1) % len(materials)].pk,
                        rfq.required_delivery_date,
                    )
                    if self.profile.name == "SMALL" and line_offset == 0:
                        line_payload["drawing_required"] = True
                    if self.profile.name == "FULL" and line_offset == 0 and index % 2 == 0:
                        line_payload["drawing_required"] = True
                    line = RfqCommandService.add_line(users["sales"], rfq.pk, line_payload)
                    if line.drawing_required:
                        uploaded = SimpleUploadedFile(
                            f"pdv1-rfq-{index}-{line_offset + 1}.step",
                            b"ISO-10303-21;\nHEADER;\nENDSEC;\nEND-ISO-10303-21;",
                            content_type="application/step",
                        )
                        RfqDocumentSecurityService().upload(
                            users["sales"],
                            rfq.pk,
                            {
                                "file": uploaded,
                                "rfq_line_id": line.pk,
                                "document_revision": "A",
                            },
                        )
                        self.report.bump("rfq_documents")
                    self.report.bump("rfq_lines")
                if self.profile.name == "SMALL" and not rfq.documents.filter(original_filename__contains="-extra").exists():
                    uploaded = SimpleUploadedFile(
                        f"pdv1-rfq-{index}-extra.pdf",
                        b"%PDF-1.4\n% pdv1 fictional drawing packet\n",
                        content_type="application/pdf",
                    )
                    RfqDocumentSecurityService().upload(
                        users["sales"],
                        rfq.pk,
                        {"file": uploaded, "document_revision": "B"},
                    )
                    self.report.bump("rfq_documents")
                if self.profile.name == "FULL" and index % 4 == 0 and not rfq.documents.filter(original_filename__contains="-extra").exists():
                    uploaded = SimpleUploadedFile(
                        f"pdv1-rfq-{index}-extra.pdf",
                        b"%PDF-1.4\n% pdv1 fictional FULL drawing packet\n",
                        content_type="application/pdf",
                    )
                    RfqDocumentSecurityService().upload(
                        users["sales"],
                        rfq.pk,
                        {"file": uploaded, "document_revision": "B"},
                    )
                    self.report.bump("rfq_documents")
                if self.profile.name == "FULL" and index % 20 == 0 and not rfq.documents.filter(original_filename__contains="-qa").exists():
                    uploaded = SimpleUploadedFile(
                        f"pdv1-rfq-{index}-qa.step",
                        b"ISO-10303-21;\nHEADER;\nENDSEC;\nEND-ISO-10303-21;",
                        content_type="application/step",
                    )
                    RfqDocumentSecurityService().upload(
                        users["sales"],
                        rfq.pk,
                        {
                            "file": uploaded,
                            "document_revision": "A",
                        },
                    )
                    self.report.bump("rfq_documents")
                if self.profile.name == "SMALL" and index % 3 == 0 and not rfq.documents.filter(original_filename__contains="-qa").exists():
                    uploaded = SimpleUploadedFile(
                        f"pdv1-rfq-{index}-qa.step",
                        b"ISO-10303-21;\nHEADER;\nENDSEC;\nEND-ISO-10303-21;",
                        content_type="application/step",
                    )
                    RfqDocumentSecurityService().upload(
                        users["sales"],
                        rfq.pk,
                        {
                            "file": uploaded,
                            "document_revision": "A",
                        },
                    )
                    self.report.bump("rfq_documents")
            self._advance_rfq(index, users, rfq)
            rfq.refresh_from_db()
            rfqs.append(rfq)
        return rfqs

    def _advance_rfq(self, index: int, users: dict[str, FoundationUser], rfq: SalesRfq) -> None:
        if rfq.status != "DRAFT":
            return
        if index <= 3:
            return
        if 4 <= index <= 6:
            RfqCommandService.archive(users["sales"], rfq.pk, marker_text("archived draft branch"))
            return
        RfqCommandService.submit(users["sales"], rfq.pk)
        if 7 <= index <= 9:
            return
        RfqCommandService.start_review(users["manager"], rfq.pk)
        if 10 <= index <= 12:
            return
        if 13 <= index <= 15:
            RfqCommandService.request_information(
                users["manager"],
                rfq.pk,
                {
                    "reason": "Need drawing revision confirmation.",
                    "notes": marker_text("needs information branch"),
                    "requested_fields": ["documents", "lines"],
                },
            )
            return
        line_ids = list(rfq.lines.values_list("id", flat=True))
        RfqCommandService.complete_review(
            users["manager"],
            rfq.pk,
            {
                "feasible_line_ids": line_ids,
                "drawing_not_required_line_ids": [
                    line.pk for line in rfq.lines.all() if not line.drawing_required
                ],
                "notes": marker_text("ready to quote branch"),
            },
        )

    def _ensure_quotations(self, users: dict[str, FoundationUser], rfqs: list[SalesRfq]) -> list[SalesQuotation]:
        quotations = []
        desired_revisions = {"TEST": 1, "SMALL": 20, "FULL": 100}.get(self.profile.name, 1)
        base_target = max(1, self.profile.quotation_revisions - desired_revisions)
        quote_rfqs = [rfq for rfq in rfqs if rfq.status == "READY_TO_QUOTE"][:base_target]
        revision_created_count = SalesQuotation.objects.filter(
            idempotency_key__startswith="pdv1-quote-revision"
        ).count()
        for offset, rfq in enumerate(quote_rfqs, start=1):
            line_ids = list(rfq.lines.values_list("id", flat=True))
            quote_key = idempotency_key("quote", offset)
            existing = SalesQuotation.objects.filter(idempotency_key=quote_key).first()
            if existing:
                quotation, created = existing, False
            else:
                quotation, created = QuotationCommandService.create(
                    users["sales"],
                    rfq.pk,
                    self.factories.quotation_payload(offset, line_ids),
                    quote_key,
                )
            self.report.bump("quotations" if created else "quotations_reused")
            self._advance_quotation(offset, users, quotation)
            quotation.refresh_from_db()
            quotations.append(quotation)
            if quotation.workflow_status == "REJECTED" and revision_created_count < desired_revisions:
                quotation.refresh_from_db()
                if quotation.workflow_status == "REJECTED":
                    revision_created_count += 1
                    revision_key = idempotency_key("quote-revision", offset)
                    existing_revision = SalesQuotation.objects.filter(idempotency_key=revision_key).first()
                    if existing_revision:
                        revision, rev_created = existing_revision, False
                    else:
                        revision, rev_created = QuotationCommandService.create(
                            users["sales"],
                            rfq.pk,
                            self.factories.quotation_payload(offset + 100, line_ids),
                            revision_key,
                            source_quotation_id=quotation.pk,
                        )
                    self.report.bump("quotations" if rev_created else "quotations_reused")
                    self._advance_revision(offset, users, revision)
                    revision.refresh_from_db()
                    quotations.append(revision)
        return quotations

    def _advance_quotation(self, index: int, users: dict[str, FoundationUser], quotation: SalesQuotation) -> None:
        if quotation.workflow_status != "DRAFT":
            return
        bucket = index % 10
        if bucket == 1:
            return
        QuotationCommandService.submit(users["sales"], quotation.pk)
        if bucket == 2:
            return
        if bucket == 5:
            QuotationCommandService.decide(
                users["manager"],
                quotation.pk,
                decision="REJECTED",
                reason=marker_text("revision requested"),
            )
            return
        QuotationCommandService.decide(users["manager"], quotation.pk, decision="APPROVED")
        if bucket == 3:
            return
        QuotationCommandService.send(
            users["sales"],
            quotation.pk,
            {"sent_to": "Demo Buyer", "evidence": marker_text("CRM send evidence")},
        )
        if bucket == 4:
            return
        decision = "ACCEPTED"
        payload = {
            "contact_snapshot": "Demo Buyer",
            "evidence": marker_text(
                "customer declined evidence" if decision == "DECLINED" else "customer accepted evidence"
            ),
        }
        if decision == "DECLINED":
            payload["reason"] = "Price review deferred."
        QuotationCommandService.record_customer_decision(
            users["sales"],
            quotation.pk,
            payload,
            decision=decision,
        )

    def _advance_revision(self, index: int, users: dict[str, FoundationUser], quotation: SalesQuotation) -> None:
        QuotationCommandService.submit(users["sales"], quotation.pk)
        QuotationCommandService.decide(users["manager"], quotation.pk, decision="APPROVED")
        QuotationCommandService.send(
            users["sales"],
            quotation.pk,
            {"sent_to": "Demo Buyer", "evidence": marker_text("revision send evidence")},
        )
        decision = "ACCEPTED" if index % 5 else "DECLINED"
        payload = {
            "contact_snapshot": "Demo Buyer",
            "evidence": marker_text("customer revision decision"),
        }
        if decision == "DECLINED":
            payload["reason"] = "Lead time no longer fits."
        QuotationCommandService.record_customer_decision(
            users["sales"], quotation.pk, payload, decision=decision
        )

    def _ensure_orders(self, users: dict[str, FoundationUser], quotations: list[SalesQuotation]) -> list[TransactionOrder]:
        accepted = [q for q in quotations if q.workflow_status == "ACCEPTED"][: self.profile.orders]
        orders = []
        for index, quotation in enumerate(accepted, start=1):
            order_key = idempotency_key("order", index)
            existing = TransactionOrder.objects.filter(idempotency_key=order_key).first()
            if existing:
                order, created = existing, False
            else:
                order, created = QuotationCommandService.convert(
                    users["sales"],
                    quotation.pk,
                    order_key,
                )
            self.report.bump("orders" if created else "orders_reused")
            self._advance_order(index, users, order)
            order.refresh_from_db()
            orders.append(order)
        return orders

    def _advance_order(self, index: int, users: dict[str, FoundationUser], order: TransactionOrder) -> None:
        if order.workflow_status != "CONFIRMED":
            return
        if self.profile.name == "FULL":
            bucket = index % 10
            if bucket == 1:
                return
            if bucket in {2, 3}:
                for progress in (15, 35, 55, 75):
                    OrderProgressCommandService.progress(
                        users["manager"],
                        order.pk,
                        {"progress_percent": progress, "milestone_note": marker_text(f"FULL progress {progress}")},
                    )
                return
            if bucket == 4:
                OrderProgressCommandService.progress(
                    users["manager"], order.pk, {"progress_percent": 20, "milestone_note": marker_text("FULL started")}
                )
                OrderProgressCommandService.hold(
                    users["manager"],
                    order.pk,
                    {"progress_percent": 30, "milestone_note": marker_text("FULL hold"), "reason": "Awaiting material certificate."},
                )
                return
            if bucket == 5:
                OrderProgressCommandService.progress(
                    users["manager"], order.pk, {"progress_percent": 15, "milestone_note": marker_text("FULL started")}
                )
                OrderProgressCommandService.hold(
                    users["manager"],
                    order.pk,
                    {"progress_percent": 30, "milestone_note": marker_text("FULL hold"), "reason": "Customer drawing confirmation."},
                )
                OrderProgressCommandService.resume(
                    users["manager"], order.pk, {"progress_percent": 45, "milestone_note": marker_text("FULL resumed")}
                )
                OrderProgressCommandService.progress(
                    users["manager"], order.pk, {"progress_percent": 70, "milestone_note": marker_text("FULL machining")}
                )
                return
            if bucket in {6, 7}:
                for progress in (10, 30, 55, 80):
                    OrderProgressCommandService.progress(
                        users["manager"],
                        order.pk,
                        {"progress_percent": progress, "milestone_note": marker_text(f"FULL completion path {progress}")},
                    )
                OrderProgressCommandService.complete(
                    users["manager"], order.pk, {"milestone_note": marker_text("FULL completed")}
                )
                return
            for progress in (10, 25):
                OrderProgressCommandService.progress(
                    users["manager"],
                    order.pk,
                    {"progress_percent": progress, "milestone_note": marker_text(f"FULL cancellation path {progress}")},
                )
            OrderProgressCommandService.cancel(
                users["manager"],
                order.pk,
                {"progress_percent": 25, "milestone_note": marker_text("FULL cancelled"), "reason": "Customer postponed project."},
            )
            return
        if index == 1:
            return
        if index == 2:
            OrderProgressCommandService.progress(
                users["manager"], order.pk, {"progress_percent": 25, "milestone_note": marker_text("started")}
            )
            return
        if index == 3:
            OrderProgressCommandService.hold(
                users["manager"],
                order.pk,
                {"progress_percent": 15, "milestone_note": marker_text("hold"), "reason": "Awaiting material certificate."},
            )
            return
        if index == 4:
            OrderProgressCommandService.hold(
                users["manager"],
                order.pk,
                {"progress_percent": 20, "milestone_note": marker_text("hold"), "reason": "Customer drawing confirmation."},
            )
            OrderProgressCommandService.resume(
                users["manager"], order.pk, {"progress_percent": 35, "milestone_note": marker_text("resumed")}
            )
            return
        if index in {5, 6}:
            OrderProgressCommandService.progress(
                users["manager"], order.pk, {"progress_percent": 60, "milestone_note": marker_text("machining")}
            )
            OrderProgressCommandService.complete(
                users["manager"], order.pk, {"milestone_note": marker_text("completed")}
            )
            return
        OrderProgressCommandService.cancel(
            users["manager"],
            order.pk,
            {"progress_percent": 0, "milestone_note": marker_text("cancelled"), "reason": "Customer postponed project."},
        )

    def _create_seed_revision(self, document, data, cleaned_content) -> None:
        """Create a new governed revision for an owned seed document refresh."""

        document.content = cleaned_content
        document.description = data["description"]
        document.metadata = data["metadata"]
        document.permission_level = data["permission_level"]
        document.department = data["department"]
        document.owner_email = data["owner_email"]
        document.effective_date = data["effective_date"]
        document.version += 1
        document.status = "DRAFT"
        document.active_version = True
        document.approved_version = None
        document.approved_at = None
        document.approved_by_email = ""
        document.approval_hash = ""
        document.ai_public_approved = False
        document.owner_reviewed_at = None
        document.owner_reviewed_by_email = ""
        document.owner_review_hash = ""
        document.pilot_corpus_approved = False
        document.save(update_fields=[
            "content", "description", "metadata", "permission_level", "department",
            "owner_email", "effective_date", "version", "status", "active_version",
            "approved_version", "approved_at", "approved_by_email", "approval_hash",
            "ai_public_approved", "owner_reviewed_at", "owner_reviewed_by_email",
            "owner_review_hash", "pilot_corpus_approved", "updated_at",
        ])
        DocumentVersion.objects.create(
            document=document,
            version=document.version,
            content=cleaned_content,
            content_hash=content_hash(cleaned_content),
            change_note="Production demo seed refresh",
            created_by_email=data["created_by_email"],
        )

    def _approve_and_index_seed_document(self, document, *, owner, approver, indexer) -> None:
        """Use the normal governance services; never bypass the indexing policy."""

        workflow = KnowledgeGovernanceService()
        if document.status == "DRAFT":
            workflow.submit_review(document.id, actor=owner)
            document.refresh_from_db()
        if document.status == "REVIEW":
            PilotGovernanceService().record_owner_review(document.id, actor=owner)
            workflow.approve(document.id, actor=approver)
            document.refresh_from_db()
        if not KnowledgeAccessPolicy().can_index(document):
            raise RuntimeError("Production demo knowledge did not satisfy the approval policy.")
        if document.status != "INDEXED" or indexer.needs_reindex(document):
            indexer.reindex(
                document,
                created_by_email=document.created_by_email,
                change_note="Production demo governed knowledge indexing",
            )

    def _ensure_knowledge(self, users: dict[str, FoundationUser]) -> None:
        service = KnowledgeService(embedding_service=DevelopmentHashEmbeddingProvider())
        indexer = KnowledgeIndexer(embedding_service=service.embedding_service)
        owner = users["admin_2"]
        approver = users["admin"]
        for index in range(1, self.profile.knowledge_documents + 1):
            data = self.factories.knowledge_document(index)
            if self.profile.name == "SMALL":
                data["content"] = data["content"] * 5
            if self.profile.name == "FULL":
                data["content"] = data["content"] * 8
            existing = KnowledgeDocument.objects.filter(
                title=data["title"], metadata__dataset=DATASET_MARKER
            ).first()
            if existing:
                cleaned_content = service.text_processor.clean_text(data["content"])
                if existing.content != cleaned_content or not KnowledgeAccessPolicy().can_index(existing) and existing.status not in {"DRAFT", "REVIEW"}:
                    self._create_seed_revision(existing, data, cleaned_content)
                    self.report.bump("knowledge_documents_refreshed")
                self._approve_and_index_seed_document(
                    existing, owner=owner, approver=approver, indexer=indexer,
                )
                self.report.reuse("knowledge_documents")
                continue
            document = service.create_document(**data)
            self._approve_and_index_seed_document(
                document, owner=owner, approver=approver, indexer=indexer,
            )
            self.report.bump("knowledge_documents")

    def _ensure_ai_eval_cases(self) -> None:
        cases = load_ai_eval_cases(self.profile.name)
        self.report.counts["ai_eval_cases"] = len(cases)

    def _validate(self, context: SeedContext) -> None:
        assert_no_deliverable_seed_pii()
        counts = owned_business_counts(self.profile.name)
        for key, value in counts.items():
            self.report.counts[f"actual_{key}"] = value
        self.report.lifecycle_paths.extend(
            [
                "RFQ create/add_line/submit/start_review/request_information/complete_review/archive",
                "Quotation create/submit/reject/create_revision/approve/send/customer_decision",
                "Accepted quotation convert_to_order",
                "Order progress/hold/resume/complete/cancel",
                "KnowledgeService.create_document with deterministic DevelopmentHashEmbeddingProvider",
            ]
        )
