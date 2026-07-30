from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("business_core", "0002_seed_business_core_from_legacy"),
        ("foundation", "0003_seed_ai_platform_permissions"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactRequest",
            fields=[
                ("id", models.IntegerField(primary_key=True, serialize=False)),
                ("name", models.TextField()),
                ("contact", models.TextField()),
                ("message", models.TextField(blank=True, null=True)),
                ("status", models.TextField(default="new")),
                ("created_at", models.TextField()),
                ("is_read", models.BooleanField(default=False)),
                ("note", models.TextField(blank=True, null=True)),
                ("company", models.TextField(blank=True, null=True)),
                ("phone", models.TextField(blank=True, null=True)),
                ("email", models.TextField(blank=True, null=True)),
                ("country", models.TextField(blank=True, null=True)),
                ("interested_product", models.TextField(blank=True, null=True)),
                ("attachment_url", models.TextField(blank=True, null=True)),
            ],
            options={"db_table": "contact_requests", "ordering": ["-created_at", "-id"], "managed": False},
        ),
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.IntegerField(primary_key=True, serialize=False)),
                ("company_name", models.TextField(blank=True, null=True)),
                ("contact_name", models.TextField()),
                ("email", models.TextField(blank=True, null=True)),
                ("phone", models.TextField(blank=True, null=True)),
                ("country", models.TextField(blank=True, default="Vietnam", null=True)),
                ("created_at", models.TextField()),
            ],
            options={"db_table": "customers", "ordering": ["-created_at", "-id"], "managed": False},
        ),
        migrations.CreateModel(
            name="CustomerNote",
            fields=[
                ("id", models.IntegerField(primary_key=True, serialize=False)),
                ("note", models.TextField()),
                ("created_by", models.TextField(blank=True, null=True)),
                ("created_at", models.TextField()),
                ("customer", models.ForeignKey(db_column="customer_id", on_delete=django.db.models.deletion.CASCADE, related_name="notes", to="crm.customer")),
            ],
            options={"db_table": "customer_notes", "ordering": ["-created_at", "-id"], "managed": False},
        ),
        migrations.CreateModel(
            name="CrmCustomerProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("segment", models.CharField(default="standard", max_length=80)),
                ("lifecycle_stage", models.CharField(default="lead", max_length=80)),
                ("preferred_contact_method", models.CharField(blank=True, max_length=80)),
                ("summary", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assigned_owner", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="crm_customer_profiles", to="foundation.foundationuser")),
                ("customer", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="crm_profile", to="business_core.businesscustomer")),
            ],
            options={"db_table": "crm_platform_customer_profiles", "ordering": ["customer_id"]},
        ),
        migrations.CreateModel(
            name="CrmInteraction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("interaction_type", models.CharField(default="note", max_length=80)),
                ("subject", models.CharField(max_length=220)),
                ("content", models.TextField(blank=True)),
                ("occurred_at", models.CharField(blank=True, max_length=40)),
                ("created_by", models.CharField(blank=True, max_length=160)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="crm_interactions", to="business_core.businesscustomer")),
            ],
            options={"db_table": "crm_platform_interactions", "ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="CrmNote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("note", models.TextField()),
                ("created_by", models.CharField(blank=True, max_length=160)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="crm_notes", to="business_core.businesscustomer")),
            ],
            options={"db_table": "crm_platform_notes", "ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="CrmTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=220)),
                ("due_date", models.CharField(blank=True, max_length=40)),
                ("status", models.CharField(default="open", max_length=40)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="crm_tasks", to="business_core.businesscustomer")),
                ("owner", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="crm_tasks", to="foundation.foundationuser")),
            ],
            options={"db_table": "crm_platform_tasks", "ordering": ["status", "due_date", "-id"]},
        ),
        migrations.CreateModel(
            name="CrmTimelineEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(max_length=80)),
                ("title", models.CharField(max_length=220)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="crm_timeline_events", to="business_core.businesscustomer")),
            ],
            options={"db_table": "crm_platform_timeline_events", "ordering": ["-created_at", "-id"]},
        ),
        migrations.AddIndex(model_name="crmcustomerprofile", index=models.Index(fields=["segment"], name="crm_profile_segment_idx")),
        migrations.AddIndex(model_name="crmcustomerprofile", index=models.Index(fields=["lifecycle_stage"], name="crm_profile_stage_idx")),
        migrations.AddIndex(model_name="crminteraction", index=models.Index(fields=["interaction_type"], name="crm_interaction_type_idx")),
        migrations.AddIndex(model_name="crmtimelineevent", index=models.Index(fields=["event_type"], name="crm_timeline_type_idx")),
    ]
