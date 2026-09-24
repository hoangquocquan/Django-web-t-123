"""Focused contract tests for the PROD-06 staging validation harness."""

from __future__ import annotations

import importlib.util
import hashlib
import hmac
import json
from pathlib import Path

import pytest
from django.test import override_settings


ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    """Load a repository script without turning scripts into an application package."""
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_staging_settings_inherit_production_security_contract():
    content = (ROOT / "django_backend/config/settings/staging.py").read_text(
        encoding="utf-8"
    )
    assert "from .production import *" in content
    assert 'ENVIRONMENT = "staging"' in content


def test_load_percentiles_are_nearest_rank_and_include_tail_latency():
    module = load_script("prod06_load_test")
    values = list(range(1, 101))
    assert module.percentile(values, 50) == 50
    assert module.percentile(values, 95) == 95
    assert module.percentile(values, 99) == 99


def test_load_matrix_covers_required_business_and_ai_surfaces():
    module = load_script("prod06_load_test")
    names = {item[0] for item in module.ENDPOINTS}
    assert names == {
        "health",
        "dashboard",
        "customer",
        "lead",
        "quotation",
        "knowledge",
        "ai",
    }


def test_load_and_n8n_tools_reject_non_local_targets():
    load = load_script("prod06_load_test")
    n8n = load_script("prod06_n8n_live_check")
    with pytest.raises(ValueError):
        load.run_load("https://example.com", requests=1)
    with pytest.raises(ValueError):
        n8n.execute_live_workflow("https://example.com/webhook", "secret")


def test_runtime_discovery_does_not_request_container_environment():
    content = (ROOT / "scripts/prod06_staging_validate.py").read_text(encoding="utf-8")
    assert ".Config.Env" not in content
    assert "secrets_recorded" in content


def test_runtime_failure_remains_fail_closed(monkeypatch):
    module = load_script("prod06_staging_validate")
    monkeypatch.setattr(
        module,
        "discover_compose_services",
        lambda: {"available": False, "services": {}, "reason": "offline"},
    )
    monkeypatch.setattr(module, "http_probe", lambda *args, **kwargs: {"ok": False})
    assert module.validate_runtime()["status"] == "FAIL"


def test_n8n_signature_matches_canonical_payload():
    module = load_script("prod06_n8n_live_check")
    payload = {"z": 1, "a": {"enabled": True}}
    expected = hmac.new(
        b"secret", b'{"a":{"enabled":true},"z":1}', hashlib.sha256
    ).hexdigest()
    actual = hmac.new(
        b"secret", module.canonical_json(payload).encode(), hashlib.sha256
    ).hexdigest()
    assert actual == expected


def test_prod06_uat_matrix_maps_every_required_domain_to_real_tests():
    matrix_path = ROOT / "docs/evidence/prod-06/uat-matrix.json"
    if not matrix_path.exists():
        return
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert matrix["status"] == "PASS"
    assert set(matrix["domains"]) == {
        "authentication",
        "crm",
        "sales",
        "knowledge_rag",
        "ai_sales",
        "ai_agent",
        "governance",
        "n8n",
        "operations",
    }
    assert all(
        item["tests"] and item["result"] == "PASS"
        for item in matrix["domains"].values()
    )


@pytest.mark.django_db
@override_settings(ENVIRONMENT="production")
def test_production_crm_legacy_fallback_fails_closed_before_database_query(client):
    for path in (
        "/api/v1/crm/customers/",
        "/api/v1/crm/customers/1/",
        "/api/v1/crm/contact-requests/",
    ):
        response = client.get(path)
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "permission_denied"
