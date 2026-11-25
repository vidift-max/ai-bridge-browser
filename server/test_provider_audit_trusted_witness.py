import unittest

from server.provider_audit_trusted_witness import (
    ProviderAuditTrustedWitness,
    replicate_trusted_head,
    verify_trusted_head_quorum,
)


HEAD = {"sequence": 1, "record_digest": "a" * 64,
        "checkpoint_audit_id": 10}
GENESIS = {"sequence": 0, "record_digest": "0" * 64,
           "checkpoint_audit_id": -1}


class FakeWitness:
    def __init__(self, latest=None, failure=None):
        self.latest = latest
        self.failure = failure
        self.writes = 0

    def read_latest(self):
        if self.failure == "read":
            raise OSError("unavailable")
        if self.failure == "timeout":
            raise TimeoutError("deadline")
        if self.failure == "unauthorized":
            raise PermissionError("denied")
        return self.latest

    def record_head(self, head):
        self.writes += 1
        if self.failure == "write":
            raise OSError("write unavailable")
        if self.failure == "timeout":
            raise TimeoutError("deadline")
        if self.failure == "bad_ack":
            return {"recorded": True, "replayed": False, "head": GENESIS}
        if self.latest == head:
            return {"recorded": False, "replayed": True, "head": head}
        if self.latest is not None and (
                head["sequence"] <= self.latest["sequence"]
                or head["checkpoint_audit_id"] <= self.latest["checkpoint_audit_id"]):
            raise ValueError("rollback")
        self.latest = dict(head)
        return {"recorded": True, "replayed": False, "head": head}


class TrustedWitnessReplicationTests(unittest.TestCase):
    def test_fake_satisfies_structural_protocol(self):
        self.assertIsInstance(FakeWitness(), ProviderAuditTrustedWitness)

    def test_write_quorum_reached(self):
        witnesses = [FakeWitness(), FakeWitness(), FakeWitness()]
        result = replicate_trusted_head(witnesses, HEAD, 2)
        self.assertTrue(result["replicated"])
        self.assertEqual(len(result["acknowledgements"]), 3)

    def test_unavailable_witness_fails_closed_below_quorum(self):
        witnesses = [FakeWitness(failure="read"), FakeWitness(failure="timeout"),
                     FakeWitness(failure="unauthorized")]
        result = replicate_trusted_head(witnesses, HEAD, 2)
        self.assertFalse(result["replicated"])
        self.assertEqual(result["acknowledgements"], [])

    def test_partial_commit_is_explicit_and_retry_completes(self):
        witnesses = [FakeWitness(), FakeWitness(failure="write"),
                     FakeWitness(failure="timeout")]
        first = replicate_trusted_head(witnesses, HEAD, 2)
        self.assertFalse(first["replicated"])
        self.assertTrue(first["partial_commit_possible"])
        witnesses[1].failure = None
        witnesses[2].failure = None
        second = replicate_trusted_head(witnesses, HEAD, 2)
        self.assertTrue(second["replicated"])
        self.assertTrue(witnesses[0].latest == HEAD)

    def test_exact_replay_is_idempotent(self):
        witnesses = [FakeWitness(HEAD), FakeWitness(HEAD)]
        result = replicate_trusted_head(witnesses, HEAD, 2)
        self.assertTrue(result["replicated"])
        self.assertEqual([w.writes for w in witnesses], [0, 0])

    def test_bad_ack_does_not_count(self):
        result = replicate_trusted_head(
            [FakeWitness(failure="bad_ack"), FakeWitness()], HEAD, 2)
        self.assertFalse(result["replicated"])

    def test_rollback_and_same_sequence_fork_rejected(self):
        older = {"sequence": 2, "record_digest": "b" * 64,
                 "checkpoint_audit_id": 20}
        fork = {"sequence": 1, "record_digest": "c" * 64,
                "checkpoint_audit_id": 11}
        for existing in (older, fork):
            witness = FakeWitness(existing)
            result = replicate_trusted_head([witness], HEAD, 1)
            self.assertFalse(result["replicated"])
            self.assertEqual(witness.latest, existing)

    def test_read_quorum_requires_exact_head(self):
        result = verify_trusted_head_quorum(
            [FakeWitness(HEAD), FakeWitness(HEAD), FakeWitness(GENESIS)],
            HEAD, 2)
        self.assertTrue(result["valid"])
        self.assertEqual(result["stale"], [2])

    def test_read_quorum_unavailable_fails_closed(self):
        result = verify_trusted_head_quorum(
            [FakeWitness(failure="timeout"), FakeWitness(GENESIS),
             FakeWitness(failure="unauthorized")], HEAD, 2)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "trusted_witness_quorum_unavailable")

    def test_any_observed_fork_fails_closed_even_with_matching_quorum(self):
        fork = {"sequence": 1, "record_digest": "f" * 64,
                "checkpoint_audit_id": 11}
        result = verify_trusted_head_quorum(
            [FakeWitness(HEAD), FakeWitness(HEAD), FakeWitness(fork)],
            HEAD, 2)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "trusted_witness_conflict")

    def test_malformed_witness_response_is_not_accepted(self):
        result = verify_trusted_head_quorum(
            [FakeWitness({"sequence": True, "record_digest": "a" * 64,
                          "checkpoint_audit_id": 10})], HEAD, 1)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "trusted_witness_quorum_unavailable")

    def test_invalid_quorum_and_duplicate_adapter_rejected(self):
        witness = FakeWitness()
        with self.assertRaisesRegex(ValueError, "trusted_witness_quorum_invalid"):
            replicate_trusted_head([witness], HEAD, 2)
        with self.assertRaisesRegex(ValueError, "trusted_witness_duplicate_adapter"):
            replicate_trusted_head([witness, witness], HEAD, 1)


if __name__ == "__main__":
    unittest.main()
