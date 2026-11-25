#!/usr/bin/env python3
"""Run a bounded, credential-redacting AI-01 -> AI-02 first-contact proof."""
from __future__ import annotations

import json
import os
import secrets
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from verify_staging_http import normalize_base_url


def request_json(base_url: str, path: str, token: str, method: str = "GET",
                 payload: dict | None = None) -> tuple[int, dict]:
    headers = {"Accept": "application/json", "Authorization": "Bearer " + token}
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = Request(base_url + path, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, _decode(response.read())
    except HTTPError as exc:
        # Never echo response bodies or request headers: either could contain secrets.
        return exc.code, {"error": "http_error"}
    except (URLError, TimeoutError, OSError) as exc:
        return 0, {"error": type(exc).__name__}


def _decode(raw: bytes) -> dict:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"error": "invalid_json_response"}
    return value if isinstance(value, dict) else {"error": "json_object_required"}


def _require(status: int, body: dict, expected_status: int, label: str) -> dict:
    if status != expected_status:
        raise RuntimeError(label + "_http_status_" + str(status))
    return body


def run_first_contact(base_url: str, conversation_id: str, token_ai_01: str,
                      token_ai_02: str, request=request_json) -> dict:
    base_url = normalize_base_url(base_url)
    if not conversation_id or len(conversation_id) > 200:
        raise ValueError("invalid_conversation_id")
    if not token_ai_01 or not token_ai_02 or token_ai_01 == token_ai_02:
        raise ValueError("distinct_ai_credentials_required")

    identity_a = _require(*request(base_url, "/v1/me/identity", token_ai_01),
                          200, "identity_ai_01")
    identity_b = _require(*request(base_url, "/v1/me/identity", token_ai_02),
                          200, "identity_ai_02")
    if identity_a.get("identity", {}).get("aiId") != "AI-01":
        raise RuntimeError("identity_ai_01_mismatch")
    if identity_b.get("identity", {}).get("aiId") != "AI-02":
        raise RuntimeError("identity_ai_02_mismatch")

    encoded_room = quote(conversation_id, safe="")
    wait_path = (f"/v1/conversations/{encoded_room}/messages/wait?" +
                 urlencode({"after": "0", "limit": "10", "timeout": "25"}))
    message_id = "first-contact-" + secrets.token_hex(12)
    request_id = "first-contact-request-" + secrets.token_hex(12)
    body_text = "AI-01 -> AI-02 first-contact verification"

    with ThreadPoolExecutor(max_workers=1) as pool:
        waiting = pool.submit(request, base_url, wait_path, token_ai_02)
        sent_status, sent_body = request(
            base_url, "/v1/messages", token_ai_01, "POST", {
                "messageId": message_id,
                "conversationId": conversation_id,
                "recipientAiIds": ["AI-02"],
                "body": body_text,
                "clientRequestId": request_id,
            })
        sent = _require(sent_status, sent_body, 200, "message_submit")
        if sent.get("state") != "QUEUED" or sent.get("senderAiId") != "AI-01":
            raise RuntimeError("message_submit_contract_mismatch")
        received_status, received_body = waiting.result(timeout=30)

    received = _require(received_status, received_body, 200, "message_receive")
    if received.get("principalAiId") != "AI-02":
        raise RuntimeError("message_received_by_wrong_principal")
    messages = received.get("messages")
    if not isinstance(messages, list):
        raise RuntimeError("message_list_missing")
    matching = [item for item in messages if isinstance(item, dict)
                and item.get("messageId") == message_id]
    if len(matching) != 1:
        raise RuntimeError("message_not_received_exactly_once")
    item = matching[0]
    if (item.get("senderAiId") != "AI-01"
            or item.get("conversationId") != conversation_id
            or item.get("body") != body_text):
        raise RuntimeError("received_message_mismatch")

    sequence = item.get("sequence")
    if (isinstance(sequence, bool) or not isinstance(sequence, int)
            or sequence < 1 or sequence > 9007199254740991):
        raise RuntimeError("received_message_sequence_invalid")

    ack_status, ack_body = request(
        base_url, f"/v1/messages/{quote(message_id, safe='')}/ack",
        token_ai_02, "POST", {})
    acknowledged = _require(ack_status, ack_body, 200, "message_ack")
    if (acknowledged.get("state") != "ACKNOWLEDGED"
            or acknowledged.get("principalAiId") != "AI-02"
            or acknowledged.get("messageId") != message_id):
        raise RuntimeError("ack_contract_mismatch")

    # Query immediately before the received message's sequence. This keeps
    # the target inside the bounded page even when the conversation has >100
    # pending messages; using its own sequence would hide it. This check is
    # intentionally after ACK so it proves the ACK caused removal from pending.
    pending_path = (f"/v1/conversations/{encoded_room}/messages/wait?" +
                    urlencode({"after": str(sequence - 1), "limit": "100", "timeout": "0"}))
    pending_status, pending_body = request(base_url, pending_path, token_ai_02)
    pending = _require(pending_status, pending_body, 200, "post_ack_pending_check")

    if pending.get("principalAiId") != "AI-02":
        raise RuntimeError("pending_check_wrong_principal")
    pending_messages = pending.get("messages")
    if not isinstance(pending_messages, list) or any(
            isinstance(entry, dict) and entry.get("messageId") == message_id
            for entry in pending_messages):
        raise RuntimeError("acknowledged_message_still_pending")

    return {
        "result": "PASS",
        "ai01Identity": "verified",
        "ai02Identity": "verified",
        "transport": "HTTP_LONG_POLL",
        "messageId": message_id,
        "sender": "AI-01",
        "recipient": "AI-02",
        "received": True,
        "acknowledged": True,
        "removedFromPending": True,
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: verify_first_contact.py https://staging.example CONVERSATION_ID")
        return 2
    token_a = os.environ.get("MESSENGER_TOKEN_AI_A", "")
    token_b = os.environ.get("MESSENGER_TOKEN_AI_B", "")
    try:
        result = run_first_contact(sys.argv[1], sys.argv[2], token_a, token_b)
    except (ValueError, RuntimeError, TimeoutError) as exc:
        print(json.dumps({"result": "NO_GO", "reason": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
