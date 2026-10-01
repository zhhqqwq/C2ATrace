# C2ATrace v0.1 — Tool Adapter Contract

Status: ACCEPTED AFTER ADVERSARIAL REVIEW.

Scope: Tool Adapter responsibility and visibility boundary; capability declaration; ToolProposal/ToolDecision association; effective ToolInvocation capture; argument-level provenance; execution-start boundary; ToolExecution lifecycle; retry/replay/duplicate/idempotency capture; ToolResult capture including streaming; remote/tool-server metadata; EffectObservation evidence acquisition; privacy-aware secret arguments/results; CaptureDiagnostic reuse; instrumentation failure versus tool-runtime failure; execution/effect/outcome evidence boundaries.

JSON Schema: NOT FROZEN.

Implementation: NOT STARTED.

## 1. Purpose

The Tool Adapter Contract translates the accepted Part E semantics into concrete capture obligations for implementations observing an application-visible tool-runtime boundary.

It answers:

- where a tool adapter can claim observation;
- how the final effective ToolInvocation is captured;
- when ToolExecution begins;
- how proposal/decision provenance is associated without being invented;
- how effective argument lineage is preserved;
- how retries, replay, duplicates, and idempotency are represented;
- what constitutes a ToolResult;
- how streaming result capture is assembled;
- how remote/tool-server metadata is classified;
- when EffectObservation can be created and with what evidence basis;
- how privacy and instrumentation failure affect evidence strength.

The contract preserves the Part E separations:

~~~text
ToolProposal
≠
ToolDecision
≠
ToolInvocation
≠
ToolExecution
≠
ToolResult
≠
EffectObservation
≠
OutcomeVerification
~~~

and:

~~~text
allowed
≠
executed

execution completed
≠
tool semantic success
≠
external Effect occurred

effect observed
≠
desired Outcome achieved
~~~

## 2. Tool Adapter role and visibility boundary

### 2.1 Tool Adapter

A Tool Adapter is instrumentation at an application-visible boundary where an application/runtime prepares, authorizes, starts, observes, or completes a tool execution.

Examples include:

- local function-call wrappers;
- MCP client/tool-call adapters;
- tool SDK/runtime wrappers;
- application command executors;
- database/file/API tool wrappers;
- remote-tool client libraries.

One logical Tool Adapter can combine several hooks.

### 2.2 Visibility ceiling

The Tool Adapter claim ceiling is the most specific boundary it actually observes.

Observation of ToolProposal does not imply ToolInvocation.

Observation of ToolInvocation does not imply ToolExecution.

Observation of ToolExecution start does not imply remote-server receipt.

Observation of ToolResult does not imply external Effect truth.

Observation of an EffectObservation does not imply desired Outcome verification.

### 2.3 Tool-internal and remote boundaries

A client-side Tool Adapter does not automatically observe:

- remote tool-server receipt;
- remote internal retries;
- remote database/file transaction commit;
- hidden remote transformations;
- remote side-effect cardinality;
- remote idempotency enforcement.

Such facts remain unknown unless separate evidence is available.

## 3. Tool Adapter capability declaration

A conforming Tool Adapter exposes a capability declaration identifying at least:

- adapter implementation identity/version metadata;
- effective ToolInvocation capture boundary;
- ToolExecution start/completion boundary;
- ToolResult capture boundary;
- supported argument representation/path schemes;
- whether ToolProposal lineage can be observed/accepted;
- whether ToolDecision capture is supported;
- whether streaming ToolResult capture is supported;
- whether retry/replay/duplicate orchestration can be observed;
- whether EffectObservation acquisition is supported and by which basis kinds;
- supported privacy treatments.

The exact wire shape remains unfrozen.

The declaration describes intended capability, not proof that every runtime tool operation was captured correctly.

## 4. Baseline Tool Adapter capability

A baseline Tool Adapter supports:

1. capture or explicit receipt of the effective ToolInvocation representation at the declared pre-execution boundary;
2. observation of ToolExecution start for visible executions;
3. observation of ToolExecution terminal lifecycle when visible;
4. capture of the application-visible terminal ToolResult when successfully observed;
5. CaptureDiagnostic for known degradation of supported/applicable capture slots.

ToolProposal association, ToolDecision capture, streaming, separate effect observation, and remote transport evidence are capability-declared extensions to this baseline.

An execution-only hook without a defensible effective ToolInvocation boundary is a subordinate capture component rather than a standalone baseline Tool Adapter.

## 5. CaptureDiagnostic reuse

Tool Adapter uses the CaptureDiagnostic Assertion defined by Provider Adapter Contract.

Typical Tool Adapter slots include:

~~~text
ToolProposal association
ToolDecision capture
effective ToolInvocation capture
argument provenance capture
ToolExecution tracking
ToolResult capture
stream-result assembly
remote metadata capture
EffectObservation acquisition
~~~

The same states apply:

~~~text
observed
partial
unavailable
unsupported
bypass_detected
unknown
~~~

CaptureDiagnostic remains bounded instrumentation evidence and is never a no-bypass or complete-history certificate.

## 6. ToolProposal association boundary

### 6.1 Proposal visibility is optional

A baseline Tool Adapter is not required to observe ToolProposal.

When ToolProposal association capability is absent, the adapter does not invent proposal ancestry.

A ToolInvocation can legitimately exist without ToolProposal ancestry under Part E.

### 6.2 Positive association

When the Tool Adapter receives a ToolProposal identity/context from an upstream C2ATrace-aware provider/application layer, it can preserve that association and the explicit ToolPreparation Transform/Derivation evidence.

### 6.3 Matching is insufficient

Equal tool names, arguments, provider tool-call IDs, timestamps, or message positions do not by themselves establish ToolProposal → ToolInvocation lineage.

### 6.4 Multiple proposal candidates

If multiple ToolProposals could correspond to one invocation and the adapter cannot establish which contributed, provenance remains unknown/ambiguous rather than choosing by similarity.

## 7. ToolDecision capture boundary

### 7.1 Decision capability

A Tool Adapter records ToolDecision only when it observes or explicitly receives a real application/policy decision occurrence.

It does not manufacture a ToolDecision solely to make execution history appear authorized.

### 7.2 Proposal-level denial

If a proposal is denied before ToolInvocation preparation, the adapter can record ToolDecision(deny) on the ToolProposal when that boundary is observed.

It does not create ToolInvocation or ToolExecution solely for the denial.

### 7.3 Invocation-level denial

If an effective ToolInvocation exists and is denied before execution begins, ToolDecision can target that ToolInvocation.

The ToolInvocation remains recorded.

No ToolExecution is created solely because the denial occurred.

### 7.4 Allow is not inferred from execution

The existence of ToolExecution does not imply that an explicit ToolDecision(allow) existed.

Some systems execute without an explicit decision object; others can execute despite a prior deny due to override, bug, bypass, or later decision.

### 7.5 Conflicting decisions

Multiple ToolDecisions can exist for the same proposal/invocation.

The adapter preserves occurrence identities, bases, and ordering/provenance that it actually observes rather than collapsing them into one final authorization truth.

## 8. Effective ToolInvocation boundary

### 8.1 Effective invocation meaning

The effective ToolInvocation is the immutable execution-relevant application-side representation immediately before one or more ToolExecution attempts can begin.

It includes as applicable:

- effective logical tool identifier;
- effective argument representation;
- execution-relevant options;
- idempotency/request identifiers;
- runtime-selected environment/tenant/repository context;
- other application-visible execution-relevant metadata.

It is not automatically the exact remote wire request.

### 8.2 Final application-visible form

The adapter captures ToolInvocation only after application-visible validation/normalization/enrichment/policy rewrite stages included before its declared execution boundary.

An earlier candidate invocation is not labelled as the effective ToolInvocation if later visible modifications occur before execution.

### 8.3 Immutable invocation identity

If execution-relevant representation changes, a new ToolInvocation identity is required.

If one immutable ToolInvocation is genuinely reused unchanged for retries/replays, multiple ToolExecutions can reference it.

### 8.4 Equality is not reuse

Equal arguments/digests do not prove that two executions reused the same ToolInvocation occurrence.

Actual reuse/correlation must be established.

### 8.5 Tool alias/resolution

If the application resolves a logical tool alias/name to another executable target while retaining the same logical invocation representation, the adapter preserves both semantic roles when they matter.

It does not silently overwrite the model/application logical tool identifier with a remote endpoint/function implementation identifier.

## 9. Tool preparation and argument provenance

### 9.1 ToolPreparation Transform

When a ToolInvocation is prepared from ToolProposal and/or application/runtime/policy Artifacts, the adapter records the ToolPreparation Transform and positive Derivation only when that lineage is actually known.

### 9.2 Argument Regions

For JSON-model arguments, json_pointer is the interoperable argument path scheme, consistent with Part E.

If another argument representation is used, the adapter identifies an applicable representation/path profile or preserves weaker/unknown mapping.

### 9.3 model_supplied

The adapter classifies an argument scope as model_supplied only when explicit positive representation ancestry supports ToolProposal-side contribution and no non-proposal representation contributor is present for that scope.

### 9.4 application_supplied

The adapter classifies an argument scope as application_supplied only when positive representation ancestry supports non-proposal application/runtime/policy contribution and no ToolProposal representation contributor is present for that scope.

### 9.5 mixed

mixed requires both ToolProposal-derived and non-ToolProposal representation contributors.

### 9.6 unknown

When exact lineage does not justify model_supplied, application_supplied, or mixed, the adapter uses unknown rather than inferring origin from who constructed the final object.

### 9.7 Control versus content

Validation schemas, allowlists, budgets, policy rules, feature flags, and configuration that affect control flow do not become argument representation contributors unless positive Derivation shows content contribution.

### 9.8 Normalization and rewrite

If normalization/rewrite changes representation, the effective ToolInvocation records the changed value and the lineage precision allowed by Part B.

The adapter does not claim exact equality with the proposal merely because the semantic argument path is the same.

### 9.9 Dropped proposal arguments

A ToolProposal argument omitted from the effective ToolInvocation remains proposal/control history where applicable but is not represented as an effective argument.

### 9.10 Application enrichment

Application/runtime-added secrets, tenant IDs, repository IDs, defaults, auth context, or routing values are not classified model_supplied merely because they accompany a model-proposed tool call.

## 10. Logical tool arguments versus transport/runtime metadata

The Tool Adapter distinguishes logical ToolInvocation arguments from execution/transport metadata when the tool API itself distinguishes them.

Examples of metadata that are not automatically logical model/tool arguments include:

- authorization headers/tokens;
- TLS/connection state;
- retry counters;
- remote endpoint address;
- tracing headers;
- transport-specific request IDs.

Such fields can remain execution-relevant ToolInvocation metadata when required for execution, but proximity to logical arguments does not create ToolProposal ancestry or model_supplied classification.

## 11. Execution-start boundary

### 11.1 ToolExecution occurrence

A ToolExecution is created only once execution actually begins at the adapter's declared tool-runtime boundary.

### 11.2 Pre-start failures

Validation error, policy denial, setup failure, missing credential, queue rejection, or cancellation before the declared execution-start boundary does not create ToolExecution solely to represent the failure.

The failure can be represented through ToolDecision, preparation/diagnostic metadata, or another applicable record.

### 11.3 Remote-call client boundary

For a remote tool client, ToolExecution can begin when the application/tool runtime initiates the remote execution attempt at the declared client boundary.

This does not prove remote server receipt or execution.

### 11.4 Local function boundary

For a local function tool, ToolExecution can begin when control is transferred into the instrumented tool implementation boundary.

### 11.5 One execution occurrence

Distinct observed execution attempts retain distinct ToolExecution identities even if all inputs and results are equal.

## 12. ToolExecution lifecycle contract

The adapter derives ToolExecution disposition from application/runtime-observed lifecycle evidence.

Core terminal dispositions remain:

~~~text
completed
failed
timeout
cancelled
interrupted
unknown
~~~

completed means the declared runtime observed normal return/completion.

It does not mean semantic success, Effect truth, Outcome success, or exactly-once behavior.

A timeout/cancellation can occur after the external operation already happened.

An interrupted result stream can have partial ToolResult evidence.

## 13. Retry / replay / duplicate contract

### 13.1 Visible retries are new executions

A visible retry of the same immutable ToolInvocation creates a new ToolExecution.

### 13.2 Changed invocation requires new ToolInvocation

If retry preparation changes effective arguments, tool target, execution-relevant options, or idempotency metadata, the changed representation gets a new ToolInvocation identity.

### 13.3 retry_of

retry_of is recorded only when application/runtime orchestration evidence establishes that relationship.

It does not prove the prior execution had no effect.

### 13.4 replay_of

replay_of is recorded only when the application/runtime intentionally replays a prior effective invocation/execution context and the adapter observes that orchestration.

It does not prove the remote system treated it as a replay.

### 13.5 duplicate_of

duplicate_of is Producer/runtime orchestration evidence and does not prove duplicate remote execution or duplicate external Effect.

### 13.6 Hidden runtime/server retries

Retries hidden inside the tool implementation, remote SDK, server, database driver, or network layer remain unknown unless separately observed.

## 14. Idempotency contract

### 14.1 Idempotency metadata

An idempotency key/token is recorded as execution-relevant ToolInvocation metadata when it affects execution.

### 14.2 Key privacy

Idempotency keys can be privacy-protected under Part G while preserving bounded equality/commitment evidence.

### 14.3 No remote guarantee inference

Presence or reuse of an idempotency key does not establish:

- remote idempotency support;
- correct remote enforcement;
- exactly-once execution;
- exactly-once Effect;
- absence of duplicate work.

### 14.4 Provider/server report

A remote/tool-server claim that a request was deduplicated remains tool_reported metadata unless independently verified.

## 15. ToolResult boundary

### 15.1 Application-visible result

ToolResult represents the terminal assembled application-visible result representation exposed by the declared tool-runtime boundary for one ToolExecution.

### 15.2 Zero or one result

One ToolExecution has zero or one core terminal ToolResult.

Intermediate events/chunks do not create additional core ToolResults.

### 15.3 Normal return versus exception

A normal return value or tool-protocol error result can be ToolResult if it is application-visible result representation.

A thrown runtime exception, transport exception, timeout diagnostic, or instrumentation exception is not automatically ToolResult unless the tool API exposes it as the tool result representation.

### 15.4 Equal result content

Equal result content/provider IDs do not merge ToolResults from distinct ToolExecutions.

### 15.5 Capture extent

ToolResult capture_extent reflects what the adapter actually captured within its declared application-visible result scope.

It is independent from ToolExecution disposition and tool-reported success.

## 16. Streaming ToolResult contract

### 16.1 Streaming capability

An adapter claiming streaming ToolResult support observes the application-visible stream/result-consumption boundary, not merely creation of a stream/iterator/subscription.

### 16.2 Terminal assembly

The adapter assembles one terminal immutable ToolResult from the streaming events it actually observed according to tool/protocol event semantics.

### 16.3 Event semantics

The adapter distinguishes delta, cumulative, replacement, indexed, structured-event, and other declared event forms.

It does not blindly concatenate all payloads as deltas.

### 16.4 Partial result

If application-visible result content was observed before abnormal termination, provenance evidence for that content is retained according to configured privacy treatment.

### 16.5 Lost events

Known loss of result events prevents capture_extent=complete for the affected scope.

### 16.6 Consumer stop

If the application stops consuming a tool-result stream, the adapter does not infer remote completion, remote cancellation, or effect cardinality solely from local consumption ending.

### 16.7 Baseline chunk retention

Persistent chunk-level provenance is not required by the baseline Tool Adapter Contract.

A future tool-stream evidence profile can add chunk artifacts/events without mutating core ToolResult identity.

## 17. Tool/runtime metadata origin

Semantics-bearing tool metadata distinguishes origin when relevant:

~~~text
application_supplied
adapter_observed
tool_reported
adapter_derived
external_observed
unknown
~~~

Examples include:

- remote request/job IDs;
- result status/error codes;
- transaction IDs;
- cache/deduplication indicators;
- server timestamps;
- row counts;
- affected-object IDs;
- remote version/build identifiers.

tool_reported means the application-visible tool/server response reported the value.

external_observed means a distinct observation source independently supplied the value to the adapter.

adapter_derived means the adapter normalized or computed the value from other evidence.

Origin classes describe evidence source, not factual truth.

## 18. Remote/tool-server metadata boundary

Tool/server IDs do not replace C2ATrace ToolInvocation, ToolExecution, ToolResult, or EffectObservation identities.

A tool-reported transaction ID does not prove transaction commit.

A tool-reported affected-row count does not independently prove database state.

A tool-reported created-object ID does not independently prove object existence.

A tool-reported server timestamp is not trusted time.

If the adapter normalizes provider/tool-specific metadata, the normalized value is adapter_derived and retains a bounded mapping basis when available.

## 19. Tool success semantics

The adapter keeps separate:

~~~text
ToolExecution disposition
ToolResult reported status
EffectObservation
Outcome
~~~

Examples:

~~~text
ToolExecution completed
+
ToolResult status = error
~~~

is possible.

~~~text
ToolExecution completed
+
ToolResult status = success
+
EffectObservation absent/unknown
~~~

is also possible.

The adapter does not convert a "success" status directly into objective Effect truth.

## 20. EffectObservation acquisition capability

### 20.1 Optional capability

A baseline Tool Adapter is not required to produce EffectObservation.

If it declares EffectObservation capability, it identifies the evidence-basis kinds it can support.

### 20.2 execution_result basis

The adapter can create EffectObservation(basis=execution_result) only when it records a bounded external-state proposition actually reported/supported by the associated ToolResult.

A generic success flag alone is not automatically a specific effect proposition.

### 20.3 separate_observation basis

The adapter can create EffectObservation(basis=separate_observation) only when a distinct observation occurrence/evidence Artifact exists apart from the effect-causing execution's ToolResult.

Examples include:

- follow-up GET/read;
- database query;
- filesystem stat/read;
- separate API lookup;
- independent observer artifact.

### 20.4 Observation identity

A separate observation is represented as its own Artifact/ToolResult/SourceObservation or applicable evidence object.

Copying the original ToolResult into another field does not make it a separate observation.

### 20.5 external_attestation basis

external_attestation requires a separately identified evidence Artifact/profile.

The label alone does not create independent verification.

### 20.6 unknown basis

If the adapter cannot establish the evidence basis, it uses unknown rather than upgrading to separate_observation.

### 20.7 Multiple evidence Artifacts

Multiple supporting artifacts can be recorded, but evidence count alone does not create objective truth.

## 21. Effect claim boundary

The adapter scopes EffectObservation to propositions its evidence actually supports.

Examples of bounded claims include:

- "follow-up read reported issue 123 exists";
- "filesystem stat reported path X exists";
- "tool result reported remote object ID 123";
- "database follow-up query returned row R".

It does not silently broaden these into:

- "the intended business transaction succeeded";
- "the object will persist";
- "all side effects completed";
- "no other effects occurred";
- "the desired Outcome was achieved".

## 22. Effect causality boundary

A ToolExecution/ToolResult being temporally associated with a later external-state observation does not by itself prove that the execution caused the state.

C2ATrace can record supported_by and explicit provenance/evidence relationships but does not infer external causality from timing or identifier equality.

## 23. Privacy-aware ToolInvocation capture

### 23.1 Runtime observation versus disclosure

Successful runtime capture of effective arguments remains distinct from Receipt privacy treatment.

### 23.2 Secret arguments

Secret arguments can be exported full, hash_only, hmac, redacted/mixed, or withheld according to Part G without replacing their historical runtime values with placeholders.

### 23.3 Commitment-before-discard

When plaintext arguments will not be retained/exported, commitment evidence is computed from the exact observed effective representation basis before the plaintext becomes unavailable, or the claim is downgraded if only reconstruction remains.

### 23.4 Placeholder safety

"***", "[REDACTED]", "<secret>", or null are not recorded as effective ToolInvocation values unless those values were actually executed.

### 23.5 Argument provenance survives privacy conservatively

Structural argument lineage can remain recorded for withheld values, but representation-verification strength is bounded by available commitments/capabilities.

## 24. Privacy-aware ToolResult capture

ToolResult can use full/hash_only/hmac/redacted/mixed disclosure profiles.

Privacy treatment does not convert a known ToolResult capture failure into success.

A provenance-bearing redacted ToolResult is a derivative Artifact under Part G and does not reuse the original ToolResult identity for changed representation.

A signed/private ToolResult commitment authenticates only the disclosed commitment evidence under Part H; it does not make unavailable result plaintext directly signed.

## 25. Privacy-aware remote/effect metadata

Remote IDs, idempotency keys, transaction IDs, paths, row keys, object IDs, effect claims, and follow-up observation values can themselves be sensitive.

Privacy treatment can narrow their disclosure but does not change their evidence origin or turn tool_reported evidence into separate_observation.

Withholding EffectObservation evidence can reduce verification strength but cannot strengthen the effect claim.

## 26. Adapter failure and instrumentation degradation

### 26.1 Known invocation capture failure

If the adapter knows the effective ToolInvocation capture slot failed, it records bounded degradation and does not fabricate effective arguments.

### 26.2 Execution tracking failure

Instrumentation failure while execution may continue does not by itself classify ToolExecution as failed/cancelled/timeout/completed.

Lifecycle uses separately observed runtime evidence or unknown.

### 26.3 Result capture failure

If result capture fails after execution begins, the adapter does not fabricate ToolResult from logs, error strings, or presumed values.

### 26.4 Effect-observer failure

Failure of a follow-up EffectObservation check is not rewritten as "effect absent" unless the observation semantics/evidence positively establish absence.

### 26.5 Adapter exception versus tool exception

An adapter/instrumentation exception is not labelled as a tool/runtime/server error unless that origin was actually observed.

### 26.6 Privacy is not failure

Privacy withholding does not by itself set CaptureDiagnostic to unavailable/partial when runtime observation succeeded.

## 27. Bypass semantics

bypass_detected requires positive evidence that an applicable tool operation traversed a path outside the declared Tool Adapter boundary.

Missing expected records alone do not prove bypass.

A detected bypass does not authorize reconstruction of unobserved ToolInvocation/ToolExecution/ToolResult as adapter-observed provenance.

Absence of bypass_detected does not prove no bypass occurred.

## 28. Multiple instrumentation layers

When several hooks observe the same tool operation, the adapter correlates them as one ToolExecution only when actual occurrence correlation supports it.

Equal arguments, same idempotency key, same remote request ID, same transaction ID, or equal result content do not alone prove one execution occurrence.

Lower-level hooks can contribute additional evidence to one ToolExecution when correlation is positive.

## 29. Unknown downgrade rules

When the adapter cannot justify stronger claims, it preserves unknown/absence as permitted.

Examples include:

- ToolProposal ancestry unknown;
- ToolDecision absent/unknown;
- argument provenance unknown;
- ToolExecution disposition unknown;
- retry/replay/duplicate relation unknown;
- ToolResult capture_extent unknown;
- metadata origin unknown;
- EffectObservation basis unknown;
- external Effect truth unknown;
- remote receipt/commit/effect cardinality unknown;
- CaptureDiagnostic unknown.

Unknown is not denied, failed, safe, successful, effect-absent, or outcome-failed.

## 30. Adapter assertions versus independently verifiable evidence

### 30.1 Adapter/runtime occurrence assertions

Ordinarily Producer/instrumentation assertions include:

- ToolInvocation occurrence at the effective boundary;
- ToolExecution occurrence/lifecycle;
- ToolDecision observation;
- retry/replay/duplicate orchestration;
- CaptureDiagnostic state/reason;
- ToolResult occurrence at the runtime boundary;
- metadata origin classification;
- EffectObservation acquisition occurrence/basis.

Signing authenticates the recorded assertions; it does not make them external truth.

### 30.2 Representation evidence

Supplied ToolInvocation/ToolResult representations and commitments can be independently checked to the extent allowed by Parts B/E/G/H.

Representation consistency does not independently prove that the adapter observed the representation at the claimed runtime boundary.

### 30.3 Remote execution remains bounded

A client-side ToolExecution occurrence does not prove remote server receipt, remote commit, remote side-effect cardinality, or remote completion.

### 30.4 Effect evidence remains per-basis

execution_result evidence remains tool-reported.

separate_observation remains bounded by its observation source.

external_attestation remains bounded by its evidence profile.

No basis automatically becomes objective outcome verification.

## 31. Baseline conformance requirements

### TAD-001 — Tool Adapter visibility is declared and bounded

A conforming Tool Adapter MUST limit default claims to application/runtime-visible evidence at its declared boundaries and MUST NOT claim hidden remote/tool-server state without separate evidence.

Planned test: tool-adapter-visibility-boundary-001.

### TAD-002 — Tool Adapter boundary declaration

A conforming Tool Adapter MUST declare its effective ToolInvocation boundary, ToolExecution start/completion boundary, and ToolResult boundary.

Planned test: tool-adapter-boundary-declaration-001.

### TAD-003 — Tool Adapter capability declaration

A conforming Tool Adapter MUST declare whether it supports ToolProposal association, ToolDecision capture, streaming ToolResult capture, orchestration relationships, EffectObservation acquisition, and applicable privacy treatments.

Planned test: tool-adapter-capability-declaration-001.

### TAD-004 — Baseline effective invocation capability

A baseline Tool Adapter MUST support capture or explicit receipt of the effective ToolInvocation representation at its declared pre-execution boundary.

Planned test: tool-adapter-effective-invocation-capability-001.

### TAD-005 — Baseline execution capability

A baseline Tool Adapter MUST support observation of visible ToolExecution start and terminal lifecycle at its declared runtime boundary.

Planned test: tool-adapter-execution-capability-001.

### TAD-006 — Baseline result capability

A baseline Tool Adapter MUST support capture of the application-visible terminal ToolResult when that result is successfully observed at its declared boundary.

Planned test: tool-adapter-result-capability-001.

### TAD-007 — Capability is not occurrence proof

A verifier MUST NOT infer that a tool occurrence was captured solely from the Tool Adapter capability declaration.

Planned test: tool-adapter-capability-not-observation-001.

### TAD-008 — Tool Adapter does not infer remote receipt

A Tool Adapter MUST NOT report remote tool-server receipt/execution solely from application-side ToolExecution start.

Planned test: tool-adapter-no-remote-receipt-001.

### TAD-009 — CaptureDiagnostic slot is bounded

A Tool Adapter CaptureDiagnostic MUST identify a bounded tool capture subject/scope and slot.

Planned test: tool-capture-diagnostic-scope-001.

### TAD-010 — CaptureDiagnostic semantics are reused unchanged

A Tool Adapter MUST use the core CaptureDiagnostic states with the same bounded semantics defined by Provider Adapter Contract and MUST NOT redefine observed as global tool-coverage completeness.

Planned test: tool-capture-diagnostic-reuse-001.

### TAD-011 — Missing diagnostic is not capture success

A verifier MUST NOT infer successful tool capture solely because no CaptureDiagnostic reports degradation.

Planned test: tool-capture-diagnostic-absence-not-success-001.

### TAD-012 — No no-bypass inference

A verifier MUST NOT infer absence of tool-path bypass solely because no bypass_detected diagnostic is present.

Planned test: tool-capture-no-bypass-inference-001.

### TAD-013 — Diagnostic conflicts are preserved

Conflicting Tool Adapter CaptureDiagnostics for the same bounded slot/scope MUST be preserved/reported absent explicit resolution evidence and MUST NOT be resolved by timestamp or insertion order alone.

Planned test: tool-capture-diagnostic-conflict-001.

### TAD-014 — Proposal capability is optional

A Tool Adapter without declared ToolProposal association capability MUST NOT invent ToolProposal ancestry for ToolInvocation.

Planned test: tool-proposal-capability-optional-001.

### TAD-015 — Proposal linkage requires positive evidence

A Tool Adapter MUST NOT infer ToolProposal → ToolInvocation lineage solely from matching tool names, arguments, provider IDs, timestamps, or message positions.

Planned test: tool-proposal-link-positive-001.

### TAD-016 — Ambiguous proposal linkage remains ambiguous

When multiple ToolProposals are plausible contributors and the adapter cannot establish one or more actual contributors, it MUST preserve unknown/ambiguity rather than select by similarity.

Planned test: tool-proposal-link-ambiguous-001.

### TAD-017 — ToolDecision requires observed/received decision occurrence

A Tool Adapter MUST NOT create ToolDecision solely to imply authorization; it MUST observe or explicitly receive a real application/policy decision occurrence.

Planned test: tool-decision-positive-occurrence-001.

### TAD-018 — Proposal denial creates no fake invocation/execution

When denial occurs before ToolInvocation preparation, a Tool Adapter MUST NOT create ToolInvocation or ToolExecution solely to represent the denial.

Planned test: tool-proposal-denial-no-fake-execution-001.

### TAD-019 — Invocation denial creates no fake execution

When a ToolInvocation is denied before execution begins, a Tool Adapter MUST NOT create ToolExecution solely to represent the denial.

Planned test: tool-invocation-denial-no-fake-execution-001.

### TAD-020 — Execution does not imply allow decision

A Tool Adapter/verifier MUST NOT infer ToolDecision(allow) solely from ToolExecution occurrence.

Planned test: tool-execution-no-implicit-allow-001.

### TAD-021 — Deny does not erase later execution

A Tool Adapter MUST preserve a recorded deny decision even if a later ToolExecution occurs and MUST NOT rewrite the history to make the denial disappear.

Planned test: tool-deny-later-execution-001.

### TAD-022 — Conflicting decisions remain occurrence evidence

A Tool Adapter MUST preserve distinct ToolDecision occurrences/bases rather than collapse them into one objective authorization state.

Planned test: tool-decision-conflict-preserved-001.

### TAD-023 — Effective ToolInvocation is final visible pre-execution representation

A Tool Adapter MUST NOT label an earlier candidate as the effective ToolInvocation when it observes later application-visible execution-relevant modification before execution.

Planned test: tool-effective-invocation-final-boundary-001.

### TAD-024 — ToolInvocation is not remote wire request by default

A verifier MUST NOT interpret ToolInvocation as exact remote transport bytes/request unless a separate capture/evidence profile establishes that representation.

Planned test: tool-invocation-not-wire-request-001.

### TAD-025 — Changed effective representation gets new ToolInvocation identity

When execution-relevant ToolInvocation representation changes, the Tool Adapter MUST use a new ToolInvocation identity.

Planned test: tool-invocation-mutation-new-id-001.

### TAD-026 — Invocation reuse requires actual reuse

A Tool Adapter MUST NOT reuse one ToolInvocation identity across executions solely because arguments/digests are equal; actual reuse of the same immutable effective invocation must be established.

Planned test: tool-invocation-reuse-not-equality-001.

### TAD-027 — Logical tool identity and executable target are not silently conflated

When logical tool identity and resolved executable/endpoint identity differ and both are semantically relevant, the adapter MUST preserve their distinct roles rather than overwrite one with the other.

Planned test: tool-logical-vs-executable-identity-001.

### TAD-028 — ToolPreparation lineage requires positive evidence

A Tool Adapter MUST NOT create ToolPreparation Transform/Derivation lineage from ToolProposal/application/runtime/policy Artifacts unless the relevant use/contribution is actually recorded/known.

Planned test: tool-preparation-lineage-positive-001.

### TAD-029 — Argument path/profile is explicit

A Tool Adapter recording argument-level provenance MUST identify the applicable argument representation/path scheme and MUST NOT silently treat runtime-native indices/paths as json_pointer when semantics differ.

Planned test: tool-argument-path-profile-001.

### TAD-030 — model_supplied requires positive proposal ancestry

A Tool Adapter MUST NOT classify an argument scope model_supplied without positive ToolProposal-side representation ancestry.

Planned test: tool-argument-model-supplied-positive-001.

### TAD-031 — application_supplied requires positive non-proposal ancestry

A Tool Adapter MUST NOT classify an argument scope application_supplied merely because application code constructed the final ToolInvocation; positive non-proposal representation ancestry is required.

Planned test: tool-argument-app-supplied-positive-001.

### TAD-032 — mixed requires both representation contributor classes

A Tool Adapter MUST NOT classify an argument scope mixed without both ToolProposal-derived and non-ToolProposal representation contributors.

Planned test: tool-argument-mixed-positive-001.

### TAD-033 — Unknown argument provenance is preserved

When positive lineage is insufficient for model_supplied/application_supplied/mixed, the Tool Adapter MUST use unknown rather than guess.

Planned test: tool-argument-provenance-unknown-001.

### TAD-034 — Control input is not argument content by default

A Tool Adapter MUST NOT classify policy/schema/configuration/control inputs as argument representation contributors without positive Derivation evidence.

Planned test: tool-argument-control-not-content-001.

### TAD-035 — Rewritten argument is the effective value

When visible normalization/policy/application rewrite changes an argument, the ToolInvocation MUST record the changed effective representation and MUST NOT retain the pre-rewrite value as though it were executed.

Planned test: tool-argument-rewrite-effective-001.

### TAD-036 — Dropped proposal argument is not effective argument

A Tool Adapter MUST NOT record a proposal argument omitted before execution as part of effective ToolInvocation content.

Planned test: tool-argument-dropped-not-effective-001.

### TAD-037 — Application enrichment is not model-supplied by proximity

Application/runtime-added secrets, IDs, defaults, auth context, routing values, or environment data MUST NOT be classified model_supplied solely because the invocation originated from a ToolProposal.

Planned test: tool-argument-enrichment-origin-001.

### TAD-038 — Transport metadata is not proposal argument ancestry by proximity

Authorization/transport/runtime metadata MUST NOT acquire ToolProposal ancestry solely because it accompanies the same execution request.

Planned test: tool-transport-metadata-no-proposal-ancestry-001.

### TAD-039 — Execution begins only at declared execution-start boundary

A Tool Adapter MUST create ToolExecution only when execution actually begins at its declared runtime boundary.

Planned test: tool-execution-start-boundary-001.

### TAD-040 — Pre-start failure creates no fake ToolExecution

A Tool Adapter MUST NOT create ToolExecution solely for validation, policy, setup, credential, queue, or cancellation failure occurring before the declared execution-start boundary.

Planned test: tool-prestart-failure-no-execution-001.

### TAD-041 — Remote client execution does not prove remote server start

For remote tools, a client-side ToolExecution start MUST NOT be reported as proof that the remote server received or started the operation.

Planned test: tool-client-start-no-remote-start-001.

### TAD-042 — Distinct executions have distinct identities

A Tool Adapter MUST preserve distinct ToolExecution identities for distinct observed execution attempts even when invocation/result content is equal.

Planned test: tool-execution-distinct-identity-001.

### TAD-043 — Execution disposition is runtime-observed

A Tool Adapter MUST derive ToolExecution disposition from application/runtime-observed lifecycle evidence and MUST NOT equate tool-reported success/status with execution disposition without corresponding lifecycle observation.

Planned test: tool-execution-disposition-boundary-001.

### TAD-044 — completed is not effect success

A verifier MUST NOT interpret ToolExecution disposition=completed as proof of tool semantic success, external Effect, Outcome success, or exactly-once behavior.

Planned test: tool-completed-not-effect-001.

### TAD-045 — timeout does not imply no effect

A Tool Adapter/verifier MUST NOT infer that no remote/external effect occurred solely because ToolExecution timed out.

Planned test: tool-timeout-not-no-effect-001.

### TAD-046 — cancellation does not prove remote stop

A Tool Adapter/verifier MUST NOT infer remote processing stopped solely from local ToolExecution cancellation.

Planned test: tool-cancel-no-remote-stop-001.

### TAD-047 — Visible retry creates new ToolExecution

A Tool Adapter observing a retry attempt MUST create a distinct ToolExecution rather than reuse the prior ToolExecution identity.

Planned test: tool-retry-new-execution-001.

### TAD-048 — Changed retry invocation gets new ToolInvocation

If retry preparation changes effective arguments, tool target, execution-relevant options, or idempotency metadata, the Tool Adapter MUST create a new ToolInvocation identity for the changed representation.

Planned test: tool-retry-changed-invocation-001.

### TAD-049 — retry_of requires orchestration evidence

A Tool Adapter MUST NOT assert retry_of solely from timing, equal arguments, timeout, or remote IDs without positive application/runtime retry orchestration evidence.

Planned test: tool-retry-relation-positive-001.

### TAD-050 — retry_of does not negate prior effect

A Tool Adapter/verifier MUST NOT interpret retry_of as proof that the prior execution had no external effect.

Planned test: tool-retry-no-prior-effect-inference-001.

### TAD-051 — replay_of requires orchestration evidence

A Tool Adapter MUST NOT assert replay_of solely from identical ToolInvocation content or idempotency key equality.

Planned test: tool-replay-relation-positive-001.

### TAD-052 — duplicate_of is not duplicate Effect proof

A Tool Adapter/verifier MUST NOT interpret duplicate_of as proof that duplicate external effects occurred or did not occur.

Planned test: tool-duplicate-relation-bounded-001.

### TAD-053 — Hidden tool/runtime retries are not invented

A Tool Adapter MUST NOT create ToolExecutions for retries hidden below its visibility boundary without separate positive evidence.

Planned test: tool-hidden-retry-no-inference-001.

### TAD-054 — Idempotency key is execution metadata

A Tool Adapter MUST preserve idempotency metadata as part of the execution-relevant ToolInvocation when applicable and MUST NOT use key equality as ToolExecution identity.

Planned test: tool-idempotency-metadata-001.

### TAD-055 — Idempotency does not establish exactly-once

A Tool Adapter/verifier MUST NOT infer remote idempotency support, correct enforcement, exactly-once execution, or exactly-once Effect solely from idempotency-key presence/reuse.

Planned test: tool-idempotency-no-exactly-once-001.

### TAD-056 — Tool-reported deduplication remains reported

A remote/tool-server statement that a call was deduplicated MUST remain tool_reported evidence unless independently verified.

Planned test: tool-idempotency-reported-dedup-001.

### TAD-057 — ToolResult is application-visible result

A Tool Adapter MUST represent ToolResult from the declared application-visible tool-result boundary and MUST NOT substitute unrelated logs/transport diagnostics as result content.

Planned test: tool-result-boundary-001.

### TAD-058 — Core ToolResult cardinality

A Tool Adapter MUST NOT emit more than one core terminal ToolResult for one ToolExecution.

Planned test: tool-result-cardinality-001.

### TAD-059 — Exception is not automatically ToolResult

A Tool Adapter MUST NOT create ToolResult solely from a thrown runtime/transport/instrumentation exception unless the tool API exposes that exception/error representation as the application-visible tool result.

Planned test: tool-exception-not-result-001.

### TAD-060 — ToolResult occurrence identity is preserved

A Tool Adapter MUST NOT merge ToolResults from distinct ToolExecutions solely because representations, status, remote IDs, or commitments match.

Planned test: tool-result-no-merge-001.

### TAD-061 — ToolResult capture extent follows capture evidence

A Tool Adapter MUST NOT set ToolResult capture_extent=complete solely from ToolExecution disposition=completed or a tool-reported success/status.

Planned test: tool-result-capture-evidence-001.

### TAD-062 — Streaming support requires result-consumption visibility

A Tool Adapter declaring streaming ToolResult support MUST observe the application-visible result stream/event-consumption boundary, not only stream creation.

Planned test: tool-stream-result-consumption-001.

### TAD-063 — Streaming assembly follows tool event semantics

A Tool Adapter MUST assemble streaming ToolResult according to declared tool/protocol event semantics and MUST NOT blindly concatenate cumulative/replacement/indexed events as deltas.

Planned test: tool-stream-result-semantics-001.

### TAD-064 — Unsupported stream semantics degrade precision

If correct result-stream assembly semantics are unsupported/unknown, the Tool Adapter MUST use partial/unknown capture semantics rather than fabricate a complete ToolResult.

Planned test: tool-stream-result-unsupported-001.

### TAD-065 — Partial streaming result evidence is preserved

When application-visible tool-result content is observed before abnormal termination, the adapter MUST preserve provenance evidence for that observed content according to configured privacy treatment.

Planned test: tool-stream-result-partial-preserve-001.

### TAD-066 — Lost result events prevent complete capture

If the adapter knows application-visible ToolResult events were lost/unprocessed, it MUST NOT report ToolResult capture_extent=complete for the affected scope.

Planned test: tool-stream-result-loss-001.

### TAD-067 — Consumer stop is not remote completion

A Tool Adapter MUST NOT infer remote tool completion/cancellation/effect cardinality solely because the application stopped consuming a result stream.

Planned test: tool-stream-consumer-stop-bounded-001.

### TAD-068 — Chunk retention is optional

A baseline Tool Adapter MAY omit persistent result-chunk provenance while preserving a correct terminal ToolResult and bounded streaming/capture metadata.

Planned test: tool-stream-chunks-optional-001.

### TAD-069 — Tool metadata origin is explicit when semantically relevant

A Tool Adapter MUST distinguish application_supplied, adapter_observed, tool_reported, adapter_derived, external_observed, or unknown origin when metadata interpretation depends on origin.

Planned test: tool-metadata-origin-001.

### TAD-070 — Tool-reported metadata remains reported

A Tool Adapter MUST NOT restate remote/tool-server status, IDs, timestamps, row counts, affected-object IDs, transaction IDs, cache/deduplication indicators, or version values as independently verified external facts solely because the tool reported them.

Planned test: tool-metadata-reported-bounded-001.

### TAD-071 — Remote IDs are not C2ATrace identity

A Tool Adapter MUST NOT use remote request/job/transaction/object IDs as substitutes for ToolInvocation, ToolExecution, ToolResult, or EffectObservation identities.

Planned test: tool-remote-id-not-c2a-identity-001.

### TAD-072 — Tool-reported transaction ID is not commit proof

A verifier MUST NOT infer transaction commit/external persistence solely from a tool-reported transaction ID or success flag.

Planned test: tool-transaction-id-no-commit-proof-001.

### TAD-073 — Tool/server timestamps are not trusted time

A verifier MUST NOT report tool/server-reported timestamps as trusted wall-clock time without a separate trusted-time profile.

Planned test: tool-server-time-bounded-001.

### TAD-074 — Normalized tool metadata is adapter-derived

When the adapter normalizes tool-specific metadata, it MUST classify the normalized value as adapter_derived and preserve an available mapping/source basis under the configured privacy treatment.

Planned test: tool-metadata-normalized-origin-001.

### TAD-075 — Tool success does not establish Effect

A Tool Adapter/verifier MUST NOT infer external Effect truth solely from ToolResult success/status.

Planned test: tool-success-no-effect-proof-001.

### TAD-076 — EffectObservation capability is explicit

A Tool Adapter producing EffectObservation MUST declare the evidence-basis kinds it supports and MUST NOT imply independent effect verification merely from capability declaration.

Planned test: tool-effect-capability-declaration-001.

### TAD-077 — execution_result effect claim requires bounded proposition

EffectObservation(basis=execution_result) MUST identify a bounded effect proposition supported by the associated ToolResult and MUST NOT be synthesized solely from a generic success flag.

Planned test: tool-effect-execution-result-proposition-001.

### TAD-078 — separate_observation requires distinct evidence occurrence

EffectObservation(basis=separate_observation) MUST reference evidence from a distinct observation occurrence separate from the effect-causing ToolResult.

Planned test: tool-effect-separate-observation-distinct-001.

### TAD-079 — Copying ToolResult is not separate observation

A Tool Adapter MUST NOT classify copied/reformatted data from the original ToolResult as separate_observation solely because it is stored in another field/object.

Planned test: tool-effect-copy-not-independent-001.

### TAD-080 — external_attestation requires separate evidence identity/profile

EffectObservation(basis=external_attestation) MUST identify the separate attestation/evidence Artifact/profile and MUST NOT derive evidentiary strength from the label alone.

Planned test: tool-effect-external-attestation-basis-001.

### TAD-081 — Unknown effect basis is preserved

If the adapter cannot establish execution_result, separate_observation, or external_attestation basis, it MUST use unknown rather than upgrade the observation basis.

Planned test: tool-effect-basis-unknown-001.

### TAD-082 — Evidence count does not create truth

A Tool Adapter/verifier MUST NOT upgrade EffectObservation to objective external truth solely because multiple supporting Artifacts exist.

Planned test: tool-effect-multiple-evidence-bounded-001.

### TAD-083 — Effect claim scope is evidence-bounded

A Tool Adapter MUST NOT broaden an EffectObservation beyond the external-state proposition actually supported/reported by its evidence.

Planned test: tool-effect-claim-scope-001.

### TAD-084 — EffectObservation is not OutcomeVerification

A Tool Adapter/verifier MUST NOT report EffectObservation as proof that the desired application/business Outcome was achieved.

Planned test: tool-effect-not-outcome-001.

### TAD-085 — Temporal association is not external causality

A Tool Adapter/verifier MUST NOT infer that a ToolExecution caused an observed external state solely from timestamps, proximity, or matching external identifiers.

Planned test: tool-effect-no-causal-inference-001.

### TAD-086 — Runtime argument capture and privacy disclosure are separate

A Tool Adapter MUST NOT infer argument capture failure solely because ToolInvocation values are exported hash_only, hmac, redacted, mixed, or withheld.

Planned test: tool-privacy-argument-capture-separation-001.

### TAD-087 — Secret placeholders are not effective arguments

A Tool Adapter MUST NOT record masking/redaction placeholders as effective ToolInvocation argument values unless those exact values were executed.

Planned test: tool-privacy-placeholder-not-effective-001.

### TAD-088 — Argument commitment-before-discard uses exact observed basis

When privacy configuration retains only commitment evidence for effective arguments, the Tool Adapter MUST compute it from the exact observed effective representation before that representation becomes unavailable, or downgrade if only reconstruction remains.

Planned test: tool-privacy-argument-commit-before-discard-001.

### TAD-089 — Argument privacy does not strengthen provenance

A Tool Adapter/verifier MUST NOT report stronger argument Derivation/provenance merely because the value is withheld for privacy.

Planned test: tool-privacy-argument-no-upgrade-001.

### TAD-090 — ToolResult privacy is disclosure-only

A Tool Adapter MUST NOT treat hash_only/hmac/redacted/withheld ToolResult disclosure as evidence that runtime result capture failed when capture actually succeeded.

Planned test: tool-privacy-result-capture-separation-001.

### TAD-091 — Redacted ToolResult uses derivative identity

A provenance-bearing changed redacted ToolResult representation MUST use a distinct derivative Artifact identity and MUST NOT replace the original ToolResult representation under the same identity.

Planned test: tool-privacy-result-redacted-identity-001.

### TAD-092 — Privacy does not upgrade effect basis

A Tool Adapter MUST NOT classify tool_reported/execution_result evidence as separate_observation merely because the underlying values are withheld or redacted.

Planned test: tool-privacy-effect-basis-stable-001.

### TAD-093 — Known ToolInvocation capture failure is explicit

When the adapter knows a supported/applicable effective ToolInvocation capture slot failed, it MUST record bounded degradation and MUST NOT fabricate effective invocation values.

Planned test: tool-capture-invocation-failure-explicit-001.

### TAD-094 — Execution instrumentation failure is not tool failure

A Tool Adapter MUST NOT classify ToolExecution failed/cancelled/timeout/completed solely from instrumentation failure; it uses separately observed lifecycle evidence or unknown.

Planned test: tool-capture-execution-failure-separation-001.

### TAD-095 — Result capture failure does not fabricate ToolResult

If supported ToolResult capture fails, the adapter MUST preserve the degradation and MUST NOT fabricate ToolResult from logs, presumed values, or unrelated diagnostics.

Planned test: tool-capture-result-failure-no-fabrication-001.

### TAD-096 — Effect observer failure is not effect absence

A Tool Adapter MUST NOT report external Effect absent solely because a follow-up effect observation failed, timed out, or was unavailable.

Planned test: tool-effect-observer-failure-not-absence-001.

### TAD-097 — Adapter exception is not tool/server exception

A Tool Adapter MUST NOT report an instrumentation exception as a tool/runtime/server error unless that origin is actually observed.

Planned test: tool-adapter-error-origin-001.

### TAD-098 — Privacy does not hide known capture failure

A Tool Adapter MUST NOT use privacy treatment as a substitute for reporting known capture degradation.

Planned test: tool-privacy-no-failure-laundering-001.

### TAD-099 — bypass_detected requires positive evidence

A Tool Adapter MUST NOT emit bypass_detected solely from missing expected records; positive evidence of an applicable bypass is required.

Planned test: tool-bypass-positive-evidence-001.

### TAD-100 — Detected bypass does not fabricate provenance

A Tool Adapter MUST NOT reconstruct unobserved bypassed ToolInvocation/ToolExecution/ToolResult as adapter-observed historical records solely from summaries or later evidence.

Planned test: tool-bypass-no-fabrication-001.

### TAD-101 — Multiple hooks require occurrence correlation

A Tool Adapter MUST NOT merge multiple hook observations into one ToolExecution solely from equal arguments, idempotency keys, remote IDs, transaction IDs, or results; actual occurrence correlation is required.

Planned test: tool-multihook-correlation-001.

### TAD-102 — Unknown state is preserved

When stronger invocation, decision, argument, lifecycle, relationship, result, metadata-origin, effect-basis, remote-state, or capture claims cannot be justified, the Tool Adapter MUST preserve unknown/absence as permitted rather than guess.

Planned test: tool-adapter-unknown-preserved-001.

### TAD-103 — Adapter occurrence assertions remain assertions

A verifier MUST NOT upgrade Tool Adapter-recorded invocation/execution/decision/orchestration/capture/effect-observation occurrences to objective external facts solely because the Receipt is signed.

Planned test: tool-adapter-assertion-bounded-001.

### TAD-104 — Representation verification does not prove runtime observation

A verifier MUST NOT infer that the Tool Adapter factually observed ToolInvocation/ToolResult at the claimed runtime boundary solely because supplied representations/commitments are internally consistent.

Planned test: tool-representation-not-observation-proof-001.

### TAD-105 — Remote tool execution remains unestablished by client evidence

A verifier MUST NOT report remote server receipt, remote commit, remote retry count, side-effect cardinality, or remote completion solely from client-side ToolExecution/ToolResult evidence.

Planned test: tool-remote-internals-unestablished-001.

### TAD-106 — Signed capture diagnostics are not global coverage proof

A verifier MUST NOT report signed Tool Adapter CaptureDiagnostics/capability declarations as proof that all applicable tool operations were instrumented.

Planned test: tool-capture-diagnostic-no-global-completeness-001.

### TAD-107 — Adapter identity/version is not implementation trust

A verifier MUST NOT infer code authenticity, correct instrumentation behavior, or trusted Tool Adapter implementation solely from recorded adapter name/version/capability metadata.

Planned test: tool-adapter-version-no-trust-001.

### TAD-108 — Adapter timestamps are not trusted time

A verifier MUST NOT report Tool Adapter-recorded invocation/execution/capture timestamps as trusted wall-clock time without a separate trusted-time profile.

Planned test: tool-adapter-time-bounded-001.

### TAD-109 — Post-boundary execution mutation remains unknown

A Tool Adapter MUST NOT report that no execution-relevant mutation occurred after its highest observed ToolInvocation boundary when lower tool/runtime/transport layers remain outside its visibility.

Planned test: tool-invocation-post-boundary-mutation-001.

### TAD-110 — ToolDecision does not automatically govern a ToolExecution

A verifier MUST NOT infer that a ToolDecision authorized, denied, or governed a specific ToolExecution solely because the decision targets the same ToolInvocation/ToolProposal or has a nearby timestamp; an explicit applicable relation/order/basis is required for that stronger claim.

Planned test: tool-decision-no-implicit-governance-001.

### TAD-111 — EffectObservation identity is occurrence-based

A Tool Adapter MUST NOT merge distinct EffectObservation occurrences solely because they state the same proposition, reference the same external identifier, or use equal evidence representations.

Planned test: tool-effect-observation-no-merge-001.

### TAD-112 — ToolResult commitment-before-discard uses exact observed basis

When privacy configuration retains only commitment evidence for ToolResult content, the Tool Adapter MUST compute it from the exact observed ToolResult representation basis before that representation becomes unavailable, or downgrade if only reconstruction remains.

Planned test: tool-privacy-result-commit-before-discard-001.

### TAD-113 — Non-completed execution does not imply no Effect

A Tool Adapter/verifier MUST NOT infer absence of external Effect solely from ToolExecution disposition=failed, timeout, cancelled, interrupted, or unknown.

Planned test: tool-noncompleted-not-no-effect-001.

### TAD-114 — Missing ToolExecution is not negative proof under incomplete capture

A verifier MUST NOT report that execution did not occur solely because no ToolExecution is present when tool-execution capture completeness/bypass status is not independently established.

Planned test: tool-missing-execution-not-negation-001.

### TAD-115 — Missing ToolResult is not proof no result existed

A verifier MUST NOT report that the runtime/tool produced no result solely because ToolResult is absent when result capture was unavailable, partial, unsupported, bypassed, or unknown.

Planned test: tool-missing-result-not-negation-001.

### TAD-116 — external_observed metadata is not automatically separate_observation

A Tool Adapter MUST NOT classify metadata as EffectObservation(basis=separate_observation) solely because its origin is external_observed; a distinct observation occurrence/evidence Artifact satisfying TAD-078 is still required.

Planned test: tool-external-metadata-not-effect-observation-001.

### TAD-117 — Async acceptance is not remote completion/effect proof

A Tool Adapter/verifier MUST NOT interpret tool-reported accepted, queued, scheduled, pending, or job-created status as proof that the asynchronous remote operation completed, produced the claimed Effect, or achieved the Outcome.

Planned test: tool-async-acceptance-bounded-001.

### TAD-118 — Proposal-to-invocation cardinality is not assumed

A Tool Adapter MUST NOT assume a fixed one-to-one ToolProposal→ToolInvocation cardinality when explicit Transform/Derivation evidence records zero, one, or multiple relevant proposal/invocation occurrences.

Planned test: tool-proposal-invocation-cardinality-001.

## 32. Adversarial architecture review

### Review A — Model proposes a tool, executor sees only final function call

The Tool Adapter has no proposal capability.

It records ToolInvocation/ToolExecution but does not invent ToolProposal ancestry.

Result: RESOLVED by TAD-014 through TAD-016.

### Review B — Tool name/arguments exactly match a proposal

Equality still does not establish proposal → invocation lineage.

Result: RESOLVED by TAD-015.

### Review C — Policy denies before invocation preparation

ToolDecision targets ToolProposal.

No ToolInvocation or ToolExecution is fabricated.

Result: RESOLVED by TAD-018.

### Review D — Invocation prepared, then denied

The ToolInvocation remains.

No ToolExecution is created solely for denial.

Result: RESOLVED by TAD-019.

### Review E — Tool executed but no explicit policy decision exists

The execution is recorded without inventing allow.

Result: RESOLVED by TAD-020.

### Review F — Deny exists, then buggy/overridden code executes anyway

Both deny and ToolExecution remain in provenance.

Core does not rewrite history or decide authorization correctness.

Result: RESOLVED by TAD-021 and TAD-022.

### Review G — Proposal says repo="A"; app rewrites repo="B"

ToolInvocation records "B".

Argument provenance preserves rewrite/Derivation rather than pretending "A" was executed.

Result: RESOLVED by TAD-035.

### Review H — Application adds API token to model-proposed call

The token is application/runtime-supplied execution metadata/argument as appropriate, not model_supplied by proximity.

Result: RESOLVED by TAD-037 and TAD-038.

### Review I — Validator only checks schema

Schema/control input does not become argument content ancestry.

Result: RESOLVED by TAD-034.

### Review J — Two effective invocations have identical JSON

Equal content does not establish same ToolInvocation occurrence/reuse.

Result: RESOLVED by TAD-025 and TAD-026.

### Review K — Validation fails before tool implementation called

No ToolExecution is fabricated.

Result: RESOLVED by TAD-039 and TAD-040.

### Review L — Remote client sends request then times out

Client-side ToolExecution exists.

Timeout does not prove remote non-receipt or no effect.

Result: RESOLVED by TAD-041 and TAD-045.

### Review M — Local cancellation after remote request begins

Local cancellation does not prove remote server stopped.

Result: RESOLVED by TAD-046.

### Review N — Retry uses identical invocation

New ToolExecution can reference same ToolInvocation when actual reuse is established.

Result: RESOLVED by TAD-047 and TAD-026.

### Review O — Retry adds a new idempotency key

Execution-relevant representation changed, so new ToolInvocation is required.

Result: RESOLVED by TAD-048.

### Review P — Tool runtime secretly retries HTTP internally

No extra ToolExecution is invented when the retry is below visibility.

Result: RESOLVED by TAD-053.

### Review Q — Same idempotency key returns "already processed"

This is tool_reported deduplication evidence, not exactly-once proof.

Result: RESOLVED by TAD-055 and TAD-056.

### Review R — Tool returns {"success": true}

ToolResult can record it, but no objective Effect is inferred.

Result: RESOLVED by TAD-075.

### Review S — Tool function throws exception

If exception is not the tool API's result representation, no ToolResult is fabricated solely from the exception string.

Result: RESOLVED by TAD-059.

### Review T — Streaming tool emits cumulative snapshots

Adapter follows event semantics rather than concatenating duplicates.

Result: RESOLVED by TAD-063.

### Review U — Streaming result loses one event

capture_extent cannot remain complete.

Result: RESOLVED by TAD-066.

### Review V — Application stops consuming remote tool stream

No remote completion/effect-cardinality conclusion is made.

Result: RESOLVED by TAD-067.

### Review W — Tool reports transaction_id=123 and success

The ID/status remain tool_reported; commit is not independently established.

Result: RESOLVED by TAD-070 through TAD-075.

### Review X — Adapter normalizes "ok"/"created"/200 into success

Normalized success is adapter_derived and keeps bounded mapping basis.

It still does not establish Effect.

Result: RESOLVED by TAD-074 and TAD-075.

### Review Y — ToolResult says issue 123 created

The adapter can make EffectObservation(basis=execution_result) with bounded proposition "tool result reported issue 123 created".

It cannot call this independent effect verification.

Result: RESOLVED by TAD-077.

### Review Z — Adapter performs GET /issues/123 after create

The follow-up read is a distinct observation occurrence and can support basis=separate_observation.

Its source truth remains bounded.

Result: RESOLVED by TAD-078.

### Review AA — Adapter copies create result into "verification" field

Copying/reformatting is not separate observation.

Result: RESOLVED by TAD-079.

### Review AB — Follow-up GET times out

Failure to verify is not evidence that issue 123 does not exist.

Result: RESOLVED by TAD-096.

### Review AC — Effect observation says row exists after update

Temporal proximity does not prove this execution caused the row state.

Result: RESOLVED by TAD-085.

### Review AD — Tool says "email sent" and business goal was "customer read email"

Even a bounded EffectObservation about send status is not desired Outcome verification.

Result: RESOLVED by TAD-084.

### Review AE — Secret argument exported as "***"

The placeholder is not the executed value.

Use privacy withholding/commitment/redacted derivative semantics.

Result: RESOLVED by TAD-086 through TAD-089.

### Review AF — ToolResult contains secret and is HMAC-only in Receipt

Runtime result capture can still be observed while disclosure is HMAC-only.

Result: RESOLVED by TAD-090.

### Review AG — Result capture hook crashes but tool completes

ToolExecution lifecycle and result capture status remain separate.

No ToolResult is fabricated.

Result: RESOLVED by TAD-094 and TAD-095.

### Review AH — Effect observer crashes

No "effect absent" conclusion is generated.

Result: RESOLVED by TAD-096.

### Review AI — Tool Adapter bug throws

The instrumentation exception is not restated as remote/tool server failure.

Result: RESOLVED by TAD-097.

### Review AJ — Application bypasses Tool Adapter

Positive host evidence can record bypass_detected.

The adapter does not invent missed execution history, and absence of bypass evidence is not no-bypass proof.

Result: RESOLVED by TAD-012, TAD-099, and TAD-100.

### Review AK — Function wrapper and HTTP hook see the same remote call

They merge into one ToolExecution only if occurrence correlation establishes that relationship.

Result: RESOLVED by TAD-101.

### Review AL — Signed Receipt says all tool capture was observed

Signature authenticates the assertion representation, not global instrumentation completeness.

Result: RESOLVED by TAD-103, TAD-104, and TAD-106.

### Review AM — Adapter name says "official"

Recorded identity/version does not prove exact trusted code ran.

Result: RESOLVED by TAD-107.

### Review AN — Tool server returns signed-looking timestamp field

Without trusted-time evidence, it remains tool-reported time.

Result: RESOLVED by TAD-073 and TAD-108.

### Review AO — EffectObservation uses three copies of same tool result

Evidence multiplicity does not make it objective truth or separate observation.

Result: RESOLVED by TAD-079 and TAD-082.

### Review AP — Remote tool performs two hidden side effects for one completed execution

Client-side completed ToolExecution and success ToolResult do not establish side-effect cardinality.

Result: RESOLVED by TAD-105.

### Review AQ — Tool runtime injects an auth/routing value after the declared ToolInvocation boundary

The captured ToolInvocation remains the final representation at the declared visible boundary, but the adapter cannot claim the lower hidden execution request was unchanged.

Result: RESOLVED by TAD-024 and TAD-109.

### Review AR — Allow decision and execution share invocation ID but ordering/governance is unclear

The verifier does not infer that this allow authorized this execution solely from common subject or timestamp proximity.

Result: RESOLVED by TAD-110.

### Review AS — Tool writes data then throws an exception

ToolExecution can be failed while an external Effect still occurred.

Failure is not no-effect evidence.

Result: RESOLVED by TAD-113.

### Review AT — Tool Adapter loses execution hook and no ToolExecution appears

Missing execution record is not proof of no execution when capture completeness is not established.

Result: RESOLVED by TAD-114.

### Review AU — Tool returns a value but result-capture hook fails

The absent ToolResult in the Receipt is not proof that no runtime result existed.

Result: RESOLVED by TAD-115.

### Review AV — Remote monitoring metadata is tagged external_observed

The origin label alone does not make it a separate effect observation; a distinct observation occurrence/evidence Artifact is still required.

Result: RESOLVED by TAD-116.

### Review AW — Remote tool returns job_status=queued

The adapter can preserve that tool-reported status but cannot claim asynchronous job completion, Effect, or Outcome.

Result: RESOLVED by TAD-117.

### Review AX — One proposal is expanded into two effective invocations

Explicit Transform/Derivation can represent both invocation occurrences.

The adapter does not enforce an artificial 1:1 proposal/invocation assumption.

Result: RESOLVED by TAD-118.

### Review AY — HMAC-only ToolResult is discarded after commitment

The adapter computes the commitment from the exact observed result representation before plaintext becomes unavailable; later reconstruction cannot silently replace that basis.

Result: RESOLVED by TAD-112.

## 33. Architecture revisions caused by Tool Adapter Contract

### 33.1 Baseline versus optional upstream/effect capabilities

Tool Adapter baseline centers on effective ToolInvocation → ToolExecution → ToolResult.

ToolProposal association, ToolDecision capture, streaming, EffectObservation acquisition, and remote evidence are declared capabilities rather than mandatory assumptions.

This prevents downstream executors from fabricating unavailable upstream provenance.

### 33.2 CaptureDiagnostic is shared unchanged

Provider and Tool adapters use one bounded instrumentation Assertion model.

The shared states do not become global capture-completeness certificates.

### 33.3 Effective invocation is the final application-visible pre-execution representation

Argument provenance attaches to what the application/tool runtime actually selected for execution, not merely what the model proposed or an earlier candidate contained.

### 33.4 Tool lifecycle and instrumentation lifecycle remain separate

Adapter failure does not imply tool/runtime failure.

Tool timeout/cancellation does not prove absence of remote work/effect.

### 33.5 ToolResult streaming mirrors provider streaming conservatively

Streaming requires result-consumption visibility and protocol-aware assembly.

Chunk persistence remains optional.

### 33.6 Effect evidence is an optional explicit acquisition layer

execution_result, separate_observation, external_attestation, and unknown remain distinct.

Separate observation requires a genuinely distinct observation occurrence.

### 33.7 Tool metadata origin is explicit

tool_reported, adapter_derived, adapter_observed, external_observed, application_supplied, and unknown are not collapsed.

This prevents remote status/transaction metadata from becoming independent Effect proof.

## 34. Contract decisions

The Tool Adapter Contract locks:

1. Tool Adapter visibility is application/runtime-side and boundary-declared.
2. Baseline conformance requires effective ToolInvocation, ToolExecution, ToolResult, and bounded capture diagnostics.
3. ToolProposal association and ToolDecision capture are optional declared capabilities.
4. ToolProposal ancestry is never inferred from equality/proximity.
5. ToolDecision is captured only from a real observed/received decision occurrence.
6. Execution does not imply explicit allow; denial does not erase later execution.
7. Effective ToolInvocation is the final visible execution-relevant pre-execution representation; lower post-boundary mutation remains unknown.
8. Changed effective representation requires new ToolInvocation identity.
9. Argument provenance uses positive Derivation and preserves control/content separation.
10. Application enrichment/secrets are not model_supplied by proximity.
11. ToolExecution begins only at the declared runtime boundary; pre-start failures do not create fake execution.
12. Client-side remote execution does not prove remote receipt/start.
13. Retry/replay/duplicate relationships require orchestration evidence and do not establish effect cardinality.
14. Idempotency metadata does not establish exactly-once behavior.
15. ToolResult is the application-visible terminal result representation, with zero-or-one core cardinality per execution.
16. Streaming ToolResult support requires consumption visibility and protocol-aware assembly.
17. Tool/server metadata origin is explicit and reported values remain reported evidence.
18. Tool-reported success/transaction IDs do not establish external Effect/commit.
19. EffectObservation acquisition is optional and evidence-basis-declared.
20. separate_observation requires a distinct observation occurrence; metadata origin labels alone do not create it.
21. EffectObservation identities are occurrence-based, remain evidence-bounded, and are not OutcomeVerification.
22. Temporal association/identifier equality do not establish external causality.
23. Privacy disclosure is orthogonal to runtime argument/result capture.
24. Instrumentation failure is distinct from tool/runtime failure; missing execution/result records are not negative proof when capture is unresolved.
25. Failed/timeout/cancelled/interrupted execution and Effect-observer failure are not effect-absence proof.
26. bypass_detected requires positive evidence and does not reconstruct missed provenance.
27. Adapter assertions remain assertions even when signed.
28. Remote server receipt/commit/retry/effect cardinality and asynchronous job completion remain unestablished by default.
29. Proposal→Invocation cardinality follows explicit Transform/Derivation rather than an assumed fixed 1:1 mapping.
30. Unknown is required when stronger evidence is not justified.

## 35. Open items handed to Verifier Contract / later profiles

This contract intentionally does not freeze:

- final JSON field names;
- adapter implementation/plugin APIs;
- tool-specific argument/path profiles beyond the existing JSON/json_pointer baseline;
- MCP/provider/tool metadata registries;
- raw remote HTTP/transport evidence profiles;
- remote server attestation profiles;
- transaction-commit proofs;
- effect-causality proofs;
- OutcomeVerification;
- streaming chunk-evidence schema;
- completeness attestations;
- final verifier result enums/output schema.

These remain constrained by this contract.

## 36. Gate decision

Tool Adapter Contract: PASS AFTER ADVERSARIAL REVIEW.

The final pre-Schema specification gate is:

~~~text
Verifier Contract
~~~

JSON Schema and implementation remain BLOCKED until the Verifier Contract passes its specification gate.
