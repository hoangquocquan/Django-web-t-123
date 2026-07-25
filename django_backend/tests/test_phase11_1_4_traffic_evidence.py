"""Tests for Phase 11.1.4 production traffic evidence collection."""

from scripts.phase11_1_4_production_traffic_evidence import (
    analyze_records,
    evaluate_traffic_evidence,
    extract_api_paths,
    is_legacy_api_path,
    is_replacement_api_path,
    mask_sensitive_text,
)


def test_legacy_route_detection_excludes_api_v1():
    """The collector must not count Django `/api/v1/...` as legacy traffic."""
    assert is_legacy_api_path("/api/products") is True
    assert is_legacy_api_path("/api/v1/catalog/products/") is False
    assert is_replacement_api_path("/api/v1/catalog/products/") is True


def test_extract_api_paths_from_access_log_text():
    """Common access log lines should expose both legacy and replacement paths."""
    line = 'client=web "GET /api/contact HTTP/1.1" "GET /api/v1/crm/contact-requests/"'

    assert extract_api_paths(line) == ["/api/contact", "/api/v1/crm/contact-requests"]


def test_empty_logs_block_decommission(tmp_path):
    """Empty evidence files are not enough because replacement API usage is not proven."""
    log_file = tmp_path / "access.log"
    log_file.write_text("", encoding="utf-8")

    result = evaluate_traffic_evidence([str(log_file)], period="2026-01-01_to_2026-01-07")

    assert result["status"] == "BLOCKED_SAFELY"
    assert result["legacy_requests"] == 0
    assert result["replacement_requests"] == 0
    assert result["safe_to_decommission"] is False


def test_zero_legacy_with_replacement_traffic_is_ready(tmp_path):
    """Clean production evidence can support the next decommission approval step."""
    log_file = tmp_path / "access.log"
    log_file.write_text(
        "client=frontend GET /api/v1/catalog/products/ 200\n"
        "client=admin POST /api/v1/crm/contact-requests/ 201\n",
        encoding="utf-8",
    )

    result = evaluate_traffic_evidence([str(log_file)], period="2026-01-01_to_2026-01-30")

    assert result["status"] == "READY_FOR_DECOMMISSION"
    assert result["legacy_requests"] == 0
    assert result["replacement_requests"] == 2
    assert result["safe_to_decommission"] is True


def test_unknown_client_detection_for_legacy_hit():
    """Legacy hits without a client marker must be visible in the evidence report."""
    result = analyze_records([{"text": "GET /api/products 200"}])

    assert result["legacy_requests"] == 1
    assert result["unknown_clients"] == 1


def test_json_log_input_counts_replacement_traffic(tmp_path):
    """JSON exports should work for gateway or application log collectors."""
    log_file = tmp_path / "gateway.jsonl"
    log_file.write_text(
        '{"client_id":"frontend","path":"/api/v1/public/home/","status":200}\n',
        encoding="utf-8",
    )

    result = evaluate_traffic_evidence([str(log_file)])

    assert result["status"] == "READY_FOR_DECOMMISSION"
    assert result["replacement_requests"] == 1


def test_csv_log_input_detects_legacy_usage(tmp_path):
    """CSV exports should detect remaining legacy traffic."""
    log_file = tmp_path / "gateway.csv"
    log_file.write_text(
        "client_id,path,status\n"
        "partner-a,/api/quote-request,200\n",
        encoding="utf-8",
    )

    result = evaluate_traffic_evidence([str(log_file)])

    assert result["status"] == "BLOCKED_SAFELY"
    assert result["legacy_requests"] == 1
    assert "Legacy API requests were detected." in result["errors"]


def test_sensitive_values_are_masked_in_samples():
    """Security review requires secrets to be masked in evidence samples."""
    masked = mask_sensitive_text("GET /api/contact?token=abc123&password=secret")

    assert "abc123" not in masked
    assert "secret" not in masked
