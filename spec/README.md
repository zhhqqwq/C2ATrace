# C2ATrace Specification

Status: pre-schema specification work.

## Current documents

- PHASE-0-FOUNDATIONS.md — reviewed Phase 0 baseline, object taxonomy, relation semantics, graph invariants, and open design gates.
- PHASE-1-PART-A-SOURCE-SEMANTICS.md — accepted SourceRef / SourceObservation semantics after adversarial review.
- PHASE-1-PART-B-TRANSFORM-DERIVATION.md — accepted Transform / Derivation semantics, Region lineage, and control-vs-content separation after adversarial review.
- THREAT-MODEL.md — trust boundaries, adversary assumptions, and numbered normative threat requirements.
- CLAIMS.md — composable evidence-basis model and numbered verifier-reporting requirements.
- TERMINOLOGY.md — shared definitional vocabulary, now aligned through Phase 1 Part B.

## Project gate

JSON Schema remains unfrozen. Phase 1 Parts A and B are complete; the current specification focus is Part C: RequestSnapshot / RequestBinding semantics.

Part C must be completed and adversarially reviewed before Schema freeze.

## Normative language discipline

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are protocol-normative only inside numbered normative requirements or definitions that explicitly cite those requirements.

Every numbered MUST / MUST NOT requirement is paired with a planned conformance test identifier before Schema freeze.
