# C2ATrace v0.1 Conformance Suite

Status: IN PROGRESS.

This directory defines the language-neutral conformance harness for the frozen C2ATrace v0.1 protocol.

The suite separates four responsibilities:

- direct_schema — local wire-shape rules checked only by JSON Schema;
- mixed_schema_semantic — Schema constrains local shape and semantic verifier checks complete the requirement;
- semantic_verifier — cross-object, graph, evidence, conflict, completeness, causality, or reporting rule;
- deterministic_vector — canonicalization, digest, signature, keyed commitment, or other algorithmic rule with reproducible vectors.

Every numbered requirement receives a unique case ID derived from both requirement ID and planned-test ID. Duplicate planned-test names therefore never merge requirements.

Cases use deterministic input documents plus optional add/remove/replace JSON-Pointer patches. Expected results are language-neutral normative matchers; free-text messages and implementation-generated finding IDs are not golden data.

A case is not counted as accepted until its input, execution phases, expected result, and requirement mapping are all executable and independently checked.

## Semantic primitive layer

The 771 `semantic_verifier` requirements are organized through reusable scenario primitives rather than 771 isolated hand-written harnesses.

Source of truth:

- `primitives/manifest.json` — 21 primitive families plus primitive → requirement coverage;
- `primitives/coverage-matrix.json` — 771/771 semantic requirements with exactly one primary primitive and optional dependency primitives;
- `primitives/receipts/` — materialized reusable Receipt scenarios;
- `expected/semantic/` — normalized expected-result documents for semantic cases.

Primitive Waves 01-05E materialize the reference/graph foundation plus complete Source, Derivation, Request, ProviderAttempt, ModelOutput, ToolLifecycle, occurrence identity, Trust, Taint, privacy commitment/redaction, multi-Receipt, Integrity, claim-strength, and ordering/time primary primitive families, plus the current Provider Adapter tranche. Semantic-verifier executability is **533 / 771**, with **238** remaining (`PAD 20 / TAD 90 / VFY 128`). Primitive names are test infrastructure only; they do not change frozen protocol semantics or wire format.
