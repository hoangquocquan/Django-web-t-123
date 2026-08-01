"""Validated read-only AI agent execution controller."""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from django.conf import settings

from apps.ai.services.normalization_service import AIInputNormalizer
from apps.ai.services.redaction_service import AIRedactionService
from apps.ai_agent.models import AgentRun, AgentToolAudit
from apps.ai_agent.services.schema_validator import SchemaValidationError, StrictSchemaValidator
from apps.ai_agent.services.structured_planner import ExecutionPlanner, StructuredExecutionPlanner
from apps.ai_agent.services.tools import ToolRegistry
from apps.foundation.services import FoundationPermissionService


class AgentControlError(ValueError):
    """Base error for plans that must not execute."""

    code = "agent_blocked"


class AgentPlanValidationError(AgentControlError):
    """Raised when a structured plan or tool contract is invalid."""

    code = "invalid_agent_plan"


class AgentPermissionError(AgentControlError):
    """Raised when the current user lacks a tool-specific permission."""

    code = "agent_tool_permission_denied"


class AgentToolTimeoutError(AgentControlError):
    """Raised internally when a read-only tool exceeds its deadline."""

    code = "agent_tool_timeout"


class MemoryManager:
    """Create bounded, redacted, request-scoped execution memory."""

    def __init__(self, redactor=None):
        self.redactor = redactor or AIRedactionService()

    def create_memory(self, request_text, plan):
        """Never carry memory across users or agent runs."""
        preview, _summary = self.redactor.redact_text(str(request_text or "")[:240])
        return {
            "request_preview": preview,
            "planned_tools": [step["tool"] for step in plan["steps"]],
            "scope": "request_only",
        }


class PlanValidator:
    """Enforce plan schema, tool allow-list, permissions and execution limits."""

    DANGEROUS_REQUEST_PATTERNS = (
        r"\b(?:run|execute|open)\s+(?:a\s+)?(?:shell|powershell|cmd|bash)\b",
        r"\b(?:select|insert|update|delete|drop|alter)\s+.*\b(?:from|into|table|database)\b",
        r"\b(?:send|dispatch)\s+(?:the\s+)?email\b",
        r"\bapprove\s+(?:the\s+)?quotation\b",
        r"\bdeploy\s+(?:to\s+)?(?:staging|production)\b",
        r"\bdelete\s+(?:the\s+)?(?:file|customer|lead|order|database)\b",
    )
    PLAN_SCHEMA = {
        "type": "object",
        "properties": {
            "goal": {"type": "string", "minLength": 1},
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "step": {"type": "integer", "minimum": 1},
                        "tool": {"type": "string", "minLength": 1},
                        "arguments": {"type": "object"},
                        "reason": {"type": "string", "minLength": 1},
                    },
                    "required": ["step", "tool", "arguments", "reason"],
                    "additionalProperties": False,
                },
            },
            "final_response_requirements": {"type": "array", "items": {"type": "string"}},
            "requires_human_approval": {"type": "boolean"},
            "generation_mode": {"type": "string"},
            "planner_model": {"type": "string"},
        },
        "required": ["goal", "steps", "final_response_requirements", "requires_human_approval"],
        "additionalProperties": False,
    }

    def __init__(self, registry, schema_validator=None, permission_service=None):
        self.registry = registry
        self.schema_validator = schema_validator or StrictSchemaValidator()
        self.permission_service = permission_service or FoundationPermissionService()

    def validate(self, request_text, plan, user=None):
        """Return a safe plan or raise before any tool is called."""
        normalized = AIInputNormalizer().normalize(request_text).scan_text
        if any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in self.DANGEROUS_REQUEST_PATTERNS):
            raise AgentPlanValidationError("Request requires a prohibited write or system capability.")
        try:
            self.schema_validator.validate(plan, self.PLAN_SCHEMA)
        except SchemaValidationError as exc:
            raise AgentPlanValidationError(str(exc)) from exc

        max_steps = int(getattr(settings, "AI_AGENT_MAX_STEPS", 5))
        if not plan["steps"]:
            raise AgentPlanValidationError("Agent plan must contain at least one step.")
        if len(plan["steps"]) > max_steps:
            raise AgentPlanValidationError(f"Agent plan exceeds max steps ({max_steps}).")
        if plan["requires_human_approval"] is not False:
            raise AgentPlanValidationError("This read-only controller cannot execute approval-required plans.")

        seen = set()
        for expected_step, step in enumerate(plan["steps"], start=1):
            if step["step"] != expected_step:
                raise AgentPlanValidationError("Agent step numbers must be sequential.")
            try:
                tool = self.registry.get(step["tool"])
            except KeyError as exc:
                raise AgentPlanValidationError(str(exc)) from exc
            definition = tool.definition
            if not definition.read_only or "ai_agent" not in definition.allowed_modules:
                raise AgentPlanValidationError(f"Tool is not approved for read-only agent use: {step['tool']}.")
            permission_module, permission_action = definition.required_permission.split(":", 1)
            if not self.permission_service.has_permission(user, permission_module, permission_action):
                raise AgentPermissionError(f"Missing permission: {definition.required_permission}")
            try:
                self.schema_validator.validate(step["arguments"], definition.input_schema)
            except SchemaValidationError as exc:
                raise AgentPlanValidationError(f"Invalid arguments for {step['tool']}: {exc}") from exc
            call_key = (step["tool"], json.dumps(step["arguments"], sort_keys=True, default=str))
            if call_key in seen:
                raise AgentPlanValidationError("Duplicate tool calls are blocked to prevent loops.")
            seen.add(call_key)
        return plan


class AgentController:
    """Plan, validate, execute and audit allow-listed read-only tools."""

    def __init__(self, planner=None, registry=None, memory_manager=None, plan_validator=None, redactor=None):
        self.planner = planner or StructuredExecutionPlanner()
        self.registry = registry or ToolRegistry()
        self.memory_manager = memory_manager or MemoryManager()
        self.plan_validator = plan_validator or PlanValidator(self.registry)
        self.redactor = redactor or AIRedactionService()

    def run(self, request_text, user=None):
        """Execute a bounded request and persist lifecycle plus per-tool evidence."""
        request_text = str(request_text or "")
        max_context = int(getattr(settings, "AI_AGENT_MAX_CONTEXT_CHARS", 12000))
        if not request_text.strip() or len(request_text) > max_context:
            raise AgentPlanValidationError("Agent request is empty or exceeds the context limit.")

        correlation_id = str(uuid.uuid4())
        request_hash = hashlib.sha256(request_text.encode("utf-8")).hexdigest()
        request_preview, _redaction = self.redactor.redact_text(request_text[:500])
        run = AgentRun.objects.create(
            request_text=request_preview,
            request_hash=request_hash,
            correlation_id=correlation_id,
            status="PLANNED",
            state_history=["PLANNED"],
            created_by_email=getattr(user, "email", "") or "",
        )

        try:
            plan = self.planner.create_plan(request_text, self.registry)
            self._transition(run, "VALIDATING")
            self.plan_validator.validate(request_text, plan, user=user)
        except AgentControlError as exc:
            self._finish_blocked(run, exc)
            raise

        memory = self.memory_manager.create_memory(request_text, plan)
        run.selected_tools = [step["tool"] for step in plan["steps"]]
        run.save(update_fields=["selected_tools"])
        self._transition(run, "EXECUTING")
        total_started = time.perf_counter()
        total_timeout = float(getattr(settings, "AI_AGENT_TOTAL_TIMEOUT_SECONDS", 20))
        tool_results = []
        for step in plan["steps"]:
            if time.perf_counter() - total_started >= total_timeout:
                tool_results.append(self._record_skipped_timeout(run, step, user, correlation_id))
                self._transition(run, "TOOL_FAILED")
                break
            result = self._execute_step(run, step, user, correlation_id)
            tool_results.append(result)
            if result["status"] != "SUCCESS":
                self._transition(run, "TOOL_FAILED")

        self._transition(run, "SYNTHESIZING")
        result = {
            "correlation_id": correlation_id,
            "plan": plan,
            "steps": run.state_history,
            "memory": memory,
            "tool_results": tool_results,
            "answer": self._compose_grounded_answer(tool_results),
            "partial_failure": any(item["status"] != "SUCCESS" for item in tool_results),
            "human_approval_required": False,
            "autonomous_action": False,
        }
        final_status = "COMPLETED" if any(item["status"] == "SUCCESS" for item in tool_results) else "FAILED"
        self._transition(run, final_status)
        result["steps"] = run.state_history
        run.result = result
        run.save(update_fields=["result"])
        result["run_id"] = run.id
        return result

    def _execute_step(self, run, step, user, correlation_id):
        tool = self.registry.get(step["tool"])
        started = time.perf_counter()
        status = "SUCCESS"
        error = ""
        output = None
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"agent-{tool.name}")
        future = executor.submit(tool.run, step["arguments"], user)
        try:
            output = future.result(timeout=tool.definition.timeout_seconds)
            StrictSchemaValidator().validate(output, tool.definition.output_schema)
        except FutureTimeoutError:
            future.cancel()
            status = "TIMEOUT"
            error = f"Tool exceeded {tool.definition.timeout_seconds} seconds."
        except Exception as exc:  # Tool errors are isolated and reported without fabricating output.
            status = "ERROR"
            error = f"{exc.__class__.__name__}: {str(exc)[:300]}"
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        latency_ms = int((time.perf_counter() - started) * 1000)
        safe_output, _summary = self.redactor.redact_value(output if output is not None else {})
        output_summary = self._bounded_output(safe_output)
        AgentToolAudit.objects.create(
            run=run,
            correlation_id=correlation_id,
            user_email=getattr(user, "email", "") or "",
            tool_name=tool.name,
            required_permission=tool.definition.required_permission,
            input_hash=hashlib.sha256(json.dumps(step["arguments"], sort_keys=True, default=str).encode("utf-8")).hexdigest(),
            output_summary=output_summary,
            latency_ms=latency_ms,
            status=status,
            error=error,
            policy_decision="ALLOW_READ_ONLY",
        )
        return {"step": step["step"], "tool": tool.name, "status": status, "output": output_summary, "error": error, "latency_ms": latency_ms}

    def _record_skipped_timeout(self, run, step, user, correlation_id):
        tool = self.registry.get(step["tool"])
        error = "Total agent timeout reached before tool execution."
        AgentToolAudit.objects.create(
            run=run,
            correlation_id=correlation_id,
            user_email=getattr(user, "email", "") or "",
            tool_name=tool.name,
            required_permission=tool.definition.required_permission,
            input_hash=hashlib.sha256(json.dumps(step["arguments"], sort_keys=True).encode("utf-8")).hexdigest(),
            status="TIMEOUT",
            error=error,
            policy_decision="BLOCK_TOTAL_TIMEOUT",
        )
        return {"step": step["step"], "tool": tool.name, "status": "TIMEOUT", "output": {}, "error": error, "latency_ms": 0}

    def _compose_grounded_answer(self, tool_results):
        """Use successful tool output verbatim and state failures without inference."""
        sections = []
        for item in tool_results:
            if item["status"] == "SUCCESS":
                sections.append(f"{item['tool']}: {json.dumps(item['output'], ensure_ascii=False, default=str)}")
            else:
                sections.append(f"{item['tool']}: unavailable ({item['status']}: {item['error']})")
        return "\n".join(sections)

    def _bounded_output(self, output):
        rendered = json.dumps(output, ensure_ascii=False, default=str)
        max_chars = int(getattr(settings, "AI_AGENT_MAX_TOOL_OUTPUT_CHARS", 4000))
        if len(rendered) <= max_chars:
            return output
        return {"truncated": True, "preview": rendered[:max_chars]}

    def _transition(self, run, state):
        history = list(run.state_history)
        if not history or history[-1] != state:
            history.append(state)
        run.status = state
        run.state_history = history
        run.save(update_fields=["status", "state_history"])

    def _finish_blocked(self, run, exc):
        self._transition(run, "BLOCKED")
        run.result = {"error": {"code": exc.code, "message": str(exc)}, "autonomous_action": False}
        run.save(update_fields=["result"])
