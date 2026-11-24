package com.vidiftmax.aibridgebrowser;

import org.junit.Test;

import static org.junit.Assert.assertEquals;

public class AudioFilePolicyTest {
    @Test public void acceptsPositiveSizeWithinLimit() {
        AudioFilePolicy.validateSize(1024);
        AudioFilePolicy.validateSize(AudioFilePolicy.MAX_BYTES);
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsEmptyAudio() {
        AudioFilePolicy.validateSize(0);
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsOversizedAudio() {
        AudioFilePolicy.validateSize(AudioFilePolicy.MAX_BYTES + 1);
    }

    @Test public void recordingTypeIsStable() {
        assertEquals("audio/mp4", AudioFilePolicy.contentTypeForRecording());
    }
}
