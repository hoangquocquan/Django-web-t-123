"""Explicit, principal-scoped business projections for internal AI only."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.db.models import Q

from apps.business_core.models import BusinessCustomer
from apps.foundation.services import FoundationPermissionService
from apps.knowledge.models import KnowledgeAuditEvent
from apps.transaction_domain.models import TransactionOrder


class BusinessKnowledgeConnector:
    """Never sample arbitrary rows; requested IDs require domain and row grants."""

    def build_context(self, query, *, user=None, customer_id=None, order_id=None):
        del query  # Natural-language text must not select rows.
        if customer_id is None and order_id is None:
            return {}  # The ordinary RAG path has no business-data enrichment.
        if user is None:
            self._deny(user)
        permissions = FoundationPermissionService()
        result = {}
        if customer_id is not None:
            if not permissions.has_permission(user, "customer", "view"):
                self._deny(user)
            customer = BusinessCustomer.objects.filter(
                pk=customer_id, created_by_id=user.id,
            ).values("id", "company_name", "status").first()
            if customer is None:
                self._deny(user)
            result["customer"] = customer
        if order_id is not None:
            if not permissions.has_permission(user, "order", "view"):
                self._deny(user)
            order = TransactionOrder.objects.filter(pk=order_id).filter(
                Q(assigned_to_id=user.id) | Q(created_by_id=user.id),
            ).values("id", "order_number", "status").first()
            if order is None:
                self._deny(user)
            result["order"] = order
        return result

    @staticmethod
    def _deny(user):
        KnowledgeAuditEvent.objects.create(
            event="denied", decision="denied", actor_id=getattr(user, "id", None),
        )
        raise PermissionDenied("Business context is unavailable for this principal.")
