"""Django-owned sales platform service layer."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.business_core.models import BusinessCustomer, BusinessProduct
from apps.sales.models import (
    SalesActivity,
    SalesFollowUp,
    SalesLead,
    SalesOpportunity,
    SalesQuotation,
    SalesQuotationLine,
)


LEAD_STATUS_FLOW = ["new", "contacted", "meeting", "quotation", "negotiation", "won", "lost"]
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

    def list_opportunities(self):
        """Return opportunities with customer, lead, and owner loaded."""
        return SalesOpportunity.objects.select_related("customer", "lead", "sales_owner").all()

    def create_opportunity(self, data, owner=None):
        """Create a sales opportunity."""
        lead = SalesLead.objects.filter(id=data.get("lead_id")).first() if data.get("lead_id") else None
        customer = BusinessCustomer.objects.filter(id=data.get("customer_id")).first() if data.get("customer_id") else None
        return SalesOpportunity.objects.create(
            lead=lead,
            customer=customer,
            title=data["title"],
            value=Decimal(str(data.get("value", "0"))),
            probability=int(data.get("probability", 10)),
            expected_close_date=data.get("expected_close_date", ""),
            sales_owner=owner,
            status=data.get("status", "open"),
            notes=data.get("notes", ""),
        )

    def list_quotations(self):
        """Return managed quotations with related data."""
        return SalesQuotation.objects.select_related("opportunity", "customer", "created_by").prefetch_related("lines").all()

    @transaction.atomic
    def create_quotation(self, data, user=None):
        """Create a quotation with line items and calculated totals."""
        opportunity = SalesOpportunity.objects.filter(id=data.get("opportunity_id")).first() if data.get("opportunity_id") else None
        customer = BusinessCustomer.objects.filter(id=data.get("customer_id")).first() if data.get("customer_id") else None
        quotation_number = data.get("quotation_number") or self._next_quotation_number()
        quotation = SalesQuotation.objects.create(
            opportunity=opportunity,
            customer=customer,
            quotation_number=quotation_number,
            version=int(data.get("version", 1)),
            status=data.get("status", "draft"),
            approval_status=data.get("approval_status", "pending"),
            created_by=user,
        )
        for line in data.get("lines", []):
            product = BusinessProduct.objects.filter(id=line.get("product_id")).first() if line.get("product_id") else None
            quantity = Decimal(str(line.get("quantity", "1")))
            unit_price = Decimal(str(line.get("unit_price", "0")))
            discount = Decimal(str(line.get("discount", "0")))
            line_total = (quantity * unit_price - discount).quantize(MONEY_QUANT)
            SalesQuotationLine.objects.create(
                quotation=quotation,
                product=product,
                description=line.get("description", ""),
                quantity=quantity,
                unit_price=unit_price,
                discount=discount,
                line_total=line_total,
            )
        self.recalculate_quotation(quotation)
        return quotation

    def recalculate_quotation(self, quotation):
        """Recalculate quotation totals from line items."""
        subtotal = Decimal("0")
        discount_total = Decimal("0")
        for line in quotation.lines.all():
            subtotal += line.quantity * line.unit_price
            discount_total += line.discount
        quotation.subtotal = subtotal.quantize(MONEY_QUANT)
        quotation.discount_total = discount_total.quantize(MONEY_QUANT)
        quotation.total = (subtotal - discount_total).quantize(MONEY_QUANT)
        quotation.save(update_fields=["subtotal", "discount_total", "total", "updated_at"])
        return quotation

    def create_follow_up(self, data, owner=None):
        """Create a follow-up task/reminder."""
        return SalesFollowUp.objects.create(
            lead_id=data.get("lead_id"),
            opportunity_id=data.get("opportunity_id"),
            customer_id=data.get("customer_id"),
            title=data["title"],
            due_date=data.get("due_date", ""),
            status=data.get("status", "open"),
            owner=owner,
            note=data.get("note", ""),
        )

    def dashboard(self):
        """Return sales dashboard metrics."""
        lead_count = SalesLead.objects.count()
        won_count = SalesLead.objects.filter(status="won").count()
        pipeline_value = sum((opportunity.value for opportunity in SalesOpportunity.objects.exclude(status__in=["won", "lost"])), Decimal("0"))
        conversion_rate = round((won_count / lead_count) * 100, 2) if lead_count else 0
        quotation_status = {
            status: SalesQuotation.objects.filter(status=status).count()
            for status in ["draft", "review", "approved", "sent", "accepted", "lost"]
        }
        revenue_forecast = sum(
            (opportunity.value * Decimal(opportunity.probability) / Decimal("100") for opportunity in SalesOpportunity.objects.exclude(status__in=["lost"])),
            Decimal("0"),
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
