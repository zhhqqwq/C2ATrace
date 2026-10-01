# C2ATrace v0.1 Terminology

Status: Phase 1 Part E aligned.

This document is primarily definitional. Normative behavior is carried by numbered TM-*, CLAIM-*, GRAPH-*, SRC-*, DRV-*, REQ-*, OUT-*, and TOOL-* requirements.

## Artifact

A recorded data representation with stable identity. Artifact identity is logically immutable: changing the represented data creates a different Artifact identity under GRAPH-002.

## Activity

A recorded process that may use Artifacts and generate Artifacts.

Core Activity types currently include Transform, ModelInvocation, ProviderAttempt, and ToolExecution.

## Assertion

A recorded claim about an object, relation, or property. Assertion presence does not establish external truth.

Core Assertion types currently include Derivation, RequestBinding, TrustAssertion, and TaintAssertion. Source alias and source-origin relationships are also treated as assertions when recorded.

## Reference

A structural object that identifies or locates something without itself being the immutable observed representation.

SourceRef is the core Reference type.

## Scope

A structural object grouping related records. Run is the core Scope type.

## Package

A portable container of records. Receipt is the core Package type.

## Provenance

Recorded information describing origins, uses, generations, transformations, and relationships associated with Artifacts and Activities.

C2ATrace provenance is recorded provenance, not guaranteed ground truth.

## Lineage

An explicit path or graph of provenance relations describing how recorded data representations evolved.

Lineage answers how recorded data reached a point. It does not explain why a model decided something.

## Derivation

A qualified positive Assertion describing direct representation ancestry through one Transform.

The Part B semantic form has exactly one target output Artifact or Region, exactly one generating Transform, and one or more contributing input Artifacts or Regions. A binary derived_from edge is only a one-input display shorthand.

Derivation is distinct from Transform: Transform is an Activity; Derivation is an ancestry Assertion. A Transform's use and generation relations do not automatically imply Derivation.

See DRV-001 through DRV-010.

## Exact Derivation

A positive direct Derivation whose claimed output scope has complete recorded origin accounting at its asserted granularity.

Exact Derivation does not imply byte equality, reversibility, semantic equivalence, model causality, or external completeness.

See DRV-008.

## Partial Derivation

A positive direct Derivation establishing some representation ancestry while leaving mapping or contributor coverage incomplete.

Partial is positive ancestry; it is not uncertainty about whether any contribution occurred.

See DRV-009.

## Unknown Derivation

A knowledge state in which contribution cannot be established.

Unknown Derivation is not represented as a positive Derivation Assertion. The relevant Transform use remains recorded with a justified usage role and no fabricated derivation edge.

See DRV-010.

## Region

A selector over a subrepresentation of one immutable Artifact.

A Region is interpreted only together with its Artifact identity, representation basis, and selector/coordinate scheme.

Concrete selector vocabularies remain unfrozen.

See DRV-016 and DRV-017.

## Transform-generated Region

An output Region explicitly recorded as introduced by a Transform rather than attributed to upstream representation content.

It is distinct from a derived Region and must not be silently attributed to source inputs.

See DRV-020.

## Recorded Ancestry Path

A transitive graph path formed from direct Derivation Assertions.

Recorded ancestry reachability is not itself a direct Derivation Assertion, and exact Region mappings compose only under the Part B precision rules.

See DRV-023 through DRV-026.

## Causality

A claim that one factor caused another decision or event. C2ATrace core v0.1 does not model LLM-internal causal responsibility.

## Inclusion

A recorded claim that a ModelInputComponent representation is present within a specific RequestSnapshot.

Inclusion is represented by RequestBinding. CLAIM-002 distinguishes structural validity from representation-verified inclusion.

## SourceRef

A Reference that provides C2ATrace's protocol-level identity for one recorded logical source inside a resolution scope.

SourceRef identity is distinct from locator equality, content equality, real-world resource identity, and external source-version identity.

The external truth of the Producer's source grouping is not established merely because records share a SourceRef.

See SRC-001 through SRC-005 and SRC-022.

## Source Locator

An address, identifier string, or access reference associated with a SourceRef or a particular SourceObservation acquisition.

Examples include URLs, app-specific URIs, file URIs, user-message identifiers, and RAG-document identifiers.

A locator is not the protocol-level identity key for SourceRef.

## Locator Resolution Trace

Producer-recorded information describing how a requested locator resolved through zero or more redirect or resolver steps to an effective locator.

A Locator Resolution Trace describes an access path, not source-identity equivalence.

See SRC-006 and SRC-007.

## Source Alias Assertion

A Producer assertion that distinct SourceRefs or locators are treated as aliases for some application purpose.

An alias assertion does not collapse SourceRef identities or prior provenance histories in core v0.1.

See SRC-008.

## SourceObservation

An immutable Artifact representing one recorded capture occurrence of a representation associated with exactly one SourceRef.

A SourceObservation is not a universal source-version number. Separate capture occurrences can have separate SourceObservation identities even when their content commitments or external validators match.

The same previously captured SourceObservation can be referenced again when no new capture occurrence is recorded.

See SRC-009 through SRC-012.

## Capture Occurrence

The Producer-recorded event boundary that gives rise to a SourceObservation.

Capture occurrence identity is distinct from content equality and external version metadata.

Part A does not define a separate CaptureOccurrence protocol object; the term describes SourceObservation identity semantics.

## Source Version Hint

External metadata reported or observed for a source representation, such as an ETag, Last-Modified value, revision ID, database row version, document version, object generation, or commit identifier.

A Source Version Hint is observation metadata rather than SourceObservation identity.

Core v0.1 does not assign generic total-order semantics to such hints.

See SRC-013 and SRC-014.

## Content Commitment

Metadata binding a SourceObservation to a declared representation under a specified commitment method and representation basis.

A matching compatible Content Commitment supports a representation-level match claim. It does not establish SourceRef identity, SourceObservation identity, capture-occurrence identity, locator equality, or external origin.

See SRC-015 through SRC-018.

## Representation Basis

A declaration of the representation to which a Content Commitment applies.

Examples may include the captured byte sequence or an explicitly defined canonical encoding of captured text.

Representation Basis is necessary to determine whether two commitments are comparable.

## Declared Capture Target

The Producer-described representation scope against which SourceObservation extent is stated.

Examples include a selected HTTP response representation, a file object, a database projection, an API page, or another explicitly bounded representation.

The declared scope is Producer-authored metadata and does not independently prove completeness of any broader external resource.

## Observation Extent

Producer-recorded metadata describing how much of the Declared Capture Target a SourceObservation represents.

Conceptually this may distinguish complete-relative-to-target, partial, and unknown observations.

"Complete" is still a Producer assertion relative to the declared capture target, not proof that the entire external resource was captured.

See SRC-019 and SRC-020.

## ContextFragment

An Artifact representing a discrete piece of contextual data that may participate in model input construction.

ContextFragment is a ModelInputComponent subtype.

## ModelInputComponent

An abstract Artifact category for application-visible model input components.

Examples may include ContextFragment, Instruction, ToolDefinition, StructuredConstraint, Media, ProviderParameter, or UnknownInput.

## Transform

An Activity that can use Artifacts, generate new Artifacts, and select or forward existing Artifacts.

Generation creates a new Artifact representation. Selection/forwarding preserves an existing Artifact identity.

Examples include extract, normalize, redact, filter, split, chunk, rerank, truncate, concat, template, serialize, and application-side tool-invocation preparation.

See DRV-001 and DRV-013 through DRV-015.

## Usage Role

Producer-asserted qualification of how an Artifact was used by a Transform.

Part B defines the conceptual roles data, control, mixed, and unknown.

A Usage Role is not a positive Derivation Assertion. In particular, control use does not by itself make the input an ancestor of generated representation content.

See DRV-011 and DRV-012.

## Selection / Forwarding

A Transform relation indicating that an already-existing Artifact was chosen or passed downstream without being generated as a new representation.

Selection/forwarding preserves Artifact identity. A new wrapper, manifest, list, or aggregate receives its own Artifact identity.

See DRV-013 through DRV-015.

## RequestSnapshot

An immutable Artifact representing one recorded request representation at exactly one Capture Level.

Every RequestSnapshot has exactly one Capture-Scope Owner: one ModelInvocation or one ProviderAttempt. Different capture levels remain different RequestSnapshot identities even when their committed representations match.

See REQ-003 through REQ-010.

## Capture Level

The application-observation boundary represented by a RequestSnapshot.

Core Part C levels are sdk_arguments, provider_payload, prepared_http_body, and unknown.

sdk_arguments is the structured representation at the instrumented SDK/adapter entry boundary. provider_payload is the provider-specific structured payload after recorded application-visible preparation. prepared_http_body is the captured body-byte representation at the instrumented application-side transport boundary.

Capture Level does not establish Provider receipt or provider-internal prompt state.

See TM-012 and REQ-011 through REQ-014.

## Capture-Scope Owner

The ModelInvocation or ProviderAttempt whose scope contains a RequestSnapshot capture.

Invocation-scoped snapshots can be reused only by attempts belonging to that same ModelInvocation. Attempt-scoped snapshots are isolated to their owning attempt.

## Effective RequestSnapshot

The RequestSnapshot designated as the effective representation for one ProviderAttempt at one Capture Level.

One ProviderAttempt has at most one effective snapshot per level, although intermediate snapshots can exist in request-preparation history.

## RequestBinding

An occurrence-specific Assertion that one ModelInputComponent scope appears at one RequestLocation in exactly one RequestSnapshot.

RequestBinding is capture-level-local. It does not automatically propagate across RequestSnapshot transitions.

See REQ-015 through REQ-019 and REQ-043 through REQ-045.

## RequestLocation

The target scope within one RequestSnapshot.

Part C semantic forms are whole_snapshot, structured_value, structured_text_region, and byte_region. These are semantic categories rather than frozen JSON fields.

## Request Path

A scheme-qualified selector into a structured RequestSnapshot.

For snapshots using the JSON data model, the core interoperable path scheme is json_pointer. A path to a JSON string selects the decoded string value rather than lexical serialized JSON bytes.

See REQ-020 through REQ-023.

## Request Text Region

A RequestBinding Region over decoded text using Unicode scalar value offsets and half-open [start,end) intervals.

The unit is not UTF-8 bytes, UTF-16 code units, grapheme clusters, or JSON escape characters.

See REQ-024 through REQ-026.

## Request Byte Region

A RequestBinding Region over an exact byte-oriented representation using byte offsets and half-open [start,end) intervals.

See REQ-027 through REQ-031.

## Semantic Digest

A digest over canonical bytes produced from a structured RequestSnapshot by an explicitly identified semantic canonicalization profile.

Semantic-digest equality does not imply byte equality.

See REQ-032 through REQ-036.

## Byte Digest

A digest over the exact declared captured byte sequence of a byte-oriented RequestSnapshot.

A prepared_http_body Byte Digest does not prove that the Provider received those bytes.

See REQ-033 through REQ-036 and REQ-046.

## Binding Structural Validity

Evidence that the RequestBinding record, references, location form, path syntax, and Region declarations are structurally valid without establishing that the target sublocation exists in unavailable content.

## Binding Location Resolution

Evidence that the target RequestLocation exists and is in bounds in the target RequestSnapshot, established from the target representation or a recognized proof/profile.

## Binding Commitment Match

Evidence that compatible commitments for the claimed source and target scopes are equal. Commitment matching is distinct from proving that a claimed sublocation is actually contained in a larger hidden RequestSnapshot.

## Binding Representation Verification

Evidence that the verifier can resolve the RequestLocation and verify the claimed source-to-target representation relationship using the required representations or a recognized proof profile.

See CLAIM-002 and REQ-037 through REQ-042.

## ModelInvocation

A logical Activity representing one Producer-recorded application request for a model result.

Its identity is occurrence-based rather than request-content-based. It can have zero or more ProviderAttempts, own invocation-scoped RequestSnapshots, and optionally designate one accepted ModelOutput.

Retry/failover/hedge grouping is Producer-recorded orchestration rather than something inferred from equal requests or timestamps.

See OUT-001 through OUT-005 and OUT-012 through OUT-018.

## ProviderAttempt

An Activity representing one discrete application-observed attempt to invoke a Provider.

Every ProviderAttempt belongs to exactly one ModelInvocation. It can designate effective RequestSnapshots at zero or more capture levels and can own zero or one core ModelOutput.

Its existence does not prove Provider receipt or provider-internal processing.

See REQ-001 through REQ-008 and OUT-003 through OUT-014.

## Attempt Disposition

The Producer-recorded terminal classification of a ProviderAttempt.

Core Part D conceptual terminal values are completed, failed, timeout, cancelled, interrupted, and unknown.

Attempt Disposition describes the application-observed attempt lifecycle and is separate from response completion and output capture completeness.

## Attempt Relationship

A Producer-asserted orchestration relationship among ProviderAttempts within one ModelInvocation, such as retry_of, failover_from, or hedged_with.

Retry/failover predecessor relationships are distinct from timestamp order and preserve concurrent/hedged execution semantics.

See OUT-012, OUT-013, and OUT-051 through OUT-053.

## Accepted ModelOutput

The optional ModelOutput selected by a ModelInvocation as its application-accepted logical result.

At most one accepted ModelOutput exists in core v0.1. Acceptance does not imply response completion or output capture completeness.

See OUT-015 through OUT-018.

## Invocation-Requested Model

The Producer-recorded model label requested or intended at the logical ModelInvocation level.

It is not proof of provider-internal model identity.

## Attempt-Effective Requested Model

The model label visible in the effective request representation for a specific ProviderAttempt.

It can differ between retries/failovers and can be representation-verified when the relevant RequestSnapshot is available.

## Provider-Reported Model

A model identifier reported in application-visible provider/SDK response metadata.

It remains reported evidence and is not provider-internal model attestation.

See OUT-019 through OUT-022.

## ModelOutput

An immutable Artifact representing the zero-or-one terminal assembled application-visible model-result representation captured for one ProviderAttempt.

Core ModelOutput is not the raw provider wire response and does not expose provider-internal state.

See OUT-023 through OUT-032.

## Response Termination

Producer-recorded evidence about whether the application observed the model response reach its normal completion boundary.

Core conceptual values are complete, incomplete, and unknown.

Response Termination is independent of Output Capture Extent.

## Output Capture Extent

Producer-recorded evidence about whether instrumentation captured all application-visible model-result content within the declared adapter-boundary capture scope.

Core conceptual values are complete, partial, and unknown.

Complete capture at this boundary does not establish provider-internal completeness.

See OUT-027 through OUT-032.

## OutputItem

An immutable, occurrence-identified Artifact subtype contained in exactly one ModelOutput.

Core conceptual kinds are text, structured, tool_proposal, and unknown.

Identical item content does not merge occurrence identities.

See OUT-033 through OUT-039.

## TextOutput

An OutputItem containing captured application-visible text. It is not hidden reasoning or token-level internal generation history.

See OUT-046.

## StructuredOutput

An OutputItem containing a captured application-visible structured result.

Independent schema validation can establish representation/schema conformance when applicable, but does not establish semantic correctness or provider-internal generation facts.

See OUT-047.

## Streaming Assembly

The core Part D model in which streaming deltas, if any, are assembled into the terminal immutable ModelOutput and OutputItems.

Chunk-level/wire-level evidence is deferred to a future profile. Absence of chunk records does not prove non-streaming behavior.

See OUT-039 through OUT-043.

## ToolProposal

An immutable OutputItem Artifact representing one application-visible proposal to invoke a tool.

Its identity is occurrence-based. Provider/SDK tool-call identifiers are metadata rather than substitutes for ToolProposal identity.

ToolProposal does not imply application authorization, ToolInvocation, or ToolExecution.

See TOOL-001 through TOOL-004.

## ToolInvocation

An immutable Artifact representing the effective application-selected tool call immediately before execution can begin.

It records the effective tool identifier, effective arguments, and applicable execution-relevant invocation representation. ToolInvocation can derive from ToolProposal and application/runtime/policy Artifacts, or can exist without ToolProposal ancestry.

The same immutable ToolInvocation can be attempted by multiple ToolExecutions when it is actually reused unchanged.

See TOOL-005 through TOOL-010 and TOOL-028 through TOOL-031.

## Tool Argument Provenance

Qualified Derivation over ToolInvocation argument Regions.

For JSON-model arguments, core interoperable argument paths use json_pointer.

Argument provenance can preserve ToolProposal, application, runtime, policy, external, or transform-generated contributors without replacing exact lineage with a coarse label.

See TOOL-011 through TOOL-019.

## Argument Provenance Summary

A bounded coarse summary over Tool Argument Provenance.

Core Part E classes are model_supplied, application_supplied, mixed, and unknown.

model_supplied means ToolProposal-side representation ancestry at the application-visible proposal boundary; it does not establish hidden model-internal causality.

See TOOL-012 through TOOL-016.

## ToolDecision

A core Assertion recording an application/policy decision about exactly one ToolProposal or ToolInvocation.

Core conceptual values are allow, deny, and unknown.

ToolDecision is not ToolExecution. Allow does not prove execution; deny does not erase a separately recorded later execution.

ToolDecision identities are occurrence-based.

See TOOL-021 through TOOL-027 and TOOL-061 through TOOL-062.

## ToolExecution

An Activity representing one actual attempt to execute exactly one ToolInvocation.

One ToolInvocation can have zero or more ToolExecutions. Each execution has occurrence identity and an application/runtime-observed lifecycle.

Core conceptual terminal dispositions are completed, failed, timeout, cancelled, interrupted, and unknown.

Completed execution does not establish semantic success, external Effect, or Outcome success.

See TOOL-028 through TOOL-035.

## ToolExecution Relationship

A Producer-asserted orchestration relation such as retry_of, replay_of, or duplicate_of between ToolExecution occurrences.

Such relations can span changed ToolInvocations and do not imply ToolInvocation equality or external effect cardinality.

Retry/replay predecessor relations are acyclic within the resolution scope.

See TOOL-049 through TOOL-056.

## Idempotency Metadata

Execution-relevant metadata intended to support duplicate suppression or idempotent remote handling.

Presence or equality of an idempotency key does not establish remote support, correct enforcement, exactly-once execution, or exactly-once Effect.

See TOOL-054 through TOOL-056.

## ToolResult

An immutable Artifact representing the zero-or-one terminal assembled application-visible result representation associated with one ToolExecution.

It can contain normal returns, errors, remote identifiers, status fields, and runtime metadata.

Tool-reported success/status is evidence about the returned representation and does not establish external Effect truth.

See TOOL-036 through TOOL-041.

## ToolResult Capture Extent

Producer-recorded evidence about whether all application-visible result content within the declared tool-runtime capture scope was captured.

Core conceptual values are complete, partial, and unknown.

Complete capture does not establish complete remote state or objective truth.

## EffectObservation

An immutable Artifact recording a bounded observation/evidence claim about possible external state.

It is not the external Effect itself and is not OutcomeVerification.

Core Part E conceptual evidence bases are execution_result, separate_observation, external_attestation, and unknown.

See TOOL-042 through TOOL-048.

## Effect Evidence Basis

The recorded basis supporting an EffectObservation.

execution_result means the effect claim is supported by the execution's ToolResult; separate_observation means a distinct later observation supports it; external_attestation refers to separately identified attestation evidence; unknown preserves lack of basis knowledge.

None of these labels alone establishes objective external truth.

## Effect

A possible real external state change.

Core v0.1 primarily records EffectObservation rather than claiming direct knowledge of objective Effect truth.

## Outcome

A desired postcondition or goal state. Outcome verification is outside core v0.1.

## Trust

A Producer- or policy-issued assessment.

Trust is represented through TrustAssertion and is not an intrinsic cryptographic property of a source.

## TrustAssertion

An Assertion associating a subject with a trust label and the identity, policy, or basis that asserted it.

Exact vocabulary and subject rules remain open under OQ-010.

## Taint

Conservative provenance metadata indicating that an object's recorded provenance envelope contains ancestry with a relevant property.

Taint is distinct from maliciousness, exact Derivation, and causal responsibility.

## TaintAssertion

An Assertion recording taint state, basis, and later-defined propagation semantics for a subject.

Exact lattice and propagation rules remain open under OQ-011 and OQ-012.

## Unknown

A first-class state meaning the available record does not justify a more specific claim.

Unknown is semantically distinct from false, safe, trusted, untrusted, empty, and an accidentally missing field.

For source identity, distinct unknown SourceRefs remain distinct recorded logical identities unless an explicit relationship is later asserted.

## Run

A Scope grouping logically related C2ATrace records.

Run does not imply complete capture, a single process, a single thread, a single Provider, or a single model call.

## Receipt

A Package containing some C2ATrace records plus integrity-related metadata.

A Receipt may represent all or part of a Run. Until OQ-013 defines external-reference semantics, normative internal references in a conforming Receipt are self-contained under GRAPH-001.

## IntegrityEnvelope

Integrity metadata describing commitments, digests, signatures, signer/key references, and authenticated scope for a Receipt or other defined representation.

Its cryptographic structure is not frozen in Phase 0. Signing scope and embedding rules remain open under OQ-015.

## Action

A non-normative documentation umbrella term.

Action is intentionally not a core protocol object because ToolProposal, ToolInvocation, ToolExecution, ToolResult, EffectObservation, and real external Effect have different semantics.
