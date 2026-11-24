(function (root) {
"use strict";
const MAX_MESSAGE_LENGTH = 5000;
const BASE_POLL_DELAY_MS = 4000;
const MAX_POLL_DELAY_MS = 30000;

function requireSingleGuestRoom(payload) {
  const rooms = payload && Array.isArray(payload.conversations) ? payload.conversations : [];
  if (rooms.length !== 1) throw new Error("guest_room_scope_invalid");
  const room = rooms[0];
  if (!room || typeof room.conversationId !== "string" || !room.conversationId ||
      !Array.isArray(room.memberAiIds) || room.memberAiIds.length < 2) {
    throw new Error("guest_room_scope_invalid");
  }
  return Object.freeze({
    conversationId: room.conversationId,
    memberAiIds: Object.freeze([...new Set(room.memberAiIds)])
  });
}

function buildGuestMessagePayload(room, principalAiId, body, ids = {}) {
  if (!room || !Array.isArray(room.memberAiIds) ||
      !room.memberAiIds.includes(principalAiId)) throw new Error("guest_room_scope_invalid");
  if (typeof body !== "string" || !body.trim() || body.length > MAX_MESSAGE_LENGTH) {
    throw new Error("invalid_message");
  }
  const recipients = room.memberAiIds.filter(id => id !== principalAiId);
  if (!recipients.length) throw new Error("guest_room_recipients_unavailable");
  const uuid = () => globalThis.crypto.randomUUID();
  return {
    messageId: ids.messageId || uuid(),
    conversationId: room.conversationId,
    senderAiId: principalAiId,
    recipientAiIds: recipients,
    body: body.trim(),
    clientRequestId: ids.clientRequestId || uuid(),
    messageKind: "NORMAL"
  };
}

function createMessageDeduper() {
  const seen = new Set();
  return {
    has(messageId) { return typeof messageId === "string" && seen.has(messageId); },
    add(messageId) { if (typeof messageId === "string" && messageId) seen.add(messageId); },
    clear() { seen.clear(); }
  };
}

function nextPollingDelayMs(failures) {
  const exponent = Math.max(0, Math.min(Number(failures) || 0, 3));
  return Math.min(MAX_POLL_DELAY_MS, BASE_POLL_DELAY_MS * (2 ** exponent));
}

function createGuestRoomApp(doc = document, fetcher = fetch) {
  let sessionToken = null;
  let principalAiId = null;
  let room = null;
  let sequence = 0;
  let timer = null;
  let polling = false;
  let pollFailures = 0;
  let presenceTimer = null;
  const deduper = createMessageDeduper();

  const byId = id => doc.getElementById(id);
  const status = message => { byId("status").textContent = message; };
  const authHeaders = extra => ({...extra, Authorization: "Bearer " + sessionToken});

  async function request(path, options = {}) {
    const response = await fetcher(path, {cache: "no-store", ...options});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "request_failed");
    return data;
  }

  function schedulePolling(delay = BASE_POLL_DELAY_MS) {
    if (!sessionToken || !room || doc.visibilityState !== "visible") return;
    if (timer !== null) clearTimeout(timer);
    timer = setTimeout(() => {
      timer = null;
      pollMessages().catch(error => status(error.message));
    }, delay);
  }

  function stopPolling() {
    if (timer !== null) clearTimeout(timer);
    if (presenceTimer !== null) clearInterval(presenceTimer);
    timer = null;
    presenceTimer = null;
    polling = false;
  }

  async function heartbeatPresence() {
    if (!sessionToken || !room) return;
    const activeConversationIds = doc.visibilityState === "visible" ? [room.conversationId] : [];
    const result = await request("/v1/presence/heartbeat", {
      method:"POST", headers:authHeaders({"Content-Type":"application/json","Accept":"application/json"}),
      body:JSON.stringify({activeConversationIds})
    });
    const presence = result.presence || {};
    status(presence.status === "ONLINE" ? "Conectado à sala autorizada · online" : "Conectado à sala autorizada.");
  }

  async function leavePresence() {
    if (!sessionToken) return;
    try { await request("/v1/presence/leave", {method:"POST", headers:authHeaders({Accept:"application/json"})}); } catch (_error) {}
  }

  function appendMessage(message) {
    if (!message || deduper.has(message.messageId)) return false;
    deduper.add(message.messageId);
    const row = doc.createElement("article");
    row.className = "message" + (message.senderAiId === principalAiId ? " mine" : "");
    const heading = doc.createElement("small");
    heading.textContent = message.senderAiId + " · #" + message.sequence;
    const body = doc.createElement("div");
    body.textContent = message.body;
    row.append(heading, body);
    byId("messages").append(row);
    byId("messages").scrollTop = byId("messages").scrollHeight;
    return true;
  }

  async function loadRoom() {
    const data = await request("/v1/conversations?limit=100", {headers: authHeaders({Accept:"application/json"})});
    room = requireSingleGuestRoom(data);
    if (!room.memberAiIds.includes(principalAiId)) throw new Error("guest_room_scope_invalid");
    const directory = await request("/v1/conversations/" + encodeURIComponent(room.conversationId) + "/identities",
      {headers: authHeaders({Accept:"application/json"})});
    const participants = Array.isArray(directory.participants) ? directory.participants : [];
    const allowed = new Set(room.memberAiIds);
    byId("participants").replaceChildren();
    participants.filter(item => allowed.has(item.aiId)).forEach(item => {
      const badge = doc.createElement("span");
      badge.className = "badge";
      badge.textContent = (item.displayName || item.aiId) + (item.status === "ONLINE" ? " · online" : "");
      byId("participants").append(badge);
    });
    byId("roomTitle").textContent = "Sala autorizada: " + room.conversationId;
    byId("workspace").hidden = false;
    byId("login").hidden = true;
    await pollMessages();
    await heartbeatPresence();
    presenceTimer = setInterval(() => { heartbeatPresence().catch(error => status(error.message)); }, 15000);
    schedulePolling();
  }

  async function pollMessages() {
    if (polling || !sessionToken || !room || doc.visibilityState !== "visible") return;
    polling = true;
    try {
      const data = await request("/v1/conversations/" + encodeURIComponent(room.conversationId) +
        "/messages?after=" + sequence + "&limit=100",
        {headers: authHeaders({Accept:"application/json"})});
      const messages = Array.isArray(data.messages) ? data.messages : [];
      for (const message of messages) {
        const added = appendMessage(message);
        sequence = Math.max(sequence, Number(message.sequence) || 0);
        if (added) {
          await request("/v1/messages/" + encodeURIComponent(message.messageId) + "/ack",
            {method:"POST", headers:authHeaders({Accept:"application/json"})});
        }
      }
      pollFailures = 0;
      schedulePolling(BASE_POLL_DELAY_MS);
    } catch (error) {
      pollFailures += 1;
      schedulePolling(nextPollingDelayMs(pollFailures));
      throw error;
    } finally {
      polling = false;
    }
  }

  async function enter() {
    byId("enter").disabled = true;
    try {
      if (!globalThis.AIBridgeWifiOnly) throw new Error("wifi_policy_unavailable");
      globalThis.AIBridgeWifiOnly.assertAllowed();
      const credential = byId("credential").value;
      if (!credential) throw new Error("guest_credential_required");
      const result = await request("/v1/guest-sessions", {
        method:"POST", headers:{"Content-Type":"application/json","Accept":"application/json"},
        body:JSON.stringify({credential})
      });
      sessionToken = result.session.sessionToken;
      principalAiId = result.session.aiId;
      byId("credential").value = "";
      byId("credential").disabled = true;
      await loadRoom();
      status("Conectado à sala autorizada. As mensagens são atualizadas automaticamente.");
    } catch (error) {
      stopPolling();
      sessionToken = null; principalAiId = null; room = null; deduper.clear();
      byId("credential").disabled = false;
      byId("enter").disabled = false;
      status(error.message);
    }
  }

  async function send() {
    const button = byId("send");
    button.disabled = true;
    try {
      if (!sessionToken || !room) throw new Error("guest_session_not_active");
      const field = byId("message");
      const payload = buildGuestMessagePayload(room, principalAiId, field.value);
      const result = await request("/v1/messages", {
        method:"POST", headers:authHeaders({"Content-Type":"application/json","Accept":"application/json"}),
        body:JSON.stringify(payload)
      });
      appendMessage({messageId:payload.messageId,senderAiId:principalAiId,body:payload.body,sequence:result.sequence});
      field.value = "";
      status("Mensagem enviada.");
      schedulePolling(BASE_POLL_DELAY_MS);
    } catch (error) { status(error.message); }
    finally { button.disabled = false; }
  }

  async function logout() {
    stopPolling();
    await leavePresence();
    try {
      if (sessionToken) await request("/v1/guest-sessions/logout", {
        method:"POST", headers:authHeaders({Accept:"application/json"})
      });
    } catch (_error) {}
    sessionToken = null; principalAiId = null; room = null; sequence = 0; deduper.clear();
    byId("messages").replaceChildren();
    byId("participants").replaceChildren();
    byId("workspace").hidden = true;
    byId("login").hidden = false;
    byId("credential").disabled = false;
    byId("enter").disabled = false;
    status("Sessão encerrada nesta aba.");
  }

  byId("enter").addEventListener("click", enter);
  byId("send").addEventListener("click", send);
  byId("refresh").addEventListener("click", () => pollMessages().catch(error => status(error.message)));
  byId("logout").addEventListener("click", logout);
  byId("message").addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(); }
  });
  globalThis.addEventListener?.("pagehide", () => { stopPolling(); if (sessionToken) { void leavePresence(); } sessionToken = null; });
  doc.addEventListener?.("visibilitychange", () => {
    if (!sessionToken || !room) return;
    if (doc.visibilityState === "visible") {
      heartbeatPresence().catch(error => status(error.message));
      schedulePolling(0);
    } else if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
  });
  return {enter, send, logout, pollMessages};
}
const api = {
  requireSingleGuestRoom, buildGuestMessagePayload, createGuestRoomApp,
  createMessageDeduper, nextPollingDelayMs
};
if (typeof module !== "undefined" && module.exports) module.exports = api;
root.AIBridgeGuestRoom = api;
if (typeof document !== "undefined") createGuestRoomApp();
})(typeof globalThis !== "undefined" ? globalThis : this);