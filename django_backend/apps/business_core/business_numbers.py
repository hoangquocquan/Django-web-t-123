"""Concurrency-safe allocation for human-readable business numbers."""

from __future__ import annotations

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import BusinessNumberSequence


GLOBAL_NAMESPACES = {"CUS", "PART", "MAT"}
YEAR_NAMESPACES = {"RFQ", "QT", "SO"}
SUPPORTED_NAMESPACES = GLOBAL_NAMESPACES | YEAR_NAMESPACES
MAX_ALLOCATION_ATTEMPTS = 3


def period_for_namespace(namespace, now=None):
    """Return the fixed period for one supported namespace."""
    normalized = str(namespace).strip().upper()
    if normalized in GLOBAL_NAMESPACES:
        return "GLOBAL"
    if normalized in YEAR_NAMESPACES:
        instant = now or timezone.now()
        return instant.strftime("%Y")
    raise ValueError(f"Unsupported business-number namespace: {namespace}")


def format_business_number(namespace, period, value):
    """Format a positive counter value using the approved business convention."""
    normalized = str(namespace).strip().upper()
    if normalized not in SUPPORTED_NAMESPACES:
        raise ValueError(f"Unsupported business-number namespace: {namespace}")
    if int(value) <= 0:
        raise ValueError("Business-number values must be positive.")
    if normalized in GLOBAL_NAMESPACES:
        if period != "GLOBAL":
            raise ValueError(f"{normalized} requires the GLOBAL period.")
        return f"{normalized}-{int(value):04d}"
    if len(str(period)) != 4 or not str(period).isdigit():
        raise ValueError(f"{normalized} requires a four-digit year period.")
    return f"{normalized}-{period}-{int(value):04d}"


@transaction.atomic
def _allocate_once(namespace, period):
    """Allocate once while holding the sequence row lock."""
    try:
        sequence = BusinessNumberSequence.objects.select_for_update().get(
            namespace=namespace,
            period=period,
        )
    except BusinessNumberSequence.DoesNotExist:
        try:
            with transaction.atomic():
                sequence = BusinessNumberSequence.objects.create(
                    namespace=namespace,
                    period=period,
                    last_value=0,
                )
        except IntegrityError:
            sequence = BusinessNumberSequence.objects.select_for_update().get(
                namespace=namespace,
                period=period,
            )

    sequence.last_value += 1
    sequence.save(update_fields=["last_value", "updated_at"])
    return format_business_number(namespace, period, sequence.last_value)


def allocate_business_number(namespace, *, now=None, max_attempts=MAX_ALLOCATION_ATTEMPTS):
    """Allocate one number, retrying an integrity race at most three times."""
    normalized = str(namespace).strip().upper()
    period = period_for_namespace(normalized, now=now)
    attempts = min(max(int(max_attempts), 1), MAX_ALLOCATION_ATTEMPTS)
    last_error = None
    for _attempt in range(attempts):
        try:
            return _allocate_once(normalized, period)
        except IntegrityError as exc:
            last_error = exc
    raise last_error
