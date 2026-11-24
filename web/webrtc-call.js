/* Experimental one-to-one WebRTC call client.
 * Signaling uses the authenticated AI Bridge API; media is peer-to-peer.
 * Microphone access is requested only by startCall()/acceptCall() user actions.
 */
(function (root) {
  "use strict";

  function createClient(options) {
    options = options || {};
    var api = options.api;
    var onState = options.onState || function () {};
    var onRemoteStream = options.onRemoteStream || function () {};
    var onDiagnostic = options.onDiagnostic || function () {};
    var connectionGraceMs = Number.isFinite(options.connectionGraceMs) ?
      Math.max(0, options.connectionGraceMs) : 8000;
    var getMedia = options.getUserMedia || function () {
      if (!root.navigator || !root.navigator.mediaDevices ||
          typeof root.navigator.mediaDevices.getUserMedia !== "function") {
        return Promise.reject(new Error("MICROPHONE_API_UNAVAILABLE"));
      }
      return root.navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    };
    var makePeer = options.createPeerConnection || function () {
      if (typeof root.RTCPeerConnection !== "function") {
        throw new Error("WEBRTC_UNAVAILABLE");
      }
      return new root.RTCPeerConnection(options.rtcConfiguration || {});
    };
    var setIntervalFn = options.setInterval || root.setInterval.bind(root);
    var clearIntervalFn = options.clearInterval || root.clearInterval.bind(root);
    var pollIntervalMs = options.pollIntervalMs || 1200;
    var call = null;
    var pc = null;
    var localStream = null;
    var remoteStream = null;
    var pollHandle = null;
    var signalCursor = 0;
    var seenSignals = Object.create(null);
    var pendingCandidates = [];
    var closed = false;
    var polling = false;
    var offerSent = false;
    var connectedReported = false;
    var disconnectTimer = null;

    function state(value, detail) {
      onState(value, detail || null);
    }
    function diagnostic(event, detail) {
      onDiagnostic({ event: event, detail: detail || null });
    }
    function clearDisconnectTimer() {
      if (disconnectTimer !== null) root.clearTimeout(disconnectTimer);
      disconnectTimer = null;
    }
    function request(method, path, body, keepalive) {
      if (typeof api !== "function") return Promise.reject(new Error("CALL_API_REQUIRED"));
      var requestOptions = { method: method,
        headers: body ? { "Content-Type": "application/json" } : {},
        body: body ? JSON.stringify(body) : undefined };
      if (keepalive) requestOptions.keepalive = true;
      return api(path, requestOptions);
    }
    function requireSecureContext() {
      if (root.isSecureContext !== true) throw new Error("SECURE_CONTEXT_REQUIRED");
    }
    function requirePeer() {
      if (!pc) throw new Error("PEER_CONNECTION_NOT_READY");
      return pc;
    }
    async function sendSignal(kind, payload) {
      if (!call) throw new Error("CALL_NOT_STARTED");
      return request("POST", "/v1/calls/" + encodeURIComponent(call.call_id) + "/signals",
        { kind: kind, payload: payload });
    }
    async function flushCandidates() {
      if (!pc || !pc.remoteDescription) return;
      var batch = pendingCandidates.splice(0);
      for (var i = 0; i < batch.length; i += 1) {
        await pc.addIceCandidate(batch[i]);
      }
    }
    async function handleSignal(signal) {
      if (!signal || !Number.isInteger(signal.signalId) || seenSignals[signal.signalId]) return;
      seenSignals[signal.signalId] = true;
      signalCursor = Math.max(signalCursor, signal.signalId);
      var peer = requirePeer();
      if (signal.kind === "OFFER") {
        if (call.callee_ai_id === options.aiId) {
          await peer.setRemoteDescription(signal.payload);
          await flushCandidates();
          var answer = await peer.createAnswer();
          await peer.setLocalDescription(answer);
          await sendSignal("ANSWER", { type: answer.type, sdp: answer.sdp });
          state("CONNECTING");
          await request("POST", "/v1/calls/" + encodeURIComponent(call.call_id) + "/connecting", {});
        }
      } else if (signal.kind === "ANSWER") {
        if (call.caller_ai_id === options.aiId) {
          await peer.setRemoteDescription(signal.payload);
          await flushCandidates();
          state("CONNECTING");
          await request("POST", "/v1/calls/" + encodeURIComponent(call.call_id) + "/connecting", {});
        }
      } else if (signal.kind === "ICE_CANDIDATE") {
        var candidate = signal.payload;
        if (!candidate || typeof candidate.candidate !== "string") return;
        if (peer.remoteDescription) await peer.addIceCandidate(candidate);
        else pendingCandidates.push(candidate);
      }
    }
    async function pollOnce() {
      if (!call || closed || polling) return;
      polling = true;
      try {
        var response = await request("GET", "/v1/calls/" + encodeURIComponent(call.call_id));
        if (response.call) {
          call = response.call;
          state(call.state);
          if (["REJECTED", "CANCELLED", "ENDED", "TIMED_OUT"].includes(call.state)) {
            await closeMedia();
            stopPolling();
            call = null;
            return;
          }
          if (call.caller_ai_id === options.aiId && call.state === "ACCEPTED" && !offerSent) {
            if (!pc) await prepareMedia();
            var offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            await sendSignal("OFFER", { type: offer.type, sdp: offer.sdp });
            offerSent = true;
            state("CONNECTING");
            await request("POST", "/v1/calls/" + encodeURIComponent(call.call_id) + "/connecting", {});
          }
        }
        var signalsResponse = await request("GET", "/v1/calls/" + encodeURIComponent(call.call_id) +
          "/signals?after=" + signalCursor + "&limit=100");
        for (var i = 0; i < (signalsResponse.signals || []).length; i += 1) {
          await handleSignal(signalsResponse.signals[i]);
        }
      } catch (error) {
        state("SIGNALING_ERROR", error.message || String(error));
      } finally {
        polling = false;
      }
    }
    function startPolling() {
      stopPolling();
      pollHandle = setIntervalFn(function () { pollOnce(); }, pollIntervalMs);
      pollOnce();
    }
    function stopPolling() {
      if (pollHandle !== null) clearIntervalFn(pollHandle);
      pollHandle = null;
    }
    async function prepareMedia() {
      requireSecureContext();
      localStream = await getMedia();
      pc = makePeer();
      remoteStream = typeof root.MediaStream === "function" ? new root.MediaStream() : null;
      if (remoteStream) onRemoteStream(remoteStream);
      localStream.getTracks().forEach(function (track) { pc.addTrack(track, localStream); });
      pc.ontrack = function (event) {
        if (remoteStream && event.track) remoteStream.addTrack(event.track);
        if (!remoteStream && event.streams && event.streams[0]) remoteStream = event.streams[0];
        if (remoteStream) onRemoteStream(remoteStream);
      };
      pc.onicecandidate = function (event) {
        if (event.candidate) {
          var candidate = typeof event.candidate.toJSON === "function" ?
            event.candidate.toJSON() : event.candidate;
          sendSignal("ICE_CANDIDATE", candidate).catch(function (error) {
            state("SIGNALING_ERROR", error.message || String(error));
          });
        } else {
          sendSignal("ICE_COMPLETE", {}).catch(function () {});
        }
      };
      pc.onicegatheringstatechange = function () {
        if (pc) diagnostic("ICE_GATHERING", pc.iceGatheringState || "unknown");
      };
      pc.oniceconnectionstatechange = function () {
        if (!pc) return;
        var iceState = pc.iceConnectionState || "unknown";
        diagnostic("ICE_CONNECTION", iceState);
        if (iceState === "connected" || iceState === "completed") clearDisconnectTimer();
        if (iceState === "disconnected" && disconnectTimer === null) {
          disconnectTimer = root.setTimeout(function () {
            disconnectTimer = null;
            if (pc && pc.iceConnectionState === "disconnected") state("MEDIA_DISCONNECTED");
          }, connectionGraceMs);
        } else if (iceState === "failed") {
          clearDisconnectTimer();
          state("MEDIA_FAILED");
        } else if (iceState === "closed") {
          clearDisconnectTimer();
          diagnostic("ICE_CLOSED");
        }
      };
      pc.onicecandidateerror = function (event) {
        diagnostic("ICE_CANDIDATE_ERROR", {
          code: Number.isFinite(event && event.errorCode) ? event.errorCode : null,
          text: event && event.errorText ? String(event.errorText).slice(0, 160) : null
        });
      };
      pc.onconnectionstatechange = function () {
        var connectionState = pc && pc.connectionState;
        diagnostic("PEER_CONNECTION", connectionState || "unknown");
        if (connectionState === "connected" && !connectedReported && call) {
          connectedReported = true;
          clearDisconnectTimer();
          request("POST", "/v1/calls/" + encodeURIComponent(call.call_id) + "/connected", {})
            .then(function (response) {
              if (!call) return;
              call = response.call || call;
              state("CONNECTED");
            })
            .catch(function (error) { state("SIGNALING_ERROR", error.message || String(error)); });
        } else if (connectionState === "failed") {
          state("MEDIA_FAILED");
        } else if (connectionState === "disconnected") {
          state("MEDIA_DISCONNECTED");
        }
      };
    }
    async function startCall(conversationId, calleeAiId) {
      if (call) throw new Error("CALL_ALREADY_ACTIVE");
      requireSecureContext();
      try {
        var response = await request("POST", "/v1/calls", {
          conversationId: conversationId, calleeAiId: calleeAiId
        });
        call = response.call;
        offerSent = false;
        connectedReported = false;
        state("RINGING");
        startPolling();
        return call;
      } catch (error) {
        await closeMedia();
        call = null;
        throw error;
      }
    }
    async function acceptCall(incomingCall) {
      if (call) throw new Error("CALL_ALREADY_ACTIVE");
      call = incomingCall;
      if (call.callee_ai_id !== options.aiId) { call = null; throw new Error("ONLY_CALLEE_CAN_ACCEPT"); }
      try {
        await prepareMedia();
        var response = await request("POST", "/v1/calls/" + encodeURIComponent(call.call_id) + "/accept", {});
        call = response.call || call;
        state("ACCEPTED");
        startPolling();
        return call;
      } catch (error) {
        await closeMedia();
        call = null;
        try { await request("POST", "/v1/calls/" + encodeURIComponent(incomingCall.call_id) + "/reject", {}); } catch (_) {}
        throw error;
      }
    }
    async function refreshIncoming(conversationId) {
      var response = await request("GET", "/v1/conversations/" +
        encodeURIComponent(conversationId) + "/calls/active");
      return response.call || null;
    }
    async function rejectCall(incomingCall) {
      if (!incomingCall || !incomingCall.call_id || incomingCall.callee_ai_id !== options.aiId) {
        throw new Error("ONLY_CALLEE_CAN_REJECT");
      }
      return request("POST", "/v1/calls/" + encodeURIComponent(incomingCall.call_id) + "/reject", {});
    }
    async function endCall() {
      if (!call) return false;
      var current = call;
      try {
        var latest = await request("GET", "/v1/calls/" + encodeURIComponent(current.call_id));
        current = latest.call || current;
        call = current;
      } catch (_) {}
      var action = current.state === "RINGING" ?
        (current.caller_ai_id === options.aiId ? "cancel" : "reject") : "end";
      try {
        await request("POST", "/v1/calls/" + encodeURIComponent(current.call_id) + "/" + action, {});
      } finally {
        await closeMedia();
        stopPolling();
        call = null;
        state("ENDED");
      }
      return true;
    }
    async function closeMedia() {
      clearDisconnectTimer();
      connectedReported = false;
      if (pc) {
        pc.onconnectionstatechange = null;
        pc.oniceconnectionstatechange = null;
        pc.onicegatheringstatechange = null;
        pc.onicecandidateerror = null;
        try { pc.close(); } catch (_) {}
      }
      pc = null;
      if (localStream && typeof localStream.getTracks === "function") {
        localStream.getTracks().forEach(function (track) { try { track.stop(); } catch (_) {} });
      }
      localStream = null;
      remoteStream = null;
      pendingCandidates = [];
    }
    function dispose() {
      if (call) {
        var current = call;
        var action = current.state === "RINGING" ?
          (current.caller_ai_id === options.aiId ? "cancel" : "reject") : "end";
        request("POST", "/v1/calls/" + encodeURIComponent(current.call_id) + "/" + action, {}, true)
          .catch(function () {});
      }
      closed = true;
      stopPolling();
      closeMedia();
    }
    return Object.freeze({
      startCall: startCall,
      acceptCall: acceptCall,
      refreshIncoming: refreshIncoming,
      rejectCall: rejectCall,
      poll: pollOnce,
      endCall: endCall,
      dispose: dispose,
      getCall: function () { return call; }
    });
  }

  root.AIBridgeWebRTCCall = Object.freeze({ createClient: createClient });
})(typeof window !== "undefined" ? window : globalThis);
