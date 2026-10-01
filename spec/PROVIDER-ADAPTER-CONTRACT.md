# C2ATrace v0.1 — Provider Adapter Contract

Status: DRAFT FOR ADVERSARIAL REVIEW.

Scope: provider-adapter responsibility and visibility boundary; capture capability declaration; CaptureDiagnostic; ModelInvocation / ProviderAttempt / RequestSnapshot / ModelOutput capture responsibilities; core capture levels; streaming assembly; retry/failover/hedge visibility; provider-reported metadata; request mutation; privacy-aware capture; instrumentation failure/bypass/partial capture; unknown downgrade; adapter assertions versus independently verifiable evidence.

JSON Schema: NOT FROZEN.

Implementation: NOT STARTED.

## 1. Purpose

The Provider Adapter Contract translates the accepted C2ATrace semantic model into concrete capture obligations for an implementation observing an application-visible model-provider boundary.

It answers:

- where the adapter is allowed to claim observation;
- which records it creates or associates;
- what request representations it can classify;
- how retries, failover, hedging, streaming, and errors are captured;
- how privacy treatment changes disclosure without changing runtime history;
- how capture degradation is represented;
- which adapter statements remain Producer/instrumentation assertions.

The contract does not authorize new provider-internal claims.

The central boundary remains:

~~~text
application-visible provider adapter evidence
≠
provider receipt
≠
provider-internal request
≠
model-internal representation
~~~

## 2. Adapter responsibility boundary

### 2.1 Provider Adapter role

A Provider Adapter is instrumentation at an application-visible boundary through which the application requests a model result and/or observes provider-facing request preparation and model-result delivery.

One implementation can combine several hooks, such as:

- application SDK-call interception;
- provider-specific request-builder interception;
- serialization/transport-body interception;
- response/result interception;
- streaming iterator/event interception.

The logical Provider Adapter can therefore aggregate evidence from multiple application-side capture points.

### 2.2 Visibility ceiling

The adapter's claim ceiling is the most specific boundary it actually observes.

Observation of sdk_arguments does not imply provider_payload or prepared_http_body.

Observation of prepared_http_body does not imply Provider receipt.

Observation of a provider response at the application boundary does not expose provider-internal routing, hidden instructions, hidden retries, or model-internal state.

### 2.3 Conformance declaration

A conforming adapter exposes a conformance/capability declaration identifying at least:

- adapter implementation identity/version metadata;
- logical invocation boundary;
- attempt boundary;
- supported request capture levels;
- output/streaming observation capability;
- whether provider-attempt retry/failover/hedge relationships can be observed directly, are host-supplied, or remain unknown;
- supported privacy treatments for captured representations.

The exact wire form remains unfrozen.

A capability declaration describes intended instrumentation capability, not proof that every runtime occurrence was captured correctly.

### 2.4 Minimum baseline capability

The baseline Provider Adapter Contract requires capability to:

1. establish or receive a real ModelInvocation context;
2. record each ProviderAttempt visible at its declared attempt boundary;
3. capture at least one core RequestSnapshot level during normal supported operation;
4. observe the application-visible terminal model-result boundary, including streaming assembly when streaming is declared supported;
5. emit bounded diagnostics when a supported observation slot is known to degrade.

An implementation that can only observe raw transport requests without a defensible ModelInvocation context is a subordinate capture component rather than a standalone baseline Provider Adapter.

## 3. CaptureDiagnostic

### 3.1 Role

CaptureDiagnostic is an Assertion describing instrumentation status for one bounded capture slot.

It is not an Artifact, Activity, provenance edge, completeness certificate, or provider attestation.

It is designed to be reusable by Provider and Tool adapter contracts.

### 3.2 Diagnostic target

A diagnostic identifies a bounded subject/scope and capture slot.

Provider examples include:

~~~text
ModelInvocation boundary
ProviderAttempt tracking
RequestSnapshot: sdk_arguments
RequestSnapshot: provider_payload
RequestSnapshot: prepared_http_body
response/model-output capture
stream assembly
provider metadata capture
~~~

The subject/scope can refer to a Run, ModelInvocation, ProviderAttempt, RequestSnapshot, ModelOutput, or another precisely identified instrumentation scope.

### 3.3 Core diagnostic states

Core conceptual states are:

~~~text
observed
partial
unavailable
unsupported
bypass_detected
unknown
~~~

observed means the declared slot was positively observed within its bounded scope. It does not mean global instrumentation completeness.

partial means some expected evidence in the slot was observed but the adapter knows the capture is incomplete.

unavailable means the adapter expected/supported the slot for that occurrence but failed to obtain the required evidence.

unsupported means the adapter capability/profile does not support that slot.

bypass_detected means positive evidence indicates an applicable operation traversed a provider path outside the declared Provider Adapter observation boundary.

unknown means the adapter cannot justify a stronger diagnostic state.

### 3.4 Diagnostic reason and basis

A CaptureDiagnostic can record a reason/basis such as:

- hook failure;
- serialization interception failure;
- unsupported SDK/provider behavior;
- stream-consumption gap;
- instrumentation disabled;
- known bypass;
- correlation failure;
- privacy policy affecting disclosure;
- unknown.

A privacy disclosure decision is not itself a runtime capture failure and must remain distinguishable from capture availability.

### 3.5 No no-bypass certificate

Core v0.1 defines no CaptureDiagnostic state meaning "all provider operations were definitely observed" or "no bypass exists."

Absence of bypass_detected does not prove absence of bypass.

## 4. ModelInvocation capture contract

### 4.1 Invocation boundary

The adapter creates or associates a ModelInvocation when it observes a real application-level logical request for a model result or receives an explicit host-provided ModelInvocation context.

It does not create invocation grouping merely from equal requests, equal timestamps, provider request IDs, or content similarity.

### 4.2 One logical call occurrence

Distinct application logical-call occurrences retain distinct ModelInvocation identities even when every input value matches.

### 4.3 Zero-attempt invocation

If a logical invocation is rejected, cancelled, abandoned, or fails before the declared ProviderAttempt boundary begins, the ModelInvocation can terminate with zero ProviderAttempts.

The adapter does not fabricate a ProviderAttempt to represent pre-attempt failure.

### 4.4 Invocation metadata

Application-requested model label and other invocation-level intent metadata are recorded as application-/Producer-originated metadata.

They are not provider-internal facts.

### 4.5 Accepted output

The adapter records accepted_output only when the application/adapter selection of the effective logical ModelOutput is positively observed or explicitly supplied by the host application.

It does not select an accepted output merely because one attempt completed first or last.

## 5. ProviderAttempt capture contract

### 5.1 Attempt boundary

The adapter records one ProviderAttempt when one attempt begins at the adapter's declared application-visible attempt boundary.

The declaration defines what "attempt" means for that integration layer.

### 5.2 Hidden lower-layer retries

Retries or reconnects performed below the adapter's visibility boundary remain unknown unless exposed by a lower hook or separate evidence integrated into the same adapter.

The adapter does not invent hidden ProviderAttempts from latency, duplicate provider IDs, retry headers, or timing patterns alone.

### 5.3 Attempt identity

Every separately observed attempt occurrence receives a distinct ProviderAttempt identity.

Content equality does not merge attempts.

### 5.4 Terminal disposition

Attempt disposition is derived only from application-observed lifecycle evidence at the declared boundary.

The adapter preserves completed / failed / timeout / cancelled / interrupted / unknown according to Part D and does not translate provider-reported success metadata directly into attempt disposition without the application lifecycle event.

### 5.5 Correlation

The adapter maintains sufficient occurrence correlation to keep each observed request representation, response, error, and output associated with the correct ProviderAttempt.

Provider request IDs can assist correlation but do not replace C2ATrace attempt identity.

## 6. Request capture capability

### 6.1 At least one supported level

A baseline adapter declares at least one supported core request capture level:

~~~text
sdk_arguments
provider_payload
prepared_http_body
~~~

The adapter can support more than one.

### 6.2 Runtime capture obligation

For a capture level declared supported and applicable to an observed attempt/invocation, the adapter records the RequestSnapshot when it successfully observes the representation.

If the adapter knows the supported/applicable representation was not captured, it records a bounded CaptureDiagnostic rather than fabricating a snapshot.

### 6.3 Unsupported level

A level outside the adapter's capability declaration is not inferred or synthesized.

The adapter can record CaptureDiagnostic(status=unsupported) when that distinction is relevant to the Receipt/diagnostic scope.

### 6.4 Unknown classification

If a representation was captured but the adapter cannot justify sdk_arguments, provider_payload, or prepared_http_body classification, it uses capture_level=unknown rather than selecting the most plausible level.

## 7. sdk_arguments contract

sdk_arguments is captured at the application-visible structured call boundary before the provider-specific normalization represented by later levels.

Where the adapter operates at that boundary, it captures the effective structured arguments presented to the instrumented provider API, subject to configured privacy disclosure.

The adapter does not claim:

- that every sdk_argument survives provider normalization;
- that defaults not yet applied were present;
- that sdk_arguments equal provider_payload;
- that the Provider received this representation.

Invocation-scoped sdk_arguments can be reused across attempts only when the same immutable captured representation is actually reused for those attempts.

## 8. provider_payload contract

provider_payload is captured only when the adapter observes the provider-specific structured request after the normalization/defaulting/conversion steps included in that capture boundary and before the body serialization represented by prepared_http_body.

If the adapter itself performs:

- field renaming;
- default insertion;
- tool-schema conversion;
- model-alias resolution;
- parameter omission;
- wrapper construction;

and both before/after representations are captured, it records the appropriate Transform/Derivation evidence rather than treating the two snapshots as the same representation.

A post-hoc reconstruction from sdk_arguments does not become a historical provider_payload capture unless the reconstruction itself was the actual captured provider_payload representation.

## 9. prepared_http_body contract

prepared_http_body is used only when the adapter observes the exact body byte sequence at the declared application-side transport-preparation boundary.

The adapter does not synthesize prepared_http_body by later reserializing a structured request and assuming the bytes match.

The adapter records the representation basis necessary to interpret the body bytes.

prepared_http_body does not include or prove, unless a future profile explicitly says otherwise:

- HTTP headers;
- authorization headers;
- later compression/content coding;
- proxy/gateway rewrites;
- TLS/framing bytes;
- network delivery;
- Provider receipt.

A transport hook that observes bytes before a later application-visible mutation cannot label those earlier bytes as the final prepared_http_body for the later attempt boundary.

## 10. Effective snapshot and transition contract

### 10.1 Effective snapshot

For each ProviderAttempt and capture level, the adapter designates at most one effective RequestSnapshot when it knows which observed representation was the effective one for that attempt.

If it cannot establish which candidate snapshot was effective, it leaves the effective association unknown/absent rather than choosing by timestamp.

### 10.2 Missing levels

Missing intermediate capture levels are not synthesized.

A pipeline can legitimately record:

~~~text
sdk_arguments
→ prepared_http_body
~~~

or only one level.

### 10.3 Transition evidence

The adapter records a Transform/Derivation between request levels only when it observed or otherwise has positive evidence for that transition.

Adjacency in capture time does not establish a transition.

### 10.4 Same-level mutation

When the effective representation at one capture level changes, the changed representation receives a new RequestSnapshot identity.

### 10.5 Actual reuse versus equality

The same invocation-scoped snapshot can be reused across attempts only when the adapter knows the same immutable representation was reused.

Equal digest/content alone does not prove actual snapshot reuse.

## 11. RequestBinding capture contract

The adapter records RequestBinding only for ModelInputComponent occurrences whose mapping into the target RequestSnapshot can be established at the relevant capture level.

A binding at sdk_arguments does not automatically propagate to provider_payload or prepared_http_body.

If provider normalization drops, rewrites, duplicates, encodes, or relocates a component, later bindings require explicit later evidence/mapping.

If the adapter can only establish structural/path metadata but not representation equality, it preserves the weaker RequestBinding verification semantics from Part C.

## 12. Request mutation detection

### 12.1 Observable mutation

If the adapter observes that retry/failover/hedge preparation changes request representation, it preserves distinct snapshots for the changed attempts/levels.

Examples include:

- request IDs/nonces;
- effective model label;
- default parameters;
- provider routing fields;
- tool-definition transformations;
- body serialization;
- failover provider schema.

### 12.2 Mutation outside visibility

If mutation can occur after the adapter's highest capture point and is not observed, the adapter does not claim it did not happen.

### 12.3 Reconstructed comparison

An adapter can compute digests/commitments for captured representations and compare them.

Such equality/difference supports representation comparison only at those capture levels and does not prove network/provider-side equality/difference.

## 13. ModelOutput capture contract

### 13.1 Output boundary

ModelOutput represents the terminal assembled model-result representation that became application-visible through the declared adapter response boundary for one ProviderAttempt.

It is not the raw wire response unless the adapter's application-visible model-result boundary actually exposes that raw response as the result representation.

### 13.2 Zero or one core ModelOutput

One ProviderAttempt has zero or one core terminal assembled ModelOutput.

Intermediate response events do not create additional core ModelOutputs.

### 13.3 No result fabrication from error payload

An HTTP/provider error body, exception message, retry metadata, or diagnostic string is not turned into ModelOutput merely because it contains text.

It can be retained as provider/adapter error metadata or another future diagnostic artifact.

### 13.4 Output items

The adapter preserves application-visible occurrence multiplicity and ordering where meaningful when assembling TextOutput, StructuredOutput, ToolProposal, or unknown OutputItems.

Content equality does not merge OutputItem occurrences.

### 13.5 Output capture extent

The adapter sets ModelOutput capture_extent according to what its instrumentation actually captured within the declared application-visible output scope.

It does not set complete solely because the attempt disposition is completed or a provider finish reason says stop.

## 14. Non-streaming response contract

For a non-streaming provider result, the adapter captures the application-visible result at the declared response boundary before later application transformations that are outside the provider adapter scope.

If the application/SDK exposes a structured result, ModelOutput records that application-visible structured representation rather than pretending it is the raw provider wire response.

Provider-specific raw response material can be recorded separately when available and privacy policy permits, but it does not replace the core ModelOutput boundary.

## 15. Streaming observation contract

### 15.1 Stream-consumption boundary

If a provider call returns a lazy stream/iterator, declaring streaming output capture support requires instrumentation of the application-visible stream-consumption boundary, not merely interception of initial stream creation.

### 15.2 Terminal assembly

The adapter assembles the terminal immutable ModelOutput from the application-visible streaming events it actually observed, according to the provider/SDK event semantics.

### 15.3 Delta versus cumulative events

The adapter does not blindly concatenate event payloads.

It respects whether the provider/SDK exposes deltas, cumulative snapshots, replacements, indexed fragments, or another documented event form.

If event semantics are unsupported/unknown, the adapter degrades capture precision rather than inventing a deterministic assembly.

### 15.4 Partial stream

If content became application-visible before timeout, cancellation, failure, or interruption, the adapter can retain a partial ModelOutput representing the assembled observed content.

response_termination and capture_extent remain independent.

### 15.5 Application stops consumption

If the application stops consuming a stream before provider-normal completion is observed, the adapter does not infer that the Provider completed or stopped.

It records the application-visible lifecycle state it can justify and uses incomplete/unknown termination as appropriate.

### 15.6 Lost stream events

If the adapter knows stream events were dropped or could not be processed, it does not report output capture_extent=complete for the affected scope.

A CaptureDiagnostic records the known degradation where possible.

### 15.7 Tool proposal assembly

Streaming fragments are not promoted into a ToolProposal until the application-visible provider semantics establish a proposal occurrence sufficiently for Part D/Part E ToolProposal representation.

An incomplete fragment sequence that never establishes a proposal is not synthesized into a completed ToolProposal.

### 15.8 Chunk provenance

Core Provider Adapter conformance does not require persistent chunk-by-chunk provenance.

A future streaming evidence profile can add chunk artifacts/events without mutating core ModelOutput identities.

## 16. Retry contract

When the adapter directly observes an application-visible retry as another attempt for the same logical operation, it records a new ProviderAttempt and can assert retry_of.

The adapter does not reuse the prior ProviderAttempt identity.

A retry does not imply that the prior attempt failed before Provider receipt or produced no provider-side work.

If retry request representation changes, request snapshots follow the Part C identity rules.

## 17. Failover contract

When the application/provider adapter changes provider endpoint, model label, provider-specific payload, or other provider-selection material while continuing the same logical operation, the new visible attempt can be recorded as failover_from the prior attempt.

Failover relation is Producer/adapter orchestration evidence.

Different effective model/provider metadata remains preserved per attempt.

The adapter does not collapse failover attempts merely because they produce equal outputs.

## 18. Hedging contract

Concurrent/overlapping attempts for one logical invocation receive distinct ProviderAttempt identities.

hedged_with is recorded only when the adapter/application knows the orchestration relation.

The adapter does not infer a total order from timestamps.

Multiple hedged attempts can produce ModelOutputs.

accepted_output is recorded only from positively observed application selection.

A losing attempt cancelled by the application is recorded as cancelled only when that application-side cancellation was observed; this does not prove remote provider processing stopped.

## 19. Provider-reported metadata contract

### 19.1 Origin classes

Semantics-bearing provider-adapter metadata distinguishes its origin when relevant:

~~~text
application_supplied
adapter_observed
provider_reported
adapter_derived
unknown
~~~

These classes describe evidence origin, not factual truth.

### 19.2 Provider-reported values

Values reported by the provider/SDK response, such as:

- provider request/response ID;
- provider-reported model;
- finish reason;
- usage/token counts;
- cache indicators;
- safety/status fields;
- rate-limit metadata;

remain provider_reported/application-observed evidence.

They are not provider-internal attestations merely because the adapter preserves them exactly.

### 19.3 Provider IDs do not replace C2ATrace identity

Provider request IDs, response IDs, stream IDs, tool-call IDs, or message IDs remain metadata and do not replace ModelInvocation, ProviderAttempt, ModelOutput, or OutputItem identities.

### 19.4 Normalized metadata

If an adapter maps raw provider metadata into a normalized cross-provider value, the normalized value is adapter_derived.

It is not labelled as a raw provider-reported value.

Where feasible under the configured privacy profile, the adapter preserves the source provider field/value or an explicit mapping basis so the derivation can be audited.

### 19.5 Provider-reported model

A provider-reported model value is kept separate from invocation-requested and attempt-effective requested model values.

The adapter does not upgrade it to provider-internal model identity.

## 20. Transport/auth metadata boundary

Transport credentials, API keys, authorization headers, connection identifiers, TLS details, proxy metadata, and network-layer values are not automatically ModelInputComponents or model-visible provider request content.

If such metadata is captured for operational provenance, it remains in an appropriate transport/diagnostic scope and follows Privacy semantics.

The adapter does not create RequestBinding from an authorization header into the model request merely because both were sent in one HTTP exchange.

## 21. Privacy-aware capture contract

### 21.1 Runtime observation versus disclosure

The adapter keeps runtime capture status separate from Receipt disclosure treatment.

A representation can be successfully observed at runtime and later exported as hash_only, hmac, or redacted.

### 21.2 Privacy does not mutate history

The adapter does not replace the historical sdk_arguments/provider_payload/prepared_http_body/ModelOutput representation with masking placeholders and claim those placeholders were the runtime values.

### 21.3 Commitment-before-discard

When configured to export hash_only or hmac evidence while not retaining plaintext, the adapter computes the applicable commitment from the exact captured representation basis at the observation boundary before the plaintext is discarded/unavailable for export.

A later reconstruction is not labelled as the original capture commitment unless equivalence is independently established.

### 21.4 Redacted derivative

If the adapter emits provenance-bearing redacted content, it uses the Part G redacted derivative Artifact/Transform model.

### 21.5 CaptureDiagnostic versus privacy

Privacy-withheld disclosure does not automatically set CaptureDiagnostic to unavailable/partial when runtime observation succeeded.

Conversely, a valid privacy commitment does not hide a known runtime capture failure.

## 22. Adapter failure and partial instrumentation

### 22.1 Known capture failure

When the adapter knows a supported/applicable capture slot failed, the resulting Receipt/diagnostic output records that degradation with CaptureDiagnostic or the existing bounded capture-status field where one already exists.

The adapter does not fabricate the missing representation.

### 22.2 Partial request capture

If only part of a representation was observed and the core RequestSnapshot representation cannot truthfully denote the whole captured level, the adapter records only the supported bounded evidence/profile and CaptureDiagnostic(partial) rather than inventing the rest.

### 22.3 Partial output capture

Known loss of application-visible model content causes capture_extent=partial or unknown as semantically appropriate.

A diagnostic can record the instrumentation reason.

### 22.4 Instrumentation failure does not rewrite provider lifecycle

A request-capture hook failure does not by itself change ProviderAttempt disposition to failed when the provider attempt itself proceeded normally.

Capture status and provider-attempt lifecycle remain separate.

### 22.5 Adapter exception

An adapter/instrumentation exception is not automatically a Provider failure.

If the provider operation continues or its outcome is unknown, the attempt and capture diagnostics preserve those distinctions.

## 23. Bypass semantics

### 23.1 Positive bypass evidence

bypass_detected is used only when positive evidence indicates an applicable provider operation crossed a path outside the declared adapter observation boundary.

### 23.2 No negative inference

Absence of bypass_detected does not establish that no bypass occurred.

### 23.3 Bypassed records are not reconstructed as observed

If another system reports a provider call that bypassed the adapter, the adapter does not fabricate request snapshots or ModelOutputs as though it observed them.

External evidence can be recorded under an applicable future/profile mechanism and capture status remains bounded.

### 23.4 Multiple instrumentation layers

When multiple hooks observe the same attempt, the adapter correlates them as evidence for one ProviderAttempt only when actual occurrence correlation supports that conclusion.

It does not merge attempts solely from equal request content.

## 24. Unknown downgrade rules

When the adapter cannot justify a stronger state, it uses unknown or omits the stronger relation/object rather than guessing.

Examples include:

- capture_level=unknown;
- attempt disposition=unknown;
- response_termination=unknown;
- capture_extent=unknown;
- attempt relationship unknown/absent;
- provider metadata origin=unknown;
- effective snapshot unknown/absent;
- accepted_output unknown/absent;
- CaptureDiagnostic(status=unknown).

Unknown is not failure, absence, safe, successful, or complete.

## 25. Adapter assertions versus independently verifiable evidence

### 25.1 Adapter occurrence assertions

The following are ordinarily Producer/instrumentation assertions:

- a logical ModelInvocation occurred;
- an application-visible ProviderAttempt began/ended;
- attempt disposition;
- retry/failover/hedge grouping;
- capture diagnostic state/reason;
- accepted_output selection;
- application-observed response termination;
- provider-reported metadata origin.

A valid Receipt signature authenticates these recorded assertions; it does not make them objective provider facts.

### 25.2 Representation evidence

When a RequestSnapshot or ModelOutput representation is disclosed, an independent verifier can check representation commitments, paths, Regions, and related structural/content claims to the extent allowed by Parts C/G/H.

That does not independently prove the adapter observed the representation at the claimed runtime moment.

### 25.3 Provider receipt remains outside default contract

No Provider Adapter observation in this contract proves that the Provider received exact prepared bytes unless separate provider/transport evidence profile establishes that claim.

### 25.4 Provider internal state remains outside default contract

Provider-reported model IDs, request IDs, finish reasons, usage, and status values do not independently establish provider-internal routing, hidden model identity, internal prompt, hidden retry count, or model causal state.

## 26. Baseline conformance requirements

### PAD-001 — Provider Adapter visibility is application-side

A conforming Provider Adapter MUST limit default provenance claims to application-visible evidence at its declared capture boundaries and MUST NOT claim provider-internal visibility without a separate evidence profile.

Planned test: provider-adapter-visibility-boundary-001.

### PAD-002 — Adapter boundary declaration

A conforming Provider Adapter MUST declare its logical invocation boundary and ProviderAttempt boundary.

Planned test: provider-adapter-boundary-declaration-001.

### PAD-003 — Capture capability declaration

A conforming Provider Adapter MUST declare the core request capture levels and output/streaming capabilities it supports.

Planned test: provider-adapter-capability-declaration-001.

### PAD-004 — Baseline request capability

A baseline Provider Adapter MUST declare support for at least one of sdk_arguments, provider_payload, or prepared_http_body.

Planned test: provider-adapter-min-request-level-001.

### PAD-005 — Baseline output capability

A baseline Provider Adapter MUST support observation of the application-visible terminal model-result boundary for non-streaming responses and for streaming responses when it declares streaming support.

Planned test: provider-adapter-output-capability-001.

### PAD-006 — Capability is not capture proof

A verifier MUST NOT infer that an occurrence was captured solely from the adapter's capability declaration.

Planned test: provider-adapter-capability-not-observation-001.

### PAD-007 — Unknown over boundary guessing

A Provider Adapter MUST use unknown/weaker evidence rather than infer a stronger capture boundary from payload shape, SDK name, provider name, or expected implementation behavior.

Planned test: provider-adapter-boundary-unknown-001.

### PAD-008 — No provider receipt inference

A Provider Adapter MUST NOT report Provider receipt of request content solely from application-side send/preparation evidence.

Planned test: provider-adapter-no-provider-receipt-001.

### PAD-009 — CaptureDiagnostic is bounded

A CaptureDiagnostic MUST identify a bounded subject/scope and capture slot.

Planned test: provider-capture-diagnostic-scope-001.

### PAD-010 — CaptureDiagnostic state vocabulary

A core CaptureDiagnostic MUST identify exactly one conceptual state from observed, partial, unavailable, unsupported, bypass_detected, or unknown.

Planned test: provider-capture-diagnostic-state-001.

### PAD-011 — Diagnostic observed is not global completeness

A verifier MUST NOT interpret CaptureDiagnostic(status=observed) as proof of complete instrumentation coverage beyond the declared slot/scope.

Planned test: provider-capture-observed-bounded-001.

### PAD-012 — No no-bypass inference

A verifier MUST NOT infer absence of bypass solely because no CaptureDiagnostic(status=bypass_detected) is present.

Planned test: provider-capture-no-bypass-inference-001.

### PAD-013 — Capture diagnostic is assertion evidence

A verifier MUST NOT upgrade a CaptureDiagnostic into independently verified instrumentation completeness solely because it is signed or structurally valid.

Planned test: provider-capture-diagnostic-asserted-001.

### PAD-014 — Logical invocation needs defensible context

A Provider Adapter MUST create/associate ModelInvocation from an observed logical application call or explicit host-provided invocation context and MUST NOT infer invocation grouping solely from request/content equality.

Planned test: provider-invocation-context-001.

### PAD-015 — Distinct logical calls remain distinct

A Provider Adapter MUST NOT merge distinct logical application-call occurrences into one ModelInvocation solely because their inputs are equal.

Planned test: provider-invocation-no-content-merge-001.

### PAD-016 — Pre-attempt failure has zero attempt

A Provider Adapter MUST NOT create a ProviderAttempt solely to represent a failure/cancellation that occurred before the declared attempt boundary began.

Planned test: provider-pre-attempt-no-fake-attempt-001.

### PAD-017 — Accepted output requires positive selection evidence

A Provider Adapter MUST NOT set accepted_output solely from attempt completion order, timestamps, or output presence.

Planned test: provider-accepted-output-positive-evidence-001.

### PAD-018 — Attempt creation follows declared boundary

A Provider Adapter MUST create a ProviderAttempt only when an attempt is observed to begin at its declared attempt boundary.

Planned test: provider-attempt-boundary-001.

### PAD-019 — Hidden retry is not invented

A Provider Adapter MUST NOT create ProviderAttempts for retries/reconnects hidden below its visibility boundary without separate positive evidence.

Planned test: provider-hidden-retry-no-inference-001.

### PAD-020 — Distinct observed attempts have distinct identities

A Provider Adapter MUST assign distinct ProviderAttempt identities to distinct observed attempt occurrences.

Planned test: provider-attempt-distinct-identity-001.

### PAD-021 — Attempt disposition is lifecycle evidence

A Provider Adapter MUST derive attempt disposition from observed application-side lifecycle evidence and MUST NOT equate provider-reported success/status metadata with disposition without the corresponding lifecycle observation.

Planned test: provider-attempt-disposition-boundary-001.

### PAD-022 — Request/response correlation is occurrence-based

A Provider Adapter MUST maintain sufficient occurrence correlation to associate captured request/output/error evidence with the correct ProviderAttempt and MUST NOT rely on content equality alone.

Planned test: provider-attempt-correlation-001.

### PAD-023 — Provider IDs are not C2ATrace identity

A Provider Adapter MUST NOT use provider request/response/stream identifiers as substitutes for C2ATrace ModelInvocation, ProviderAttempt, ModelOutput, or OutputItem identities.

Planned test: provider-id-not-c2a-identity-001.

### PAD-024 — Supported/applicable request capture produces snapshot or diagnostic

For a declared-supported request capture level that is applicable and successfully observed, the adapter MUST record the RequestSnapshot; if the adapter knows capture failed, it MUST record bounded degradation rather than fabricate the snapshot.

Planned test: provider-request-snapshot-or-diagnostic-001.

### PAD-025 — Unsupported request level is not synthesized

A Provider Adapter MUST NOT synthesize a RequestSnapshot at a capture level it did not observe merely to fill the sdk_arguments → provider_payload → prepared_http_body sequence.

Planned test: provider-no-synthetic-level-001.

### PAD-026 — Capture level classification is evidence-bound

A Provider Adapter MUST NOT label a RequestSnapshot sdk_arguments, provider_payload, or prepared_http_body unless its observed boundary satisfies the corresponding Part C semantics.

Planned test: provider-capture-level-evidence-001.

### PAD-027 — sdk_arguments is not later-level evidence

A Provider Adapter MUST NOT infer provider_payload, prepared_http_body, or Provider receipt solely from sdk_arguments capture.

Planned test: provider-sdk-args-bounded-001.

### PAD-028 — provider_payload requires actual structured capture

A Provider Adapter MUST NOT label a post-hoc reconstruction as historical provider_payload unless that reconstruction was the actual observed provider-specific structured representation or equivalence is separately established and reported as reconstruction rather than capture.

Planned test: provider-payload-no-reconstruction-001.

### PAD-029 — prepared_http_body requires exact captured bytes

A Provider Adapter MUST NOT label a later reserialization or inferred byte sequence as prepared_http_body without actual byte capture at the declared boundary.

Planned test: provider-body-exact-capture-001.

### PAD-030 — prepared body does not include unobserved transport stages

A Provider Adapter MUST NOT claim prepared_http_body includes headers, later compression, proxy rewrites, TLS/framing, delivery, or Provider receipt unless a separate profile/evidence explicitly observes those stages.

Planned test: provider-body-transport-boundary-001.

### PAD-031 — Effective snapshot selection is positive

A Provider Adapter MUST NOT designate one of multiple same-level candidate RequestSnapshots as effective solely by timestamp when the effective representation cannot be established.

Planned test: provider-effective-snapshot-positive-001.

### PAD-032 — Missing intermediate level is valid

A Provider Adapter MUST permit request evidence that skips core capture levels and MUST NOT create missing intermediate RequestSnapshots.

Planned test: provider-missing-level-valid-001.

### PAD-033 — Request transition requires positive evidence

A Provider Adapter MUST NOT create Transform/Derivation request-level transition claims solely because two snapshots were observed sequentially.

Planned test: provider-request-transition-positive-001.

### PAD-034 — Changed same-level representation gets new identity

When the adapter observes a changed effective representation at one capture level, it MUST use a new RequestSnapshot identity for the changed representation.

Planned test: provider-request-mutation-new-snapshot-001.

### PAD-035 — Reuse requires actual reuse

A Provider Adapter MUST NOT reuse one invocation-scoped RequestSnapshot identity across attempts solely because representations/digests are equal; actual immutable snapshot reuse must be established.

Planned test: provider-request-reuse-not-equality-001.

### PAD-036 — RequestBinding stays capture-level local

A Provider Adapter MUST NOT automatically propagate a RequestBinding from one capture level to another without explicit later mapping/evidence.

Planned test: provider-binding-level-local-001.

### PAD-037 — RequestBinding requires positive mapping

A Provider Adapter MUST NOT create representation-level RequestBinding for a component/location when the source-to-target mapping cannot be positively established at that capture level.

Planned test: provider-binding-positive-mapping-001.

### PAD-038 — Mutation outside visibility remains unknown

A Provider Adapter MUST NOT report that no request mutation occurred after its highest observed capture point merely because no later mutation was visible to it.

Planned test: provider-request-post-boundary-unknown-001.

### PAD-039 — Representation comparison stays capture-local

A Provider Adapter MUST NOT upgrade digest/content equality between captured snapshots into network-delivery or provider-internal equality claims.

Planned test: provider-request-comparison-bounded-001.

### PAD-040 — ModelOutput is application-visible result

A Provider Adapter MUST represent ModelOutput from the application-visible model-result boundary and MUST NOT substitute raw provider wire/error material unless that material is actually the model-result representation at the declared boundary.

Planned test: provider-output-boundary-001.

### PAD-041 — Core output cardinality

A Provider Adapter MUST NOT emit more than one core terminal ModelOutput for one ProviderAttempt.

Planned test: provider-output-cardinality-001.

### PAD-042 — Error text is not automatically ModelOutput

A Provider Adapter MUST NOT create ModelOutput solely from HTTP/provider error bodies, exception text, retry diagnostics, or transport errors that were not application-visible model-result content.

Planned test: provider-error-not-model-output-001.

### PAD-043 — Output occurrence multiplicity is preserved

A Provider Adapter MUST NOT merge distinct application-visible OutputItem occurrences solely because their content or provider IDs match.

Planned test: provider-outputitem-no-merge-001.

### PAD-044 — Capture extent follows instrumentation evidence

A Provider Adapter MUST NOT set ModelOutput capture_extent=complete solely from ProviderAttempt disposition=completed, provider finish_reason, or SDK success.

Planned test: provider-output-capture-evidence-001.

### PAD-045 — Non-streaming result uses declared result boundary

When the adapter successfully observes a non-streaming model result, it MUST capture the ModelOutput representation at its declared application-visible result boundary and MUST NOT mislabel a later application-transformed value as the provider-adapter result unless that later boundary is explicitly the adapter boundary.

If the supported result capture itself fails, PAD-072 applies.

Planned test: provider-nonstream-result-boundary-001.

### PAD-046 — Streaming support requires stream-consumption observation

An adapter declaring streaming output capture support MUST observe the application-visible stream-consumption/event boundary, not only the creation of a lazy stream/iterator.

Planned test: provider-stream-consumption-boundary-001.

### PAD-047 — Streaming assembly follows event semantics

A Provider Adapter MUST assemble streaming ModelOutput according to the provider/SDK event semantics and MUST NOT blindly concatenate cumulative/replacement/indexed event payloads as if every event were a delta.

Planned test: provider-stream-event-semantics-001.

### PAD-048 — Unsupported stream semantics degrade precision

If streaming event semantics needed for correct assembly are unsupported or unknown, the adapter MUST use partial/unknown capture semantics rather than fabricate a complete terminal representation.

Planned test: provider-stream-unsupported-degrade-001.

### PAD-049 — Partial stream evidence is preserved when observed

When application-visible model content was observed before abnormal stream termination, the adapter MUST preserve provenance evidence for that observed content according to the configured privacy treatment and MUST NOT erase it solely because the attempt later timed out, failed, was cancelled, or was interrupted.

Planned test: provider-stream-partial-preserve-001.

### PAD-050 — Application stop is not provider completion

A Provider Adapter MUST NOT infer provider-normal completion or provider-side stop solely because the application stopped consuming/cancelled a stream.

Planned test: provider-stream-app-stop-bounded-001.

### PAD-051 — Known dropped events prevent complete capture

If the adapter knows application-visible stream events were lost/unprocessed in the declared capture scope, it MUST NOT report capture_extent=complete for that output scope.

Planned test: provider-stream-drop-no-complete-001.

### PAD-052 — Incomplete tool fragments are not completed ToolProposals

A Provider Adapter MUST NOT synthesize a completed ToolProposal from streaming fragments that never established an application-visible proposal occurrence under the provider/SDK semantics.

Planned test: provider-stream-tool-fragment-001.

### PAD-053 — Chunk retention is not baseline-required

A baseline Provider Adapter MAY omit persistent chunk-level provenance while retaining a correct terminal assembled ModelOutput and bounded streaming/capture metadata.

Planned test: provider-stream-chunks-optional-001.

### PAD-054 — Visible retry creates new attempt

A Provider Adapter observing a retry attempt for the same logical invocation MUST create a distinct ProviderAttempt rather than reuse the predecessor attempt identity.

Planned test: provider-retry-new-attempt-001.

### PAD-055 — retry_of requires known orchestration

A Provider Adapter MUST NOT assert retry_of solely from request similarity, timestamps, or provider retry metadata without application/adapter orchestration evidence.

Planned test: provider-retry-relation-positive-001.

### PAD-056 — Retry does not negate prior provider work

A Provider Adapter MUST NOT report retry_of as proof that the prior attempt was not received or processed by the Provider.

Planned test: provider-retry-no-prior-negation-001.

### PAD-057 — Failover preserves per-attempt request/model metadata

When a visible failover changes provider/model/request preparation, the adapter MUST preserve the distinct effective request/model/provider metadata for each attempt.

Planned test: provider-failover-metadata-001.

### PAD-058 — failover_from requires known orchestration

A Provider Adapter MUST NOT assert failover_from solely because two attempts target different provider/model identifiers.

Planned test: provider-failover-positive-001.

### PAD-059 — Hedged attempts remain distinct

A Provider Adapter MUST preserve distinct identities for concurrent/overlapping hedged ProviderAttempts.

Planned test: provider-hedge-distinct-attempts-001.

### PAD-060 — Hedging does not create total order

A Provider Adapter MUST NOT infer a total attempt order solely from timestamps when attempts can overlap/hedge.

Planned test: provider-hedge-no-total-order-001.

### PAD-061 — Losing hedge cancellation is application-side evidence

A Provider Adapter MUST NOT report a cancelled losing hedge as proof that remote provider processing stopped.

Planned test: provider-hedge-cancel-bounded-001.

### PAD-062 — Provider metadata origin is explicit when semantically relevant

A Provider Adapter MUST distinguish application_supplied, adapter_observed, provider_reported, adapter_derived, or unknown origin for provider metadata whose interpretation depends on origin.

Planned test: provider-metadata-origin-001.

### PAD-063 — Provider-reported metadata stays reported

A Provider Adapter MUST NOT restate provider-reported model, finish reason, usage, cache, safety/status, request/response IDs, or rate-limit values as independently verified provider-internal facts solely because they were received through the SDK/response.

Planned test: provider-metadata-reported-bounded-001.

### PAD-064 — Normalized metadata is adapter-derived

When an adapter maps provider-specific metadata into a normalized value, it MUST classify the normalized value as adapter_derived rather than raw provider_reported evidence.

Planned test: provider-metadata-normalized-origin-001.

### PAD-065 — Provider-reported model stays separate

A Provider Adapter MUST NOT overwrite invocation-requested or attempt-effective requested model identity with provider-reported model metadata.

Planned test: provider-model-identity-separation-001.

### PAD-066 — Transport credentials are not model inputs by proximity

A Provider Adapter MUST NOT create ModelInputComponent/RequestBinding claims for API keys, authorization headers, TLS metadata, or other transport credentials solely because they accompanied the provider request.

Planned test: provider-transport-secret-not-model-input-001.

### PAD-067 — Runtime capture and Receipt disclosure are separate

A Provider Adapter MUST NOT infer runtime capture failure solely because the exported Receipt uses hash_only, hmac, redacted, or withheld privacy treatment.

Planned test: provider-privacy-capture-separation-001.

### PAD-068 — Privacy masking does not mutate runtime representation

A Provider Adapter MUST NOT replace historical request/output values with presentation masking placeholders and report the placeholders as the runtime representations unless they actually were the runtime values.

Planned test: provider-privacy-placeholder-no-mutation-001.

### PAD-069 — Commitment-before-discard uses exact observed basis

When a configured privacy profile requires commitment-only export without retaining plaintext, the adapter MUST compute the commitment from the exact observed representation basis before that representation becomes unavailable, or otherwise downgrade the claim if only a reconstruction is available.

Planned test: provider-privacy-commit-before-discard-001.

### PAD-070 — Redacted capture uses derivative identity

A Provider Adapter producing provenance-bearing redacted request/output content MUST use the Part G derivative Artifact/Transform semantics and MUST NOT reuse the original Artifact identity for changed redacted representation.

Planned test: provider-privacy-redacted-identity-001.

### PAD-071 — Privacy does not hide known capture failure

A Provider Adapter MUST NOT report privacy treatment as a substitute for a known supported-slot capture failure.

Planned test: provider-privacy-no-failure-laundering-001.

### PAD-072 — Known capture failure is explicit

When producing a C2ATrace record after it knows a supported/applicable capture slot failed, the adapter MUST preserve that degradation through CaptureDiagnostic or an existing semantically equivalent bounded capture-status field.

Planned test: provider-capture-failure-explicit-001.

### PAD-073 — Capture failure does not fabricate representation

A Provider Adapter MUST NOT fabricate a missing RequestSnapshot, ModelOutput, stream event sequence, or provider metadata value to make the capture appear complete.

Planned test: provider-capture-failure-no-fabrication-001.

### PAD-074 — Capture failure is separate from attempt failure

A Provider Adapter MUST NOT classify ProviderAttempt disposition=failed solely because adapter instrumentation/capture failed while the provider attempt lifecycle was completed or unknown.

Planned test: provider-capture-vs-attempt-failure-001.

### PAD-075 — Adapter exception is not Provider exception

A Provider Adapter MUST NOT report an instrumentation exception as a provider-reported/provider-side error unless that origin is independently observed.

Planned test: provider-adapter-error-origin-001.

### PAD-076 — Known bypass uses positive evidence

A Provider Adapter MUST NOT emit CaptureDiagnostic(status=bypass_detected) solely from absence of expected records; bypass_detected requires positive bypass evidence.

Planned test: provider-bypass-positive-evidence-001.

### PAD-077 — Bypass evidence does not fabricate missing provenance

A Provider Adapter MUST NOT reconstruct unobserved bypassed RequestSnapshots/ModelOutputs as adapter-observed historical representations solely from external summaries.

Planned test: provider-bypass-no-fabrication-001.

### PAD-078 — Multiple hooks require occurrence correlation

A Provider Adapter MUST NOT merge observations from multiple instrumentation hooks into one ProviderAttempt solely because request content/provider IDs match; actual occurrence correlation must support the merge.

Planned test: provider-multihook-correlation-001.

### PAD-079 — Unknown state is preserved

When the adapter cannot justify a stronger lifecycle, capture, relationship, metadata-origin, effective-snapshot, or accepted-output claim, it MUST preserve unknown/absence as permitted by the semantic layer rather than guess.

Planned test: provider-adapter-unknown-preserved-001.

### PAD-080 — Adapter assertions remain Producer/instrumentation assertions

A verifier MUST NOT upgrade adapter-recorded invocation/attempt occurrence, lifecycle, orchestration, capture diagnostic, accepted-output selection, or response-termination claims to external provider facts solely because the Receipt is signed.

Planned test: provider-adapter-assertion-bounded-001.

### PAD-081 — Representation verification does not prove runtime observation truth

A verifier MUST NOT infer that the adapter factually observed a representation at the claimed runtime boundary solely because the supplied representation/digest/commitment is internally consistent.

Planned test: provider-representation-not-observation-proof-001.

### PAD-082 — Provider receipt remains unestablished by default

A verifier MUST NOT report exact request receipt by the Provider solely from Provider Adapter RequestSnapshot/ProviderAttempt evidence.

Planned test: provider-adapter-provider-receipt-unestablished-001.

### PAD-083 — Provider internals remain unestablished by default

A verifier MUST NOT report provider-internal routing, hidden retry count, hidden prompt transformation, actual internal model identity, or model-internal state solely from Provider Adapter evidence.

Planned test: provider-adapter-internals-unestablished-001.

### PAD-084 — Signed CaptureDiagnostic is not coverage completeness

A verifier MUST NOT report a signed CaptureDiagnostic or signed adapter capability declaration as proof that all applicable provider operations were instrumented.

Planned test: provider-capture-diagnostic-no-global-completeness-001.

### PAD-085 — CaptureDiagnostic identity is occurrence-based

A verifier MUST NOT merge distinct CaptureDiagnostic identities solely because their subject/scope, slot, state, reason, adapter identity, or timestamps match.

Planned test: provider-capture-diagnostic-no-merge-001.

### PAD-086 — Missing diagnostic is not successful observation proof

Absence of CaptureDiagnostic for a capture slot MUST NOT be reported as proof that the slot was successfully observed.

Planned test: provider-capture-diagnostic-absence-not-success-001.

### PAD-087 — Conflicting diagnostics are preserved

When incompatible CaptureDiagnostics exist for the same bounded slot/scope and no explicit supersession/evidence rule resolves them, a verifier MUST preserve/report the conflict rather than choose by timestamp or insertion order.

Planned test: provider-capture-diagnostic-conflict-001.

### PAD-088 — Adapter identity/version is not implementation trust

A verifier MUST NOT infer code authenticity, correct instrumentation behavior, or trusted adapter implementation solely from recorded adapter name/version/capability metadata.

Planned test: provider-adapter-version-no-trust-001.

### PAD-089 — Adapter timestamps are not trusted time

A verifier MUST NOT report adapter-recorded invocation/attempt/capture timestamps as trusted wall-clock time without a separate trusted-time profile.

Planned test: provider-adapter-time-bounded-001.

### PAD-090 — Response parse failure is not fabricated ModelOutput

If provider/transport response bytes or metadata are observed but the declared application-visible model-result parsing/assembly boundary fails before a model result is established, the adapter MUST NOT fabricate ModelOutput from the raw response solely to fill the output slot.

Planned test: provider-response-parse-failure-no-output-001.

### PAD-091 — Streaming unsupported is explicit when applicable

If a call uses streaming but the adapter's declared capability does not support the required stream-consumption boundary, the adapter MUST NOT report complete streaming capture and MUST preserve the unsupported/unknown limitation when producing diagnostics.

Planned test: provider-stream-unsupported-explicit-001.

### PAD-092 — Normalized metadata needs bounded mapping basis

When adapter_derived metadata is used as a semantics-bearing normalized value, the adapter MUST preserve the provider-specific source field/value or an explicit mapping/profile basis when that basis is available under the configured privacy treatment; otherwise the normalization basis remains unknown rather than being presented as raw provider evidence.

Planned test: provider-metadata-normalization-basis-001.

### PAD-093 — CaptureDiagnostic unsupported and unavailable remain distinct

A verifier MUST NOT collapse CaptureDiagnostic(status=unsupported) and status=unavailable: unsupported describes declared capability absence, while unavailable describes failure/lack of evidence for a slot that was expected/supported for the occurrence.

Planned test: provider-capture-unsupported-vs-unavailable-001.

### PAD-094 — Diagnostic privacy reason does not redefine capture state

A privacy disclosure reason attached to CaptureDiagnostic MUST NOT by itself convert a successfully observed runtime slot into status=unavailable or partial.

Planned test: provider-capture-privacy-reason-bounded-001.

### PAD-095 — Adapter response capture failure preserves attempt lifecycle uncertainty

When response/result instrumentation fails after an attempt has begun, the adapter MUST NOT infer completed, failed, timeout, cancelled, or interrupted solely from the capture failure; it uses separately observed lifecycle evidence or unknown.

Planned test: provider-response-capture-lifecycle-001.

## 27. Adversarial architecture review

### Review A — High-level SDK silently retries internally

The adapter sees one high-level attempt boundary and no lower retry hook.

It records only the application-observed attempt and does not invent hidden ProviderAttempts.

Result: RESOLVED by PAD-018 through PAD-020.

### Review B — Retry reuses sdk_arguments but inserts new provider request ID

The invocation-scoped sdk_arguments can remain reused if actually reused.

The provider_payload/body changes get new attempt-scoped snapshots.

Result: RESOLVED by PAD-034 and PAD-035.

### Review C — Adapter captures structured payload, then transport middleware changes bytes

The adapter does not claim prepared_http_body unless it observed the post-serialization body boundary matching Part C.

Later unseen mutation remains unknown.

Result: RESOLVED by PAD-026, PAD-029, PAD-030, and PAD-038.

### Review D — Adapter reserializes payload after the request and calls it prepared body

This is reconstruction, not historical body capture.

Result: RESOLVED by PAD-029.

### Review E — provider_payload captured but sdk_arguments unavailable

This is valid. No sdk_arguments snapshot is synthesized.

Result: RESOLVED by PAD-024 through PAD-032.

### Review F — SDK arguments include context that provider conversion drops

The sdk_arguments RequestBinding does not propagate automatically into provider_payload.

Result: RESOLVED by PAD-036 and PAD-037.

### Review G — Two adjacent request snapshots but transform hook was not observed

No Transform/Derivation is invented solely from adjacency.

Result: RESOLVED by PAD-033.

### Review H — Lazy stream returned, adapter records only stream object creation

The adapter cannot claim complete streaming output capture without observing application-visible stream consumption.

Result: RESOLVED by PAD-046.

### Review I — Provider SDK emits cumulative text snapshots

Blind concatenation would duplicate text.

The adapter follows SDK event semantics or degrades capture.

Result: RESOLVED by PAD-047 and PAD-048.

### Review J — Stream emits half a tool call then disconnects

No completed ToolProposal is synthesized if the provider/SDK semantics never established one.

Partial output/capture state is retained.

Result: RESOLVED by PAD-049 and PAD-052.

### Review K — Timeout after partial visible text

The attempt can be timeout/interrupted as appropriate while ModelOutput preserves observed partial text.

Capture extent can still be complete relative to everything the adapter actually received before termination if no events were lost.

Result: RESOLVED by PAD-049 and the Part D independent axes.

### Review L — HTTP 400 body contains human-readable text

The adapter records error metadata, not a ModelOutput, unless the declared application model-result boundary actually exposes it as model-result content.

Result: RESOLVED by PAD-040 through PAD-042.

### Review M — Two hedged attempts both return complete outputs

Both ProviderAttempts and ModelOutputs remain.

Only positively observed application selection sets accepted_output.

Result: RESOLVED by PAD-059 through PAD-061 and PAD-017.

### Review N — Failover changes model/provider

Per-attempt effective request/model/provider metadata remains separate.

Result: RESOLVED by PAD-057 and PAD-065.

### Review O — Provider reports model B while application requested alias A

Both values are retained in their respective semantic roles.

Result: RESOLVED by PAD-065.

### Review P — Provider request ID repeats on two attempts

The ID remains metadata and does not merge C2ATrace attempt identity.

Result: RESOLVED by PAD-023.

### Review Q — Adapter normalizes provider finish reason

The normalized field is adapter_derived, not raw provider_reported.

Result: RESOLVED by PAD-062 through PAD-064.

### Review R — Runtime request captured fully but external Receipt is hash-only

Capture can be observed while disclosure is commitment-only.

The privacy profile does not turn runtime capture into failure.

Result: RESOLVED by PAD-067.

### Review S — Adapter exports token="***" after executing with real secret

The placeholder is not the historical request value.

Use privacy withholding/commitment or a derivative redacted Artifact.

Result: RESOLVED by PAD-068 through PAD-070.

### Review T — Authorization header accompanies prompt

The API key is transport metadata, not automatically a ModelInputComponent visible to the model.

Result: RESOLVED by PAD-066.

### Review U — Request capture hook fails, provider call succeeds

ProviderAttempt can complete while request capture diagnostic is unavailable.

The missing request is not fabricated and attempt disposition is not rewritten to failed.

Result: RESOLVED by PAD-072 through PAD-075.

### Review V — Adapter crashes after attempt begins

If later instrumentation/host evidence can record the gap, lifecycle/capture state remains partial/unknown.

Missing records alone are not interpreted as provider failure or complete capture.

Result: RESOLVED by PAD-072 through PAD-075 and existing absence semantics.

### Review W — Application bypasses adapter with a raw client

If positive external/host evidence detects the bypass, CaptureDiagnostic can record bypass_detected.

The adapter does not invent the missed request/output.

Absence of such a diagnostic does not prove no bypass.

Result: RESOLVED by PAD-012, PAD-076, and PAD-077.

### Review X — Two hooks observe the same network attempt

They can be correlated into one ProviderAttempt only from real occurrence correlation.

Equal payload/provider request ID alone is insufficient.

Result: RESOLVED by PAD-078.

### Review Y — Transport-only instrumenter sees HTTP request but no logical call context

It cannot independently satisfy the baseline Provider Adapter contract by inventing a logical ModelInvocation grouping.

It can serve as a subordinate capture component feeding a higher-level adapter.

Result: RESOLVED by PAD-014 and the baseline capability model.

### Review Z — Provider SDK returns usage=100

The adapter preserves it as provider_reported metadata.

It does not independently attest provider-internal token accounting.

Result: RESOLVED by PAD-063.

### Review AA — Adapter sees request sent and HTTP response later

This does not prove the Provider received the exact prepared bytes unless a separate transport/provider evidence profile establishes it.

Result: RESOLVED by PAD-008 and PAD-082.

### Review AB — Application stops reading a stream after first item

The adapter does not mark provider response complete merely because its own observation ended.

Result: RESOLVED by PAD-050.

### Review AC — Losing hedge is cancelled locally

The adapter records local cancellation but does not claim the remote Provider stopped work.

Result: RESOLVED by PAD-061.

### Review AD — Same content appears in two separately captured attempt-scoped snapshots

Equal content/digest does not merge the snapshot occurrences.

Result: RESOLVED by PAD-034 and PAD-035 plus Part C identity rules.

### Review AE — Provider Adapter inserts a default tool definition

If before/after request representations are captured, the adapter records Transform/Derivation/control provenance according to Parts B/C rather than attributing the inserted content to an unrelated user component.

Result: RESOLVED by PAD-033, PAD-036, and existing Derivation semantics.

### Review AF — Privacy policy withholds RequestLocation metadata

The adapter preserves the available structural capture, but later verifier location-resolution strength is bounded by Part G.

Privacy does not authorize guessing the path.

Result: RESOLVED by PAD-067 and Part G.

### Review AG — Receipt signature validates an adapter claim that capture was complete

The signature authenticates the assertion representation.

It does not independently prove instrumentation coverage or absence of bypass.

Result: RESOLVED by PAD-080, PAD-081, and PAD-084.

### Review AH — HTTP 200 arrives but SDK response parser crashes

Transport/response bytes can exist while no application-visible model-result representation was successfully established.

The adapter keeps raw/provider diagnostics separate and does not invent ModelOutput.

Result: RESOLVED by PAD-040, PAD-042, and PAD-090.

### Review AI — Adapter supports non-streaming only, application requests streaming

The adapter does not treat stream creation as complete output capture.

It preserves unsupported/unknown streaming limitation.

Result: RESOLVED by PAD-046 and PAD-091.

### Review AJ — Two CaptureDiagnostics disagree for the same body-capture slot

One reports observed; another reports unavailable.

The verifier preserves the conflict absent explicit resolution evidence and does not use latest timestamp as truth.

Result: RESOLVED by PAD-085 through PAD-087.

### Review AK — Receipt says adapter=v1.2.3 from trusted project name

The version/name identifies recorded implementation metadata only.

It does not prove that exact code ran or that instrumentation was correct.

Result: RESOLVED by PAD-088.

### Review AL — Adapter timestamp is signed

The signature authenticates the timestamp representation but does not make it trusted wall-clock time.

Result: RESOLVED by PAD-089.

### Review AM — Partial stream captured under hash_only privacy

The adapter can preserve commitment evidence for observed partial content without retaining/disclosing plaintext.

Abnormal termination does not erase the observation, and privacy does not turn it into a capture failure.

Result: RESOLVED by PAD-049, PAD-067, and PAD-094.

## 28. Architecture revisions caused by Provider Adapter Contract

### 28.1 CaptureDiagnostic becomes a reusable Assertion

Provider Adapter conformance requires explicit representation of known capture degradation.

CaptureDiagnostic is therefore promoted as a reusable instrumentation Assertion that can later be used by Tool Adapter Contract.

It does not prove global coverage.

### 28.2 Adapter capability is distinct from runtime capture

Static/configured capability declaration describes what the adapter intends to observe.

Runtime objects and CaptureDiagnostics describe what it actually recorded for a bounded occurrence.

Neither implies complete application instrumentation.

### 28.3 Provider Adapter remains application-side

The adapter contract does not redefine ProviderAttempt as provider-internal transport truth.

Hidden SDK/provider retries remain unknown unless separately observed.

### 28.4 Streaming capture requires consumption visibility

A wrapper around stream creation is insufficient for complete streaming capture.

The actual application-visible event/iterator boundary is the output observation boundary.

### 28.5 Privacy and capture status are orthogonal

Runtime representation observation can be successful even when the Receipt withholds plaintext.

Privacy export is not capture failure, and capture failure cannot be laundered as privacy.

### 28.6 Metadata provenance is explicit

Provider-reported, application-supplied, adapter-observed, adapter-derived, and unknown metadata are not collapsed.

This prevents normalized/provider-reported values from being upgraded to provider-internal facts.

## 29. Contract decisions

The Provider Adapter Contract locks:

1. Provider Adapter visibility is application-side and explicitly declared.
2. A baseline adapter has a defensible ModelInvocation boundary, attempt boundary, at least one request capture level, and model-result observation capability.
3. Capture capability declaration is not runtime capture proof.
4. CaptureDiagnostic is occurrence-identified, preserves conflicts, and explicitly records bounded instrumentation state/degradation without claiming global coverage.
5. ModelInvocation grouping is based on observed logical call context, not request equality.
6. ProviderAttempt is created only at the declared visible attempt boundary; hidden lower retries are not invented.
7. Request capture levels remain exactly those defined by Part C and are evidence-bound.
8. Missing request levels are valid and are not synthesized.
9. prepared_http_body requires exact byte capture at the declared boundary, not later reserialization.
10. Request transitions/bindings are not inferred across capture levels.
11. Request mutation creates new snapshots and unseen downstream mutation remains unknown.
12. ModelOutput is the application-visible model-result boundary, not arbitrary raw/error response content.
13. Streaming support requires application-visible stream-consumption observation.
14. Streaming assembly follows provider/SDK event semantics; unsupported semantics degrade capture precision.
15. Partial visible output is preserved across timeout/failure/cancellation/interruption.
16. Visible retries/failovers/hedges remain distinct attempts and orchestration relations require positive evidence.
17. Provider IDs remain metadata, not C2ATrace identity.
18. Provider-reported metadata stays reported; normalized metadata is adapter-derived and retains a bounded mapping basis when available.
19. Transport credentials are not model-visible inputs by proximity.
20. Runtime capture and privacy disclosure are orthogonal.
21. Known adapter capture failure is explicit and cannot fabricate missing provenance.
22. Instrumentation failure is separate from provider-attempt failure.
23. bypass_detected requires positive evidence; absence of bypass diagnostic is not no-bypass proof.
24. Unknown is the required downgrade when evidence is insufficient.
25. Adapter identity/version/timestamps remain bounded metadata rather than implementation-trust or trusted-time proof.
26. Adapter assertions remain Producer/instrumentation assertions even when signed.
27. Provider receipt and provider-internal behavior remain unestablished by default.

## 30. Open items handed to later contracts

The Provider Adapter Contract intentionally does not freeze:

- final JSON field names for CaptureDiagnostic or adapter capability declaration;
- exact adapter implementation/plugin API;
- provider-specific event mapping tables;
- provider-specific metadata registries;
- raw HTTP/header evidence profiles;
- provider-originated receipt/attestation profiles;
- streaming chunk-evidence profile;
- distributed tracing export details;
- exact error taxonomy;
- Tool Adapter capture obligations;
- final independent Verifier output schema.

These remain constrained by this contract.

## 31. Gate decision

Provider Adapter Contract is ready for adversarial/mechanical review.

JSON Schema and implementation remain BLOCKED.
