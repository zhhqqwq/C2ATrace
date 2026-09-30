# C2ATrace v0.1 Threat Model

Status: Phase 0 baseline.

## 1. Fundamental security model

C2ATrace describes Producer-recorded provenance, not objective reality itself.

The protocol MUST preserve the following distinctions:

~~~text
recorded ≠ true
signed ≠ true
valid ≠ complete
included ≠ causal
trusted ≠ objectively trustworthy
tainted ≠ malicious
tool succeeded ≠ desired outcome achieved
~~~

## 2. Actors and trust boundaries

### Producer

The application or runtime that emits C2ATrace records. A Producer may be correct, buggy, misconfigured, partially bypassed, fully compromised, or malicious. C2ATrace v0.1 does not assume Producer honesty.

### Instrumentation

Captures sources, transformations, provider requests, model outputs, and tool activity. Ordinary v0.1 instrumentation typically shares the application's trust domain. A fully compromised application process can generally bypass or falsify in-process instrumentation.

### Provider Adapter

Captures the application-side provider boundary. It may record RequestSnapshot, ProviderAttempt, and ModelOutput, but MUST NOT claim visibility into provider-internal state without separate evidence.

### Model Provider

Provider-internal instructions, rewriting, routing, model selection, server-side retries, safety transforms, provider-added tools, and internal model representations are unknown unless separately evidenced.

### Tool Runtime

Executes ToolInvocation. Tool-runtime success and returned data are recorded evidence, not automatic proof of external ground truth.

### Signer

A valid signature establishes that the corresponding private-key holder authenticated a representation. It does not establish Producer honesty, capture completeness, factual correctness, or trusted wall-clock time.

### Verifier

Checks syntax, graph structure, references, digests, signatures, and semantic invariants. It MUST NOT silently strengthen claims beyond their evidence.

## 3. In-scope failure classes

C2ATrace v0.1 MUST safely represent or reject, as appropriate:

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

- malicious Producer omission resistance
- security under a fully compromised process
- signing-key non-compromise
- public-key identity
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

An implementation MUST distinguish integrity, truth, and completeness.

Planned test: verifier-wording-001.

### TM-002 — No causal inference

A verifier MUST NOT infer model causal responsibility merely from a provenance path.

Planned test: causality-negative-001.

### TM-003 — Unknown is first-class

Where the specification permits unknown provenance, trust, derivation, or effect state, a conforming implementation MUST accept and preserve unknown.

Planned test: unknown-valid-001.

### TM-004 — Producer assertion is not independent verification

A verifier MUST NOT upgrade a Producer-asserted external fact to independently verified merely because receipt integrity or signature verification succeeds.

Planned test: producer-assertion-001.

### TM-005 — Provider attempts are distinct

Each recorded ProviderAttempt MUST have a distinct identity. A retry MUST NOT overwrite a prior attempt.

Planned test: provider-retry-001.

### TM-006 — Effective invocation is explicit

When an application may modify, supplement, validate, or normalize proposed tool arguments, the protocol MUST be able to represent the final effective ToolInvocation separately from ToolProposal.

Planned test: tool-enrichment-001.

### TM-007 — No execution without an execution attempt

If a ToolProposal is rejected before execution begins, a ToolExecution MUST NOT be created solely to encode that rejection.

Planned test: tool-denied-001.

### TM-008 — Execution is not effect

A successful ToolExecution MUST NOT automatically establish external Effect truth.

Planned test: tool-success-no-effect-001.

### TM-009 — Chain validity is not global completeness

A verifier MAY report that the supplied receipt chain is valid, but MUST NOT infer that no earlier, later, or omitted receipts exist.

Planned test: chain-truncation-001.

### TM-010 — Provider internals default to unknown

Provider-internal state MUST remain unknown unless supported by separate provider-originated or otherwise independently acceptable evidence.

Planned test: provider-hidden-state-001.

### TM-011 — Explicit dependency ordering dominates timestamps

Wall-clock timestamps MUST NOT be used as the sole basis to override contradictory explicit provenance dependencies. A verifier SHOULD report timestamp inconsistency.

Planned test: timestamp-conflict-001.