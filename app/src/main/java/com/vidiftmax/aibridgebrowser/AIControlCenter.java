package com.vidiftmax.aibridgebrowser;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Dynamic control-center registry for up to six independently bound AI tabs. */
final class AIControlCenter {
    static final int MAX_AI_TABS = 6;
    enum ResponseState { IDLE, SENDING, RESPONDING, RESPONSE_COMPLETE, ERROR }
    enum ContextState { UNKNOWN, NORMAL, CRITICAL, FULL, NEW_CHAT_REQUIRED, NEW_CHAT_LOADING }

    static final class Panel {
        final String aiId;
        final String tabId;
        final String profileId;
        String responseTail = "";
        String pendingMessage = "";
        ResponseState responseState = ResponseState.IDLE;
        ContextState contextState = ContextState.UNKNOWN;
        boolean reportConfirmed;
        Panel(String aiId, String tabId, String profileId) {
            this.aiId = aiId; this.tabId = tabId; this.profileId = profileId;
        }
    }

    private final List<Panel> panels = new ArrayList<>();
    List<Panel> panels() { return Collections.unmodifiableList(panels); }

    boolean register(String aiId, String tabId, String profileId) {
        if (blank(aiId) || blank(tabId) || blank(profileId)) return false;
        if (findByTab(tabId) != null || findByAi(aiId) != null || panels.size() >= MAX_AI_TABS) return false;
        panels.add(new Panel(aiId, tabId, profileId));
        return true;
    }

    boolean unregisterByTab(String tabId) {
        Panel panel = findByTab(tabId);
        return panel != null && panels.remove(panel);
    }

    boolean beginMessage(String tabId, String profileId, String message) {
        Panel panel = find(tabId, profileId);
        if (panel == null || blank(message)) return false;
        panel.responseTail = ""; panel.pendingMessage = message;
        panel.responseState = ResponseState.SENDING; panel.reportConfirmed = false;
        return true;
    }

    boolean markResponding(String tabId, String profileId) {
        Panel panel = find(tabId, profileId);
        if (panel == null || panel.responseState != ResponseState.SENDING) return false;
        panel.responseState = ResponseState.RESPONDING; return true;
    }

    boolean completeResponse(String tabId, String profileId, String responseText) {
        Panel panel = find(tabId, profileId);
        if (panel == null || panel.responseState != ResponseState.RESPONDING) return false;
        panel.responseTail = lastTwoLines(responseText); panel.pendingMessage = "";
        panel.responseState = ResponseState.RESPONSE_COMPLETE; return true;
    }

    boolean setContextState(String tabId, String profileId, ContextState state) {
        Panel panel = find(tabId, profileId);
        if (panel == null || state == null) return false;
        panel.contextState = state; return true;
    }

    boolean confirmReport(String tabId, String profileId) {
        Panel panel = find(tabId, profileId);
        if (panel == null || panel.responseState != ResponseState.RESPONSE_COMPLETE) return false;
        panel.reportConfirmed = true; return true;
    }

    private Panel findByTab(String tabId) {
        for (Panel panel : panels) if (panel.tabId.equals(tabId)) return panel;
        return null;
    }
    private Panel findByAi(String aiId) {
        for (Panel panel : panels) if (panel.aiId.equals(aiId)) return panel;
        return null;
    }
    private Panel find(String tabId, String profileId) {
        for (Panel panel : panels) if (panel.tabId.equals(tabId) && panel.profileId.equals(profileId)) return panel;
        return null;
    }
    private static String lastTwoLines(String value) {
        if (value == null || value.trim().isEmpty()) return "";
        String[] lines = value.replace("\r\n", "\n").replace('\r', '\n').trim().split("\n");
        StringBuilder result = new StringBuilder();
        for (int i = Math.max(0, lines.length - 2); i < lines.length; i++) {
            if (result.length() > 0) result.append('\n');
            result.append(lines[i].trim());
        }
        return result.toString();
    }
    private static boolean blank(String value) { return value == null || value.trim().isEmpty(); }
}