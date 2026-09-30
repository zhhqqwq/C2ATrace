# C2ATrace Specification

Status: pre-schema specification work.

## Current documents

- PHASE-0-FOUNDATIONS.md — reviewed Phase 0 baseline, object taxonomy, relation semantics, graph invariants, and open design gates.
- PHASE-1-PART-A-SOURCE-SEMANTICS.md — accepted SourceRef / SourceObservation semantics after adversarial review.
- PHASE-1-PART-B-TRANSFORM-DERIVATION.md — accepted Transform / Derivation semantics, Region lineage, and control-vs-content separation after adversarial review.
- PHASE-1-PART-C-REQUEST-SEMANTICS.md — accepted RequestSnapshot / RequestBinding semantics, capture levels, request locations, digest semantics, and hash-only verification boundaries after adversarial review.
- THREAT-MODEL.md — trust boundaries, adversary assumptions, and numbered normative threat requirements.
- CLAIMS.md — composable evidence-basis model and numbered verifier-reporting requirements.
- TERMINOLOGY.md — shared definitional vocabulary, now aligned through Phase 1 Part C.

## Project gate

JSON Schema remains unfrozen. Phase 1 Parts A, B, and C are complete.

The next semantic focus is ModelInvocation / ProviderAttempt / ModelOutput behavior, followed by tool/effect, trust/taint, privacy, integrity/receipt, adapter, and verifier contracts. These gates remain before Schema freeze.

## Normative language discipline

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are protocol-normative only inside numbered normative requirements or definitions that explicitly cite those requirements.

Every numbered MUST / MUST NOT requirement is paired with a planned conformance test identifier before Schema freeze.
