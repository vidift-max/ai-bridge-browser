package com.vidiftmax.aibridgebrowser;

/** Pure lifecycle gate for updater callbacks posted from background work. */
public final class UpdaterUiPolicy {
    private UpdaterUiPolicy() {}

    public static boolean shouldDeliver(boolean destroyed, boolean finishing, boolean activityDestroyed) {
        return !destroyed && !finishing && !activityDestroyed;
    }
}
