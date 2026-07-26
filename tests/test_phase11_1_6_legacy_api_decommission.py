import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase11_1_6_execute_legacy_api_decommission import (
    execute_legacy_api_decommission,
    verify_post_shutdown_state,
)
from scripts.phase11_1_6_pre_shutdown_validation import evaluate_pre_shutdown_validation
from scripts.phase11_1_6_rollback_legacy_api import create_rollback_report


COMPLETE_EVIDENCE = {
    "status": "COMPLETE_EVIDENCE_PACKAGE",
    "ready_for_shutdown": True,
    "environment": "production",
    "simulation": False,
    "source": "iis_w3c_logs_and_csv",
    "collection_period": "2026-07-20 to 2026-07-26",
    "approved_by": "ops-owner",
    "legacy_requests": 0,
    "django_requests": 12,
    "unknown_clients": 0,
    "routes_changed": False,
    "proxy_modified": False,
    "errors": [],
}


APPROVED_ENV = {
    "PHASE11_1_6_TECHNICAL_APPROVAL": "approved",
    "PHASE11_1_6_BUSINESS_APPROVAL": "approved",
    "PHASE11_1_6_ROLLBACK_OWNER": "ops-owner",
    "PHASE11_1_6_MAINTENANCE_WINDOW": "approved",
    "PHASE11_1_6_MONITORING_READY": "approved",
}


def test_missing_evidence_is_blocked():
    result = evaluate_pre_shutdown_validation(evidence={"status": "INCOMPLETE_EVIDENCE_PACKAGE"}, env=APPROVED_ENV)

    assert result["status"] == "BLOCKED_SAFELY"
    assert result["execution_allowed"] is False
    assert "Production evidence is not COMPLETE_EVIDENCE_PACKAGE." in result["errors"]


def test_missing_approval_is_blocked():
    result = evaluate_pre_shutdown_validation(evidence=COMPLETE_EVIDENCE, env={})

    assert result["status"] == "BLOCKED_SAFELY"
    assert result["approval_status"] == "PENDING_OR_INCOMPLETE"
    assert any("Approval document" in error for error in result["errors"])


def test_complete_evidence_and_approval_is_ready_to_execute():
    result = evaluate_pre_shutdown_validation(evidence=COMPLETE_EVIDENCE, env=APPROVED_ENV)

    assert result["status"] == "READY_TO_EXECUTE"
    assert result["execution_allowed"] is True
    assert result["approval_status"] == "APPROVED"


def test_legacy_route_shutdown_validation():
    result = verify_post_shutdown_state({"legacy_available": False, "replacement_available": True})

    assert result["valid"] is True
    assert result["legacy_route_unavailable"] is True
    assert result["replacement_api_available"] is True


def test_django_route_must_remain_active():
    result = verify_post_shutdown_state({"legacy_available": False, "replacement_available": False})

    assert result["valid"] is False
    assert "Replacement `/api/v1/*` route is unavailable or was not verified." in result["errors"]


def test_execution_is_blocked_without_approval(tmp_path):
    result = execute_legacy_api_decommission(
        env={},
        output_dir=tmp_path,
        route_state={"legacy_available": False, "replacement_available": True},
    )

    assert result["status"] == "BLOCKED_SAFELY"
    assert result["execution_status"] == "NOT_EXECUTED"
    assert result["execution_record"]["legacy_routes_disabled_by_script"] is False
    assert Path(result["artifacts"]["execution_record"]).exists()


def test_execution_framework_keeps_django_route_active_when_ready(tmp_path):
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps(COMPLETE_EVIDENCE), encoding="utf-8")

    result = execute_legacy_api_decommission(
        evidence_report_path=evidence_path,
        env=APPROVED_ENV,
        output_dir=tmp_path,
        route_state={"legacy_available": False, "replacement_available": True},
    )

    assert result["status"] == "READY_TO_EXECUTE"
    assert result["execution_status"] == "AWAITING_APPROVED_PRODUCTION_ROUTE_CHANGE"
    assert result["post_shutdown_validation"]["replacement_api_available"] is True
    assert result["execution_record"]["api_v1_kept_active"] is True


def test_rollback_report_is_available_after_checkpoint(tmp_path):
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(
        json.dumps(
            {
                "rollback_route": "/api/*",
                "replacement_route": "/api/v1/*",
                "restore_action": "restore_previous_router_or_proxy_rule",
            }
        ),
        encoding="utf-8",
    )

    report_path = tmp_path / "rollback_report.json"
    result = create_rollback_report(checkpoint_path=checkpoint, report_path=report_path)

    assert result["status"] == "ROLLBACK_READY"
    assert result["rollback_available"] is True
    assert report_path.exists()
