"""Phase 13.1 Docker build pipeline helper.

This script builds and inspects a local Docker image when Docker is available.
It never pushes images and never deploys production.
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
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "docker" / "docker_build_report.json"
DEFAULT_IMAGE = "mecprecision-vietnam:phase-13.1"


def utc_now():
    """Return an ISO timestamp for build evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_command(args, timeout=300):
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
        return {"available": False, "detail": "Docker CLI not found.", "version": "", "server_version": ""}

    version = run_command(["docker", "--version"], timeout=20)
    info = run_command(["docker", "info", "--format", "{{json .ServerVersion}}"], timeout=30)
    return {
        "available": version["returncode"] == 0 and info["returncode"] == 0,
        "detail": info["stderr"] or version["stderr"],
        "version": version["stdout"],
        "server_version": info["stdout"].strip('"'),
    }


def inspect_image(image):
    """Inspect a local Docker image."""
    result = run_command(["docker", "image", "inspect", image], timeout=60)
    if result["returncode"] != 0:
        return {"exists": False, "error": result["stderr"], "raw": []}
    try:
        payload = json.loads(result["stdout"])
    except json.JSONDecodeError as exc:
        return {"exists": False, "error": str(exc), "raw": []}

    image_info = payload[0] if payload else {}
    config = image_info.get("Config", {})
    return {
        "exists": True,
        "id": image_info.get("Id", ""),
        "created": image_info.get("Created", ""),
        "size_bytes": image_info.get("Size", 0),
        "user": config.get("User", ""),
        "healthcheck_present": "Healthcheck" in config,
        "exposed_ports": sorted((config.get("ExposedPorts") or {}).keys()),
    }


def build_image(image=DEFAULT_IMAGE, output_path=None, skip_build=False):
    """Build the local Docker image and write a JSON report."""
    docker_state = docker_available()
    build_result = {"skipped": True, "returncode": None, "stdout": "", "stderr": ""}
    image_info = {"exists": False}

    if not docker_state["available"]:
        status = "DOCKER_BUILD_BLOCKED"
    else:
        if skip_build:
            build_result = {"skipped": True, "returncode": 0, "stdout": "Build skipped by argument.", "stderr": ""}
        else:
            build_result = run_command(["docker", "build", "--pull=false", "-t", image, "."], timeout=900)
        image_info = inspect_image(image)
        status = "DOCKER_BUILD_COMPLETE" if build_result["returncode"] == 0 and image_info.get("exists") else "DOCKER_BUILD_BLOCKED"

    report = {
        "phase": "13.1",
        "created_at": utc_now(),
        "status": status,
        "image": image,
        "docker": docker_state,
        "build": build_result,
        "image_info": image_info,
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

    parser = argparse.ArgumentParser(description="Build local Docker image for Phase 13.1.")
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--output", default=None)
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()

    result = build_image(image=args.image, output_path=args.output, skip_build=args.skip_build)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

