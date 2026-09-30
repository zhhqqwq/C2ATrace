# C2ATrace v0.1 Terminology

Status: Phase 0 baseline.

## Provenance

Recorded information describing origins, transformations, uses, generations, and relationships associated with artifacts and activities. C2ATrace provenance is recorded provenance, not guaranteed ground truth.

## Lineage

An explicit path or graph of provenance relations describing how recorded data representations evolved. Lineage answers how recorded data reached a point; it does not explain why a model decided something.

## Derivation

An explicit assertion that one Artifact was produced wholly or partially from another Artifact. Derivation MUST NOT be inferred merely because an activity used A and generated B. If derivation cannot be established, it remains unknown or is omitted.

## Causality

A claim that one factor caused another decision or event. C2ATrace v0.1 does not model LLM-internal causality. Provenance dependency is not causal responsibility.

## Inclusion

A claim that a ModelInputComponent representation appears within a specific RequestSnapshot. Inclusion is expressed by RequestBinding and is always relative to a capture level.

## SourceRef

A logical source identity or locator, such as a URL, app URI, user message URI, or RAG document URI. It does not identify the exact bytes observed during a particular run.

## SourceObservation

An immutable Producer-recorded representation claimed to have been observed from a SourceRef during execution. One SourceRef may have many SourceObservations.

## Artifact

A recorded data representation with stable identity. Once identified, an Artifact SHOULD be immutable. A changed representation SHOULD receive a new identity.

## Activity

A recorded process that may use Artifacts and generate Artifacts. Examples include Transform, ProviderAttempt, and ToolExecution.

## Assertion

A recorded claim about an object, relation, or property. Assertion presence does not itself establish external truth.

## ContextFragment

An immutable Artifact representing a discrete piece of contextual data that may participate in model input construction.

## ModelInputComponent

The generalized abstraction for application-visible model input. It may include ContextFragment, Instruction, ToolDefinition, StructuredConstraint, Media, ProviderParameter, or UnknownInput.

## Transform

An Activity consuming zero or more Artifacts and producing zero or more Artifacts. Examples include extract, normalize, redact, filter, split, chunk, rerank, truncate, concat, template, and serialize.

## RequestSnapshot

An immutable representation of a provider request at a declared capture level, such as sdk_arguments, provider_payload, or prepared_http_body.

## Capture Level

The layer at which a RequestSnapshot was observed. C2ATrace claims MUST NOT be stronger than the capture level permits.

## RequestBinding

A qualified assertion that a ModelInputComponent appears in exactly one target RequestSnapshot at a recorded path and, where supported, range.

## ModelInvocation

A logical application-level request for a model result. A ModelInvocation may produce zero or more ProviderAttempts.

## ProviderAttempt

A discrete attempt to submit a provider request. Retries are separate ProviderAttempts.

## ModelOutput

An application-visible output Artifact associated with a ProviderAttempt. It does not represent hidden reasoning or provider-internal state.

## OutputItem

An independently identifiable item inside ModelOutput, such as TextOutput, StructuredOutput, ToolProposal, or UnknownOutput.

## ToolProposal

A model-output Artifact suggesting a tool invocation. A proposal is not an execution record.

## ToolInvocation

An immutable Artifact representing the final application-selected tool identity, arguments, and execution-relevant metadata immediately before execution.

## ToolExecution

An Activity representing an actual attempt to execute a ToolInvocation. If execution never begins, ToolExecution MUST NOT be created solely to represent rejection.

## ToolResult

An Artifact produced or returned by ToolExecution, such as a function result, MCP result, HTTP response, or error representation.

## EffectObservation

An Artifact recording evidence suggesting an external state or side effect. It MUST preserve an observation basis or explicitly record that the basis is unknown.

## Effect

A possible real external state change. C2ATrace v0.1 primarily records EffectObservation rather than claiming direct knowledge of objective Effect truth.

## Outcome

A desired postcondition or goal state. Outcome verification is outside the v0.1 core.

## Trust

A Producer- or policy-issued assessment. Trust is an assertion, not an intrinsic cryptographic property.

## TrustAssertion

A record connecting a subject to a trust label and the identity or policy basis that asserted it.

## Taint

Conservative provenance metadata indicating that an object's provenance envelope contains ancestry with a relevant property. Taint is not maliciousness, exact derivation, or causality.

## TaintAssertion

A record of taint state, basis, and propagation rule for a subject.

## Unknown

A first-class state meaning the available record does not justify a more specific claim. Unknown is not false, safe, trusted, untrusted, empty, or a missing value.

## Run

A logical grouping of related C2ATrace records. A Run does not imply complete capture, one process, one thread, one provider, or one model call.

## Receipt

A portable provenance package containing some C2ATrace records plus integrity metadata. A Receipt may contain all or only part of a Run.

## Action

A non-normative documentation umbrella term. Action is intentionally not a v0.1 core protocol object because ToolProposal, ToolInvocation, ToolExecution, and external Effect are distinct concepts.