package com.vidiftmax.aibridgebrowser;

import java.io.File;
import java.io.IOException;

/** Restricts installer handoff to the one verified APK in the private updater directory. */
public final class UpdateInstallPolicy {
    private UpdateInstallPolicy() {}

    public static boolean isSameApplicationIdentity(String installedPackage, String incomingPackage,
            boolean signingCertificateMatches) {
        return installedPackage != null && !installedPackage.isEmpty()
                && installedPackage.equals(incomingPackage) && signingCertificateMatches;
    }

    public static boolean isEligibleCandidate(File candidate, File verifiedCandidate,
            File allowedDirectory, String expectedName) throws IOException {
        if (candidate == null || verifiedCandidate == null || allowedDirectory == null
                || expectedName == null || expectedName.trim().isEmpty()) return false;
        File canonicalCandidate = candidate.getCanonicalFile();
        File canonicalVerified = verifiedCandidate.getCanonicalFile();
        File canonicalDirectory = allowedDirectory.getCanonicalFile();
        return canonicalCandidate.isFile()
                && canonicalCandidate.length() > 0
                && canonicalCandidate.equals(canonicalVerified)
                && canonicalDirectory.equals(canonicalCandidate.getParentFile())
                && expectedName.equals(canonicalCandidate.getName());
    }

    /** Rebinds the staged APK's on-disk byte length to the official Release asset before installer handoff. */
    public static boolean isExpectedVerifiedApk(File candidate, File verifiedCandidate,
            File allowedDirectory, String expectedName, long expectedBytes, long maximumBytes)
            throws IOException {
        if (expectedBytes <= 0 || maximumBytes <= 0 || expectedBytes > maximumBytes) return false;
        return isEligibleCandidate(candidate, verifiedCandidate, allowedDirectory, expectedName)
                && candidate.length() == expectedBytes
                && candidate.length() <= maximumBytes;
    }
}
