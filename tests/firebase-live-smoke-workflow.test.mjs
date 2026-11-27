import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const workflow = fs.readFileSync(path.join(root, ".github", "workflows", "firebase-live-smoke.yml"), "utf8");

test("live smoke workflow is manual-only", () => {
  assert.match(workflow, /workflow_dispatch:/);
  assert.doesNotMatch(workflow, /^\s*(push|pull_request|schedule):/m);
});

test("live smoke requires exact explicit confirmation", () => {
  assert.match(workflow, /confirm_verify:/);
  assert.match(workflow, /VERIFY_AI_MESSENGER/);
  assert.match(workflow, /inputs\.confirm_verify == 'VERIFY_AI_MESSENGER'/);
});

test("live smoke can run only from the reviewed bootstrap branch", () => {
  assert.match(workflow, /github\.ref == 'refs\/heads\/feat\/mission-181-firebase-project-bootstrap'/);
});

test("live smoke has read-only GitHub permissions and no Google authentication", () => {
  assert.match(workflow, /permissions:\s*\n\s+contents: read/);
  assert.doesNotMatch(workflow, /id-token:\s*write|google-github-actions\/auth|FIREBASE_WORKLOAD/);
});

test("live smoke runs the verifier and does not deploy", () => {
  assert.match(workflow, /node scripts\/verify-firebase-live\.mjs/);
  assert.doesNotMatch(workflow, /firebase deploy|npm install.*firebase-tools/i);
});

test("live smoke has bounded runtime and non-cancelling concurrency", () => {
  assert.match(workflow, /timeout-minutes: 5/);
  assert.match(workflow, /cancel-in-progress: false/);
});
