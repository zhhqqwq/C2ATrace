# C2ATrace v0.1 — Phase 1 Part D: ModelInvocation / ProviderAttempt / ModelOutput Semantics

Status: ACCEPTED AFTER ADVERSARIAL REVIEW.

Scope: ModelInvocation identity and lifecycle; ProviderAttempt lifecycle and terminal disposition; retry, timeout, failover, and hedging; model-identity claims; ModelOutput ownership and selection; OutputItem identity/cardinality; text, structured, and tool-proposal outputs; streaming and partial output; response completion versus capture completeness; attempt-to-output claim strength.

JSON Schema: NOT FROZEN.

Implementation: NOT STARTED.

## 1. Design objective

Part D defines how C2ATrace connects one logical model operation to physical provider attempts and to the application-visible output artifacts observed from those attempts.

The central separations are:

~~~text
ModelInvocation
≠
ProviderAttempt

attempt completed
≠
output captured completely

response completed
≠
output capture complete

ModelOutput recorded
≠
Provider generated exactly that representation

requested model
≠
provider-reported model
≠
provider-internal model identity

attempt produced output
≠
application accepted that output
~~~

Part D preserves retry, failover, timeout, hedging, streaming, and partial-output cases without collapsing them into a single success boolean.

## 2. ModelInvocation identity

### 2.1 Logical-operation identity

A ModelInvocation is one Producer-recorded logical application request for a model result.

Its identity is occurrence-based, not content-based.

Two logical invocations remain distinct even when they have:

- identical request snapshots;
- identical model labels;
- identical parameters;
- identical timestamps;
- identical outputs.

Likewise, multiple ProviderAttempts can belong to one ModelInvocation when the application treats them as attempts to satisfy the same logical operation.

### 2.2 Retry versus new invocation

Retry, reconnect, failover, or hedge attempts can remain within one ModelInvocation when they are recorded as alternative physical attempts for the same logical operation.

A follow-up prompt, continuation request, new turn, or application decision that constitutes a new logical model operation is represented by a new ModelInvocation.

Whether two physical requests belong to the same logical operation is a Producer-recorded grouping assertion; core v0.1 does not infer it from request equality.

### 2.3 Invocation lifecycle

Part D conceptually distinguishes:

~~~text
active
terminal
unknown
~~~

A terminal ModelInvocation can carry a Producer-recorded terminal disposition such as:

~~~text
output_accepted
failed
cancelled
abandoned
unknown
~~~

Exact wire vocabulary remains unfrozen.

Invocation terminal disposition is not inferred solely from the ProviderAttempts present in a Receipt because the supplied provenance can be incomplete.

## 3. ProviderAttempt lifecycle

### 3.1 Attempt occurrence

A ProviderAttempt represents one application-observed physical/provider-adapter attempt.

An attempt exists only once the application/instrumentation records that the attempt began.

A logical invocation that is rejected or abandoned before any physical attempt can therefore have zero ProviderAttempts.

### 3.2 Attempt lifecycle state

Part D conceptually distinguishes:

~~~text
in_progress
terminal
unknown
~~~

A terminal ProviderAttempt can carry one terminal disposition:

~~~text
completed
failed
timeout
cancelled
interrupted
unknown
~~~

These values describe the application-observed attempt lifecycle, not external Provider truth.

### 3.3 completed

completed means the application observed the attempt reach its normal provider-adapter response termination rather than a locally observed failure, timeout, cancellation, or interruption.

completed does not establish:

- ModelOutput existence;
- output capture completeness;
- Provider receipt of exact request bytes;
- provider-internal success;
- business success.

### 3.4 failed

failed means the application observed the attempt terminate through an error condition other than the separately recorded timeout, cancellation, or interrupted-stream cases.

Error taxonomy is provider/adapter metadata and is not frozen in Part D.

### 3.5 timeout

timeout means the application/runtime ended or classified the attempt because its timeout condition was reached.

A timed-out attempt can still have a partial ModelOutput if application-visible model content had already been captured.

### 3.6 cancelled

cancelled means the application/runtime records that it intentionally cancelled the in-progress attempt.

Cancellation does not imply that the Provider stopped processing at the same instant or at all.

### 3.7 interrupted

interrupted means application-visible response production began but the response/stream ended abnormally before normal completion was observed.

An interrupted attempt can have a partial ModelOutput.

### 3.8 unknown

unknown preserves inability to classify the attempt lifecycle more precisely.

## 4. Retry, failover, and hedging

### 4.1 Multiple attempts are not automatically sequential

One ModelInvocation can contain multiple ProviderAttempts that are:

- sequential retries;
- sequential failovers;
- concurrent or overlapping hedges;
- otherwise related;
- relation unknown.

Attempt timestamps do not by themselves define retry causality or a total order.

### 4.2 Attempt relationship assertion

When the Producer knows the relationship, it can record an optional relationship such as:

~~~text
retry_of
failover_from
hedged_with
unknown
~~~

This is a Producer assertion about orchestration.

The exact wire representation is unfrozen.

### 4.3 Multiple successful/returning attempts

More than one ProviderAttempt in the same ModelInvocation can produce ModelOutput, especially with hedging or race strategies.

Part D therefore distinguishes:

~~~text
attempt produced output
~~~

from:

~~~text
invocation accepted output
~~~

## 5. Accepted ModelOutput

### 5.1 Purpose

A ModelInvocation can designate at most one ModelOutput as its accepted/effective logical result.

The accepted-output relation records which output the application selected as the logical result of the invocation.

Other recorded ModelOutputs remain part of provenance.

### 5.2 No accepted output

A ModelInvocation can have no accepted output when:

- all attempts failed;
- the invocation was cancelled or abandoned;
- outputs were observed but rejected;
- capture is incomplete;
- selection is unknown.

Absence of an accepted-output relation in a supplied Receipt does not prove that the application never accepted an output.

### 5.3 Accepted output need not be complete

An application can accept a partial or interrupted output.

The accepted-output relation therefore does not upgrade response termination or output capture extent.

## 6. Model identity claims

Part D distinguishes several model-identity concepts.

### 6.1 Invocation-requested model

The logical invocation can carry the Producer-recorded model label requested or intended by the application.

This can be absent or unknown.

### 6.2 Attempt-effective requested model

A ProviderAttempt can have an effective requested model visible in its effective RequestSnapshot lineage.

This can differ across attempts because of:

- fallback;
- routing configured by the application;
- alias substitution;
- provider-specific request preparation.

Where the effective request representation is available, the requested label can be representation-verified as request content.

### 6.3 Provider-reported model

A response or SDK result can report a model identifier.

C2ATrace records this as provider-reported/application-observed metadata.

It does not independently prove which internal model actually produced the response.

### 6.4 Provider-internal model identity

The actual provider-internal model implementation, deployment, router result, expert path, or hidden model version remains unknown unless a future recognized provider-evidence profile establishes it.

### 6.5 Requested versus reported mismatch

A mismatch between requested and provider-reported model labels is recorded rather than normalized away.

The verifier does not decide that one label is the true internal model identity.

## 7. ModelOutput ownership and cardinality

### 7.1 ModelOutput role

A ModelOutput is an immutable Artifact representing the terminal assembled application-visible model-result representation captured for one ProviderAttempt.

Core v0.1 models the application-visible result after provider-adapter processing.

Raw provider wire-response snapshots are outside this core object and can be introduced by a future response-evidence profile.

### 7.2 Attempt ownership

Every ModelOutput belongs to exactly one ProviderAttempt.

Core v0.1 designates at most one effective ModelOutput per ProviderAttempt.

An attempt can have no ModelOutput.

### 7.3 Partial ModelOutput

A ModelOutput can represent partial application-visible content when the attempt times out, is interrupted, is cancelled after content arrival, or instrumentation captures only part of the result.

Partial output remains an immutable Artifact once recorded.

### 7.4 Output identity

ModelOutput identity is occurrence-based.

Equal content commitments do not merge ModelOutputs from:

- different attempts;
- different invocations;
- repeated provider choices;
- repeated application operations.

## 8. Response termination and capture extent

Part D uses two independent axes.

### 8.1 Response Termination

Response Termination describes whether the application observed the provider-adapter model response reach its normal completion boundary.

Conceptual values:

~~~text
complete
incomplete
unknown
~~~

This is Producer-recorded response-lifecycle evidence.

### 8.2 Output Capture Extent

Output Capture Extent describes whether instrumentation claims to have captured all application-visible model-output content within its declared capture scope.

Conceptual values:

~~~text
complete
partial
unknown
~~~

The default declared scope for core ModelOutput is:

> application-visible model-result content delivered through the instrumented adapter boundary for the ProviderAttempt.

Capture extent is not provider-internal completion.

### 8.3 Independent axes

Examples:

~~~text
response_termination = complete
capture_extent = partial

response_termination = incomplete
capture_extent = complete
~~~

The second case means instrumentation captured all content that became application-visible before the abnormal termination; it does not mean the Provider finished the intended response.

### 8.4 Attempt disposition does not collapse the axes

A completed attempt can have partial or unknown output capture.

An interrupted or timed-out attempt can have complete capture of the application-visible partial content that arrived before termination.

## 9. OutputItem identity and cardinality

### 9.1 OutputItem ownership

Every OutputItem belongs to exactly one ModelOutput.

One ModelOutput can contain zero or more OutputItems.

### 9.2 Occurrence identity

OutputItem identity is occurrence-based.

If two items contain identical text, structured values, or tool arguments but are two separate application-visible occurrences, they retain distinct OutputItem identities.

### 9.3 Core OutputItem kinds

Part D defines the conceptual core kinds:

~~~text
text
structured
tool_proposal
unknown
~~~

ToolProposal remains the Artifact subtype defined by Phase 0 and receives additional execution semantics in the later tool phase.

### 9.4 Item ordering

When the application-visible ModelOutput has meaningful item order, the Producer can record item position/ordinal information.

Recorded order belongs to the output representation.

Core v0.1 does not infer a total item order from timestamps.

### 9.5 No streaming mutation of OutputItem identity

Core v0.1 treats OutputItems as terminal assembled immutable items.

Streaming deltas/chunks are not represented as mutations of an existing OutputItem identity.

A future streaming-event profile can expose chunk-level evidence separately.

## 10. Text output

A text OutputItem represents application-visible text content.

Its representation commitment can bind the captured text under an applicable representation basis.

Text equality or digest equality does not establish:

- hidden reasoning;
- token-level provider generation history;
- causal relation to a source;
- provider-internal exact token sequence.

If the application-visible text is partial, the ModelOutput capture/termination state preserves that limitation.

## 11. Structured output

A structured OutputItem represents an application-visible structured result.

The structured data model and commitment profile determine what can be representation-verified.

Provider schema-validation claims, response-format compliance flags, or similar metadata remain Producer/provider-reported evidence unless independently checked.

A verifier can independently validate a supplied structured representation against an applicable schema when that schema and verification profile are available, but Part D does not freeze such a schema-validation profile.

## 12. ToolProposal output

A ToolProposal is an OutputItem representing an application-visible proposal to invoke a tool.

Part D establishes only output-layer ownership:

~~~text
ProviderAttempt
→ ModelOutput
→ ToolProposal
~~~

It does not establish:

- ToolExecution;
- ToolInvocation equality;
- model causal responsibility;
- external side effect.

The later tool phase defines ToolProposal → ToolInvocation → ToolExecution semantics.

If the provider/SDK emits multiple tool proposals, each proposal has its own OutputItem identity even when tool names or arguments match.

## 13. Streaming semantics

### 13.1 Core assembly boundary

Core v0.1 records the terminal assembled ModelOutput available when the application's observation of the attempt ends.

It does not require chunk-by-chunk stream provenance.

### 13.2 Streaming assembly mode

The Producer can record whether ModelOutput was assembled from:

~~~text
non_streaming_result
streaming_result
unknown
~~~

This is descriptive capture metadata.

### 13.3 Stream chunk omission

Absence of chunk-level records does not imply that streaming did not occur.

A terminal assembled ModelOutput can be valid without preserving individual deltas.

### 13.4 Partial stream

If a stream ends abnormally after application-visible content arrives, the attempt can be interrupted, response termination can be incomplete, and a partial ModelOutput can record the assembled content observed before interruption.

### 13.5 Finish reason

Provider- or SDK-reported finish reasons are recorded as reported metadata.

A finish reason does not independently establish response completeness, output capture completeness, or provider-internal stopping cause.

## 14. Attempt-to-output claim matrix

| Claim | Evidence basis | Core v0.1 interpretation |
|---|---|---|
| Attempt A belongs to Invocation I | STRUCTURAL + PRODUCER_ASSERTED grouping | Recorded logical grouping |
| Attempt A disposition=timeout | PRODUCER_ASSERTED | Application-observed timeout classification |
| A retry_of B | PRODUCER_ASSERTED | Orchestration relationship |
| Attempt A references requested model M | STRUCTURAL/REPRESENTATION when request supplied | Requested model label, not internal identity |
| ModelOutput O belongs to Attempt A | STRUCTURAL + PRODUCER_ASSERTED occurrence premise | Recorded output ownership |
| O has capture_extent=complete | PRODUCER_ASSERTED | Complete relative to declared application-visible capture scope |
| O response_termination=complete | PRODUCER_ASSERTED | Normal response completion observed |
| Invocation I accepted O | PRODUCER_ASSERTED | Application-selected logical result |
| Text item digest matches supplied text | REPRESENTATION | Captured representation match |
| Structured item validates against supplied schema | REPRESENTATION, if independently checked | Schema conformance only |
| Provider-reported model=M | PRODUCER_ASSERTED/provider-reported | Does not establish internal model |
| Provider actually used internal model M | unsupported by core | Requires provider evidence |
| completed attempt means capture complete | PROHIBITED_INFERENCE | Separate axes |
| accepted output means response complete | PROHIBITED_INFERENCE | Selection does not upgrade completeness |
| finish_reason means hidden stopping cause is proven | PROHIBITED_INFERENCE | Reported metadata only |

## 15. Normative requirements

### OUT-001 — Invocation identity is occurrence-based

A verifier MUST NOT merge distinct ModelInvocation identities solely because their request representations, model labels, parameters, timestamps, or outputs are equal.

Planned test: model-invocation-no-content-merge-001.

### OUT-002 — Attempt grouping is explicit

A verifier MUST NOT infer that two ProviderAttempts belong to the same ModelInvocation solely from request equality, output equality, model label, or temporal proximity.

Planned test: model-attempt-grouping-no-inference-001.

### OUT-003 — Attempt ownership

Every ProviderAttempt MUST reference exactly one ModelInvocation.

Planned test: model-attempt-owner-001.

### OUT-004 — Zero-attempt invocation

A conforming representation MUST permit a ModelInvocation with zero ProviderAttempts.

Planned test: model-invocation-zero-attempt-001.

### OUT-005 — Invocation status is not derived from receipt completeness

A verifier MUST NOT infer a terminal ModelInvocation disposition solely from the attempts or outputs present in the supplied Receipt.

Planned test: model-invocation-status-no-inference-001.

### OUT-006 — Attempt starts before it exists

A Producer MUST NOT create a ProviderAttempt solely to represent a logical invocation that was rejected, cancelled, or abandoned before any physical/application-side attempt began.

Planned test: model-no-phantom-attempt-001.

### OUT-007 — Attempt terminal disposition is single-valued

A terminal ProviderAttempt MUST have at most one terminal disposition in the core Part D vocabulary.

Planned test: model-attempt-terminal-disposition-001.

### OUT-008 — Completed is not output completeness

A verifier MUST NOT infer ModelOutput existence, response completeness, or capture completeness solely from ProviderAttempt disposition=completed.

Planned test: model-attempt-completed-no-output-upgrade-001.

### OUT-009 — Timeout can retain partial output

A conforming representation MUST permit a timed-out ProviderAttempt to own a partial ModelOutput when application-visible model content was captured before timeout.

Planned test: model-timeout-partial-output-001.

### OUT-010 — Interrupted can retain partial output

A conforming representation MUST permit an interrupted ProviderAttempt to own a partial ModelOutput.

Planned test: model-interrupted-partial-output-001.

### OUT-011 — Cancellation is not Provider-stop proof

A verifier MUST NOT report ProviderAttempt cancellation as proof that the Provider stopped processing at the same time or stopped processing at all.

Planned test: model-cancel-no-provider-stop-001.

### OUT-012 — Attempt relationships are explicit

A verifier MUST NOT infer retry_of, failover_from, hedged_with, or equivalent orchestration relationships solely from attempt order or timestamps.

Planned test: model-attempt-relation-no-inference-001.

### OUT-013 — Attempt relation preserves concurrency

A verifier MUST NOT impose a total retry order on attempts recorded as concurrent/hedged or whose ordering relationship is unknown.

Planned test: model-hedge-no-total-order-001.

### OUT-014 — Multiple attempts can produce outputs

A conforming representation MUST permit more than one ProviderAttempt in one ModelInvocation to own ModelOutputs.

Planned test: model-multiple-attempt-outputs-001.

### OUT-015 — Accepted output cardinality

A ModelInvocation MUST NOT designate more than one ModelOutput as its accepted/effective logical result in core v0.1.

Planned test: model-accepted-output-cardinality-001.

### OUT-016 — Accepted output belongs to invocation

A ModelOutput designated as accepted by a ModelInvocation MUST belong to a ProviderAttempt owned by that same ModelInvocation.

Planned test: model-accepted-output-owner-001.

### OUT-017 — Accepted output is not completeness proof

A verifier MUST NOT infer response completion or capture completeness solely because a ModelOutput is designated as accepted.

Planned test: model-accepted-output-no-completeness-001.

### OUT-018 — No accepted output does not prove no acceptance

Absence of an accepted-output relation in the supplied Receipt MUST NOT be reported as proof that the application never accepted an output.

Planned test: model-accepted-output-absence-001.

### OUT-019 — Requested model is not internal model identity

A verifier MUST NOT report an invocation-requested or attempt-effective requested model label as proof of provider-internal model identity.

Planned test: model-requested-not-internal-001.

### OUT-020 — Provider-reported model is reported evidence

A verifier MUST NOT upgrade a provider-reported model identifier to independently verified provider-internal model identity without a recognized provider-evidence profile.

Planned test: model-reported-model-no-upgrade-001.

### OUT-021 — Requested/reported mismatch is preserved

When both requested and provider-reported model identifiers are recorded and differ, a conforming representation MUST preserve both values rather than normalize them into one model identity.

Planned test: model-identity-mismatch-preserved-001.

### OUT-022 — Hidden routing remains unknown

A verifier MUST NOT infer provider-internal routing, hidden fallback, deployment identity, expert selection, or model version solely from request and application-visible response metadata.

Planned test: model-hidden-routing-unknown-001.

### OUT-023 — ModelOutput attempt ownership

Every ModelOutput MUST reference exactly one ProviderAttempt.

Planned test: model-output-attempt-owner-001.

### OUT-024 — Effective ModelOutput cardinality

A ProviderAttempt MUST NOT designate more than one effective ModelOutput in core v0.1.

Planned test: model-output-effective-cardinality-001.

### OUT-025 — ModelOutput is application-visible boundary

A verifier MUST NOT describe core ModelOutput as an exact raw provider wire response or provider-internal representation solely from its ModelOutput identity.

Planned test: model-output-boundary-001.

### OUT-026 — Output identity is occurrence-based

A verifier MUST NOT merge distinct ModelOutput identities solely because their representations or commitments match.

Planned test: model-output-no-content-merge-001.

### OUT-027 — Partial output is valid

A conforming representation MUST permit ModelOutput capture extent to be partial or unknown.

Planned test: model-output-partial-valid-001.

### OUT-028 — Response termination is explicit

A ModelOutput with recorded response-termination state MUST use one of complete, incomplete, or unknown under the core Part D semantics.

Planned test: model-response-termination-vocabulary-001.

### OUT-029 — Capture extent is explicit

A ModelOutput with recorded capture-extent state MUST use one of complete, partial, or unknown under the core Part D semantics.

Planned test: model-capture-extent-vocabulary-001.

### OUT-030 — Completion axes are independent

A verifier MUST NOT infer capture_extent=complete from response_termination=complete or infer response_termination=complete from capture_extent=complete.

Planned test: model-completion-axes-independent-001.

### OUT-031 — Complete capture is scope-bounded

A verifier MUST NOT report capture_extent=complete as proof that the Provider generated no additional hidden, lost-before-boundary, or provider-internal output.

Planned test: model-capture-complete-scope-001.

### OUT-032 — Attempt disposition does not determine capture extent

A verifier MUST NOT derive ModelOutput capture extent solely from ProviderAttempt terminal disposition.

Planned test: model-attempt-status-no-capture-inference-001.

### OUT-033 — OutputItem ownership

Every OutputItem MUST reference exactly one ModelOutput.

Planned test: model-output-item-owner-001.

### OUT-034 — Zero or more OutputItems

A conforming representation MUST permit a ModelOutput containing zero OutputItems.

Planned test: model-output-zero-items-001.

### OUT-035 — OutputItem occurrence identity

A verifier MUST NOT merge distinct OutputItem identities solely because their text, structured representation, tool name, arguments, or commitments match.

Planned test: model-output-item-no-content-merge-001.

### OUT-036 — Core OutputItem kind

A core v0.1 OutputItem MUST identify exactly one conceptual kind from text, structured, tool_proposal, or unknown.

Planned test: model-output-item-kind-001.

### OUT-037 — Unknown OutputItem kind remains unknown

A verifier MUST NOT infer a stronger OutputItem kind solely from payload shape, field names, or content similarity when the recorded kind is unknown.

Planned test: model-output-item-kind-unknown-001.

### OUT-038 — Item order is not timestamp order

A verifier MUST NOT infer ModelOutput item order solely from timestamps when explicit output-position information is absent.

Planned test: model-output-item-order-no-timestamp-001.

### OUT-039 — Streaming does not mutate item identity

A conforming core v0.1 representation MUST NOT model successive streaming deltas by mutating the representation associated with an existing immutable OutputItem identity.

Planned test: model-stream-no-item-mutation-001.

### OUT-040 — Chunk absence is not non-streaming proof

Absence of stream-chunk records MUST NOT be reported as proof that the ProviderAttempt was non-streaming.

Planned test: model-stream-absence-not-negation-001.

### OUT-041 — Partial stream preserves incompleteness

When a stream terminates abnormally before normal completion is observed, a verifier MUST NOT report response_termination=complete solely because a partial ModelOutput exists.

Planned test: model-partial-stream-no-complete-001.

### OUT-042 — Streaming assembly is application-visible representation

A verifier MUST NOT infer raw provider chunk boundaries, token boundaries, or wire ordering solely from a terminal assembled ModelOutput.

Planned test: model-stream-assembly-no-wire-inference-001.

### OUT-043 — Finish reason is reported metadata

A verifier MUST NOT report a provider/SDK finish reason as independently verified provider-internal stopping cause or as proof of capture completeness.

Planned test: model-finish-reason-no-upgrade-001.

### OUT-044 — ToolProposal is not execution

A verifier MUST NOT infer ToolInvocation or ToolExecution solely from ToolProposal presence in ModelOutput.

Planned test: model-tool-proposal-no-execution-001.

### OUT-045 — ToolProposal occurrence identity

Distinct application-visible tool proposal occurrences MUST retain distinct ToolProposal/OutputItem identities even when tool names and arguments are identical.

Planned test: model-tool-proposal-occurrence-001.

### OUT-046 — Text output is not hidden reasoning

A verifier MUST NOT report a text OutputItem as hidden reasoning, chain-of-thought, or token-level internal generation history solely because it is model output text.

Planned test: model-text-no-hidden-reasoning-001.

### OUT-047 — Structured output validation is bounded

If a verifier independently validates a structured OutputItem against a supplied schema/profile, it MUST NOT upgrade that result beyond representation/schema conformance.

Planned test: model-structured-validation-bounded-001.

### OUT-048 — Attempt-to-output relation is not Provider truth

A verifier MUST NOT report the ProviderAttempt → ModelOutput relation as independent proof that the Provider or a particular internal model generated exactly that representation.

Planned test: model-attempt-output-no-provider-truth-001.

### OUT-049 — Missing ModelOutput is not no-output proof

Absence of ModelOutput for a ProviderAttempt in the supplied Receipt MUST NOT be reported as proof that no application-visible model output existed.

Planned test: model-output-absence-not-negation-001.

### OUT-050 — Output capture does not establish request receipt

A verifier MUST NOT use ModelOutput existence by itself as proof that the Provider received the exact prepared_http_body recorded for the ProviderAttempt.

Planned test: model-output-no-exact-request-receipt-001.

## 16. Adversarial architecture review

### Review A — First attempt times out, second succeeds

~~~text
Invocation I
  Attempt A → timeout
  Attempt B → completed → Output O
  accepted_output = O
~~~

The invocation does not inherit failure from Attempt A.

Result: RESOLVED by OUT-005 and OUT-015 through OUT-017.

### Review B — Timeout after partial text

~~~text
Attempt A
  some text observed
  timeout
  ModelOutput O:
    response_termination = incomplete
    capture_extent = complete
~~~

Complete capture means all application-visible content observed before timeout was captured. It does not mean the model response was complete.

Result: RESOLVED by OUT-009 and OUT-030 through OUT-032.

### Review C — Provider response completes but instrumentation drops an item

~~~text
response_termination = complete
capture_extent = partial
~~~

Normal provider-adapter termination does not repair missing capture.

Result: RESOLVED by OUT-030.

### Review D — Hedged requests both return

~~~text
Attempt A → Output OA
Attempt B → Output OB
accepted_output = OB
~~~

Both outputs remain recorded; accepted output is explicit.

Result: RESOLVED by OUT-014 through OUT-016.

### Review E — Hedged attempts overlap in time

Timestamp order does not create retry causality or a total order.

Result: RESOLVED by OUT-012 and OUT-013.

### Review F — Same prompt intentionally called twice

Two logical application operations using identical RequestSnapshots remain two ModelInvocations.

Result: RESOLVED by OUT-001.

### Review G — Failover changes requested model

~~~text
Invocation requested model = alias-A

Attempt A effective request = provider/model-A
Attempt B effective request = provider/model-B

Provider reports model-C for B
~~~

All labels are preserved. Core does not decide which hidden model actually executed.

Result: RESOLVED by OUT-019 through OUT-022.

### Review H — SDK reports model name from alias

Provider-reported metadata can be stored but is not internal-model attestation.

Result: RESOLVED by OUT-020.

### Review I — Completed attempt but output capture failed entirely

ProviderAttempt can be completed with no ModelOutput in the supplied provenance.

Core does not invent output.

Result: RESOLVED by OUT-008 and OUT-049.

### Review J — Failed stream still produced a tool proposal

A ToolProposal can exist in a partial ModelOutput before interruption.

Its existence does not imply ToolInvocation or execution.

Result: RESOLVED by OUT-010 and OUT-044.

### Review K — Two identical tool calls in one response

They remain separate ToolProposal identities because they are distinct occurrences.

Result: RESOLVED by OUT-035 and OUT-045.

### Review L — Streaming text grows over time

Core does not mutate one immutable TextOutput identity for each delta.

It records terminal assembled immutable items; chunk-level evidence belongs to a future profile.

Result: RESOLVED by OUT-039 and OUT-042.

### Review M — Provider finish_reason says stop but local stream was truncated

finish_reason metadata does not override capture_extent=partial.

Result: RESOLVED by OUT-043.

### Review N — Application accepts partial output

accepted_output can reference a partial ModelOutput.

Acceptance does not upgrade completeness.

Result: RESOLVED by OUT-017 and OUT-027.

### Review O — Receipt omits the winning attempt

A supplied partial Receipt can contain an invocation but not the accepted-output relation or winning attempt.

Verifier cannot infer that no accepted output existed.

Result: RESOLVED by OUT-018 and Phase 0 completeness rules.

### Review P — ModelOutput text equals known prompt text

String equality does not establish causal copying, hidden reasoning, or source derivation.

Any provenance relation requires explicit derivation/inclusion evidence under earlier phases.

Result: RESOLVED by OUT-046 and Phase 1 Part B.

### Review Q — Provider returns structured object and local schema validation succeeds

The verifier can report schema conformance when independently checked, but not semantic correctness or provider-internal generation guarantees.

Result: RESOLVED by OUT-047.

### Review R — Provider returns error body containing text

An adapter/provider error payload is not automatically a ModelOutput merely because it contains text.

ModelOutput is reserved for the application-visible model-result representation classified as such by the Producer/adapter.

Result: RESOLVED conceptually; provider adapter contract will define error/result classification.

### Review S — Provider response exists, therefore exact request must have been received

A model output can support a broad Producer assertion that some request attempt elicited a response, but it does not prove that the exact recorded prepared body bytes were the bytes received by the Provider.

Result: RESOLVED by OUT-050 and Part C.

### Review T — Application starts a continuation after accepted output

A continuation/follow-up is a new logical ModelInvocation rather than another retry attempt when the application records it as a new logical operation.

Result: RESOLVED by the invocation identity model.

## 17. Architecture revisions caused by Part D

### 17.1 Invocation accepted-output relation

Part D adds an explicit semantic distinction between:

~~~text
ProviderAttempt produced ModelOutput
~~~

and:

~~~text
ModelInvocation accepted ModelOutput
~~~

This is necessary for retry, failover, hedging, and race strategies.

### 17.2 ProviderAttempt success boolean is rejected

Core Part D does not use one success boolean to represent attempt outcome.

Instead it separates:

~~~text
attempt lifecycle/disposition
response termination
output capture extent
~~~

### 17.3 ModelOutput is one application-visible result boundary

Core ModelOutput is the terminal assembled application-visible model-result representation for one ProviderAttempt.

Raw provider wire-response evidence and streaming chunk evidence are future profiles rather than overloaded into ModelOutput.

### 17.4 OutputItem remains independently identified

ModelOutput is a container/aggregate Artifact whose items retain their own occurrence identities.

ToolProposal is an OutputItem subtype and remains separate from later ToolInvocation and ToolExecution.

## 18. Part D resolved decisions

Part D locks the following decisions:

1. ModelInvocation identity is occurrence-based, not request-content-based.
2. Retry/failover/hedge grouping is explicit Producer-recorded orchestration, not inferred from timestamps or equality.
3. ProviderAttempt has application-observed lifecycle/disposition separate from output semantics.
4. More than one attempt in one invocation can produce output.
5. One invocation has at most one accepted/effective ModelOutput in core v0.1.
6. Acceptance does not imply completeness.
7. Requested, effective-requested, provider-reported, and provider-internal model identities are distinct claim levels.
8. One ModelOutput belongs to exactly one ProviderAttempt; one attempt has at most one effective core ModelOutput.
9. ModelOutput is the terminal assembled application-visible result boundary, not raw provider wire response.
10. Response Termination and Output Capture Extent are independent axes.
11. Output capture completeness is bounded to application-visible captured content and does not imply provider-internal completeness.
12. Every OutputItem belongs to exactly one ModelOutput and has occurrence identity.
13. Core OutputItem kinds are text, structured, tool_proposal, and unknown.
14. Core streaming semantics preserve terminal assembly and partial/incomplete state without mutating OutputItem identity.
15. Finish reason is reported metadata, not provider-internal proof.
16. ToolProposal presence does not imply ToolInvocation or ToolExecution.
17. Attempt-to-output linkage is recorded provenance, not independent proof of exact Provider/model generation.
18. ModelOutput existence does not prove receipt of exact request bytes.

## 19. Open items handed to later phases

Part D intentionally does not freeze:

- JSON field names or enum serialization;
- detailed Provider error taxonomy;
- chunk-level streaming event schema;
- raw provider response snapshot model;
- transport/provider acknowledgement evidence;
- schema-validation profile for StructuredOutput;
- provider-originated model-identity attestation;
- exact ToolProposal argument representation rules;
- tool-call execution semantics;
- token usage/accounting provenance;
- logprobs or token-level output evidence;
- multi-choice/provider-specific candidate metadata beyond OutputItems.

These remain constrained by Part D semantics.

## 20. Gate decision

Phase 1 Part D: PASS AFTER ADVERSARIAL REVIEW.

The next specification work is:

~~~text
Phase 1 Part E
ToolProposal / ToolInvocation / ToolExecution / ToolResult / EffectObservation
~~~

JSON Schema and implementation remain BLOCKED.
