"""Fail-closed, in-memory TOOL_USE authorization primitives.

This module does not authenticate callers and does not persist grants. Callers
must pass an AI identity obtained from the authenticated request context.
"""
from dataclasses import dataclass
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

    def __init__(self, grants: Mapping[str, Iterable[str]] = None):
        self._grants: Dict[str, FrozenSet[str]] = {}
        for principal, tool_ids in (grants or {}).items():
            if not isinstance(principal, str) or not principal or principal.strip() != principal:
                raise ValueError("invalid_tool_permission_principal")
            normalized = frozenset(tool_ids)
            if not normalized.issubset(SUPPORTED_TOOL_IDS):
                raise ValueError("unsupported_tool_permission")
            self._grants[principal] = normalized

    def can_use(self, principal_ai_id: str, tool_id: str) -> bool:
        if not principal_ai_id or not tool_id or tool_id not in SUPPORTED_TOOL_IDS:
            return False
        return tool_id in self._grants.get(principal_ai_id, frozenset())

    def require(self, principal_ai_id: str, tool_id: str) -> ToolPermission:
        if not principal_ai_id:
            raise PermissionError("authentication_required")
        if tool_id not in SUPPORTED_TOOL_IDS:
            raise LookupError("tool_not_found")
        if not self.can_use(principal_ai_id, tool_id):
            raise PermissionError("tool_use_forbidden")
        return ToolPermission(principal_ai_id, frozenset({tool_id}))

    def permitted_tool_ids(self, principal_ai_id: str) -> FrozenSet[str]:
        if not principal_ai_id:
            return frozenset()
        return self._grants.get(principal_ai_id, frozenset())
