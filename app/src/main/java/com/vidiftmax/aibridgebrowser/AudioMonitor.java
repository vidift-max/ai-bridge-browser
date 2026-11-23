package com.vidiftmax.aibridgebrowser;

import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.AudioTrack;
import android.media.MediaRecorder;

public final class AudioMonitor {
    private AudioRecord recorder;
    private AudioTrack player;
    private Thread worker;
    private volatile boolean running;
    private volatile boolean playbackEnabled;

    public AudioMonitor() {
        playbackEnabled = true;
    }

    public synchronized void setPlaybackEnabled(boolean enabled) {
        playbackEnabled = enabled;
    }

    public synchronized boolean isPlaybackEnabled() {
        return playbackEnabled;
    }

    public synchronized void start() {
        if (running) return;
        int minRecord = AudioRecord.getMinBufferSize(
                16000, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
        int minPlay = AudioTrack.getMinBufferSize(
                16000, AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT);
        if (minRecord <= 0 || minPlay <= 0) throw new IllegalStateException("audio_monitor_unavailable");
        int buffer = Math.max(minRecord, minPlay) * 2;
        AudioRecord r = new AudioRecord(
                MediaRecorder.AudioSource.VOICE_COMMUNICATION,
                16000,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                buffer);
        AudioTrack p = new AudioTrack(
                android.media.AudioManager.STREAM_VOICE_CALL,
                16000,
                AudioFormat.CHANNEL_OUT_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                buffer,
                AudioTrack.MODE_STREAM);
        recorder = r;
        player = p;
        running = true;
        worker = new Thread(() -> {
            byte[] data = new byte[buffer];
            try {
                r.startRecording();
                p.play();
                while (running) {
                    int read = r.read(data, 0, data.length);
                    if (read > 0 && running && playbackEnabled) p.write(data, 0, read);
                }
            } finally {
                try { r.stop(); } catch (RuntimeException ignored) {}
                try { p.stop(); } catch (RuntimeException ignored) {}
                r.release();
                p.release();
                synchronized (AudioMonitor.this) {
                    if (recorder == r) recorder = null;
                    if (player == p) player = null;
                    worker = null;
                }
            }
        }, "ai-phone-audio-monitor");
        worker.start();
    }

    public synchronized void stop() {
        running = false;
        Thread t = worker;
        worker = null;
        if (t != null) t.interrupt();
    }

    public synchronized boolean isRunning() {
        return running;
    }
}