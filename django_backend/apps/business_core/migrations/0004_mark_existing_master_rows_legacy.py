"""Keep every pre-Phase-3B customer and product on the legacy contract."""

from django.db import migrations
from django.db.models import Count, Q


def mark_existing_rows_legacy(apps, schema_editor):
    """Idempotently prevent ambiguous existing rows from being promoted."""
    customer_model = apps.get_model("business_core", "BusinessCustomer")
    product_model = apps.get_model("business_core", "BusinessProduct")
    db_alias = schema_editor.connection.alias
    customer_model.objects.using(db_alias).exclude(data_contract="LEGACY").update(
        data_contract="LEGACY"
    )
    product_model.objects.using(db_alias).exclude(data_contract="LEGACY").update(
        data_contract="LEGACY"
    )


def preserve_contract_on_reverse(apps, schema_editor):
    """A reverse must not guess that historical rows satisfy MVP V1."""


def validate_master_preflight(apps, schema_editor):
    """Stop before constraints if any applicable row violates the V1 contract."""
    customer_model = apps.get_model("business_core", "BusinessCustomer")
    product_model = apps.get_model("business_core", "BusinessProduct")
    material_model = apps.get_model("business_core", "BusinessMaterial")
    db_alias = schema_editor.connection.alias
    customers = customer_model.objects.using(db_alias)
    products = product_model.objects.using(db_alias)
    materials = material_model.objects.using(db_alias)

    duplicate_customer_codes = (
        customers.exclude(customer_code__isnull=True)
        .values("customer_code")
        .annotate(row_count=Count("id"))
        .filter(row_count__gt=1)
        .count()
    )
    duplicate_part_codes = (
        products.exclude(part_code__isnull=True)
        .values("part_code")
        .annotate(row_count=Count("id"))
        .filter(row_count__gt=1)
        .count()
    )
    duplicate_material_codes = (
        materials.values("material_code")
        .annotate(row_count=Count("id"))
        .filter(row_count__gt=1)
        .count()
    )
    violations = {
        "blank_v1_company_names": customers.filter(
            data_contract="MVP_V1", company_name=""
        ).count(),
        "unknown_v1_customer_statuses": customers.filter(
            data_contract="MVP_V1"
        ).exclude(status__in=["ACTIVE", "INACTIVE"]).count(),
        "invalid_v1_customer_contacts": customers.filter(
            data_contract="MVP_V1", status="ACTIVE", email="", phone=""
        ).count(),
        "duplicate_customer_codes": duplicate_customer_codes,
        "duplicate_part_codes": duplicate_part_codes,
        "duplicate_material_codes": duplicate_material_codes,
        "invalid_v1_part_revision_or_unit": products.filter(
            data_contract="MVP_V1"
        ).filter(
            Q(revision__isnull=True)
            | Q(revision="")
            | Q(unit__isnull=True)
            | ~Q(unit__in=["PCS", "KG", "M", "MM"])
        ).count(),
        "missing_v1_customer_actor": customers.filter(
            data_contract="MVP_V1", created_by__isnull=True
        ).count(),
        "missing_v1_part_actor": products.filter(
            data_contract="MVP_V1", created_by__isnull=True
        ).count(),
        "missing_v1_material_actor": materials.filter(
            data_contract="MVP_V1", created_by__isnull=True
        ).count(),
    }
    if any(violations.values()):
        details = ", ".join(
            f"{name}={count}" for name, count in violations.items() if count
        )
        raise RuntimeError(f"BLOCKED_PHASE_3B_DATA_CONSTRAINT: {details}")


class Migration(migrations.Migration):
    dependencies = [("business_core", "0003_businessmaterial_businessnumbersequence_and_more")]

    operations = [
        migrations.RunPython(mark_existing_rows_legacy, preserve_contract_on_reverse),
        migrations.RunPython(validate_master_preflight, migrations.RunPython.noop),
    ]
