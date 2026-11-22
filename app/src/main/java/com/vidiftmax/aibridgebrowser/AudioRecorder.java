package com.vidiftmax.aibridgebrowser;

import android.content.Context;
import android.media.MediaRecorder;
import java.io.File;
import java.io.IOException;

/** Records an AAC-in-MP4 voice note only after the caller explicitly starts it. */
public final class AudioRecorder {
    private static final long MAX_BYTES = 5L * 1024L * 1024L;
    private MediaRecorder recorder;
    private File outputFile;
    private boolean recorderStoppedByLimit;

    public synchronized File start(Context context) throws IOException {
        if (recorder != null) throw new IllegalStateException("recording_already_active");
        File dir = new File(context.getCacheDir(), "voice_notes");
        if (!dir.exists() && !dir.mkdirs()) throw new IOException("voice_note_directory_unavailable");
        outputFile = File.createTempFile("voice-", ".m4a", dir);
        MediaRecorder r = new MediaRecorder();
        try {
            r.setAudioSource(MediaRecorder.AudioSource.MIC);
            r.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);
            r.setAudioEncoder(MediaRecorder.AudioEncoder.AAC);
            r.setAudioEncodingBitRate(64000);
            r.setAudioSamplingRate(44100);
            r.setMaxFileSize(MAX_BYTES);
            r.setMaxDuration(5 * 60 * 1000);
            recorderStoppedByLimit = false;
            r.setOnInfoListener((mr, what, extra) -> {
                if (what == MediaRecorder.MEDIA_RECORDER_INFO_MAX_FILESIZE_REACHED ||
                        what == MediaRecorder.MEDIA_RECORDER_INFO_MAX_DURATION_REACHED) recorderStoppedByLimit = true;
            });
            r.setOutputFile(outputFile.getAbsolutePath());
            r.prepare();
            r.start();
            recorder = r;
            return outputFile;
        } catch (RuntimeException | IOException error) {
            r.release();
            outputFile.delete();
            outputFile = null;
            recorderStoppedByLimit = false;
            throw error;
        }
    }

    public synchronized File stop() {
        if (recorder == null || outputFile == null) throw new IllegalStateException("recording_not_active");
        MediaRecorder r = recorder;
        File result = outputFile;
        recorder = null;
        outputFile = null;
        try {
            if (!recorderStoppedByLimit) r.stop();
        } finally {
            r.release();
        }
        recorderStoppedByLimit = false;
        if (!result.isFile() || result.length() <= 0 || result.length() > MAX_BYTES) {
            result.delete();
            throw new IllegalStateException("voice_note_size_invalid");
        }
        return result;
    }

    public synchronized boolean isRecording() {
        return recorder != null;
    }

    public synchronized void cancel() {
        if (recorder == null) return;
        MediaRecorder r = recorder;
        File result = outputFile;
        recorder = null;
        outputFile = null;
        try { if (!recorderStoppedByLimit) r.stop(); } catch (RuntimeException ignored) { }
        r.release();
        if (result != null) result.delete();
    }
}
