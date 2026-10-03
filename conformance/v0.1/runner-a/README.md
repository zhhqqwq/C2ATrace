# Runner A

Runner A is the first independent C2ATrace v0.1 conformance runner.

Wave 01 implements:

- suite/index/case loading;
- deterministic path/inline materialization;
- JSON Pointer extraction;
- ordered add/remove/replace patches;
- frozen protocol/conformance Schema resolution;
- actual Schema validation;
- language-neutral Schema-result comparison;
- normalized finding matcher/comparator primitives.

Wave 02 adds an independent deterministic-vector executor for all 43 vector cases:

- RFC 8785 JCS canonicalization;
- SHA-256 and unpadded base64url;
- HMAC-SHA256 candidate verification;
- Ed25519 key derivation, signing, and verification;
- Signing Statement field binding;
- embedded/detached envelope binding;
- post-sign tamper and record-deletion separation;
- hash/HMAC/redaction privacy-commitment checks;
- integrity/privacy composition checks;
- normalized vector-result comparison.

Vector execution is selected from the case's `planned_test_id`. The executor never reads an expected-result file when producing actual vector results.

Wave 03 begins the independent semantic executor. The first foundation batch implements `prim.ref.local`, `prim.ref.external`, `prim.ref.failure`, and `prim.graph.invariants` for 16 primary semantic requirements. Unimplemented semantic requirements remain fail-closed with `semantic_executor_not_implemented`.

The semantic executor derives findings from materialized Receipt/harness inputs. Expected-result files are used only by the runner comparator, never by the executor.

Current gates:

```text
direct_schema          6 / 6
deterministic_vector  43 / 43
semantic foundation    16 / 16 target
```

Runner A must not import or call the P5 matcher coverage auditor.
