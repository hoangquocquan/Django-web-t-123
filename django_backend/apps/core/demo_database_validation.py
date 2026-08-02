"""Read-only validation helpers for the local Django demonstration database.

The functions in this module never create, update, or delete business records.
CRUD behaviour is validated separately with Django's isolated test database.
"""

from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path
from typing import Any

from django.conf import settings
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.business_core.models import BusinessCustomer, BusinessProduct
from apps.crm.models import CrmCustomerProfile
from apps.foundation.models import FoundationRole, FoundationUser
from apps.knowledge.models import KnowledgeChunk, KnowledgeDocument
from apps.sales.models import SalesLead, SalesOpportunity, SalesQuotation

EXPECTED_COUNTS = {
    "products": 214,
    "customers": 501,
    "leads": 1003,
    "quotations": 503,
    "knowledge_documents": 105,
    "users": 17,
}

MODEL_TABLES: dict[str, tuple[Any, str]] = {
    "products": (BusinessProduct, "business_products"),
    "customers": (CrmCustomerProfile, "crm_platform_customer_profiles"),
    "leads": (SalesLead, "sales_platform_leads"),
    "quotations": (SalesQuotation, "sales_platform_quotations"),
    "knowledge_documents": (KnowledgeDocument, "knowledge_documents"),
    "users": (FoundationUser, "foundation_users"),
}


def sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 digest without loading the database into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def database_metadata() -> dict:
    """Describe the configured database and validate its SQLite header."""
    raw_name = str(settings.DATABASES["default"]["NAME"])
    in_memory = raw_name == ":memory:" or raw_name.startswith("file:memorydb_")
    configured_name = Path(raw_name).resolve() if not in_memory else Path(raw_name)
    exists = configured_name.exists()
    header = b""
    if exists:
        with configured_name.open("rb") as source:
            header = source.read(16)
    stat = configured_name.stat() if exists else None
    return {
        "engine": settings.DATABASES["default"]["ENGINE"],
        "path": str(configured_name),
        "exists": exists or in_memory,
        "in_memory": in_memory,
        "size_bytes": stat.st_size if stat else 0,
        "last_modified_epoch": stat.st_mtime if stat else None,
        "readable": exists,
        "writable": exists and configured_name.parent.exists(),
        "sqlite_header_valid": header == b"SQLite format 3\x00" or in_memory,
        "sha256": sha256_file(configured_name) if exists else "",
    }


def _sqlite_counts(database_path: Path) -> dict:
    """Count rows through a read-only SQLite connection for ORM comparison."""
    if str(settings.DATABASES["default"]["NAME"]) == ":memory:" or str(
        settings.DATABASES["default"]["NAME"]
    ).startswith("file:memorydb_"):
        with connection.cursor() as cursor:
            result = {}
            for key, (_model, table) in MODEL_TABLES.items():
                quoted_table = connection.ops.quote_name(table)
                # Identifier comes only from the fixed MODEL_TABLES mapping.
                cursor.execute(f"SELECT COUNT(*) FROM {quoted_table}")  # nosec B608
                result[key] = cursor.fetchone()[0]
            return result
    uri = f"file:{database_path.as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as database:
        return {
            key: database.execute(
                # Identifier comes only from the fixed MODEL_TABLES mapping.
                f'SELECT COUNT(*) FROM "{table}"'  # nosec B608
            ).fetchone()[0]
            for key, (_model, table) in MODEL_TABLES.items()
        }


def _table_inventory() -> list[dict]:
    """Return Django's table inventory with row counts for managed tables."""
    inventory = []
    with connection.cursor() as cursor:
        for table in sorted(connection.introspection.table_names(cursor)):
            quoted_table = connection.ops.quote_name(table)
            # Identifier is returned by Django introspection and quoted by the backend.
            cursor.execute(f"SELECT COUNT(*) FROM {quoted_table}")  # nosec B608
            inventory.append({"table": table, "rows": cursor.fetchone()[0]})
    return inventory


def _quality_findings() -> dict:
    """Find deterministic data-quality issues without changing any records."""
    product_statuses = {"draft", "published", "archived"}
    lead_statuses = {value for value, _label in SalesLead.STATUS_CHOICES}
    opportunity_statuses = {value for value, _label in SalesOpportunity.STATUS_CHOICES}
    quotation_statuses = {value for value, _label in SalesQuotation.STATUS_CHOICES}

    critical: list[dict] = []
    high: list[dict] = []
    medium: list[dict] = []
    low: list[dict] = []
    informational: list[dict] = []

    checks = {
        "products_empty_name": BusinessProduct.objects.filter(name="").count(),
        "products_negative_price": BusinessProduct.objects.filter(price__lt=0).count(),
        "products_missing_category": BusinessProduct.objects.filter(
            category_name=""
        ).count(),
        "products_invalid_status": BusinessProduct.objects.exclude(
            status__in=product_statuses
        ).count(),
        "customers_empty_contact": BusinessCustomer.objects.filter(
            contact_name=""
        ).count(),
        "customers_missing_company": BusinessCustomer.objects.filter(
            company_name=""
        ).count(),
        "leads_missing_company": SalesLead.objects.filter(company="").count(),
        "leads_missing_source": SalesLead.objects.filter(lead_source="").count(),
        "leads_missing_owner": SalesLead.objects.filter(owner__isnull=True).count(),
        "leads_invalid_status": SalesLead.objects.exclude(
            status__in=lead_statuses
        ).count(),
        "opportunities_invalid_status": SalesOpportunity.objects.exclude(
            status__in=opportunity_statuses
        ).count(),
        "opportunities_probability_over_100": SalesOpportunity.objects.filter(
            probability__gt=100
        ).count(),
        "quotations_negative_total": SalesQuotation.objects.filter(total__lt=0).count(),
        "quotations_invalid_status": SalesQuotation.objects.exclude(
            status__in=quotation_statuses
        ).count(),
        "quotations_without_customer_or_opportunity": SalesQuotation.objects.filter(
            customer__isnull=True, opportunity__isnull=True
        ).count(),
        "documents_without_chunks": KnowledgeDocument.objects.filter(
            chunks__isnull=True
        )
        .distinct()
        .count(),
        "chunks_without_embedding": KnowledgeChunk.objects.filter(
            embedding__isnull=True
        ).count(),
        "users_without_role": FoundationUser.objects.filter(role__isnull=True).count(),
        "roles_without_permissions": FoundationRole.objects.filter(
            permissions__isnull=True
        )
        .distinct()
        .count(),
    }

    severe_keys = {
        "products_empty_name",
        "products_negative_price",
        "customers_empty_contact",
        "leads_missing_company",
        "leads_invalid_status",
        "opportunities_invalid_status",
        "opportunities_probability_over_100",
        "quotations_negative_total",
        "quotations_invalid_status",
        "users_without_role",
        "roles_without_permissions",
    }
    for key, count in checks.items():
        if not count:
            continue
        finding = {"code": key, "count": count}
        if key in severe_keys:
            high.append(finding)
        elif key in {"documents_without_chunks", "chunks_without_embedding"}:
            medium.append(finding)
        else:
            low.append(finding)

    informational.append(
        {
            "code": "default_demo_admin_password",
            "count": FoundationUser.objects.filter(
                email="admin@mecprecision.vn"
            ).count(),
            "message": "Local demo credential must never be reused in production.",
        }
    )
    return {
        "checks": checks,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "informational": informational,
    }


def _performance_snapshot() -> dict:
    """Measure representative paginated ORM reads and detect obvious N+1 queries."""
    operations = {
        "products_page": lambda: list(BusinessProduct.objects.order_by("id")[:25]),
        "customers_page": lambda: list(BusinessCustomer.objects.order_by("id")[:25]),
        "leads_page": lambda: list(
            SalesLead.objects.select_related("owner").order_by("id")[:25]
        ),
        "quotations_page": lambda: list(
            SalesQuotation.objects.select_related("customer", "opportunity").order_by(
                "id"
            )[:25]
        ),
        "knowledge_page": lambda: list(
            KnowledgeDocument.objects.prefetch_related("chunks").order_by("id")[:25]
        ),
    }
    result = {}
    for name, operation in operations.items():
        started = time.perf_counter()
        with CaptureQueriesContext(connection) as captured:
            records = operation()
            if name == "knowledge_page":
                for record in records:
                    list(record.chunks.all())
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        result[name] = {
            "records": len(records),
            "queries": len(captured),
            "elapsed_ms": elapsed_ms,
            "n_plus_one_detected": len(captured) > 3,
            "paginated": True,
        }
    return result


def collect_demo_database_validation(expected_counts=None) -> dict:
    """Collect a complete read-only validation result for the configured database."""
    expected = dict(expected_counts or EXPECTED_COUNTS)
    metadata = database_metadata()
    orm_counts = {
        key: model.objects.count() for key, (model, _table) in MODEL_TABLES.items()
    }
    sqlite_counts = _sqlite_counts(Path(metadata["path"]))
    count_status = {
        key: (
            "PASS"
            if orm_counts[key] == expected[key] == sqlite_counts[key]
            else "PASS_WITH_DATA_DRIFT"
            if orm_counts[key] == sqlite_counts[key]
            else "FAIL"
        )
        for key in expected
    }
    quality = _quality_findings()
    decision = "DEMO_DATABASE_VALIDATION_PASS"
    if quality["critical"] or quality["high"] or "FAIL" in count_status.values():
        decision = "DEMO_DATABASE_VALIDATION_FAILED"
    elif "PASS_WITH_DATA_DRIFT" in count_status.values():
        decision = "DEMO_DATABASE_VALIDATION_PASS_WITH_DATA_DRIFT"

    return {
        "database": metadata,
        "expected_counts": expected,
        "orm_counts": orm_counts,
        "sqlite_counts": sqlite_counts,
        "count_status": count_status,
        "orm_sqlite_consistent": orm_counts == sqlite_counts,
        "table_inventory": _table_inventory(),
        "integrity_findings": quality,
        "performance": _performance_snapshot(),
        "decision": decision,
        "read_only_validation": True,
    }
