"""Kiểm tra Final Readiness Gate bằng dữ liệu mô phỏng cho Phase 11.1.6.4.1.

Script này chỉ phục vụ diễn tập quy trình. Nó không tắt Legacy API, không sửa
IIS, không sửa proxy, không đổi route và không chạm vào database.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

try:
    from scripts.phase11_1_6_3_approval_validator import DEFAULT_APPROVAL_DIR
    from scripts.phase11_1_6_4_final_readiness_gate import (
        DEFAULT_ROLLBACK_CHECKPOINT,
        DEFAULT_ROLLBACK_PROCEDURE,
        REQUIRED_MONITORING_FIELDS,
        evaluate_final_readiness,
        load_json,
    )
except ModuleNotFoundError:
    from phase11_1_6_3_approval_validator import DEFAULT_APPROVAL_DIR
    from phase11_1_6_4_final_readiness_gate import (
        DEFAULT_ROLLBACK_CHECKPOINT,
        DEFAULT_ROLLBACK_PROCEDURE,
        REQUIRED_MONITORING_FIELDS,
        evaluate_final_readiness,
        load_json,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRAINING_STATUS_OUTPUT = (
    PROJECT_ROOT
    / "docs"
    / "migration"
    / "phase11_1_6_execution"
    / "FINAL_READINESS_SIMULATION_STATUS.json"
)
DEFAULT_SIMULATION_EVIDENCE_REPORT = (
    PROJECT_ROOT
    / "docs"
    / "migration"
    / "production_evidence"
    / "reports"
    / "SIMULATION_PRODUCTION_EVIDENCE_REPORT.json"
)
DEFAULT_REVIEW_OUTPUT = PROJECT_ROOT / "docs" / "reviews" / "PHASE_11.1.6.4.1_SIMULATION_READINESS_REPORT.md"
DEFAULT_RUNBOOK = PROJECT_ROOT / "docs" / "migration" / "LEGACY_API_DECOMMISSION_EXECUTION_RUNBOOK.md"


def _path_exists(path):
    """Trả về True nếu file tồn tại; tách hàm nhỏ để test đọc dễ hơn."""
    return Path(path).exists()


def _json_has_keys(path, required_keys):
    """Kiểm tra file JSON có đọc được và có các khóa quan trọng hay không."""
    payload, errors = load_json(path)
    if errors:
        return False, errors

    missing = [key for key in required_keys if key not in (payload or {})]
    if missing:
        return False, [f"Missing JSON keys: {', '.join(missing)}."]
    return True, []


def validate_training_rollback(rollback_procedure=None, rollback_checkpoint=None):
    """Kiểm tra rollback cho diễn tập, chỉ yêu cầu tài liệu và checkpoint có sẵn.

    Gate thật trong production còn cần rollback owner ký duyệt. Phase này không
    sửa approval thật, nên phần owner được tính vào approval simulation.
    """
    procedure = Path(rollback_procedure or DEFAULT_ROLLBACK_PROCEDURE)
    checkpoint = Path(rollback_checkpoint or DEFAULT_ROLLBACK_CHECKPOINT)
    errors = []

    if not _path_exists(procedure):
        errors.append(f"Rollback procedure does not exist: {procedure}.")
    else:
        content = procedure.read_text(encoding="utf-8", errors="ignore").lower()
        if "rollback steps" not in content:
            errors.append("Rollback procedure does not contain a rollback steps section.")

    valid_checkpoint, checkpoint_errors = _json_has_keys(
        checkpoint,
        ["rollback_route", "replacement_route", "restore_action"],
    )
    if not valid_checkpoint:
        errors.extend(checkpoint_errors)

    return {
        "status": "PASS" if not errors else "FAIL",
        "rollback_procedure": str(procedure),
        "rollback_checkpoint": str(checkpoint),
        "errors": errors,
    }


def validate_training_monitoring(approval_dir=None, runbook_path=None):
    """Kiểm tra checklist monitoring cho diễn tập.

    Trong phase này, các trường có thể vẫn là PENDING vì chưa có người ký thật.
    Điều cần xác nhận là checklist và các metric cần theo dõi đã được định nghĩa.
    """
    approval_directory = Path(approval_dir or DEFAULT_APPROVAL_DIR)
    monitoring_template = approval_directory / "MONITORING_OWNER.md"
    runbook = Path(runbook_path or DEFAULT_RUNBOOK)
    errors = []

    if not monitoring_template.exists():
        errors.append(f"Monitoring checklist does not exist: {monitoring_template}.")
        template_content = ""
    else:
        template_content = monitoring_template.read_text(encoding="utf-8", errors="ignore")

    missing_fields = [field for field in REQUIRED_MONITORING_FIELDS if f"{field}:" not in template_content]
    if missing_fields:
        errors.append(f"Monitoring checklist misses fields: {', '.join(missing_fields)}.")

    if not runbook.exists():
        errors.append(f"Execution runbook does not exist: {runbook}.")
        runbook_content = ""
    else:
        runbook_content = runbook.read_text(encoding="utf-8", errors="ignore").lower()

    required_runbook_terms = ["legacy `/api/*`", "replacement `/api/v1/*`", "error rate", "latency", "unknown clients"]
    missing_terms = [term for term in required_runbook_terms if term.lower() not in runbook_content]
    if missing_terms:
        errors.append(f"Monitoring runbook misses terms: {', '.join(missing_terms)}.")

    return {
        "status": "PASS" if not errors else "FAIL",
        "monitoring_checklist": str(monitoring_template),
        "monitoring_metrics": REQUIRED_MONITORING_FIELDS,
        "runbook": str(runbook),
        "errors": errors,
    }


def build_training_readiness(
    evidence_report=None,
    approval_dir=None,
    rollback_procedure=None,
    rollback_checkpoint=None,
    status_output=None,
    review_output=None,
    runbook_path=None,
):
    """Tổng hợp gate gốc và gate diễn tập thành quyết định training."""
    started_at = time.perf_counter()
    evidence_path = Path(evidence_report or DEFAULT_SIMULATION_EVIDENCE_REPORT)
    with tempfile.TemporaryDirectory() as temporary_directory:
        raw_status_output = Path(temporary_directory) / "FINAL_READINESS_STATUS_FOR_SIMULATION.json"
        final_gate = evaluate_final_readiness(
            evidence_report=evidence_path,
            approval_dir=approval_dir,
            rollback_procedure=rollback_procedure,
            rollback_checkpoint=rollback_checkpoint,
            output_path=raw_status_output,
            readiness_mode="training",
        )

    evidence_payload, evidence_errors = load_json(evidence_path)
    evidence_payload = evidence_payload or {}
    evidence_simulation_ok = bool(evidence_payload.get("simulation")) and evidence_payload.get("environment") == "STAGING_SIMULATION"

    evidence_errors = list(evidence_errors)
    if final_gate["evidence"] != "PASS":
        evidence_errors.extend(final_gate["gates"]["evidence"]["errors"])
    if not evidence_simulation_ok:
        evidence_errors.append("Evidence is not marked as STAGING_SIMULATION.")

    evidence = {
        "status": "PASS" if not evidence_errors else "FAIL",
        "source_gate_status": final_gate["evidence"],
        "evidence_status": evidence_payload.get("status", "UNKNOWN"),
        "environment": evidence_payload.get("environment", "UNKNOWN"),
        "simulation": bool(evidence_payload.get("simulation")),
        "legacy_requests": final_gate["gates"]["evidence"]["legacy_requests"],
        "django_requests": final_gate["gates"]["evidence"]["django_requests"],
        "unknown_clients": final_gate["gates"]["evidence"]["unknown_clients"],
        "errors": evidence_errors,
    }

    approval_simulation = {
        "status": "TRAINING_APPROVAL_SIMULATION" if final_gate["approval"] != "PASS" else "APPROVAL_COMPLETE",
        "source_gate_status": final_gate["approval"],
        "real_approval_modified": False,
        "unsigned_or_pending_items": len(final_gate["gates"]["approval"].get("errors", [])),
        "note": "Approval templates are not changed during this training simulation.",
    }

    rollback = validate_training_rollback(
        rollback_procedure=rollback_procedure,
        rollback_checkpoint=rollback_checkpoint,
    )
    monitoring = validate_training_monitoring(approval_dir=approval_dir, runbook_path=runbook_path)

    ready_for_training = (
        evidence["status"] == "PASS"
        and rollback["status"] == "PASS"
        and monitoring["status"] == "PASS"
        and approval_simulation["status"] in {"TRAINING_APPROVAL_SIMULATION", "APPROVAL_COMPLETE"}
    )
    decision = "READY_TO_EXECUTE_TRAINING" if ready_for_training else "BLOCKED_SAFELY"

    result = {
        "evidence": evidence["status"],
        "approval_simulation": approval_simulation["status"],
        "rollback": rollback["status"],
        "monitoring": monitoring["status"],
        "decision": decision,
        "gates": {
            "evidence": evidence,
            "approval_simulation": approval_simulation,
            "rollback": rollback,
            "monitoring": monitoring,
        },
        "safety": {
            "shutdown_executed": False,
            "legacy_api_disabled": False,
            "iis_modified": False,
            "proxy_modified": False,
            "routes_changed": False,
            "database_modified": False,
            "production_configuration_changed": False,
            "real_approval_modified": False,
        },
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
    }

    status_path = Path(status_output or DEFAULT_TRAINING_STATUS_OUTPUT)
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    review_path = Path(review_output or DEFAULT_REVIEW_OUTPUT)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(render_review_report(result), encoding="utf-8")
    result["review_report"] = str(review_path)
    result["status_report"] = str(status_path)
    return result


def render_review_report(result):
    """Tạo báo cáo Markdown ngắn gọn để reviewer đọc nhanh."""
    evidence = result["gates"]["evidence"]
    approval = result["gates"]["approval_simulation"]
    rollback = result["gates"]["rollback"]
    monitoring = result["gates"]["monitoring"]

    return f"""# Phase 11.1.6.4.1 Simulation Readiness Report

## Phase

Phase 11.1.6.4.1 - Final Readiness Gate Simulation Validation

## Scope

This report validates the final readiness workflow with `STAGING_SIMULATION`
traffic evidence only. It does not approve or execute production Legacy API
shutdown.

## Evidence Result

| Check | Result |
| --- | --- |
| Evidence status | `{evidence["evidence_status"]}` |
| Environment | `{evidence["environment"]}` |
| Simulation flag | `{evidence["simulation"]}` |
| Legacy `/api/*` traffic | `{evidence["legacy_requests"]}` |
| Django `/api/v1/*` traffic | `{evidence["django_requests"]}` |
| Unknown clients | `{evidence["unknown_clients"]}` |
| Gate result | `{evidence["status"]}` |

## Approval Simulation Result

| Check | Result |
| --- | --- |
| Source approval gate | `{approval["source_gate_status"]}` |
| Training approval result | `{approval["status"]}` |
| Pending approval items | `{approval["unsigned_or_pending_items"]}` |
| Real approval modified | `{approval["real_approval_modified"]}` |

Unsigned approval templates remain pending by design. This phase only validates
the training path.

## Rollback Readiness

| Check | Result |
| --- | --- |
| Rollback result | `{rollback["status"]}` |
| Rollback procedure | `{rollback["rollback_procedure"]}` |
| Rollback checkpoint | `{rollback["rollback_checkpoint"]}` |

## Monitoring Readiness

| Check | Result |
| --- | --- |
| Monitoring result | `{monitoring["status"]}` |
| Monitoring checklist | `{monitoring["monitoring_checklist"]}` |
| Runbook | `{monitoring["runbook"]}` |
| Metrics defined | `{", ".join(monitoring["monitoring_metrics"])}` |

## Safety Confirmation

| Safety item | Value |
| --- | --- |
| Shutdown executed | `{result["safety"]["shutdown_executed"]}` |
| Legacy API disabled | `{result["safety"]["legacy_api_disabled"]}` |
| IIS modified | `{result["safety"]["iis_modified"]}` |
| Proxy modified | `{result["safety"]["proxy_modified"]}` |
| Routes changed | `{result["safety"]["routes_changed"]}` |
| Database modified | `{result["safety"]["database_modified"]}` |
| Real approval modified | `{result["safety"]["real_approval_modified"]}` |

## Final Decision

`{result["decision"]}`

## Next Step

Use this result for training shutdown validation only. Real production shutdown
still requires real IIS production evidence and signed approvals.
"""


def main():
    """Entry point dòng lệnh cho phase 11.1.6.4.1."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.1.6.4.1 readiness simulation validator")
    parser.add_argument("--evidence-report", default=None, help="Simulation evidence JSON report.")
    parser.add_argument("--approval-dir", default=None, help="Approval directory. Real files are read only.")
    parser.add_argument("--rollback-procedure", default=None, help="Rollback procedure document.")
    parser.add_argument("--rollback-checkpoint", default=None, help="Rollback checkpoint JSON.")
    parser.add_argument("--status-output", default=None, help="Training status JSON output.")
    parser.add_argument("--review-output", default=None, help="Training review Markdown output.")
    parser.add_argument("--runbook", default=None, help="Execution runbook document.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when training readiness is blocked. Default blocked state exits 0.",
    )
    args = parser.parse_args()

    result = build_training_readiness(
        evidence_report=args.evidence_report,
        approval_dir=args.approval_dir,
        rollback_procedure=args.rollback_procedure,
        rollback_checkpoint=args.rollback_checkpoint,
        status_output=args.status_output,
        review_output=args.review_output,
        runbook_path=args.runbook,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["decision"] == "READY_TO_EXECUTE_TRAINING":
        return 0
    return 2 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
