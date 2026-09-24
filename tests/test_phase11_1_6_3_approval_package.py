import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase11_1_6_3_approval_validator import REQUIRED_DOCUMENTS, validate_approval_package


APPROVAL_VALUES = {
    "System owner": "Platform Owner",
    "Technical reviewer": "Senior Architect",
    "Evidence confirmation": "approved",
    "Risk assessment": "approved",
    "Rollback validation": "approved",
    "Business owner": "Business Owner",
    "Business impact review": "approved",
    "Customer impact assessment": "approved",
    "Downtime acceptance": "approved",
    "Rollback owner": "Ops Owner",
    "Backup owner": "Backup Ops",
    "Rollback procedure reference": "docs/migration/LEGACY_API_DECOMMISSION_ROLLBACK.md",
    "Contact information": "ops@example.com",
    "Planned execution date": "2026-07-26",
    "Start time": "22:00",
    "End time": "23:00",
    "Timezone": "Asia/Tokyo",
    "Expected impact": "Low",
    "Communication plan": "Support team notified",
    "Rollback decision time": "22:30",
    "Monitoring owner": "Monitoring Owner",
    "Monitoring tools": "APM and IIS logs",
    "API errors metric": "5xx rate",
    "Latency metric": "p95 latency",
    "Traffic metric": "request count",
    "HTTP status codes metric": "status code distribution",
    "Escalation path": "Ops to Architect",
    "Approval status": "approved",
    "Signature": "Signed",
    "Date": "2026-07-26",
}


def write_document(directory, filename, fields, overrides=None):
    overrides = overrides or {}
    lines = [f"# {filename}", ""]
    for field in fields:
        value = overrides.get(field, APPROVAL_VALUES.get(field, "approved"))
        lines.append(f"{field}: {value}")
        lines.append("")
    path = Path(directory) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_complete_package(directory, overrides_by_file=None):
    overrides_by_file = overrides_by_file or {}
    for config in REQUIRED_DOCUMENTS.values():
        write_document(
            directory,
            config["filename"],
            config["fields"],
            overrides=overrides_by_file.get(config["filename"]),
        )


def test_missing_approval_blocked(tmp_path):
    result = validate_approval_package(tmp_path)

    assert result["status"] == "APPROVAL_PENDING"
    assert result["approval_complete"] is False
    assert any("does not exist" in error for error in result["missing_information"])


def test_complete_approval_accepted(tmp_path):
    write_complete_package(tmp_path)

    result = validate_approval_package(tmp_path)

    assert result["status"] == "APPROVAL_COMPLETE"
    assert result["approval_complete"] is True
    assert result["execution_readiness"] == "READY_FOR_EXECUTION_APPROVAL"


def test_missing_owner_detected(tmp_path):
    write_complete_package(
        tmp_path,
        overrides_by_file={"ROLLBACK_OWNER.md": {"Rollback owner": "PENDING"}},
    )

    result = validate_approval_package(tmp_path)

    assert result["status"] == "APPROVAL_PENDING"
    assert any("rollback_owner: Rollback owner is missing or pending." in error for error in result["missing_information"])


def test_missing_maintenance_window_detected(tmp_path):
    write_complete_package(
        tmp_path,
        overrides_by_file={"MAINTENANCE_WINDOW.md": {"Start time": "PENDING"}},
    )

    result = validate_approval_package(tmp_path)

    assert result["status"] == "APPROVAL_PENDING"
    assert any("maintenance_window: Start time is missing or pending." in error for error in result["missing_information"])
