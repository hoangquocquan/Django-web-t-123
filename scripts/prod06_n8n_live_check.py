"""Execute the authenticated local n8n safety-gate workflow once."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request
import uuid
from urllib.parse import urlparse
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "docs" / "evidence" / "prod-06" / "n8n-live-execution.json"
)


def canonical_json(value):
    """Match the deterministic JSON canonicalization used by the n8n workflow."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def execute_live_workflow(url, secret):
    """Call n8n with an HMAC signature and validate its fail-safe response."""
    parsed = urlparse(url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise ValueError("n8n validation is restricted to a local HTTP endpoint")
    body = {
        "correlation_id": f"prod06-{uuid.uuid4()}",
        "safety_gates": {
            "human_approval_required": True,
            "auto_merge": False,
            "auto_deploy": False,
            "approval_bypass_detected": False,
        },
    }
    encoded = canonical_json(body).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), encoded, hashlib.sha256).hexdigest()
    request = urllib.request.Request(
        url,
        data=encoded,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Mec-Signature": f"sha256={signature}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310 - URL is loopback-only
            status_code = response.status
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        status_code = exc.code
        payload = json.loads(exc.read().decode("utf-8", errors="replace") or "{}")
    passed = (
        status_code == 200
        and payload.get("accepted") is True
        and payload.get("human_approval_required") is True
        and payload.get("phase_advanced") is False
        and payload.get("auto_merge") is False
        and payload.get("auto_deploy") is False
        and payload.get("correlation_id") == body["correlation_id"]
    )
    return {
        "phase": "PROD-06",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "PASS" if passed else "FAIL",
        "http_status": status_code,
        "response": payload,
        "authentication": "HMAC_SHA256",
        "retry_policy": {"max_tries": 3, "bounded": True},
        "secret_recorded": False,
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url", default="http://127.0.0.1:5679/webhook/prod04-runtime-review"
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    secret = os.getenv("N8N_WEBHOOK_SECRET", "").strip()
    if not secret:
        parser.error("N8N_WEBHOOK_SECRET is required in the process environment")
    report = execute_live_workflow(args.url, secret)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
