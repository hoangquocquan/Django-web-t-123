# Edge security requirements

Use modern TLS, HTTP redirect, trusted proxy headers, request/body/time limits, WAF/rate limits for auth/AI/expensive routes, restricted admin/operations routes and sanitized access logs. Block direct origin access. Validate HSTS, frame/content controls, cookie flags, CSRF origins and denial behavior in staging. Platform implementation is `MANUAL_EXECUTION_REQUIRED`.
