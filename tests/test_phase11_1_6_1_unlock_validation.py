import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase11_1_6_1_approval_validator import validate_approval_package
from scripts.phase11_1_6_1_final_evidence_validator import evaluate_final_evidence


COMPLETE_EVIDENCE = {
    "status": "COMPLETE_EVIDENCE_PACKAGE",
    "ready_for_shutdown": True,
    "environment": "production",
    "simulation": False,
    "source": "iis_w3c_logs_and_csv",
    "collection_period": "2026-07-20 to 2026-07-26",
    "approved_by": "ops-owner",
    "legacy_requests": 0,
    "django_requests": 20,
    "unknown_clients": 0,
    "routes_changed": False,
    "proxy_modified": False,
    "legacy_code_removed": False,
    "database_archived": False,
    "errors": [],
}


def write_approval_file(directory, filename, owner="Owner Name", status="approved"):
    path = Path(directory) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"# {filename}",
                "",
                f"Owner: {owner}",
                "",
                "Date: 2026-07-26",
                "",
                f"Approval status: {status}",
                "",
                f"Signature: {owner}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def write_complete_approval_package(directory):
    for filename in [
        "TECHNICAL_APPROVAL.md",
        "BUSINESS_APPROVAL.md",
        "ROLLBACK_OWNER.md",
        "MAINTENANCE_WINDOW.md",
        "MONITORING_OWNER.md",
    ]:
        write_approval_file(directory, filename)


def test_missing_evidence_blocked():
    result = evaluate_final_evidence(evidence={"status": "INCOMPLETE_EVIDENCE_PACKAGE"})

    assert result["status"] == "BLOCKED_SAFELY"
    assert result["evidence_ready"] is False
    assert "Evidence status must be COMPLETE_EVIDENCE_PACKAGE." in result["errors"]


def test_missing_approval_blocked(tmp_path):
    write_approval_file(tmp_path, "TECHNICAL_APPROVAL.md")

    result = validate_approval_package(tmp_path)

    assert result["status"] == "APPROVAL_PENDING"
    assert result["approval_complete"] is False
    assert any("business_approval" in error for error in result["errors"])


def test_complete_package_accepted(tmp_path):
    write_complete_approval_package(tmp_path)

    evidence_result = evaluate_final_evidence(evidence=COMPLETE_EVIDENCE)
    approval_result = validate_approval_package(tmp_path)

    assert evidence_result["status"] == "READY_FOR_EXECUTION"
    assert evidence_result["evidence_ready"] is True
    assert approval_result["status"] == "APPROVAL_COMPLETE"
    assert approval_result["approval_complete"] is True


def test_unknown_client_detected():
    evidence = COMPLETE_EVIDENCE.copy()
    evidence["unknown_clients"] = 1

    result = evaluate_final_evidence(evidence=evidence)

    assert result["status"] == "BLOCKED_SAFELY"
    assert "Unknown clients must be 0." in result["errors"]
