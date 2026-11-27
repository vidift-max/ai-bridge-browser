package com.vidiftmax.aibridgebrowser;

import org.junit.Test;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Collections;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import static org.junit.Assert.*;

public final class DataSafeArchiveEngineTest {
    @Test public void writesAndValidatesArchiveWithChecksumIndex() throws Exception {
        File file = File.createTempFile("data-safe-", ".zip");
        try {
            Map<String, byte[]> source = Collections.singletonMap(
                    "browser/state.json", "{\"tabs\":[]}".getBytes(StandardCharsets.UTF_8));
            try (FileOutputStream output = new FileOutputStream(file)) {
                DataSafeArchiveEngine.write(output, source);
            }
            Map<String, byte[]> restored = DataSafeArchiveEngine.readAndValidate(file);
            assertArrayEquals(source.get("browser/state.json"), restored.get("browser/state.json"));
            assertEquals(1, restored.size());
        } finally {
            assertTrue(file.delete());
        }
    }

    @Test public void rejectsTraversalBeforeAnyExtraction() throws Exception {
        File file = rawZip("../outside.txt", new byte[] {1}, "");
        try {
            try {
                DataSafeArchiveEngine.readAndValidate(file);
                fail("Traversal must be rejected");
            } catch (IOException expected) {
                assertEquals("archive_path_rejected", expected.getMessage());
            }
        } finally {
            assertTrue(file.delete());
        }
    }

    @Test public void rejectsCompressionRatioAboveLimit() throws Exception {
        byte[] repetitive = new byte[128 * 1024];
        File file = rawZip("payload.bin", repetitive, checksumLine("payload.bin", repetitive));
        try {
            try {
                DataSafeArchiveEngine.readAndValidate(file);
                fail("High compression ratio must be rejected");
            } catch (IOException expected) {
                assertEquals("archive_compression_ratio_exceeded", expected.getMessage());
            }
        } finally {
            assertTrue(file.delete());
        }
    }

    @Test public void rejectsChecksumMismatch() throws Exception {
        byte[] data = "actual".getBytes(StandardCharsets.UTF_8);
        File file = rawZip("state.json", data, repeat('0', 64) + "  state.json\n");
        try {
            try {
                DataSafeArchiveEngine.readAndValidate(file);
                fail("Checksum mismatch must be rejected");
            } catch (IOException expected) {
                assertEquals("archive_checksum_mismatch", expected.getMessage());
            }
        } finally {
            assertTrue(file.delete());
        }
    }

    @Test public void writerRejectsReservedChecksumName() throws Exception {
        try {
            DataSafeArchiveEngine.write(new ByteArrayOutputStream(),
                    Collections.singletonMap(DataSafeArchiveEngine.CHECKSUMS_ENTRY, new byte[] {1}));
            fail("Reserved checksum path must be rejected");
        } catch (IllegalArgumentException expected) {
            assertEquals("archive_reserved_or_null_entry", expected.getMessage());
        }
    }

    private static File rawZip(String name, byte[] data, String checksum) throws Exception {
        File file = File.createTempFile("data-safe-raw-", ".zip");
        try (ZipOutputStream zip = new ZipOutputStream(new FileOutputStream(file))) {
            zip.putNextEntry(new ZipEntry(name));
            zip.write(data);
            zip.closeEntry();
            zip.putNextEntry(new ZipEntry(DataSafeArchiveEngine.CHECKSUMS_ENTRY));
            zip.write(checksum.getBytes(StandardCharsets.UTF_8));
            zip.closeEntry();
        }
        return file;
    }

    private static String checksumLine(String name, byte[] data) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256").digest(data);
        StringBuilder hex = new StringBuilder();
        for (byte b : digest) hex.append(String.format(java.util.Locale.ROOT, "%02x", b & 0xff));
        return hex + "  " + name + "\n";
    }

    private static String repeat(char value, int count) {
        char[] chars = new char[count];
        java.util.Arrays.fill(chars, value);
        return new String(chars);
    }
}
