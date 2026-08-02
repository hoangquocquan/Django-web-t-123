"""Focused tests for PROD-05 observability, backup, and isolated restore."""

from __future__ import annotations

import io
import json
import logging
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from apps.common.logging import JsonLogFormatter
from apps.common.observability import MetricsRegistry, OperationalHealthService
from django.test import override_settings

from scripts.prod05_backup import create_backup, sha256_file
from scripts.prod05_restore_test import BackupError, run_restore_test, safe_extract


class FakeRedis:
    def __init__(self):
        self.values = {}

    def hincrbyfloat(self, _name, field, amount):
        self.values[field] = self.values.get(field, 0) + amount

    def hgetall(self, _name):
        return dict(self.values)

    def ping(self):
        return True


class FakeOllamaHealth:
    def __init__(self, available):
        self.available = available

    def check(self):
        return {
            "endpoint_reachable": self.available,
            "model_available": self.available,
            "status": "ready" if self.available else "unavailable",
        }


class FailingRedis:
    def hincrbyfloat(self, *_args):
        raise ConnectionError("redis unavailable")

    def hgetall(self, *_args):
        raise ConnectionError("redis unavailable")


class BackupRunner:
    def __init__(self):
        self.commands = []

    def run(self, command, *, output_path=None, input_path=None, env=None):
        self.commands.append(command)
        if output_path:
            Path(output_path).write_bytes(b"test-backup-artifact")
            return ""
        if command[:3] == ["git", "rev-parse", "HEAD"]:
            return "a" * 40
        if command[:3] == ["docker", "image", "inspect"]:
            return "sha256:test-image"
        if command[:2] == ["docker", "ps"]:
            service_filter = next(item for item in command if "service=" in item)
            return service_filter.rsplit("=", 1)[-1] + "-container"
        if command[:2] == ["docker", "inspect"]:
            container = command[2]
            if container == "database-container":
                return json.dumps(
                    [
                        {
                            "Config": {
                                "Env": [
                                    "POSTGRES_DB=mecprecision",
                                    "POSTGRES_USER=mecprecision",
                                ]
                            },
                            "Mounts": [],
                        }
                    ]
                )
            destination = (
                "/app/django_backend/media"
                if container == "web-container"
                else "/home/node/.n8n"
            )
            return json.dumps(
                [
                    {
                        "Config": {"Env": []},
                        "Mounts": [
                            {
                                "Destination": destination,
                                "Type": "volume",
                                "Name": container + "-volume",
                            }
                        ],
                    }
                ]
            )
        return ""


@pytest.mark.django_db
def test_metrics_endpoint_is_fail_closed_without_token(client):
    response = client.get("/api/v1/metrics/")
    assert response.status_code == 401


@pytest.mark.django_db
@override_settings(METRICS_BEARER_TOKEN="metrics-test-token")
def test_metrics_endpoint_returns_prometheus_text(client):
    class FakeHealth:
        def prometheus_lines(self):
            return ['mecprecision_dependency_up{dependency="database"} 1']

    registry = MetricsRegistry(redis_client=FakeRedis())
    registry.increment(
        "mecprecision_http_requests_total", method="GET", route="/health", status="200"
    )
    with (
        patch("apps.core.views.MetricsRegistry", return_value=registry),
        patch("apps.core.views.OperationalHealthService", return_value=FakeHealth()),
    ):
        response = client.get(
            "/api/v1/metrics/",
            HTTP_AUTHORIZATION="Bearer metrics-test-token",
        )
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/plain")
    assert b"mecprecision_http_requests_total" in response.content
    assert b"mecprecision_dependency_up" in response.content


def test_ollama_outage_is_reported_as_degraded():
    service = OperationalHealthService(
        redis_client=FakeRedis(),
        ollama_service=FakeOllamaHealth(False),
        n8n_url="http://127.0.0.1:1/healthz",
    )
    status = service.ollama_status()
    assert status.available is False
    assert status.detail == "unavailable"


def test_metrics_fall_back_without_breaking_requests_when_redis_fails():
    registry = MetricsRegistry(redis_client=FailingRedis())
    registry.increment("mecprecision_application_errors_total", component="test")
    rendered = "\n".join(registry.render())
    assert "mecprecision_application_errors_total" in rendered
    assert registry.redis_client is None


def test_json_logging_does_not_serialize_arbitrary_secret_fields():
    record = logging.LogRecord(
        "apps.operations", logging.INFO, "", 1, "completed", (), None
    )
    record.event = "http_request"
    record.correlation_id = "corr-1"
    record.authorization = "Bearer should-not-appear"
    rendered = JsonLogFormatter().format(record)
    assert "corr-1" in rendered
    assert "should-not-appear" not in rendered


def test_backup_manifest_covers_database_media_and_n8n(tmp_path):
    runner = BackupRunner()
    package, manifest = create_backup(
        output_root=tmp_path,
        runner=runner,
        now=datetime(2026, 8, 2, tzinfo=UTC),
    )
    assert package.name == "20260802T000000Z"
    assert {item["kind"] for item in manifest["components"]} == {
        "postgresql_and_n8n_database",
        "django_media",
        "n8n_encrypted_runtime_config",
        "n8n_versioned_workflows",
    }
    assert manifest["safety_gates"]["human_approval_required"] is True
    assert manifest["safety_gates"]["auto_deploy"] is False


def _write_tar(path, name="sample.txt", content=b"safe"):
    with tarfile.open(path, "w:gz") as archive:
        info = tarfile.TarInfo(name)
        info.size = len(content)
        archive.addfile(info, io.BytesIO(content))


def _write_restore_package(path):
    path.mkdir()
    (path / "postgres.dump").write_bytes(b"database")
    for name in ("media.tar.gz", "n8n-data.tar.gz", "n8n-workflows.tar.gz"):
        _write_tar(path / name)
    components = []
    for artifact in sorted(path.iterdir()):
        if artifact.is_file():
            components.append({"name": artifact.name, "sha256": sha256_file(artifact)})
    manifest = {
        "schema_version": 1,
        "components": components,
        "safety_gates": {
            "human_approval_required": True,
            "auto_merge": False,
            "auto_deploy": False,
            "approval_bypass_detected": False,
        },
    }
    (path / "release-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_restore_validates_files_and_uses_isolated_database(tmp_path):
    package = tmp_path / "package"
    _write_restore_package(package)
    with patch(
        "scripts.prod05_restore_test.restore_database_test",
        return_value={"migration_check": "PASS", "database_smoke": "PASS"},
    ):
        result = run_restore_test(package, runner=BackupRunner())
    assert result["status"] == "RESTORE_TEST_PASS"
    assert result["isolated_restore"] is True
    assert result["production_data_modified"] is False
    assert result["files"] == {"media": 1, "n8n_runtime": 1, "n8n_workflows": 1}


def test_restore_rejects_checksum_tampering(tmp_path):
    package = tmp_path / "package"
    _write_restore_package(package)
    (package / "postgres.dump").write_bytes(b"tampered")
    with pytest.raises(BackupError, match="checksum mismatch"):
        run_restore_test(package, runner=BackupRunner())


def test_restore_rejects_archive_path_traversal(tmp_path):
    archive_path = tmp_path / "unsafe.tar.gz"
    _write_tar(archive_path, "../escape.txt")
    with pytest.raises(BackupError, match="Unsafe path"):
        safe_extract(archive_path, tmp_path / "target")


def test_prometheus_and_dashboard_contracts_are_parseable():
    root = Path(__file__).resolve().parents[1]
    dashboard = json.loads(
        (root / "ops" / "grafana" / "prod05-dashboard.json").read_text(encoding="utf-8")
    )
    alerts = (root / "ops" / "prometheus" / "prod05-alerts.yml").read_text(
        encoding="utf-8"
    )
    scrape = (root / "ops" / "prometheus" / "prometheus.yml").read_text(
        encoding="utf-8"
    )
    assert len(dashboard["panels"]) >= 7
    assert "MecPrecisionDependencyDown" in alerts
    assert "MecPrecisionHighErrorRate" in alerts
    assert "bearer_token_file" in scrape
    assert "mecprecision.example.com" in scrape
