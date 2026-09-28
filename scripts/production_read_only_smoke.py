"""Read-only production smoke checks; deliberately contains no mutation/send paths."""

from __future__ import annotations

import argparse
import json
import sys
from urllib import error, request

SAFE_PATHS = ("/phase6/live/", "/phase6/ready/")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--timeout", type=float, default=5)
    args = parser.parse_args()
    results = []
    ok = True
    for path in SAFE_PATHS:
        url = args.base_url.rstrip("/") + path
        try:
            with request.urlopen(url, timeout=args.timeout) as response:
                passed = 200 <= response.status < 300
                status = response.status
        except (error.URLError, TimeoutError) as exc:
            passed, status = False, type(exc).__name__
        ok &= passed
        results.append({"path": path, "status": status, "result": "PASS" if passed else "FAIL"})
    print(json.dumps({"mode": "read-only", "result": "PASS" if ok else "FAIL", "checks": results}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
