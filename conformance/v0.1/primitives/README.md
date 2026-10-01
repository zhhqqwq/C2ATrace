# C2ATrace v0.1 Semantic Verifier Primitives

This directory is the reusable semantic-scenario layer for the 771 `semantic_verifier` requirements.

## Assignment model

Every semantic requirement has:

- exactly one **primary primitive**: the scenario family that owns its main verifier behavior;
- zero or more **dependency primitives**: other scenario capabilities needed to execute or interpret the case.

The machine-readable source of truth is:

- `manifest.json` — primitive catalog and primitive → requirement coverage;
- `coverage-matrix.json` — one row per semantic requirement with primary/dependency primitive assignments.

## Primitive families

The catalog intentionally separates:

- local vs external reference resolution;
- reference failure modes from ReceiptLink/pin semantics;
- core graph invariants from occurrence identity;
- derivation mapping from request binding;
- provider attempts from model output;
- tool lifecycle from trust/taint/privacy;
- integrity verification from claim-strength wording;
- adapter capture from verifier reporting;
- ordering/time from causal claims.

## Materialization rule

A semantic case may reuse an existing public fixture or a materialized primitive Receipt. Cases SHOULD record the primitive IDs they exercise in `notes`, while normative acceptance continues to compare typed expected findings rather than primitive names.

Wave 01 initially materializes the reference/graph/identity foundation primitives. Later waves add reusable request, provider, tool, trust/taint, privacy, multi-Receipt, integrity, claim, adapter, verifier, and ordering scenarios.

Primitive classification is planning/execution infrastructure. It does not change frozen v0.1 protocol semantics or JSON Schema.
