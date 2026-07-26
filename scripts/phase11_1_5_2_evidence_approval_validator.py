"""Validate collected production evidence and shutdown approvals.

This Phase 11.1.5.2 validator is read-only. It can read an optional JSON
approval package and returns either `READY_FOR_LEGACY_API_SHUTDOWN` or
`KEEP_LEGACY_API_ACTIVE`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    from scripts.phase11_1_4_production_traffic_evidence import evaluate_traffic_evidence
except ModuleNotFoundError:
    from phase11_1_4_production_traffic_evidence import evaluate_traffic_evidence


TRUTHY_VALUES = {"1", "true", "yes", "passed", "approved", "completed", "verified", "ready"}
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def truthy(value):
    """Return True for explicit positive values only."""
    return str(value or "").strip().lower() in TRUTHY_VALUES


def load_package(package_path=None):
    """Load an optional JSON evidence/approval package."""
    if not package_path:
        return {}
    path = Path(package_path)
    if not path.exists():
        return {"package_errors": [f"Package file does not exist: {path}."]}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"package_errors": [f"Package JSON is invalid: {exc}."]}


def read_env_package(env=None):
    """Build a validation package from environment variables."""
    env = env or os.environ
    return {
        "evidence": {
            "legacy_requests": int(env.get("PHASE11_1_5_2_LEGACY_REQUESTS") or 0),
            "replacement_requests": int(env.get("PHASE11_1_5_2_REPLACEMENT_REQUESTS") or 0),
            "unknown_clients": int(env.get("PHASE11_1_5_2_UNKNOWN_CLIENTS") or 0),
            "logs_provided": truthy(env.get("PHASE11_1_5_2_LOGS_PROVIDED")),
            "safe_to_decommission": truthy(env.get("PHASE11_1_5_2_TRAFFIC_VERIFIED")),
        },
        "approval": {
            "technical": truthy(env.get("PHASE11_1_5_2_TECHNICAL_APPROVED")),
            "business": truthy(env.get("PHASE11_1_5_2_BUSINESS_APPROVED")),
            "rollback": truthy(env.get("PHASE11_1_5_2_ROLLBACK_READY")),
            "monitoring": truthy(env.get("PHASE11_1_5_2_MONITORING_READY")),
        },
        "clients": [],
    }


def merge_packages(base, override):
    """Merge optional package data over environment/default data."""
    result = dict(base)
    for key in ("evidence", "approval"):
        result[key] = dict(base.get(key, {}))
        result[key].update(override.get(key, {}))
    result["clients"] = override.get("clients", base.get("clients", []))
    result["package_errors"] = override.get("package_errors", [])
    return result


def collect_evidence(log_paths=None, period=None, env=None, package=None):
    """Prefer explicit package evidence; otherwise analyze provided logs."""
    if package and package.get("evidence"):
        evidence = dict(package["evidence"])
        evidence.setdefault("status", "READY_FOR_DECOMMISSION" if evidence.get("safe_to_decommission") else "BLOCKED_SAFELY")
        evidence.setdefault("decision", evidence["status"])
        return evidence
    return evaluate_traffic_evidence(log_paths=log_paths, period=period, env=env)


def validate_evidence(evidence):
    """Validate traffic metrics required for shutdown readiness."""
    errors = []
    if not evidence.get("logs_provided"):
        errors.append("Production evidence logs are missing.")
    if evidence.get("legacy_requests") != 0:
        errors.append("Legacy API traffic must equal zero.")
    if evidence.get("replacement_requests", 0) <= 0:
        errors.append("Django `/api/v1/...` traffic must be active.")
    if evidence.get("unknown_clients") != 0:
        errors.append("Unknown clients must equal zero.")
    if not evidence.get("safe_to_decommission"):
        errors.append("Traffic validation is not safe for decommission.")
    return errors


def validate_approval(approval):
    """Validate technical, business, rollback and monitoring approvals."""
    errors = []
    if not truthy(approval.get("technical")):
        errors.append("Technical approval is missing.")
    if not truthy(approval.get("business")):
        errors.append("Business approval is missing.")
    if not truthy(approval.get("rollback")):
        errors.append("Rollback readiness is missing.")
    if not truthy(approval.get("monitoring")):
        errors.append("Monitoring readiness is missing.")
    return errors


def validate_clients(clients):
    """Validate client confirmations for all known client sources."""
    if not clients:
        return ["Client confirmation records are missing."]

    errors = []
    for index, client in enumerate(clients, start=1):
        name = client.get("client") or f"client #{index}"
        if client.get("legacy_api_usage") not in {"none", "0", 0, False}:
            errors.append(f"{name}: legacy API usage is not confirmed as zero.")
        if not client.get("replacement_api"):
            errors.append(f"{name}: replacement API is missing.")
        if not truthy(client.get("migration_completed")):
            errors.append(f"{name}: migration completion is not confirmed.")
        if not client.get("confirmation_date"):
            errors.append(f"{name}: confirmation date is missing.")
    return errors


def validate_evidence_approval(log_paths=None, period=None, env=None, package_path=None, package_data=None):
    """Validate final collected evidence and approval package."""
    started_at = time.perf_counter()
    env_package = read_env_package(env)
    file_package = package_data if package_data is not None else load_package(package_path)
    package = merge_packages(env_package, file_package)
    evidence = collect_evidence(log_paths=log_paths, period=period, env=env, package=package)
    approval = package.get("approval", {})
    clients = package.get("clients", [])

    errors = []
    errors.extend(package.get("package_errors", []))
    errors.extend(validate_evidence(evidence))
    errors.extend(validate_approval(approval))
    errors.extend(validate_clients(clients))

    ready = not errors
    return {
        "status": "READY_FOR_LEGACY_API_SHUTDOWN" if ready else "KEEP_LEGACY_API_ACTIVE",
        "ready_for_shutdown": ready,
        "legacy_routes_disabled": False,
        "proxy_modified": False,
        "routes_changed": False,
        "database_archived": False,
        "legacy_code_deleted": False,
        "evidence": evidence,
        "approval": approval,
        "clients_checked": len(clients),
        "errors": errors,
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
    }


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.5.2 evidence approval validator")
    parser.add_argument("--package", default=None, help="Optional JSON package with evidence, approval and clients.")
    parser.add_argument("--log", action="append", default=[], help="Production traffic log.")
    parser.add_argument("--period", default=None, help="Verification period.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when blocked.")
    args = parser.parse_args()
    result = validate_evidence_approval(
        log_paths=args.log,
        period=args.period,
        package_path=args.package,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["ready_for_shutdown"]:
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
