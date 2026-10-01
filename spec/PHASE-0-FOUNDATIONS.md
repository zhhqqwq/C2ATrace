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
| ExternalReference | Reference form | Explicit cross-Receipt object address with optional target-payload pin |
| SourceObservation | Artifact | Producer-recorded observed representation |
| ModelInputComponent | Artifact abstraction | Abstract superclass for application-visible model inputs |
| ContextFragment | Artifact | ModelInputComponent subtype |
| Transform | Activity | Data/process transformation |
| Derivation | Assertion | Explicit artifact-to-artifact ancestry claim |
| RequestBinding | Assertion | Occurrence-specific, capture-level-local inclusion claim relative to one RequestSnapshot |
| RequestSnapshot | Artifact | Request representation at one capture level with one capture-scope owner |
| ModelInvocation | Activity | Logical application-level model invocation; can contain multiple physical attempts |
| ProviderAttempt | Activity | One discrete application-observed provider attempt |
| ModelOutput | Artifact | Terminal assembled application-visible model-result representation for one ProviderAttempt |
| OutputItem | Artifact abstraction | Occurrence-identified item contained in one ModelOutput |
| ToolProposal | Artifact | OutputItem subtype representing one model-output proposal occurrence |
| ToolInvocation | Artifact | Immutable effective application-selected tool call before execution |
| ToolDecision | Assertion | Application/policy allow/deny/unknown decision on one ToolProposal or ToolInvocation |
| ToolExecution | Activity | One actual execution attempt of one ToolInvocation |
| ToolResult | Artifact | Terminal assembled application-visible result representation for one ToolExecution |
| EffectObservation | Artifact | Bounded evidence claim about possible external state |
| TrustAssertion | Assertion | Trust judgement and basis |
| TaintAssertion | Assertion | Conservative taint judgement and basis |
| CaptureDiagnostic | Assertion | Bounded instrumentation capture-state/degradation assertion; not completeness proof |
| Receipt | Package | Portable package identity centered on one immutable Authenticated Receipt Payload |
| ReceiptLink | Integrity metadata | Digest-pinned package-level link to a prior Receipt payload |
| IntegrityEnvelope | Integrity metadata | Embedded/detached signature metadata authenticating a defined Receipt payload commitment |

## 4. Corrected core graph

Transform and Derivation are deliberately separate: Transform is an Activity; Derivation is an Assertion.

The diagram is compositional rather than mandatory: a valid path may omit Transform when no transformation is recorded.

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

Optional display shorthand:
ContextFragment ── derived_from ──> SourceObservation

Part B refinement:
Derivation is semantically a qualified Assertion with one target output, one generating Transform, and one or more contributing inputs. The binary edge above is only the one-input shorthand.

ModelInputComponent
    │
    │ RequestBinding (recorded inclusion assertion)
    ▼
RequestSnapshot

ProviderAttempt ── uses_request ──> RequestSnapshot
ProviderAttempt ── attempt_of ────> ModelInvocation
ProviderAttempt ── produces ──────> ModelOutput
ModelInvocation ── accepted_output ─> ModelOutput  (optional, at most one)
ModelOutput ────── contains ──────> OutputItem / ToolProposal

ToolProposal
    │
    │ optional ToolDecision
    │
    │ used by optional application preparation Transform
    ▼
Transform
    │
    │ generates
    ▼
ToolInvocation
    │
    │ optional ToolDecision
    ▼

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
| derived_from | Artifact(s) | Artifact | Derivation Assertion; binary rendering is shorthand for the qualified Part B form |
| selects_or_forwards | Transform | Artifact | Existing Artifact selected/forwarded without generation |
| bound_into | ModelInputComponent | RequestSnapshot | RequestBinding Assertion |
| uses_request | ProviderAttempt | RequestSnapshot | Effective request-snapshot association at a declared capture level |
| attempt_of | ProviderAttempt | ModelInvocation | Structural/provenance relation |
| retry_of / failover_from / hedged_with | ProviderAttempt | ProviderAttempt | Optional Producer-asserted orchestration relation within one ModelInvocation |
| produces | ProviderAttempt | ModelOutput | Provenance relation |
| accepted_output | ModelInvocation | ModelOutput | Producer-asserted selected logical result |
| contains | ModelOutput | OutputItem | Structural composition |
| decision_on | ToolDecision | ToolProposal or ToolInvocation | Policy/application Assertion |
| uses_invocation | ToolExecution | ToolInvocation | Provenance relation |
| retry_of / replay_of / duplicate_of | ToolExecution | ToolExecution | Optional Producer-asserted execution orchestration relation |
| returns | ToolExecution | ToolResult | Provenance relation |
| supported_by | EffectObservation | Artifact | Evidence Assertion |
| diagnoses | CaptureDiagnostic | bounded instrumentation subject/scope | Instrumentation Assertion |

Exact wire names remain unfrozen.

## 6. Core graph invariants

### GRAPH-001 — Reference resolution

Every normative object reference in a conforming Receipt MUST either resolve internally within that Receipt or be explicitly represented as an ExternalReference under the Part H external-reference-capable semantics; an unresolved ordinary local reference is invalid and MUST NOT be silently treated as external.

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

Project gate: all of the following are to be resolved before JSON Schema is frozen:

- OQ-001 RESOLVED by Phase 1 Part C: text RequestBinding ranges use Unicode scalar half-open intervals; byte-oriented ranges use byte half-open intervals.
- OQ-002 RESOLVED at core semantic level by Phase 1 Part C: binary/media partial bindings use byte Regions when bytes are exposed; richer media selectors remain profile work.
- OQ-003 RESOLVED by Phase 1 Part B: exact and partial are positive derivation precision states; unknown is not a positive Derivation Assertion.
- OQ-004 RESOLVED at semantic level by Phase 1 Part B: split / concat / truncation use qualified Region lineage; concrete Region selector vocabularies remain open.
- OQ-005 RESOLVED by Phase 1 Part C: core levels are sdk_arguments, provider_payload, prepared_http_body, and unknown; transitions reuse Transform / Derivation and remain explicitly recorded.
- OQ-006 RESOLVED at semantic level by Phase 1 Part C: semantic digest commits a profile-canonicalized structured representation; byte digest commits exact captured bytes; concrete algorithms remain later profile work.
- OQ-007 RESOLVED by Phase 1 Part C: hash-only sublocations are not location-resolved or representation-verified without the target representation or a recognized inclusion proof.
- OQ-008 RESOLVED at semantic level by Phase 1 Part E: ToolInvocation argument provenance uses qualified Derivation over argument Regions; model_supplied / application_supplied / mixed / unknown are bounded coarse summaries over recorded representation ancestry.
- OQ-009 RESOLVED at core semantic level by Phase 1 Part D: one attempt has zero or one terminal assembled ModelOutput; OutputItems are occurrence-identified; streaming chunk evidence is deferred to a future profile while response termination and output capture extent remain separate.
- OQ-010 RESOLVED by Phase 1 Part F: TrustAssertion is subject-local, dimensioned, issuer/policy-scoped, and uses trusted / untrusted / unknown without automatic inheritance.
- OQ-011 RESOLVED by Phase 1 Part F: TaintAssertion uses policy-defined taint_kind plus state/channel/precision; compatible conservative state join is absent < unknown < present and propagation is policy-scoped.
- OQ-012 RESOLVED by Phase 1 Part F: sanitization is explicit, kind/channel/scope-specific, evidence-bounded, and history-preserving; sanitizer names, trust labels, tool success, signatures, and representation changes do not launder taint.
- OQ-013 RESOLVED by Phase 1 Part H: ExternalReference explicitly addresses target Receipt + object identity with optional target payload-digest pin; Resolution Set ambiguity/unresolved state is preserved and cross-Receipt graph invariants remain enforced.
- OQ-014 RESOLVED by Phase 1 Part H: package inventory, Producer-authored Receipt scope, reference closure, and runtime/history completeness are distinct; subset Receipts are first-class and core v0.1 has no generic complete-history bit.
- OQ-015 RESOLVED by Phase 1 Part H: immutable Authenticated Receipt Payload is canonicalized with RFC 8785 JCS, digested with SHA-256, and authenticated by embedded/detached Ed25519 IntegrityEnvelopes over a domain-separated canonical Signing Statement; envelope attachments are outside ARP identity.

## 9. Gate decision

Threat Model: PASS AFTER SECOND REVIEW.

Claim Matrix: PASS AFTER SECOND REVIEW.

Terminology: PASS AFTER SECOND REVIEW.

Core Artifact/Event Graph: PASS AFTER SECOND REVIEW WITH OPEN DESIGN ITEMS.

Specification progress:

~~~text
SourceRef / SourceObservation
        ✓ Phase 1 Part A

Transform / Derivation
        ✓ Phase 1 Part B

RequestSnapshot / RequestBinding
        ✓ Phase 1 Part C

ModelInvocation / ProviderAttempt / ModelOutput
        ✓ Phase 1 Part D

ToolProposal / ToolInvocation / ToolDecision / ToolExecution / ToolResult / EffectObservation
        ✓ Phase 1 Part E

Trust / Taint
        ✓ Phase 1 Part F

Privacy
        ✓ Phase 1 Part G

Integrity / Receipt
        ✓ Phase 1 Part H

Provider Adapter Contract
        ✓ accepted

Tool Adapter Contract
        ✓ accepted

Verifier Contract
        ← final pre-Schema gate
~~~

Project gate: JSON Schema freeze and implementation remain blocked. Phase 1 Parts A-H plus Provider Adapter Contract and Tool Adapter Contract are complete; only the Verifier Contract remains before Schema freeze.
