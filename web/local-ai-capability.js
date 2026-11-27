/* Local AI capability probe. No downloads, fetches, or persistence. */
(function (root) {
  "use strict";
  async function inspect() {
    var nav = root.navigator || {};
    var network = root.AIBridgeWifiOnly
      ? root.AIBridgeWifiOnly.readState()
      : { allowed: false, status: "WIFI_POLICY_UNAVAILABLE", connectionType: "unknown" };
    var storage = null;
    try {
      if (nav.storage && typeof nav.storage.estimate === "function") {
        var estimate = await nav.storage.estimate();
        storage = {
          quotaBytes: Number.isFinite(estimate.quota) ? estimate.quota : null,
          usageBytes: Number.isFinite(estimate.usage) ? estimate.usage : null
        };
      }
    } catch (_) { storage = null; }

    var webgpu = !!(nav.gpu && typeof nav.gpu.requestAdapter === "function");
    var adapterAvailable = false;
    if (webgpu) {
      try {
        var adapter = await nav.gpu.requestAdapter();
        adapterAvailable = !!adapter;
      } catch (_) { adapterAvailable = false; }
    }

    var deviceMemoryGb = Number.isFinite(nav.deviceMemory) ? nav.deviceMemory : null;
    var secureContext = root.isSecureContext === true;
    var reasons = [];
    if (!secureContext) reasons.push("HTTPS_REQUIRED");
    if (!network.allowed) reasons.push(network.status);
    if (!webgpu) reasons.push("WEBGPU_API_UNAVAILABLE");
    else if (!adapterAvailable) reasons.push("WEBGPU_ADAPTER_UNAVAILABLE");
    if (deviceMemoryGb !== null && deviceMemoryGb < 4) reasons.push("LOW_REPORTED_DEVICE_MEMORY");
    if (!storage) reasons.push("STORAGE_ESTIMATE_UNAVAILABLE");

    return {
      status: reasons.length ? "LOCAL_AI_NOT_READY" : "LOCAL_AI_CANDIDATE_READY",
      network: network,
      secureContext: secureContext,
      webgpuApiAvailable: webgpu,
      webgpuAdapterAvailable: adapterAvailable,
      deviceMemoryGb: deviceMemoryGb,
      storage: storage,
      reasons: reasons,
      modelLoaded: false,
      downloadStarted: false,
      inferenceStarted: false
    };
  }
  root.AIBridgeLocalAICapability = Object.freeze({ inspect: inspect });
})(window);
