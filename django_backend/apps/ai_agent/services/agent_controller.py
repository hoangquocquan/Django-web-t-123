"""Local AI agent controller and execution planner."""

from __future__ import annotations

from django.db import transaction

from apps.ai_agent.models import AgentRun
from apps.ai_agent.services.tools import ToolRegistry


class ExecutionPlanner:
    """Choose safe local tools for one user request."""

    def plan(self, request_text):
        """Return tool names based on request intent keywords."""
        text = str(request_text or "").lower()
        tools = []
        if any(keyword in text for keyword in ["knowledge", "document", "catalog", "search", "product"]):
            tools.append("knowledge_search")
        if any(keyword in text for keyword in ["database", "count", "how many", "report", "sales"]):
            tools.append("database_summary")
        if any(keyword in text for keyword in ["system", "health", "runtime", "server"]):
            tools.append("system_information")
        if any(keyword in text for keyword in ["report", "summary", "monthly", "sales"]):
            tools.append("report_generator")
        return tools or ["knowledge_search"]


class MemoryManager:
    """Prepare short-lived execution memory for one agent run."""

    def create_memory(self, request_text, tools):
        """Return memory that is not reused across requests."""
        return {
            "request_preview": str(request_text or "")[:120],
            "planned_tools": tools,
        }


class AgentController:
    """Execute an AI agent run with local tools only."""

    def __init__(self, planner=None, registry=None, memory_manager=None):
        """Allow tests to inject agent collaborators."""
        self.planner = planner or ExecutionPlanner()
        self.registry = registry or ToolRegistry()
        self.memory_manager = memory_manager or MemoryManager()

    @transaction.atomic
    def run(self, request_text, user=None):
        """Plan, execute tools, and persist an audited agent run."""
        planned_tools = self.planner.plan(request_text)
        memory = self.memory_manager.create_memory(request_text, planned_tools)
        tool_results = []
        for tool_name in planned_tools:
            tool = self.registry.get(tool_name)
            tool_results.append(
                {
                    "tool": tool_name,
                    "output": tool.run(request_text),
                }
            )

        result = {
            "steps": [
                "understand_request",
                "select_tools",
                "execute_tools",
                "generate_response",
            ],
            "memory": memory,
            "tool_results": tool_results,
            "answer": self._compose_answer(request_text, tool_results),
        }
        run = AgentRun.objects.create(
            request_text=request_text,
            selected_tools=planned_tools,
            result=result,
            created_by_email=getattr(user, "email", "") or "",
        )
        result["run_id"] = run.id
        return result

    def _compose_answer(self, request_text, tool_results):
        """Create a deterministic response from tool outputs."""
        tool_names = ", ".join(item["tool"] for item in tool_results)
        return f"Agent processed the request using: {tool_names}. Request: {request_text}"

