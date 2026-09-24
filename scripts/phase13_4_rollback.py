"""Run Phase 13.4 rollback simulation.

The rollback simulation records the previous artifact reference and cleans up
the local deployment container when present. It never rolls back production.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT_RESULT = PROJECT_ROOT / "docs" / "deployment" / "deployment_result.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "deployment" / "rollback_result.json"


def utc_now():
    """Return an ISO timestamp for rollback evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_command(args, timeout=60):
    """Run a command and return structured output without raising."""
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
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"command": " ".join(args), "returncode": 124, "stdout": "", "stderr": str(exc)}
    return {
        "command": " ".join(args),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def load_deployment(path=DEPLOYMENT_RESULT):
    """Load deployment evidence if it exists."""
    target = Path(path)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def docker_available():
    """Check Docker availability."""
    if not shutil.which("docker"):
        return False
    return run_command(["docker", "info", "--format", "{{json .ServerVersion}}"], timeout=30)["returncode"] == 0


def simulate_rollback(deployment_path=DEPLOYMENT_RESULT, output_path=None, dry_run=False):
    """Generate rollback evidence and clean up local simulation if possible."""
    deployment = load_deployment(deployment_path)
    artifact = deployment.get("artifact", {})
    container = deployment.get("container", {})
    container_name = container.get("name", "mecprecision-phase13-4-deployment")
    previous_image = artifact.get("previous_image", "mecprecision-vietnam:previous-safe")
    current_image = artifact.get("image", "mecprecision-vietnam:phase-13.1")
    deployment_failed = deployment.get("status") != "DEPLOYMENT_SIMULATION_COMPLETE"

    if dry_run:
        cleanup = {"skipped": False, "returncode": 0, "stdout": "dry-run cleanup", "stderr": ""}
    elif docker_available():
        cleanup = run_command(["docker", "rm", "-f", container_name], timeout=60)
    else:
        cleanup = {"skipped": True, "returncode": None, "stdout": "", "stderr": "Docker unavailable."}

    report = {
        "phase": "13.4",
        "created_at": utc_now(),
        "status": "ROLLBACK_SIMULATION_COMPLETE",
        "deployment_failed": deployment_failed,
        "current_artifact": current_image,
        "restored_artifact_reference": previous_image,
        "cleanup": cleanup,
        "safety": {
            "production_rollback_executed": False,
            "production_deployed": False,
            "cloud_infrastructure_modified": False,
            "rollback_capability_preserved": True,
            "human_approval_required": True,
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

    parser = argparse.ArgumentParser(description="Run Phase 13.4 rollback simulation.")
    parser.add_argument("--deployment", default=str(DEPLOYMENT_RESULT))
    parser.add_argument("--output", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    report = simulate_rollback(deployment_path=args.deployment, output_path=args.output, dry_run=args.dry_run)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
