package com.vidiftmax.aibridgebrowser;

import android.media.MediaPlayer;
import java.io.File;

/** Small lifecycle wrapper for one local voice note. */
public final class AudioPlayback {
    private MediaPlayer player;

    public synchronized void play(File file) throws Exception {
        stop();
        if (file == null || !file.isFile() || file.length() <= 0) throw new IllegalArgumentException("voice_note_missing");
        MediaPlayer p = new MediaPlayer();
        try {
            p.setDataSource(file.getAbsolutePath());
            p.setOnCompletionListener(done -> {
                synchronized (AudioPlayback.this) {
                    if (player == done) {
                        done.release();
                        player = null;
                    }
                }
            });
            p.prepare();
            p.start();
            player = p;
        } catch (Exception error) {
            p.release();
            throw error;
        }
    }

    public synchronized void stop() {
        if (player == null) return;
        try { player.stop(); } catch (RuntimeException ignored) { }
        player.release();
        player = null;
    }
}
