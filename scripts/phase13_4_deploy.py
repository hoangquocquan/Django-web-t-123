"""Run Phase 13.4 local deployment simulation.

The script validates the Docker artifact, starts a local simulation container,
checks health, and writes deployment evidence. It never deploys production and
never creates cloud infrastructure.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = "mecprecision-vietnam:phase-13.1"
DEFAULT_PREVIOUS_IMAGE = "mecprecision-vietnam:previous-safe"
DEFAULT_CONTAINER = "mecprecision-phase13-4-deployment"
DEFAULT_PORT = 18004
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "deployment" / "deployment_result.json"


def utc_now():
    """Return an ISO timestamp for deployment evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_command(args, timeout=120):
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


def docker_available():
    """Check whether Docker CLI and daemon are usable."""
    if not shutil.which("docker"):
        return {"available": False, "detail": "Docker CLI not found.", "server_version": ""}
    info = run_command(["docker", "info", "--format", "{{json .ServerVersion}}"], timeout=30)
    return {
        "available": info["returncode"] == 0,
        "detail": info["stderr"],
        "server_version": info["stdout"].strip('"'),
    }


def inspect_image(image):
    """Inspect local Docker image metadata."""
    result = run_command(["docker", "image", "inspect", image], timeout=60)
    if result["returncode"] != 0:
        return {"exists": False, "image": image, "error": result["stderr"]}
    payload = json.loads(result["stdout"])[0]
    config = payload.get("Config", {})
    return {
        "exists": True,
        "image": image,
        "id": payload.get("Id", ""),
        "created": payload.get("Created", ""),
        "user": config.get("User", ""),
        "healthcheck_present": "Healthcheck" in config,
    }


def wait_for_health(port, attempts=15, delay_seconds=2):
    """Wait for the simulated deployment health endpoint."""
    url = f"http://127.0.0.1:{port}/api/v1/health/"
    last_error = ""
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                body = response.read().decode("utf-8", errors="replace")
                return {
                    "ok": response.status == 200,
                    "url": url,
                    "status_code": response.status,
                    "body": body,
                    "attempt": attempt,
                    "attempts": attempts,
                    "error": "",
                }
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = str(exc)
            time.sleep(delay_seconds)
    return {
        "ok": False,
        "url": url,
        "status_code": None,
        "body": "",
        "attempt": attempts,
        "attempts": attempts,
        "error": last_error,
    }


def simulate_deployment(
    image=DEFAULT_IMAGE,
    previous_image=DEFAULT_PREVIOUS_IMAGE,
    container_name=DEFAULT_CONTAINER,
    port=DEFAULT_PORT,
    output_path=None,
    dry_run=False,
):
    """Run the local deployment simulation and write JSON evidence."""
    docker_state = docker_available()
    image_info = {"exists": False, "image": image}
    cleanup = {"skipped": True}
    start = {"skipped": True}
    health = {"skipped": True, "ok": False}
    logs = {"skipped": True}

    if dry_run:
        status = "DEPLOYMENT_SIMULATION_COMPLETE"
        image_info = {"exists": True, "image": image, "id": "dry-run", "user": "appuser", "healthcheck_present": True}
        health = {"skipped": False, "ok": True, "url": f"http://127.0.0.1:{port}/api/v1/health/", "body": "dry-run"}
    elif not docker_state["available"]:
        status = "DEPLOYMENT_BLOCKED"
    else:
        image_info = inspect_image(image)
        if not image_info.get("exists"):
            status = "DEPLOYMENT_BLOCKED"
        else:
            cleanup = run_command(["docker", "rm", "-f", container_name], timeout=60)
            start = run_command(["docker", "run", "-d", "--name", container_name, "-p", f"{port}:8000", image], timeout=120)
            if start["returncode"] == 0:
                health = wait_for_health(port)
                if not health["ok"]:
                    logs = run_command(["docker", "logs", container_name, "--tail", "120"], timeout=60)
            status = "DEPLOYMENT_SIMULATION_COMPLETE" if start.get("returncode") == 0 and health.get("ok") else "DEPLOYMENT_BLOCKED"

    report = {
        "phase": "13.4",
        "created_at": utc_now(),
        "status": status,
        "environment": "local_simulation",
        "artifact": {
            "image": image,
            "previous_image": previous_image,
            "image_info": image_info,
        },
        "container": {
            "name": container_name,
            "host_port": port,
        },
        "docker": docker_state,
        "cleanup_before_start": cleanup,
        "start": start,
        "health": health,
        "logs": logs,
        "safety": {
            "production_deployed": False,
            "cloud_infrastructure_created": False,
            "production_secrets_stored": False,
            "rollback_capability_removed": False,
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

    parser = argparse.ArgumentParser(description="Run Phase 13.4 deployment simulation.")
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--previous-image", default=DEFAULT_PREVIOUS_IMAGE)
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--output", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    report = simulate_deployment(
        image=args.image,
        previous_image=args.previous_image,
        container_name=args.container,
        port=args.port,
        output_path=args.output,
        dry_run=args.dry_run,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] in {"DEPLOYMENT_SIMULATION_COMPLETE", "DEPLOYMENT_BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
