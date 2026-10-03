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

Runner A still fails closed for `semantic_verifier` and `mixed_schema_semantic` until their independent semantic executor is implemented.

Current gates:

```text
direct_schema          6 / 6
deterministic_vector  43 / 43 target
```

Runner A must not import or call the P5 matcher coverage auditor.
