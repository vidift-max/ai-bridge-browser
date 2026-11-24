/* Mission 21: local-only browser/device feasibility probe.
 * No network requests, persistence, model downloads, fingerprints, or inference.
 */
(function (root) {
  "use strict";

  function bucket(value, ranges) {
    if (!Number.isFinite(value) || value <= 0) return "UNKNOWN";
    for (var i = 0; i < ranges.length; i += 1) {
      if (value <= ranges[i][0]) return ranges[i][1];
    }
    return ranges[ranges.length - 1][1];
  }

  function safeFeature(object, key, method) {
    return !!(object && (method ? typeof object[key] === "function" : object[key] != null));
  }

  async function inspect() {
    var nav = root.navigator || {};
    var wifi = root.AIBridgeWifiOnly && typeof root.AIBridgeWifiOnly.readState === "function"
      ? root.AIBridgeWifiOnly.readState()
      : { allowed: false, status: "WIFI_POLICY_UNAVAILABLE" };
    var secure = root.isSecureContext === true;
    var webgpuApi = safeFeature(nav, "gpu") && safeFeature(nav.gpu, "requestAdapter", true);
    var webgpuAdapter = false;
    if (webgpuApi) {
      try { webgpuAdapter = !!(await nav.gpu.requestAdapter()); }
      catch (_) { webgpuAdapter = false; }
    }

    var storageEstimate = null;
    if (nav.storage && typeof nav.storage.estimate === "function") {
      try {
        var estimate = await nav.storage.estimate();
        storageEstimate = {
          quotaBucket: bucket(estimate.quota, [[1073741824, "UNDER_1_GB"], [4294967296, "1_TO_4_GB"], [Infinity, "OVER_4_GB"]]),
          usageBucket: bucket(estimate.usage, [[104857600, "UNDER_100_MB"], [1073741824, "100_MB_TO_1_GB"], [Infinity, "OVER_1_GB"]])
        };
      } catch (_) { storageEstimate = null; }
    }

    var memory = bucket(nav.deviceMemory, [[3, "UP_TO_3_GB"], [7, "4_TO_7_GB"], [Infinity, "8_GB_OR_MORE"]]);
    var cores = bucket(nav.hardwareConcurrency, [[2, "1_TO_2"], [4, "3_TO_4"], [8, "5_TO_8"], [Infinity, "9_OR_MORE"]]);
    var webnn = safeFeature(nav, "ml") && safeFeature(nav.ml, "createContext", true);
    var workers = typeof root.Worker === "function";
    var indexedDb = !!nav.indexedDB || safeFeature(root, "indexedDB");
    var reasons = [];
    if (!secure) reasons.push("SECURE_CONTEXT_REQUIRED");
    if (!wifi.allowed) reasons.push(wifi.status || "WIFI_NOT_CONFIRMED");
    if (!webgpuApi) reasons.push("WEBGPU_API_UNAVAILABLE");
    else if (!webgpuAdapter) reasons.push("WEBGPU_ADAPTER_UNAVAILABLE");
    if (memory === "UP_TO_3_GB") reasons.push("LOW_REPORTED_DEVICE_MEMORY");
    if (!workers) reasons.push("WORKERS_UNAVAILABLE");
    if (!indexedDb) reasons.push("INDEXEDDB_UNAVAILABLE");
    if (!storageEstimate) reasons.push("STORAGE_ESTIMATE_UNAVAILABLE");

    return Object.freeze({
      schemaVersion: 1,
      status: reasons.length ? "LOCAL_AI_NOT_READY" : "LOCAL_AI_CANDIDATE_READY",
      runtimeScope: "user_device_browser",
      network: { allowed: wifi.allowed === true, status: wifi.status || "UNKNOWN" },
      secureContext: secure,
      apis: Object.freeze({
        webgpu: { available: webgpuApi, adapterAvailable: webgpuAdapter },
        webnn: { available: webnn },
        workers: workers,
        indexedDb: indexedDb,
        storageEstimate: storageEstimate !== null
      }),
      resourceHints: Object.freeze({ memoryBucket: memory, cpuConcurrencyBucket: cores }),
      storage: storageEstimate,
      reasons: Object.freeze(reasons),
      privacy: Object.freeze({
        transmitted: false,
        persisted: false,
        userAgentCollected: false,
        hardwareFingerprintCreated: false
      }),
      execution: Object.freeze({
        modelLoaded: false,
        downloadStarted: false,
        inferenceStarted: false,
        inferenceAvailable: false
      })
    });
  }

  root.AIBridgeLocalAICapability = Object.freeze({ inspect: inspect });
})(typeof window !== "undefined" ? window : globalThis);
