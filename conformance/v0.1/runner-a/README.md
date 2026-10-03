# C2ATrace Runner A

Runner A is the first independent conformance execution implementation for P6.

## Wave 01

Wave 01 loads all 907 indexed cases and independently performs:

- deterministic case input materialization;
- JSON Pointer extraction and ordered add/remove/replace patches;
- Draft 2020-12 Schema validation against the frozen protocol bundle and conformance schemas;
- SHA-256 and HMAC-SHA256 recomputation;
- Ed25519 verification;
- the current deterministic-vector checks;
- normalized expected-result comparison after execution.

The executable gate in this wave is 49 cases: 6 `direct_schema` plus 43 `deterministic_vector`.

The remaining 858 `mixed_schema_semantic` and `semantic_verifier` cases are loaded and their materialized Schema surface is evaluated, but they remain `blocked_semantic_checker` until the 21 semantic primitive checkers are implemented. A blocked case is not accepted.

## Independence boundary

Runner A does not import the P5 audit implementation and does not use expected-result files to generate actual Schema or vector results. Expected results enter only after materialization, Schema execution, and applicable vector execution, for comparison.

Runner A is conformance infrastructure. It is not the Product Verifier or SDK.

## JCS boundary in Wave 01

The current vector corpus uses integer numeric values and ASCII object keys. Runner A fails closed on floating-point values or non-ASCII object keys rather than claiming unimplemented general RFC 8785 behavior. This boundary must be widened before any later case depends on those inputs.

## Run

```bash
python -m pip install -r conformance/v0.1/runner-a/requirements.txt
python conformance/v0.1/runner-a/runner.py --output /tmp/runner-a-wave-01.json
```

A successful Wave 01 run requires exactly 49 passed cases and zero failed/error cases. The report keeps the remaining cases explicit as blocked semantic work.
