import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const workflow = fs.readFileSync(path.join(root, ".github", "workflows", "firebase-wif-readiness.yml"), "utf8");

test("WIF readiness workflow is manual-only", () => {
  assert.match(workflow, /workflow_dispatch:/);
  assert.doesNotMatch(workflow, /^\\s*(push|pull_request|schedule):/m);
});

test("WIF readiness requires exact confirmation and trusted branch", () => {
  assert.match(workflow, /VERIFY_FIREBASE_WIF/);
  assert.match(workflow, /inputs\\.confirm_verify == 'VERIFY_FIREBASE_WIF'/);
  assert.match(workflow, /github\\.ref == 'refs\\/heads\\/feat\\/mission-181-firebase-project-bootstrap'/);
});

test("WIF readiness uses the protected production environment and minimum permissions", () => {
  assert.match(workflow, /environment: firebase-production/);
  assert.match(workflow, /permissions:\\s*\\n\\s+contents: read\\s*\\n\\s+id-token: write/);
  assert.doesNotMatch(workflow, /contents: write|pull-requests: write/);
});

test("WIF authentication follows local configuration validation", () => {
  const validation = workflow.indexOf("node scripts/validate-firebase-wif-config.mjs");
  const auth = workflow.indexOf("google-github-actions/auth@v2");
  assert.ok(validation >= 0 && auth > validation);
});

test("workflow verifies token presence without printing it", () => {
  assert.match(workflow, /steps\\.auth\\.outputs\\.access_token/);
  assert.match(workflow, /test -n "\\$GOOGLE_ACCESS_TOKEN"/);
  assert.doesNotMatch(workflow, /echo "\\$GOOGLE_ACCESS_TOKEN"|print-access-token/);
});

test("WIF readiness does not deploy or mutate Firebase", () => {
  assert.doesNotMatch(workflow, /firebase deploy|firebase database:set|firebase hosting:channel:deploy/i);
  assert.match(workflow, /timeout-minutes: 10/);
  assert.match(workflow, /cancel-in-progress: false/);
});
