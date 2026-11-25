"""Explicit, fail-closed composition gate for Messenger Provider Audit routes.

This factory does not create storage, read environment credentials, start a
listener, or mutate MessengerHandler. Production activation remains a separate
operator-controlled integration step.
"""
from server.provider_audit_remote_service import ProviderAuditRemoteService


def build_provider_audit_messenger_service(
        *, enabled=False, anchor=None, authenticate_token=None,
        authorize_principal=None, max_body_bytes=8192):
    """Build the opt-in service only from explicitly injected dependencies.

    The default path is disabled and returns None. Enabling requires an
    independently provisioned anchor adapter and both authentication and
    authorization callbacks. No default-allow policy is provided.
    """
    if type(enabled) is not bool:
        raise ValueError("invalid_provider_audit_enabled")
    if not enabled:
        return None
    if anchor is None:
        raise ValueError("provider_audit_anchor_required")
    if not callable(getattr(anchor, "read_latest", None)) or not callable(
            getattr(anchor, "append_checkpoint", None)):
        raise ValueError("provider_audit_anchor_contract_invalid")
    if not callable(authenticate_token):
        raise ValueError("provider_audit_authenticator_required")
    if not callable(authorize_principal):
        raise ValueError("provider_audit_authorizer_required")
    return ProviderAuditRemoteService(
        anchor,
        authenticate_token=authenticate_token,
        authorize_principal=authorize_principal,
        max_body_bytes=max_body_bytes,
    )
