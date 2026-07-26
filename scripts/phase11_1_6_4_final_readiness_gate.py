"""Final readiness gate for Legacy API shutdown, Phase 11.1.6.4.

The gate combines production evidence, approval package, rollback readiness,
maintenance window and monitoring readiness. It only reads files and writes a
decision report. It does not execute shutdown, disable Legacy API, modify IIS,
change proxy/routes or modify databases.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

try:
    from scripts.phase11_1_6_3_approval_validator import (
        DEFAULT_APPROVAL_DIR,
        read_field,
        validate_approval_package,
    )
except ModuleNotFoundError:
    from phase11_1_6_3_approval_validator import DEFAULT_APPROVAL_DIR, read_field, validate_approval_package


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_REPORT = (
    PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "reports"
    / "REAL_PRODUCTION_EVIDENCE_REPORT.json"
)
DEFAULT_ROLLBACK_PROCEDURE = PROJECT_ROOT / "docs" / "migration" / "LEGACY_API_DECOMMISSION_ROLLBACK.md"
DEFAULT_ROLLBACK_CHECKPOINT = (
    PROJECT_ROOT
    / "docs"
    / "migration"
    / "phase11_1_6_execution"
    / "LEGACY_API_DECOMMISSION_ROLLBACK_CHECKPOINT.json"
)
DEFAULT_STATUS_OUTPUT = (
    PROJECT_ROOT
    / "docs"
    / "migration"
    / "phase11_1_6_execution"
    / "FINAL_READINESS_STATUS.json"
)

REQUIRED_MONITORING_FIELDS = [
    "Monitoring owner",
    "Monitoring tools",
    "API errors metric",
    "Latency metric",
    "Traffic metric",
    "HTTP status codes metric",
    "Escalation path",
]


def load_json(path):
    """Load a JSON file and return fallback errors when invalid."""
    json_path = Path(path)
    if not json_path.exists():
        return None, [f"JSON file does not exist: {json_path}."]
    try:
        return json.loads(json_path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [f"JSON file is invalid: {json_path}: {exc}."]


def meaningful(value):
    """Return True when an approval field has non-placeholder content."""
    return str(value or "").strip().lower() not in {"", "pending", "tbd", "missing", "not_provided", "not provided"}


def validate_evidence_gate(evidence_report=None):
    """Validate production evidence readiness."""
    evidence_path = Path(evidence_report or DEFAULT_EVIDENCE_REPORT)
    evidence, errors = load_json(evidence_path)
    evidence = evidence or {}
    legacy_count = int(evidence.get("legacy_requests") or 0)
    django_count = int(evidence.get("django_requests") or evidence.get("replacement_requests") or 0)
    unknown_clients = int(evidence.get("unknown_clients") or 0)

    if evidence.get("status") != "COMPLETE_EVIDENCE_PACKAGE":
        errors.append("Evidence status is not COMPLETE_EVIDENCE_PACKAGE.")
    if legacy_count != 0:
        errors.append("Legacy `/api/*` request count is not 0.")
    if django_count <= 0:
        errors.append("Django `/api/v1/*` request count is not greater than 0.")
    if unknown_clients != 0:
        errors.append("Unknown client count is not 0.")
    if evidence.get("routes_changed") or evidence.get("proxy_modified") or evidence.get("shutdown_executed"):
        errors.append("Evidence indicates route/proxy/shutdown changes already occurred.")

    return {
        "status": "PASS" if not errors else "FAIL",
        "path": str(evidence_path),
        "evidence_status": evidence.get("status", "UNKNOWN"),
        "legacy_requests": legacy_count,
        "django_requests": django_count,
        "unknown_clients": unknown_clients,
        "errors": errors,
    }


def validate_approval_gate(approval_dir=None):
    """Validate formal approval package readiness."""
    approval_result = validate_approval_package(approval_dir=approval_dir)
    return {
        "status": "PASS" if approval_result["status"] == "APPROVAL_COMPLETE" else "FAIL",
        "approval_status": approval_result["status"],
        "approval_complete": approval_result["approval_complete"],
        "approval_dir": approval_result["approval_dir"],
        "errors": approval_result["missing_information"],
        "documents": approval_result["documents"],
    }


def validate_rollback_gate(approval_gate=None, rollback_procedure=None, rollback_checkpoint=None):
    """Validate rollback procedure, owner and checkpoint readiness."""
    procedure = Path(rollback_procedure or DEFAULT_ROLLBACK_PROCEDURE)
    checkpoint = Path(rollback_checkpoint or DEFAULT_ROLLBACK_CHECKPOINT)
    errors = []

    if not procedure.exists():
        errors.append(f"Rollback procedure does not exist: {procedure}.")
    if not checkpoint.exists():
        errors.append(f"Rollback checkpoint does not exist: {checkpoint}.")

    rollback_document = (approval_gate or {}).get("documents", {}).get("rollback_owner", {})
    rollback_fields = rollback_document.get("fields", {})
    if not rollback_document.get("complete"):
        errors.append("Rollback owner approval document is not complete.")
    if not meaningful(rollback_fields.get("Rollback owner")):
        errors.append("Rollback owner is not assigned.")

    return {
        "status": "PASS" if not errors else "FAIL",
        "rollback_procedure": str(procedure),
        "rollback_checkpoint": str(checkpoint),
        "rollback_owner": rollback_fields.get("Rollback owner") or None,
        "errors": errors,
    }


def validate_maintenance_gate(approval_gate=None):
    """Validate maintenance window assignment."""
    maintenance_document = (approval_gate or {}).get("documents", {}).get("maintenance_window", {})
    fields = maintenance_document.get("fields", {})
    errors = []
    for field in ["Planned execution date", "Start time", "End time", "Timezone", "Rollback decision time"]:
        if not meaningful(fields.get(field)):
            errors.append(f"{field} is not assigned.")
    if not maintenance_document.get("complete"):
        errors.append("Maintenance window approval document is not complete.")
    return {
        "status": "PASS" if not errors else "FAIL",
        "fields": fields,
        "errors": errors,
    }


def validate_monitoring_gate(approval_dir=None, approval_gate=None):
    """Validate monitoring owner and required metrics."""
    approval_directory = Path(approval_dir or DEFAULT_APPROVAL_DIR)
    monitoring_path = approval_directory / "MONITORING_OWNER.md"
    errors = []
    fields = {}

    if not monitoring_path.exists():
        errors.append(f"Monitoring owner document does not exist: {monitoring_path}.")
    else:
        content = monitoring_path.read_text(encoding="utf-8", errors="ignore")
        fields = {field: read_field(content, field) for field in REQUIRED_MONITORING_FIELDS}
        for field, value in fields.items():
            if not meaningful(value):
                errors.append(f"{field} is not assigned.")

    monitoring_document = (approval_gate or {}).get("documents", {}).get("monitoring_owner", {})
    if not monitoring_document.get("complete"):
        errors.append("Monitoring owner approval document is not complete.")

    return {
        "status": "PASS" if not errors else "FAIL",
        "path": str(monitoring_path),
        "fields": fields,
        "errors": errors,
    }


def evaluate_final_readiness(
    evidence_report=None,
    approval_dir=None,
    rollback_procedure=None,
    rollback_checkpoint=None,
    output_path=None,
):
    """Evaluate all final readiness gates and write JSON status."""
    started_at = time.perf_counter()
    evidence = validate_evidence_gate(evidence_report=evidence_report)
    approval = validate_approval_gate(approval_dir=approval_dir)
    rollback = validate_rollback_gate(
        approval_gate=approval,
        rollback_procedure=rollback_procedure,
        rollback_checkpoint=rollback_checkpoint,
    )
    maintenance = validate_maintenance_gate(approval_gate=approval)
    monitoring = validate_monitoring_gate(approval_dir=approval_dir, approval_gate=approval)

    gates = {
        "evidence": evidence,
        "approval": approval,
        "rollback": rollback,
        "maintenance": maintenance,
        "monitoring": monitoring,
    }
    decision = "READY_TO_EXECUTE" if all(gate["status"] == "PASS" for gate in gates.values()) else "BLOCKED_SAFELY"
    result = {
        "evidence": evidence["status"],
        "approval": approval["status"],
        "rollback": rollback["status"],
        "maintenance": maintenance["status"],
        "monitoring": monitoring["status"],
        "decision": decision,
        "gates": gates,
        "safety": {
            "shutdown_executed": False,
            "legacy_api_disabled": False,
            "iis_modified": False,
            "proxy_modified": False,
            "routes_changed": False,
            "database_modified": False,
        },
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
    }

    destination = Path(output_path or DEFAULT_STATUS_OUTPUT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.6.4 final readiness gate")
    parser.add_argument("--evidence-report", default=None, help="Production evidence JSON report.")
    parser.add_argument("--approval-dir", default=None, help="Approval package directory.")
    parser.add_argument("--rollback-procedure", default=None, help="Rollback procedure document.")
    parser.add_argument("--rollback-checkpoint", default=None, help="Rollback checkpoint JSON.")
    parser.add_argument("--output", default=None, help="Final readiness JSON output path.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when readiness is blocked. Default blocked state exits 0.",
    )
    args = parser.parse_args()
    result = evaluate_final_readiness(
        evidence_report=args.evidence_report,
        approval_dir=args.approval_dir,
        rollback_procedure=args.rollback_procedure,
        rollback_checkpoint=args.rollback_checkpoint,
        output_path=args.output,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["decision"] == "READY_TO_EXECUTE":
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
