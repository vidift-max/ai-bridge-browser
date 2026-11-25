import concurrent.futures
import json
import os
import tempfile
import threading
import unittest
import urllib.request

from http.server import ThreadingHTTPServer

from server.provider_audit_durable_anchor import SQLiteDurableAuditAnchor
from server.provider_audit_http_server import create_provider_audit_http_server
from server.provider_audit_remote_service import ProviderAuditRemoteService


class ProviderAuditHTTPServerFactoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.anchor = SQLiteDurableAuditAnchor(os.path.join(self.temp.name, "anchor.sqlite"))
        self.service = ProviderAuditRemoteService(
            self.anchor,
            authenticate_token=lambda token: "factory-agent" if token == "factory-token" else None,
            authorize_principal=lambda principal: principal == "factory-agent",
        )

    def tearDown(self):
        self.temp.cleanup()

    def _start(self, server):
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return thread

    def test_factory_returns_threading_server_bound_to_ipv4_loopback(self):
        server = create_provider_audit_http_server(self.service)
        try:
            self.assertIsInstance(server, ThreadingHTTPServer)
            self.assertEqual(server.server_address[0], "127.0.0.1")
            self.assertGreater(server.server_address[1], 0)
            self.assertTrue(server.daemon_threads)
            self.assertTrue(server.block_on_close)
        finally:
            server.server_close()

    def test_factory_does_not_start_listener_implicitly(self):
        server = create_provider_audit_http_server(self.service)
        try:
            self.assertFalse(server._BaseServer__is_shut_down.is_set())
            self.assertFalse(server._BaseServer__shutdown_request)
        finally:
            server.server_close()

    def test_non_loopback_and_hostname_binds_are_rejected(self):
        for host in ("0.0.0.0", "192.0.2.10", "::1", "localhost"):
            with self.subTest(host=host):
                with self.assertRaisesRegex(ValueError, "loopback_host_required"):
                    create_provider_audit_http_server(self.service, host=host)

    def test_invalid_ports_are_rejected(self):
        for port in (-1, 65536, True, False, "0", 1.5, None):
            with self.subTest(port=port):
                with self.assertRaisesRegex(ValueError, "invalid_port"):
                    create_provider_audit_http_server(self.service, port=port)

    def test_invalid_service_is_rejected(self):
        for service in (None, object(), lambda: None):
            with self.subTest(service=service):
                with self.assertRaisesRegex(ValueError, "provider_audit_service_required"):
                    create_provider_audit_http_server(service)

    def test_factory_server_serves_authenticated_latest_request(self):
        server = create_provider_audit_http_server(self.service)
        thread = self._start(server)
        try:
            request = urllib.request.Request(
                "http://127.0.0.1:%d/v1/audit-anchor/latest" % server.server_address[1],
                headers={"Authorization": "Bearer factory-token"},
            )
            with urllib.request.urlopen(request, timeout=3) as response:
                self.assertEqual(response.status, 200)
                self.assertIsNone(json.loads(response.read())["record"])
                self.assertEqual(response.headers.get("Cache-Control"), "no-store")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
            self.assertFalse(thread.is_alive())

    def test_factory_server_rejects_missing_authentication(self):
        server = create_provider_audit_http_server(self.service)
        thread = self._start(server)
        try:
            request = urllib.request.Request(
                "http://127.0.0.1:%d/v1/audit-anchor/latest" % server.server_address[1]
            )
            with self.assertRaises(Exception) as caught:
                urllib.request.urlopen(request, timeout=3)
            self.assertEqual(getattr(caught.exception, "code", None), 401)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_factory_server_handles_parallel_authenticated_reads(self):
        server = create_provider_audit_http_server(self.service)
        thread = self._start(server)
        url = "http://127.0.0.1:%d/v1/audit-anchor/latest" % server.server_address[1]

        def read_latest(_):
            request = urllib.request.Request(
                url, headers={"Authorization": "Bearer factory-token"}
            )
            with urllib.request.urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read())["record"]

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(read_latest, range(16)))
            self.assertEqual(len(results), 16)
            self.assertTrue(all(status == 200 and record is None for status, record in results))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
            self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()
