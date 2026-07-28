"""Create or send a Phase 13.3 n8n orchestration event.

The script can call a configured n8n webhook, but it safely falls back to local
dry-run evidence when `N8N_WEBHOOK_URL` is not configured. It never deploys
production and never stores real secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "n8n" / "n8n_execution_report.json"
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


def main():
    """Command-line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Trigger or simulate n8n CI/CD orchestration.")
    parser.add_argument("--webhook-url", default=DEFAULT_WEBHOOK_URL)
    parser.add_argument("--output", default=None)
    parser.add_argument("--local-only", action="store_true")
    args = parser.parse_args()

    report = create_execution_report(
        output_path=args.output,
        webhook_url=args.webhook_url,
        local_only=args.local_only,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "N8N_ORCHESTRATION_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
