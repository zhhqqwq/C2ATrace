# C2ATrace v0.1 Terminology

Status: Provider Adapter Contract aligned.

This document is primarily definitional. Normative behavior is carried by numbered TM-*, CLAIM-*, GRAPH-*, SRC-*, DRV-*, REQ-*, OUT-*, TOOL-*, TRUST-*, TAINT-*, PRIV-*, RCPT-*, INTG-*, and PAD-* requirements.

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

## Provider Adapter

Instrumentation at an application-visible boundary through which the application requests a model result and/or observes provider-facing request preparation and model-result delivery.

A Provider Adapter can combine logical-call, request-builder, serialization/transport-body, response-result, and streaming-consumption hooks, but its claim ceiling is limited to the boundaries it actually observes.

Provider Adapter evidence does not establish Provider receipt or provider-internal state by default.

See PAD-001 through PAD-008 and PAD-080 through PAD-084.

## Provider Adapter Conformance Declaration

Metadata declaring the adapter's logical invocation boundary, ProviderAttempt boundary, supported RequestSnapshot capture levels, output/streaming capability, orchestration visibility, privacy capability, and implementation identity/version metadata.

The declaration describes intended capability, not proof that every runtime occurrence was successfully captured.

## CaptureDiagnostic

An occurrence-identified Assertion describing instrumentation state for one bounded subject/scope and capture slot.

Core conceptual states are observed, partial, unavailable, unsupported, bypass_detected, and unknown.

CaptureDiagnostic is not a provenance edge, Provider attestation, or instrumentation completeness certificate. Conflicting diagnostics are preserved absent explicit resolution evidence.

See PAD-009 through PAD-013 and PAD-085 through PAD-094.

## Adapter Metadata Origin

A bounded origin classification for semantics-bearing provider-adapter metadata.

Core Provider Adapter conceptual classes are application_supplied, adapter_observed, provider_reported, adapter_derived, and unknown.

The class describes evidence origin, not factual truth.

See PAD-062 through PAD-065 and PAD-092.

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

A local Producer-/policy-issued assessment about one explicit subject and one Trust Dimension.

Trust is not objective truth, is not an intrinsic cryptographic property, and does not automatically inherit across provenance relations.

## TrustAssertion

An occurrence-identified Assertion containing one subject, one Trust Dimension, one Trust State, asserted_by identity (or unknown), policy context (or unknown), and optional evidence/basis references.

Core Trust States are trusted, untrusted, and unknown.

TrustAssertions are local. SourceRef trust does not automatically apply to SourceObservation; input trust does not automatically apply to derived/request/output/tool/effect objects.

See TRUST-001 through TRUST-025.

## Trust Dimension

The policy-scoped dimension being assessed by a TrustAssertion.

Examples may include source authority, content reliability, runtime integrity, policy approval, or application-defined dimensions.

Core v0.1 does not define one universal "trusted" dimension.

## Trust State

One of trusted, untrusted, or unknown under one issuer/policy Trust Dimension.

The state is an asserted assessment and not objective truth.

## Taint

Policy-scoped conservative metadata describing an active property over one subject scope.

Taint is distinct from maliciousness, objective safety, Trust, exact Derivation, and causal responsibility.

## TaintAssertion

An occurrence-identified Assertion containing a subject scope, taint_kind, Taint State, Taint Channel, Taint Precision, asserted_by identity (or unknown), policy context (or unknown), and a direct/propagated/sanitization/unknown basis.

See TAINT-001 through TAINT-059.

## Taint Kind

A policy-defined identifier for the property tracked by TaintAssertion.

Core v0.1 standardizes taint mechanics rather than a universal catalogue of taint kinds. Examples can include sensitive, secret, user_controlled, untrusted_source, or application-defined properties.

## Taint State

One of present, absent, or unknown.

present means the policy asserts the active taint kind applies somewhere in the declared scope. absent means the policy asserts absence under its evidence/scope. unknown means neither stronger state is justified.

absent does not mean objectively clean, and present does not mean malicious.

## Taint Channel

One of content, control, mixed, or unknown.

content tracks representation ancestry. control tracks policy-defined influence through explicit control-use/activity relations without claiming representation contribution. mixed requires both channels.

## Taint Precision

One of exact, conservative, or unknown.

exact means the asserted scope is not intentionally broader than the provenance/mapping evidence used. conservative can over-approximate the tainted scope. Precision does not upgrade factual truth.

## Conservative Taint Lattice

For compatible assertions under one policy identity, taint_kind, channel, and comparable subject scope, the conservative state order is:

~~~text
absent < unknown < present
~~~

Assertions from different or unknown policy contexts are not automatically joined.

## Sanitization Discharge

A policy-scoped TaintAssertion with basis=sanitization that records downstream taint discharge/reclassification for a specific taint kind, channel, and scope through an identified Transform and policy rule.

Sanitization changes active downstream taint state; it does not delete upstream provenance or prior taint assertions, and it does not create Trust.

See TAINT-035 through TAINT-045.

## Privacy Disclosure Scope

The concrete Receipt or exported C2ATrace package relative to which representation disclosure is evaluated.

Privacy is package-relative. A representation withheld in one Receipt can be fully disclosed in another without changing the underlying Artifact identity.

## Privacy Profile

A package-relative description of how a representation scope is disclosed and what commitment capability remains.

Core Part G named presets are full, hash_only, hmac, redacted, mixed, and unknown. These are compositional disclosure presets rather than intrinsic Artifact properties.

See PRIV-001 through PRIV-019.

## full Privacy Profile

The original subject representation for the declared scope is disclosed in the evaluated package.

full does not establish external truth, completeness, confidentiality, or provenance beyond the underlying Artifact semantics.

## hash_only Privacy Profile

The original subject representation is withheld from the evaluated package while an unkeyed commitment over an explicit representation basis is disclosed.

hash_only is not a confidentiality guarantee and can allow low-entropy candidate enumeration and equality linkability.

See PRIV-007 through PRIV-008 and PRIV-025 through PRIV-027.

## hmac Privacy Profile

The original subject representation is withheld while a keyed commitment/MAC over an explicit representation basis is disclosed.

Candidate verification requires the corresponding secret capability. Independent authorized verification is possible without making verification public.

Stable keyed commitments can still create linkability.

See PRIV-009 through PRIV-010 and PRIV-028 through PRIV-033.

## redacted Privacy Profile

A package disclosure in which provenance-bearing replacement content is represented as a distinct redacted derivative Artifact produced through an explicit Transform/Derivation from the original Artifact.

The redacted representation does not replace the original Artifact identity and does not verify the hidden original.

See PRIV-011, PRIV-018, and PRIV-034 through PRIV-039.

## Privacy Commitment

A commitment associated with one explicit Artifact or Region representation scope and one declared representation basis/profile.

Commitment equality is bounded evidence and does not establish external origin, hidden sublocation membership, Provider receipt, or Artifact occurrence identity.

## Privacy Verifier Capability

The actual evidence/capability set available to a verifier, such as original representation, candidate representation, keyed-commitment secret, compatible commitment profile, or recognized inclusion/redaction proof.

Privacy withholding can preserve or reduce verification strength; it never strengthens a claim.

See PRIV-070 through PRIV-075.

## Withheld Representation

A representation known or asserted to exist in the underlying provenance record but not disclosed in the evaluated package.

Withheld is distinct from empty, null, false, zero, absent, and unknown existence.

## Presentation Mask

A user-interface or display-only replacement such as "***" or "[REDACTED]" that is not itself the underlying provenance-bearing representation unless explicitly recorded as such.

A presentation mask must not be treated as the effective runtime value.

## Unknown

A first-class state meaning the available record does not justify a more specific claim.

Unknown is semantically distinct from false, safe, trusted, untrusted, empty, and an accidentally missing field.

For source identity, distinct unknown SourceRefs remain distinct recorded logical identities unless an explicit relationship is later asserted.

## Run

A Scope grouping logically related C2ATrace records.

Run does not imply complete capture, a single process, a single thread, a single Provider, or a single model call.

## Receipt

A Package identity centered on one immutable Authenticated Receipt Payload (ARP), with zero or more non-identity-defining IntegrityEnvelope attachments.

A Receipt may represent all or part of a Run. Subset Receipts are first-class and do not imply complete runtime history.

See RCPT-001 through RCPT-011.

## Receipt Presentation

A concrete transport serialization of one Receipt ARP together with some selected embedded/detached IntegrityEnvelope material.

Different Presentations of the same unchanged ARP/Receipt identity do not create new Receipt identity.

## Authenticated Receipt Payload (ARP)

The complete semantics-bearing Receipt payload committed by the baseline digest/signature profile.

It includes Receipt identity, inventory, included records, ExternalReferences, ReceiptLinks, scope/privacy metadata, and other semantics-bearing fields. IntegrityEnvelope signature values/attachments are outside the ARP.

## Receipt Inventory

The explicit or deterministic membership set of records included in one ARP.

Inventory completeness is package-local and does not establish Run/runtime/history completeness.

## Receipt Scope Descriptor

Producer-authored metadata describing the intended selection context of a Receipt, such as Run, root objects, time window, or application selection.

Scope does not imply complete coverage.

## ExternalReference

An explicit cross-Receipt Reference form locating a target by target Receipt identity plus target object identity, with an optional target Receipt payload-digest pin.

The tuple is a package-location address; it does not redefine the underlying C2ATrace object identity.

Unpinned resolution is identifier-based; digest pinning binds an exact target ARP commitment when matched.

See RCPT-012 through RCPT-030 and RCPT-049 through RCPT-050.

## Resolution Set

The Receipts and external resolution material actually available to one verifier invocation.

External-reference resolution, ambiguity, and closure are relative to this supplied set/capability.

## Reference Closure

The state in which all explicit normative references required for a given verification operation are resolvable in the supplied Resolution Set.

Reference closure is not runtime/capture/history completeness.

## ReceiptLink

Digest-pinned package-level integrity/linkage metadata included in the current ARP, pointing to a prior Receipt identity and payload digest.

ReceiptLink is distinct from object-level ExternalReference. Multiple prior links are allowed and create partial order, not global complete history.

See RCPT-031 through RCPT-045.

## IntegrityEnvelope

Occurrence-identified integrity metadata authenticating a defined Receipt ARP commitment under a signature profile.

IntegrityEnvelopes can be embedded or detached and multiple envelopes can authenticate one ARP. Envelope attachment count does not define Receipt identity.

## Receipt Payload Digest

The computational commitment to the canonical ARP under the selected canonicalization/digest profile.

Baseline v0.1 uses RFC 8785 JCS UTF-8 canonical bytes followed by SHA-256.

Digest match is not factual truth, completeness, or Receipt identity.

## Signing Statement

The deterministic domain-separated statement authenticated by an IntegrityEnvelope signature.

Baseline v0.1 canonicalizes the Signing Statement with RFC 8785 JCS to UTF-8 and signs it with Ed25519. It binds Receipt identity, payload digest, algorithm/profile identifiers, verification-key reference, envelope identity, and interpreted signed envelope metadata.

## Receipt Integrity Status

The multidimensional result of canonicalization, digest, signature, key resolution, reference/link resolution, and related checks.

Core v0.1 does not collapse these dimensions into one generic fully-verified boolean.

## Runtime/History Completeness

The claim that all relevant runtime/capture/history records in a defined scope are present.

Ordinary Receipt inventory, reference closure, signatures, or ReceiptLinks do not establish this claim.

## Unknown

A first-class state meaning the available record does not justify a more specific claim.

## Action

A non-normative documentation umbrella term.

Action is intentionally not a core protocol object because ToolProposal, ToolInvocation, ToolExecution, ToolResult, EffectObservation, and real external Effect have different semantics.
