package com.vidiftmax.aibridgebrowser;

import java.util.UUID;

/** Durable tab metadata. WebView remains outside this model. */
final class TabRecord {
    final String tabId;
    final String profileId;
    String url;
    String title;
    boolean locked;
    String missionState;

    TabRecord(String url) {
        this(UUID.randomUUID().toString(), "profile-" + UUID.randomUUID(), url);
    }

    TabRecord(String tabId, String profileId, String url) {
        this.tabId = tabId;
        this.profileId = profileId;
        this.url = url;
        this.title = "Nova aba";
        this.locked = true;
        this.missionState = "WAITING_PAGE";
    }
}