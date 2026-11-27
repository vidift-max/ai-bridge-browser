import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const validator = path.join(root, "scripts", "validate-firebase-wif-config.mjs");

function run(env) {
  return spawnSync(process.execPath, [validator], {
    encoding: "utf8",
    env: { ...process.env, FIREBASE_WORKLOAD_IDENTITY_PROVIDER: "", FIREBASE_DEPLOY_SERVICE_ACCOUNT: "", ...env },
  });
}

const valid = {
  FIREBASE_WORKLOAD_IDENTITY_PROVIDER: "projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider",
  FIREBASE_DEPLOY_SERVICE_ACCOUNT: "firebase-deployer@ai-messenger-b97df.iam.gserviceaccount.com",
};

test("accepts valid WIF provider resource and service-account email", () => {
  const result = run(valid);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /FIREBASE_WIF_CONFIGURATION_SHAPE_OK/);
});

test("rejects missing provider", () => {
  const result = run({ ...valid, FIREBASE_WORKLOAD_IDENTITY_PROVIDER: "" });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /FIREBASE_WORKLOAD_IDENTITY_PROVIDER is missing/);
});

test("rejects malformed provider resource", () => {
  const result = run({ ...valid, FIREBASE_WORKLOAD_IDENTITY_PROVIDER: "https://example.com/provider" });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /invalid resource-name format/);
});

test("rejects non-global provider location", () => {
  const result = run({ ...valid, FIREBASE_WORKLOAD_IDENTITY_PROVIDER: "projects/123/locations/us-central1/workloadIdentityPools/p/providers/x" });
  assert.notEqual(result.status, 0);
});

test("rejects missing service account", () => {
  const result = run({ ...valid, FIREBASE_DEPLOY_SERVICE_ACCOUNT: "" });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /FIREBASE_DEPLOY_SERVICE_ACCOUNT is missing/);
});

test("rejects malformed service-account email", () => {
  const result = run({ ...valid, FIREBASE_DEPLOY_SERVICE_ACCOUNT: "not-an-email" });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /invalid service-account email format/);
});

test("does not print configured provider or service-account values", () => {
  const result = run(valid);
  assert.equal(result.status, 0);
  assert.doesNotMatch(result.stdout + result.stderr, /123456789|firebase-deployer@/);
});
