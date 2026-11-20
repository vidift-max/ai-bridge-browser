package com.vidiftmax.aibridgebrowser;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Small in-memory model for browser structure. No remote-control behavior. */
final class BrowserState {
    private final List<String> tabIds = new ArrayList<>();
    private int activeIndex = 0;
    private boolean paused = false;

    List<String> getTabIds() { return Collections.unmodifiableList(tabIds); }
    int getActiveIndex() { return activeIndex; }
    boolean isPaused() { return paused; }

    void replaceTabs(List<String> ids, int active, boolean isPaused) {
        tabIds.clear();
        tabIds.addAll(ids);
        activeIndex = Math.max(0, Math.min(active, Math.max(0, tabIds.size() - 1)));
        paused = isPaused;
    }

    void addTab(String tabId) {
        if (tabId == null || tabId.trim().isEmpty() || tabIds.contains(tabId)) return;
        tabIds.add(tabId);
        activeIndex = tabIds.size() - 1;
    }

    boolean removeTab(String tabId) {
        int index = tabIds.indexOf(tabId);
        if (index < 0) return false;
        tabIds.remove(index);
        if (tabIds.isEmpty()) activeIndex = 0;
        else if (activeIndex >= tabIds.size()) activeIndex = tabIds.size() - 1;
        return true;
    }

    boolean selectTab(int index) {
        if (index < 0 || index >= tabIds.size()) return false;
        activeIndex = index;
        return true;
    }

    void setPaused(boolean value) { paused = value; }
}
