"""Application security headers shared by HTML and API responses."""


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
