"""Reusable validation helpers for URLs and outbound endpoints."""

import ipaddress
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_safe_url(value, *, allow_relative=True, allowed_hosts=None):
    """Reject executable schemes, credentials, private IPs, and unknown hosts."""
    raw = str(value or "").strip()
    if not raw:
        return raw
    if allow_relative and raw.startswith("/") and not raw.startswith("//"):
        return raw
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValidationError("URL must use an approved HTTP(S) endpoint.")
    if parsed.username or parsed.password:
        raise ValidationError("Credentials are not allowed in URLs.")
    host = parsed.hostname.casefold()
    allowed = {
        item.casefold()
        for item in (allowed_hosts or getattr(settings, "ALLOWED_EXTERNAL_HOSTS", []))
    }
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and (address.is_private or address.is_loopback or address.is_link_local):
        raise ValidationError("Private network URLs are not allowed here.")
    if not allowed or host not in allowed:
        raise ValidationError("External URL host is not allowlisted.")
    return raw
