"""Fail-closed boundary for noncanonical services sharing canonical tables."""

from django.core.exceptions import ValidationError


def require_legacy_record(record, *, entity_name):
    """Reject any legacy-service mutation of an MVP_V1 aggregate."""
    if getattr(record, "data_contract", None) != "LEGACY":
        raise ValidationError(
            f"Canonical MVP_V1 {entity_name} records may be changed only through canonical commands."
        )
    return record
