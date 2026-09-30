# C2ATrace v0.1 Threat Model

Status: Phase 0 baseline, second-review revision.

## 1. Fundamental security model

C2ATrace describes Producer-recorded provenance, not objective reality itself.

The model is founded on these distinctions:

~~~text
recorded ≠ true
signed ≠ true
valid ≠ complete
included ≠ causal
trusted ≠ objectively trustworthy
tainted ≠ malicious
tool succeeded ≠ desired outcome achieved
~~~

The numbered requirements below enforce the machine-testable parts of those boundaries.

## 2. Actors and trust boundaries

### Producer

The application or runtime that emits C2ATrace records. A Producer may be correct, buggy, misconfigured, partially bypassed, fully compromised, or malicious. C2ATrace v0.1 does not assume Producer honesty.

### Instrumentation

Captures sources, transformations, provider requests, model outputs, and tool activity. Ordinary v0.1 instrumentation typically shares the application's trust domain. A fully compromised application process can generally bypass or falsify in-process instrumentation.

### Provider Adapter

Captures the application-side provider boundary. It records application-visible evidence only.

### Model Provider

Provider-internal instructions, rewriting, routing, model selection, server-side retries, safety transforms, provider-added tools, and internal model representations are outside the default visibility boundary.

### Tool Runtime

Executes ToolInvocation. Tool-runtime success and returned data are recorded evidence, not automatic proof of external ground truth.

### Signer

A valid signature authenticates a defined representation under a public key. It does not by itself establish Producer honesty, capture completeness, factual correctness, trusted wall-clock time, or real-world identity of the key holder.

### Verifier

Checks syntax, graph structure, references, representations, digests, signatures, and semantic invariants. It does not silently strengthen claim scope.

## 3. Failure/adversary cases considered

Phase 0 is designed to avoid false precision when confronted with:

- malicious external content
- incorrect source metadata
- unknown source
- incorrect trust assertion
- missing or partial instrumentation
- provider retries
- request mutation across capture levels or attempts
- concurrent model calls
- application-modified tool arguments
- tool execution failure
- tool-server misreporting
- missing effect evidence
- receipt modification
- receipt omission or truncation
- incorrect timestamps
- unknown derivation

## 4. Explicit out-of-scope guarantees

C2ATrace v0.1 does not establish:

- resistance to malicious Producer omission
- security under a fully compromised process
- signing-key non-compromise
- public-key real-world identity
- trusted wall-clock time
- provider-internal visibility
- model hidden reasoning
- token-level causal attribution
- model decision causality
- objective source trustworthiness
- external ground truth
- complete runtime history
- tamper-resistant hardware capture
- transparency-log completeness

## 5. Normative threat requirements

### TM-001 — Integrity / truth / completeness separation

A conforming verifier MUST NOT report integrity success as establishing factual truth or capture completeness.

Planned test: `verifier-wording-001`.

### TM-002 — No causal inference

A conforming verifier MUST NOT infer model causal responsibility merely from a provenance path.

Planned test: `causality-negative-001`.

### TM-003 — Unknown is first-class

Where the specification permits unknown provenance, trust, derivation, effect basis, or provider-internal state, a conforming implementation MUST preserve that unknown state rather than replace it with a stronger value.

Planned test: `unknown-valid-001`.

### TM-004 — Producer assertion is not independent verification

A conforming verifier MUST NOT upgrade a Producer-asserted external fact to independently verified merely because representation integrity or signature verification succeeds.

Planned test: `producer-assertion-001`.

### TM-005 — Provider attempts are distinct

Each recorded ProviderAttempt MUST have a distinct identity. A retry MUST NOT overwrite or reuse a prior ProviderAttempt identity.

Planned test: `provider-retry-001`.

### TM-006 — Effective invocation is explicit

When an application may modify, supplement, validate, or normalize proposed tool arguments, the protocol MUST be able to represent the final effective ToolInvocation separately from ToolProposal.

Planned test: `tool-enrichment-001`.

### TM-007 — No execution without an execution attempt

If a ToolProposal is rejected before execution begins, a ToolExecution MUST NOT be created solely to encode that rejection.

Planned test: `tool-denied-001`.

### TM-008 — Execution is not effect

A successful ToolExecution MUST NOT, by itself, establish external Effect truth or desired-outcome success.

Planned test: `tool-success-no-effect-001`.

### TM-009 — Supplied linkage is not global completeness

If an implementation supports linkage among multiple Receipts, a verifier MUST NOT infer from valid supplied linkage that no earlier, later, or omitted Receipt exists.

Planned test: `chain-truncation-001`.

### TM-010 — Provider internals default to unknown

In core v0.1, a verifier MUST report provider-internal processing state as UNKNOWN unless a future recognized evidence profile explicitly defines how that state is established.

Planned test: `provider-hidden-state-001`.

### TM-011 — Explicit dependency ordering dominates timestamps

A verifier MUST NOT use wall-clock timestamp ordering to override contradictory explicit provenance dependencies.

Planned test: `timestamp-conflict-001`.

### TM-012 — Capture-level bounded claims

A verifier MUST NOT report a request claim at a stronger boundary than the RequestSnapshot capture level supports.

Examples: a provider_payload snapshot does not establish exact transmitted bytes or provider-internal model input.

Planned test: `capture-level-overclaim-001`.
