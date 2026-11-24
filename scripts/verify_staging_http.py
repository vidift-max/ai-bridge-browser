#!/usr/bin/env python3
"""Read-only HTTPS health/readiness verifier for AI Bridge Browser staging."""
from __future__ import annotations
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen


def normalize_base_url(value: str) -> str:
    """Accept only an HTTPS origin; reject credentials, paths and query data."""
    try:
        parsed = urlsplit(value)
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("invalid_staging_url") from exc
    if (parsed.scheme.lower() != "https" or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise ValueError("invalid_staging_url")
    return urlunsplit(("https", parsed.netloc, "", "", ""))


def check(base_url: str, path: str) -> tuple[int, dict]:
    request = Request(base_url + path, method="GET", headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return response.status, payload if isinstance(payload, dict) else {"error": "json_object_required"}
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8", errors="replace"))
            if not isinstance(payload, dict):
                payload = {"error": "json_object_required"}
        except json.JSONDecodeError:
            payload = {"error": "invalid_json_response"}
        return exc.code, payload
    except (URLError, TimeoutError, OSError) as exc:
        return 0, {"error": type(exc).__name__}


def verify(base_url: str) -> tuple[int, dict]:
    normalized = normalize_base_url(base_url)
    hs, health = check(normalized, "/healthz")
    rs, ready = check(normalized, "/readyz")
    result = {"baseUrl": normalized, "healthz": {"status": hs, "body": health},
              "readyz": {"status": rs, "body": ready}}
    ok = hs == 200 and health.get("status") == "ok" and rs == 200 and ready.get("status") == "ready"
    return (0 if ok else 1), result


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_staging_http.py https://staging.example")
        return 2
    try:
        code, result = verify(sys.argv[1])
    except ValueError:
        print(json.dumps({"error": "invalid_staging_url"}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
