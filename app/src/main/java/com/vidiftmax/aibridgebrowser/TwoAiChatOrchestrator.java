package com.vidiftmax.aibridgebrowser;

import android.os.Handler;
import android.os.Looper;
import android.webkit.WebView;
import java.util.Objects;

/**
 * User-started two-tab relay. AI-01 and AI-02 remain in separate WebViews/profiles.
 * The bridge alternates turns only after a completed assistant response is observed.
 */
final class TwoAiChatOrchestrator {
    interface Listener {
        void onState(String state);
        void onTurn(String senderAiId, String response);
        void onFinished(int turns);
        void onError(String code);
    }

    private static final int MAX_TURNS = 20;
    private static final long POLL_MS = 900L;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final ChatGPTDomBridge bridge;
    private final AiBridgeEvidence evidence = new AiBridgeEvidence();
    private boolean running;
    private int turns;
    private int maxTurns;
    private String nextAiId;
    private String pendingPrompt;
    private String previousResponse = "";
    private String lastDeliveredResponse = "";
    private WebView ai01;
    private WebView ai02;
    private Listener listener;

    TwoAiChatOrchestrator(ChatGPTDomBridge bridge) {
        this.bridge = Objects.requireNonNull(bridge);
    }

    boolean start(WebView ai01, WebView ai02, String firstPrompt, int maxTurns, Listener listener) {
        if (running || !AiBridgeRoundTripPolicy.isAllowed(new String[]{"AI-01","AI-02"}) ||
                ai01 == null || ai02 == null || listener == null ||
                firstPrompt == null || firstPrompt.trim().isEmpty() ||
                !AiBridgeRoundTripPolicy.isTurnCountAllowed(maxTurns)) return false;
        this.ai01 = ai01;
        this.ai02 = ai02;
        this.pendingPrompt = firstPrompt.trim();
        this.maxTurns = maxTurns;
        this.turns = 0;
        this.nextAiId = "AI-01";
        this.previousResponse = "";
        this.lastDeliveredResponse = "";
        this.evidence.clear();
        this.listener = listener;
        this.running = true;
        bridge.install(ai01);
        bridge.install(ai02);
        listener.onState("AI-01 preparando envio");
        sendCurrent();
        return true;
    }

    void stop() {
        running = false;
        handler.removeCallbacksAndMessages(null);
        if (listener != null) listener.onState("PARADO");
        listener = null;
    }

    private WebView current() { return "AI-01".equals(nextAiId) ? ai01 : ai02; }

    int getTurnCount() { return turns; }

    String lastDeliveredResponse() { return lastDeliveredResponse; }

    String evidenceSummary() { return evidence.summary(); }

    private void sendCurrent() {
        if (!running) return;
        final WebView target = current();
        final String prompt = pendingPrompt;
        final String sender = nextAiId;
        bridge.inspect(target, before -> {
            if (!running) return;
            String baseline = extract(before, "latestAssistant");
            previousResponse = baseline == null ? "" : baseline;
            bridge.send(target, prompt, result -> {
                if (!running) return;
                if (result == null || !result.contains("SUBMITTED")) {
                    fail("SEND_FAILED_" + sender);
                    return;
                }
                listener.onState(sender + " enviou; aguardando resposta");
                pollResponse(target, sender, previousResponse, 0);
            });
        });
    }

    private void pollResponse(WebView target, String sender, String baseline, int attempts) {
        if (!running) return;
        bridge.inspect(target, json -> {
            if (!running) return;
            String response = extract(json, "latestAssistant");
            boolean generating = "true".equals(extract(json, "generating"));
            if (!generating && AiBridgeRoundTripPolicy.isFreshResponse(baseline, response)) {
                turns++;
                lastDeliveredResponse = response;
                if (!evidence.addTurn(turns, sender, response)) {
                    fail("EVIDENCE_CAPTURE_FAILED_" + sender);
                    return;
                }
                listener.onTurn(sender, response);
                if (turns >= maxTurns) {
                    running = false;
                    listener.onFinished(turns);
                    return;
                }
                pendingPrompt = response;
                nextAiId = "AI-01".equals(sender) ? "AI-02" : "AI-01";
                listener.onState(nextAiId + " preparando resposta");
                sendCurrent();
                return;
            }
            if (attempts >= 80) { fail("RESPONSE_TIMEOUT_" + sender); return; }
            handler.postDelayed(() -> pollResponse(target, sender, baseline, attempts + 1), POLL_MS);
        });
    }

    private void fail(String code) {
        running = false;
        handler.removeCallbacksAndMessages(null);
        if (listener != null) listener.onError(code);
    }

    private static String extract(String json, String key) {
        if (json == null || json.equals("null")) return null;
        try {
            String decoded = json.startsWith("\"") ?
                    new org.json.JSONTokener(json).nextValue().toString() : json;
            org.json.JSONObject object = new org.json.JSONObject(decoded);
            return object.optString(key, null);
        } catch (Exception ignored) {
            return null;
        }
    }
}
