package com.vidiftmax.aibridgebrowser;

import android.media.AudioManager;
import android.media.ToneGenerator;

public final class PhoneSoundEngine {
    public static final int MESSAGE = 0;
    public static final int INVITATION = 1;
    public static final int CALL = 2;

    private PhoneSoundEngine() {}

    public static void preview(int preset) {
        final int[] tones;
        final int[] durations;
        switch (preset) {
            case INVITATION:
                tones = new int[]{ToneGenerator.TONE_PROP_BEEP, ToneGenerator.TONE_PROP_BEEP2};
                durations = new int[]{150, 260};
                break;
            case CALL:
                tones = new int[]{ToneGenerator.TONE_SUP_RINGTONE, ToneGenerator.TONE_SUP_RINGTONE};
                durations = new int[]{320, 520};
                break;
            case MESSAGE:
            default:
                tones = new int[]{ToneGenerator.TONE_PROP_ACK, ToneGenerator.TONE_PROP_ACK};
                durations = new int[]{110, 190};
                break;
        }
        new Thread(() -> {
            ToneGenerator generator = new ToneGenerator(AudioManager.STREAM_NOTIFICATION, 78);
            try {
                for (int i = 0; i < tones.length; i++) {
                    generator.startTone(tones[i], durations[i]);
                    try { Thread.sleep(durations[i] + 90L); }
                    catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); break; }
                }
            } finally {
                generator.release();
            }
        }, "ai-phone-tone").start();
    }
}
