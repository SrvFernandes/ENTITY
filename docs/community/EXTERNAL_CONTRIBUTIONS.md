# ENTITY External Contribution Ledger

This ledger records attributable work contributed by people or organizations outside Blackmore Technology Group Limited (BTG) control.

It exists to recognize real external participation **without overstating what the participation proves**. An external bug report, documentation improvement, portability result or bounded counterexample is an external contribution; it is not automatically an independent implementation, interoperability result, security audit, certification or endorsement.

## Recorded contributions

| Date | Contributor | Project / target | Contribution | Public evidence | Evidence class | Claim boundary |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-09-27 | [@soyeladice-svg](https://github.com/soyeladice-svg) | ENTITY v3.4.2 economic participation / causal-attribution boundary | Reviewed the immutable v3.4.2 derivative-revenue path and identified a source-level counterexample where one commercial occurrence can be represented under two different valid evidence hashes. Because the current derivative dedupe key includes the evidence hash, the second evidence object can produce a distinct dedupe key even when `policy_id` and `derivative_ref` identify the same underlying occurrence. The report proposed a focused invalid vector requiring one occurrence to accrue at most one economic obligation while allowing multiple evidence objects to remain provenance for that occurrence. | [Issue #28 comment](https://github.com/blackmore-technology-group/ENTITY/issues/28#issuecomment-5852329568), maintainer source review in the same issue | External source-derived counterexample / economic replay-boundary review | BTG confirmed the cited v3.4.2 source structure makes the counterexample legitimate for follow-up qualification. This is **not yet claimed as a runtime reproduction**, independent security audit, whole-protocol validation or endorsement. The immutable v3.4.2 tag is unchanged; remediation and regression evidence belong in a later candidate/release. |
| 2026-09-23 to 2026-09-24 | [@kant2002](https://github.com/kant2002) | ENTITY Protocol 1.0 Conformance Kit | Independently attempted the public developer workflow inside a local `.venv`, identified that kit validation recursively treated virtual-environment packages as prohibited implementation files, and supplied reproducible commands/output. The report led to the v1.0.2 developer-mode fix while preserving strict worktree verification for CI/sealed validation. | [Issue #6](https://github.com/blackmore-technology-group/ENTITY-Protocol-1.0-Conformance-Kit/issues/6), [fix PR #7](https://github.com/blackmore-technology-group/ENTITY-Protocol-1.0-Conformance-Kit/pull/7), main merge `905c309d2461ad192514bfd356527119f134739b` | External defect / developer-workflow / portability report | This is real outside participation and a reproduced defect report. It is **not** claimed as independent protocol conformance, independent interoperability, third-party security validation or endorsement of ENTITY. |

## Why these contributions matter

The Protocol 1.0 kit and the current ENTITY qualification issues are deliberately designed to be exercised by unrelated implementers and reviewers. External participation is most useful when it produces a concrete reproduction, counterexample, portability result or bounded ambiguity that BTG-controlled qualification did not surface in the same way.

The `.venv` report exposed a real developer-workflow defect. The v3.4.2 economic counterexample exposed a distinct occurrence/evidence modeling question: additional evidence for one causal occurrence must not silently become a second economic occurrence.

The correct response is not to dismiss environment differences or weaken qualification targets. It is to preserve the immutable released evidence, record the external finding accurately, and add the appropriate regression or clarification to the next candidate when the finding is reproduced or remediated.

That is the kind of external feedback this project wants: concrete, attributable work that improves the public engineering surface without inflating the claim beyond the evidence.

## What will be recorded here

Future entries may include:

- reproducible external bug reports that materially change the project;
- external portability or environment reproductions;
- merged external pull requests;
- specification ambiguities or counterexamples;
- independently authored benchmarks;
- independently authored clean-room implementations;
- conformance/interoperability results;
- independently authored security-review findings after disclosure requirements are satisfied.

Each entry should identify the **actual evidence class** and its **claim boundary**.

## What will not be inferred

An entry in this ledger does not by itself mean that the contributor:

- endorses ENTITY or BTG;
- works for or represents BTG;
- independently validated the whole protocol;
- completed live interoperability;
- performed a security audit;
- made a legal, regulatory or certification determination.

Those stronger milestones require their own evidence and are tracked separately where appropriate, including the [Interoperability Status](../interoperability/STATUS.md) and [Independent Security Review Program](../security/INDEPENDENT_SECURITY_REVIEW_PROGRAM.md).

## Corrections or attribution preferences

If a contributor wants an attribution corrected, scoped differently or removed from BTG-authored recognition text, open a documentation issue or use an appropriate private company channel where privacy is involved. Underlying public GitHub issue/commit history remains governed by GitHub and the repositories in which that activity occurred.
