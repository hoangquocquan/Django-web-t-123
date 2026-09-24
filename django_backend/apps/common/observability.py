"""Prometheus-compatible metrics and operational dependency health."""

from __future__ import annotations

import json
import os
import shutil
import socket
import threading
import time
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import ClassVar
from urllib.error import URLError
from urllib.request import urlopen

from django.conf import settings
from django.db import connection
from django.utils import timezone


def _normalized_labels(labels):
    return tuple(sorted((str(key), str(value)) for key, value in labels.items()))


def _metric_field(name, labels):
    return json.dumps([name, _normalized_labels(labels)], separators=(",", ":"))


def _escape_label(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _format_labels(labels):
    if not labels:
        return ""
    values = ",".join(f'{key}="{_escape_label(value)}"' for key, value in labels)
    return "{" + values + "}"


class MetricsRegistry:
    """Store low-cardinality counters in Redis with a process-local fallback."""

    redis_hash = "mecprecision:ops:metrics:counters"
    _fallback: ClassVar[dict[str, float]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self, redis_client=None):
        self.redis_client = (
            redis_client if redis_client is not None else self._redis_client()
        )

    @staticmethod
    def _redis_client():
        redis_url = str(getattr(settings, "REDIS_URL", "") or "").strip()
        if not redis_url:
            return None
        try:
            from redis import Redis

            client = Redis.from_url(
                redis_url, socket_connect_timeout=1, socket_timeout=1
            )
            client.ping()
            return client
        except Exception:  # noqa: BLE001 - metrics must degrade without breaking requests.
            return None

    def increment(self, name, amount=1, **labels):
        field = _metric_field(name, labels)
        if self.redis_client is not None:
            try:
                self.redis_client.hincrbyfloat(self.redis_hash, field, float(amount))
                return
            except Exception:  # noqa: BLE001 - telemetry cannot break the request.
                self.redis_client = None
        self._increment_fallback(field, amount)

    def _increment_fallback(self, field, amount):
        with self._lock:
            self._fallback[field] = float(self._fallback.get(field, 0)) + float(amount)

    def snapshot(self):
        if self.redis_client is not None:
            try:
                raw = self.redis_client.hgetall(self.redis_hash)
                return {
                    key.decode("utf-8") if isinstance(key, bytes) else str(key): float(
                        value
                    )
                    for key, value in raw.items()
                }
            except Exception:  # noqa: BLE001 - exporter falls back during outage.
                self.redis_client = None
        with self._lock:
            return dict(self._fallback)

    def render(self):
        grouped = {}
        for field, value in self.snapshot().items():
            name, labels = json.loads(field)
            grouped.setdefault(name, []).append((labels, value))
        lines = []
        for name in sorted(grouped):
            lines.append(f"# TYPE {name} counter")
            for labels, value in sorted(grouped[name]):
                lines.append(f"{name}{_format_labels(labels)} {value:g}")
        return lines


@dataclass(frozen=True)
class DependencyStatus:
    """Sanitized state for one production dependency."""

    name: str
    available: bool
    latency_ms: float
    detail: str = ""


class OperationalHealthService:
    """Collect live dependency and host metrics without exposing secrets."""

    def __init__(self, redis_client=None, ollama_service=None, n8n_url=None):
        self.redis_client = redis_client
        self.ollama_service = ollama_service
        self.n8n_url = n8n_url or getattr(
            settings, "N8N_HEALTH_URL", "http://n8n:5678/healthz"
        )

    def database_status(self):
        started = time.perf_counter()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return DependencyStatus(
                "database", True, self._elapsed(started), "query_ok"
            )
        except Exception as exc:  # noqa: BLE001 - health reports dependency failures.
            return DependencyStatus(
                "database", False, self._elapsed(started), type(exc).__name__
            )

    def redis_status(self):
        started = time.perf_counter()
        client = self.redis_client or MetricsRegistry._redis_client()
        if client is None:
            return DependencyStatus(
                "redis", False, self._elapsed(started), "not_configured_or_unreachable"
            )
        try:
            client.ping()
            return DependencyStatus("redis", True, self._elapsed(started), "ping_ok")
        except Exception as exc:  # noqa: BLE001 - health reports dependency failures.
            return DependencyStatus(
                "redis", False, self._elapsed(started), type(exc).__name__
            )

    def ollama_status(self):
        started = time.perf_counter()
        try:
            if self.ollama_service is None:
                from apps.ai.services.health_service import OllamaHealthService

                self.ollama_service = OllamaHealthService()
            payload = self.ollama_service.check()
            available = bool(
                payload.get("endpoint_reachable") and payload.get("model_available")
            )
            detail = "ready" if available else str(payload.get("status", "unavailable"))
            return DependencyStatus("ollama", available, self._elapsed(started), detail)
        except Exception as exc:  # noqa: BLE001 - health reports dependency failures.
            return DependencyStatus(
                "ollama", False, self._elapsed(started), type(exc).__name__
            )

    def n8n_status(self):
        started = time.perf_counter()
        try:
            with urlopen(self.n8n_url, timeout=2) as response:  # nosec B310 - URL is server-configured
                available = 200 <= response.status < 300
            return DependencyStatus("n8n", available, self._elapsed(started), "healthz")
        except (OSError, URLError, ValueError) as exc:
            return DependencyStatus(
                "n8n", False, self._elapsed(started), type(exc).__name__
            )

    @staticmethod
    def _elapsed(started):
        return round((time.perf_counter() - started) * 1000, 3)

    @staticmethod
    def host_gauges():
        disk = shutil.disk_usage(Path(settings.BASE_DIR))
        memory_total, memory_available = _memory_bytes()
        memory_ratio = (
            0 if not memory_total else (memory_total - memory_available) / memory_total
        )
        load = os.getloadavg()[0] if hasattr(os, "getloadavg") else 0.0
        cpu_count = max(1, os.cpu_count() or 1)
        return {
            "disk_usage_ratio": (disk.total - disk.free) / disk.total,
            "memory_usage_ratio": memory_ratio,
            "cpu_load_ratio": min(load / cpu_count, 1.0),
        }

    def snapshot(self):
        dependencies = [
            self.database_status(),
            self.redis_status(),
            self.ollama_status(),
            self.n8n_status(),
        ]
        return {
            "status": "ready"
            if all(item.available for item in dependencies)
            else "degraded",
            "hostname": socket.gethostname(),
            "checked_at": timezone.now().isoformat(),
            "dependencies": {
                item.name: {
                    "available": item.available,
                    "latency_ms": item.latency_ms,
                    "detail": item.detail,
                }
                for item in dependencies
            },
            "host": self.host_gauges(),
        }

    def prometheus_lines(self):
        snapshot = self.snapshot()
        lines = [
            "# TYPE mecprecision_dependency_up gauge",
            "# TYPE mecprecision_dependency_latency_seconds gauge",
        ]
        for name, item in snapshot["dependencies"].items():
            labels = _format_labels((("dependency", name),))
            lines.append(
                f"mecprecision_dependency_up{labels} {1 if item['available'] else 0}"
            )
            lines.append(
                f"mecprecision_dependency_latency_seconds{labels} {item['latency_ms'] / 1000:g}"
            )
        lines.extend(
            [
                "# TYPE mecprecision_host_disk_usage_ratio gauge",
                f"mecprecision_host_disk_usage_ratio {snapshot['host']['disk_usage_ratio']:g}",
                "# TYPE mecprecision_host_memory_usage_ratio gauge",
                f"mecprecision_host_memory_usage_ratio {snapshot['host']['memory_usage_ratio']:g}",
                "# TYPE mecprecision_host_cpu_load_ratio gauge",
                f"mecprecision_host_cpu_load_ratio {snapshot['host']['cpu_load_ratio']:g}",
            ]
        )
        lines.extend(self.application_gauge_lines())
        return lines

    def application_gauge_lines(self):
        """Read bounded operational counts from Django-owned tables."""
        from apps.ai.models import AIGovernanceEvent
        from apps.ai_agent.models import AgentRun
        from apps.foundation.models import FoundationAuthToken, FoundationLoginAttempt
        from apps.knowledge.models import KnowledgeDocument

        cutoff = timezone.now() - timedelta(minutes=5)
        active_sessions = FoundationAuthToken.objects.filter(
            revoked_at__isnull=True,
            expires_at__gte=timezone.now(),
        ).count()
        login_failures = FoundationLoginAttempt.objects.filter(
            success=False,
            created_at__gte=cutoff,
        ).count()
        governance_blocked = AIGovernanceEvent.objects.filter(
            decision__in=["blocked", "rate_limited"],
            created_at__gte=cutoff,
        ).count()
        uploaded = KnowledgeDocument.objects.exclude(source_path="").count()
        extracted = KnowledgeDocument.objects.exclude(content="").count()
        queue_depth = AgentRun.objects.filter(status__in=["pending", "running"]).count()
        connection_count = self._database_connection_count()
        return [
            "# TYPE mecprecision_active_sessions gauge",
            f"mecprecision_active_sessions {active_sessions}",
            "# TYPE mecprecision_login_failures_5m gauge",
            f"mecprecision_login_failures_5m {login_failures}",
            "# TYPE mecprecision_ai_governance_blocks_5m gauge",
            f"mecprecision_ai_governance_blocks_5m {governance_blocked}",
            "# TYPE mecprecision_knowledge_uploads gauge",
            f"mecprecision_knowledge_uploads {uploaded}",
            "# TYPE mecprecision_knowledge_extractions gauge",
            f"mecprecision_knowledge_extractions {extracted}",
            "# TYPE mecprecision_queue_depth gauge",
            f'mecprecision_queue_depth{{queue="ai_agent"}} {queue_depth}',
            "# TYPE mecprecision_database_connections gauge",
            f"mecprecision_database_connections {connection_count}",
        ]

    @staticmethod
    def _database_connection_count():
        if connection.vendor != "postgresql":
            return 1
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
                )
                return int(cursor.fetchone()[0])
        except Exception:  # noqa: BLE001 - a missing gauge must not fail the scrape.
            return 0


def _memory_bytes():
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return 0, 0
    values = {}
    for line in meminfo.read_text(encoding="utf-8").splitlines():
        key, _, raw = line.partition(":")
        if key in {"MemTotal", "MemAvailable"}:
            values[key] = int(raw.strip().split()[0]) * 1024
    return values.get("MemTotal", 0), values.get("MemAvailable", 0)
