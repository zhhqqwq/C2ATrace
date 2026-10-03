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

It intentionally fails closed for `semantic_verifier`, `mixed_schema_semantic`, and `deterministic_vector` execution until their independent executors are implemented. Expected-result files are never used as actual execution output.

Current Wave 01 gate:

```text
6 direct_schema cases
→ independently materialized
→ independently Schema-validated
→ golden schema_results compared
→ 6/6 pass
```

Runner A must not import or call the P5 matcher coverage auditor.
