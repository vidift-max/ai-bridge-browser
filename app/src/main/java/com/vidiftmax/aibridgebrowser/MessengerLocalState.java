package com.vidiftmax.aibridgebrowser;

/**
 * Local-only message state. These states describe this device's local record,
 * not remote delivery.
 */
public final class MessengerLocalState {
    public static final String SAVED_LOCAL = "SAVED_LOCAL";
    public static final String READ_LOCAL = "READ_LOCAL";
    public static final String ARCHIVED_LOCAL = "ARCHIVED_LOCAL";

    private MessengerLocalState() {}

    public static boolean isValid(String state) {
        return SAVED_LOCAL.equals(state)
                || READ_LOCAL.equals(state)
                || ARCHIVED_LOCAL.equals(state);
    }
}
