package com.vidiftmax.aibridgebrowser;

import org.json.JSONException;
import org.json.JSONObject;

/** Builds a credential-free, read-only first-contact diagnostic result. */
public final class FirebaseFirstContactDiagnostics {
    private FirebaseFirstContactDiagnostics() { }

    public static JSONObject evaluate(String expectedAiId, String authenticatedUid,
                                       JSONObject identity, JSONObject conversation)
            throws JSONException {
        if (expectedAiId == null || expectedAiId.trim().isEmpty())
            throw new IllegalArgumentException("ai_id_required");
        if (authenticatedUid == null || authenticatedUid.trim().isEmpty())
            throw new IllegalArgumentException("authenticated_uid_required");
        if (identity == null || !expectedAiId.equals(identity.optString("aiId", "")))
            throw new IllegalStateException("firebase_identity_not_provisioned");
        if (!authenticatedUid.equals(identity.optString("uid", "")))
            throw new IllegalStateException("firebase_identity_uid_mismatch");
        if (conversation == null) throw new IllegalStateException("firebase_conversation_not_found");
        JSONObject members = conversation.optJSONObject("members");
        if (members == null || !members.optBoolean(expectedAiId, false))
            throw new IllegalStateException("firebase_room_membership_missing");
        return new JSONObject()
                .put("state", "CLIENT_PREFLIGHT_PASS")
                .put("transport", "firebase_rtdb")
                .put("aiId", expectedAiId)
                .put("identityMatch", true)
                .put("authenticated", true)
                .put("roomMembership", "PASS")
                .put("credentialDisclosure", "NONE");
    }
}
