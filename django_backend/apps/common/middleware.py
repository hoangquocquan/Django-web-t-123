"""Security and observability middleware shared by HTML and API responses."""

from __future__ import annotations

import logging
import time
import uuid

from .observability import MetricsRegistry

logger = logging.getLogger("apps.operations")


class ObservabilityMiddleware:
    """Record sanitized request telemetry and propagate a correlation ID."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.metrics = MetricsRegistry()

    def __call__(self, request):
        started = time.perf_counter()
        correlation_id = request.headers.get("X-Correlation-ID", "")[:64]
        request.correlation_id = correlation_id or str(uuid.uuid4())
        response = self.get_response(request)
        duration = time.perf_counter() - started
        route = self._route(request)
        status_code = int(response.status_code)
        self.metrics.increment(
            "mecprecision_http_requests_total",
            method=request.method,
            route=route,
            status=str(status_code),
        )
        self.metrics.increment(
            "mecprecision_http_response_seconds_sum",
            amount=duration,
            method=request.method,
            route=route,
        )
        self.metrics.increment(
            "mecprecision_http_response_seconds_count",
            method=request.method,
            route=route,
        )
        response["X-Correlation-ID"] = request.correlation_id
        log_method = logger.error if status_code >= 500 else logger.info
        log_method(
            "HTTP request completed.",
            extra={
                "event": "http_request",
                "correlation_id": request.correlation_id,
                "method": request.method,
                "route": route,
                "status_code": status_code,
                "duration_ms": round(duration * 1000, 3),
            },
        )
        return response

    def process_exception(self, request, exception):
        self.metrics.increment(
            "mecprecision_application_errors_total",
            component="django",
            exception=type(exception).__name__,
        )
        logger.exception(
            "Unhandled application error.",
            extra={
                "event": "unhandled_error",
                "correlation_id": getattr(request, "correlation_id", ""),
                "method": request.method,
                "route": self._route(request),
                "component": "django",
                "outcome": "failed",
            },
        )

    @staticmethod
    def _route(request):
        match = getattr(request, "resolver_match", None)
        route = getattr(match, "route", "") if match else ""
        return f"/{route}" if route else "unmatched"


class SecurityHeadersMiddleware:
    """Add browser hardening headers not covered by Django defaults."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; connect-src 'self'",
        )
        response.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        response.setdefault("X-Content-Type-Options", "nosniff")
        return response
