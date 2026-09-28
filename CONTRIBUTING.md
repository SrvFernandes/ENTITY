# Contributing to ENTITY

Contributions are welcome where they preserve ENTITY's published authority, evidence and claim boundaries.

You do **not** need to understand the entire system before contributing. Small, reproducible improvements are useful: documentation corrections, portability reports, schema ambiguity reviews, failing vectors, examples, tests, benchmarks and narrowly scoped implementation work.

Start with [START_HERE.md](START_HERE.md). For clean-room implementation work, also read [docs/INTEROPERABILITY_CHALLENGE.md](docs/INTEROPERABILITY_CHALLENGE.md).

## Before opening a pull request

1. Read the relevant public protocol/profile material for the area you are changing.
2. Keep authoritative state separate from adapters, user interfaces and provider infrastructure.
3. Preserve historical interpretation of already-signed records.
4. Add or update tests for behavior changes.
5. Run:

```bash
python -m compileall -q src sdk protocol
python -m unittest discover -s tests -v
```

If the proposed change is large or touches protocol semantics, opening an issue/discussion first is encouraged. That is coordination, not a request for permission to explore the problem.

## Required design discipline

Changes must not silently turn:

- registration into ownership;
- provenance into truth;
- a valid signature into objective external truth;
- custody, hosting or resolution into sovereign authority;
- an external evidence source into ENTITY authority;
- application events into protected rights/economic authority;
- usage into realized value without required evidence;
- aliases into cryptographic identity;
- a disputed historical claim into deleted history.

## v3.4 evidence, passport and profile discipline

v3.4 inherits the v3.3 verification boundaries. For Global Passport/profile work, keep these distinct:

- **cryptographic verification** — signature/commitment integrity;
- **protocol verification** — valid ENTITY semantics/state transition;
- **reality/evidence verification** — attributed evidence supporting an external-world claim.

Code or documentation that collapses these layers should be treated as a semantic defect. Profile composition must not create authority; external standards must be mapped rather than redefined; and industry packages must not create separate sovereignty silos.

## Protocol changes

ENTITY Protocol 1.0 is frozen for its external conformance campaign. Security-critical or semantic changes to frozen behavior require an erratum or a new protocol version.

Later ENTITY versions may add profiles/layers, but historical signed records must remain interpretable under the semantics that applied when they were created.

## Pull request description

Please identify, where applicable:

- requirement/profile addressed;
- authority or truth boundary affected;
- implementation change;
- test/evidence added;
- compatibility impact;
- whether the change is protocol-semantic or implementation-only;
- whether any public conformance vector/kit needs to change.

A concise PR with a clear reproduction/test path is preferable to a large narrative.

## Independent implementations

Independent clean-room implementations should live in repositories controlled by the independent implementer. BTG can clarify published specifications and vector intent, but should not author an implementation that is later presented as independent evidence.

If you are considering a full implementation, you are welcome to begin with only a subset or a design discussion. Your architecture, libraries, repository layout and internal implementation choices remain yours.

## Security and private state

Do not include production state, credentials, private bindings, recovery keys, real user/business data or private signer material in issues, pull requests or test fixtures.

For security-sensitive reports, follow [SECURITY.md](SECURITY.md).

## Project conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

Critical, reproducible feedback is welcome. Finding an ambiguity, an incorrect assumption or a failing edge case is a contribution to the protocol.
