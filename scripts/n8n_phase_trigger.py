"""Create or send n8n orchestration events.

The script supports the original Phase 13.3 evidence flow and the Phase 13.7
real automation controller. It can call a configured n8n webhook, but safely
falls back to local controller mode when `N8N_WEBHOOK_URL` is not configured.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "n8n" / "n8n_execution_report.json"
DEFAULT_HISTORY = PROJECT_ROOT / "n8n" / "results" / "execution_history.json"
DEFAULT_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")


def utc_now():
    """Return an ISO timestamp for orchestration evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_git(args):
    """Run read-only Git commands for event context."""
    completed = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def run_command(args, timeout=900):
    """Run an approved local automation command and capture evidence."""
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            args,
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except (subprocess.TimeoutExpired, OSError) as exc:
        returncode = 124
        stdout = ""
        stderr = str(exc)
    return {
        "command": " ".join(str(arg) for arg in args),
        "returncode": returncode,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "stdout_tail": stdout[-12000:],
        "stderr_tail": stderr[-12000:],
        "status": "PASS" if returncode == 0 else "FAIL",
    }


def parse_command_json(command_result):
    """Read the review gate contract; a successful process alone cannot advance n8n."""
    try:
        return json.loads(str(command_result.get("stdout_tail", "")).strip())
    except json.JSONDecodeError:
        return {}


def load_json(path):
    """Load JSON evidence if it exists."""
    target = Path(path)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def build_event(phase="13.3"):
    """Build a compact event payload for n8n."""
    test_result = load_json(PROJECT_ROOT / "docs" / "cicd" / "test_pipeline_result.json")
    docker_result = load_json(PROJECT_ROOT / "docs" / "docker" / "docker_build_report.json")
    return {
        "phase": phase,
        "created_at": utc_now(),
        "branch": run_git(["branch", "--show-current"]),
        "commit": run_git(["rev-parse", "HEAD"]),
        "test_status": test_result.get("summary", {}).get("status", "UNKNOWN"),
        "docker_status": docker_result.get("status", "UNKNOWN"),
        "requested_action": "review_orchestration",
        "production_deployment_requested": False,
        "human_approval_required": True,
    }


def post_webhook(url, payload, timeout=20):
    """Send event to n8n webhook and return structured result."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {
                "sent": True,
                "status_code": response.status,
                "response_body": body[:4000],
                "error": "",
            }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "sent": False,
            "status_code": None,
            "response_body": "",
            "error": str(exc),
        }


def create_execution_report(output_path=None, webhook_url=DEFAULT_WEBHOOK_URL, local_only=False):
    """Create n8n execution evidence without requiring production access."""
    event = build_event()
    webhook_configured = bool(webhook_url) and not local_only
    webhook_result = (
        post_webhook(webhook_url, event)
        if webhook_configured
        else {"sent": False, "status_code": None, "response_body": "", "error": "Local dry-run mode."}
    )

    status = "N8N_ORCHESTRATION_COMPLETE" if event["test_status"] == "TEST_PIPELINE_COMPLETE" else "N8N_ORCHESTRATION_BLOCKED"
    report = {
        "phase": "13.3",
        "created_at": utc_now(),
        "status": status,
        "mode": "webhook" if webhook_configured else "local_dry_run",
        "webhook_configured": webhook_configured,
        "event": event,
        "webhook_result": webhook_result,
        "outputs": {
            "test_pipeline": "docs/cicd/test_pipeline_result.json",
            "docker_build": "docs/docker/docker_build_report.json",
            "ai_review": "docs/ai-devops/N8N_AI_REVIEW_REPORT.md",
        },
        "safety": {
            "production_deployed": False,
            "real_secrets_stored": False,
            "human_approval_bypassed": False,
            "ci_testing_replaced": False,
        },
    }

    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def load_history(path=DEFAULT_HISTORY):
    """Load controller execution history."""
    target = Path(path)
    if not target.exists():
        return []
    payload = json.loads(target.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else payload.get("executions", [])


def append_history(entry, path=DEFAULT_HISTORY):
    """Append one execution entry to history JSON."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    history = load_history(output)
    history.append(entry)
    output.write_text(json.dumps(history[-20:], indent=2, ensure_ascii=False), encoding="utf-8")
    return history[-20:]


def create_controller_event(phase="13.7"):
    """Build the Phase 13.7 automation event."""
    return {
        "phase": phase,
        "created_at": utc_now(),
        "branch": run_git(["branch", "--show-current"]),
        "commit": run_git(["rev-parse", "HEAD"]),
        "trigger_source": "local_controller",
        "requested_action": "phase_automation_controller",
        "production_deployment_requested": False,
        "auto_merge_requested": False,
        "human_approval_required": True,
    }


def run_local_controller(phase="13.7"):
    """Run the local controller path using existing systems."""
    phase_validation = run_command([sys.executable, "scripts/phase_validator.py", "--phase", phase], timeout=120)
    if phase_validation["returncode"] != 0:
        return {
            "status": "BLOCKED",
            "state": "BLOCKED",
            "phase_validation": phase_validation,
            "ai_review": {},
            "ai_review_contract": {},
            "self_correction": {},
        }
    ai_review = run_command([sys.executable, "ai-review/run_phase_review.py", "--phase", phase, "--skip-migration"], timeout=900)
    contract = parse_command_json(ai_review)
    review_status = contract.get("status", "BLOCKED")
    self_correction = {}
    if review_status == "WAITING_HUMAN_APPROVAL":
        status = "WAITING_HUMAN_APPROVAL"
    elif review_status == "WAITING_HUMAN_REVIEW":
        status = "WAITING_HUMAN_REVIEW"
    else:
        self_correction = run_command([sys.executable, "ai-review/retry_controller.py"], timeout=900)
        status = "CORRECTION_REQUIRED" if self_correction.get("returncode") == 0 else "BLOCKED"
    return {
        "status": status,
        "state": status,
        "phase_validation": phase_validation,
        "ai_review": ai_review,
        "ai_review_contract": contract,
        "self_correction": self_correction,
    }


def create_automation_history(output_path=None, webhook_url=DEFAULT_WEBHOOK_URL, local_only=False, phase="13.7"):
    """Trigger n8n or run local automation controller and store execution history."""
    event = create_controller_event(phase=phase)
    webhook_configured = bool(webhook_url) and not local_only
    webhook_result = (
        post_webhook(webhook_url, event)
        if webhook_configured
        else {"sent": False, "status_code": None, "response_body": "", "error": "Local controller mode."}
    )
    local_result = (
        {"status": "CODEX_RUNNING", "phase_validation": {}, "ai_review": {}, "ai_review_contract": {}, "self_correction": {}}
        if webhook_configured and webhook_result["sent"]
        else run_local_controller(phase=phase)
    )

    entry = {
        "phase": phase,
        "created_at": utc_now(),
        "mode": "webhook" if webhook_configured else "local_controller",
        "status": local_result["status"] if not webhook_configured else ("CODEX_RUNNING" if webhook_result["sent"] else "BLOCKED"),
        "event": event,
        "webhook_result": webhook_result,
        "execution_result": local_result,
        "outputs": {
            "phase_review": "docs/reviews/PHASE_AI_REVIEW_REPORT.md",
            "self_correction": "docs/reviews/PHASE_13.6_SELF_CORRECTION_REPORT.md",
            "history": "n8n/results/execution_history.json",
        },
        "safety": {
            "production_deployed": False,
            "code_auto_merged": False,
            "human_approval_bypassed": False,
            "failed_tests_hidden": False,
            "human_approval_required": True,
        },
    }

    append_history(entry, path=output_path or DEFAULT_HISTORY)
    return entry


def main():
    """Command-line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Trigger or simulate n8n automation orchestration.")
    parser.add_argument("--webhook-url", default=DEFAULT_WEBHOOK_URL)
    parser.add_argument("--output", default=None)
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument("--phase", default="13.7")
    parser.add_argument("--legacy-report", action="store_true")
    args = parser.parse_args()

    if args.legacy_report:
        report = create_execution_report(
            output_path=args.output,
            webhook_url=args.webhook_url,
            local_only=args.local_only,
        )
    else:
        report = create_automation_history(
            output_path=args.output,
            webhook_url=args.webhook_url,
            local_only=args.local_only,
            phase=args.phase,
        )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] in {"N8N_ORCHESTRATION_COMPLETE", "WAITING_HUMAN_APPROVAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
