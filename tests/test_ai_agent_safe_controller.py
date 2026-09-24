import time

import pytest
from django.test import override_settings

from apps.ai_agent.models import AgentRun, AgentToolAudit
from apps.ai_agent.services.agent_controller import (
    AgentPermissionError,
    AgentPlanValidationError,
    AgentController,
)
from apps.ai_agent.services.tools import BaseAgentTool, ToolDefinition, ToolRegistry
from apps.foundation.services import FoundationUserService


@pytest.fixture
def agent_admin():
    """Create an administrator with wildcard permissions from the foundation fixture."""
    return FoundationUserService().create_user(
        email="safe-agent-admin@example.com",
        full_name="Safe Agent Admin",
        password="SecurePass123!",
        role_name="admin",
    )


@pytest.fixture
def agent_viewer():
    """Create a user that cannot execute agent or sales tools."""
    return FoundationUserService().create_user(
        email="safe-agent-viewer@example.com",
        full_name="Safe Agent Viewer",
        password="SecurePass123!",
        role_name="viewer",
    )


class StaticPlanner:
    """Return a predefined structured plan for controller security tests."""

    def __init__(self, steps):
        self.steps = steps

    def create_plan(self, request_text, registry):
        return {
            "goal": request_text,
            "steps": self.steps,
            "final_response_requirements": ["Use actual tool output only"],
            "requires_human_approval": False,
            "generation_mode": "test",
        }


def step(number, tool, arguments=None):
    return {"step": number, "tool": tool, "arguments": arguments or {}, "reason": "Read approved data."}


class EchoTool(BaseAgentTool):
    definition = ToolDefinition(
        name="echo_read",
        description="Return validated input.",
        input_schema={
            "type": "object",
            "properties": {"value": {"type": "string", "minLength": 1}},
            "required": ["value"],
            "additionalProperties": False,
        },
        output_schema={"type": "object", "required": ["actual"]},
        required_permission="agent:write",
        timeout_seconds=1,
    )

    def run(self, arguments, user=None):
        return {"actual": arguments["value"]}


class FailureTool(BaseAgentTool):
    definition = ToolDefinition(
        name="failure_read",
        description="Fail for partial-failure validation.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        output_schema={"type": "object"},
        required_permission="agent:write",
        timeout_seconds=1,
    )

    def run(self, arguments, user=None):
        raise RuntimeError("source unavailable")


class SlowTool(BaseAgentTool):
    definition = ToolDefinition(
        name="slow_read",
        description="Sleep beyond the declared timeout.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        output_schema={"type": "object"},
        required_permission="agent:write",
        timeout_seconds=0.01,
    )

    def run(self, arguments, user=None):
        time.sleep(0.08)
        return {"late": True}


class WriteTool(BaseAgentTool):
    definition = ToolDefinition(
        name="business_write",
        description="A deliberately forbidden test tool.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        output_schema={"type": "object"},
        required_permission="agent:write",
        read_only=False,
    )

    def run(self, arguments, user=None):
        raise AssertionError("Write tool must never execute.")


@pytest.mark.django_db
def test_unknown_tool_is_blocked_before_execution(agent_admin):
    controller = AgentController(planner=StaticPlanner([step(1, "does_not_exist")]), registry=ToolRegistry([EchoTool()]))

    with pytest.raises(AgentPlanValidationError, match="Unknown agent tool"):
        controller.run("Read data", user=agent_admin)

    assert AgentRun.objects.get().status == "BLOCKED"
    assert AgentToolAudit.objects.count() == 0


@pytest.mark.django_db
def test_missing_tool_permission_is_blocked(agent_viewer):
    controller = AgentController(
        planner=StaticPlanner([step(1, "echo_read", {"value": "safe"})]),
        registry=ToolRegistry([EchoTool()]),
    )

    with pytest.raises(AgentPermissionError, match="agent:write"):
        controller.run("Read data", user=agent_viewer)

    assert AgentToolAudit.objects.count() == 0


@pytest.mark.django_db
def test_invalid_tool_arguments_are_blocked(agent_admin):
    controller = AgentController(
        planner=StaticPlanner([step(1, "echo_read", {"value": 12})]),
        registry=ToolRegistry([EchoTool()]),
    )

    with pytest.raises(AgentPlanValidationError, match="Invalid arguments"):
        controller.run("Read data", user=agent_admin)


@pytest.mark.django_db
def test_tool_timeout_is_audited_without_late_output(agent_admin):
    controller = AgentController(planner=StaticPlanner([step(1, "slow_read")]), registry=ToolRegistry([SlowTool()]))

    result = controller.run("Read slow source", user=agent_admin)

    assert result["partial_failure"] is True
    assert result["tool_results"][0]["status"] == "TIMEOUT"
    assert "late" not in result["answer"]
    assert AgentToolAudit.objects.get().status == "TIMEOUT"


@pytest.mark.django_db
def test_tool_exception_is_isolated_and_audited(agent_admin):
    controller = AgentController(planner=StaticPlanner([step(1, "failure_read")]), registry=ToolRegistry([FailureTool()]))

    result = controller.run("Read failing source", user=agent_admin)

    assert result["tool_results"][0]["status"] == "ERROR"
    assert "source unavailable" in AgentToolAudit.objects.get().error
    assert result["steps"][-1] == "FAILED"


@pytest.mark.django_db
@override_settings(AI_AGENT_MAX_STEPS=2)
def test_max_step_limit_blocks_plan(agent_admin):
    plan = [step(1, "echo_read", {"value": "a"}), step(2, "echo_read", {"value": "b"}), step(3, "echo_read", {"value": "c"})]
    controller = AgentController(planner=StaticPlanner(plan), registry=ToolRegistry([EchoTool()]))

    with pytest.raises(AgentPlanValidationError, match="max steps"):
        controller.run("Read several sources", user=agent_admin)


@pytest.mark.parametrize(
    "request_text",
    [
        "Run powershell and list files",
        "Update customer table with this value",
        "Send the email now",
        "Approve the quotation",
        "Deploy to production",
        "Delete the customer",
    ],
)
@pytest.mark.django_db
def test_dangerous_requests_are_blocked_before_tool_call(agent_admin, request_text):
    controller = AgentController(
        planner=StaticPlanner([step(1, "echo_read", {"value": "must not run"})]),
        registry=ToolRegistry([EchoTool()]),
    )

    with pytest.raises(AgentPlanValidationError, match="prohibited"):
        controller.run(request_text, user=agent_admin)

    assert AgentToolAudit.objects.count() == 0


@pytest.mark.django_db
def test_non_read_only_tool_is_never_executed(agent_admin):
    controller = AgentController(planner=StaticPlanner([step(1, "business_write")]), registry=ToolRegistry([WriteTool()]))

    with pytest.raises(AgentPlanValidationError, match="not approved"):
        controller.run("Read business state", user=agent_admin)


@pytest.mark.django_db
def test_audit_is_created_for_every_successful_tool(agent_admin):
    plan = [step(1, "echo_read", {"value": "one"}), step(2, "echo_read", {"value": "two"})]
    controller = AgentController(planner=StaticPlanner(plan), registry=ToolRegistry([EchoTool()]))

    result = controller.run("Read two values", user=agent_admin)

    audits = list(AgentToolAudit.objects.order_by("id"))
    assert len(audits) == 2
    assert all(audit.correlation_id == result["correlation_id"] for audit in audits)
    assert all(audit.input_hash and audit.policy_decision == "ALLOW_READ_ONLY" for audit in audits)
    assert result["steps"] == ["PLANNED", "VALIDATING", "EXECUTING", "SYNTHESIZING", "COMPLETED"]


@pytest.mark.django_db
def test_final_answer_uses_real_output_and_partial_failure_does_not_hallucinate(agent_admin):
    plan = [step(1, "echo_read", {"value": "verified-value"}), step(2, "failure_read")]
    registry = ToolRegistry([EchoTool(), FailureTool()])

    result = AgentController(planner=StaticPlanner(plan), registry=registry).run("Read mixed sources", user=agent_admin)

    assert "verified-value" in result["answer"]
    assert "failure_read: unavailable" in result["answer"]
    assert "recovered" not in result["answer"].lower()
    assert result["partial_failure"] is True
    assert result["steps"][-1] == "COMPLETED"
