"""Add nullable/default-safe Phase 3C quotation schema without V1 constraints."""

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("business_core", "0005_phase3b_master_constraints"),
        ("foundation", "0008_define_phase3c_permissions"),
        ("sales", "0002_salesrfq_salesrfqline_salesrfqdocument_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SalesQuotationApprovalDecision",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("decision", models.CharField(choices=[("APPROVED", "Approved"), ("REJECTED", "Rejected")], max_length=16)),
                ("reason", models.TextField(blank=True)),
                ("notes", models.TextField(blank=True)),
                ("decided_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("quotation", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="approval_decisions", to="sales.salesquotation")),
                ("reviewer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="quotation_approval_decisions", to="foundation.foundationuser")),
            ],
            options={
                "db_table": "sales_quotation_approval_decisions",
                "ordering": ["quotation_id", "decided_at", "id"],
            },
        ),
        migrations.CreateModel(
            name="SalesQuotationCustomerDecision",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("decision", models.CharField(choices=[("ACCEPTED", "Accepted"), ("DECLINED", "Declined")], max_length=16)),
                ("contact_snapshot", models.CharField(max_length=254)),
                ("evidence", models.TextField()),
                ("reason", models.TextField(blank=True)),
                ("decided_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("quotation", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="customer_decisions", to="sales.salesquotation")),
                ("recorded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="recorded_customer_decisions", to="foundation.foundationuser")),
            ],
            options={
                "db_table": "sales_quotation_customer_decisions",
                "ordering": ["quotation_id", "decided_at", "id"],
            },
        ),
        migrations.AlterModelOptions(
            name="salesquotationline",
            options={"ordering": ["quotation_id", "line_number", "id"]},
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="currency",
            field=models.CharField(blank=True, choices=[("VND", "Vietnamese dong"), ("USD", "US dollar")], max_length=3, null=True),
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="customer_snapshot",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="data_contract",
            field=models.CharField(choices=[("LEGACY", "Legacy"), ("MVP_V1", "MVP V1")], db_index=True, default="LEGACY", max_length=16),
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="idempotency_key",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="request_hash",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="revision",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="rfq",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="quotations", to="sales.salesrfq"),
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="rfq_snapshot",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="sent_evidence",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="sent_to",
            field=models.CharField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="tax_amount",
            field=models.DecimalField(decimal_places=4, default=0, max_digits=20),
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="terms",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="updated_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="updated_sales_quotations", to="foundation.foundationuser"),
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="valid_from",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="valid_until",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="salesquotation",
            name="workflow_status",
            field=models.CharField(blank=True, choices=[("DRAFT", "Draft"), ("PENDING_APPROVAL", "Pending approval"), ("APPROVED", "Approved"), ("REJECTED", "Rejected"), ("SENT", "Sent"), ("ACCEPTED", "Accepted"), ("DECLINED", "Declined"), ("EXPIRED", "Expired"), ("SUPERSEDED", "Superseded")], db_index=True, max_length=24, null=True),
        ),
        migrations.AddField(
            model_name="salesquotationline",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="salesquotationline",
            name="data_contract",
            field=models.CharField(choices=[("LEGACY", "Legacy"), ("MVP_V1", "MVP V1")], db_index=True, default="LEGACY", max_length=16),
        ),
        migrations.AddField(
            model_name="salesquotationline",
            name="line_number",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="salesquotationline",
            name="line_subtotal",
            field=models.DecimalField(decimal_places=4, default=0, max_digits=20),
        ),
        migrations.AddField(
            model_name="salesquotationline",
            name="material_snapshot",
            field=models.CharField(blank=True, max_length=240),
        ),
        migrations.AddField(
            model_name="salesquotationline",
            name="part_code_snapshot",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="salesquotationline",
            name="source_rfq_line",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="quotation_lines", to="sales.salesrfqline"),
        ),
        migrations.AddField(
            model_name="salesquotationline",
            name="unit",
            field=models.CharField(blank=True, choices=[("PCS", "Pieces"), ("KG", "Kilograms"), ("M", "Metres"), ("MM", "Millimetres")], max_length=8),
        ),
        migrations.AlterField(
            model_name="salesquotation",
            name="discount_total",
            field=models.DecimalField(decimal_places=4, default=0, max_digits=20),
        ),
        migrations.AlterField(
            model_name="salesquotation",
            name="subtotal",
            field=models.DecimalField(decimal_places=4, default=0, max_digits=20),
        ),
        migrations.AlterField(
            model_name="salesquotation",
            name="total",
            field=models.DecimalField(decimal_places=4, default=0, max_digits=20),
        ),
        migrations.AlterField(
            model_name="salesquotationline",
            name="discount",
            field=models.DecimalField(decimal_places=4, default=0, max_digits=20),
        ),
        migrations.AlterField(
            model_name="salesquotationline",
            name="line_total",
            field=models.DecimalField(decimal_places=4, default=0, max_digits=20),
        ),
        migrations.AlterField(
            model_name="salesquotationline",
            name="quantity",
            field=models.DecimalField(decimal_places=4, default=1, max_digits=16),
        ),
        migrations.AlterField(
            model_name="salesquotationline",
            name="unit_price",
            field=models.DecimalField(decimal_places=4, default=0, max_digits=20),
        ),
        migrations.AddIndex(
            model_name="salesquotation",
            index=models.Index(fields=["rfq", "revision"], name="sales_quote_rfq_rev_idx"),
        ),
        migrations.AddIndex(
            model_name="salesquotation",
            index=models.Index(fields=["workflow_status", "valid_until"], name="sales_quote_flow_valid_idx"),
        ),
        migrations.AddIndex(
            model_name="salesquotation",
            index=models.Index(fields=["created_by"], name="sales_quote_creator_idx"),
        ),
    ]
