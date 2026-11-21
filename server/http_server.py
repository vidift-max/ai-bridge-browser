import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from server.messenger_backend import MessengerBackend

class MessengerHandler(BaseHTTPRequestHandler):
    backend = None

    @staticmethod
    def _permission_status(exc):
        return 401 if str(exc) == "authentication_required" else 403

    def _auth(self):
        header = self.headers.get("Authorization", "")
        return header[7:] if header.startswith("Bearer ") else ""

    def _read_json(self):
        if self.headers.get("Content-Type", "").split(";")[0].lower() != "application/json":
            raise ValueError("content_type_required")
        length = int(self.headers.get("Content-Length", "0"))
        if length < 1 or length > 10000:
            raise ValueError("invalid_content_length")
        return json.loads(self.rfile.read(length))

    def _json(self, status, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parts = self.path.split("/")
        if len(parts) == 5 and parts[1:3] == ["v1", "conversations"] and parts[4] == "messages":
            try:
                messages = self.backend.pending(self._auth(), parts[3])
                self._json(200, {"messages": [{"messageId": m.message_id, "conversationId": m.conversation_id, "senderAiId": m.sender_ai_id, "sequence": m.sequence, "body": m.body} for m in messages]})
            except PermissionError as exc:
                self._json(self._permission_status(exc), {"error": str(exc)})
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path == "/v1/messages":
            try:
                payload = self._read_json()
                msg = self.backend.submit(self._auth(), payload["messageId"], payload["conversationId"], payload["recipientAiIds"], payload["body"], payload["clientRequestId"])
                self._json(200, {"messageId": msg.message_id, "sequence": msg.sequence, "state": "QUEUED"})
            except PermissionError as exc:
                self._json(403, {"error": str(exc)})
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                self._json(400, {"error": str(exc)})
            return
        if self.path.startswith("/v1/messages/") and self.path.endswith("/ack"):
            try:
                msg = self.backend.acknowledge(self._auth(), self.path[len("/v1/messages/"):-len("/ack")])
                self._json(200, {"messageId": msg.message_id, "state": "ACKNOWLEDGED"})
            except PermissionError as exc:
                self._json(403, {"error": str(exc)})
            return
        self._json(404, {"error": "not_found"})

    def log_message(self, *_args):
        return

def serve(host="127.0.0.1", port=8080):
    backend = MessengerBackend({"demo-a": "AI-A", "demo-b": "AI-B"}, {"demo": {"AI-A", "AI-B"}})
    MessengerHandler.backend = backend
    HTTPServer((host, port), MessengerHandler).serve_forever()
