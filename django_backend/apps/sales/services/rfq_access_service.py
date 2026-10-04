"""Object-scope policy for private RFQ decision-support workflows."""

from django.db.models import Q

from apps.sales.models import SalesRfq


class RfqAccessService:
    """Apply the smallest proven RFQ scope without claiming tenant isolation."""

    elevated_roles = frozenset({"admin", "manager"})

    @staticmethod
    def _role_name(user):
        return str(getattr(getattr(user, "role", None), "name", "")).casefold()

    def visible_queryset(self, user):
        """Return RFQs visible to the current internal sales principal."""
        queryset = SalesRfq.objects.select_related(
            "customer", "assigned_to", "created_by", "updated_by"
        )
        if not user or not getattr(user, "is_active", False):
            return queryset.none()
        role_name = self._role_name(user)
        if role_name in self.elevated_roles:
            return queryset
        if role_name == "sales":
            return queryset.filter(Q(created_by=user) | Q(assigned_to=user)).distinct()
        return queryset.none()

    def get_visible(self, user, rfq_id):
        """Return one scoped RFQ or the normal not-found result to avoid ID leaks."""
        return self.visible_queryset(user).get(pk=rfq_id)
