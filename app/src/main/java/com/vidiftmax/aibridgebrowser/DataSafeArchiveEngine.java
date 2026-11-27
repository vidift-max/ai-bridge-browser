package com.vidiftmax.aibridgebrowser;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FilterOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import java.util.zip.ZipOutputStream;

/**
 * Validates a DATA SAFE ZIP without extracting entries to disk.
 * The caller remains responsible for encrypting the completed ZIP with DataSafeCrypto.
 */
public final class DataSafeArchiveEngine {
    public static final String CHECKSUMS_ENTRY = "checksums.sha256";
    private static final int BUFFER_BYTES = 8192;

    private DataSafeArchiveEngine() {}

    /** Writes validated in-memory files and a SHA-256 index to the supplied stream. */
    public static void write(OutputStream destination, Map<String, byte[]> files) throws IOException {
        if (destination == null || files == null) throw new IllegalArgumentException("archive_arguments_required");
        if (files.isEmpty() || files.size() >= DataSafeLimits.MAX_ENTRIES)
            throw new IllegalArgumentException("archive_entry_count_invalid");

        Map<String, byte[]> ordered = new LinkedHashMap<>();
        long expanded = 0;
        for (Map.Entry<String, byte[]> item : files.entrySet()) {
            String path = DataSafePathPolicy.validate(item.getKey());
            byte[] data = item.getValue();
            if (CHECKSUMS_ENTRY.equals(path) || data == null)
                throw new IllegalArgumentException("archive_reserved_or_null_entry");
            if (ordered.containsKey(path)) throw new IllegalArgumentException("archive_duplicate_path");
            if (data.length > DataSafeLimits.MAX_ENTRY_BYTES)
                throw new IllegalArgumentException("archive_entry_too_large");
            expanded += data.length;
            if (expanded > DataSafeLimits.MAX_TOTAL_EXPANDED_BYTES)
                throw new IllegalArgumentException("archive_expanded_size_exceeded");
            ordered.put(path, data);
        }

        List<String> names = new ArrayList<>(ordered.keySet());
        Collections.sort(names);
        StringBuilder index = new StringBuilder();
        for (String name : names) index.append(hex(sha256(ordered.get(name))))
                .append("  ").append(name).append("\n");
        long checksumBytes = index.toString().getBytes(StandardCharsets.UTF_8).length;
        if (checksumBytes > DataSafeLimits.MAX_ENTRY_BYTES
                || expanded + checksumBytes > DataSafeLimits.MAX_TOTAL_EXPANDED_BYTES)
            throw new IllegalArgumentException("archive_checksum_index_too_large");

        CountingOutputStream bounded = new CountingOutputStream(destination, DataSafeLimits.MAX_ARCHIVE_BYTES);
        ZipOutputStream zip = new ZipOutputStream(bounded, StandardCharsets.UTF_8);
        for (String name : names) {
            ZipEntry entry = new ZipEntry(name);
            entry.setTime(0L);
            zip.putNextEntry(entry);
            zip.write(ordered.get(name));
            zip.closeEntry();
        }
        ZipEntry checksumEntry = new ZipEntry(CHECKSUMS_ENTRY);
        checksumEntry.setTime(0L);
        zip.putNextEntry(checksumEntry);
        zip.write(index.toString().getBytes(StandardCharsets.UTF_8));
        zip.closeEntry();
        zip.finish();
        zip.flush();
    }

    /**
     * Reads and verifies every entry in memory. No archive path is ever used to create a file.
     * The returned map excludes the checksum index.
     */
    public static Map<String, byte[]> readAndValidate(File archive) throws IOException {
        if (archive == null || !archive.isFile()) throw new IOException("archive_file_required");
        if (archive.length() <= 0 || archive.length() > DataSafeLimits.MAX_ARCHIVE_BYTES)
            throw new IOException("archive_size_invalid");

        Map<String, byte[]> payloads = new LinkedHashMap<>();
        Map<String, String> expectedHashes = new HashMap<>();
        Set<String> seen = new HashSet<>();
        long totalExpanded = 0;
        boolean checksumFound = false;

        try (ZipFile zip = new ZipFile(archive, StandardCharsets.UTF_8)) {
            Enumeration<? extends ZipEntry> entries = zip.entries();
            int count = 0;
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                if (++count > DataSafeLimits.MAX_ENTRIES) throw new IOException("archive_entry_count_exceeded");
                String name;
                try {
                    name = DataSafePathPolicy.validate(entry.getName());
                } catch (IllegalArgumentException invalidPath) {
                    throw new IOException("archive_path_rejected", invalidPath);
                }
                if (!seen.add(name)) throw new IOException("archive_duplicate_path");
                if (entry.isDirectory()) throw new IOException("archive_directory_entries_not_allowed");
                long declared = entry.getSize();
                long compressed = entry.getCompressedSize();
                if (declared < 0 || compressed < 0) throw new IOException("archive_size_metadata_missing");
                if (declared > DataSafeLimits.MAX_ENTRY_BYTES) throw new IOException("archive_entry_too_large");
                if (declared > 0 && (compressed <= 0
                        || declared > compressed * (long) DataSafeLimits.MAX_COMPRESSION_RATIO))
                    throw new IOException("archive_compression_ratio_exceeded");
                totalExpanded += declared;
                if (totalExpanded > DataSafeLimits.MAX_TOTAL_EXPANDED_BYTES)
                    throw new IOException("archive_expanded_size_exceeded");

                byte[] bytes;
                try (InputStream input = zip.getInputStream(entry)) {
                    bytes = readBounded(input, declared);
                }
                if (bytes.length != declared) throw new IOException("archive_entry_size_mismatch");
                if (CHECKSUMS_ENTRY.equals(name)) {
                    checksumFound = true;
                    parseChecksumIndex(bytes, expectedHashes);
                } else {
                    payloads.put(name, bytes);
                }
            }
            if (count == 0 || !checksumFound) throw new IOException("archive_checksum_index_missing");
        }

        if (expectedHashes.size() != payloads.size()) throw new IOException("archive_checksum_set_mismatch");
        for (Map.Entry<String, byte[]> item : payloads.entrySet()) {
            String expected = expectedHashes.get(item.getKey());
            if (expected == null || !expected.equals(hex(sha256(item.getValue()))))
                throw new IOException("archive_checksum_mismatch");
        }
        return Collections.unmodifiableMap(payloads);
    }

    private static byte[] readBounded(InputStream input, long declared) throws IOException {
        ByteArrayOutputStream output = new ByteArrayOutputStream((int) Math.min(declared, BUFFER_BYTES));
        byte[] buffer = new byte[BUFFER_BYTES];
        long total = 0;
        int read;
        while ((read = input.read(buffer)) != -1) {
            total += read;
            if (total > DataSafeLimits.MAX_ENTRY_BYTES || total > declared)
                throw new IOException("archive_actual_size_exceeded");
            output.write(buffer, 0, read);
        }
        return output.toByteArray();
    }

    private static void parseChecksumIndex(byte[] bytes, Map<String, String> hashes) throws IOException {
        String text = new String(bytes, StandardCharsets.UTF_8);
        if (text.isEmpty() || !text.endsWith("\n")) throw new IOException("archive_checksum_index_invalid");
        String[] lines = text.split("\n", -1);
        for (int i = 0; i < lines.length - 1; i++) {
            String line = lines[i];
            if (line.length() < 67 || !line.substring(0, 64).matches("[0-9a-f]{64}")
                    || !line.startsWith("  ", 64)) throw new IOException("archive_checksum_line_invalid");
            String path = line.substring(66);
            try {
                DataSafePathPolicy.validate(path);
            } catch (IllegalArgumentException invalidPath) {
                throw new IOException("archive_checksum_path_invalid", invalidPath);
            }
            if (CHECKSUMS_ENTRY.equals(path) || hashes.put(path, line.substring(0, 64)) != null)
                throw new IOException("archive_checksum_duplicate_path");
        }
    }

    private static byte[] sha256(byte[] value) throws IOException {
        try {
            return MessageDigest.getInstance("SHA-256").digest(value);
        } catch (NoSuchAlgorithmException impossible) {
            throw new IOException("sha256_unavailable", impossible);
        }
    }

    private static String hex(byte[] value) {
        StringBuilder result = new StringBuilder(value.length * 2);
        for (byte item : value) result.append(String.format(java.util.Locale.ROOT, "%02x", item & 0xff));
        return result.toString();
    }

    private static final class CountingOutputStream extends FilterOutputStream {
        private final long maximum;
        private long count;

        CountingOutputStream(OutputStream output, long maximum) {
            super(output);
            this.maximum = maximum;
        }

        @Override public void write(int value) throws IOException {
            ensureCapacity(1);
            out.write(value);
            count++;
        }

        @Override public void write(byte[] bytes, int offset, int length) throws IOException {
            ensureCapacity(length);
            out.write(bytes, offset, length);
            count += length;
        }

        private void ensureCapacity(int length) throws IOException {
            if (length < 0 || count + length > maximum) throw new IOException("archive_output_size_exceeded");
        }
    }
}
