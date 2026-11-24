/* AI Bridge Remote Control Plane — policy-gated adapter orchestration.
 * A host must provide an authenticated adapter and explicit, short-lived grants.
 * No arbitrary code, shell commands, or unrestricted browser navigation.
 */
(function (root) {
  "use strict";
  var ALLOWED_ACTIONS = Object.freeze(["SEND_MESSAGE", "REQUEST_RECONNECT", "READ_STATUS"]);
  function create(options) {
    options = options || {};
    var adapter = options.adapter || {}, now = options.now || Date.now;
    var onAudit = options.onAudit || function () {};
    var maxAttempts = Number.isInteger(options.maxRecoveryAttempts) ? Math.max(0, options.maxRecoveryAttempts) : 3;
    var baseDelay = Number.isFinite(options.baseDelayMs) ? Math.max(0, options.baseDelayMs) : 1000;
    var maxDelay = Number.isFinite(options.maxDelayMs) ? Math.max(baseDelay, options.maxDelayMs) : 15000;
    var grants = new Map(), sessions = new Map(), results = new Map(), recovery = new Map(), stopped = false;
    function validId(v) { return typeof v === "string" && /^[A-Za-z0-9._:-]{1,128}$/.test(v); }
    function audit(event, fields) {
      var safe = { event: event, at: now() };
      Object.keys(fields || {}).forEach(function (k) {
        var v = fields[k];
        if (["sessionId","action","status","reason","attempt","grantId","actionId"].includes(k) &&
            (typeof v === "string" || Number.isFinite(v))) safe[k] = v;
      });
      try { onAudit(Object.freeze(safe)); } catch (_) {}
    }
    function issueGrant(input) {
      input = input || {};
      if (stopped) throw new Error("CONTROL_PLANE_STOPPED");
      if (!validId(input.grantId) || !validId(input.sessionId)) throw new Error("INVALID_GRANT_ID");
      if (!Array.isArray(input.actions) || !input.actions.length ||
          input.actions.some(function (a) { return !ALLOWED_ACTIONS.includes(a); })) throw new Error("ACTION_NOT_ALLOWED");
      var ttl = Number(input.ttlMs), uses = Number.isInteger(input.maxUses) ? input.maxUses : 1;
      if (!Number.isFinite(ttl) || ttl < 1000 || ttl > 900000) throw new Error("GRANT_TTL_OUT_OF_RANGE");
      if (uses < 1 || uses > 20) throw new Error("GRANT_USE_LIMIT_OUT_OF_RANGE");
      var g = { grantId: input.grantId, sessionId: input.sessionId, actions: new Set(input.actions),
        expiresAt: now() + ttl, maxUses: uses, uses: 0 };
      grants.set(g.grantId, g);
      audit("GRANT_ISSUED", { grantId: g.grantId, sessionId: g.sessionId });
      return Object.freeze({ grantId:g.grantId, sessionId:g.sessionId, actions:Array.from(g.actions),
        expiresAt:g.expiresAt, maxUses:g.maxUses });
    }
    function revokeGrant(id) { var ok = grants.delete(id); if (ok) audit("GRANT_REVOKED",{grantId:id}); return ok; }
    async function execute(input) {
      input = input || {};
      if (stopped) throw new Error("CONTROL_PLANE_STOPPED");
      if (!validId(input.actionId) || !validId(input.sessionId)) throw new Error("INVALID_ACTION_ID");
      if (results.has(input.actionId)) return results.get(input.actionId);
      var g = grants.get(input.grantId), action = input.action, sessionId = input.sessionId;
      if (!g || g.sessionId !== sessionId || g.expiresAt <= now() || g.uses >= g.maxUses || !g.actions.has(action)) {
        audit("ACTION_DENIED",{actionId:input.actionId,sessionId:sessionId,action:action,reason:"GRANT_REQUIRED"});
        throw new Error("ACTION_NOT_AUTHORIZED");
      }
      var fn = action === "SEND_MESSAGE" ? adapter.sendMessage :
        action === "REQUEST_RECONNECT" ? adapter.requestReconnect : action === "READ_STATUS" ? adapter.readStatus : null;
      if (typeof fn !== "function") throw new Error("ADAPTER_CAPABILITY_UNAVAILABLE");
      if (action === "SEND_MESSAGE" && (typeof input.message !== "string" || !input.message.length || input.message.length > 4000))
        throw new Error("MESSAGE_INVALID");
      g.uses += 1;
      audit("ACTION_STARTED",{actionId:input.actionId,grantId:g.grantId,sessionId:sessionId,action:action});
      try {
        var value = await fn.call(adapter,sessionId,action === "SEND_MESSAGE" ? input.message : undefined);
        var result = Object.freeze({actionId:input.actionId,status:"SUCCESS",
          result:action === "READ_STATUS" && value && typeof value.state === "string" ? {state:value.state} : null});
        results.set(input.actionId,result);
        audit("ACTION_FINISHED",{actionId:input.actionId,sessionId:sessionId,action:action,status:"SUCCESS"});
        return result;
      } catch (err) {
        results.set(input.actionId,Object.freeze({actionId:input.actionId,status:"FAILED"}));
        audit("ACTION_FINISHED",{actionId:input.actionId,sessionId:sessionId,action:action,status:"FAILED"});
        throw err;
      }
    }
    function observeHeartbeat(id, timestamp) {
      if (!validId(id)) throw new Error("INVALID_SESSION_ID");
      var at = Number(timestamp === undefined ? now() : timestamp);
      if (!Number.isFinite(at) || at > now() + 30000) throw new Error("INVALID_HEARTBEAT");
      var s = sessions.get(id) || {lastHeartbeat:0,state:"UNKNOWN"};
      if (at >= s.lastHeartbeat) {
        s.lastHeartbeat=at; s.state="CONNECTED"; s.missedAt=null; recovery.delete(id); sessions.set(id,s);
        audit("HEARTBEAT_RECEIVED",{sessionId:id,status:"CONNECTED"});
      }
      return Object.freeze({sessionId:id,lastHeartbeat:s.lastHeartbeat,state:s.state});
    }
    function inspectSession(id, staleAfterMs) {
      var s=sessions.get(id);
      if (!s) return Object.freeze({sessionId:id,state:"UNKNOWN",stale:true});
      var stale=now()-s.lastHeartbeat > Math.max(1000,Number(staleAfterMs)||15000);
      if (stale && s.state!=="OFFLINE") { s.state="OFFLINE"; s.missedAt=now(); audit("SESSION_STALE",{sessionId:id,status:"OFFLINE"}); }
      return Object.freeze({sessionId:id,state:s.state,stale:stale,lastHeartbeat:s.lastHeartbeat});
    }
    async function recoverSession(id) {
      if (stopped) throw new Error("CONTROL_PLANE_STOPPED");
      if (typeof adapter.requestReconnect!=="function") throw new Error("ADAPTER_CAPABILITY_UNAVAILABLE");
      var r=recovery.get(id)||{attempts:0,nextAt:0};
      if (r.attempts>=maxAttempts) return Object.freeze({status:"EXHAUSTED",attempts:r.attempts});
      if (now()<r.nextAt) return Object.freeze({status:"BACKOFF",attempts:r.attempts,retryAt:r.nextAt});
      r.attempts+=1; r.nextAt=now()+Math.min(maxDelay,baseDelay*Math.pow(2,r.attempts-1)); recovery.set(id,r);
      audit("RECOVERY_REQUESTED",{sessionId:id,attempt:r.attempts});
      try { await adapter.requestReconnect(id); return Object.freeze({status:"REQUESTED",attempts:r.attempts,retryAt:r.nextAt}); }
      catch (_) { audit("RECOVERY_FAILED",{sessionId:id,attempt:r.attempts}); return Object.freeze({status:"FAILED",attempts:r.attempts,retryAt:r.nextAt}); }
    }
    function stop() { stopped=true; grants.clear(); recovery.clear(); audit("CONTROL_PLANE_STOPPED",{}); }
    return Object.freeze({issueGrant:issueGrant,revokeGrant:revokeGrant,execute:execute,
      observeHeartbeat:observeHeartbeat,inspectSession:inspectSession,recoverSession:recoverSession,stop:stop,
      allowedActions:ALLOWED_ACTIONS});
  }
  root.AIBridgeControlPlane=Object.freeze({create:create,allowedActions:ALLOWED_ACTIONS});
})(typeof window!=="undefined"?window:globalThis);
