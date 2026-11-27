package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public class SigningCertificatePolicyTest {
    @Test public void acceptsOneExactSigner() {
        assertTrue(SigningCertificatePolicy.areSameSignerSets(
                new byte[][]{{1, 2, 3}}, new byte[][]{{1, 2, 3}}));
    }

    @Test public void acceptsSameSignerSetRegardlessOfOrder() {
        assertTrue(SigningCertificatePolicy.areSameSignerSets(
                new byte[][]{{1}, {2}}, new byte[][]{{2}, {1}}));
    }

    @Test public void rejectsDifferentSignerBytes() {
        assertFalse(SigningCertificatePolicy.areSameSignerSets(
                new byte[][]{{1, 2}}, new byte[][]{{1, 3}}));
    }

    @Test public void rejectsMissingOrAdditionalSigners() {
        assertFalse(SigningCertificatePolicy.areSameSignerSets(
                new byte[][]{{1}}, new byte[][]{{1}, {2}}));
        assertFalse(SigningCertificatePolicy.areSameSignerSets(
                new byte[][]{{1}, {2}}, new byte[][]{{1}}));
    }

    @Test public void rejectsNullOrEmptySignerSetsAndEntries() {
        assertFalse(SigningCertificatePolicy.areSameSignerSets(null, new byte[][]{{1}}));
        assertFalse(SigningCertificatePolicy.areSameSignerSets(new byte[0][], new byte[][]{{1}}));
        assertFalse(SigningCertificatePolicy.areSameSignerSets(new byte[][]{{1}}, null));
        assertFalse(SigningCertificatePolicy.areSameSignerSets(new byte[][]{{1}}, new byte[0][]));
        assertFalse(SigningCertificatePolicy.areSameSignerSets(new byte[][]{null}, new byte[][]{{1}}));
        assertFalse(SigningCertificatePolicy.areSameSignerSets(new byte[][]{{1}}, new byte[][]{{}}));
    }

    @Test public void matchesDuplicateEntriesOneToOne() {
        assertTrue(SigningCertificatePolicy.areSameSignerSets(
                new byte[][]{{7}, {7}}, new byte[][]{{7}, {7}}));
        assertFalse(SigningCertificatePolicy.areSameSignerSets(
                new byte[][]{{7}, {7}}, new byte[][]{{7}, {8}}));
    }
}
