"""Structured local Ollama planner with a deterministic read-only fallback."""

from __future__ import annotations

import json
import re

from django.conf import settings

from apps.ai.services.ollama_client import OllamaClient, OllamaClientError


class StructuredExecutionPlanner:
    """Create plans containing only registry tools and explicit arguments."""

    def __init__(self, client=None, attempts=1):
        self.client = client or OllamaClient(retries=0)
        self.attempts = max(1, int(attempts))

    def create_plan(self, request_text, registry):
        """Prefer real local planning and fall back without pretending Ollama succeeded."""
        if not getattr(settings, "AI_AGENT_OLLAMA_PLANNER_ENABLED", True):
            return {**self._fallback_plan(request_text), "generation_mode": "deterministic_fallback"}

        prompt = self._prompt(request_text, registry)
        for _attempt in range(self.attempts):
            try:
                response = self.client.generate_response(prompt, response_format="json")
                plan = json.loads(response.answer)
                if not isinstance(plan, dict):
                    raise ValueError("Planner response must be an object.")
                return {**plan, "generation_mode": "ollama", "planner_model": response.model}
            except (OllamaClientError, json.JSONDecodeError, ValueError):
                continue
        return {**self._fallback_plan(request_text), "generation_mode": "deterministic_fallback"}

    def plan(self, request_text):
        """Backward-compatible tool-name list used by older learning tests."""
        return [step["tool"] for step in self._fallback_plan(request_text)["steps"]]

    def _prompt(self, request_text, registry):
        tools = [
            {
                "name": item["name"],
                "description": item["description"],
                "input_schema": item["input_schema"],
                "read_only": item["read_only"],
            }
            for item in registry.list_tools()
        ]
        return (
            "Plan a read-only business information request. Return JSON only: "
            "{goal:string, steps:[{step:integer, tool:string, arguments:object, reason:string}], "
            "final_response_requirements:[string], requires_human_approval:false}. "
            "Use only listed tools. Never invent IDs. Do not plan shell, SQL, writes, email send, approval, deploy or delete. "
            f"Tools: {json.dumps(tools)} Request: {request_text}"
        )

    def _fallback_plan(self, request_text):
        """Build an auditable plan when local inference is disabled or unavailable."""
        text = str(request_text or "")
        folded = text.casefold()
        selected = []
        lead_id = self._extract_id(folded, "lead")
        customer_id = self._extract_id(folded, "customer")
        if lead_id:
            selected.append(("lead_summary", {"lead_id": lead_id}, "Read the requested lead."))
        if customer_id:
            selected.append(("customer_summary", {"customer_id": customer_id}, "Read the requested customer."))
        if any(word in folded for word in ["knowledge", "document", "catalog", "search", "product"]):
            selected.append(("knowledge_search", {"query": text, "limit": 3}, "Search approved knowledge."))
        if any(word in folded for word in ["sales", "pipeline", "opportunity"]):
            selected.append(("sales_pipeline_summary", {}, "Read aggregate sales pipeline facts."))
        if any(word in folded for word in ["inventory", "stock", "warehouse"]):
            selected.append(("inventory_summary", {}, "Read aggregate inventory facts."))
        if any(word in folded for word in ["database", "count", "how many"]):
            selected.append(("database_summary", {}, "Read allow-listed model counts."))
        if any(word in folded for word in ["system", "health", "runtime", "server"]):
            selected.extend([
                ("system_health", {}, "Read Django and Ollama health."),
                ("system_information", {}, "Read non-sensitive runtime metadata."),
            ])
        if any(word in folded for word in ["report", "summary", "monthly"]):
            selected.append(("report_generator", {"title": text[:120]}, "Prepare an in-memory report heading."))
        if not selected:
            selected.append(("knowledge_search", {"query": text, "limit": 3}, "Search approved knowledge."))

        deduplicated = []
        seen = set()
        for tool, arguments, reason in selected:
            key = (tool, json.dumps(arguments, sort_keys=True))
            if key not in seen:
                seen.add(key)
                deduplicated.append((tool, arguments, reason))
        return {
            "goal": text[:240],
            "steps": [
                {"step": index, "tool": tool, "arguments": arguments, "reason": reason}
                for index, (tool, arguments, reason) in enumerate(deduplicated, start=1)
            ],
            "final_response_requirements": ["Use only successful tool outputs", "Report tool failures explicitly"],
            "requires_human_approval": False,
        }

    def _extract_id(self, text, entity):
        match = re.search(rf"\b{entity}(?:\s+id)?\s*[:#]?\s*(\d+)\b", text)
        return int(match.group(1)) if match else None


ExecutionPlanner = StructuredExecutionPlanner
