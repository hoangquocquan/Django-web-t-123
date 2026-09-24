"""Apply named Phase 3B master-data constraints after legacy normalization."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("business_core", "0004_mark_existing_master_rows_legacy")]

    operations = [
        migrations.AddConstraint(
            model_name="businesscustomer",
            constraint=models.UniqueConstraint(
                condition=models.Q(customer_code__isnull=False),
                fields=("customer_code",),
                name="uq_customer_code_nonnull",
            ),
        ),
        migrations.AddConstraint(
            model_name="businesscustomer",
            constraint=models.CheckConstraint(
                condition=(~models.Q(data_contract="MVP_V1") | models.Q(status__in=["ACTIVE", "INACTIVE"])),
                name="ck_customer_v1_status",
            ),
        ),
        migrations.AddConstraint(
            model_name="businesscustomer",
            constraint=models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | (
                        models.Q(customer_code__isnull=False)
                        & ~models.Q(customer_code="")
                        & ~models.Q(company_name="")
                        & models.Q(created_by__isnull=False)
                    )
                ),
                name="ck_customer_v1_required",
            ),
        ),
        migrations.AddConstraint(
            model_name="businesscustomer",
            constraint=models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1", status="ACTIVE")
                    | ~models.Q(email="")
                    | ~models.Q(phone="")
                ),
                name="ck_customer_v1_contact",
            ),
        ),
        migrations.AddConstraint(
            model_name="businessproduct",
            constraint=models.UniqueConstraint(
                condition=models.Q(part_code__isnull=False),
                fields=("part_code",),
                name="uq_part_code_nonnull",
            ),
        ),
        migrations.AddConstraint(
            model_name="businessproduct",
            constraint=models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | (
                        models.Q(part_code__isnull=False)
                        & ~models.Q(part_code="")
                        & models.Q(revision__isnull=False)
                        & ~models.Q(revision="")
                        & models.Q(unit__isnull=False)
                        & ~models.Q(name="")
                        & models.Q(created_by__isnull=False)
                    )
                ),
                name="ck_part_v1_required",
            ),
        ),
        migrations.AddConstraint(
            model_name="businessproduct",
            constraint=models.CheckConstraint(
                condition=(~models.Q(data_contract="MVP_V1") | models.Q(unit__in=["PCS", "KG", "M", "MM"])),
                name="ck_part_v1_unit",
            ),
        ),
        migrations.AddConstraint(
            model_name="businessnumbersequence",
            constraint=models.UniqueConstraint(
                fields=("namespace", "period"),
                name="uq_numseq_namespace_period",
            ),
        ),
        migrations.AddConstraint(
            model_name="businessnumbersequence",
            constraint=models.CheckConstraint(
                condition=models.Q(namespace__in=["CUS", "PART", "MAT", "RFQ", "QT", "SO"]),
                name="ck_numseq_namespace",
            ),
        ),
        migrations.AddConstraint(
            model_name="businessnumbersequence",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(namespace__in=["CUS", "PART", "MAT"], period="GLOBAL")
                    | models.Q(namespace__in=["RFQ", "QT", "SO"], period__regex=r"^[0-9]{4}$")
                ),
                name="ck_numseq_period",
            ),
        ),
        migrations.AddConstraint(
            model_name="businessnumbersequence",
            constraint=models.CheckConstraint(
                condition=models.Q(last_value__gte=0),
                name="ck_numseq_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="businessmaterial",
            constraint=models.UniqueConstraint(fields=("material_code",), name="uq_material_code"),
        ),
        migrations.AddConstraint(
            model_name="businessmaterial",
            constraint=models.UniqueConstraint(
                condition=models.Q(legacy_material_id__isnull=False),
                fields=("legacy_material_id",),
                name="uq_material_legacy_id",
            ),
        ),
        migrations.AddConstraint(
            model_name="businessmaterial",
            constraint=models.CheckConstraint(
                condition=(
                    ~models.Q(data_contract="MVP_V1")
                    | (
                        ~models.Q(material_code="")
                        & ~models.Q(name="")
                        & models.Q(created_by__isnull=False)
                    )
                ),
                name="ck_material_v1_required",
            ),
        ),
    ]
