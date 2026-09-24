import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase11_1_6_8_training_legacy_shutdown import execute_training_shutdown
from scripts.phase11_1_6_8_training_rollback import execute_training_rollback


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def training_status(evidence_status="TRAINING_ONLY", simulation=True):
    return {
        "decision": "READY_TO_EXECUTE_TRAINING",
        "gates": {
            "evidence": {
                "evidence_status": evidence_status,
                "simulation": simulation,
                "legacy_requests": 0,
                "django_requests": 12,
                "unknown_clients": 0,
            }
        },
        "safety": {
            "shutdown_executed": False,
            "legacy_api_disabled": False,
        },
    }


def production_status(decision="BLOCKED_SAFELY"):
    return {
        "decision": decision,
        "safety": {
            "shutdown_executed": False,
            "legacy_api_disabled": False,
            "iis_modified": False,
            "proxy_modified": False,
            "routes_changed": False,
            "database_modified": False,
        },
    }


def run_shutdown(tmp_path, training_payload=None, production_payload=None):
    training_file = write_json(tmp_path / "training-status.json", training_payload or training_status())
    production_file = write_json(tmp_path / "production-status.json", production_payload or production_status())
    return execute_training_shutdown(
        training_status_path=training_file,
        production_status_path=production_file,
        training_state_path=tmp_path / "training-state.json",
        checkpoint_path=tmp_path / "checkpoint.json",
        shutdown_result_path=tmp_path / "shutdown-result.json",
        traffic_verification_path=tmp_path / "traffic.md",
        execution_report_path=tmp_path / "report.md",
    )


def test_training_only_protection(tmp_path):
    result = run_shutdown(tmp_path, training_payload=training_status(evidence_status="COMPLETE_EVIDENCE_PACKAGE"))

    assert result["status"] == "TRAINING_SHUTDOWN_FAILED"
    assert "Training evidence status is not TRAINING_ONLY." in result["precheck"]["errors"]


def test_legacy_disabled_after_training_shutdown(tmp_path):
    result = run_shutdown(tmp_path)

    assert result["status"] == "TRAINING_SHUTDOWN_SUCCESS"
    assert result["training_legacy_disabled"] is True
    assert result["after_state"]["legacy_available"] is False


def test_django_api_remains_active(tmp_path):
    result = run_shutdown(tmp_path)

    assert result["api_v1_active"] is True
    assert result["after_state"]["replacement_available"] is True


def test_rollback_restores_training_legacy_route(tmp_path):
    run_shutdown(tmp_path)
    rollback = execute_training_rollback(
        checkpoint_path=tmp_path / "checkpoint.json",
        training_state_path=tmp_path / "training-state.json",
        rollback_result_path=tmp_path / "rollback.md",
    )
    state = json.loads((tmp_path / "training-state.json").read_text(encoding="utf-8"))

    assert rollback["status"] == "TRAINING_ROLLBACK_SUCCESS"
    assert state["legacy_available"] is True
    assert state["replacement_available"] is True


def test_production_shutdown_blocked(tmp_path):
    result = run_shutdown(tmp_path, production_payload=production_status(decision="READY_TO_EXECUTE_PRODUCTION"))

    assert result["status"] == "TRAINING_SHUTDOWN_FAILED"
    assert "Production readiness is not BLOCKED_SAFELY." in result["precheck"]["errors"]
    assert result["safety"]["production_shutdown_executed"] is False
