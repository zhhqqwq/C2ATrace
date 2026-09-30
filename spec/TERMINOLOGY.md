# C2ATrace v0.1 Terminology

Status: Phase 0 baseline, second-review revision.

This document is primarily definitional. Normative behavior is carried by numbered TM-*, CLAIM-*, and GRAPH-* requirements.

## Artifact

A recorded data representation with stable identity. Artifact identity is logically immutable: changing the represented data creates a different Artifact identity under GRAPH-002.

## Activity

A recorded process that may use Artifacts and generate Artifacts.

Core Activity types currently include Transform, ModelInvocation, ProviderAttempt, and ToolExecution.

## Assertion

A recorded claim about an object, relation, or property. Assertion presence does not establish external truth.

Core Assertion types currently include Derivation, RequestBinding, TrustAssertion, and TaintAssertion.

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

A logical source identity or locator, such as a URL, app URI, user-message URI, or RAG-document URI.

SourceRef is a Reference, not the exact bytes observed during a particular run.

## SourceObservation

An immutable Artifact containing the Producer-recorded representation claimed to have been observed from a SourceRef during execution.

One SourceRef may have multiple SourceObservations.

The digest of a SourceObservation can bind supplied bytes without independently proving that those bytes originated from the claimed SourceRef.

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
