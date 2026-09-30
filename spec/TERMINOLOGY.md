# C2ATrace v0.1 Terminology

Status: Phase 1 Part A aligned.

This document is primarily definitional. Normative behavior is carried by numbered TM-*, CLAIM-*, GRAPH-*, and SRC-* requirements.

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

An Assertion that one Artifact was produced wholly or partially from another Artifact.

Derivation is distinct from Transform: Transform is an Activity; Derivation is an ancestry claim between Artifacts. A Transform's use and generation relations do not automatically imply exact Derivation.

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

## Observation Extent

Producer-recorded metadata describing how much of the declared capture target a SourceObservation represents.

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

An Activity consuming zero or more Artifacts and producing zero or more Artifacts.

Examples include extract, normalize, redact, filter, split, chunk, rerank, truncate, concat, template, serialize, and application-side tool-invocation preparation.

## RequestSnapshot

An immutable Artifact representing a provider request at one declared capture level.

Candidate capture levels include sdk_arguments, provider_payload, and prepared_http_body. Exact vocabulary remains open under OQ-005.

## Capture Level

The application-observation boundary represented by a RequestSnapshot.

TM-012 governs how strongly a verifier may describe a request relative to its capture level.

## RequestBinding

An Assertion recording that a ModelInputComponent is bound into exactly one target RequestSnapshot at some path and, where defined later, range.

A RequestBinding can be structurally valid without being representation-verified; see CLAIM-002.

## ModelInvocation

A logical Activity representing the application's request to obtain a model result.

It may be associated with zero or more ProviderAttempts.

## ProviderAttempt

An Activity representing one discrete attempt to invoke a Provider through the instrumented boundary.

A ProviderAttempt records an application-side attempt; by itself it does not prove Provider receipt or Provider-internal processing.

## ModelOutput

An Artifact representing application-visible model output associated with a ProviderAttempt.

It excludes hidden reasoning and unknown provider-internal state.

## OutputItem

An abstract Artifact subtype contained in ModelOutput.

Examples include TextOutput, StructuredOutput, ToolProposal, or UnknownOutput.

## ToolProposal

An OutputItem Artifact suggesting a tool invocation.

It is not an execution record and may differ from the effective ToolInvocation.

## ToolInvocation

An immutable Artifact representing the final application-selected tool identity, effective arguments, and execution-relevant metadata immediately before execution.

A ToolInvocation may derive from a ToolProposal, application-supplied data, both, or unknown provenance.

## ToolExecution

An Activity representing an actual attempt to execute a ToolInvocation.

A proposal rejected before execution has no ToolExecution under TM-007.

## ToolResult

An Artifact produced or returned by ToolExecution, such as a function result, MCP result, HTTP response, or error representation.

ToolResult is distinct from ToolExecution under GRAPH-010.

## EffectObservation

An Artifact recording evidence or an observation about possible external state.

It carries or references an evidence basis, which may explicitly be unknown under GRAPH-012.

An EffectObservation is not objective Effect truth.

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
