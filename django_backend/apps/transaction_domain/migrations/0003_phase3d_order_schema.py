# Generated for Phase 3D: additive order shadows and new empty evidence tables.

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("business_core", "0005_phase3b_master_constraints"),
        ("foundation", "0008_define_phase3c_permissions"),
        ("sales", "0005_phase3c_quotation_constraints"),
        ("transaction_domain", "0002_seed_transaction_domain_from_legacy"),
    ]

    operations = [
        migrations.AddField(
            model_name="transactionorder",
            name="data_contract",
            field=models.CharField(
                choices=[("LEGACY", "Legacy"), ("MVP_V1", "MVP V1")],
                db_index=True,
                default="LEGACY",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="source_quotation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="sales_orders",
                to="sales.salesquotation",
            ),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="source_rfq",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="sales_orders",
                to="sales.salesrfq",
            ),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="workflow_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("CONFIRMED", "Confirmed"),
                    ("IN_PROGRESS", "In progress"),
                    ("ON_HOLD", "On hold"),
                    ("COMPLETED", "Completed"),
                    ("CANCELLED", "Cancelled"),
                ],
                db_index=True,
                max_length=16,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="currency",
            field=models.CharField(
                blank=True,
                choices=[("VND", "Vietnamese dong"), ("USD", "US dollar")],
                max_length=3,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="subtotal",
            field=models.DecimalField(decimal_places=4, default=0, max_digits=20),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="discount_total",
            field=models.DecimalField(decimal_places=4, default=0, max_digits=20),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="tax_amount",
            field=models.DecimalField(decimal_places=4, default=0, max_digits=20),
        ),
        migrations.AlterField(
            model_name="transactionorder",
            name="total_amount",
            field=models.DecimalField(decimal_places=4, default=0, max_digits=20),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="customer_snapshot",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="quotation_snapshot",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="ordered_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="expected_delivery_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="progress_percent",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="hold_reason",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="cancel_reason",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="source_quotation_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="completed_at_v1",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="idempotency_key",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="request_hash",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="created_transaction_orders",
                to="foundation.foundationuser",
            ),
        ),
        migrations.AddField(
            model_name="transactionorder",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="updated_transaction_orders",
                to="foundation.foundationuser",
            ),
        ),
        migrations.AddField(
            model_name="transactionorderitem",
            name="data_contract",
            field=models.CharField(
                choices=[("LEGACY", "Legacy"), ("MVP_V1", "MVP V1")],
                db_index=True,
                default="LEGACY",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="transactionorderitem",
            name="line_number",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="transactionorderitem",
            name="source_quotation_line",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="order_lines",
                to="sales.salesquotationline",
            ),
        ),
        migrations.AddField(
            model_name="transactionorderitem",
            name="description_snapshot",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="transactionorderitem",
            name="part_code_snapshot",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="transactionorderitem",
            name="material_snapshot",
            field=models.CharField(blank=True, max_length=240),
        ),
        migrations.AlterField(
            model_name="transactionorderitem",
            name="quantity",
            field=models.DecimalField(decimal_places=4, default=1, max_digits=16),
        ),
        migrations.AddField(
            model_name="transactionorderitem",
            name="unit",
            field=models.CharField(
                blank=True,
                choices=[
                    ("PCS", "Pieces"),
                    ("KG", "Kilograms"),
                    ("M", "Metres"),
                    ("MM", "Millimetres"),
                ],
                max_length=8,
            ),
        ),
        migrations.AlterField(
            model_name="transactionorderitem",
            name="unit_price",
            field=models.DecimalField(decimal_places=4, default=0, max_digits=20),
        ),
        migrations.AlterField(
            model_name="transactionorderitem",
            name="line_total",
            field=models.DecimalField(decimal_places=4, default=0, max_digits=20),
        ),
        migrations.CreateModel(
            name="OrderProgressEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_status", models.CharField(blank=True, max_length=16)),
                ("to_status", models.CharField(
                    choices=[
                        ("CONFIRMED", "Confirmed"),
                        ("IN_PROGRESS", "In progress"),
                        ("ON_HOLD", "On hold"),
                        ("COMPLETED", "Completed"),
                        ("CANCELLED", "Cancelled"),
                    ],
                    max_length=16,
                )),
                ("progress_percent", models.PositiveSmallIntegerField()),
                ("milestone_note", models.CharField(blank=True, max_length=240)),
                ("reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="order_progress_events",
                    to="foundation.foundationuser",
                )),
                ("order", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="progress_events",
                    to="transaction_domain.transactionorder",
                )),
            ],
            options={
                "db_table": "transaction_order_progress_events",
                "ordering": ["order_id", "created_at", "id"],
            },
        ),
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("actor_ref", models.CharField(max_length=80)),
                ("actor_display", models.CharField(max_length=160)),
                ("action", models.CharField(max_length=120)),
                ("entity_type", models.CharField(max_length=80)),
                ("entity_id", models.CharField(max_length=80)),
                ("old_status", models.CharField(blank=True, max_length=24)),
                ("new_status", models.CharField(blank=True, max_length=24)),
                ("reason", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("correlation_id", models.UUIDField(db_index=True, default=uuid.uuid4)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor_user", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="audit_events",
                    to="foundation.foundationuser",
                )),
            ],
            options={
                "db_table": "transaction_audit_events",
                "ordering": ["entity_type", "entity_id", "created_at", "id"],
            },
        ),
        migrations.AddIndex(
            model_name="transactionorder",
            index=models.Index(fields=["source_rfq"], name="tx_order_source_rfq_idx"),
        ),
        migrations.AddIndex(
            model_name="transactionorder",
            index=models.Index(
                fields=["workflow_status", "expected_delivery_date"],
                name="tx_order_flow_date_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="transactionorder",
            index=models.Index(fields=["ordered_at"], name="tx_order_ordered_idx"),
        ),
        migrations.AddIndex(
            model_name="transactionorder",
            index=models.Index(fields=["created_by"], name="tx_order_creator_idx"),
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(
                fields=["entity_type", "entity_id", "created_at"],
                name="tx_audit_entity_time_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(fields=["action", "created_at"], name="tx_audit_action_time_idx"),
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(fields=["actor_ref", "created_at"], name="tx_audit_actor_time_idx"),
        ),
        migrations.AddIndex(
            model_name="orderprogressevent",
            index=models.Index(fields=["order", "created_at"], name="tx_progress_order_time_idx"),
        ),
        migrations.AddIndex(
            model_name="orderprogressevent",
            index=models.Index(fields=["to_status", "created_at"], name="tx_progress_status_time_idx"),
        ),
        migrations.AddIndex(
            model_name="orderprogressevent",
            index=models.Index(fields=["actor", "created_at"], name="tx_progress_actor_time_idx"),
        ),
    ]
