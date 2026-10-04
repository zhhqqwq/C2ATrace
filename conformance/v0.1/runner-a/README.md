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

Wave 03 begins the independent semantic executor. Batch 01 implements `prim.ref.local`, `prim.ref.external`, `prim.ref.failure`, and `prim.graph.invariants` for 16 primary semantic requirements. Batch 02 adds the derivation cluster: all 23 semantic requirements whose primary primitive is `prim.derivation.mapping`, plus six adjacent DRV mixed-schema-semantic boundaries, for 29 cases. Unimplemented semantic requirements remain fail-closed with `semantic_executor_not_implemented`.

The semantic executor derives findings from materialized Receipt/harness inputs. Expected-result files are used only by the runner comparator, never by the executor.

Current gates:

```text
direct_schema           6 / 6
deterministic_vector    43 / 43
semantic foundation     16 / 16
semantic derivation     29 / 29
request binding          47 / 47
identity core              8 / 8
provider occurrence         3 / 3
model/output core            2 / 2
provider retry core           5 / 5
provider hedge core           2 / 2
model output bounded claims    3 / 3
tool result/effect bounded      3 / 3
```

Runner A must not import or call the P5 matcher coverage auditor.

Batch 03 adds the request-binding cluster: all 34 semantic requirements whose primary primitive is `prim.request.binding`, plus 13 adjacent REQ mixed-schema-semantic boundaries. It independently evaluates request ownership, snapshot reuse/isolation, effective-request cardinality, transition ordering and propagation, source/target occurrence binding, JSON Pointer/location resolution, text/byte Region bounds, semantic/byte digests, commitment comparison, redaction/HMAC capability limits, and prepared-body claim bounds.

Batch manifests are machine-readable runner selection specifications. A batch manifest may select semantic requirements by primary primitive and explicitly add adjacent mixed-schema-semantic requirement IDs. Runner A verifies the declared expected case count before treating the batch as complete.

Batch 04 starts `prim.identity.occurrence` using explicit requirement selection because the 60 identity-primary requirements span eleven families and multiple not-yet-executed dependency primitives. The first 8-case core batch is limited to identity invariants whose dependencies are already implemented by the graph, derivation, and request-binding foundations.

Batch 05 selects the dependency-closed provider occurrence identity core after comparing the remaining model/output and provider identity clusters. It covers PAD-023, PAD-078, and PAD-085 only: provider-reported remote IDs do not replace C2ATrace occurrence IDs, and semantically matching CaptureDiagnostic observations remain distinct occurrences. Provider retry/failover/hedge semantics, adapter capture, and model-output primitives remain outside this batch.

Batch 06 selects the only two identity-primary requirements whose dependency closure is complete after Batch 05 without introducing a new major primitive: OUT-019 and OUT-026. Shared-receipt neighbors OUT-021/PAD-065 remain blocked on `prim.verifier.report`, and PAD-022 remains blocked on `prim.provider.attempts`.

Batch 07 ranks the next blocker primitives by single-step unlock impact: `prim.verifier.report` 93, `prim.model.output` 20, and `prim.provider.attempts` 19. The verifier surface is intentionally deferred because it spans eleven families and a much larger reporting/completeness/conflict surface. Between the two compact candidates, provider-attempt semantics have denser shared scenarios. The selected 5-case retry core uses one `provider-visible-retry.json` receipt for PAD-020, PAD-054, PAD-055, PAD-056, and TM-005. Cycle, failover, hedge, and adapter-capture cases remain fail-closed.

Batch 08 re-ranks residual provider-attempt subclusters against the dependency-closed model-output core. The selected PAD-059/PAD-061 hedge core is the tightest incremental surface: both cases use one `provider-hedged-attempts.json` receipt and reuse ProviderAttempt occurrence/lifecycle predicates. PAD-060 and OUT-013 remain blocked on `prim.ordering.time`; predecessor graph, failover, and model-output primary clusters remain fail-closed.

Batch 09 re-ranks the post-hedge residual surface from the 161-case Runner A support baseline. The selected OUT-025/OUT-031/OUT-046 cluster has 20-case single-step `prim.model.output` leverage, a 10-case dependency-closed model-output primary core, and three selected cases on one shared `fixtures/v0.1/valid/provider-retry.json` fixture. All three reuse one accepted-ModelOutput ownership resolver; the batch then bounds ModelOutput identity, complete capture scope, and TextOutput claims without upgrading them to provider-wire identity, hidden-output absence, hidden reasoning, or token history. Provider predecessor/failover cases remain fail-closed.

Batch 10 selects TOOL-040/TOOL-043/TOOL-048 only on the shared `fixtures/v0.1/valid/tool-effect.json` fixture. Runner A independently resolves the ToolInvocation → ToolExecution → ToolResult → EffectObservation chain through local references and same-run ownership. It bounds complete ToolResult capture to the captured result, treats `basis=execution_result` as result-supported rather than independent external verification, and prevents EffectObservation from being upgraded to desired-outcome proof. TOOL-011 and all other tool-lifecycle cases remain fail-closed.
