# C2ATrace v0.1 — Phase 0 Foundations

Status: ACCEPTED WITH REVISIONS.

Scope: Threat Model, Claim Matrix, Terminology, Core Artifact/Event Graph.

JSON Schema: NOT FROZEN.

Implementation: NOT STARTED.

## 1. Normative convention

MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are normative. Every MUST / MUST NOT requirement is expected to map to a future conformance test.

## 2. Core object categories

C2ATrace uses three foundational categories:

- Artifact — immutable recorded data representation.
- Activity — recorded process that uses and/or generates Artifacts.
- Assertion — recorded claim about objects, relations, or properties.

This separation prevents request data, execution activities, and external-state claims from being collapsed into one ambiguous event log.

## 3. Accepted core graph

~~~text
SourceRef
    ↓ observed_as
SourceObservation
    ↓
Transform / Derivation
    ↓
ModelInputComponent / ContextFragment
    ↓ RequestBinding
RequestSnapshot
    ↓ used_request
ProviderAttempt ── attempt_of ──> ModelInvocation
    ↓ produces
ModelOutput
    ↓ contains
ToolProposal
    ↓ application validation / enrichment / normalization
ToolInvocation
    ↓
ToolExecution
    ↓
ToolResult
    ↓ supports
EffectObservation
~~~

Horizontal assertions include TrustAssertion, TaintAssertion, Derivation, and future integrity metadata.

## 4. Why the revisions are necessary

### RequestSnapshot is distinct from ProviderAttempt

A request may exist at multiple capture levels and may differ across retries. Inclusion therefore binds to an immutable RequestSnapshot, not directly to a logical model call or provider attempt.

### ToolInvocation is distinct from ToolProposal

The application may validate, normalize, enrich, rewrite, or supplement proposed tool arguments. The effective invocation must therefore be separately identifiable.

### ToolResult is distinct from ToolExecution

Execution is an Activity; returned data is an Artifact. This distinction allows ToolResult to become future context while preserving provenance semantics.

### EffectObservation is distinct from ToolResult

A tool can report success or a remote identifier without independently proving the external state. EffectObservation records evidence and its basis without upgrading it to outcome truth.

### Action is non-normative

Action remains a human-facing umbrella term only. The protocol preserves proposal, invocation, execution, result, and effect as separate concepts.

## 5. Core graph invariants

### GRAPH-001 — Reference resolution

All internal references MUST resolve within the receipt's resolution scope or through a future explicitly defined external-reference mechanism.

Planned test: graph-missing-reference-001.

### GRAPH-002 — Immutable Artifact identity

The same Artifact ID MUST NOT denote different representations.

Planned test: artifact-id-reuse-001.

### GRAPH-003 — Derivation DAG

The explicit Artifact derivation graph MUST be acyclic. Agent loops remain representable by creating new identities in each iteration.

Planned test: derivation-cycle-001.

### GRAPH-004 — Binding target

A RequestBinding MUST target exactly one RequestSnapshot. A component MAY have multiple RequestBindings.

Planned test: binding-target-001.

### GRAPH-005 — Request is not attempt

ProviderAttempt MUST NOT be used as a substitute for RequestSnapshot.

Planned test: request-attempt-conflation-001.

### GRAPH-006 — Output attempt identity

Every recorded ModelOutput MUST identify the ProviderAttempt associated with its production.

Planned test: orphan-model-output-001.

### GRAPH-007 — Proposal is not execution

ToolProposal presence MUST NOT imply ToolExecution presence.

Planned test: proposal-only-001.

### GRAPH-008 — Effective invocation

Every ToolExecution MUST reference the effective ToolInvocation it attempted to execute.

Planned test: execution-without-invocation-001.

### GRAPH-009 — No fake denied execution

A ToolProposal rejected before execution begins MUST NOT create ToolExecution solely to represent denial.

Planned test: denied-with-fake-execution-001.

### GRAPH-010 — Result remains an Artifact

When execution-return data is preserved for provenance, it SHOULD be represented as ToolResult rather than embedded as ToolExecution identity.

Planned test: tool-result-artifact-001.

### GRAPH-011 — Result is not effect truth

ToolResult MUST NOT automatically establish external Effect truth.

Planned test: lying-tool-result-001.

### GRAPH-012 — Effect evidence

EffectObservation MUST preserve an evidence basis or explicitly record basis as unknown.

Planned test: effect-basis-001.

### GRAPH-013 — Explicit ordering wins

Wall-clock timestamps MUST NOT override contradictory explicit provenance dependencies. A verifier SHOULD report timestamp inconsistency.

Planned test: timestamp-conflict-001.

### GRAPH-014 — Missing edge is not negation

The absence of a relation in the supplied graph MUST NOT automatically be interpreted as proof that the relation did not exist.

Planned test: absence-not-negation-001.

## 6. Architecture review outcomes

The Phase 0 graph was tested conceptually against:

- provider retries
- differing retry request representations
- multiple request capture levels
- application-modified tool arguments
- rejected tool proposals
- tool results reused as future context
- lying or incorrect tool servers
- malicious but correctly signing Producers
- truncated receipt chains
- concurrent agent execution
- streaming output
- hash-only privacy constraints

All are either resolved by the core model or explicitly deferred without creating a false claim.

## 7. Current normative core object set

~~~text
Run

SourceRef
SourceObservation

ModelInputComponent
ContextFragment

Transform
Derivation

RequestBinding
RequestSnapshot

ModelInvocation
ProviderAttempt
ModelOutput
OutputItem

ToolProposal
ToolInvocation
ToolExecution
ToolResult
EffectObservation

TrustAssertion
TaintAssertion

Receipt
IntegrityEnvelope
~~~

Action is not a normative core object.

## 8. Open questions before Schema freeze

The following MUST be resolved before JSON Schema is frozen:

- OQ-001 RequestBinding text-range coordinate system.
- OQ-002 Binary/media partial binding.
- OQ-003 Exact / partial / approximate derivation vocabulary.
- OQ-004 Split / concat / truncation range lineage.
- OQ-005 RequestSnapshot capture-level transition model.
- OQ-006 Semantic digest versus byte digest.
- OQ-007 Hash-only verification strength for RequestBinding.
- OQ-008 ToolInvocation argument-level provenance.
- OQ-009 ModelOutput multi-item / streaming profile.
- OQ-010 TrustAssertion subjects and vocabulary.
- OQ-011 Taint lattice and propagation rules.
- OQ-012 Sanitization semantics and anti-laundering constraints.
- OQ-013 External references and multi-receipt resolution.
- OQ-014 Receipt scope declaration without implying completeness.

## 9. Gate decision

Threat Model: PASS.

Claim Matrix: PASS.

Terminology: PASS.

Core Artifact/Event Graph: PASS WITH OPEN DESIGN ITEMS.

The next specification stage MUST focus on:

~~~text
SourceRef / SourceObservation
        ↓
Transform / Derivation
        ↓
RequestSnapshot / RequestBinding
~~~

No JSON Schema freeze or implementation work should begin until those semantics and their adversarial test cases are complete.