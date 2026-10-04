"""Fail-closed object access policy for AI Sales reads."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.db.models import Q

from apps.business_core.models import BusinessCustomer
from apps.foundation.services import FoundationPermissionService
from apps.sales.models import SalesLead, SalesOpportunity, SalesQuotation
from apps.sales.services.rfq_access_service import RfqAccessService


class AISalesAccessPolicy:
    """Keep AI Sales visibility no broader than the invoking principal."""

    def require_principal(self, user):
        if user is None or not getattr(user, "is_active", False):
            raise PermissionDenied("An active principal is required for AI Sales data.")
        if not FoundationPermissionService().has_permission(user, "ai_sales", "read"):
            raise PermissionDenied("Missing permission: ai_sales:read")
        return user

    def leads(self, user):
        user = self.require_principal(user)
        return SalesLead.objects.filter(owner_id=user.id)

    def customers(self, user):
        user = self.require_principal(user)
        return BusinessCustomer.objects.filter(
            Q(created_by_id=user.id) | Q(crm_profile__assigned_owner_id=user.id)
        ).distinct()

    def opportunities(self, user):
        user = self.require_principal(user)
        return SalesOpportunity.objects.filter(sales_owner_id=user.id)

    def quotations(self, user):
        user = self.require_principal(user)
        return SalesQuotation.objects.filter(
            Q(created_by_id=user.id) | Q(approval_decisions__reviewer_id=user.id)
        ).distinct()

    def rfqs(self, user):
        self.require_principal(user)
        return RfqAccessService().visible_queryset(user)
