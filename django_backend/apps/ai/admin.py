"""Django Admin chỉ đọc cho audit AI Governance V2."""

from django.contrib import admin

from apps.ai.models import AIGovernanceEvent, AIRequestLog


@admin.register(AIGovernanceEvent)
class AIGovernanceEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "decision", "module", "endpoint", "action", "user_email", "policy_version")
    list_filter = ("decision", "module", "policy_version", "request_source")
    search_fields = ("user_email", "endpoint", "action", "correlation_id", "matched_rule_ids")
    readonly_fields = [field.name for field in AIGovernanceEvent._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AIRequestLog)
class AIRequestLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "request_type", "status", "model_name", "user_email", "confidence")
    list_filter = ("request_type", "status", "provider")
    search_fields = ("user_email", "question_hash", "model_name")
    readonly_fields = [field.name for field in AIRequestLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
