"""Local tools that an AI agent can execute safely."""

from __future__ import annotations

import platform

from django.apps import apps

from apps.knowledge.services.knowledge_service import KnowledgeService, search_result_to_dict


class BaseAgentTool:
    """Base class for agent tools."""

    name = "base"
    description = "Base tool"

    def run(self, request_text):
        """Execute the tool for a request."""
        raise NotImplementedError


class KnowledgeSearchTool(BaseAgentTool):
    """Search local RAG documents."""

    name = "knowledge_search"
    description = "Search company knowledge documents."

    def run(self, request_text):
        """Return the top local knowledge matches."""
        results = KnowledgeService().search(request_text, limit=3)
        return [search_result_to_dict(result) for result in results]


class DatabaseSummaryTool(BaseAgentTool):
    """Return safe aggregate counts from selected Django-owned models."""

    name = "database_summary"
    description = "Return high-level database counts without raw SQL."

    tracked_models = [
        ("knowledge", "KnowledgeDocument"),
        ("knowledge", "KnowledgeChunk"),
        ("ai_agent", "AgentRun"),
        ("foundation", "FoundationUser"),
    ]

    def run(self, request_text):
        """Return model counts using Django ORM only."""
        counts = {}
        for app_label, model_name in self.tracked_models:
            model = apps.get_model(app_label, model_name)
            counts[f"{app_label}.{model_name}"] = model.objects.count()
        return counts


class ReportGeneratorTool(BaseAgentTool):
    """Build a compact report from the request and collected tool results."""

    name = "report_generator"
    description = "Generate a readable local report."

    def run(self, request_text):
        """Return a simple report skeleton."""
        return {
            "title": "AI Agent Report",
            "summary": f"Generated local report for: {request_text}",
            "format": "json",
        }


class SystemInformationTool(BaseAgentTool):
    """Return non-sensitive runtime information."""

    name = "system_information"
    description = "Return local system information useful for operations."

    def run(self, request_text):
        """Return safe system metadata."""
        return {
            "python": platform.python_version(),
            "platform": platform.system(),
            "machine": platform.machine(),
        }


class ToolRegistry:
    """Registry for agent tools."""

    def __init__(self):
        """Register built-in local tools."""
        self._tools = {
            tool.name: tool
            for tool in [
                KnowledgeSearchTool(),
                DatabaseSummaryTool(),
                ReportGeneratorTool(),
                SystemInformationTool(),
            ]
        }

    def get(self, name):
        """Return one registered tool by name."""
        return self._tools[name]

    def list_tools(self):
        """Return metadata for all registered tools."""
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self._tools.values()
        ]

