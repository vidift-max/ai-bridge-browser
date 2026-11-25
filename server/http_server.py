import json
import hashlib
from urllib.parse import parse_qs, urlsplit
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from server.auth import Authenticator
from server.messenger_backend import MessengerBackend
from server.runtime_config import RuntimeConfig
from server.sqlite_store import SQLiteMessengerStore
from server.rate_limit import SlidingWindowRateLimiter, RateLimitExceeded
from server.request_context import authenticate_request, bearer_token
from server.audio_blob_store import AudioBlobStore
from pathlib import Path
from server.openai_text_adapter import OpenAITextAdapter
from server.provider_registry import ProviderRegistry
from server.gpt6_room_agent import GPT6RoomAgent
from server.ai_provider_host import AuthenticatedProviderHost, ProviderHostError


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _reject_json_constant(_value):
    raise ValueError("invalid_json_constant")

def parse_long_poll_query(query_string):
    try:
        query = parse_qs(query_string, keep_blank_values=True,
                         strict_parsing=True, max_num_fields=3)
    except ValueError:
        raise ValueError("invalid_long_poll_query")
    if set(query) != {"after", "limit", "timeout"} or any(
            len(values) != 1 or not values[0] for values in query.values()):
        raise ValueError("invalid_long_poll_query")
    values = {key: items[0] for key, items in query.items()}
    if any(not value.isascii() or not value.isdecimal()
           for value in values.values()):
        raise ValueError("invalid_long_poll_query")
    after_sequence = int(values["after"])
    limit = int(values["limit"])
    timeout_seconds = int(values["timeout"])
    if (after_sequence > 9007199254740991 or
            limit < 1 or limit > 100 or
            timeout_seconds > 25):
        raise ValueError("invalid_long_poll_query")
    return after_sequence, limit, timeout_seconds


class MessengerHandler(BaseHTTPRequestHandler):
    backend=None
    authenticator=None
    rate_limiter=SlidingWindowRateLimiter()
    operational=None
    audio_store=None
    voice_control=None
    voice_calls=None
    openai_text=None
    provider_registry=None
    gpt6_room_agent=None
    provider_host=None
    guest_sessions=None

    def _auth(self):
        return bearer_token(self.headers)

    def _principal(self):
        return authenticate_request(self.authenticator, self.headers)

    def _read_json(self, max_length=10000):
        if self.headers.get("Content-Type","").split(";")[0].lower()!="application/json":
            raise ValueError("content_type_required")
        raw_length=self.headers.get("Content-Length","")
        try:
            length=int(raw_length)
        except (TypeError, ValueError):
            raise ValueError("invalid_content_length")
        if length<1 or length>max_length:
            raise ValueError("invalid_content_length")
        try:
            raw = self.rfile.read(length).decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("invalid_json_encoding")
        payload=json.loads(raw, object_pairs_hook=_unique_json_object,
                           parse_constant=_reject_json_constant)
        if not isinstance(payload, dict):
            raise ValueError("json_object_required")
        return payload

    def _audit(self, identity, event_type, subject, **metadata):
        self.authenticator.audit_log.record(event_type, subject, ai_id=identity.principal.ai_id, metadata=metadata, correlation_id=identity.correlation_id)
        if self.operational is not None:
            self.operational.record(event_type, correlation_id=identity.correlation_id, principal=identity.principal.ai_id, metadata=metadata)

    def _permission_error(self, exc):
        return {"error": "authentication_required" if str(exc) == "authentication_required" else "forbidden"}

    def _json(self,status,payload):
        data=json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _rooms_web(self):
        page = Path(__file__).resolve().parent.parent / "web" / "rooms.html"
        try:
            data = page.read_bytes()
        except OSError:
            self._json(404, {"error": "rooms_web_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _guest_web(self):
        page = Path(__file__).resolve().parent.parent / "web" / "guest.html"
        try:
            data = page.read_bytes()
        except OSError:
            self._json(404, {"error": "guest_web_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _invite_web(self):
        page = Path(__file__).resolve().parent.parent / "web" / "invite.html"
        try:
            data = page.read_bytes()
        except OSError:
            self._json(404, {"error": "invite_web_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _gpt6_web(self):
        page = Path(__file__).resolve().parent.parent / "web" / "gpt6-messenger.html"
        try:
            data = page.read_bytes()
        except OSError:
            self._json(404, {"error": "gpt6_web_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _room_ui_messenger_script(self):
        script = Path(__file__).resolve().parent.parent / "web" / "ai-room-ui-messenger.js"
        try:
            data = script.read_bytes()
        except OSError:
            self._json(404, {"error": "room_ui_messenger_script_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _room_gpt6_script(self):
        script = Path(__file__).resolve().parent.parent / "web" / "ai-room-gpt6.js"
        try:
            data = script.read_bytes()
        except OSError:
            self._json(404, {"error": "room_gpt6_script_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


    def _ai_conversation_script(self, filename):
        allowed = {
            "ai-conversation-loop.js",
            "ai-agent-adapter.js",
            "ai-conversation-runtime.js",
            "ai-conversation-panel.js",
        }
        if filename not in allowed:
            self._json(404, {"error": "ai_conversation_script_not_found"})
            return
        script = Path(__file__).resolve().parent.parent / "web" / filename
        try:
            data = script.read_bytes()
        except OSError:
            self._json(404, {"error": "ai_conversation_script_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _wifi_only_script(self):
        script = Path(__file__).resolve().parent.parent / "web" / "wifi-only.js"
        try:
            data = script.read_bytes()
        except OSError:
            self._json(404, {"error": "wifi_policy_script_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _voice_capabilities_script(self):
        script = Path(__file__).resolve().parent.parent / "web" / "voice-capabilities.js"
        try:
            data = script.read_bytes()
        except OSError:
            self._json(404, {"error": "voice_capabilities_script_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _local_ai_capability_script(self):
        script = Path(__file__).resolve().parent.parent / "web" / "local-ai-capability.js"
        try:
            data = script.read_bytes()
        except OSError:
            self._json(404, {"error": "local_ai_capability_script_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _room_creation_script(self):
        script = Path(__file__).resolve().parent.parent / "web" / "ai-room-creation.js"
        try:
            data = script.read_bytes()
        except OSError:
            self._json(404, {"error": "room_creation_script_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _room_notifications_script(self):
        script = Path(__file__).resolve().parent.parent / "web" / "ai-room-notifications.js"
        try:
            data = script.read_bytes()
        except OSError:
            self._json(404, {"error": "room_notifications_script_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _room_event_notifications_script(self):
        script = Path(__file__).resolve().parent.parent / "web" / "ai-room-event-notifications.js"
        try:
            data = script.read_bytes()
        except OSError:
            self._json(404, {"error": "room_event_notifications_script_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _room_inbox_script(self):
        script = Path(__file__).resolve().parent.parent / "web" / "ai-room-inbox.js"
        try:
            data = script.read_bytes()
        except OSError:
            self._json(404, {"error": "room_inbox_script_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _room_message_actions_script(self):
        script = Path(__file__).resolve().parent.parent / "web" / "ai-room-message-actions.js"
        try:
            data = script.read_bytes()
        except OSError:
            self._json(404, {"error": "room_message_actions_script_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _room_message_reply_script(self):
        script = Path(__file__).resolve().parent.parent / "web" / "ai-room-message-reply.js"
        try:
            data = script.read_bytes()
        except OSError:
            self._json(404, {"error": "room_message_reply_script_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _room_message_search_script(self):
        script = Path(__file__).resolve().parent.parent / "web" / "ai-room-message-search.js"
        try:
            data = script.read_bytes()
        except OSError:
            self._json(404, {"error": "room_message_search_script_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _room_message_conversation_export_script(self):
        script = Path(__file__).resolve().parent.parent / "web" / "ai-room-conversation-export.js"
        try:
            data = script.read_bytes()
        except OSError:
            self._json(404, {"error": "room_message_conversation_export_script_not_found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/guest", "/guest/"):
            self._guest_web()
            return
        if self.path in ("/invite", "/invite/"):
            self._invite_web()
            return
        if self.path in ("/", "/rooms", "/rooms/"):
            self._rooms_web()
            return
        if self.path == "/voice-capabilities.js":
            self._voice_capabilities_script()
            return
        if self.path == "/local-ai-capability.js":
            self._local_ai_capability_script()
            return
        if self.path == "/ai-room-notifications.js":
            self._room_notifications_script()
            return
        if self.path == "/ai-room-event-notifications.js":
            self._room_event_notifications_script()
            return
        if self.path == "/ai-room-inbox.js":
            self._room_inbox_script()
            return
        if self.path == "/ai-room-message-actions.js":
            self._room_message_actions_script()
            return
        if self.path == "/ai-room-message-reply.js":
            self._room_message_reply_script()
            return
        if self.path == "/ai-room-message-search.js":
            self._room_message_search_script()
            return
        if self.path == "/ai-room-conversation-export.js":
            self._room_message_conversation_export_script()
            return
        if self.path == "/ai-room-creation.js":
            self._room_creation_script()
            return
        if self.path == "/ai-room-ui-messenger.js":
            self._room_ui_messenger_script()
            return
        if self.path == "/ai-room-gpt6.js":
            self._room_gpt6_script()
            return
        if self.path in (
            "/ai-conversation-loop.js",
            "/ai-agent-adapter.js",
            "/ai-conversation-runtime.js",
            "/ai-conversation-panel.js",
        ):
            self._ai_conversation_script(self.path.lstrip("/"))
            return
        if self.path == "/wifi-only.js":
            self._wifi_only_script()
            return
        if self.path in ("/gpt6", "/gpt6/"):
            self._gpt6_web()
            return
        if self.path=="/healthz":
            self._json(200,{"status":"ok","service":"ai-messenger-experimental"}); return
        if self.path=="/readyz":
            try:
                RuntimeConfig.auth_tokens()
                storage_mode = RuntimeConfig.validate_storage_contract()
                RuntimeConfig.request_timeout_seconds()
                RuntimeConfig.retry_limit()
                if self.operational is not None:
                    storage_ok, _ = self.operational.check_storage(
                        RuntimeConfig.storage_path(), connection=self.backend._store.connection)
                    if not storage_ok:
                        self._json(503,{"status":"not_ready","error":"storage_unavailable_or_invalid"})
                        return
                self._json(200,{"status":"ready","storageMode":storage_mode})
            except RuntimeError:
                self._json(503,{"status":"not_ready","error":"runtime_configuration_invalid"})
            return
        if self.path == "/v1/guest-sessions/current":
            try:
                token = self._auth()
                if self.guest_sessions is None:
                    self._json(503, {"error": "guest_sessions_unavailable"})
                    return
                self.rate_limiter.allow("guest-session:" + self.client_address[0])
                current = self.guest_sessions.authenticate(token)
                self._json(200, {"session": current})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError:
                self._json(401, {"error": "guest_session_not_active"})
            return
        if self.path == "/v1/operations/summary":
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                if self.operational is None:
                    self._json(503, {"error": "operations_unavailable"})
                    return
                self._audit(identity, "OPERATIONS_SUMMARY_READ", "operations_summary")
                self._json(200, {
                    "summary": self.operational.summary(),
                    "correlationId": identity.correlation_id,
                })
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403, self._permission_error(exc))
            return
        if self.path == "/v1/local-ai":
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                from server.local_ai_registry import LocalAIRegistry
                self._audit(identity, "LOCAL_AI_CATALOG_READ", "local_ai_catalog")
                self._json(200, {
                    "engines": LocalAIRegistry.list_engines(),
                    "messenger": LocalAIRegistry.messenger_capabilities(),
                    "inferenceContract": LocalAIRegistry.inference_contract(),
                    "correlationId": identity.correlation_id,
                })
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403, self._permission_error(exc))
            return
        if self.path == "/v1/providers":
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                registry = self.provider_registry or ProviderRegistry(self.openai_text)
                self._audit(identity, "PROVIDER_CATALOG_READ", "provider_catalog")
                self._json(200, {
                    "providers": registry.list_providers(),
                    "correlationId": identity.correlation_id,
                })
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403, self._permission_error(exc))
            return
        if self.path == "/v1/gpt6/status":
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                configured = self.openai_text is not None and self.openai_text.enabled()
                connection = (
                    self.openai_text.connection_status()
                    if self.openai_text is not None and hasattr(self.openai_text, "connection_status")
                    else {
                        "connectionState": "CONFIGURED_UNVERIFIED" if configured else "NOT_CONFIGURED",
                        "lastSuccessfulRequestAt": None,
                        "lastResponseId": None,
                        "lastSuccessfulModel": None,
                        "online": False,
                        "accountSessionConnected": False,
                    }
                )
                self._json(200, {
                    "assistant": {"id": "AI-GPT6", "displayName": "GPT-6", "online": False},
                    "transport": "OpenAI Responses API" if configured else "not_configured",
                    **connection,
                    "configured": configured,
                    "apiCallsEnabled": bool(self.openai_text is not None and self.openai_text.api_calls_enabled()),
                    "model": self.openai_text.model if self.openai_text is not None else None,
                    "correlationId": identity.correlation_id,
                })
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403, self._permission_error(exc))
            return
        if self.path == "/v1/me/identity":
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                self._audit(identity, "AI_IDENTITY_READ", principal.ai_id)
                self._json(200, {"identity": {"aiId": principal.ai_id}, "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403, self._permission_error(exc))
            return
        parsed = urlsplit(self.path)
        if parsed.path == "/v1/conversations":
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                query = parse_qs(parsed.query, keep_blank_values=True)
                if any(len(values) != 1 for values in query.values()) or set(query) - {"limit", "after"}:
                    raise ValueError("invalid_conversation_cursor")
                limit = int(query.get("limit", ["50"])[0])
                after = query.get("after", [""])[0]
                self.rate_limiter.allow(principal.ai_id)
                result = self.backend.list_conversations(self._auth(), limit=limit, after=after)
                self._audit(identity, "CONVERSATIONS_LISTED", principal.ai_id,
                            count=str(len(result["conversations"])))
                self._json(200, {**result, "principalAiId": principal.ai_id,
                                 "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except (TypeError, ValueError):
                self._json(400, {"error": "invalid_conversation_query"})
            return
        presence_parts = parsed.path.split("/")
        if (len(presence_parts) == 5 and presence_parts[1:3] == ["v1", "conversations"]
                and presence_parts[4] == "presence" and presence_parts[3]):
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                participants = self.backend.list_conversation_presence(
                    self._auth(), presence_parts[3])
                self._audit(identity, "ROOM_PRESENCE_LISTED", presence_parts[3],
                            online_count=str(sum(1 for item in participants
                                                  if item["status"] == "ONLINE")))
                self._json(200, {"conversationId": presence_parts[3],
                                 "participants": participants,
                                 "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except ValueError:
                self._json(400, {"error": "invalid_conversation"})
            return
        identity_parts = parsed.path.split("/")
        if (len(identity_parts) == 5 and identity_parts[1:3] == ["v1", "conversations"]
                and identity_parts[4] == "identities" and identity_parts[3]):
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                participants = self.backend.list_conversation_identities(
                    self._auth(), identity_parts[3])
                self._audit(identity, "ROOM_IDENTITIES_LISTED", identity_parts[3],
                            participant_count=str(len(participants)))
                self._json(200, {"conversationId": identity_parts[3],
                                 "participants": participants,
                                 "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except (TypeError, ValueError, KeyError):
                self._json(400, {"error": "identity_directory_unavailable"})
            return
        guest_parts = parsed.path.split("/")
        if (len(guest_parts) == 5 and guest_parts[1:3] == ["v1", "conversations"]
                and guest_parts[4] == "guest-applications" and guest_parts[3]):
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                items = self.backend.list_guest_applications(self._auth(), guest_parts[3])
                self._audit(identity, "GUEST_APPLICATIONS_LISTED", guest_parts[3])
                self._json(200, {"applications": items,
                                 "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            return
        invite_parts = parsed.path.split("/")
        if len(invite_parts) == 4 and invite_parts[1:3] == ["v1", "invites"] and invite_parts[3]:
            try:
                self.rate_limiter.allow("invite:" + self.client_address[0])
                result = self.backend.get_public_invite(invite_parts[3])
                self._json(200, {"invite": result})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except ValueError:
                self._json(404, {"error": "invite_unavailable"})
            return
        if (len(invite_parts) == 5 and invite_parts[1:3] == ["v1", "conversations"]
                and invite_parts[4] in ("invites", "join-requests") and invite_parts[3]):
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                if invite_parts[4] == "invites":
                    items = self.backend.list_room_invites(self._auth(), invite_parts[3])
                    self._audit(identity, "ROOM_INVITES_LISTED", invite_parts[3],
                                count=str(len(items)))
                    self._json(200, {"invites": items,
                                     "correlationId": identity.correlation_id})
                else:
                    items = self.backend.list_join_requests(self._auth(), invite_parts[3])
                    self._audit(identity, "JOIN_REQUESTS_LISTED", invite_parts[3],
                                count=str(len(items)))
                    self._json(200, {"requests": items,
                                     "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            return
        call_parts = parsed.path.split("/")
        if (len(call_parts) == 6 and call_parts[1:3] == ["v1", "conversations"]
                and call_parts[4:] == ["calls", "active"] and call_parts[3]):
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                if self.voice_calls is None:
                    self._json(503, {"error": "voice_call_service_unavailable"})
                    return
                call = self.voice_calls.active_for_conversation(principal.ai_id, call_parts[3])
                self._json(200, {"call": call, "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except ValueError as exc:
                self._json(400, {"error": str(exc)})
            return
        if len(call_parts) == 4 and call_parts[1:3] == ["v1", "calls"] and call_parts[3]:
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                if self.voice_calls is None:
                    self._json(503, {"error": "voice_call_service_unavailable"})
                    return
                call = self.voice_calls.get(principal.ai_id, call_parts[3])
                self._audit(identity, "VOICE_CALL_STATE_READ", call_parts[3], state=call["state"])
                self._json(200, {"call": call, "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except ValueError as exc:
                self._json(404 if str(exc) == "voice_call_not_found" else 400,
                           {"error": str(exc)})
            return
        if (len(call_parts) == 5 and call_parts[1:3] == ["v1", "calls"]
                and call_parts[4] == "signals" and call_parts[3]):
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                query = parse_qs(parsed.query)
                after_id = int(query.get("after", ["0"])[0])
                limit = int(query.get("limit", ["100"])[0])
                self.rate_limiter.allow(principal.ai_id)
                if self.voice_calls is None:
                    self._json(503, {"error": "voice_call_service_unavailable"})
                    return
                signals = self.voice_calls.pending_signals(principal.ai_id, call_parts[3], after_id, limit)
                self._json(200, {"signals": signals, "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except ValueError as exc:
                self._json(400, {"error": str(exc)})
            return
        parsed = urlsplit(self.path)
        parts=parsed.path.split("/")
        if (len(parts) == 6 and parts[1:3] == ["v1", "conversations"]
                and parts[4] == "voice" and parts[5] == "status" and parts[3]):
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                if self.voice_control is None:
                    self._json(503, {"error": "voice_admin_control_unavailable"})
                    return
                members = self.backend.conversation_members().get(parts[3])
                if not members or principal.ai_id not in members:
                    raise PermissionError("voice_room_membership_required")
                muted = sorted(self.voice_control.muted_participants(parts[3]))
                self._audit(identity, "VOICE_ROOM_STATE_READ", parts[3],
                            muted_count=str(len(muted)))
                self._json(200, {
                    "conversationId": parts[3],
                    "mutedAiIds": muted,
                    "correlationId": identity.correlation_id,
                })
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            return
        if len(parts) == 5 and parts[1:3] == ["v1", "messages"] and parts[4] == "audio" and parts[3]:
            try:
                identity=self._principal()
                principal=identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                attachments=self.backend.list_audio_attachments(self._auth(),parts[3])
                self._json(200,{"messageId":parts[3],"attachments":[
                    {"objectId":a.object_id,"messageId":a.message_id,"contentType":a.content_type,
                     "size":a.size,"sha256":a.sha256,"senderAiId":a.sender_ai_id}
                    for a in attachments]})
            except RateLimitExceeded:
                self._json(429,{"error":"rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc)=="authentication_required" else 403,self._permission_error(exc))
            except (ValueError,FileNotFoundError):
                self._json(404,{"error":"not_found"})
            return
        if len(parts) == 6 and parts[1:3] == ["v1", "messages"] and parts[4] == "audio" and parts[3] and parts[5]:
            try:
                identity=self._principal()
                principal=identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                data=self.backend.read_audio(self._auth(),parts[3],parts[5],self.audio_store)
                self.send_response(200)
                self.send_header("Content-Type","application/octet-stream")
                self.send_header("Cache-Control","no-store")
                self.send_header("Content-Length",str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except RateLimitExceeded:
                self._json(429,{"error":"rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc)=="authentication_required" else 403,self._permission_error(exc))
            except (ValueError,FileNotFoundError):
                self._json(404,{"error":"not_found"})
            return
        if len(parts)==5 and parts[1:3]==["v1","conversations"] and parts[4]=="transport":
            try:
                identity=self._principal()
                principal=identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                capabilities=self.backend.transport_capabilities(self._auth(), parts[3])
                self._audit(identity, "MESSAGE_TRANSPORT_CAPABILITIES_READ", parts[3])
                self._json(200, {"principalAiId":principal.ai_id, "correlationId":identity.correlation_id, **capabilities})
            except RateLimitExceeded:
                self._json(429,{"error":"rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc)=="authentication_required" else 403,self._permission_error(exc))
            return
        if len(parts)==6 and parts[1:3]==["v1","conversations"] and parts[4]=="messages" and parts[5]=="wait":
            try:
                identity=self._principal()
                principal=identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                after_sequence, limit, timeout = parse_long_poll_query(parsed.query)
                self.rate_limiter.allow(principal.ai_id)
                messages=self.backend.wait_for_messages(self._auth(),parts[3],after_sequence=after_sequence,limit=limit,timeout_seconds=timeout)
                self._audit(identity, "MESSAGE_LONG_POLL", parts[3], count=str(len(messages)))
                self._json(200,{"principalAiId":principal.ai_id,"correlationId":identity.correlation_id,"messages":[{"messageId":m.message_id,"conversationId":m.conversation_id,"senderAiId":m.sender_ai_id,"sequence":m.sequence,"body":m.body,"messageKind":m.kind,"createdAtEpochMs":int(m.created_at_epoch_seconds*1000),"expiresAtEpochMs":int(self.backend.message_expires_at(m)*1000)} for m in messages]})
            except RateLimitExceeded:
                self._json(429,{"error":"rate_limit_exceeded"})
            except (ValueError, TypeError):
                self._json(400,{"error":"invalid_long_poll"})
            except PermissionError as exc:
                self._json(401 if str(exc)=="authentication_required" else 403,self._permission_error(exc))
            return
        if len(parts)==5 and parts[1:3]==["v1","conversations"] and parts[4]=="history" and parts[3]:
            try:
                identity=self._principal()
                principal=identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                query=parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True, max_num_fields=2)
                if set(query)-{"before","limit"} or any(len(values)!=1 for values in query.values()):
                    raise ValueError("invalid_history_query")
                raw_before=query.get("before", ["0"])[0]
                raw_limit=query.get("limit", ["50"])[0]
                if (not raw_before or not raw_limit or not raw_before.isascii()
                        or not raw_limit.isascii() or not raw_before.isdecimal()
                        or not raw_limit.isdecimal()):
                    raise ValueError("invalid_history_query")
                before_sequence=int(raw_before)
                limit=int(raw_limit)
                self.rate_limiter.allow(principal.ai_id)
                messages=self.backend.history(self._auth(),parts[3],before_sequence=before_sequence,limit=limit)
                self._audit(identity, "MESSAGE_HISTORY_READ", parts[3], count=str(len(messages)))
                self._json(200,{"principalAiId":principal.ai_id,"correlationId":identity.correlation_id,
                    "messages":[{"messageId":m.message_id,"conversationId":m.conversation_id,
                    "senderAiId":m.sender_ai_id,"sequence":m.sequence,"body":m.body,
                    "messageKind":m.kind,"createdAtEpochMs":int(m.created_at_epoch_seconds*1000),
                    "expiresAtEpochMs":int(self.backend.message_expires_at(m)*1000)} for m in messages]})
            except RateLimitExceeded:
                self._json(429,{"error":"rate_limit_exceeded"})
            except (ValueError, TypeError):
                self._json(400,{"error":"invalid_history_query"})
            except PermissionError as exc:
                self._json(401 if str(exc)=="authentication_required" else 403,self._permission_error(exc))
            return
        if len(parts)==5 and parts[1:3]==["v1","conversations"] and parts[4]=="messages":
            try:
                identity=self._principal()
                principal=identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                query=parse_qs(parsed.query)
                after_sequence=int(query.get("after", ["0"])[0])
                limit=int(query.get("limit", ["50"])[0])
                self.rate_limiter.allow(principal.ai_id)
                messages=self.backend.pending(self._auth(),parts[3],after_sequence=after_sequence,limit=limit)
                self._audit(identity, "MESSAGE_READ", parts[3], count=str(len(messages)))
                self._json(200,{"principalAiId":principal.ai_id,"correlationId":identity.correlation_id,"messages":[{"messageId":m.message_id,"conversationId":m.conversation_id,"senderAiId":m.sender_ai_id,"sequence":m.sequence,"body":m.body,"messageKind":m.kind,"createdAtEpochMs":int(m.created_at_epoch_seconds*1000),"expiresAtEpochMs":int(self.backend.message_expires_at(m)*1000)} for m in messages]})
            except RateLimitExceeded:
                self._json(429,{"error":"rate_limit_exceeded"})
            except (ValueError, TypeError):
                self._json(400,{"error":"invalid_cursor"})
            except PermissionError as exc:
                self._json(401 if str(exc)=="authentication_required" else 403,self._permission_error(exc))
            return
        self._json(404,{"error":"not_found"})

    def do_POST(self):
        if urlsplit(self.path).path == "/v1/ai/provider/respond":
            try:
                if self.provider_host is None:
                    self._json(503, {"error": "provider_host_not_configured"})
                    return
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                payload = self._read_json(max_length=6000)
                result = self.provider_host.execute(self._auth(), payload)
                response_text = result["text"]
                if len(response_text) > self.backend.MAX_BODY_LENGTH:
                    raise ValueError("provider_response_too_large")
                conversation_id = payload["conversationId"]
                agent_id = payload["agentId"]
                members = self.backend.conversation_members().get(conversation_id, set())
                recipients = sorted(members - {agent_id})
                request_digest = hashlib.sha256(
                    (agent_id + ":" + payload["requestId"]).encode("utf-8")
                ).hexdigest()[:40]
                message = self.backend.submit(
                    self._auth(),
                    "provider-" + request_digest,
                    conversation_id,
                    recipients,
                    response_text,
                    "provider-host:" + payload["requestId"],
                )
                self._audit(identity, "AI_PROVIDER_RESPONSE_PERSISTED",
                            message.message_id, provider=result["attestation"]["statement"]["providerId"],
                            model=result["attestation"]["statement"]["model"])
                self._json(201, {
                    "message": {
                        "messageId": message.message_id,
                        "conversationId": message.conversation_id,
                        "senderAiId": message.sender_ai_id,
                        "recipientAiIds": list(message.recipient_ai_ids),
                        "sequence": message.sequence,
                        "body": message.body,
                    },
                    "attestation": result["attestation"],
                })
            except ProviderHostError as exc:
                self._json(exc.status, {"error": exc.code})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                self._json(400, {"error": "invalid_provider_request"})
            except RuntimeError as exc:
                code = str(exc)
                self._json(503, {"error": code if code in (
                    "openai_api_calls_disabled", "openai_api_not_configured",
                    "provider_host_not_configured") else "provider_execution_unavailable"})
            return
        if urlsplit(self.path).path == "/v1/guest-sessions":
            try:
                if self.guest_sessions is None:
                    self._json(503, {"error": "guest_sessions_unavailable"})
                    return
                self.rate_limiter.allow("guest-session:" + self.client_address[0])
                payload = self._read_json(max_length=2000)
                result = self.guest_sessions.exchange(payload.get("credential"))
                self._json(201, {"session": {
                    "sessionToken": result["sessionToken"],
                    "aiId": result["aiId"],
                    "expiresAt": result["expiresAt"],
                    "expiresInSeconds": result["expiresInSeconds"],
                }})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError:
                self._json(401, {"error": "guest_credential_invalid"})
            except (TypeError, ValueError):
                self._json(400, {"error": "guest_credential_invalid"})
            return
        if urlsplit(self.path).path == "/v1/guest-sessions/logout":
            try:
                if self.guest_sessions is None or not self.guest_sessions.revoke(self._auth()):
                    self._json(401, {"error": "guest_session_not_active"})
                    return
                self._json(200, {"loggedOut": True})
            except PermissionError:
                self._json(401, {"error": "guest_session_not_active"})
            return
        if urlsplit(self.path).path == "/v1/guest-applications/status":
            try:
                self.rate_limiter.allow("guest-status-ip:" + self.client_address[0])
                payload = self._read_json(max_length=256)
                if not isinstance(payload, dict) or set(payload) != {"statusCapability"}:
                    raise ValueError("guest_application_status_unavailable")
                from server.guest_intake import decode_status_capability
                raw_capability = decode_status_capability(payload.get("statusCapability"))
                fingerprint = hashlib.sha256(raw_capability).hexdigest()
                self.rate_limiter.allow("guest-status-capability:" + fingerprint)
                result = self.backend.get_public_guest_application_status(payload.get("statusCapability"))
                self._json(200, {"status": {"state": result["state"], "updatedAt": result["updatedAt"]}})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except (TypeError, ValueError):
                self._json(404, {"error": "guest_application_status_unavailable"})
            return
        if urlsplit(self.path).path == "/v1/guest-applications":
            try:
                self.rate_limiter.allow("guest:" + self.client_address[0])
                payload = self._read_json(max_length=2000)
                result = self.backend.submit_public_guest_application(payload)
                if result.get("duplicate"):
                    self._json(202, {"application": {"duplicate": True, "accessGranted": False, "providerVerified": False}})
                    return
                self._json(202, {"application": {
                    "applicationId": result["applicationId"],
                    "status": result["status"],
                    "displayName": result["displayName"],
                    "providerClaim": result["providerClaim"],
                    "providerVerified": False,
                    "accessGranted": False,
                    "idempotentReplay": result.get("idempotentReplay", False),
                }})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except (TypeError, ValueError):
                self._json(400, {"error": "guest_invite_unavailable"})
            return
        presence_path = urlsplit(self.path).path
        if presence_path in ("/v1/presence/heartbeat", "/v1/presence/leave"):
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                if presence_path.endswith("/heartbeat"):
                    payload = self._read_json(max_length=12000)
                    active_rooms = payload.get("activeConversationIds", [])
                    result = self.backend.heartbeat_presence(self._auth(), active_rooms)
                    event_type = "AI_PRESENCE_HEARTBEAT"
                else:
                    result = {"left": self.backend.leave_presence(self._auth())}
                    event_type = "AI_PRESENCE_LEFT"
                self._audit(identity, event_type, principal.ai_id)
                self._json(200, {"presence": result,
                                 "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except (TypeError, ValueError):
                self._json(400, {"error": "invalid_presence_request"})
            return
        guest_provision_path = urlsplit(self.path).path.split("/")
        if (len(guest_provision_path) == 7
                and guest_provision_path[1:3] == ["v1", "conversations"]
                and guest_provision_path[4] == "guest-applications"
                and guest_provision_path[5] and guest_provision_path[6] in ("provision", "revoke")):
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                if guest_provision_path[6] == "provision":
                    result = self.backend.provision_guest_application(
                        self._auth(), guest_provision_path[3], guest_provision_path[5])
                    self._audit(identity, "GUEST_CREDENTIAL_PROVISIONED",
                                result["identity"]["aiId"],
                                conversation_id=guest_provision_path[3],
                                application_id=guest_provision_path[5])
                    self._json(201, {"provisioning": result,
                                     "correlationId": identity.correlation_id})
                else:
                    result = self.backend.revoke_guest_provisioning(
                        self._auth(), guest_provision_path[3], guest_provision_path[5])
                    self._audit(identity, "GUEST_CREDENTIAL_REVOKED",
                                result["aiId"], conversation_id=guest_provision_path[3])
                    self._json(200, {"provisioning": result,
                                     "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except (TypeError, ValueError, KeyError, RuntimeError):
                self._json(400, {"error": "guest_provisioning_unavailable"})
            return
        guest_decision_path = urlsplit(self.path).path.split("/")
        if (len(guest_decision_path) == 6 and guest_decision_path[1:3] == ["v1", "conversations"]
                and guest_decision_path[4] == "guest-applications"
                and guest_decision_path[5] and guest_decision_path[3]):
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                payload = self._read_json(max_length=500)
                result = self.backend.decide_guest_application(
                    self._auth(), guest_decision_path[3], guest_decision_path[5],
                    payload.get("decision"))
                self._audit(identity, "GUEST_APPLICATION_DECIDED",
                            result["application_id"], conversation_id=guest_decision_path[3],
                            decision=result["status"])
                self._json(200, {"application": result,
                                 "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except (TypeError, ValueError):
                self._json(400, {"error": "guest_application_unavailable"})
            return
        invite_path = urlsplit(self.path).path.split("/")
        if len(invite_path) == 4 and invite_path[1:3] == ["v1", "invites"] and invite_path[3] == "redeem":
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                payload = self._read_json(max_length=2000)
                result = self.backend.redeem_room_invite(self._auth(), payload.get("token"))
                self._audit(identity, "ROOM_JOIN_REQUESTED", result["requestId"],
                            conversation_id=result["conversationId"])
                self._json(202, {"request": result, "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except (TypeError, ValueError):
                self._json(400, {"error": "invite_unavailable"})
            return
        if (len(invite_path) == 5 and invite_path[1:3] == ["v1", "conversations"]
                and invite_path[4] == "invites" and invite_path[3]):
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                payload = self._read_json()
                result = self.backend.create_room_invite(
                    self._auth(), invite_path[3],
                    payload.get("expiresInSeconds", 86400),
                    payload.get("maxUses", 5))
                self._audit(identity, "ROOM_INVITE_CREATED", result["inviteId"],
                            conversation_id=invite_path[3],
                            expires_at=str(result["expiresAt"]))
                self._json(201, {"invite": result, "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except (TypeError, ValueError):
                self._json(400, {"error": "invalid_invite_request"})
            return
        if (len(invite_path) == 7 and invite_path[1:3] == ["v1", "conversations"]
                and invite_path[4] == "join-requests" and invite_path[6] == "decision"):
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                payload = self._read_json()
                result = self.backend.decide_join_request(
                    self._auth(), invite_path[3], invite_path[5], payload.get("decision"))
                self._audit(identity, "ROOM_JOIN_REQUEST_DECIDED", invite_path[5],
                            decision=result["status"], invited_ai_id=result["aiId"])
                self._json(200, {"request": result, "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except (TypeError, ValueError):
                self._json(400, {"error": "invalid_join_request"})
            return
        call_path = urlsplit(self.path).path.split("/")
        if urlsplit(self.path).path == "/v1/calls" or (
                len(call_path) == 4 and call_path[1:3] == ["v1", "calls"] and call_path[3]) or (
                len(call_path) == 5 and call_path[1:3] == ["v1", "calls"] and call_path[3]
                and call_path[4] in ("accept", "reject", "cancel", "end", "connecting", "connected", "signals")):
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                if self.voice_calls is None:
                    self._json(503, {"error": "voice_call_service_unavailable"})
                    return
                if urlsplit(self.path).path == "/v1/calls":
                    payload = self._read_json()
                    target = payload.get("calleeAiId")
                    conversation_id = payload.get("conversationId")
                    call = self.voice_calls.create(
                        principal.ai_id, target, conversation_id,
                        self.backend.conversation_members(),
                        self.backend.conversation_kinds())
                    self._audit(identity, "VOICE_CALL_INVITED", call["call_id"],
                                callee_ai_id=target)
                    self._json(201, {"call": call, "correlationId": identity.correlation_id})
                    return
                if len(call_path) == 4:
                    self._json(405, {"error": "method_not_allowed"})
                    return
                call_id, action = call_path[3], call_path[4]
                if action == "signals":
                    payload = self._read_json(max_length=30000)
                    result = self.voice_calls.add_signal(
                        principal.ai_id, call_id, payload.get("kind"), payload.get("payload"))
                    self._audit(identity, "VOICE_CALL_SIGNAL_SENT", call_id,
                                signal_kind=payload.get("kind"))
                    self._json(201, {"signal": result, "correlationId": identity.correlation_id})
                    return
                if action in ("connecting", "connected"):
                    call = (self.voice_calls.set_connecting(principal.ai_id, call_id)
                            if action == "connecting" else
                            self.voice_calls.set_connected(principal.ai_id, call_id))
                else:
                    call = self.voice_calls.transition(principal.ai_id, call_id, action)
                self._audit(identity, "VOICE_CALL_STATE_CHANGED", call_id,
                            state=call["state"])
                self._json(200, {"call": call, "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except RuntimeError as exc:
                self._json(409, {"error": str(exc)})
            except (TypeError, ValueError, KeyError) as exc:
                self._json(400, {"error": str(exc) or "invalid_voice_call_request"})
            return
        voice_path = urlsplit(self.path).path.split("/")
        if (len(voice_path) == 6 and voice_path[1:3] == ["v1", "conversations"]
                and voice_path[4] == "voice" and voice_path[5] in ("mute", "unmute")
                and voice_path[3]):
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                if self.voice_control is None:
                    self._json(503, {"error": "voice_admin_control_unavailable"})
                    return
                payload = self._read_json()
                target_ai_id = payload.get("targetAiId")
                action = voice_path[5]
                if action == "mute":
                    duration_seconds = payload.get(
                        "durationSeconds", self.voice_control.DEFAULT_MUTE_SECONDS)
                    result = self.voice_control.mute(
                        principal.ai_id, voice_path[3], target_ai_id,
                        self.backend.conversation_members(), duration_seconds)
                    event_type = "VOICE_PARTICIPANT_MUTED"
                else:
                    result = self.voice_control.unmute(
                        principal.ai_id, voice_path[3], target_ai_id,
                        self.backend.conversation_members())
                    event_type = "VOICE_PARTICIPANT_UNMUTED"
                self._audit(identity, event_type, voice_path[3],
                            target_ai_id=target_ai_id)
                self._json(200, {"voiceControl": result,
                                 "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except (TypeError, ValueError):
                self._json(400, {"error": "invalid_voice_control_request"})
            return
        if self.path == "/v1/gpt6/realtime/client-secret":
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                if self.openai_text is None or not self.openai_text.api_calls_enabled():
                    self._json(503, {"error": "openai_api_calls_disabled"})
                    return
                if not self.openai_text.enabled():
                    self._json(503, {"error": "openai_api_not_configured"})
                    return
                result = self.openai_text.create_realtime_client_secret()
                self._audit(identity, "GPT6_REALTIME_CLIENT_SECRET_CREATED", "AI-GPT6")
                self._json(200, {
                    "assistant": {"id": "AI-GPT6", "displayName": "GPT-6"},
                    **result,
                    "correlationId": identity.correlation_id,
                })
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403, self._permission_error(exc))
            except RuntimeError as exc:
                self._json(502, {"error": str(exc)})
            return

        if urlsplit(self.path).path == "/v1/gpt6/room/respond":
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                if self.gpt6_room_agent is None:
                    self._json(503, {"error": "gpt6_room_agent_unavailable"})
                    return
                payload = self._read_json(max_length=12000)
                if set(payload) != {"conversationId", "message", "clientRequestId"}:
                    raise ValueError("invalid_gpt6_room_request")
                result = self.gpt6_room_agent.respond(
                    self._auth(), payload["conversationId"], payload["message"],
                    payload["clientRequestId"])
                self._audit(identity, "GPT6_ROOM_RESPONSE_CREATED",
                            result["assistantMessage"]["messageId"],
                            model=result.get("model") or "unknown")
                self._json(200, result)
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except RuntimeError as exc:
                if str(exc) in ("openai_api_calls_disabled", "openai_api_not_configured",
                                "gpt6_room_agent_unavailable"):
                    self._json(503, {"error": str(exc)})
                elif str(exc).startswith("openai_http_"):
                    self._json(502, {"error": "openai_upstream_error"})
                else:
                    self._json(502, {"error": "gpt6_provider_error"})
            except (TypeError, ValueError, KeyError):
                self._json(400, {"error": "invalid_gpt6_room_request"})
            return

        if self.path == "/v1/gpt6/respond":
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                if self.openai_text is None or not self.openai_text.api_calls_enabled():
                    self._json(503, {"error": "openai_api_calls_disabled"})
                    return
                if not self.openai_text.enabled():
                    self._json(503, {"error": "openai_api_not_configured"})
                    return
                payload = self._read_json(max_length=20000)
                result = self.openai_text.respond(
                    payload.get("message", ""),
                    payload.get("previousResponseId") or None,
                )
                self._audit(identity, "GPT6_RESPONSE_CREATED", result.get("responseId") or "unknown",
                            model=result.get("model", "unknown"))
                self._json(200, {
                    "assistant": {"id": "AI-GPT6", "displayName": "GPT-6", "online": False},
                    "connectionState": "REQUEST_SUCCEEDED",
                    "requestSucceeded": True,
                    "responseId": result.get("responseId"),
                    "model": result.get("model"),
                    "text": result["text"],
                    "correlationId": identity.correlation_id,
                })
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403, self._permission_error(exc))
            except RuntimeError as exc:
                if str(exc) == "openai_api_not_configured":
                    self._json(503, {"error": str(exc)})
                elif str(exc).startswith("openai_http_"):
                    self._json(502, {"error": "openai_upstream_error"})
                else:
                    self._json(502, {"error": str(exc)})
            except (TypeError, ValueError, KeyError):
                self._json(400, {"error": "invalid_gpt6_request"})
            return
        if self.path=="/v1/conversations":
            try:
                identity=self._principal()
                principal=identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                payload=self._read_json()
                conversation=self.backend.create_conversation(
                    self._auth(), payload.get("conversationId"),
                    payload.get("memberAiIds"), payload.get("kind", "GROUP"))
                self._audit(identity, "CONVERSATION_CREATED",
                            conversation["conversationId"],
                            kind=conversation["kind"],
                            member_count=str(conversation["memberCount"]))
                self._json(201, {"conversation":conversation,
                                 "correlationId":identity.correlation_id})
            except RateLimitExceeded:
                self._json(429,{"error":"rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc)=="authentication_required" else 403,self._permission_error(exc))
            except (KeyError,TypeError,ValueError,json.JSONDecodeError):
                self._json(400,{"error":"invalid_conversation"})
            return
        if self.path=="/v1/messages":
            try:
                identity=self._principal()
                principal=identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                payload=self._read_json()
                claimed_sender = payload.get("senderAiId", "")
                self.backend.assert_authenticated_sender(self._auth(), claimed_sender)
                msg=self.backend.submit(self._auth(),payload["messageId"],payload["conversationId"],payload["recipientAiIds"],payload["body"],payload["clientRequestId"],payload.get("messageKind","NORMAL"))
                self._audit(identity, "MESSAGE_SUBMITTED", msg.message_id, sequence=str(msg.sequence))
                self._json(200,{"messageId":msg.message_id,"conversationId":msg.conversation_id,"recipientAiIds":list(msg.recipient_ai_ids),"sequence":msg.sequence,"state":"QUEUED","senderAiId":msg.sender_ai_id,"messageKind":msg.kind,"createdAtEpochMs":int(msg.created_at_epoch_seconds*1000),"correlationId":identity.correlation_id})
            except RateLimitExceeded:
                self._json(429,{"error":"rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc)=="authentication_required" else 403,self._permission_error(exc))
            except (KeyError,TypeError,ValueError,json.JSONDecodeError):
                self._json(400,{"error":"invalid_request"})
            return
        audio_path = urlsplit(self.path).path
        audio_parts = audio_path.split("/")
        if len(audio_parts) == 5 and audio_parts[1:3] == ["v1", "messages"] and audio_parts[4] == "audio" and audio_parts[3]:
            try:
                identity=self._principal()
                principal=identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                content_type=self.headers.get("Content-Type","").split(";")[0].lower()
                raw_length=self.headers.get("Content-Length","")
                length=int(raw_length)
                if length < 1 or length > AudioBlobStore.MAX_AUDIO_BYTES:
                    raise ValueError("invalid_audio_length")
                data=self.rfile.read(length)
                if len(data) != length:
                    raise ValueError("invalid_audio_length")
                attachment=self.backend.attach_audio(self._auth(),audio_parts[3],self.audio_store,data,content_type)
                self._audit(identity,"AUDIO_ATTACHED",attachment.object_id,message_id=attachment.message_id,size=str(attachment.size))
                self._json(201,{"attachment":{"objectId":attachment.object_id,"messageId":attachment.message_id,"contentType":attachment.content_type,"size":attachment.size,"sha256":attachment.sha256},"correlationId":identity.correlation_id})
            except RateLimitExceeded:
                self._json(429,{"error":"rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc)=="authentication_required" else 403,self._permission_error(exc))
            except ValueError as exc:
                if str(exc) == "message_not_found":
                    self._json(404,{"error":"message_not_found"})
                else:
                    self._json(400,{"error":"invalid_audio"})
            except (TypeError,KeyError):
                self._json(400,{"error":"invalid_audio"})
            return
        ack_path = urlsplit(self.path).path
        ack_parts = ack_path.split("/")
        if len(ack_parts) == 5 and ack_parts[1:3] == ["v1", "messages"] and ack_parts[4] == "ack" and ack_parts[3]:
            try:
                identity=self._principal()
                principal=identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                msg=self.backend.acknowledge(self._auth(),ack_parts[3])
                self._audit(identity, "MESSAGE_ACKNOWLEDGED", msg.message_id)
                self._json(200,{"messageId":msg.message_id,"state":"ACKNOWLEDGED","principalAiId":principal.ai_id,"correlationId":identity.correlation_id})
            except RateLimitExceeded:
                self._json(429,{"error":"rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc)=="authentication_required" else 403,self._permission_error(exc))
            return
        self._json(404,{"error":"not_found"})

    def do_DELETE(self):
        parts = urlsplit(self.path).path.split("/")
        if (len(parts) == 6 and parts[1:3] == ["v1", "conversations"]
                and parts[4] == "invites" and parts[3] and parts[5]):
            try:
                identity = self._principal()
                principal = identity.principal
                self.backend.assert_authenticated_principal(self._auth(), principal)
                self.rate_limiter.allow(principal.ai_id)
                result = self.backend.revoke_room_invite(
                    self._auth(), parts[3], parts[5])
                self._audit(identity, "ROOM_INVITE_REVOKED", parts[5],
                            conversation_id=parts[3])
                self._json(200, {"invite": result,
                                 "correlationId": identity.correlation_id})
            except RateLimitExceeded:
                self._json(429, {"error": "rate_limit_exceeded"})
            except PermissionError as exc:
                self._json(401 if str(exc) == "authentication_required" else 403,
                           self._permission_error(exc))
            except ValueError:
                self._json(404, {"error": "invite_not_found"})
            return
        self._json(404, {"error": "not_found"})

    def log_message(self,*_args): return

def serve(host="127.0.0.1",port=8080):
    tokens=RuntimeConfig.auth_tokens()
    authenticator=Authenticator(tokens)
    from server.voice_room_control import VoiceRoomControl
    store=SQLiteMessengerStore(RuntimeConfig.storage_path())
    voice_control=VoiceRoomControl(RuntimeConfig.voice_admin_ids(tokens), store=store)
    backend=MessengerBackend(tokens,{"default":set(tokens.values()) | {"AI-GPT6"}},store,authenticator=authenticator,identity_display_names={"AI-GPT6":"GPT-6"},internal_ai_ids={"AI-GPT6"})
    MessengerHandler.backend=backend
    MessengerHandler.authenticator=authenticator
    MessengerHandler.voice_control=voice_control
    from server.voice_call_control import VoiceCallControl
    MessengerHandler.voice_calls=VoiceCallControl(store)
    from server.operational_runtime import OperationalRuntime
    MessengerHandler.operational=OperationalRuntime()
    MessengerHandler.audio_store=AudioBlobStore(str(Path(RuntimeConfig.storage_path()).resolve().parent / "audio"))
    MessengerHandler.openai_text=OpenAITextAdapter()
    MessengerHandler.provider_registry=ProviderRegistry(MessengerHandler.openai_text)
    MessengerHandler.gpt6_room_agent=GPT6RoomAgent(backend, MessengerHandler.openai_text)
    MessengerHandler.provider_host = None
    host_key_hex = RuntimeConfig.optional("AI_PROVIDER_HOST_HMAC_KEY_HEX", "")
    if host_key_hex:
        try:
            host_key = bytes.fromhex(host_key_hex)
        except ValueError as exc:
            raise RuntimeError("invalid_runtime_config:AI_PROVIDER_HOST_HMAC_KEY_HEX") from exc
        def authorize_provider_agent(principal_id, conversation_id, agent_id):
            members = backend.conversation_members().get(conversation_id, set())
            kinds = backend.conversation_kinds()
            return (principal_id == agent_id and len(members) == 2
                    and agent_id in members and kinds.get(conversation_id) == "PRIVATE")
        def resolve_agent_provider(agent_id):
            if (agent_id not in set(tokens.values())
                    or not MessengerHandler.openai_text.enabled()
                    or not MessengerHandler.openai_text.api_calls_enabled()):
                return None
            def invoke(prompt):
                response = MessengerHandler.openai_text.respond(prompt)
                return {
                    "text": response.get("text", ""),
                    "providerId": "openai",
                    "model": response.get("model", MessengerHandler.openai_text.model),
                }
            return invoke
        MessengerHandler.provider_host = AuthenticatedProviderHost(
            authenticate=backend.authenticate,
            authorize_agent=authorize_provider_agent,
            resolve_provider=resolve_agent_provider,
            attestation_key=host_key,
            server_identity="AI-BRIDGE-MESSENGER",
        )
    from server.guest_web_session import GuestWebSessionService
    MessengerHandler.guest_sessions=GuestWebSessionService(authenticator)
    server = ThreadingHTTPServer((host, port), MessengerHandler)
    server.daemon_threads = True
    try:
        server.serve_forever()
    finally:
        server.shutdown()
        server.server_close()
        backend.close()