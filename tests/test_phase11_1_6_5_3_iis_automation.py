import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


SCRIPT_PATH = PROJECT_ROOT / "scripts" / "windows" / "Collect-IIS-Production-Evidence.ps1"


def read_script():
    return SCRIPT_PATH.read_text(encoding="utf-8")


def test_iis_not_installed_is_handled():
    content = read_script()

    assert "function Test-IISInstalled" in content
    assert "Import-Module WebAdministration" in content
    assert "IIS_NOT_DETECTED" in content
    assert "No IIS websites were detected." in content


def test_iis_logs_missing_is_reported():
    content = read_script()

    assert "function Get-RecentLogFiles" in content
    assert "No IIS log files were found in the selected collection window." in content
    assert "IIS_LOG_ROOT_MISSING" in content


def test_valid_log_detection_checks_required_w3c_fields():
    content = read_script()

    assert "function Test-W3CLogging" in content
    for field in ["date", "time", "c-ip", "cs-uri-stem", "sc-status", "cs(User-Agent)"]:
        assert field in content
    assert "W3C_LOGGING_VALID" in content


def test_metadata_generation_contains_required_fields():
    content = read_script()

    assert "function Write-Metadata" in content
    for field in [
        "server",
        "environment",
        "iis_site",
        "site_id",
        "collection_start",
        "collection_end",
        "operator",
        "reviewer",
    ]:
        assert re.search(rf"\b{field}\b", content)


def test_csv_generation_and_validator_are_wired():
    content = read_script()

    assert "export_iis_api_evidence.ps1" in content
    assert "iis_api_evidence.csv" in content
    assert "phase11_1_6_5_2_evidence_acceptance_validator.py" in content
    assert "COMPLETE_EVIDENCE_PACKAGE" in content
