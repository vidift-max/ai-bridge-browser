"""Fail-closed HTTP service boundary for the AI Tool Hub.

Discovery is authenticated and filtered by explicit TOOL_USE grants.
Invocation is deliberately non-executable: a reviewed adapter is required.
"""
import json
import re
from pathlib import Path

from server.tool_permissions import SUPPORTED_TOOL_IDS, ToolPermissionRegistry


class ToolUnavailable(Exception):
    pass


class ToolNotImplemented(Exception):
    pass


class ToolHubService:
    _VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
    _STATUSES = {"BLOCKED_LICENSE_REVIEW", "BLOCKED_API_REVIEW", "READY"}
    _CATALOG_STATUSES = {"READY", "PARTIALLY_BLOCKED", "BLOCKED"}
    _REQUIRED_FIELDS = {
        "toolId", "version", "status", "enabled", "requiredPermission",
        "inputSchemaRef", "outputSchemaRef",
    }

    def __init__(self, catalog_path=None, permissions=None):
        path = Path(catalog_path) if catalog_path else (
            Path(__file__).resolve().parents[1] / "registry" / "tool-hub" / "catalog.json"
        )
        with path.open("r", encoding="utf-8") as handle:
            document = json.load(handle, object_pairs_hook=self._reject_duplicate_keys)
        self._catalog = self._validate_catalog(document)
        self._permissions = permissions if permissions is not None else ToolPermissionRegistry()

    @staticmethod
    def _reject_duplicate_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate_tool_catalog_key")
            result[key] = value
        return result

    @classmethod
    def _validate_catalog(cls, document):
        if not isinstance(document, dict):
            raise ValueError("invalid_tool_catalog")
        if document.get("catalogVersion") != 1:
            raise ValueError("unsupported_tool_catalog_version")
        if document.get("status") not in cls._CATALOG_STATUSES:
            raise ValueError("invalid_tool_catalog_status")
        tools = document.get("tools")
        if not isinstance(tools, list) or len(tools) != len(SUPPORTED_TOOL_IDS):
            raise ValueError("invalid_tool_catalog")
        catalog = {}
        for item in tools:
            if not isinstance(item, dict) or not cls._REQUIRED_FIELDS.issubset(item):
                raise ValueError("invalid_tool_catalog")
            tool_id = item.get("toolId")
            if not isinstance(tool_id, str) or tool_id not in SUPPORTED_TOOL_IDS or tool_id in catalog:
                raise ValueError("invalid_tool_catalog")
            if not isinstance(item.get("version"), str) or not cls._VERSION.fullmatch(item["version"]):
                raise ValueError("invalid_tool_version")
            status = item.get("status")
            enabled = item.get("enabled")
            if status not in cls._STATUSES or not isinstance(enabled, bool):
                raise ValueError("invalid_tool_state")
            if item.get("requiredPermission") != "TOOL_USE":
                raise ValueError("invalid_tool_permission_contract")
            input_ref = item.get("inputSchemaRef")
            output_ref = item.get("outputSchemaRef")
            if status == "READY":
                if not enabled or not cls._valid_schema_ref(input_ref) or not cls._valid_schema_ref(output_ref):
                    raise ValueError("ready_tool_requires_schemas")
            elif enabled or input_ref is not None or output_ref is not None:
                raise ValueError("blocked_tool_must_not_be_enabled")
            description = item.get("description", "")
            if not isinstance(description, str) or len(description) > 240:
                raise ValueError("invalid_tool_description")
            catalog[tool_id] = dict(item)
        if set(catalog) != set(SUPPORTED_TOOL_IDS):
            raise ValueError("incomplete_tool_catalog")
        states = [item["status"] for item in catalog.values()]
        expected_status = (
            "READY" if all(state == "READY" for state in states)
            else "BLOCKED" if all(state != "READY" for state in states)
            else "PARTIALLY_BLOCKED"
        )
        if document["status"] != expected_status:
            raise ValueError("catalog_status_mismatch")
        return catalog

    @staticmethod
    def _valid_schema_ref(value):
        if not isinstance(value, str) or not value or len(value) > 200:
            return False
        candidate = Path(value)
        return not candidate.is_absolute() and ".." not in candidate.parts and value.endswith(".schema.json")

    def discover(self, principal_ai_id):
        allowed = self._permissions.permitted_tool_ids(principal_ai_id)
        visible = []
        for tool_id in sorted(allowed):
            item = self._catalog.get(tool_id)
            if item and item["enabled"] is True and item["status"] == "READY":
                visible.append({
                    "toolId": tool_id,
                    "version": item["version"],
                    "description": item.get("description", ""),
                })
        return {"tools": visible}

    def invoke(self, principal_ai_id, tool_id):
        if not isinstance(tool_id, str) or tool_id not in SUPPORTED_TOOL_IDS:
            raise LookupError("tool_not_found")
        self._permissions.require(principal_ai_id, tool_id)
        item = self._catalog[tool_id]
        if item["enabled"] is not True or item["status"] != "READY":
            raise ToolUnavailable("tool_unavailable")
        # No executor is registered. Catalog readiness cannot execute code.
        raise ToolNotImplemented("tool_adapter_not_implemented")
