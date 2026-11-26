"""Production composition for the authenticated two-agent messaging runtime.

This factory is shared by the HTTP server and integration tests so the live
startup path cannot drift from the path exercised by the two-agent tests.
It performs no provider network calls while constructing the runtime.
"""
from dataclasses import dataclass

from server.ai_conversation_host import AgentSessionRegistry, TwoAgentConversationHost
from server.ai_provider_host import AuthenticatedProviderHost
from server.agent_provider_router import AgentProviderRouter


@dataclass(frozen=True)
class TwoAgentRuntime:
    router: AgentProviderRouter
    provider_host: object = None
    session_registry: object = None
    conversation_host: object = None


def build_two_agent_runtime(backend, tokens, adapters, *, host_key_hex="", assignments=None):
    """Build the same provider/session/host graph used by the HTTP server.

    Missing host key leaves provider execution unavailable (fail closed), while
    invalid non-empty keys fail startup. Provider adapters remain policy-gated.
    """
    router = AgentProviderRouter(adapters, assignments)
    if not isinstance(host_key_hex, str) or not host_key_hex.strip():
        return TwoAgentRuntime(router=router)
    if (len(host_key_hex) != 64
            or any(char not in "0123456789abcdefABCDEF" for char in host_key_hex)):
        raise RuntimeError("invalid_runtime_config:AI_PROVIDER_HOST_HMAC_KEY_HEX")
    try:
        host_key = bytes.fromhex(host_key_hex)
    except ValueError as exc:
        raise RuntimeError("invalid_runtime_config:AI_PROVIDER_HOST_HMAC_KEY_HEX") from exc
    if len(host_key) != 32:
        raise RuntimeError("invalid_runtime_config:AI_PROVIDER_HOST_HMAC_KEY_HEX")

    def authorize_provider_agent(principal_id, conversation_id, agent_id):
        members = backend.conversation_members().get(conversation_id, set())
        kinds = backend.conversation_kinds()
        return (principal_id == agent_id and len(members) == 2
                and agent_id in members and kinds.get(conversation_id) == "PRIVATE")

    known_ai_ids = set(tokens.values())

    def resolve_agent_provider(agent_id):
        if agent_id not in known_ai_ids:
            return None
        return router.resolve(agent_id)

    provider_host = AuthenticatedProviderHost(
        authenticate=backend.authenticate,
        authorize_agent=authorize_provider_agent,
        resolve_provider=resolve_agent_provider,
        attestation_key=host_key,
        server_identity="AI-BRIDGE-MESSENGER",
    )
    session_registry = AgentSessionRegistry(backend)
    conversation_host = TwoAgentConversationHost(
        backend, provider_host, session_registry)
    return TwoAgentRuntime(
        router=router,
        provider_host=provider_host,
        session_registry=session_registry,
        conversation_host=conversation_host,
    )
