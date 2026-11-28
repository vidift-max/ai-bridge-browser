"""Fail-closed HTTP service boundary for the AI Tool Hub.

Discovery is authenticated and filtered by explicit TOOL_USE grants.
Invocation is intentionally non-executable until each tool has approved
rights, a READY catalog record, a versioned schema, and a reviewed adapter.
"""
import json
from pathlib import Path

from server.tool_permissions import SUPPORTED_TOOL_IDS, ToolPermissionRegistry


class ToolUnavailable(Exception):
    pass


class ToolNotImplemented(Exception):
    pass


class ToolHubService:
    def __init__(self, catalog_path=None, permissions=None):
        path = Path(catalog_path) if catalog_path else (
            Path(__file__).resolve().parents[1] / "registry" / "tool-hub" / "catalog.json"
        )
        with path.open("r", encoding="utf-8") as handle:
            document = json.load(handle)
        tools = document.get("tools")
        if not isinstance(tools, list):
            raise ValueError("invalid_tool_catalog")
        self._catalog = {}
        for item in tools:
            if not isinstance(item, dict):
                raise ValueError("invalid_tool_catalog")
            tool_id = item.get("toolId")
            if tool_id not in SUPPORTED_TOOL_IDS or tool_id in self._catalog:
                raise ValueError("invalid_tool_catalog")
            if not isinstance(item.get("enabled"), bool):
                raise ValueError("invalid_tool_catalog")
            self._catalog[tool_id] = dict(item)
        if set(self._catalog) != set(SUPPORTED_TOOL_IDS):
            raise ValueError("incomplete_tool_catalog")
        self._permissions = permissions or ToolPermissionRegistry()

    def discover(self, principal_ai_id):
        allowed = self._permissions.permitted_tool_ids(principal_ai_id)
        visible = []
        for tool_id in sorted(allowed):
            item = self._catalog.get(tool_id)
            if item and item.get("enabled") is True and item.get("status") == "READY":
                visible.append({
                    "toolId": tool_id,
                    "version": item["version"],
                    "description": item.get("description", ""),
                })
        return {"tools": visible}

    def invoke(self, principal_ai_id, tool_id):
        if tool_id not in SUPPORTED_TOOL_IDS:
            raise LookupError("tool_not_found")
        self._permissions.require(principal_ai_id, tool_id)
        item = self._catalog[tool_id]
        if item.get("enabled") is not True or item.get("status") != "READY":
            raise ToolUnavailable("tool_unavailable")
        # Deliberately no executor: READY is not sufficient until a reviewed
        # adapter and tool-specific schemas are registered in a later change.
        raise ToolNotImplemented("tool_adapter_not_implemented")
