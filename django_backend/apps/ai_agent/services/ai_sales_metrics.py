"""Low-cardinality, content-free operational metrics for AI Sales."""

from apps.common.observability import MetricsRegistry


class AISalesMetricsService:
    """Record bounded AI Sales outcomes without prompts, notes, or customer PII."""

    statuses = frozenset({"SUPPORTED", "NEEDS_MORE_INFORMATION", "UNAVAILABLE"})
    priorities = frozenset({"HIGH", "MEDIUM", "LOW", "NEEDS_REVIEW"})
    retrieval_outcomes = frozenset({"hit", "miss", "not_run"})
    provider_outcomes = frozenset({"success", "fallback", "not_called"})

    def __init__(self, registry=None):
        self.registry = registry or MetricsRegistry()

    @staticmethod
    def _bounded(value, allowed, fallback):
        normalized = str(value or "")
        return normalized if normalized in allowed else fallback

    def record(self, result, *, duration_seconds):
        """Record one completed analysis using only allowlisted labels."""
        telemetry = result.get("_telemetry", {})
        status = self._bounded(result.get("status"), self.statuses, "UNAVAILABLE")
        priority = self._bounded(
            result.get("priority"), self.priorities, "NEEDS_REVIEW"
        )
        retrieval = self._bounded(
            telemetry.get("retrieval"), self.retrieval_outcomes, "not_run"
        )
        provider = self._bounded(
            telemetry.get("provider"), self.provider_outcomes, "not_called"
        )
        fallback = "true" if telemetry.get("deterministic_fallback") else "false"

        self.registry.increment("mecprecision_ai_sales_requests_total", status=status)
        self.registry.increment("mecprecision_ai_sales_status_total", status=status)
        self.registry.increment("mecprecision_ai_sales_priority_total", priority=priority)
        self.registry.increment(
            "mecprecision_ai_sales_retrieval_total", outcome=retrieval
        )
        self.registry.increment(
            "mecprecision_ai_sales_provider_total", outcome=provider
        )
        self.registry.increment(
            "mecprecision_ai_sales_deterministic_fallback_total", used=fallback
        )
        self.registry.increment(
            "mecprecision_ai_sales_response_seconds_sum",
            amount=max(float(duration_seconds), 0.0),
            status=status,
        )
        self.registry.increment(
            "mecprecision_ai_sales_response_seconds_count", status=status
        )

        return {
            "status": status,
            "priority": priority,
            "retrieval": retrieval,
            "provider": provider,
            "deterministic_fallback": fallback == "true",
        }
