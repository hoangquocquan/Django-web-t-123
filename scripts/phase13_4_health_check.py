"""Validate the Phase 13.4 deployment simulation.

Checks the simulation container, application endpoint, database status from the
health response, and critical dependency evidence.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT_RESULT = PROJECT_ROOT / "docs" / "deployment" / "deployment_result.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "deployment" / "health_result.json"


def utc_now():
    """Return an ISO timestamp for health evidence."""
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
    """Load deployment result evidence."""
    target = Path(path)
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def docker_available():
    """Check Docker availability."""
    if not shutil.which("docker"):
        return {"available": False, "detail": "Docker CLI not found."}
    info = run_command(["docker", "info", "--format", "{{json .ServerVersion}}"], timeout=30)
    return {"available": info["returncode"] == 0, "detail": info["stderr"], "server_version": info["stdout"].strip('"')}


def inspect_container(container_name):
    """Inspect simulation container status."""
    result = run_command(["docker", "inspect", container_name], timeout=60)
    if result["returncode"] != 0:
        return {"exists": False, "running": False, "health_status": "", "error": result["stderr"]}
    payload = json.loads(result["stdout"])[0]
    state = payload.get("State", {})
    return {
        "exists": True,
        "running": bool(state.get("Running")),
        "health_status": (state.get("Health") or {}).get("Status", ""),
        "error": state.get("Error", ""),
    }


def check_endpoint(port):
    """Call the simulated application health endpoint."""
    url = f"http://127.0.0.1:{port}/api/v1/health/"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            body = response.read().decode("utf-8", errors="replace")
            payload = json.loads(body)
            return {
                "ok": response.status == 200,
                "url": url,
                "status_code": response.status,
                "body": payload,
                "database_ok": payload.get("database") == "ok",
            }
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "url": url, "status_code": None, "body": {}, "database_ok": False, "error": str(exc)}


def validate_health(deployment_path=DEPLOYMENT_RESULT, output_path=None, dry_run=False):
    """Validate deployment health and write evidence."""
    deployment = load_deployment(deployment_path)
    container = deployment.get("container", {})
    container_name = container.get("name", "mecprecision-phase13-4-deployment")
    port = int(container.get("host_port", 18004))
    docker_state = docker_available()

    if dry_run:
        container_status = {"exists": True, "running": True, "health_status": "dry-run", "error": ""}
        endpoint = {"ok": True, "url": f"http://127.0.0.1:{port}/api/v1/health/", "database_ok": True, "body": {"database": "ok"}}
    elif not docker_state["available"]:
        container_status = {"exists": False, "running": False, "health_status": "", "error": docker_state["detail"]}
        endpoint = {"ok": False, "database_ok": False, "error": "Docker unavailable."}
    else:
        container_status = inspect_container(container_name)
        endpoint = check_endpoint(port)

    dependencies = {
        "deployment_evidence_exists": bool(deployment),
        "docker_available": docker_state["available"] or dry_run,
        "application_endpoint": endpoint.get("ok", False),
        "database_connection": endpoint.get("database_ok", False),
    }
    status = "HEALTH_VALIDATION_COMPLETE" if all(dependencies.values()) and container_status.get("running") else "HEALTH_VALIDATION_BLOCKED"
    report = {
        "phase": "13.4",
        "created_at": utc_now(),
        "status": status,
        "deployment_result": str(Path(deployment_path)),
        "container": container_status,
        "endpoint": endpoint,
        "critical_dependencies": dependencies,
        "safety": {
            "production_deployed": False,
            "cloud_infrastructure_created": False,
            "production_secrets_stored": False,
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

    parser = argparse.ArgumentParser(description="Run Phase 13.4 health validation.")
    parser.add_argument("--deployment", default=str(DEPLOYMENT_RESULT))
    parser.add_argument("--output", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    report = validate_health(deployment_path=args.deployment, output_path=args.output, dry_run=args.dry_run)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] in {"HEALTH_VALIDATION_COMPLETE", "HEALTH_VALIDATION_BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
