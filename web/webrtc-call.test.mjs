import { readFile } from "node:fs/promises";
import vm from "node:vm";
import test from "node:test";
import assert from "node:assert/strict";

const source = await readFile(new URL("./webrtc-call.js", import.meta.url), "utf8");

class FakePeerConnection {
  constructor() {
    this.localDescription = null;
    this.remoteDescription = null;
    this.connectionState = "new";
    this.addedCandidates = [];
    this.tracks = [];
    FakePeerConnection.instances.push(this);
  }
  addTrack(track, stream) { this.tracks.push({ track, stream }); }
  async createOffer() { return { type: "offer", sdp: "offer-sdp" }; }
  async createAnswer() { return { type: "answer", sdp: "answer-sdp" }; }
  async setLocalDescription(value) { this.localDescription = value; }
  async setRemoteDescription(value) { this.remoteDescription = value; }
  async addIceCandidate(value) { this.addedCandidates.push(value); }
  close() { this.connectionState = "closed"; }
}
FakePeerConnection.instances = [];

class FakeMediaStream {
  constructor() { this.tracks = []; }
  addTrack(track) { this.tracks.push(track); }
}

function createApiServer() {
  const state = { call: null, signals: [], nextSignal: 1 };
  function apiFor(aiId) {
    return async (path, options = {}) => {
      const method = options.method || "GET";
      const body = options.body ? JSON.parse(options.body) : {};
      if (method === "GET" && /^\/v1\/conversations\/[^/]+\/calls\/active$/.test(path)) {
        return { call: state.call ? { ...state.call } : null };
      }
      if (method === "POST" && path === "/v1/calls") {
        assert.equal(state.call, null);
        state.call = {
          call_id: "call-test-1", conversation_id: "private-1",
          caller_ai_id: aiId, callee_ai_id: body.calleeAiId,
          state: "RINGING"
        };
        return { call: { ...state.call } };
      }
      const match = path.match(/^\/v1\/calls\/([^/?]+)(?:\/(signals|accept|reject|cancel|end|connecting|connected))?(?:\?(.*))?$/);
      if (!match) throw new Error("unexpected API path: " + path);
      const [, callId, action, query] = match;
      assert.equal(callId, "call-test-1");
      if (!action) return { call: { ...state.call } };
      if (action === "signals" && method === "GET") {
        const params = new URLSearchParams(query || "");
        const after = Number(params.get("after") || 0);
        return { signals: state.signals.filter(s => s.signalId > after && s.senderAiId !== aiId) };
      }
      if (action === "signals" && method === "POST") {
        assert.equal(["ACCEPTED", "CONNECTING", "CONNECTED"].includes(state.call.state), true);
        const signal = {
          signalId: state.nextSignal++, callId, senderAiId: aiId,
          kind: body.kind, payload: body.payload
        };
        state.signals.push(signal);
        return { signal };
      }
      if (action === "accept") {
        assert.equal(aiId, state.call.callee_ai_id);
        state.call.state = "ACCEPTED";
      } else if (action === "connecting") {
        state.call.state = "CONNECTING";
      } else if (action === "connected") {
        state.call.state = "CONNECTED";
      } else if (action === "cancel") {
        state.call.state = "CANCELLED";
      } else if (action === "reject") {
        state.call.state = "REJECTED";
      } else if (action === "end") {
        state.call.state = "ENDED";
      }
      return { call: { ...state.call } };
    };
  }
  return { state, apiFor };
}

function makeClient(aiId, api, counters = {}) {
  const tracks = [{ stopped: false, stop() { this.stopped = true; } }];
  const context = {
    window: {
      isSecureContext: true,
      RTCPeerConnection: FakePeerConnection,
      MediaStream: FakeMediaStream,
      navigator: { mediaDevices: { getUserMedia: async constraints => {
        counters.mediaRequests = (counters.mediaRequests || 0) + 1;
        assert.equal(constraints.audio, true);
        assert.equal(constraints.video, false);
        return { getTracks: () => tracks };
      } } },
      setInterval: () => 1,
      clearInterval: () => {}
    }
  };
  vm.runInNewContext(source, context);
  return {
    client: context.window.AIBridgeWebRTCCall.createClient({
      aiId, api, pollIntervalMs: 10, setInterval: () => 1, clearInterval: () => {}
    }),
    tracks,
    counters
  };
}

test("no microphone permission is requested when client is merely created", () => {
  const server = createApiServer();
  const counters = {};
  makeClient("AI-01", server.apiFor("AI-01"), counters);
  assert.equal(counters.mediaRequests || 0, 0);
});

test("caller waits for acceptance before sending the WebRTC offer", async () => {
  const server = createApiServer();
  const counters = {};
  const caller = makeClient("AI-01", server.apiFor("AI-01"), counters);
  await caller.client.startCall("private-1", "AI-02");
  assert.equal(server.state.call.state, "RINGING");
  assert.equal(server.state.signals.length, 0);
  assert.equal(counters.mediaRequests || 0, 0);
  await caller.client.endCall();
  assert.equal(server.state.call.state, "CANCELLED");
  assert.equal(counters.mediaRequests || 0, 0);
});

test("callee acceptance unlocks offer/answer exchange through authenticated signaling", async () => {
  FakePeerConnection.instances = [];
  const server = createApiServer();
  const callerCounters = {};
  const caller = makeClient("AI-01", server.apiFor("AI-01"), callerCounters);
  const callee = makeClient("AI-02", server.apiFor("AI-02"));

  await caller.client.startCall("private-1", "AI-02");
  const incoming = await callee.client.refreshIncoming("private-1");
  assert.equal(incoming.call_id, "call-test-1");
  await callee.client.acceptCall(incoming);

  await caller.client.poll();
  assert.equal(callerCounters.mediaRequests, 1);
  assert.equal(server.state.signals[0].kind, "OFFER");
  assert.equal(server.state.call.state, "CONNECTING");

  await callee.client.poll();
  assert.equal(server.state.signals[1].kind, "ANSWER");
  assert.equal(FakePeerConnection.instances[1].remoteDescription.type, "offer");
  assert.equal(FakePeerConnection.instances[1].localDescription.type, "answer");

  await caller.client.poll();
  assert.equal(FakePeerConnection.instances[0].remoteDescription.type, "answer");
  assert.equal(caller.client.getCall().call_id, "call-test-1");

  await callee.client.endCall();
  assert.equal(server.state.call.state, "ENDED");
  assert.equal(caller.tracks[0].stopped, false);
  caller.client.dispose();
  callee.client.dispose();
});

test("microphone access is rejected outside a secure context", async () => {
  const server = createApiServer();
  const context = { window: { isSecureContext: false, setInterval: () => 1, clearInterval: () => {} } };
  vm.runInNewContext(source, context);
  const client = context.window.AIBridgeWebRTCCall.createClient({
    aiId: "AI-01", api: server.apiFor("AI-01"),
    getUserMedia: async () => { throw new Error("should not be called"); },
    createPeerConnection: () => new FakePeerConnection()
  });
  await assert.rejects(client.startCall("private-1", "AI-02"), /SECURE_CONTEXT_REQUIRED/);
});
