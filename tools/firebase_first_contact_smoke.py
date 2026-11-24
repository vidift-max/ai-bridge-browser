#!/usr/bin/env python3
"""One-shot, credential-safe Firebase RTDB AI-AI text round-trip probe.

All bearer ID tokens are read from the process environment and are never printed.
This tool sends exactly one test message only when --send is explicitly supplied.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

AI_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
CONVERSATION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
MAX_RESPONSE_BYTES = 1024 * 1024


class ProbeError(RuntimeError):
    pass


def validate_config(env):
    required = (
        "MESSENGER_FIREBASE_DATABASE_URL",
        "MESSENGER_FIREBASE_AI_A_ID",
        "MESSENGER_FIREBASE_AI_B_ID",
        "MESSENGER_FIREBASE_AI_A_ID_TOKEN",
        "MESSENGER_FIREBASE_AI_B_ID_TOKEN",
        "MESSENGER_FIREBASE_CONVERSATION_ID",
    )
    missing = [name for name in required if not env.get(name, "").strip()]
    if missing:
        raise ProbeError("missing_configuration:" + ",".join(missing))
    if env["MESSENGER_FIREBASE_AI_A_ID"] == env["MESSENGER_FIREBASE_AI_B_ID"]:
        raise ProbeError("identities_must_be_distinct")
    if not AI_ID_RE.fullmatch(env["MESSENGER_FIREBASE_AI_A_ID"]):
        raise ProbeError("invalid_ai_a_id")
    if not AI_ID_RE.fullmatch(env["MESSENGER_FIREBASE_AI_B_ID"]):
        raise ProbeError("invalid_ai_b_id")
    if not CONVERSATION_RE.fullmatch(env["MESSENGER_FIREBASE_CONVERSATION_ID"]):
        raise ProbeError("invalid_conversation_id")
    raw_database_url = env["MESSENGER_FIREBASE_DATABASE_URL"].rstrip("/")
    parsed = urllib.parse.urlsplit(raw_database_url)
    emulator_mode = env.get("MESSENGER_FIREBASE_EMULATOR", "").lower() == "true"
    if emulator_mode:
        query = urllib.parse.parse_qs(parsed.query, strict_parsing=True)
        namespace = query.get("ns", [])
        if (parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost") or
                parsed.port not in (9000, 9001) or parsed.username or parsed.password or
                parsed.fragment or len(namespace) != 1 or not namespace[0] or
                set(query) != {"ns"}):
            raise ProbeError("invalid_firebase_emulator_url")
        database_url = "http://" + parsed.netloc
    else:
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or
                parsed.password or parsed.query or parsed.fragment or
                parsed.path not in ("", "/") or parsed.port not in (None, 443) or
                not (parsed.hostname.endswith(".firebaseio.com") or
                     parsed.hostname.endswith(".firebasedatabase.app"))):
            raise ProbeError("invalid_firebase_database_url")
        database_url = "https://" + parsed.netloc
        namespace = []
    return {
        "database_url": database_url,
        "database_namespace": namespace[0] if namespace else None,
        "ai_a": env["MESSENGER_FIREBASE_AI_A_ID"],
        "ai_b": env["MESSENGER_FIREBASE_AI_B_ID"],
        "token_a": env["MESSENGER_FIREBASE_AI_A_ID_TOKEN"],
        "token_b": env["MESSENGER_FIREBASE_AI_B_ID_TOKEN"],
        "conversation": env["MESSENGER_FIREBASE_CONVERSATION_ID"],
    }


def _path(value):
    return urllib.parse.quote(value, safe="")


def firebase_request(config, method, path, token, payload=None, timeout=10, query_params=None):
    query = {"auth": token}
    if config.get("database_namespace"):
        query["ns"] = config["database_namespace"]
    if query_params:
        query.update(query_params)
    url = config["database_url"] + path + ".json?" + urllib.parse.urlencode(query)
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ProbeError("firebase_response_too_large")
            if not raw:
                return None
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Never include the request URL or response body: the URL contains the ID token.
        raise ProbeError("firebase_http_status:" + str(exc.code)) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ProbeError("firebase_connection_failed") from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ProbeError("firebase_invalid_json") from None


def authorize_send(config, env, send, allow_production_send=False):
    if not send or config.get("database_namespace"):
        return
    if (not allow_production_send or
            env.get("MESSENGER_FIREBASE_ALLOW_PRODUCTION_SEND", "").lower() != "true"):
        raise ProbeError("production_send_requires_cli_and_environment_opt_in")


def production_readiness_report(config):
    """Return configuration-only readiness; never contacts Firebase or sends data."""
    return {
        "state": "CONFIGURATION_VALID",
        "ai_pair": {"sender": config["ai_a"], "recipient": config["ai_b"]},
        "conversation_id": config["conversation"],
        "database_target": "PRODUCTION_FIREBASE",
        "credentials": {
            "ai_a_id_token": "PRESENT_NOT_VERIFIED",
            "ai_b_id_token": "PRESENT_NOT_VERIFIED",
        },
        "network_check": "NOT_RUN",
        "identity_provisioning": "NOT_VERIFIED",
        "conversation_membership": "NOT_VERIFIED",
        "message_send": "NOT_RUN",
        "acknowledgement": "NOT_RUN",
    }


def run_probe(config, send=False, timeout=10, wait_seconds=45):
    identity_a = firebase_request(config, "GET", "/messenger/identities/" + _path(config["ai_a"]), config["token_a"], timeout=timeout)
    if not isinstance(identity_a, dict) or identity_a.get("aiId") != config["ai_a"]:
        raise ProbeError("ai_a_identity_not_provisioned")
    identity_b = firebase_request(config, "GET", "/messenger/identities/" + _path(config["ai_b"]), config["token_b"], timeout=timeout)
    if not isinstance(identity_b, dict) or identity_b.get("aiId") != config["ai_b"]:
        raise ProbeError("ai_b_identity_not_provisioned")
    if not identity_a.get("uid") or not identity_b.get("uid") or identity_a["uid"] == identity_b["uid"]:
        raise ProbeError("firebase_uids_not_distinct")

    room_path = "/messenger/conversations/" + _path(config["conversation"])
    room = firebase_request(config, "GET", room_path, config["token_a"], timeout=timeout)
    members = room.get("members", {}) if isinstance(room, dict) else {}
    if members.get(config["ai_a"]) is not True or members.get(config["ai_b"]) is not True:
        raise ProbeError("conversation_membership_not_ready")

    result = {
        "state": "PREFLIGHT_PASS",
        "ai_a": config["ai_a"],
        "ai_b": config["ai_b"],
        "conversation_id": config["conversation"],
        "uids_distinct": True,
        "identity_mappings": {
            config["ai_a"]: "VERIFIED",
            config["ai_b"]: "VERIFIED",
        },
        "conversation_membership": {
            config["ai_a"]: "VERIFIED_MEMBER",
            config["ai_b"]: "VERIFIED_MEMBER",
        },
        "message_round_trip": "NOT_RUN",
        "acknowledgement": "NOT_RUN",
        "write_operations": "NONE",
    }
    if not send:
        return result

    nonce = "first-contact-" + uuid.uuid4().hex
    message = {
        "senderAiId": config["ai_a"],
        "recipientAiIds": {config["ai_b"]: True},
        "body": nonce,
        "messageKind": "NORMAL",
        "createdAtEpochMs": int(time.time() * 1000),
    }
    pushed = firebase_request(config, "POST", room_path + "/messages", config["token_a"], message, timeout)
    message_id = pushed.get("name") if isinstance(pushed, dict) else None
    if not isinstance(message_id, str) or not message_id:
        raise ProbeError("firebase_message_key_missing")

    deadline = time.monotonic() + max(1, min(wait_seconds, 180))
    message_path = room_path + "/messages"
    received = False
    while time.monotonic() < deadline:
        messages = firebase_request(
            config, "GET", message_path, config["token_b"], timeout=timeout,
            query_params={"orderBy": '"$key"', "limitToLast": "50"}
        )
        if isinstance(messages, dict):
            candidate = messages.get(message_id)
            if (isinstance(candidate, dict) and
                    candidate.get("senderAiId") == config["ai_a"] and
                    candidate.get("body") == nonce and
                    candidate.get("recipientAiIds", {}).get(config["ai_b"]) is True):
                received = True
                break
        time.sleep(1)
    if not received:
        raise ProbeError("recipient_did_not_receive_message_before_timeout")

    ack_path = room_path + "/acks/" + _path(message_id) + "/" + _path(config["ai_b"])
    firebase_request(config, "PUT", ack_path, config["token_b"], True, timeout)
    ack = firebase_request(config, "GET", ack_path, config["token_a"], timeout=timeout)
    if ack is not True:
        raise ProbeError("sender_could_not_verify_recipient_ack")

    result.update({
        "state": "TEXT_ROUND_TRIP_PASS",
        "message_round_trip": "PASS",
        "message_id": message_id,
        "acknowledgement": "VERIFIED",
    })
    return result



def _canonical_payload_bytes(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def validate_send_plan(plan, config):
    """Fail closed unless a dry-run plan is intact and bound to this AI pair."""
    if not isinstance(plan, dict) or plan.get("schema_version") != 1:
        raise ProbeError("send_plan_schema_invalid")
    if (plan.get("state") != "SEND_PLAN_READY" or
            plan.get("sender") != config["ai_a"] or
            plan.get("recipient") != config["ai_b"] or
            plan.get("conversation_id") != config["conversation"]):
        raise ProbeError("send_plan_identity_binding_invalid")
    payload = plan.get("payload")
    if not isinstance(payload, dict):
        raise ProbeError("send_plan_payload_invalid")
    if (payload.get("senderAiId") != config["ai_a"] or
            payload.get("recipientAiIds") != {config["ai_b"]: True} or
            payload.get("messageKind") != "NORMAL"):
        raise ProbeError("send_plan_recipient_or_kind_invalid")
    body = payload.get("body")
    if not isinstance(body, str) or not body.strip() or len(body) > 280:
        raise ProbeError("send_plan_body_invalid")
    if not isinstance(payload.get("createdAtEpochMs"), int):
        raise ProbeError("send_plan_timestamp_invalid")
    digest = hashlib.sha256(_canonical_payload_bytes(payload)).hexdigest()
    if plan.get("payload_sha256") != digest:
        raise ProbeError("send_plan_payload_integrity_mismatch")
    if (plan.get("write_operations") != "NONE" or
            plan.get("send_operation") != "NOT_EXECUTED" or
            plan.get("acknowledgement") != "NOT_RUN" or
            plan.get("credentials_included") is not False):
        raise ProbeError("send_plan_safety_metadata_invalid")
    return True


def prepare_send_plan(config):
    """Build and validate a credential-free one-message plan; never writes."""
    preflight = run_probe(config, send=False)
    nonce = "first-contact-" + uuid.uuid4().hex
    payload = {
        "senderAiId": config["ai_a"],
        "recipientAiIds": {config["ai_b"]: True},
        "body": "AI Bridge Browser first-contact test " + nonce,
        "messageKind": "NORMAL",
        "createdAtEpochMs": int(time.time() * 1000),
    }
    plan = {
        "schema_version": 1,
        "state": "SEND_PLAN_READY",
        "preflight": preflight["state"],
        "sender": config["ai_a"],
        "recipient": config["ai_b"],
        "conversation_id": config["conversation"],
        "operation": "ONE_TEXT_MESSAGE",
        "payload": payload,
        "payload_sha256": hashlib.sha256(_canonical_payload_bytes(payload)).hexdigest(),
        "write_operations": "NONE",
        "send_operation": "NOT_EXECUTED",
        "acknowledgement": "NOT_RUN",
        "credentials_included": False,
    }
    validate_send_plan(plan, config)
    return plan


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate and optionally run a two-identity Firebase text round trip.")
    parser.add_argument("--send", action="store_true", help="send one nonce message and wait for the other identity to ACK it")
    parser.add_argument("--config-check", action="store_true",
                        help="validate local configuration only; never contact Firebase")
    parser.add_argument("--preflight", action="store_true",
                        help="perform read-only Firebase identity and conversation membership checks")
    parser.add_argument("--prepare-send", action="store_true",
                        help="verify production identities and print a one-message dry-run plan; never sends")
    parser.add_argument("--allow-production-send", action="store_true", help="second explicit opt-in; also requires MESSENGER_FIREBASE_ALLOW_PRODUCTION_SEND=true")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--wait-seconds", type=int, default=45)
    args = parser.parse_args(argv)
    try:
        config = validate_config(os.environ)
        if args.config_check:
            if args.send or args.preflight or args.prepare_send or args.allow_production_send:
                raise ProbeError("config_check_cannot_be_combined_with_network_or_send_options")
            print(json.dumps(production_readiness_report(config), sort_keys=True))
            return 0
        if args.preflight and (args.send or args.prepare_send or args.allow_production_send):
            raise ProbeError("preflight_cannot_be_combined_with_send_options")
        if args.prepare_send and (args.send or args.preflight or args.allow_production_send):
            raise ProbeError("prepare_send_cannot_be_combined_with_send_options")
        authorize_send(config, os.environ, args.send, args.allow_production_send)
        if args.prepare_send:
            result = prepare_send_plan(config)
        else:
            result = run_probe(config, send=args.send, timeout=max(1, min(args.timeout, 30)),
                               wait_seconds=args.wait_seconds)
        print(json.dumps(result, sort_keys=True))
        return 0
    except ProbeError as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
