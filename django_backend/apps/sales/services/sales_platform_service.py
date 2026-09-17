"""Django-owned sales platform service layer."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.business_core.models import BusinessCustomer, BusinessProduct
from apps.common.legacy_write_boundary import require_legacy_record
from apps.sales.models import (
    SalesActivity,
    SalesFollowUp,
    SalesLead,
    SalesOpportunity,
    SalesQuotation,
    SalesQuotationLine,
)

LEAD_STATUS_FLOW = [
    "new",
    "contacted",
    "meeting",
    "quotation",
    "negotiation",
    "won",
    "lost",
]
MONEY_QUANT = Decimal("0.01")


class SalesPlatformService:
    """Own professional sales workflow writes in Django."""

    def list_leads(self):
        """Return all leads with owner loaded."""
        return SalesLead.objects.select_related("owner").all()

    def create_lead(self, data, owner=None):
        """Create a new sales lead."""
        return SalesLead.objects.create(
            lead_source=data.get("lead_source", ""),
            company=data["company"],
            contact_person=data["contact_person"],
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            industry=data.get("industry", ""),
            status=data.get("status", "new"),
            priority=data.get("priority", "medium"),
            owner=owner,
            notes=data.get("notes", ""),
        )

    @transaction.atomic
    def advance_lead(self, lead_id, status, actor=""):
        """Move a lead to a valid pipeline status and record activity."""
        if status not in LEAD_STATUS_FLOW:
            raise ValidationError("Invalid lead status.")
        lead = SalesLead.objects.get(id=lead_id)
        previous = lead.status
        lead.status = status
        lead.save(update_fields=["status", "updated_at"])
        SalesActivity.objects.create(
            lead=lead,
            activity_type="pipeline",
            subject=f"Lead moved from {previous} to {status}",
            created_by=actor,
        )
        return lead

    @transaction.atomic
    def assign_lead(self, lead_id, owner, actor=""):
        """Assign a lead and preserve the assignment in the activity history."""
        lead = SalesLead.objects.select_for_update().get(id=lead_id)
        lead.owner = owner
        lead.save(update_fields=["owner", "updated_at"])
        SalesActivity.objects.create(
            lead=lead,
            activity_type="assignment",
            subject=f"Lead assigned to {owner.full_name}",
            created_by=actor,
        )
        return lead

    def list_opportunities(self):
        """Return opportunities with customer, lead, and owner loaded."""
        return SalesOpportunity.objects.select_related(
            "customer", "lead", "sales_owner"
        ).all()

    def create_opportunity(self, data, owner=None):
        """Create a sales opportunity."""
        title = str(data.get("title", "")).strip()
        if not title:
            raise ValidationError("Opportunity title is required.")
        value = Decimal(str(data.get("value", "0")))
        probability = int(data.get("probability", 10))
        if value < 0:
            raise ValidationError("Opportunity value cannot be negative.")
        if not 0 <= probability <= 100:
            raise ValidationError("Opportunity probability must be between 0 and 100.")
        lead = (
            SalesLead.objects.filter(id=data.get("lead_id")).first()
            if data.get("lead_id")
            else None
        )
        customer = (
            BusinessCustomer.objects.filter(id=data.get("customer_id")).first()
            if data.get("customer_id")
            else None
        )
        return SalesOpportunity.objects.create(
            lead=lead,
            customer=customer,
            title=title,
            value=value,
            probability=probability,
            expected_close_date=data.get("expected_close_date", ""),
            sales_owner=owner,
            status=data.get("status", "open"),
            notes=data.get("notes", ""),
        )

    def list_quotations(self):
        """Return managed quotations with related data."""
        return (
            SalesQuotation.objects.select_related(
                "opportunity", "customer", "created_by"
            )
            .prefetch_related("lines")
            .all()
        )

    @transaction.atomic
    def create_quotation(self, data, user=None):
        """Create a quotation with line items and calculated totals."""
        lines = data.get("lines", [])
        if not lines:
            raise ValidationError("Quotation requires at least one line.")
        opportunity = (
            SalesOpportunity.objects.filter(id=data.get("opportunity_id")).first()
            if data.get("opportunity_id")
            else None
        )
        customer = (
            BusinessCustomer.objects.filter(id=data.get("customer_id")).first()
            if data.get("customer_id")
            else None
        )
        quotation_number = data.get("quotation_number") or self._next_quotation_number()
        quotation = SalesQuotation.objects.create(
            data_contract="LEGACY",
            opportunity=opportunity,
            customer=customer,
            quotation_number=quotation_number,
            version=int(data.get("version", 1)),
            status=data.get("status", "draft"),
            approval_status=data.get("approval_status", "pending"),
            created_by=user,
        )
        for line in lines:
            product = (
                BusinessProduct.objects.filter(id=line.get("product_id")).first()
                if line.get("product_id")
                else None
            )
            quantity = Decimal(str(line.get("quantity", "1")))
            unit_price = Decimal(str(line.get("unit_price", "0")))
            discount = Decimal(str(line.get("discount", "0")))
            description = str(line.get("description", "")).strip()
            if not description:
                raise ValidationError("Quotation line description is required.")
            if quantity <= 0 or unit_price < 0 or discount < 0:
                raise ValidationError(
                    "Quotation amounts must be valid non-negative values."
                )
            if discount > quantity * unit_price:
                raise ValidationError(
                    "Quotation discount cannot exceed the line subtotal."
                )
            line_total = (quantity * unit_price - discount).quantize(MONEY_QUANT)
            SalesQuotationLine.objects.create(
                quotation=quotation,
                data_contract="LEGACY",
                product=product,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                discount=discount,
                line_total=line_total,
            )
        self.recalculate_quotation(quotation)
        return quotation

    def recalculate_quotation(self, quotation):
        """Recalculate quotation totals from line items."""
        require_legacy_record(quotation, entity_name="quotation")
        subtotal = Decimal(0)
        discount_total = Decimal(0)
        for line in quotation.lines.all():
            subtotal += line.quantity * line.unit_price
            discount_total += line.discount
        quotation.subtotal = subtotal.quantize(MONEY_QUANT)
        quotation.discount_total = discount_total.quantize(MONEY_QUANT)
        quotation.total = (subtotal - discount_total).quantize(MONEY_QUANT)
        quotation.save(
            update_fields=["subtotal", "discount_total", "total", "updated_at"]
        )
        return quotation

    def create_follow_up(self, data, owner=None):
        """Create a follow-up task/reminder."""
        title = str(data.get("title", "")).strip()
        if not title:
            raise ValidationError("Follow-up title is required.")
        return SalesFollowUp.objects.create(
            lead_id=data.get("lead_id"),
            opportunity_id=data.get("opportunity_id"),
            customer_id=data.get("customer_id"),
            title=title,
            due_date=data.get("due_date", ""),
            status=data.get("status", "open"),
            owner=owner,
            note=data.get("note", ""),
        )

    @transaction.atomic
    def approve_quotation(self, quotation_id, actor=""):
        """Record an explicit human quotation approval."""
        quotation = SalesQuotation.objects.select_for_update().get(id=quotation_id)
        require_legacy_record(quotation, entity_name="quotation")
        if quotation.approval_status == "approved":
            return quotation
        if quotation.status not in {"draft", "review"}:
            raise ValidationError("Only draft or review quotations can be approved.")
        quotation.approval_status = "approved"
        quotation.status = "approved"
        quotation.save(update_fields=["approval_status", "status", "updated_at"])
        SalesActivity.objects.create(
            opportunity=quotation.opportunity,
            customer=quotation.customer,
            activity_type="quotation_approval",
            subject=f"Quotation {quotation.quotation_number} approved",
            created_by=actor,
        )
        return quotation

    @transaction.atomic
    def handoff_quotation(self, quotation_id, actor=""):
        """Mark an approved quotation accepted and ready for order handoff."""
        quotation = SalesQuotation.objects.select_for_update().get(id=quotation_id)
        require_legacy_record(quotation, entity_name="quotation")
        if quotation.approval_status != "approved":
            raise ValidationError("Quotation requires human approval before handoff.")
        quotation.status = "accepted"
        quotation.save(update_fields=["status", "updated_at"])
        SalesActivity.objects.create(
            opportunity=quotation.opportunity,
            customer=quotation.customer,
            activity_type="order_handoff",
            subject=f"Quotation {quotation.quotation_number} handed off",
            created_by=actor,
        )
        return quotation

    def dashboard(self):
        """Return sales dashboard metrics."""
        lead_count = SalesLead.objects.count()
        won_count = SalesLead.objects.filter(status="won").count()
        pipeline_value = sum(
            (
                opportunity.value
                for opportunity in SalesOpportunity.objects.exclude(
                    status__in=["won", "lost"]
                )
            ),
            Decimal(0),
        )
        conversion_rate = round((won_count / lead_count) * 100, 2) if lead_count else 0
        quotation_status = {
            status: SalesQuotation.objects.filter(status=status).count()
            for status in ["draft", "review", "approved", "sent", "accepted", "lost"]
        }
        revenue_forecast = sum(
            (
                opportunity.value * Decimal(opportunity.probability) / Decimal(100)
                for opportunity in SalesOpportunity.objects.exclude(status__in=["lost"])
            ),
            Decimal(0),
        )
        return {
            "lead_count": lead_count,
            "pipeline_value": str(pipeline_value),
            "conversion_rate": conversion_rate,
            "quotation_status": quotation_status,
            "revenue_forecast": str(revenue_forecast),
        }

    def _next_quotation_number(self):
        """Create a deterministic quotation number for local demo."""
        return f"SQ-{SalesQuotation.objects.count() + 1:06d}"
