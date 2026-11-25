import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const design = await readFile(new URL("../docs/MISSION_130_GUEST_STATUS_CAPABILITY.md", import.meta.url), "utf8");
const invite = await readFile(new URL("./invite.html", import.meta.url), "utf8");
const http = await readFile(new URL("../server/http_server.py", import.meta.url), "utf8");
const store = await readFile(new URL("../server/sqlite_store.py", import.meta.url), "utf8");

test("status capability is separate from public application ID and invite token", () => {
  assert.match(design, /32 random bytes/);
  assert.match(design, /SHA-256\(token\) only/);
  assert.match(design, /Application ID alone, invite token.*must never authorize status lookup/);
  assert.match(design, /X-Guest-Status-Token/);
});

test("status capability is header-only and avoids URL and browser persistence leakage", () => {
  assert.match(design, /never URL query, path, referrer, localStorage, analytics, or logs/);
  assert.match(design, /redact this header/);
  assert.match(design, /Generic failure responses/);
});

test("status response is an explicit minimal allowlist with no PII or credentials", () => {
  assert.match(design, /applicationId.*status.*provisioningStatus.*statusCheckedAt/);
  assert.match(design, /no display name, provider claim, conversation\/room ID/);
  assert.match(design, /must not return or recreate the one-time guest credential/);
});

test("capability expiry, revocation, and polling limits are specified", () => {
  assert.match(design, /7-day expiry/);
  assert.match(design, /revoked/);
  assert.match(design, /minimum 30 seconds/);
  assert.match(design, /Retry-After/);
});

test("M129 runtime remains fail-closed: no public status route or implicit guest session", () => {
  assert.match(invite, /Esta página não consulta o estado automaticamente/);
  assert.doesNotMatch(http, /urlsplit\(self\.path\)\.path\s*==\s*["']\/v1\/guest-applications\/status/);
  assert.doesNotMatch(store, /status_token_hash/);
  assert.match(design, /architecture and contract mission only/);
});
