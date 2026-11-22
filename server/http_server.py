import json
from urllib.parse import parse_qs, urlsplit
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from server.auth import Authenticator
from server.messenger_backend import MessengerBackend
from server.runtime_config import RuntimeConfig
from server.sqlite_store import SQLiteMessengerStore
from server.rate_limit import SlidingWindowRateLimiter, RateLimitExceeded
from server.request_context import authenticate_request, bearer_token
from server.audio_blob_store import AudioBlobStore


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _reject_json_constant(_value):
    raise ValueError("invalid_json_constant")


class MessengerHandler(BaseHTTPRequestHandler):
    backend=None
    authenticator=None
    rate_limiter=SlidingWindowRateLimiter()
    operational=None
    audio_store=None

    def _auth(self):
        return bearer_token(self.headers)

    def _principal(self):
        return authenticate_request(self.authenticator, self.headers)

    def _read_json(self):
        if self.headers.get("Content-Type","").split(";")[0].lower()!="application/json":
            raise ValueError("content_type_required")
        raw_length=self.headers.get("Content-Length","")
        try:
            length=int(raw_length)
        except (TypeError, ValueError):
            raise ValueError("invalid_content_length")
        if length<1 or length>10000:
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

    def do_GET(self):
        if self.path=="/healthz":
            self._json(200,{"status":"ok","service":"ai-messenger-experimental"}); return
        if self.path=="/readyz":
            try:
                RuntimeConfig.auth_tokens()
                storage_mode = RuntimeConfig.validate_storage_contract()
                RuntimeConfig.request_timeout_seconds()
                RuntimeConfig.retry_limit()
                if self.operational is not None:
                    storage_ok, _ = self.operational.check_storage(RuntimeConfig.storage_path())
                    if not storage_ok:
                        self._json(503,{"status":"not_ready","error":"storage_unavailable_or_invalid"})
                        return
                self._json(200,{"status":"ready","storageMode":storage_mode})
            except RuntimeError:
                self._json(503,{"status":"not_ready","error":"runtime_configuration_invalid"})
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
        parts=parsed.path.split("/")
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
                self._json(200,{"principalAiId":principal.ai_id,"correlationId":identity.correlation_id,"messages":[{"messageId":m.message_id,"conversationId":m.conversation_id,"senderAiId":m.sender_ai_id,"sequence":m.sequence,"body":m.body} for m in messages]})
            except RateLimitExceeded:
                self._json(429,{"error":"rate_limit_exceeded"})
            except (ValueError, TypeError):
                self._json(400,{"error":"invalid_cursor"})
            except PermissionError as exc:
                self._json(401 if str(exc)=="authentication_required" else 403,self._permission_error(exc))
            return
        self._json(404,{"error":"not_found"})

    def do_POST(self):
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
                msg=self.backend.submit(self._auth(),payload["messageId"],payload["conversationId"],payload["recipientAiIds"],payload["body"],payload["clientRequestId"])
                self._audit(identity, "MESSAGE_SUBMITTED", msg.message_id, sequence=str(msg.sequence))
                self._json(200,{"messageId":msg.message_id,"sequence":msg.sequence,"state":"QUEUED","senderAiId":msg.sender_ai_id,"correlationId":identity.correlation_id})
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
            except (TypeError,ValueError,KeyError):
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

    def log_message(self,*_args): return

def serve(host="127.0.0.1",port=8080):
    tokens=RuntimeConfig.auth_tokens()
    authenticator=Authenticator(tokens)
    store=SQLiteMessengerStore(RuntimeConfig.storage_path())
    backend=MessengerBackend(tokens,{"default":set(tokens.values())},store,authenticator=authenticator)
    MessengerHandler.backend=backend
    MessengerHandler.authenticator=authenticator
    from server.operational_runtime import OperationalRuntime
    MessengerHandler.operational=OperationalRuntime()
    MessengerHandler.audio_store=AudioBlobStore(str(RuntimeConfig.storage_path()) + "/audio")
    server = ThreadingHTTPServer((host, port), MessengerHandler)
    server.daemon_threads = True
    try:
        server.serve_forever()
    finally:
        server.shutdown()
        server.server_close()
        backend.close()
