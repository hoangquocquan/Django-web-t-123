import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase12_3_health_check import run_health_check
from tests.legacy_sqlite_helpers import (
    create_legacy_sqlite_fixture,
    django_sqlite_database_config,
)


MONITORING_DIR = PROJECT_ROOT / "docs" / "monitoring"
REVIEW_DIR = PROJECT_ROOT / "docs" / "reviews"
HEALTH_RESULT = MONITORING_DIR / "health_check_result.json"


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def test_health_check_works(tmp_path, monkeypatch, settings):
    database = create_legacy_sqlite_fixture(tmp_path / "legacy.sqlite")
    monkeypatch.setitem(
        settings.DATABASES,
        "legacy",
        django_sqlite_database_config(database),
    )
    result = run_health_check(output_path=tmp_path / "health.json")

    assert result["status"] == "HEALTHY"
    assert result["production_modified"] is False
    assert result["routes_changed"] is False
    assert result["database_schema_changed"] is False
    assert result["component_count"] >= 5


def test_health_check_result_file_exists():
    assert HEALTH_RESULT.exists()
    payload = json.loads(HEALTH_RESULT.read_text(encoding="utf-8"))

    assert payload["phase"] == "12.3"
    assert payload["status"] == "HEALTHY"


def test_metrics_document_exists():
    path = MONITORING_DIR / "METRICS_CATALOG.md"

    assert path.exists()
    content = read_text(path)
    assert "request_count" in content
    assert "response_latency_ms" in content
    assert "query_latency_ms" in content


def test_alert_rules_exist():
    path = MONITORING_DIR / "ALERT_RULES.md"

    assert path.exists()
    content = read_text(path)
    assert "API unavailable" in content
    assert "Database unavailable" in content
    assert "High latency" in content


def test_monitoring_report_generated():
    path = REVIEW_DIR / "PHASE_12.3_MONITORING_REPORT.md"

    assert path.exists()
    content = read_text(path)
    assert "MONITORING_FOUNDATION_COMPLETE" in content
    assert "No production monitoring agent deployed" in content

