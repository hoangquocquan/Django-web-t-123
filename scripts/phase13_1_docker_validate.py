"""Phase 13.1 Docker image validation helper.

The validator checks local image/container behavior when Docker is available.
It never deploys production and never pushes images externally.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILD_REPORT = PROJECT_ROOT / "docs" / "docker" / "docker_build_report.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "docker" / "docker_validation_report.json"
DEFAULT_IMAGE = "mecprecision-vietnam:phase-13.1"


def utc_now():
    """Return an ISO timestamp for validation evidence."""
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
    """Check Docker CLI and daemon availability."""
    if not shutil.which("docker"):
        return {"available": False, "detail": "Docker CLI not found.", "server_version": ""}
    info = run_command(["docker", "info", "--format", "{{json .ServerVersion}}"], timeout=30)
    return {"available": info["returncode"] == 0, "detail": info["stderr"], "server_version": info["stdout"].strip('"')}


def inspect_image(image):
    """Inspect image security-related metadata."""
    result = run_command(["docker", "image", "inspect", image], timeout=60)
    if result["returncode"] != 0:
        return {"exists": False, "error": result["stderr"], "user": "", "healthcheck_present": False}
    payload = json.loads(result["stdout"])[0]
    config = payload.get("Config", {})
    return {
        "exists": True,
        "user": config.get("User", ""),
        "healthcheck_present": "Healthcheck" in config,
        "exposed_ports": sorted((config.get("ExposedPorts") or {}).keys()),
    }


def check_container_health(container_name, attempts=15, delay_seconds=2):
    """Wait for Django inside the container before deciding health status.

    Docker can report a container as started before Django has finished booting.
    The retry loop keeps validation honest: it waits for a real successful
    `/api/v1/health/` response, but still fails if the app never becomes ready.
    """
    health_command = [
        "docker",
        "exec",
        container_name,
        "python",
        "-c",
        "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/', timeout=5).read()",
    ]
    last_result = {"skipped": False, "returncode": None, "stdout": "", "stderr": ""}

    for attempt in range(1, attempts + 1):
        result = run_command(health_command, timeout=60)
        result["attempt"] = attempt
        result["attempts"] = attempts
        last_result = result
        if result["returncode"] == 0:
            return result
        time.sleep(delay_seconds)

    return last_result


def validate_image(image=DEFAULT_IMAGE, output_path=None, skip_container=False):
    """Validate image existence, metadata, and optional container startup."""
    docker_state = docker_available()
    image_info = {"exists": False, "user": "", "healthcheck_present": False}
    container_result = {"skipped": True, "returncode": None, "stdout": "", "stderr": ""}
    health_result = {"skipped": True, "returncode": None, "stdout": "", "stderr": ""}
    container_logs = {"skipped": True, "returncode": None, "stdout": "", "stderr": ""}
    cleanup_result = {"skipped": True, "returncode": None, "stdout": "", "stderr": ""}

    if not docker_state["available"]:
        status = "DOCKER_VALIDATION_BLOCKED"
    else:
        image_info = inspect_image(image)
        if image_info.get("exists") and not skip_container:
            container_name = "mecprecision-phase13-1-validation"
            cleanup_result = run_command(["docker", "rm", "-f", container_name], timeout=60)
            container_result = run_command(["docker", "run", "-d", "--name", container_name, "-p", "18000:8000", image], timeout=120)
            if container_result["returncode"] == 0:
                health_result = check_container_health(container_name)
                if health_result["returncode"] != 0:
                    container_logs = run_command(["docker", "logs", container_name, "--tail", "120"], timeout=60)
            cleanup_result = run_command(["docker", "rm", "-f", container_name], timeout=60)

        security = {
            "non_root_user": bool(image_info.get("user")) and image_info.get("user") != "root",
            "healthcheck_present": bool(image_info.get("healthcheck_present")),
            "host_port_exposed_by_validation_only": True,
        }
        container_ok = skip_container or container_result["returncode"] == 0
        health_ok = skip_container or health_result["returncode"] == 0
        status = "DOCKER_VALIDATION_COMPLETE" if image_info.get("exists") and all(security.values()) and container_ok and health_ok else "DOCKER_VALIDATION_BLOCKED"

    report = {
        "phase": "13.1",
        "created_at": utc_now(),
        "status": status,
        "image": image,
        "docker": docker_state,
        "build_report": str(BUILD_REPORT),
        "image_info": image_info,
        "container_start": container_result,
        "health_check": health_result,
        "container_logs": container_logs,
        "cleanup": cleanup_result,
        "safety": {
            "production_deployed": False,
            "image_pushed_externally": False,
            "real_registry_credentials_used": False,
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

    parser = argparse.ArgumentParser(description="Validate local Docker image for Phase 13.1.")
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--output", default=None)
    parser.add_argument("--skip-container", action="store_true")
    args = parser.parse_args()

    result = validate_image(image=args.image, output_path=args.output, skip_container=args.skip_container)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
