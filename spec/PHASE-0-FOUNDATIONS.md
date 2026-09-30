# C2ATrace v0.1 — Phase 0 Foundations

Status: REVIEWED AND REVISED.

Scope: Threat Model, Claim Matrix, Terminology, Core Artifact/Event Graph.

JSON Schema: NOT FROZEN.

Implementation: NOT STARTED.

## 1. Normative discipline

The keywords MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are normative only inside a numbered normative requirement or when a definition explicitly cites such a requirement.

Phase 0 terminology is otherwise definitional, not an independent source of untracked normative behavior.

Every numbered MUST / MUST NOT requirement in Phase 0 has a planned conformance test identifier.

## 2. Semantic categories

C2ATrace uses three primary runtime provenance categories:

- **Artifact** — an immutable recorded data representation.
- **Activity** — a recorded process that uses and/or generates Artifacts.
- **Assertion** — a recorded claim about an object, relation, or property.

C2ATrace also uses structural/meta objects that are not runtime provenance nodes:

- **Reference** — identifies or locates something outside the artifact identity model, for example SourceRef.
- **Scope** — groups records logically, for example Run.
- **Package** — carries records, for example Receipt.
- **Integrity metadata** — authenticates or commits to a package/representation, for example IntegrityEnvelope.

This distinction closes the object taxonomy without forcing SourceRef, Run, Receipt, or IntegrityEnvelope into Artifact / Activity / Assertion.

## 3. Core object classification

| Object | Classification | Notes |
|---|---|---|
| Run | Scope | Logical grouping; does not imply completeness |
| SourceRef | Reference | Logical source identity / locator |
| SourceObservation | Artifact | Producer-recorded observed representation |
| ModelInputComponent | Artifact abstraction | Abstract superclass for application-visible model inputs |
| ContextFragment | Artifact | ModelInputComponent subtype |
| Transform | Activity | Data/process transformation |
| Derivation | Assertion | Explicit artifact-to-artifact ancestry claim |
| RequestBinding | Assertion | Qualified inclusion claim relative to a RequestSnapshot |
| RequestSnapshot | Artifact | Request representation at one capture level |
| ModelInvocation | Activity | Logical application-level model invocation |
| ProviderAttempt | Activity | One discrete provider attempt |
| ModelOutput | Artifact | Application-visible output representation |
| OutputItem | Artifact abstraction | Item contained in ModelOutput |
| ToolProposal | Artifact | OutputItem subtype |
| ToolInvocation | Artifact | Effective tool invocation before execution |
| ToolExecution | Activity | Actual execution attempt |
| ToolResult | Artifact | Returned/result representation |
| EffectObservation | Artifact | Recorded evidence about external state |
| TrustAssertion | Assertion | Trust judgement and basis |
| TaintAssertion | Assertion | Conservative taint judgement and basis |
| Receipt | Package | Portable set of records |
| IntegrityEnvelope | Integrity metadata | Commitments/signatures over defined representations |

## 4. Corrected core graph

Transform and Derivation are deliberately separate: Transform is an Activity; Derivation is an Assertion.

~~~text
SourceRef
    ▲
    │ observed_from (assertion)
    │
SourceObservation
    │
    │ used by
    ▼
Transform
    │
    │ generates
    ▼
ContextFragment / ModelInputComponent

Optional explicit assertion:
ContextFragment ── derived_from ──> SourceObservation

ModelInputComponent
    │
    │ RequestBinding (recorded inclusion assertion)
    ▼
RequestSnapshot

ProviderAttempt ── uses_request ──> RequestSnapshot
ProviderAttempt ── attempt_of ────> ModelInvocation
ProviderAttempt ── produces ──────> ModelOutput
ModelOutput ────── contains ──────> OutputItem / ToolProposal

ToolProposal
    │
    │ used by optional application preparation Transform
    ▼
Transform
    │
    │ generates
    ▼
ToolInvocation

ToolExecution ── uses_invocation ──> ToolInvocation
ToolExecution ── returns ──────────> ToolResult
EffectObservation ── supported_by ─> ToolResult or other evidence Artifact
~~~

A Transform using an Artifact and generating another Artifact does not, by itself, establish Derivation between those Artifacts.

## 5. Core relation semantics

| Relation | Source | Target | Semantic class |
|---|---|---|---|
| observed_from | SourceObservation | SourceRef | Assertion |
| uses | Activity | Artifact | Provenance relation |
| generates | Activity | Artifact | Provenance relation |
| derived_from | Artifact | Artifact | Derivation Assertion |
| bound_into | ModelInputComponent | RequestSnapshot | RequestBinding Assertion |
| uses_request | ProviderAttempt | RequestSnapshot | Provenance relation |
| attempt_of | ProviderAttempt | ModelInvocation | Structural/provenance relation |
| produces | ProviderAttempt | ModelOutput | Provenance relation |
| contains | ModelOutput | OutputItem | Structural composition |
| uses_invocation | ToolExecution | ToolInvocation | Provenance relation |
| returns | ToolExecution | ToolResult | Provenance relation |
| supported_by | EffectObservation | Artifact | Evidence Assertion |

Exact wire names remain unfrozen.

## 6. Core graph invariants

### GRAPH-001 — Reference resolution

Until an external-reference profile is defined, every normative internal reference in a conforming Receipt MUST resolve within that supplied Receipt.

Planned test: `graph-missing-reference-001`.

### GRAPH-002 — Immutable Artifact identity

The same Artifact ID MUST NOT denote different representations.

Planned test: `artifact-id-reuse-001`.

### GRAPH-003 — Derivation DAG

The explicit Artifact derivation graph MUST be acyclic.

Planned test: `derivation-cycle-001`.

### GRAPH-004 — Binding target

A RequestBinding MUST target exactly one RequestSnapshot. A ModelInputComponent MAY participate in multiple RequestBindings.

Planned test: `binding-target-001`.

### GRAPH-005 — Request is not attempt

A ProviderAttempt MUST NOT be used as a substitute for RequestSnapshot.

Planned test: `request-attempt-conflation-001`.

### GRAPH-006 — Output attempt identity

Every recorded ModelOutput MUST identify the ProviderAttempt associated with its production.

Planned test: `orphan-model-output-001`.

### GRAPH-007 — Proposal is not execution

ToolProposal presence MUST NOT imply ToolExecution presence.

Planned test: `proposal-only-001`.

### GRAPH-008 — Effective invocation

Every ToolExecution MUST reference the effective ToolInvocation it attempted to execute.

Planned test: `execution-without-invocation-001`.

### GRAPH-009 — No fake denied execution

A ToolProposal rejected before execution begins MUST NOT create ToolExecution solely to represent denial.

Planned test: `denied-with-fake-execution-001`.

### GRAPH-010 — Result remains an Artifact

If execution-return data is retained as provenance-bearing data, it MUST have Artifact identity distinct from ToolExecution; ToolResult is the v0.1 core representation for this role.

Planned test: `tool-result-artifact-001`.

### GRAPH-011 — Result is not effect truth

ToolResult MUST NOT, by itself, establish external Effect truth.

Planned test: `lying-tool-result-001`.

### GRAPH-012 — Effect evidence basis

EffectObservation MUST reference an evidence basis or explicitly represent the basis as unknown.

Planned test: `effect-basis-001`.

### GRAPH-013 — Explicit ordering dominates timestamps

A verifier MUST NOT use wall-clock timestamp ordering to override contradictory explicit provenance dependencies.

Planned test: `timestamp-conflict-001`.

### GRAPH-014 — Missing edge is not negation

The absence of a provenance relation in the supplied graph MUST NOT be reported as proof that the relation did not exist.

Planned test: `absence-not-negation-001`.

### GRAPH-015 — Core object classification is explicit

Every normative v0.1 core object MUST have exactly one primary classification in the Phase 0 classification table, except an explicitly declared abstraction such as ModelInputComponent or OutputItem.

Planned test: `core-type-classification-001`.

### GRAPH-016 — Activity / Assertion separation

Derivation and RequestBinding MUST NOT be encoded or interpreted as Activities; Transform MUST NOT be encoded or interpreted as a Derivation Assertion.

Planned test: `activity-assertion-separation-001`.

## 7. Architecture review outcomes

The revised Phase 0 model has been checked against:

- provider retries
- different request representations across retries
- multiple capture levels
- application-modified tool arguments
- rejected tool proposals
- tool results reused as later context
- incorrect or dishonest tool servers
- malicious but correctly signing Producers
- truncated receipt sets/chains
- concurrent agent execution
- streaming output
- hash-only privacy constraints
- object taxonomy closure
- Activity / Assertion category confusion
- structural versus content-verified RequestBinding
- claim-evidence composition

The unresolved items below are explicitly deferred and do not authorize stronger claims.

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
- OQ-015 IntegrityEnvelope signing scope and detached/embedded representation.

## 9. Gate decision

Threat Model: PASS AFTER SECOND REVIEW.

Claim Matrix: PASS AFTER SECOND REVIEW.

Terminology: PASS AFTER SECOND REVIEW.

Core Artifact/Event Graph: PASS AFTER SECOND REVIEW WITH OPEN DESIGN ITEMS.

The next specification stage MUST focus on:

~~~text
SourceRef / SourceObservation
        ↓
Transform / Derivation
        ↓
RequestSnapshot / RequestBinding
~~~

No JSON Schema freeze or implementation work may begin until those semantics and their adversarial conformance cases are complete.
