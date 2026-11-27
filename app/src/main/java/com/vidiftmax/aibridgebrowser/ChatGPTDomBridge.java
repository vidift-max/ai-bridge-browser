package com.vidiftmax.aibridgebrowser;

import android.content.Context;
import android.webkit.WebView;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

/**
 * Explicit DOM boundary for ChatGPT WebView automation.
 * It never bypasses authentication and only acts on the selected WebView after
 * the user starts an AI-01 <-> AI-02 conversation.
 */
final class ChatGPTDomBridge {
    interface ResultCallback { void onResult(String json); }

    private final String script;

    ChatGPTDomBridge(Context context) {
        script = readAsset(context, "ai_bridge_chatgpt_dom_bridge.js");
    }

    void install(WebView webView) {
        if (webView == null) return;
        webView.evaluateJavascript(script, null);
    }

    void inspect(WebView webView, ResultCallback callback) {
        evaluate(webView, "window.AIBridgeChatGPTDomBridge&&window.AIBridgeChatGPTDomBridge.inspect(document)", callback);
    }

    void send(WebView webView, String text, ResultCallback callback) {
        String encoded = org.json.JSONObject.quote(text == null ? "" : text);
        evaluate(webView,
                "window.AIBridgeChatGPTDomBridge&&window.AIBridgeChatGPTDomBridge.prepareAndSend(document," + encoded + ")",
                callback);
    }

    private void evaluate(WebView webView, String expression, ResultCallback callback) {
        if (webView == null) { if (callback != null) callback.onResult(null); return; }
        webView.evaluateJavascript("(function(){try{return JSON.stringify(" + expression + ")}catch(e){return JSON.stringify({ok:false,code:'BRIDGE_EXCEPTION',message:String(e)})}})()",
                value -> { if (callback != null) callback.onResult(value); });
    }

    private static String readAsset(Context context, String name) {
        StringBuilder out = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                context.getAssets().open(name), StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) out.append(line).append('\n');
            return out.toString();
        } catch (Exception e) {
            throw new IllegalStateException("CHATGPT_DOM_BRIDGE_ASSET_UNAVAILABLE", e);
        }
    }
}
