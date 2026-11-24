#!/usr/bin/env python3
"""Verify a deployed AI Bridge Browser staging URL without credentials.

This script is intentionally read-only. It checks only public health/readiness
endpoints and never sends invitation, authentication, or message data.
"""

from __future__ import annotations

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def check(base_url: str, path: str) -> tuple[int, dict]:
    url = base_url.rstrip("/") + path
    request = Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"raw": body}
        return exc.code, payload
    except URLError as exc:
        return 0, {"error": str(exc.reason)}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_staging_http.py https://staging.example")
        return 2

    base_url = sys.argv[1]
    health_status, health = check(base_url, "/healthz")
    ready_status, ready = check(base_url, "/readyz")

    print(json.dumps({
        "baseUrl": base_url.rstrip("/"),
        "healthz": {"status": health_status, "body": health},
        "readyz": {"status": ready_status, "body": ready},
    }, sort_keys=True))

    health_ok = health_status == 200 and health.get("status") == "ok"
    ready_ok = ready_status == 200 and ready.get("status") == "ready"
    return 0 if health_ok and ready_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
