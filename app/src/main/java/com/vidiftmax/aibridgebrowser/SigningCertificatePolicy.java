package com.vidiftmax.aibridgebrowser;

/** Conservative exact-match policy for installed and incoming APK signer sets. */
public final class SigningCertificatePolicy {
    private SigningCertificatePolicy() {}

    public static boolean areSameSignerSets(byte[][] installed, byte[][] incoming) {
        if (installed == null || incoming == null || installed.length == 0
                || installed.length != incoming.length) {
            return false;
        }
        boolean[] matchedIncoming = new boolean[incoming.length];
        for (byte[] installedSigner : installed) {
            if (installedSigner == null || installedSigner.length == 0) return false;
            boolean found = false;
            for (int i = 0; i < incoming.length; i++) {
                byte[] incomingSigner = incoming[i];
                if (!matchedIncoming[i] && incomingSigner != null
                        && incomingSigner.length > 0 && equals(installedSigner, incomingSigner)) {
                    matchedIncoming[i] = true;
                    found = true;
                    break;
                }
            }
            if (!found) return false;
        }
        return true;
    }

    private static boolean equals(byte[] left, byte[] right) {
        if (left.length != right.length) return false;
        int difference = 0;
        for (int i = 0; i < left.length; i++) difference |= left[i] ^ right[i];
        return difference == 0;
    }
}
