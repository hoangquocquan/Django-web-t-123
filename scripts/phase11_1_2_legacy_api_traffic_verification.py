"""Verify whether legacy `/api/...` routes still receive traffic.

This phase does not disable routes. It only reads operator-provided logs and
returns a JSON decision. `/api/v1/...` is counted as Django replacement traffic,
not legacy traffic.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

API_PATH_PATTERN = re.compile(r"(?P<path>/api(?:/[A-Za-z0-9._~{}-]+)+)")
SECRET_PATTERN = re.compile(
    r"(?i)(token|api_key|apikey|password|secret|authorization|session_id)=([^&\s]+)"
)


def is_replacement_api_path(path):
    """Return True when a path belongs to Django `/api/v1/...` namespace."""
    return path == "/api/v1" or path.startswith("/api/v1/")


def is_legacy_api_path(path):
    """Return True when a path belongs to legacy `/api/...` namespace."""
    return path.startswith("/api/") and not is_replacement_api_path(path)


def mask_sensitive_text(text):
    """Mask common secret values before writing samples to reports."""
    return SECRET_PATTERN.sub(lambda match: f"{match.group(1)}=***", text)


def extract_api_paths(line):
    """Extract API paths from one log line."""
    paths = []
    for match in API_PATH_PATTERN.finditer(line):
        path = match.group("path").rstrip(".")
        if path in {"/api", "/api/"}:
            continue
        paths.append(path)
    return paths


def client_is_unknown(line):
    """Return True when the log line has no obvious client identifier."""
    lowered = line.lower()
    known_markers = ("client=", "client_id=", "user-agent", "user_agent", "ua=")
    return not any(marker in lowered for marker in known_markers)


def analyze_log_lines(lines, source_name="<memory>"):
    """Analyze iterable log lines and count legacy/replacement API traffic."""
    legacy_requests = 0
    replacement_requests = 0
    unknown_clients = 0
    legacy_samples = []
    replacement_samples = []

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\n")
        for path in extract_api_paths(line):
            sample = {
                "source": source_name,
                "line": line_number,
                "path": path,
                "sample": mask_sensitive_text(line)[:300],
            }
            if is_replacement_api_path(path):
                replacement_requests += 1
                if len(replacement_samples) < 10:
                    replacement_samples.append(sample)
            elif is_legacy_api_path(path):
                legacy_requests += 1
                if client_is_unknown(line):
                    unknown_clients += 1
                if len(legacy_samples) < 10:
                    legacy_samples.append(sample)

    return {
        "source": source_name,
        "legacy_requests": legacy_requests,
        "replacement_requests": replacement_requests,
        "unknown_clients": unknown_clients,
        "legacy_samples": legacy_samples,
        "replacement_samples": replacement_samples,
    }


def analyze_log_file(path):
    """Analyze one log file if it exists."""
    log_path = Path(path)
    if not log_path.exists():
        return {
            "source": str(log_path),
            "exists": False,
            "legacy_requests": 0,
            "replacement_requests": 0,
            "unknown_clients": 0,
            "legacy_samples": [],
            "replacement_samples": [],
            "errors": ["Log file does not exist."],
        }

    with log_path.open("r", encoding="utf-8", errors="ignore") as file:
        result = analyze_log_lines(file, source_name=str(log_path))
    result["exists"] = True
    result["errors"] = []
    return result


def parse_log_paths(values=None, env=None):
    """Read log paths from CLI values or `PHASE11_1_2_LOG_PATHS`."""
    if values:
        return [str(Path(value)) for value in values]

    env = env or os.environ
    raw = env.get("PHASE11_1_2_LOG_PATHS", "")
    if not raw.strip():
        return []
    parts = re.split(r"[;,]", raw)
    return [part.strip() for part in parts if part.strip()]


def evaluate_traffic(log_paths=None, env=None):
    """Evaluate whether provided traffic evidence supports decommission."""
    started_at = time.perf_counter()
    paths = parse_log_paths(log_paths, env=env)
    source_results = [analyze_log_file(path) for path in paths]
    legacy_requests = sum(item["legacy_requests"] for item in source_results)
    replacement_requests = sum(item["replacement_requests"] for item in source_results)
    unknown_clients = sum(item["unknown_clients"] for item in source_results)
    logs_checked = sum(1 for item in source_results if item.get("exists"))
    errors = [
        error
        for item in source_results
        for error in item.get("errors", [])
    ]

    if not paths:
        errors.append("No production traffic logs were provided.")
    if legacy_requests:
        errors.append("Legacy API traffic is still present.")
    if unknown_clients:
        errors.append("Unknown legacy API clients were detected.")
    if logs_checked and replacement_requests == 0:
        errors.append("No Django replacement API traffic was observed.")

    safe_to_decommission = bool(paths) and logs_checked == len(paths) and not errors
    return {
        "status": "passed" if safe_to_decommission else "blocked_safely",
        "legacy_requests": legacy_requests,
        "replacement_requests": replacement_requests,
        "unknown_clients": unknown_clients,
        "logs_provided": bool(paths),
        "logs_checked": logs_checked,
        "safe_to_decommission": safe_to_decommission,
        "decision": "READY_FOR_DECOMMISSION" if safe_to_decommission else "KEEP_LEGACY_API_ACTIVE",
        "sources": source_results,
        "errors": errors,
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
    }


def main():
    """CLI entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Phase 11.1.2 legacy API traffic verification")
    parser.add_argument("--log", action="append", default=[], help="Path to API/proxy/application log.")
    args = parser.parse_args()
    result = evaluate_traffic(args.log)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
