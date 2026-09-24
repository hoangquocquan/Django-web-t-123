"""Read-only unmanaged ORM models for legacy CRM tables."""

from django.db import models

from apps.common.models import LegacyReadOnlyModel


class Customer(LegacyReadOnlyModel):
    """Khách hàng hoặc công ty đã gửi thông tin cho MecPrecision."""

    id = models.IntegerField(primary_key=True)
    company_name = models.TextField(blank=True, null=True)
    contact_name = models.TextField()
    email = models.TextField(blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    country = models.TextField(default="Vietnam", blank=True, null=True)
    created_at = models.TextField()

    class Meta:
        managed = False
        db_table = "customers"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.company_name or self.contact_name


class CustomerNote(LegacyReadOnlyModel):
    """Ghi chú chăm sóc khách hàng trong CRM legacy."""

    id = models.IntegerField(primary_key=True)
    customer = models.ForeignKey(
        Customer,
        db_column="customer_id",
        on_delete=models.CASCADE,
        related_name="notes",
    )
    note = models.TextField()
    created_by = models.TextField(blank=True, null=True)
    created_at = models.TextField()

    class Meta:
        managed = False
        db_table = "customer_notes"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.note


class ContactRequest(LegacyReadOnlyModel):
    """Form liên hệ public được lưu trong database legacy."""

    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    contact = models.TextField()
    message = models.TextField(blank=True, null=True)
    status = models.TextField(default="new")
    created_at = models.TextField()
    is_read = models.BooleanField(default=False)
    note = models.TextField(blank=True, null=True)
    company = models.TextField(blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    interested_product = models.TextField(blank=True, null=True)
    attachment_url = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "contact_requests"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.name} - {self.status}"


class CrmCustomerProfile(models.Model):
    """Django-owned CRM extension for a business customer."""

    customer = models.OneToOneField(
        "business_core.BusinessCustomer",
        on_delete=models.CASCADE,
        related_name="crm_profile",
    )
    segment = models.CharField(max_length=80, default="standard")
    lifecycle_stage = models.CharField(max_length=80, default="lead")
    preferred_contact_method = models.CharField(max_length=80, blank=True)
    assigned_owner = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.SET_NULL,
        related_name="crm_customer_profiles",
        blank=True,
        null=True,
    )
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "crm_platform_customer_profiles"
        ordering = ["customer_id"]
        indexes = [
            models.Index(fields=["segment"], name="crm_profile_segment_idx"),
            models.Index(fields=["lifecycle_stage"], name="crm_profile_stage_idx"),
        ]

    def __str__(self):
        """Return the linked business customer display name."""
        return str(self.customer)


class CrmInteraction(models.Model):
    """Django-owned customer interaction history."""

    customer = models.ForeignKey(
        "business_core.BusinessCustomer",
        on_delete=models.CASCADE,
        related_name="crm_interactions",
    )
    interaction_type = models.CharField(max_length=80, default="note")
    subject = models.CharField(max_length=220)
    content = models.TextField(blank=True)
    occurred_at = models.CharField(max_length=40, blank=True)
    created_by = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "crm_platform_interactions"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["interaction_type"], name="crm_interaction_type_idx"),
        ]


class CrmNote(models.Model):
    """Django-owned sales or service note for a customer."""

    customer = models.ForeignKey("business_core.BusinessCustomer", on_delete=models.CASCADE, related_name="crm_notes")
    note = models.TextField()
    created_by = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "crm_platform_notes"
        ordering = ["-created_at", "-id"]


class CrmTask(models.Model):
    """Django-owned customer task for CRM follow-up."""

    customer = models.ForeignKey("business_core.BusinessCustomer", on_delete=models.CASCADE, related_name="crm_tasks")
    title = models.CharField(max_length=220)
    due_date = models.CharField(max_length=40, blank=True)
    status = models.CharField(max_length=40, default="open")
    owner = models.ForeignKey(
        "foundation.FoundationUser",
        on_delete=models.SET_NULL,
        related_name="crm_tasks",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "crm_platform_tasks"
        ordering = ["status", "due_date", "-id"]


class CrmTimelineEvent(models.Model):
    """Unified CRM timeline event for customer history."""

    customer = models.ForeignKey(
        "business_core.BusinessCustomer",
        on_delete=models.CASCADE,
        related_name="crm_timeline_events",
    )
    event_type = models.CharField(max_length=80)
    title = models.CharField(max_length=220)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "crm_platform_timeline_events"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["event_type"], name="crm_timeline_type_idx"),
        ]
