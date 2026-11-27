import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const script = fs.readFileSync(path.join(root, "scripts", "verify-firebase-live.mjs"), "utf8");

test("live smoke checks only the two official Hosting domains", () => {
  assert.match(script, /https:\/\/ai-messenger-b97df\.web\.app/);
  assert.match(script, /https:\/\/ai-messenger-b97df\.firebaseapp\.com/);
  assert.match(script, /ai-messenger-b97df-default-rtdb\.firebaseio\.com/);
});

test("live smoke targets the invite route, not an assumed homepage", () => {
  assert.match(script, /\/i\/smoke-conversation\/abcdefghijklmnopqrst/);
  assert.match(script, /Convite AI Messenger/);
  assert.doesNotMatch(script, /origin \+ ["']\/["']/);
});

test("requests are read-only GETs and do not follow redirects", () => {
  assert.match(script, /method: ["']GET["']/);
  assert.match(script, /redirect: ["']manual["']/);
  assert.doesNotMatch(script, /method: ["'](POST|PUT|PATCH|DELETE)["']/);
});

test("network requests have a bounded timeout", () => {
  assert.match(script, /timeoutMs = 15_000/);
  assert.match(script, /AbortSignal\.timeout\(timeoutMs\)/);
});

test("invite route must return HTTP 200 and HTML", () => {
  assert.match(script, /response\.status !== 200/);
  assert.match(script, /includes\(["']text\/html["']\)/);
  assert.match(script, /<h1>Convite AI Messenger<\/h1>/);
});

test("unauthenticated database read must be denied", () => {
  assert.match(script, /response\.status !== 401 && response\.status !== 403/);
  assert.match(script, /permission denied/i);
  assert.match(script, /FIREBASE_DATABASE_PUBLIC_READ_BLOCKED/);
});

test("smoke verification never supplies credentials or writes Firebase data", () => {
  assert.doesNotMatch(script, /Authorization|Bearer |service.account|access.token|idToken/i);
  assert.doesNotMatch(script, /\.set\(|\.update\(|\.remove\(|\.push\(/);
});

test("success marker is emitted only when all checks pass", () => {
  assert.match(script, /if \(process\.exitCode !== 1\) console\.log\("FIREBASE_LIVE_SMOKE_OK/);
});
