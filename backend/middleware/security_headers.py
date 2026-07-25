def send_security_headers(handler):
    """Thêm HTTP security headers cơ bản cho mọi response."""
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("X-Frame-Options", "DENY")
    handler.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
    handler.send_header("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
