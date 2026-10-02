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

## Wave 01 status

- catalogued semantic requirements: 771 / 771
- primitive families: 21
- executable semantic cases: 21 / 771
- remaining semantic cases: 750
- materialized foundation primitives: local reference, external reference, reference failures, graph invariants, occurrence identity

The first materialized Receipt primitives live under `receipts/` and are shared by multiple cases.

## Wave 02 status

- executable semantic cases: 96 / 771
- remaining semantic cases: 675
- fully materialized primary primitive families:
  - `prim.source.observation` — 18 / 18
  - `prim.derivation.mapping` — 23 / 23
  - `prim.request.binding` — 34 / 34
- reusable primitive Receipts: 77
- normalized semantic expected results: 96

Wave 02 uses shared primitive Receipts plus case-level normative matchers. It does not change frozen protocol semantics or JSON Schema.

## Wave 03 status

- executable semantic cases: 184 / 771
- remaining semantic cases: 587
- fully materialized primary primitive families:
  - `prim.source.observation` — 18 / 18
  - `prim.derivation.mapping` — 23 / 23
  - `prim.request.binding` — 34 / 34
  - `prim.provider.attempts` — 13 / 13
  - `prim.model.output` — 32 / 32
  - `prim.tool.lifecycle` — 43 / 43
- reusable primitive Receipts: 135
- normalized semantic expected results: 184

Review rule applied during materialization: sentences that only pre-empt criticism and add no fact, inference, constraint, or action are omitted.


## Current status after Wave 05-E Provider Adapter B

- executable semantic cases: 533 / 771
- remaining semantic cases: 238
- remaining by family: PAD 20, TAD 90, VFY 128
- reusable primitive Receipts registered: 223
- normalized semantic expected results: 533
- fully materialized primary primitive families now also include occurrence identity, Trust, Taint, privacy commitment/redaction, multi-Receipt, Integrity composition, claim strength, and ordering/time
- adapter-capture primary requirements executable: 45 / 155; Tool Adapter and Verifier families remain the largest unresolved buckets

This status is mechanically derived from the 16 family indexes and `coverage-matrix.json`; it is a conformance-state synchronization and does not change frozen protocol semantics or JSON Schema.
