"""Tests for Phase 11.1.2 legacy API traffic verification."""

from scripts.phase11_1_2_api_dependency_scanner import scan_dependencies
from scripts.phase11_1_2_legacy_api_traffic_verification import (
    analyze_log_lines,
    evaluate_traffic,
    extract_api_paths,
    is_legacy_api_path,
    is_replacement_api_path,
    mask_sensitive_text,
)


def test_legacy_route_detection_excludes_api_v1():
    """Legacy `/api/...` and Django `/api/v1/...` must be classified separately."""
    assert is_legacy_api_path("/api/contact") is True
    assert is_legacy_api_path("/api/products/123") is True
    assert is_replacement_api_path("/api/v1/crm/contact-requests/") is True
    assert is_legacy_api_path("/api/v1/crm/contact-requests/") is False


def test_extract_api_paths_from_log_line():
    """The parser should find API paths inside common log formats."""
    line = '127.0.0.1 "GET /api/products HTTP/1.1" 200 "GET /api/v1/catalog/products/"'

    assert extract_api_paths(line) == ["/api/products", "/api/v1/catalog/products"]


def test_unknown_client_detection_for_legacy_hits():
    """Legacy hits without a client marker should be counted as unknown clients."""
    result = analyze_log_lines(["GET /api/contact 200\n"], source_name="test.log")

    assert result["legacy_requests"] == 1
    assert result["unknown_clients"] == 1
    assert result["replacement_requests"] == 0


def test_empty_traffic_report_blocks_decommission():
    """No production logs means no proof of zero legacy traffic."""
    result = evaluate_traffic([])

    assert result["status"] == "blocked_safely"
    assert result["safe_to_decommission"] is False
    assert result["decision"] == "KEEP_LEGACY_API_ACTIVE"


def test_safe_decommission_decision_with_clean_replacement_traffic(tmp_path):
    """A provided log with only `/api/v1/...` traffic can pass traffic verification."""
    log_file = tmp_path / "proxy-access.log"
    log_file.write_text(
        'client=web GET /api/v1/catalog/products/ 200\n'
        'client=admin POST /api/v1/crm/contact-requests/ 201\n',
        encoding="utf-8",
    )

    result = evaluate_traffic([str(log_file)])

    assert result["status"] == "passed"
    assert result["legacy_requests"] == 0
    assert result["replacement_requests"] == 2
    assert result["safe_to_decommission"] is True
    assert result["decision"] == "READY_FOR_DECOMMISSION"


def test_legacy_traffic_blocks_decommission(tmp_path):
    """Any legacy `/api/...` hit should block the decommission decision."""
    log_file = tmp_path / "proxy-access.log"
    log_file.write_text("client=mobile GET /api/products 200\n", encoding="utf-8")

    result = evaluate_traffic([str(log_file)])

    assert result["status"] == "blocked_safely"
    assert result["legacy_requests"] == 1
    assert result["safe_to_decommission"] is False


def test_dependency_scanner_reports_ready_replacement(tmp_path):
    """Source scan should map known legacy references to replacement endpoints."""
    source_file = tmp_path / "app.js"
    source_file.write_text('fetch("/api/contact")\nfetch("/api/v1/health/")\n', encoding="utf-8")

    result = scan_dependencies([str(source_file)])

    assert result["legacy_references"] == 1
    assert result["unknown_references"] == 0
    assert result["findings"][0]["replacement"] == "/api/v1/crm/contact-requests/"


def test_dependency_scanner_reports_unknown_reference(tmp_path):
    """Unknown legacy API names should stay visible for reviewer action."""
    source_file = tmp_path / "integration.py"
    source_file.write_text('url = "/api/custom-legacy"\n', encoding="utf-8")

    result = scan_dependencies([str(source_file)])

    assert result["status"] == "blocked_safely"
    assert result["unknown_references"] == 1


def test_log_samples_mask_sensitive_values():
    """Reports must not expose token/password-like values from logs."""
    masked = mask_sensitive_text("GET /api/contact?token=abc123&password=secret")

    assert "abc123" not in masked
    assert "secret" not in masked
