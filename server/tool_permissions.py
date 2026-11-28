"""Fail-closed TOOL_USE authorization with optional durable SQLite storage.

This module does not authenticate callers. Callers must pass an AI identity
obtained from the authenticated request context. Missing grants always deny.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, Mapping, FrozenSet


SUPPORTED_TOOL_IDS: FrozenSet[str] = frozenset({
    "duration_timer",
    "recipe_scaler",
    "quiz_engine",
    "svg_chart",
    "link_card",
})


@dataclass(frozen=True)
class ToolPermission:
    principal_ai_id: str
    tool_ids: FrozenSet[str]


class ToolPermissionRegistry:
    """Explicit per-principal tool grants; absent grants always deny."""

    def __init__(self, grants: Mapping[str, Iterable[str]] = None, store=None):
        self._grants: Dict[str, FrozenSet[str]] = {}
        self._store = store
        for principal, tool_ids in (grants or {}).items():
            if (not isinstance(principal, str) or not principal
                    or principal.strip() != principal):
                raise ValueError("invalid_tool_permission_principal")
            if isinstance(tool_ids, (str, bytes)):
                raise ValueError("invalid_tool_permission_grants")
            try:
                normalized = frozenset(tool_ids)
            except (TypeError, ValueError):
                raise ValueError("invalid_tool_permission_grants")
            if not all(isinstance(tool_id, str) for tool_id in normalized):
                raise ValueError("invalid_tool_permission_grants")
            if not normalized.issubset(SUPPORTED_TOOL_IDS):
                raise ValueError("unsupported_tool_permission")
            self._grants[principal] = normalized
        if self._store is not None:
            for row in self._store.load_tool_permissions():
                self._validate_principal(row["principal_ai_id"])
                if row["tool_id"] not in SUPPORTED_TOOL_IDS:
                    raise ValueError("unsupported_tool_permission")
                self._grants.setdefault(row["principal_ai_id"], frozenset())
                self._grants[row["principal_ai_id"]] = (
                    self._grants[row["principal_ai_id"]] | frozenset({row["tool_id"]})
                )

    @staticmethod
    def _validate_principal(principal_ai_id):
        if (not isinstance(principal_ai_id, str) or not principal_ai_id
                or principal_ai_id.strip() != principal_ai_id or len(principal_ai_id) > 200):
            raise ValueError("invalid_tool_permission_principal")

    def grant(self, principal_ai_id: str, tool_id: str, granted_by: str):
        self._validate_principal(principal_ai_id)
        if not isinstance(tool_id, str) or tool_id not in SUPPORTED_TOOL_IDS:
            raise ValueError("unsupported_tool_permission")
        self._validate_principal(granted_by)
        granted_at = datetime.now(timezone.utc).isoformat()
        if self._store is not None:
            self._store.grant_tool_permission(principal_ai_id, tool_id, granted_by, granted_at)
        self._grants[principal_ai_id] = self._grants.get(principal_ai_id, frozenset()) | frozenset({tool_id})
        return {"principalAiId": principal_ai_id, "toolId": tool_id,
                "grantedBy": granted_by, "grantedAt": granted_at}

    def revoke(self, principal_ai_id: str, tool_id: str, revoked_by: str = "tool-hub-admin"):
        self._validate_principal(principal_ai_id)
        if not isinstance(tool_id, str) or tool_id not in SUPPORTED_TOOL_IDS:
            raise ValueError("unsupported_tool_permission")
        removed = tool_id in self._grants.get(principal_ai_id, frozenset())
        self._validate_principal(revoked_by)
        if self._store is not None:
            revoked_at = datetime.now(timezone.utc).isoformat()
            removed = self._store.revoke_tool_permission(
                principal_ai_id, tool_id, revoked_by, revoked_at
            )
        current = self._grants.get(principal_ai_id, frozenset()) - frozenset({tool_id})
        if current:
            self._grants[principal_ai_id] = current
        else:
            self._grants.pop(principal_ai_id, None)
        return removed

    def list_audit_events(self):
        if self._store is None:
            return []
        return [
            {"auditId": row["audit_id"], "action": row["action"],
             "principalAiId": row["principal_ai_id"], "toolId": row["tool_id"],
             "actorId": row["actor_id"], "occurredAt": row["occurred_at"],
             "grantExisted": bool(row["grant_existed"])}
            for row in self._store.load_tool_permission_audit()
        ]

    def list_grants(self):
        if self._store is not None:
            return [
                {"principalAiId": row["principal_ai_id"], "toolId": row["tool_id"],
                 "grantedBy": row["granted_by"], "grantedAt": row["granted_at"]}
                for row in self._store.load_tool_permissions()
            ]
        return [
            {"principalAiId": principal, "toolId": tool_id,
             "grantedBy": "in-memory", "grantedAt": None}
            for principal, tool_ids in sorted(self._grants.items())
            for tool_id in sorted(tool_ids)
        ]

    def can_use(self, principal_ai_id: str, tool_id: str) -> bool:
        if (not isinstance(principal_ai_id, str) or not principal_ai_id
                or not isinstance(tool_id, str) or tool_id not in SUPPORTED_TOOL_IDS):
            return False
        return tool_id in self._grants.get(principal_ai_id, frozenset())

    def require(self, principal_ai_id: str, tool_id: str) -> ToolPermission:
        if not isinstance(principal_ai_id, str) or not principal_ai_id:
            raise PermissionError("authentication_required")
        if not isinstance(tool_id, str) or tool_id not in SUPPORTED_TOOL_IDS:
            raise LookupError("tool_not_found")
        if not self.can_use(principal_ai_id, tool_id):
            raise PermissionError("tool_use_forbidden")
        return ToolPermission(principal_ai_id, frozenset({tool_id}))

    def permitted_tool_ids(self, principal_ai_id: str) -> FrozenSet[str]:
        if not isinstance(principal_ai_id, str) or not principal_ai_id:
            return frozenset()
        return self._grants.get(principal_ai_id, frozenset())
