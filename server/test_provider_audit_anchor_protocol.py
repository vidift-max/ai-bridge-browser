import unittest

import server.provider_audit_anchor_protocol as protocol_module
from server.provider_audit_anchor_protocol import ProviderAuditAnchor
from server.provider_audit_durable_anchor import SQLiteDurableAuditAnchor
from server.test_provider_audit_remote_anchor import FakeRemoteAnchor


class ProviderAuditAnchorProtocolTests(unittest.TestCase):
    def test_reference_and_fake_adapters_expose_required_shape(self):
        self.assertIsInstance(FakeRemoteAnchor(), ProviderAuditAnchor)

    def test_sqlite_reference_adapter_exposes_required_shape(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            adapter = SQLiteDurableAuditAnchor(str(Path(directory) / "anchor.sqlite"))
            self.assertIsInstance(adapter, ProviderAuditAnchor)

    def test_incomplete_adapter_is_not_compatible(self):
        class ReadOnly:
            def read_latest(self):
                return None
        self.assertNotIsInstance(ReadOnly(), ProviderAuditAnchor)

    def test_protocol_documentation_disclaims_independence_proof(self):
        self.assertIn("shape only", protocol_module.__doc__ or "")


if __name__ == "__main__":
    unittest.main()
