import test from "node:test";
import assert from "node:assert/strict";
import { validateGuestJoinRequest, guestJoinDisclosure } from "./guest-join-contract.js";

test("accepts a minimal declared guest identity but keeps it unverified and pending", () => {
  const result = validateGuestJoinRequest({
    displayName: "Gemini convidado", providerClaim: "GEMINI", participantType: "EXTERNAL_AGENT"
  });
  assert.equal(result.ok, true);
  assert.equal(result.request.admissionStatus, "PENDING_ADMIN_APPROVAL");
  assert.equal(result.request.identityVerified, false);
  assert.equal(result.request.providerVerified, false);
  assert.equal(result.request.autoAdmission, false);
  assert.equal(result.request.autoExecution, false);
});

test("rejects malformed input and arrays", () => {
  assert.equal(validateGuestJoinRequest(null).reason, "request_object_required");
  assert.equal(validateGuestJoinRequest([]).reason, "request_object_required");
});

test("requires a meaningful bounded display name", () => {
  assert.equal(validateGuestJoinRequest({displayName:" ",providerClaim:"OTHER",participantType:"HUMAN_OPERATOR"}).reason, "display_name_invalid");
  const result = validateGuestJoinRequest({displayName:"A".repeat(90),providerClaim:"OTHER",participantType:"HUMAN_OPERATOR"});
  assert.equal(result.request.displayName.length, 60);
});

test("rejects provider names outside the allowlist", () => {
  assert.equal(validateGuestJoinRequest({displayName:"Guest",providerClaim:"UNKNOWN",participantType:"EXTERNAL_AGENT"}).reason, "provider_claim_invalid");
});

test("rejects participant types outside the allowlist", () => {
  assert.equal(validateGuestJoinRequest({displayName:"Guest",providerClaim:"OTHER",participantType:"ADMIN"}).reason, "participant_type_invalid");
});

test("normalizes display names and strips control characters", () => {
  const result = validateGuestJoinRequest({displayName:"  AI\\u0000 Guest  ",providerClaim:"CLAUDE",participantType:"EXTERNAL_AGENT"});
  assert.equal(result.request.displayName, "AI Guest");
});

test("does not copy credentials, invite tokens, or arbitrary caller fields", () => {
  const result = validateGuestJoinRequest({
    displayName:"Guest",providerClaim:"KIMI",participantType:"EXTERNAL_AGENT",
    token:"secret",bearer:"secret",inviteToken:"secret",isAdmin:true,aiId:"forged"
  });
  assert.deepEqual(Object.keys(result.request).sort(), [
    "admissionStatus","autoAdmission","autoExecution","displayName",
    "identityVerified","participantType","providerClaim","providerVerified"
  ].sort());
});

test("provider claim remains a claim, never proof of provider identity", () => {
  const result = validateGuestJoinRequest({displayName:"Claude",providerClaim:"CLAUDE",participantType:"EXTERNAL_AGENT"});
  assert.equal(result.request.providerVerified, false);
});

test("disclosure explicitly avoids promising external platform automation", () => {
  const disclosure = guestJoinDisclosure();
  assert.equal(disclosure.externalPlatformAutomationGuaranteed, false);
  assert.equal(disclosure.inviteAuthenticatesProvider, false);
});

test("web guest access does not require installing the AI Bridge Browser", () => {
  assert.equal(guestJoinDisclosure().aiBridgeBrowserInstallationRequiredForWebGuest, false);
});
