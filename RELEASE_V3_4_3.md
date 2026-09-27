# ENTITY v3.4.3

ENTITY v3.4.3 is a bounded remediation release based on immutable v3.4.2 commit
`6dfa3d6cc738d9369cf092d2782676bf4f2a46e4`.

## Scope

This release addresses the two reproduced findings tracked in GitHub issue #28:

1. Derivative-revenue evidence substitution could create a second economic event and obligation for the same occurrence.
2. A zero-edge causal graph could return a positive self-trace for missing or empty endpoints and label an empty path evidence-bound.

## Remediation

Derivative revenue now distinguishes authoritative occurrence identity from evidence identity. Exact replay is rejected. New evidence for the same occurrence is recorded as additional provenance without creating another obligation. Distinct authoritative `occurrence_ref` values can represent distinct revenue occurrences.

Causal tracing now validates both endpoints before traversal. Missing or empty endpoints fail closed. Existing-node self reachability may remain topologically connected, but an empty path is not treated as evidence-bound causation.

## Qualification

- Issue #28 final remediation module: **76/76 PASS**
- Full repository source suite: **279/279 PASS**
- Full source-suite exit code: **0**

## Version boundary

- ENTITY release: **3.4.3**
- BTDU component: **3.4.2** (unchanged)
- v3.4.2 remains immutable historical evidence.
- Production state and the active 30-day wall-clock qualification were not modified.

## Claim boundary

This release is limited to the two reproduced Issue #28 defects. It does not establish external settlement, payment, legal-entitlement, fair-value, or broader economic-causality claims beyond the qualified behavior above.

## Inherited unchanged-scope qualification

The following previously closed v3.4.2 qualification evidence is carried forward because v3.4.3 does not modify the qualified components or paths:

- **Compiled Rust clean-room/conformance qualification:** PASS (inherited unchanged scope)
  - Evidence SHA-256: `96a7b5175dc11e1d881a9a1aa53c3496dac93d182d7072e71ad4982921571754`
- **Real-world BTDU training qualification:** PASS (inherited unchanged scope)
  - Evidence SHA-256: `4d31bc1a3ae8c8ff6dcf096b304914808e27cc60595510cc7088b5af021931ff`

These are inherited qualification records, not re-executed v3.4.3 test runs.
