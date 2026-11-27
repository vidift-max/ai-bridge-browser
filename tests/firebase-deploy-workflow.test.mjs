import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const workflowPath = path.join(root, ".github", "workflows", "firebase-ai-messenger-deploy.yml");
const workflow = fs.readFileSync(workflowPath, "utf8");

test("Firebase production deployment is manual-only", () => {
  assert.match(workflow, /workflow_dispatch:/);
  assert.doesNotMatch(workflow, /^\s*(push|pull_request|schedule):/m);
});

test("deployment requires the exact typed confirmation", () => {
  assert.match(workflow, /confirm_deploy:/);
  assert.match(workflow, /DEPLOY_AI_MESSENGER/);
  assert.match(workflow, /inputs\.confirm_deploy == 'DEPLOY_AI_MESSENGER'/);
});

test("deployment is restricted to the reviewed bootstrap branch", () => {
  assert.match(workflow, /github\.ref == 'refs\/heads\/feat\/mission-181-firebase-project-bootstrap'/);
});

test("production environment approval boundary is declared", () => {
  assert.match(workflow, /environment: firebase-production/);
});

test("workflow uses minimum GitHub token permissions for OIDC", () => {
  assert.match(workflow, /permissions:\s*\n\s+contents: read\s*\n\s+id-token: write/);
  assert.doesNotMatch(workflow, /permissions:[\s\S]*?contents:\s*write/);
});

test("deployment project is fixed to the expected Firebase project", () => {
  assert.match(workflow, /FIREBASE_PROJECT_ID: ai-messenger-b97df/);
  assert.match(workflow, /project_id: \$\{\{ env\.FIREBASE_PROJECT_ID \}\}/);
});

test("authentication uses Workload Identity Federation, not a JSON key", () => {
  assert.match(workflow, /google-github-actions\/auth@v2/);
  assert.match(workflow, /workload_identity_provider:/);
  assert.doesNotMatch(workflow, /GOOGLE_APPLICATION_CREDENTIALS|service_account_key|credentials_json/i);
});

test("deployment is limited to Hosting and Realtime Database rules", () => {
  assert.match(workflow, /--only hosting,database/);
  assert.doesNotMatch(workflow, /--only[^\n]*(functions|storage|firestore|apphosting)/);
});

test("static project validation runs before Google authentication", () => {
  const validateIndex = workflow.indexOf("node scripts/validate-firebase-project.mjs");
  const authIndex = workflow.indexOf("google-github-actions/auth@v2");
  assert.ok(validateIndex >= 0 && authIndex > validateIndex);
});

test("deployment has a timeout and non-cancelling production concurrency", () => {
  assert.match(workflow, /timeout-minutes: 20/);
  assert.match(workflow, /cancel-in-progress: false/);
});
