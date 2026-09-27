from __future__ import annotations

import hashlib
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from test_v3_economic_participation import EconomicParticipationTests, econ_mod
from test_v3_verifiable_reality import V33VerifiableRealityTests


class Issue28EconomicRegression(EconomicParticipationTests):
    def test_issue_28_evidence_substitution_does_not_double_accrue(self):
        occurred = econ_mod.now_ms()
        derivative_ref = "occurrence:issue-28-001"
        evidence_a = hashlib.sha256(b"issue28 original evidence").hexdigest()
        evidence_b = hashlib.sha256(b"issue28 enriched evidence same occurrence").hexdigest()

        self.profile.record_derivative_revenue(
            self.policy["policy_id"],
            self.buyer1,
            derivative_ref,
            100000,
            "CAD",
            evidence_a,
            occurred_at_ms=occurred,
        )

        with self.assertRaises(ValueError):
            self.profile.record_derivative_revenue(
                self.policy["policy_id"],
                self.buyer1,
                derivative_ref,
                100000,
                "CAD",
                evidence_a,
                occurred_at_ms=occurred,
            )

        try:
            self.profile.record_derivative_revenue(
                self.policy["policy_id"],
                self.buyer1,
                derivative_ref,
                100000,
                "CAD",
                evidence_b,
                occurred_at_ms=occurred,
            )
        except ValueError:
            pass

        total = self.profile.position(
            self.treasury["treasury_id"], self.exchange
        )["monetary_obligations"]["CAD"]["ACCRUED"]
        self.assertEqual(total, 1000)



    def test_issue_28_evidence_enrichment_reuses_same_occurrence(self):
        occurred = econ_mod.now_ms()
        derivative_ref = "derivative:issue28-enrichment"
        occurrence_ref = "revenue-occurrence:issue28:001"
        evidence_a = hashlib.sha256(b"issue28 evidence A").hexdigest()
        evidence_b = hashlib.sha256(b"issue28 evidence B").hexdigest()

        first = self.profile.record_derivative_revenue(
            self.policy["policy_id"], self.buyer1, derivative_ref, 100000, "CAD", evidence_a,
            occurred_at_ms=occurred, occurrence_ref=occurrence_ref,
        )
        second = self.profile.record_derivative_revenue(
            self.policy["policy_id"], self.buyer1, derivative_ref, 100000, "CAD", evidence_b,
            occurred_at_ms=occurred, occurrence_ref=occurrence_ref,
        )

        self.assertEqual(second["event"]["event_id"], first["event"]["event_id"])
        self.assertEqual(second["obligation"]["obligation_id"], first["obligation"]["obligation_id"])
        total = self.profile.position(
            self.treasury["treasury_id"], self.exchange
        )["monetary_obligations"]["CAD"]["ACCRUED"]
        self.assertEqual(total, 1000)

    def test_issue_28_distinct_authoritative_occurrences_can_both_accrue(self):
        occurred = econ_mod.now_ms()
        derivative_ref = "derivative:issue28-repeat"
        evidence_a = hashlib.sha256(b"issue28 occurrence A").hexdigest()
        evidence_b = hashlib.sha256(b"issue28 occurrence B").hexdigest()

        first = self.profile.record_derivative_revenue(
            self.policy["policy_id"], self.buyer1, derivative_ref, 100000, "CAD", evidence_a,
            occurred_at_ms=occurred, occurrence_ref="revenue-occurrence:issue28:A",
        )
        second = self.profile.record_derivative_revenue(
            self.policy["policy_id"], self.buyer1, derivative_ref, 100000, "CAD", evidence_b,
            occurred_at_ms=occurred, occurrence_ref="revenue-occurrence:issue28:B",
        )

        self.assertNotEqual(second["event"]["event_id"], first["event"]["event_id"])
        total = self.profile.position(
            self.treasury["treasury_id"], self.exchange
        )["monetary_obligations"]["CAD"]["ACCRUED"]
        self.assertEqual(total, 2000)

class Issue28CausalRegression(V33VerifiableRealityTests):
    def test_issue_28_trace_fails_closed_and_self_trace_is_not_evidence_bound(self):
        node = self.causal.add_node(
            self.owner,
            "SOURCE_DATA",
            "issue28:source",
            evidence_refs=["issue28:origin"],
        )

        for source, target in (
            ("missing:source", node["node_id"]),
            (node["node_id"], "missing:target"),
            ("missing:same", "missing:same"),
            ("", ""),
        ):
            result = self.causal.trace(source, target)
            self.assertFalse(result["connected"])
            self.assertFalse(result["causal_chain_is_evidence_bound"])

        self_trace = self.causal.trace(node["node_id"], node["node_id"])
        self.assertTrue(self_trace["connected"])
        self.assertEqual(self_trace["path"], [])
        self.assertFalse(self_trace["causal_chain_is_evidence_bound"])


if __name__ == "__main__":
    unittest.main()
