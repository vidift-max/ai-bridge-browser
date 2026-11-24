import { readFile } from "node:fs/promises";
import vm from "node:vm";
import test from "node:test";
import assert from "node:assert/strict";

const source = await readFile(new URL("./local-ai-capability.js", import.meta.url), "utf8");
const page = await readFile(new URL("./rooms.html", import.meta.url), "utf8");

function loadProbe(overrides = {}) {
  const nav = {
    gpu: { async requestAdapter() { return {}; } },
    ml: { async createContext() { return {}; } },
    deviceMemory: 8,
    hardwareConcurrency: 8,
    storage: { async estimate() { return { quota: 5 * 1024 ** 3, usage: 50 * 1024 ** 2 }; } },
    indexedDB: {},
    ...overrides.navigator
  };
  const root = {
    navigator: nav,
    isSecureContext: true,
    Worker: function Worker() {},
    AIBridgeWifiOnly: { readState: () => ({ allowed: true, status: "WIFI_ALLOWED" }) },
    ...overrides.root
  };
  vm.runInNewContext(source, { window: root });
  return { api: root.AIBridgeLocalAICapability, root, nav };
}

test("reports browser APIs and coarse resource buckets without raw fingerprint data", async () => {
  const { api } = loadProbe();
  const report = await api.inspect();
  assert.equal(report.status, "LOCAL_AI_CANDIDATE_READY");
  assert.equal(report.runtimeScope, "user_device_browser");
  assert.equal(report.apis.webgpu.adapterAvailable, true);
  assert.equal(report.apis.webnn.available, true);
  assert.equal(report.resourceHints.memoryBucket, "8_GB_OR_MORE");
  assert.equal(report.resourceHints.cpuConcurrencyBucket, "5_TO_8");
  assert.equal(report.storage.quotaBucket, "OVER_4_GB");
  assert.equal("userAgent" in report, false);
  assert.equal("platform" in report, false);
});

test("fails closed outside secure context and without confirmed Wi-Fi", async () => {
  const { api } = loadProbe({
    root: {
      isSecureContext: false,
      AIBridgeWifiOnly: { readState: () => ({ allowed: false, status: "WIFI_NOT_CONFIRMED" }) }
    }
  });
  const report = await api.inspect();
  assert.equal(report.status, "LOCAL_AI_NOT_READY");
  assert.ok(report.reasons.includes("SECURE_CONTEXT_REQUIRED"));
  assert.ok(report.reasons.includes("WIFI_NOT_CONFIRMED"));
});

test("reports missing WebGPU and adapter failure distinctly", async () => {
  const noApi = loadProbe({ navigator: { gpu: undefined } });
  const first = await noApi.api.inspect();
  assert.ok(first.reasons.includes("WEBGPU_API_UNAVAILABLE"));

  const noAdapter = loadProbe({ navigator: { gpu: { async requestAdapter() { return null; } } } });
  const second = await noAdapter.api.inspect();
  assert.ok(second.reasons.includes("WEBGPU_ADAPTER_UNAVAILABLE"));
});

test("marks low memory, missing workers, IndexedDB and storage estimate", async () => {
  const { api } = loadProbe({
    navigator: {
      deviceMemory: 2,
      storage: undefined,
      indexedDB: undefined
    },
    root: { Worker: undefined }
  });
  const report = await api.inspect();
  assert.ok(report.reasons.includes("LOW_REPORTED_DEVICE_MEMORY"));
  assert.ok(report.reasons.includes("WORKERS_UNAVAILABLE"));
  assert.ok(report.reasons.includes("INDEXEDDB_UNAVAILABLE"));
  assert.ok(report.reasons.includes("STORAGE_ESTIMATE_UNAVAILABLE"));
});

test("handles WebGPU and storage API exceptions without throwing", async () => {
  const { api } = loadProbe({
    navigator: {
      gpu: { async requestAdapter() { throw new Error("device detail"); } },
      storage: { async estimate() { throw new Error("quota detail"); } }
    }
  });
  const report = await api.inspect();
  assert.equal(report.apis.webgpu.adapterAvailable, false);
  assert.equal(report.storage, null);
  assert.ok(report.reasons.includes("WEBGPU_ADAPTER_UNAVAILABLE"));
});

test("probe declares no network, persistence, download, or inference side effects", async () => {
  const { api } = loadProbe();
  const report = await api.inspect();
  assert.deepEqual(
    JSON.parse(JSON.stringify(report.privacy)),
    { transmitted: false, persisted: false, userAgentCollected: false, hardwareFingerprintCreated: false }
  );
  assert.equal(report.execution.modelLoaded, false);
  assert.equal(report.execution.downloadStarted, false);
  assert.equal(report.execution.inferenceStarted, false);
  assert.equal(report.execution.inferenceAvailable, false);
});

test("source contains no network or persistence APIs", () => {
  assert.doesNotMatch(source, /\bfetch\s*\(/);
  assert.doesNotMatch(source, /XMLHttpRequest|WebSocket|localStorage|sessionStorage|indexedDB\.open/);
});

test("rooms UI consumes the versioned report shape and never uploads it", () => {
  assert.match(page, /result\.apis\.webgpu\.adapterAvailable/);
  assert.match(page, /result\.resourceHints\.memoryBucket/);
  assert.match(page, /Relatório somente neste navegador/);
  assert.doesNotMatch(page, /fetch\([^)]*local-ai-capability/);
});

test("capability probe button is explicit, accessible, and starts disabled only while probing", () => {
  assert.match(page, /id="probeLocalAi" type="button"/);
  assert.match(page, /id="localAiStatus" class="sub" role="status" aria-live="polite"/);
  assert.match(page, /button\.disabled=true/);
  assert.match(page, /finally\{button\.disabled=false\}/);
});
