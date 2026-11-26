package com.vidiftmax.aibridgebrowser;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public class AiBridgeEvidenceTest {
    @Test
    public void acceptsAlternatingTenTurnsWithoutStoringText() {
        AiBridgeEvidence evidence = new AiBridgeEvidence();
        for (int i = 1; i <= 10; i++) {
            String sender = i % 2 == 1 ? "AI-01" : "AI-02";
            assertTrue(evidence.addTurn(i, sender, "response-" + i));
        }
        assertEquals(10, evidence.turnCount());
        assertTrue(evidence.isAlternatingPair());
        assertEquals(10, evidence.events().get(9).responseChars);
    }

    @Test
    public void rejectsEmptyResponseAndWrongSequence() {
        AiBridgeEvidence evidence = new AiBridgeEvidence();
        assertFalse(evidence.addTurn(1, "AI-01", " "));
        assertTrue(evidence.addTurn(1, "AI-01", "ok"));
        assertTrue(evidence.addTurn(2, "AI-01", "wrong"));
        assertFalse(evidence.isAlternatingPair());
    }

    @Test
    public void capsEvidenceEvents() {
        AiBridgeEvidence evidence = new AiBridgeEvidence();
        for (int i = 1; i <= 40; i++) {
            assertTrue(evidence.addTurn(i, i % 2 == 1 ? "AI-01" : "AI-02", "x"));
        }
        assertFalse(evidence.addTurn(41, "AI-01", "x"));
        assertEquals(40, evidence.turnCount());
    }
}
