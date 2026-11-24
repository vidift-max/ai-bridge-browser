export const GUEST_PROVIDER_CLAIMS = Object.freeze([
  "CHATGPT", "GEMINI", "CLAUDE", "KIMI", "OTHER"
]);
export const GUEST_PARTICIPANT_TYPES = Object.freeze([
  "HUMAN_OPERATOR", "EXTERNAL_AGENT"
]);

const cleanText = (value, max) => typeof value === "string"
  ? value.normalize("NFKC").trim().replace(/[\\u0000-\\u001f\\u007f]/g, "").slice(0, max)
  : "";

export function validateGuestJoinRequest(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    return { ok: false, reason: "request_object_required" };
  }
  const displayName = cleanText(input.displayName, 60);
  const providerClaim = typeof input.providerClaim === "string" ? input.providerClaim : "";
  const participantType = typeof input.participantType === "string" ? input.participantType : "";
  if (displayName.length < 2) return { ok: false, reason: "display_name_invalid" };
  if (!GUEST_PROVIDER_CLAIMS.includes(providerClaim)) return { ok: false, reason: "provider_claim_invalid" };
  if (!GUEST_PARTICIPANT_TYPES.includes(participantType)) return { ok: false, reason: "participant_type_invalid" };
  return {
    ok: true,
    request: Object.freeze({
      displayName,
      providerClaim,
      participantType,
      admissionStatus: "PENDING_ADMIN_APPROVAL",
      identityVerified: false,
      providerVerified: false,
      autoAdmission: false,
      autoExecution: false
    })
  };
}

export function guestJoinDisclosure() {
  return Object.freeze({
    inviteGrantsAdmission: false,
    inviteAuthenticatesProvider: false,
    externalPlatformAutomationGuaranteed: false,
    adminApprovalRequired: true,
    aiBridgeBrowserInstallationRequiredForWebGuest: false
  });
}
