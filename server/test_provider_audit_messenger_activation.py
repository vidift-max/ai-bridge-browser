import unittest

from server.provider_audit_messenger_activation import (
    build_provider_audit_messenger_service,
)


class FakeAnchor:
    def read_latest(self):
        return None

    def append_checkpoint(self, expected_sequence, record):
        return record


class ProviderAuditMessengerActivationTests(unittest.TestCase):
    def test_default_is_disabled(self):
        self.assertIsNone(build_provider_audit_messenger_service())

    def test_disabled_ignores_unconfigured_dependencies(self):
        self.assertIsNone(build_provider_audit_messenger_service(
            enabled=False, anchor=object(), authenticate_token=None,
            authorize_principal=None))

    def test_enabled_flag_must_be_boolean(self):
        with self.assertRaisesRegex(ValueError, "invalid_provider_audit_enabled"):
            build_provider_audit_messenger_service(enabled="true")

    def test_enabled_requires_anchor(self):
        with self.assertRaisesRegex(ValueError, "provider_audit_anchor_required"):
            build_provider_audit_messenger_service(
                enabled=True, authenticate_token=lambda _token: None,
                authorize_principal=lambda _principal: False)

    def test_enabled_requires_anchor_contract(self):
        with self.assertRaisesRegex(ValueError, "provider_audit_anchor_contract_invalid"):
            build_provider_audit_messenger_service(
                enabled=True, anchor=object(),
                authenticate_token=lambda _token: None,
                authorize_principal=lambda _principal: False)

    def test_enabled_requires_authenticator(self):
        with self.assertRaisesRegex(ValueError, "provider_audit_authenticator_required"):
            build_provider_audit_messenger_service(
                enabled=True, anchor=FakeAnchor(),
                authorize_principal=lambda _principal: False)

    def test_enabled_requires_explicit_authorizer(self):
        with self.assertRaisesRegex(ValueError, "provider_audit_authorizer_required"):
            build_provider_audit_messenger_service(
                enabled=True, anchor=FakeAnchor(),
                authenticate_token=lambda _token: "agent")

    def test_explicit_dependencies_build_service_without_mounting_it(self):
        service = build_provider_audit_messenger_service(
            enabled=True,
            anchor=FakeAnchor(),
            authenticate_token=lambda token: "agent" if token == "secret" else None,
            authorize_principal=lambda principal: principal == "agent",
        )
        self.assertIsNotNone(service)
        self.assertEqual(service.max_body_bytes, 8192)
        self.assertEqual(service.handle(
            "GET", "/v1/audit-anchor/latest",
            {"Authorization": "Bearer secret"})[0], 200)
        self.assertEqual(service.handle(
            "GET", "/v1/audit-anchor/latest",
            {"Authorization": "Bearer wrong"})[0], 401)

    def test_custom_body_limit_is_validated_by_service(self):
        with self.assertRaisesRegex(ValueError, "invalid_max_body_bytes"):
            build_provider_audit_messenger_service(
                enabled=True, anchor=FakeAnchor(),
                authenticate_token=lambda _token: "agent",
                authorize_principal=lambda _principal: True,
                max_body_bytes=1)


if __name__ == "__main__":
    unittest.main()
