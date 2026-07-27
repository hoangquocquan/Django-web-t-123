import json
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase12_2_api_benchmark import GET_SCENARIOS, run_benchmark
from scripts.phase12_2_database_performance_check import run_database_check
from tests.performance.phase12_2_load_test import run_load_scenario


API_RESULT = PROJECT_ROOT / "docs" / "performance" / "api_benchmark_result.json"
DB_REPORT = PROJECT_ROOT / "docs" / "performance" / "database_performance_report.md"
DB_RESULT = PROJECT_ROOT / "docs" / "performance" / "database_performance_result.json"
PERFORMANCE_REPORT = PROJECT_ROOT / "docs" / "reviews" / "PHASE_12.2_PERFORMANCE_REPORT.md"
ROADMAP = PROJECT_ROOT / "docs" / "reviews" / "PHASE_12.2_OPTIMIZATION_ROADMAP.md"
PLAN = PROJECT_ROOT / "docs" / "reviews" / "PHASE_12.2_PERFORMANCE_TEST_PLAN.md"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_benchmark_output_exists():
    assert API_RESULT.exists()
    payload = read_json(API_RESULT)

    assert payload["request_count"] > 0
    assert payload["status"] == "API_BENCHMARK_COMPLETE"


def test_performance_reports_generated():
    for report in [PLAN, DB_REPORT, PERFORMANCE_REPORT, ROADMAP]:
        assert report.exists(), f"Missing performance report: {report}"
        assert report.stat().st_size > 0


def test_metrics_collected():
    api_payload = read_json(API_RESULT)
    db_payload = read_json(DB_RESULT)

    assert api_payload["average_latency_ms"] >= 0
    assert api_payload["p95_latency_ms"] >= 0
    assert api_payload["p99_latency_ms"] >= 0
    assert api_payload["throughput_requests_per_second"] > 0
    assert db_payload["query_count"] > 0
    assert db_payload["average_query_ms"] >= 0


def test_no_production_modification():
    api_payload = read_json(API_RESULT)
    db_payload = read_json(DB_RESULT)

    assert api_payload["production_modified"] is False
    assert api_payload["routes_changed"] is False
    assert api_payload["database_schema_changed"] is False
    assert db_payload["production_modified"] is False
    assert db_payload["database_schema_changed"] is False


@pytest.mark.django_db(databases="__all__")
def test_benchmark_helpers_can_run_in_isolation(tmp_path):
    api_result = run_benchmark(iterations=1, output_path=tmp_path / "api.json", scenarios=GET_SCENARIOS[:2])
    db_result = run_database_check(
        report_path=tmp_path / "db.md",
        json_path=tmp_path / "db.json",
        dashboard_path=tmp_path / "dashboard.md",
    )
    load_result = run_load_scenario("light", endpoints=["/api/v1/health/"])

    assert api_result["request_count"] > 0
    assert db_result["status"] == "DATABASE_PERFORMANCE_BASELINE_COMPLETE"
    assert load_result["request_count"] == 10
    assert load_result["production_modified"] is False
