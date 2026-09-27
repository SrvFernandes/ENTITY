# ENTITY

[![Release](https://img.shields.io/github/v/release/blackmore-technology-group/ENTITY?sort=semver)](https://github.com/blackmore-technology-group/ENTITY/releases/latest)
[![CI](https://github.com/blackmore-technology-group/ENTITY/actions/workflows/ci.yml/badge.svg)](https://github.com/blackmore-technology-group/ENTITY/actions/workflows/ci.yml)
[![Dependency review](https://github.com/blackmore-technology-group/ENTITY/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/blackmore-technology-group/ENTITY/actions/workflows/dependency-review.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/blackmore-technology-group/ENTITY/badge)](https://securityscorecards.dev/viewer/?uri=github.com/blackmore-technology-group/ENTITY)
[![License](https://img.shields.io/github/license/blackmore-technology-group/ENTITY)](LICENSE)

**Open infrastructure for sovereign digital authority, verifiable claims, data rights, continuous provenance and economic state that survives providers.**

> **Run it. Verify it. Break it. Implement it independently.**

ENTITY is Blackmore Technology Group's open-source protocol and reference implementation for persistent identity, delegated authority, provenance, evidence, rights, trusted state transitions, portable recovery and data-economic infrastructure.

[**ENTITY v3.4.3 Release**](https://github.com/blackmore-technology-group/ENTITY/releases/tag/v3.4.3) · [**External Qualification**](https://github.com/blackmore-technology-group/ENTITY/issues/55) · [**ERQ Campaign**](https://github.com/blackmore-technology-group/ENTITY/issues/78) · [**Documentation**](https://blackmore-technology-group.github.io/ENTITY-DOCS/) · [**Conformance Kit**](https://github.com/blackmore-technology-group/ENTITY-Protocol-1.0-Conformance-Kit) · [**Interoperability Challenge**](docs/INTEROPERABILITY_CHALLENGE.md)

---

## ENTITY v3.4.3 — current supported release

**ENTITY v3.4.3 is the current supported ENTITY runtime.** It is a bounded remediation release based on the immutable v3.4.2 release. The **BTDU component remains version 3.4.2 unchanged**. v3.4.2 remains immutable historical evidence and is superseded for current deployment.

v3.4.3 remediates two reproduced Issue #28 defects:

1. derivative-revenue evidence substitution could create a second economic event and obligation for the same occurrence;
2. a zero-edge causal graph could return a positive self-trace for missing or empty endpoints and label an empty path evidence-bound.

The remediation keeps authoritative occurrence identity separate from evidence identity, rejects exact replay, records additional evidence without creating a duplicate obligation, and validates causal-trace endpoints before traversal.

### v3.4.3 qualification

| Evidence | Result |
| --- | --- |
| Issue #28 remediation module | **76/76 PASS** |
| Full repository source suite | **279/279 PASS** |
| Full source-suite exit code | **0** |
| Compiled Rust qualification | **PASS — inherited unchanged scope** |
| Real-world BTDU training qualification | **PASS — inherited unchanged scope** |

Release merge commit: `528b70aabd05b1e930b77e4933f157731e47274f`  
Immutable predecessor commit: `6dfa3d6cc738d9369cf092d2782676bf4f2a46e4`

The v3.4.3 release does **not** rewrite the active 30-day wall-clock evidence campaign or immutable v3.4.2 evidence.

---

## Canonical origin and claim boundary

Canonical ENTITY origin remains:

```text
Shawn Blackmore → Blackmore Technology Group → ENTITY
```

Protocol origin is separate from downstream asset ownership, custody and economic entitlement.

```text
UPSTREAM OWNERSHIP
        ≠
BTG FORK CUSTODY
        ≠
BTG ENTITY METADATA OWNERSHIP
        ≠
ENTITY PROTOCOL ORIGIN
        ≠
AUTOMATIC ECONOMIC RIGHTS
```

ENTITY may record provenance, authorship, copyright, licence, custody, rights metadata and governed relationships. Registration, mirroring, ingestion, verification or custody do not themselves transfer upstream ownership or create automatic economic entitlement.

---

## Blackmore Technology Data Universe

BTDU remains **component version 3.4.2** in ENTITY v3.4.3. It provides an atomic/bonded information architecture in which reusable atoms, bonds and compounds can be connected to ENTITY provenance, authority, rights and economic state.

```text
Atoms → Bonds → Compounds → Governed Objects → Provenance / Rights / Economic Lineage
```

BTDU is not presented as generic raw-file compression. It is a representation model for structured, semantic and relational information with explicit provenance and rights boundaries.

Historical v3.4.2 + BTDU documentation remains available at the [v3.4.2 documentation archive](https://blackmore-technology-group.github.io/ENTITY-DOCS/v342/).

---

## Data-rights economic architecture

ENTITY models explicit rights around data rather than requiring artificial scarcity in the bytes themselves.

```text
DCO
 ↓
Instrument
 ↓
Listing
 ↓
Disclosure
 ↓
Order / RFQ / Auction
 ↓
Price Discovery
 ↓
Trade
 ↓
Clearing
 ↓
Settlement
 ↓
Entitlement
 ↓
Usage
 ↓
Derived Output
 ↓
Economic Consequence
```

Originator participation may be expressed through explicit terms such as issuance participation, retained rights, secondary participation or derivative participation. ENTITY does not require a cryptocurrency, gas token or automatic BTG tax.

---

## Quick start

Python 3.11+ is recommended for the reference implementation.

```bash
git clone https://github.com/blackmore-technology-group/ENTITY.git
cd ENTITY
git checkout v3.4.3
python -m pip install -r requirements.txt
python -m compileall -q src sdk protocol
python -m unittest discover -s tests -v
```

Then choose a narrow path:

- [External Verification Challenge](https://github.com/blackmore-technology-group/ENTITY/issues/55)
- [External Repository Qualification campaign](https://github.com/blackmore-technology-group/ENTITY/issues/78)
- [Reproduce the published Rust baseline](https://github.com/blackmore-technology-group/ENTITY/issues/48)
- [Attempt an independent implementation](docs/INTEROPERABILITY_CHALLENGE.md)
- [Read the Protocol 1.0 Conformance Kit](https://github.com/blackmore-technology-group/ENTITY-Protocol-1.0-Conformance-Kit)

A reproducible failure, ambiguity, counterexample or portability problem is useful evidence.

---

## Public cross-language baselines

BTG publishes controlled reproducibility baselines in:

- [Rust](https://github.com/blackmore-technology-group/ENTITY-RUST-CLEANROOM)
- [TypeScript](https://github.com/blackmore-technology-group/ENTITY-TYPESCRIPT-CLEANROOM)
- [C# / .NET](https://github.com/blackmore-technology-group/ENTITY-CSHARP-CLEANROOM)
- [Go](https://github.com/blackmore-technology-group/ENTITY-GO-CLEANROOM)
- [Swift](https://github.com/blackmore-technology-group/ENTITY-SWIFT-CLEANROOM)
- [Java](https://github.com/blackmore-technology-group/ENTITY-JAVA-CLEANROOM)

Some of these repositories deliberately reproduce sealed **v3.4.2** campaigns. Those version labels are historical test-target identifiers and should not be read as statements that v3.4.2 remains the current runtime.

These repositories are **BTG-controlled reproducibility baselines, not independent third-party implementations**. External reproduction of a baseline is meaningful portability/reproducibility evidence, but the stronger milestone remains an implementation independently authored and controlled by an unrelated engineer or organization from the public protocol/specification material.

---

## External qualification status

ENTITY separates BTG-controlled qualification from evidence that should come from unrelated participants.

Current entry points:

- [#55 — External Verification Challenge](https://github.com/blackmore-technology-group/ENTITY/issues/55)
- [#78 — External Repository Qualification campaign](https://github.com/blackmore-technology-group/ENTITY/issues/78)

Historical issues #58–#62 were created against the frozen v3.4.2 target. Their evidence scope remains v3.4.2 unless an issue explicitly states that it has been retargeted to v3.4.3. Historical hashes, tags and receipts are not rewritten simply because the supported runtime advanced.

The active 30-day wall-clock qualification remains time-dependent and was not reset or modified by v3.4.3.

---

## Domain entry points

The same ENTITY sovereignty model is packaged for:

- [Healthcare](https://github.com/blackmore-technology-group/ENTITY-HEALTHCARE)
- [Finance](https://github.com/blackmore-technology-group/ENTITY-FINANCE)
- [Manufacturing](https://github.com/blackmore-technology-group/ENTITY-MANUFACTURING)
- [AI](https://github.com/blackmore-technology-group/ENTITY-AI)
- [Robotics](https://github.com/blackmore-technology-group/ENTITY-ROBOTICS)
- [Defence / Public-Unclassified](https://github.com/blackmore-technology-group/ENTITY-DEFENCE)

The packages configure one ENTITY sovereignty model; they do not create separate sovereignty systems or redefine external standards.

---

## Core invariants

- Identity is not an account.
- Registration is not ownership.
- Provenance is not truth.
- A valid signature is not proof that an external-world assertion is correct.
- Possession, hosting, routing, custody and storage do not create sovereign authority.
- Applications and agents act only through explicit, scoped, revocable authority.
- Data bytes do not require artificial scarcity; scarcity can exist in rights, entitlements, capacity, duration, jurisdiction, usage quantity, derivation and participation.
- Usage does not become realized economic value without the required evidence.
- Historical signed semantics are superseded, not silently rewritten.
- An ENTITY identity is intended to survive replacement of a device, host, provider or BTG infrastructure subject to the applicable recovery/qualification evidence.

---

## Security boundary

**Never commit operational sovereignty state to this repository.**

Do not commit private signing/recovery keys, live credentials, principal/device/application binding instances, `.entitybackup` files, runtime databases, production state directories or unredacted user/business data.

See [SECURITY.md](SECURITY.md).

---

## Documentation and governance

- [ENTITY v3.4.3 release](https://github.com/blackmore-technology-group/ENTITY/releases/tag/v3.4.3)
- [Documentation portal](https://blackmore-technology-group.github.io/ENTITY-DOCS/)
- [Historical v3.4.2 + BTDU documentation](https://blackmore-technology-group.github.io/ENTITY-DOCS/v342/)
- [External Verification Challenge](https://github.com/blackmore-technology-group/ENTITY/issues/55)
- [ERQ campaign](https://github.com/blackmore-technology-group/ENTITY/issues/78)
- [Engineering evidence](docs/ENGINEERING_EVIDENCE.md)
- [Interoperability challenge](docs/INTEROPERABILITY_CHALLENGE.md)
- [Governance](GOVERNANCE.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Citation metadata](CITATION.cff)
- [CodeMeta](codemeta.json)
- [All releases](https://github.com/blackmore-technology-group/ENTITY/releases)

ENTITY is published under the Apache License 2.0.
