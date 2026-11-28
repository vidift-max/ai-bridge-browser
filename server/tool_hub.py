"""Authenticated Tool Hub with independently authored local adapters."""
import json
import re
from pathlib import Path

from server.tool_adapters import execute_tool, ToolInputError, MAX_OUTPUT_BYTES
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
        self._root = Path(__file__).resolve().parents[1]
        path = Path(catalog_path) if catalog_path else self._root / "registry" / "tool-hub" / "catalog.json"
        with path.open("r", encoding="utf-8") as handle:
            document = json.load(handle, object_pairs_hook=self._reject_duplicate_keys)
        self._catalog = self._validate_catalog(document)
        self._schemas = self._load_schema_files(self._catalog)
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
        if type(document.get("catalogVersion")) is not int or document.get("catalogVersion") != 1:
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
            status, enabled = item.get("status"), item.get("enabled")
            if status not in cls._STATUSES or not isinstance(enabled, bool):
                raise ValueError("invalid_tool_state")
            if item.get("requiredPermission") != "TOOL_USE":
                raise ValueError("invalid_tool_permission_contract")
            input_ref, output_ref = item.get("inputSchemaRef"), item.get("outputSchemaRef")
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
        expected = "READY" if all(s == "READY" for s in states) else (
            "BLOCKED" if all(s != "READY" for s in states) else "PARTIALLY_BLOCKED")
        if document["status"] != expected:
            raise ValueError("catalog_status_mismatch")
        return catalog

    @classmethod
    def _valid_schema_ref(cls, value):
        if not isinstance(value, str) or not value or len(value) > 200:
            return False
        candidate = Path(value)
        return (not candidate.is_absolute() and ".." not in candidate.parts
                and value.endswith(".schema.json"))

    def _load_schema_files(self, catalog):
        schema_root = (self._root / "registry" / "tool-hub" / "schemas").resolve()
        loaded = {}
        for tool_id, item in catalog.items():
            if item["status"] != "READY":
                continue
            loaded[tool_id] = {}
            for key in ("inputSchemaRef", "outputSchemaRef"):
                candidate = (self._root / item[key]).resolve()
                if not candidate.is_relative_to(schema_root) or not candidate.is_file():
                    raise ValueError("tool_schema_file_missing")
                with candidate.open("r", encoding="utf-8") as handle:
                    schema = json.load(handle, object_pairs_hook=self._reject_duplicate_keys)
                if not isinstance(schema, dict) or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                    raise ValueError("invalid_tool_schema")
                loaded[tool_id]["inputSchema" if key == "inputSchemaRef" else "outputSchema"] = schema
        return loaded

    @property
    def permissions(self):
        return self._permissions

    def discover(self, principal_ai_id):
        allowed = self._permissions.permitted_tool_ids(principal_ai_id)
        visible = []
        for tool_id in sorted(allowed):
            item = self._catalog.get(tool_id)
            if item and item["enabled"] is True and item["status"] == "READY":
                visible.append({"toolId": tool_id, "version": item["version"],
                                "description": item.get("description", ""),
                                "inputSchema": self._schemas[tool_id]["inputSchema"],
                                "outputSchema": self._schemas[tool_id]["outputSchema"]})
        return {"tools": visible}

    def invoke(self, principal_ai_id, tool_id, request):
        if not isinstance(tool_id, str) or tool_id not in SUPPORTED_TOOL_IDS:
            raise LookupError("tool_not_found")
        self._permissions.require(principal_ai_id, tool_id)
        item = self._catalog[tool_id]
        if item["enabled"] is not True or item["status"] != "READY":
            raise ToolUnavailable("tool_unavailable")
        if not isinstance(request, dict) or set(request) != {"requestId", "toolVersion", "input"}:
            raise ToolInputError("INVALID_REQUEST")
        request_id = request.get("requestId")
        if not isinstance(request_id, str) or not re.fullmatch(
                r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}",
                request_id):
            raise ToolInputError("INVALID_REQUEST")
        if request.get("toolVersion") != item["version"]:
            raise ToolInputError("UNSUPPORTED_VERSION")
        result = execute_tool(tool_id, request.get("input"))
        encoded = json.dumps(result, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode("utf-8")
        if len(encoded) > MAX_OUTPUT_BYTES:
            raise ToolInputError("OUTPUT_TOO_LARGE")
        return {"requestId": request_id, "toolId": tool_id, "status": "SUCCEEDED", "result": result}
