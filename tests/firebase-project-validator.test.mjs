import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { afterEach, test } from "node:test";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const validatorPath = path.join(repoRoot, "scripts", "validate-firebase-project.mjs");
const tempRoots = [];

function fixture(overrides = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "firebase-preflight-"));
  tempRoots.push(root);
  const firebase = path.join(root, "firebase");
  fs.mkdirSync(path.join(firebase, "public", "i"), { recursive: true });
  fs.mkdirSync(path.join(root, "scripts"), { recursive: true });
  fs.writeFileSync(path.join(firebase, "public", "i", "index.html"), "<!doctype html><title>Invite</title>");
  fs.writeFileSync(path.join(firebase, ".firebaserc"), JSON.stringify(overrides.alias ?? {
    projects: { default: "ai-messenger-b97df" }
  }));
  fs.writeFileSync(path.join(firebase, "firebase.json"), JSON.stringify(overrides.config ?? {
    database: { rules: "database.rules.json" },
    hosting: {
      public: "public",
      ignore: ["firebase.json", "**/node_modules/**", "**/*.template"],
      rewrites: [{ source: "/i/**", destination: "/i/index.html" }]
    }
  }));
  fs.writeFileSync(path.join(firebase, "database.rules.json"), JSON.stringify(overrides.rules ?? {
    rules: { messenger: { ".read": "auth != null" } }
  }));
  return root;
}

function runValidator(root) {
  return spawnSync(process.execPath, [validatorPath], {
    cwd: root,
    encoding: "utf8"
  });
}

afterEach(() => {
  for (const root of tempRoots.splice(0)) fs.rmSync(root, { recursive: true, force: true });
});

test("accepts a valid Firebase project configuration", () => {
  const result = runValidator(fixture());
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /FIREBASE_PROJECT_CONFIG_OK/);
});

test("rejects a project alias that points to another Firebase project", () => {
  const root = fixture({ alias: { projects: { default: "some-other-project" } } });
  const result = runValidator(root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Alias Firebase default/);
});

test("rejects a missing invite page", () => {
  const root = fixture();
  fs.rmSync(path.join(root, "firebase", "public", "i", "index.html"));
  const result = runValidator(root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Página de convite não encontrada/);
});

test("rejects a missing invite route rewrite", () => {
  const root = fixture({
    config: {
      database: { rules: "database.rules.json" },
      hosting: { public: "public", ignore: ["**/*.template"], rewrites: [] }
    }
  });
  const result = runValidator(root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Rewrite \/i\/\*\* -> \/i\/index.html ausente/);
});

test("rejects a Hosting directory that drifts from the config-relative public path", () => {
  const root = fixture({
    config: {
      database: { rules: "database.rules.json" },
      hosting: {
        public: "firebase/public",
        ignore: ["**/*.template"],
        rewrites: [{ source: "/i/**", destination: "/i/index.html" }]
      }
    }
  });
  const result = runValidator(root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Hosting public deve ser public/);
});

test("rejects deployment when template files are not excluded", () => {
  const root = fixture({
    config: {
      database: { rules: "database.rules.json" },
      hosting: {
        public: "public",
        ignore: ["firebase.json"],
        rewrites: [{ source: "/i/**", destination: "/i/index.html" }]
      }
    }
  });
  const result = runValidator(root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /templates não estão excluídos/);
});

test("rejects an unexpected Realtime Database rules path", () => {
  const root = fixture({
    config: {
      database: { rules: "../database.rules.json" },
      hosting: {
        public: "public",
        ignore: ["**/*.template"],
        rewrites: [{ source: "/i/**", destination: "/i/index.html" }]
      }
    }
  });
  const result = runValidator(root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Realtime Database deve apontar/);
});

test("rejects a globally open read rule at the root", () => {
  const root = fixture({ rules: { rules: { ".read": true } } });
  const result = runValidator(root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Regra aberta/);
});

test("rejects a nested globally open write rule expressed as a string", () => {
  const root = fixture({
    rules: { rules: { messenger: { conversations: { "$id": { ".write": "true" } } } } }
  });
  const result = runValidator(root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Regra aberta/);
});

test("rejects malformed Firebase JSON instead of continuing", () => {
  const root = fixture();
  fs.writeFileSync(path.join(root, "firebase", "database.rules.json"), "{ invalid");
  const result = runValidator(root);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /JSON inválido/);
});
