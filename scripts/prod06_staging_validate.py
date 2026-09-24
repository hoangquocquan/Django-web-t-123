"""Validate the running production-like staging stack without changing it."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from urllib.parse import urlparse
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "evidence" / "prod-06" / "staging-runtime.json"
REQUIRED_SERVICES = {"web", "database", "redis", "n8n"}
COMPOSE_PROJECT = "mecprecision-vietnam"


def utc_now():
    """Return a stable UTC timestamp for evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_command(args, timeout=30):
    """Run a read-only command and return a serializable result."""
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
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"returncode": 124, "stdout": "", "stderr": str(exc)}
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def http_probe(url, expected_statuses=(200,), headers=None, timeout=10):
    """Probe an HTTP endpoint while retaining only non-sensitive metadata."""
    parsed = urlparse(url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
        return {
            "ok": False,
            "status_code": None,
            "latency_ms": 0,
            "error": "Only local HTTP probes are allowed",
        }
    request = urllib.request.Request(url, headers=headers or {})
    started = datetime.now(timezone.utc)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310 - URL is loopback-only
            status = response.status
            body = response.read(4096).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read(4096).decode("utf-8", errors="replace")
    except (OSError, urllib.error.URLError) as exc:
        return {"ok": False, "status_code": None, "latency_ms": 0, "error": str(exc)}
    elapsed = (datetime.now(timezone.utc) - started).total_seconds() * 1000
    return {
        "ok": status in expected_statuses,
        "status_code": status,
        "latency_ms": round(elapsed, 2),
        "body_preview": body[:300],
    }


def discover_compose_services():
    """Discover running Compose services without reading container secrets."""
    if not shutil.which("docker"):
        return {"available": False, "services": {}, "reason": "Docker CLI missing"}
    command = run_command(
        [
            "docker",
            "ps",
            "--filter",
            f"label=com.docker.compose.project={COMPOSE_PROJECT}",
            "--format",
            "{{json .}}",
        ]
    )
    if command["returncode"] != 0:
        return {"available": False, "services": {}, "reason": command["stderr"]}

    services = {}
    for line in command["stdout"].splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        name = row.get("Names", "")
        inspect = run_command(
            [
                "docker",
                "inspect",
                name,
                "--format",
                "{{json .Config.Labels}}|{{json .State}}|{{json .Config.User}}",
            ]
        )
        if inspect["returncode"] != 0:
            continue
        labels_raw, state_raw, user_raw = inspect["stdout"].split("|", 2)
        labels = json.loads(labels_raw)
        service = labels.get("com.docker.compose.service")
        if not service:
            continue
        state = json.loads(state_raw)
        services[service] = {
            "container": name,
            "running": bool(state.get("Running")),
            "health": (state.get("Health") or {}).get("Status", "not-configured"),
            "non_root_user": json.loads(user_raw) not in {"", "0", "root"},
        }
    return {"available": True, "services": services, "reason": ""}


def validate_runtime(base_url="http://127.0.0.1:8000", n8n_url="http://127.0.0.1:5679"):
    """Validate service health, HTTPS proxy behavior, and local Ollama access."""
    docker = discover_compose_services()
    forwarded_https = {"X-Forwarded-Proto": "https", "Host": "localhost"}
    operations_headers = dict(forwarded_https)
    metrics_token = os.getenv("METRICS_BEARER_TOKEN", "").strip()
    if metrics_token:
        operations_headers["Authorization"] = f"Bearer {metrics_token}"
    probes = {
        "django_health": http_probe(
            f"{base_url}/api/v1/health/", headers=forwarded_https
        ),
        "operations_health": http_probe(
            f"{base_url}/api/v1/operations/health/", headers=operations_headers
        ),
        "ai_health": http_probe(
            f"{base_url}/api/v1/ai/health/", headers=forwarded_https
        ),
        "n8n_health": http_probe(f"{n8n_url}/healthz"),
        "ollama_models": http_probe("http://127.0.0.1:11434/api/tags"),
    }
    services = docker.get("services", {})
    services_ok = REQUIRED_SERVICES.issubset(services) and all(
        services[name]["running"]
        and services[name]["health"] in {"healthy", "not-configured"}
        for name in REQUIRED_SERVICES
    )
    non_root = bool(services.get("web", {}).get("non_root_user"))
    status = (
        "PASS"
        if services_ok and non_root and all(item["ok"] for item in probes.values())
        else "FAIL"
    )
    return {
        "phase": "PROD-06",
        "created_at": utc_now(),
        "status": status,
        "environment": "production-like-local-staging",
        "tls_equivalent": "X-Forwarded-Proto=https through trusted proxy contract",
        "docker": docker,
        "probes": probes,
        "safety": {
            "production_modified": False,
            "deployment_executed": False,
            "secrets_recorded": False,
        },
    }


def main():
    """Run validation and persist evidence."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--n8n-url", default="http://127.0.0.1:5679")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    report = validate_runtime(args.base_url.rstrip("/"), args.n8n_url.rstrip("/"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
