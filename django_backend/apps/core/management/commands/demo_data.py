"""Shared helpers for generating and clearing safe enterprise demo data."""

from __future__ import annotations

import random
from dataclasses import dataclass
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils.text import slugify

from apps.business_core.models import (
    BusinessCustomer,
    BusinessProduct,
    InventoryItem,
    InventoryTransaction,
    InventoryWarehouse,
)
from apps.crm.models import CrmCustomerProfile, CrmInteraction, CrmNote, CrmTask, CrmTimelineEvent
from apps.foundation.models import FoundationPermission, FoundationRole, FoundationRolePermission, FoundationUser, FoundationUserProfile
from apps.knowledge.models import KnowledgeDocument
from apps.knowledge.services.knowledge_service import KnowledgeService
from apps.sales.models import SalesActivity, SalesFollowUp, SalesLead, SalesOpportunity, SalesQuotation, SalesQuotationLine
from apps.transaction_domain.models import (
    OrderStatusHistory,
    TransactionHistory,
    TransactionOrder,
    TransactionOrderItem,
    WorkflowApproval,
)


DEMO_PREFIX = "DEMO"
DEMO_EMAIL_DOMAIN = "demo.mecprecision.local"
DEMO_PASSWORD = "Demo12345!"


try:
    from faker import Faker as FakerFactory
except ImportError:  # pragma: no cover - used only when Faker is not installed locally.
    FakerFactory = None


class SimpleFaker:
    """Small deterministic fallback when the Faker package is not installed."""

    first_names = ["An", "Binh", "Cuong", "Dung", "Hoa", "Khanh", "Linh", "Minh", "Quan", "Trang"]
    last_names = ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Vu", "Dang", "Do"]
    streets = ["Nguyen Van Linh", "Vo Van Kiet", "Pham Van Dong", "Cong Hoa", "Dien Bien Phu"]

    def __init__(self, seed=2026):
        self.random = random.Random(seed)

    def seed_instance(self, seed):
        """Match Faker's seed API."""
        self.random.seed(seed)

    def name(self):
        """Return a Vietnamese-style demo contact name."""
        return f"{self.random.choice(self.last_names)} {self.random.choice(self.first_names)}"

    def company(self):
        """Return a fictional company name."""
        suffix = self.random.choice(["Manufacturing", "Precision", "Industrial", "Automation", "Mechanical"])
        return f"{self.random.choice(self.last_names)} {suffix} Demo Co"

    def address(self):
        """Return a fictional address."""
        return f"{self.random.randint(1, 999)} {self.random.choice(self.streets)}, Ho Chi Minh City"

    def phone_number(self):
        """Return a safe fictional phone number."""
        return f"0900{self.random.randint(100000, 999999)}"

    def sentence(self, nb_words=8):
        """Return a simple generated sentence."""
        words = ["precision", "CNC", "fixture", "quality", "inspection", "quotation", "delivery", "material"]
        return " ".join(self.random.choice(words) for _ in range(nb_words)).capitalize() + "."

    def paragraph(self, nb_sentences=3):
        """Return a simple generated paragraph."""
        return " ".join(self.sentence() for _ in range(nb_sentences))


def make_faker(seed):
    """Create Faker when available and fallback safely when it is missing."""
    fake = FakerFactory("vi_VN") if FakerFactory else SimpleFaker(seed=seed)
    fake.seed_instance(seed)
    return fake


@dataclass(frozen=True)
class DemoCounts:
    """Data volumes for one demo generation run."""

    customers: int = 500
    products: int = 200
    leads: int = 1000
    activities: int = 5000
    opportunities: int = 300
    quotations: int = 500
    orders: int = 200
    documents: int = 100


class DemoDataCleaner:
    """Delete only records that were created by the demo generator."""

    @transaction.atomic
    def clear(self):
        """Remove demo data in dependency-safe order."""
        demo_customers = BusinessCustomer.objects.filter(notes__contains="demo_data=true")
        demo_products = BusinessProduct.objects.filter(sku__startswith=f"{DEMO_PREFIX}-")
        demo_leads = SalesLead.objects.filter(email__endswith=f"@{DEMO_EMAIL_DOMAIN}")
        demo_orders = TransactionOrder.objects.filter(order_number__startswith="DO-DEMO-")
        demo_quotes = SalesQuotation.objects.filter(quotation_number__startswith="SQ-DEMO-")
        demo_opportunities = SalesOpportunity.objects.filter(title__startswith="[DEMO]")

        TransactionHistory.objects.filter(order__in=demo_orders).delete()
        WorkflowApproval.objects.filter(order__in=demo_orders).delete()
        OrderStatusHistory.objects.filter(order__in=demo_orders).delete()
        TransactionOrderItem.objects.filter(order__in=demo_orders).delete()
        demo_orders.delete()

        SalesQuotationLine.objects.filter(quotation__in=demo_quotes).delete()
        demo_quotes.delete()
        SalesActivity.objects.filter(lead__in=demo_leads).delete()
        SalesActivity.objects.filter(customer__in=demo_customers).delete()
        SalesFollowUp.objects.filter(lead__in=demo_leads).delete()
        SalesFollowUp.objects.filter(customer__in=demo_customers).delete()
        demo_opportunities.delete()
        demo_leads.delete()

        CrmTimelineEvent.objects.filter(customer__in=demo_customers).delete()
        CrmTask.objects.filter(customer__in=demo_customers).delete()
        CrmNote.objects.filter(customer__in=demo_customers).delete()
        CrmInteraction.objects.filter(customer__in=demo_customers).delete()
        CrmCustomerProfile.objects.filter(customer__in=demo_customers).delete()

        InventoryTransaction.objects.filter(item__product__in=demo_products).delete()
        InventoryItem.objects.filter(product__in=demo_products).delete()
        InventoryWarehouse.objects.filter(code__startswith="DEMO-").delete()
        demo_products.delete()
        demo_customers.delete()

        KnowledgeDocument.objects.filter(title__startswith="[DEMO]").delete()
        FoundationUser.objects.filter(email__endswith=f"@{DEMO_EMAIL_DOMAIN}").delete()
        FoundationRole.objects.filter(name__startswith="demo-").delete()
        return {"status": "cleared"}


class DemoDataGenerator:
    """Generate a realistic but completely fictional MEC demo dataset."""

    industries = ["Automotive", "Mechanical Manufacturing", "Electronics", "Industrial Equipment", "Construction"]
    countries = ["Vietnam", "Japan", "South Korea", "Thailand", "Singapore"]
    customer_statuses = ["active", "lead", "inactive"]
    tiers = ["A", "B", "C"]
    categories = ["CNC Components", "Precision Parts", "Metal Components", "Assembly Parts", "Industrial Equipment"]
    materials = ["SUS304", "S45C", "A6061", "SKD11", "Brass", "POM", "Titanium"]
    lead_sources = ["Website", "Email", "Referral", "Trade Event", "Partner"]
    lead_statuses = ["new", "contacted", "meeting", "quotation", "negotiation", "won", "lost"]
    quote_statuses = ["draft", "review", "approved", "sent", "accepted", "lost"]
    order_statuses = ["pending", "confirmed", "production", "completed", "cancelled"]
    knowledge_types = ["Product Catalogue", "Technical Specification", "Quality Procedure", "Manufacturing Guide", "FAQ"]

    def __init__(self, counts=None, seed=2026):
        """Prepare deterministic random generators for repeatable demo data."""
        self.counts = counts or DemoCounts()
        self.random = random.Random(seed)
        self.fake = make_faker(seed)

    @transaction.atomic
    def generate(self, clean=True):
        """Create the complete demo dataset inside one database transaction."""
        if clean:
            DemoDataCleaner().clear()
        users = self._create_users()
        customers = self._create_customers(users)
        products = self._create_products()
        warehouses = self._create_inventory(products)
        leads = self._create_leads(users)
        self._create_crm_data(customers, users)
        opportunities = self._create_opportunities(leads, customers, users)
        quotations = self._create_quotations(opportunities, customers, products, users)
        orders = self._create_orders(customers, products, users)
        documents = self._create_knowledge_documents(users)
        self._create_activity_history(leads, customers, opportunities, users)
        summary = {
            "users": len(users),
            "customers": len(customers),
            "products": len(products),
            "warehouses": len(warehouses),
            "leads": len(leads),
            "opportunities": len(opportunities),
            "quotations": len(quotations),
            "orders": len(orders),
            "knowledge_documents": len(documents),
            "sales_activities": SalesActivity.objects.filter(subject__startswith="[DEMO]").count(),
            "crm_interactions": CrmInteraction.objects.filter(subject__startswith="[DEMO]").count(),
        }
        summary["dashboard_validation"] = self._dashboard_validation()
        summary["ai_validation"] = self._ai_validation()
        return summary

    def _create_users(self):
        """Create demo users, roles, permissions, and profiles."""
        permission_specs = [
            ("*", "*"),
            ("crm", "read"),
            ("crm", "write"),
            ("sales", "read"),
            ("sales", "write"),
            ("knowledge", "read"),
            ("knowledge", "write"),
            ("ai_sales", "read"),
            ("agent", "write"),
        ]
        permissions = []
        for module, action in permission_specs:
            permission, _created = FoundationPermission.objects.get_or_create(
                module=module,
                action=action,
                defaults={"code": f"{module}:{action}", "description": f"Demo permission {module}:{action}"},
            )
            permissions.append(permission)

        users = []
        specs = [
            ("ceo", "CEO", "Executive", ["*:*"]),
            ("sales.manager", "Sales Manager", "Sales", ["crm:read", "crm:write", "sales:read", "sales:write", "knowledge:read", "ai_sales:read"]),
            ("technical.manager", "Technical Manager", "Technical", ["knowledge:read", "knowledge:write", "sales:read", "ai_sales:read"]),
            ("sales.staff1", "Sales Staff 1", "Sales", ["crm:read", "crm:write", "sales:read", "sales:write", "ai_sales:read"]),
            ("sales.staff2", "Sales Staff 2", "Sales", ["crm:read", "crm:write", "sales:read", "sales:write", "ai_sales:read"]),
            ("engineer1", "Engineer 1", "Engineering", ["knowledge:read", "knowledge:write", "sales:read"]),
            ("engineer2", "Engineer 2", "Engineering", ["knowledge:read", "knowledge:write", "sales:read"]),
        ]
        for key, full_name, department, role_permissions in specs:
            role, _created = FoundationRole.objects.get_or_create(
                name=f"demo-{key}",
                defaults={"description": f"Demo role for {department} department"},
            )
            if "*:*" in role_permissions:
                selected_permissions = permissions
            else:
                wanted = set(role_permissions)
                selected_permissions = [permission for permission in permissions if f"{permission.module}:{permission.action}" in wanted]
            for permission in selected_permissions:
                FoundationRolePermission.objects.get_or_create(role=role, permission=permission)
            user, _created = FoundationUser.objects.get_or_create(
                email=f"{key}@{DEMO_EMAIL_DOMAIN}",
                defaults={
                    "full_name": f"{full_name} Demo",
                    "password_hash": make_password(DEMO_PASSWORD),
                    "role": role,
                },
            )
            FoundationUserProfile.objects.get_or_create(
                user=user,
                defaults={
                    "phone": self.fake.phone_number()[:50],
                    "language": "vi",
                    "timezone": "Asia/Tokyo",
                },
            )
            users.append(user)
        return users

    def _create_customers(self, users):
        """Create fictional enterprise customers."""
        customers = []
        for index in range(1, self.counts.customers + 1):
            industry = self.random.choice(self.industries)
            tier = self.random.choice(self.tiers)
            status = self.random.choice(self.customer_statuses)
            contact_name = self.fake.name()
            company = f"{self.fake.company()} {index:03d}"
            customer = BusinessCustomer.objects.create(
                company_name=company[:220],
                contact_name=contact_name[:160],
                email=f"demo.customer.{index:04d}@{DEMO_EMAIL_DOMAIN}",
                phone=self.fake.phone_number()[:80],
                country=self.random.choice(self.countries),
                status=status,
                notes=f"demo_data=true; industry={industry}; tier={tier}; address={self.fake.address()}",
            )
            customers.append(customer)
        return customers

    def _create_products(self):
        """Create fictional MEC products and technical descriptions."""
        products = []
        for index in range(1, self.counts.products + 1):
            category = self.random.choice(self.categories)
            material = self.random.choice(self.materials)
            name = f"{category} {material} Demo {index:03d}"
            price = Decimal(self.random.randint(25, 2500)).quantize(Decimal("0.01"))
            product = BusinessProduct.objects.create(
                category_name=category,
                name=name,
                slug=f"demo-product-{index:04d}-{slugify(name)[:80]}",
                sku=f"{DEMO_PREFIX}-SKU-{index:04d}",
                price=price,
                status=self.random.choice(["draft", "published", "archived"]),
                short_description=f"Demo {category.lower()} made from {material}.",
                description=f"demo_data=true; Material: {material}. Specification: tolerance +/-0.01mm, CNC inspection ready.",
                seo_title=f"{name} | MecPrecision Demo",
                seo_description=f"Fictional demo product for {category} using {material}.",
                seo_keywords=f"{category}, {material}, CNC, demo",
                sort_order=index,
            )
            products.append(product)
        return products

    def _create_inventory(self, products):
        """Create demo warehouses and stock balances."""
        warehouses = [
            InventoryWarehouse.objects.create(code="DEMO-HCM", name="Demo Ho Chi Minh Warehouse", location="Ho Chi Minh City"),
            InventoryWarehouse.objects.create(code="DEMO-QC", name="Demo Quality Control Storage", location="Factory QC Area"),
        ]
        items = []
        for product in products[: min(len(products), 80)]:
            warehouse = self.random.choice(warehouses)
            quantity = Decimal(self.random.randint(5, 500))
            item = InventoryItem.objects.create(
                product=product,
                warehouse=warehouse,
                quantity=quantity,
                reserved_quantity=Decimal(self.random.randint(0, 20)),
                reorder_point=Decimal(self.random.randint(5, 30)),
            )
            items.append(item)
        InventoryTransaction.objects.bulk_create(
            [
                InventoryTransaction(
                    item=item,
                    transaction_type="initial",
                    quantity_delta=item.quantity,
                    reason="demo_data=true; initial demo stock",
                    reference="DEMO-STOCK",
                    created_by="demo-generator",
                )
                for item in items
            ]
        )
        return warehouses

    def _create_leads(self, users):
        """Create sales leads across a realistic pipeline distribution."""
        owners = [user for user in users if "sales" in user.email] or users
        leads = []
        for index in range(1, self.counts.leads + 1):
            industry = self.random.choice(self.industries)
            status = self.random.choice(self.lead_statuses)
            leads.append(
                SalesLead(
                    lead_source=self.random.choice(self.lead_sources),
                    company=f"{self.fake.company()} Lead {index:04d}"[:220],
                    contact_person=self.fake.name()[:160],
                    email=f"demo.lead.{index:04d}@{DEMO_EMAIL_DOMAIN}",
                    phone=self.fake.phone_number()[:80],
                    industry=industry,
                    status=status,
                    priority=self.random.choice(["low", "medium", "high"]),
                    owner=self.random.choice(owners),
                    notes=f"demo_data=true; Customer requested quotation for CNC parts in {industry}.",
                )
            )
        return SalesLead.objects.bulk_create(leads, batch_size=500)

    def _create_crm_data(self, customers, users):
        """Create CRM profile, interactions, notes, tasks, and timeline events."""
        owners = users or [None]
        CrmCustomerProfile.objects.bulk_create(
            [
                CrmCustomerProfile(
                    customer=customer,
                    segment=self.random.choice(["enterprise", "standard", "strategic"]),
                    lifecycle_stage=self.random.choice(["lead", "qualified", "customer", "inactive"]),
                    preferred_contact_method=self.random.choice(["email", "phone", "meeting"]),
                    assigned_owner=self.random.choice(owners),
                    summary="demo_data=true; Fictional CRM profile for platform testing.",
                )
                for customer in customers
            ],
            batch_size=500,
        )
        sample_customers = customers[: min(len(customers), max(1, self.counts.activities))]
        interactions = []
        notes = []
        tasks = []
        timeline = []
        for index, customer in enumerate(sample_customers, start=1):
            interactions.append(
                CrmInteraction(
                    customer=customer,
                    interaction_type=self.random.choice(["call", "email", "meeting", "technical"]),
                    subject=f"[DEMO] Customer requested quotation {index}",
                    content="Customer requested quotation, technical discussion, follow-up meeting, or document sent.",
                    occurred_at=f"2026-07-{(index % 28) + 1:02d}",
                    created_by=self.random.choice(owners).email,
                )
            )
            notes.append(CrmNote(customer=customer, note="demo_data=true; Follow up after technical review.", created_by="demo-generator"))
            tasks.append(
                CrmTask(
                    customer=customer,
                    title=f"[DEMO] Follow up quotation {index}",
                    due_date=f"2026-08-{(index % 28) + 1:02d}",
                    status=self.random.choice(["open", "done", "pending"]),
                    owner=self.random.choice(owners),
                )
            )
            timeline.append(
                CrmTimelineEvent(
                    customer=customer,
                    event_type="demo_activity",
                    title=f"[DEMO] Timeline event {index}",
                    payload={"demo_data": True, "activity": "quotation_follow_up"},
                )
            )
        CrmInteraction.objects.bulk_create(interactions, batch_size=500)
        CrmNote.objects.bulk_create(notes, batch_size=500)
        CrmTask.objects.bulk_create(tasks, batch_size=500)
        CrmTimelineEvent.objects.bulk_create(timeline, batch_size=500)

    def _create_opportunities(self, leads, customers, users):
        """Create sales opportunities connected to leads and customers."""
        opportunities = []
        for index in range(1, self.counts.opportunities + 1):
            lead = self.random.choice(leads) if leads else None
            customer = self.random.choice(customers) if customers else None
            status = self.random.choice(["open", "proposal", "negotiation", "won", "lost"])
            opportunities.append(
                SalesOpportunity(
                    lead=lead,
                    customer=customer,
                    title=f"[DEMO] CNC annual supply opportunity {index:04d}",
                    value=Decimal(self.random.randint(5000, 250000)),
                    probability=self.random.randint(10, 95),
                    expected_close_date=f"2026-{self.random.randint(8, 12):02d}-{self.random.randint(1, 28):02d}",
                    sales_owner=self.random.choice(users),
                    status=status,
                    notes="demo_data=true; Sales opportunity for enterprise demo.",
                )
            )
        return SalesOpportunity.objects.bulk_create(opportunities, batch_size=300)

    def _create_quotations(self, opportunities, customers, products, users):
        """Create quotations and lines with calculated totals."""
        quotations = []
        for index in range(1, self.counts.quotations + 1):
            opportunity = self.random.choice(opportunities) if opportunities else None
            customer = opportunity.customer if opportunity and opportunity.customer else self.random.choice(customers)
            quotations.append(
                SalesQuotation(
                    opportunity=opportunity,
                    customer=customer,
                    quotation_number=f"SQ-DEMO-{index:06d}",
                    status=self.random.choice(self.quote_statuses),
                    approval_status=self.random.choice(["pending", "approved", "rejected", "needs_review"]),
                    created_by=self.random.choice(users),
                )
            )
        quotations = SalesQuotation.objects.bulk_create(quotations, batch_size=300)
        lines = []
        for quotation in quotations:
            for _line_index in range(self.random.randint(1, 3)):
                product = self.random.choice(products)
                quantity = Decimal(self.random.randint(1, 50))
                unit_price = product.price
                discount = Decimal(self.random.randint(0, 100))
                line_total = quantity * unit_price - discount
                lines.append(
                    SalesQuotationLine(
                        quotation=quotation,
                        product=product,
                        description=f"Demo line for {product.name}",
                        quantity=quantity,
                        unit_price=unit_price,
                        discount=discount,
                        line_total=line_total,
                    )
                )
        SalesQuotationLine.objects.bulk_create(lines, batch_size=500)
        for quotation in SalesQuotation.objects.filter(quotation_number__startswith="SQ-DEMO-").prefetch_related("lines"):
            subtotal = sum((line.quantity * line.unit_price for line in quotation.lines.all()), Decimal("0"))
            discount_total = sum((line.discount for line in quotation.lines.all()), Decimal("0"))
            quotation.subtotal = subtotal
            quotation.discount_total = discount_total
            quotation.total = subtotal - discount_total
            quotation.save(update_fields=["subtotal", "discount_total", "total", "updated_at"])
        return quotations

    def _create_orders(self, customers, products, users):
        """Create production orders, order items, status history, and audit logs."""
        orders = []
        for index in range(1, self.counts.orders + 1):
            status = self.random.choice(self.order_statuses)
            orders.append(
                TransactionOrder(
                    order_number=f"DO-DEMO-{index:06d}",
                    customer=self.random.choice(customers),
                    project_name=f"Demo production order {index}",
                    message="demo_data=true; Order created for platform validation.",
                    status=status,
                    assigned_to=self.random.choice(users),
                    internal_note="demo_data=true; Fictional order.",
                    total_amount=Decimal("0"),
                    quoted_at=f"2026-07-{(index % 28) + 1:02d}",
                    completed_at=f"2026-08-{(index % 28) + 1:02d}" if status == "completed" else "",
                )
            )
        orders = TransactionOrder.objects.bulk_create(orders, batch_size=300)
        items = []
        histories = []
        approvals = []
        events = []
        for order in orders:
            total = Decimal("0")
            for line_index in range(self.random.randint(1, 3)):
                product = self.random.choice(products)
                quantity = self.random.randint(1, 20)
                line_total = Decimal(quantity) * product.price
                total += line_total
                items.append(
                    TransactionOrderItem(
                        order=order,
                        product=product,
                        drawing_code=f"DWG-DEMO-{order.id}-{line_index}",
                        material_name=self.random.choice(self.materials),
                        quantity=quantity,
                        tolerance="+/-0.01mm",
                        note="demo_data=true; Generated order item.",
                        unit_price=product.price,
                        line_total=line_total,
                    )
                )
            order.total_amount = total
            order.save(update_fields=["total_amount", "updated_at"])
            histories.append(OrderStatusHistory(order=order, from_status="", to_status=order.status, actor="demo-generator", note="demo_data=true"))
            approvals.append(WorkflowApproval(order=order, requested_status=order.status, decision="approved", requested_by="demo-generator", reviewed_by="demo-manager"))
            events.append(
                TransactionHistory(
                    order=order,
                    entity_type="order",
                    entity_id=str(order.id),
                    action="demo_order_created",
                    actor="demo-generator",
                    payload={"demo_data": True, "status": order.status},
                )
            )
        TransactionOrderItem.objects.bulk_create(items, batch_size=500)
        OrderStatusHistory.objects.bulk_create(histories, batch_size=300)
        WorkflowApproval.objects.bulk_create(approvals, batch_size=300)
        TransactionHistory.objects.bulk_create(events, batch_size=300)
        return orders

    def _create_knowledge_documents(self, users):
        """Create searchable AI knowledge documents."""
        service = KnowledgeService()
        creator = users[0].email if users else "demo-generator"
        documents = []
        for index in range(1, self.counts.documents + 1):
            doc_type = self.random.choice(self.knowledge_types)
            material = self.random.choice(self.materials)
            content = (
                f"Demo knowledge document {index}. Type: {doc_type}. "
                f"MecPrecision can support CNC machining, fixture design, and quality inspection. "
                f"For material questions, {material} may be selected based on tolerance, corrosion resistance, and production volume. "
                "This is fictional demo content for AI search testing only."
            )
            documents.append(
                service.create_document(
                    title=f"[DEMO] {doc_type} {index:03d}",
                    content=content,
                    description=f"demo_data=true; Fictional {doc_type}.",
                    category_name=doc_type,
                    permission_level="internal",
                    created_by_email=creator,
                    metadata={"demo_data": True, "document_type": doc_type, "material": material},
                )
            )
        return documents

    def _create_activity_history(self, leads, customers, opportunities, users):
        """Create additional activity history up to the requested volume."""
        target = max(0, self.counts.activities - CrmInteraction.objects.filter(subject__startswith="[DEMO]").count())
        activities = []
        followups = []
        for index in range(1, target + 1):
            lead = self.random.choice(leads) if leads else None
            customer = self.random.choice(customers) if customers else None
            opportunity = self.random.choice(opportunities) if opportunities else None
            activities.append(
                SalesActivity(
                    lead=lead,
                    opportunity=opportunity,
                    customer=customer,
                    activity_type=self.random.choice(["call", "email", "meeting", "note"]),
                    subject=f"[DEMO] Sales activity {index:05d}",
                    content="demo_data=true; Customer requested quotation, document sent, or follow-up meeting.",
                    created_by=self.random.choice(users).email if users else "demo-generator",
                )
            )
            if index <= min(target, 500):
                followups.append(
                    SalesFollowUp(
                        lead=lead,
                        opportunity=opportunity,
                        customer=customer,
                        title=f"[DEMO] Follow-up reminder {index:05d}",
                        due_date=f"2026-08-{(index % 28) + 1:02d}",
                        status=self.random.choice(["open", "done", "pending"]),
                        owner=self.random.choice(users) if users else None,
                        note="demo_data=true; Follow-up reminder generated for demo.",
                    )
                )
        SalesActivity.objects.bulk_create(activities, batch_size=1000)
        SalesFollowUp.objects.bulk_create(followups, batch_size=500)

    def _dashboard_validation(self):
        """Return dashboard counts that UI and reports can verify."""
        open_pipeline = SalesOpportunity.objects.filter(title__startswith="[DEMO]").exclude(status__in=["won", "lost"])
        return {
            "customer_count": BusinessCustomer.objects.filter(notes__contains="demo_data=true").count(),
            "lead_count": SalesLead.objects.filter(email__endswith=f"@{DEMO_EMAIL_DOMAIN}").count(),
            "pipeline_value": str(sum((opportunity.value for opportunity in open_pipeline), Decimal("0"))),
            "quotation_count": SalesQuotation.objects.filter(quotation_number__startswith="SQ-DEMO-").count(),
            "order_count": TransactionOrder.objects.filter(order_number__startswith="DO-DEMO-").count(),
            "ai_activity_ready": KnowledgeDocument.objects.filter(title__startswith="[DEMO]").exists(),
        }

    def _ai_validation(self):
        """Return AI test prompts and the data domains they should use."""
        return {
            "scenarios": [
                {"prompt": "Analyze customer DEMO", "uses": ["CRM", "Sales"]},
                {"prompt": "Which product fits this customer?", "uses": ["Products", "Knowledge"]},
                {"prompt": "What material should be used?", "uses": ["Knowledge"]},
                {"prompt": "Which customer should sales contact?", "uses": ["CRM", "Sales"]},
            ],
            "knowledge_documents": KnowledgeDocument.objects.filter(title__startswith="[DEMO]").count(),
        }
