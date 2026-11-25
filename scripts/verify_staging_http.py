#!/usr/bin/env python3
"""Read-only HTTPS health/readiness verifier for AI Bridge Browser staging."""
from __future__ import annotations

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen


def normalize_base_url(value: str) -> str:
    """Accept only an HTTPS origin; reject credentials, paths and ambiguous input."""
    if not isinstance(value, str) or not value or any(
        char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value
    ):
        raise ValueError("invalid_staging_url")
    try:
        parsed = urlsplit(value)
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("invalid_staging_url") from exc
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or parsed.netloc.endswith(":")
        or "%" in parsed.netloc
    ):
        raise ValueError("invalid_staging_url")
    return urlunsplit(("https", parsed.netloc, "", "", ""))


def _json_object(raw: bytes) -> dict:
    """Decode a response defensively; never leak response bytes into diagnostics."""
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"error": "invalid_json_response"}
    if not isinstance(payload, dict):
        return {"error": "json_object_required"}
    return payload


def check(base_url: str, path: str) -> tuple[int, dict]:
    request = Request(
        base_url + path, method="GET", headers={"Accept": "application/json"}
    )
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, _json_object(response.read())
    except HTTPError as exc:
        return exc.code, _json_object(exc.read())
    except (URLError, TimeoutError, OSError) as exc:
        return 0, {"error": type(exc).__name__}


def verify(base_url: str) -> tuple[int, dict]:
    normalized = normalize_base_url(base_url)
    health_status, health = check(normalized, "/healthz")
    ready_status, ready = check(normalized, "/readyz")
    result = {
        "baseUrl": normalized,
        "healthz": {"status": health_status, "body": health},
        "readyz": {"status": ready_status, "body": ready},
    }
    ok = (
        health_status == 200
        and health.get("status") == "ok"
        and ready_status == 200
        and ready.get("status") == "ready"
    )
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
