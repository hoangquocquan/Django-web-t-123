"""Explicit read-only tool registry for the structured AI agent."""

from __future__ import annotations

import platform
from dataclasses import asdict, dataclass

from django.apps import apps
from django.db.models import Count, Sum

from apps.ai.services.health_service import OllamaHealthService
from apps.business_core.models import BusinessCustomer, InventoryItem
from apps.crm.models import CrmCustomerProfile
from apps.knowledge.services.search_service import KnowledgeSearchService
from apps.sales.models import SalesLead, SalesOpportunity


@dataclass(frozen=True)
class ToolDefinition:
    """Security and validation contract for one callable agent tool."""

    name: str
    description: str
    input_schema: dict
    output_schema: dict
    required_permission: str
    risk_level: str = "low"
    read_only: bool = True
    timeout_seconds: float = 5.0
    allowed_modules: tuple[str, ...] = ("ai_agent",)
    audit_required: bool = True

    def to_dict(self):
        """Return serializable metadata for API/debug views."""
        data = asdict(self)
        data["allowed_modules"] = list(self.allowed_modules)
        return data


class BaseAgentTool:
    """Base contract for tools that cannot mutate business data."""

    definition = ToolDefinition(
        name="base",
        description="Base tool",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        output_schema={"type": "object"},
        required_permission="agent:read",
    )

    @property
    def name(self):
        return self.definition.name

    def run(self, arguments, user=None):
        """Execute one validated read-only operation."""
        raise NotImplementedError


class KnowledgeSearchTool(BaseAgentTool):
    """Search local RAG documents with document-level access checks."""

    definition = ToolDefinition(
        name="knowledge_search",
        description="Search approved company knowledge documents.",
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string", "minLength": 1}, "limit": {"type": "integer", "minimum": 1, "maximum": 5}},
            "required": ["query"],
            "additionalProperties": False,
        },
        output_schema={"type": "object", "required": ["sources", "confidence"]},
        required_permission="knowledge:read",
        timeout_seconds=10,
    )

    def run(self, arguments, user=None):
        result = KnowledgeSearchService().search(arguments["query"], limit=arguments.get("limit", 3), user=user)
        return {
            "confidence": result["confidence"],
            "sources": [
                {"id": source.get("id"), "title": source.get("title"), "relevance_score": source.get("relevance_score", 0)}
                for source in result["sources"]
            ],
        }


class CustomerSummaryTool(BaseAgentTool):
    """Return a non-sensitive customer and CRM activity summary."""

    definition = ToolDefinition(
        name="customer_summary",
        description="Summarize one customer without exposing contact secrets.",
        input_schema={
            "type": "object",
            "properties": {"customer_id": {"type": "integer", "minimum": 1}},
            "required": ["customer_id"],
            "additionalProperties": False,
        },
        output_schema={"type": "object", "required": ["id", "company_name", "status"]},
        required_permission="crm:read",
    )

    def run(self, arguments, user=None):
        customer = BusinessCustomer.objects.prefetch_related(
            "crm_interactions", "crm_notes", "crm_tasks", "sales_opportunities"
        ).get(id=arguments["customer_id"])
        profile = CrmCustomerProfile.objects.filter(customer=customer).first()
        return {
            "id": customer.id,
            "company_name": customer.company_name,
            "contact_name": customer.contact_name,
            "status": customer.status,
            "segment": profile.segment if profile else "",
            "lifecycle_stage": profile.lifecycle_stage if profile else "",
            "interaction_count": customer.crm_interactions.count(),
            "open_task_count": customer.crm_tasks.exclude(status="done").count(),
            "open_opportunity_count": customer.sales_opportunities.exclude(status__in=["won", "lost"]).count(),
        }


class LeadSummaryTool(BaseAgentTool):
    """Return one lead's deterministic pipeline state."""

    definition = ToolDefinition(
        name="lead_summary",
        description="Read a lead's current pipeline facts.",
        input_schema={
            "type": "object",
            "properties": {"lead_id": {"type": "integer", "minimum": 1}},
            "required": ["lead_id"],
            "additionalProperties": False,
        },
        output_schema={"type": "object", "required": ["id", "company", "status", "priority"]},
        required_permission="sales:read",
    )

    def run(self, arguments, user=None):
        lead = SalesLead.objects.get(id=arguments["lead_id"])
        return {
            "id": lead.id,
            "company": lead.company,
            "contact_person": lead.contact_person,
            "industry": lead.industry,
            "status": lead.status,
            "priority": lead.priority,
            "opportunity_count": lead.opportunities.count(),
            "follow_up_count": lead.follow_ups.exclude(status="done").count(),
        }


class SalesPipelineSummaryTool(BaseAgentTool):
    """Aggregate pipeline counts and values through Django ORM."""

    definition = ToolDefinition(
        name="sales_pipeline_summary",
        description="Return aggregate sales pipeline metrics.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        output_schema={"type": "object", "required": ["lead_status_counts", "open_pipeline_value"]},
        required_permission="sales:read",
    )

    def run(self, arguments, user=None):
        lead_counts = {row["status"]: row["count"] for row in SalesLead.objects.values("status").annotate(count=Count("id"))}
        open_value = SalesOpportunity.objects.exclude(status__in=["won", "lost"]).aggregate(total=Sum("value"))["total"] or 0
        return {
            "lead_status_counts": lead_counts,
            "open_opportunity_count": SalesOpportunity.objects.exclude(status__in=["won", "lost"]).count(),
            "open_pipeline_value": str(open_value),
        }


class InventorySummaryTool(BaseAgentTool):
    """Return aggregate inventory levels without stock updates."""

    definition = ToolDefinition(
        name="inventory_summary",
        description="Return read-only stock totals and reorder risk count.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        output_schema={"type": "object", "required": ["item_count", "total_quantity"]},
        required_permission="product:read",
    )

    def run(self, arguments, user=None):
        totals = InventoryItem.objects.aggregate(quantity=Sum("quantity"), reserved=Sum("reserved_quantity"))
        reorder_risk = sum(1 for item in InventoryItem.objects.only("quantity", "reserved_quantity", "reorder_point") if item.quantity - item.reserved_quantity <= item.reorder_point)
        return {
            "item_count": InventoryItem.objects.count(),
            "total_quantity": str(totals["quantity"] or 0),
            "reserved_quantity": str(totals["reserved"] or 0),
            "reorder_risk_count": reorder_risk,
        }


class SystemHealthTool(BaseAgentTool):
    """Return non-sensitive application and local Ollama health."""

    definition = ToolDefinition(
        name="system_health",
        description="Read Django and local Ollama readiness.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        output_schema={"type": "object", "required": ["django", "ollama"]},
        required_permission="developer:read",
        timeout_seconds=8,
    )

    def run(self, arguments, user=None):
        health = OllamaHealthService().check()
        return {"django": "ready", "ollama": health["status"], "model": health["model"], "model_available": health["model_available"]}


class DatabaseSummaryTool(BaseAgentTool):
    """Keep the existing safe aggregate-count tool for backward compatibility."""

    definition = ToolDefinition(
        name="database_summary",
        description="Return allow-listed Django model counts without raw SQL.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        output_schema={"type": "object"},
        required_permission="agent:write",
    )
    tracked_models = [("knowledge", "KnowledgeDocument"), ("ai_agent", "AgentRun"), ("foundation", "FoundationUser")]

    def run(self, arguments, user=None):
        return {f"{app_label}.{model_name}": apps.get_model(app_label, model_name).objects.count() for app_label, model_name in self.tracked_models}


class ReportGeneratorTool(BaseAgentTool):
    """Return a deterministic in-memory report skeleton; no file is written."""

    definition = ToolDefinition(
        name="report_generator",
        description="Compose an in-memory report heading from already provided context.",
        input_schema={
            "type": "object",
            "properties": {"title": {"type": "string", "minLength": 1}},
            "required": ["title"],
            "additionalProperties": False,
        },
        output_schema={"type": "object", "required": ["title", "format"]},
        required_permission="agent:write",
    )

    def run(self, arguments, user=None):
        return {"title": arguments["title"], "format": "json", "write_performed": False}


class SystemInformationTool(BaseAgentTool):
    """Keep existing non-sensitive runtime metadata for compatibility."""

    definition = ToolDefinition(
        name="system_information",
        description="Return non-sensitive local runtime information.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        output_schema={"type": "object", "required": ["python", "platform"]},
        required_permission="agent:write",
    )

    def run(self, arguments, user=None):
        return {"python": platform.python_version(), "platform": platform.system(), "machine": platform.machine()}


class ToolRegistry:
    """Allow-list registry; arbitrary functions, shell commands and SQL are impossible to register implicitly."""

    def __init__(self, tools=None):
        built_ins = tools or [
            KnowledgeSearchTool(), CustomerSummaryTool(), LeadSummaryTool(), SalesPipelineSummaryTool(),
            InventorySummaryTool(), SystemHealthTool(), DatabaseSummaryTool(), ReportGeneratorTool(), SystemInformationTool(),
        ]
        self._tools = {tool.name: tool for tool in built_ins}

    def register(self, tool):
        """Explicitly register a test or application tool with a complete definition."""
        if not isinstance(getattr(tool, "definition", None), ToolDefinition):
            raise TypeError("Agent tools require a ToolDefinition.")
        self._tools[tool.name] = tool

    def get(self, name):
        """Return one allow-listed tool or raise a descriptive lookup error."""
        if name not in self._tools:
            raise KeyError(f"Unknown agent tool: {name}")
        return self._tools[name]

    def list_tools(self):
        """Return complete metadata for security review and structured planning."""
        return [tool.definition.to_dict() for tool in self._tools.values()]
