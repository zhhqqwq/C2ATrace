# C2ATrace v0.1 — Phase 1 Part E: Tool Proposal / Invocation / Execution / Result / Effect Semantics

Status: ACCEPTED AFTER ADVERSARIAL REVIEW.

Scope: ToolProposal identity/ownership; effective ToolInvocation semantics; proposal-to-invocation transformation; argument-level provenance; model/application/mixed/unknown argument provenance; validation/normalization/policy rewrite; denied proposal semantics; ToolExecution lifecycle; ToolResult semantics; EffectObservation evidence basis; execution/effect/outcome boundaries; retry, duplicate execution, and idempotency semantics.

JSON Schema: NOT FROZEN.

Implementation: NOT STARTED.

## 1. Design objective

Part E defines how C2ATrace connects an application-visible model tool proposal to the effective invocation selected by the application, the execution attempts of that invocation, returned tool data, and later observations of possible external effects.

The central separations are:

~~~text
ToolProposal
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
proposed arguments
≠
effective arguments

allowed
≠
executed

denied
≠
ToolExecution

execution completed
≠
tool-reported success
≠
external effect true

effect observed
≠
desired outcome verified

same idempotency key
≠
exactly-once effect
~~~

Part E preserves effective argument provenance and execution history without treating tool/runtime reports as objective external truth.

## 2. ToolProposal identity and ownership

### 2.1 ToolProposal role

A ToolProposal is the OutputItem Artifact defined in Part D that represents one application-visible proposal to invoke a tool.

It can contain, as application-visible representation:

- proposed tool identifier or name;
- proposed arguments;
- provider/SDK proposal identifier;
- proposal metadata.

ToolProposal is immutable once identified.

### 2.2 Ownership

Every ToolProposal belongs to exactly one ModelOutput through the OutputItem ownership rules from Part D.

Two identical proposals in one or more outputs remain distinct ToolProposal identities when they are distinct occurrences.

### 2.3 Proposal identifier versus ToolProposal identity

A provider/SDK tool-call identifier is application-visible metadata.

It does not replace the C2ATrace ToolProposal identity and does not create global identity across ModelOutputs, ProviderAttempts, or Receipts.

### 2.4 Proposal is not application authorization

ToolProposal records what was proposed at the model-output boundary.

It does not establish that the application accepted, authorized, prepared, invoked, or executed the proposal.

## 3. ToolInvocation effective semantics

### 3.1 Effective invocation artifact

A ToolInvocation is an immutable Artifact representing the effective application-selected tool call immediately before a ToolExecution attempt can begin.

It contains the execution-relevant representation visible at that boundary, including as applicable:

- effective tool identifier;
- effective arguments;
- execution-relevant options;
- idempotency or request identifiers;
- application/runtime metadata required by the tool runtime.

Secrets can be omitted or privacy-protected under later privacy semantics, but missing secret material does not authorize a verifier to guess it.

### 3.2 ToolInvocation identity

ToolInvocation identity is occurrence/representation-bound, not argument-hash identity.

Distinct application selections remain distinct ToolInvocation identities even when effective tool identifiers and arguments are equal.

The same immutable ToolInvocation can be referenced by multiple ToolExecutions when the application retries the exact same effective invocation without changing execution-relevant representation.

### 3.3 Invocation without proposal

A ToolInvocation can exist without a ToolProposal.

Examples include:

- application-initiated tool calls;
- deterministic workflow steps;
- cleanup operations;
- retry/recovery logic not proposed by the model.

Such an invocation must not be described as model-proposed or model-derived unless positive provenance supports that claim.

## 4. Proposal to invocation transformation

### 4.1 Semantic transition

When a ToolInvocation is prepared from a ToolProposal, Part E reuses the Part B Transform / Derivation model.

Conceptually:

~~~text
ToolProposal
     ↓ use
ToolPreparation Transform
     ↓ generate
ToolInvocation
~~~

Additional application/runtime/policy Artifacts can also be used by the ToolPreparation Transform.

### 4.2 Semantic distinction survives equality

Even when proposed and effective tool name/arguments are byte-for-byte or semantically equal:

~~~text
ToolProposal
≠
ToolInvocation
~~~

because proposal and effective application selection are different protocol roles.

Representation equality can be verified where evidence permits, but identity and role remain separate.

### 4.3 No implicit proposal linkage

A verifier does not infer that a ToolInvocation came from a ToolProposal solely because tool identifiers, arguments, timestamps, or provider call identifiers match.

Positive proposal-to-invocation lineage requires explicit Transform / Derivation provenance.

## 5. Argument-level provenance

### 5.1 Argument scope

For a ToolInvocation whose arguments use the JSON data model, Part E uses json_pointer as the interoperable structured path scheme for argument locations.

A Tool Argument Region is an Artifact Region over the ToolInvocation argument representation.

The same Part B Region discipline applies:

~~~text
Artifact identity
+
representation basis
+
path/selector
+
optional subvalue Region
~~~

### 5.2 Positive argument derivation

Argument-level provenance is represented through qualified Derivation Assertions targeting ToolInvocation argument scopes.

Contributors can include:

- ToolProposal argument scopes;
- application-owned Artifacts;
- runtime/configuration Artifacts;
- policy Artifacts;
- external observations;
- other explicit Artifacts.

A tool argument can therefore be many-to-one derived.

### 5.3 Coarse argument provenance summary

Part E defines four coarse summary classes:

~~~text
model_supplied
application_supplied
mixed
unknown
~~~

These summaries do not replace exact Derivation lineage.

### 5.4 model_supplied

model_supplied means the recorded positive non-transform-generated ancestry for the argument scope comes only from the ToolProposal / model-output side.

It means:

> derived from application-visible ToolProposal provenance.

It does not mean:

> proved to originate from the model's hidden internal reasoning.

Normalization or encoding by the ToolPreparation Transform can preserve model_supplied ancestry when no non-model content contributor is added.

### 5.5 application_supplied

application_supplied means the argument scope has no recorded ToolProposal representation contributor and its positive provenance is from application/runtime/policy Artifacts or explicitly application-generated defaults.

This category can summarize multiple application-side sub-origins, but exact lineage remains authoritative.

### 5.6 mixed

mixed means the argument scope has at least one ToolProposal-derived representation contributor and at least one non-ToolProposal application/runtime/policy representation contributor.

### 5.7 unknown

unknown means the available record does not justify classifying representation contribution as model_supplied, application_supplied, or mixed.

Unknown is not treated as application-supplied merely because the application constructed the ToolInvocation.

### 5.8 Control inputs versus argument contributors

A policy, schema, validator, budget, feature flag, or runtime configuration can affect whether/how an invocation is created without contributing representation content to a particular argument.

Part B control-versus-content semantics continue to apply.

Such control use does not make the control Artifact an argument content ancestor unless a positive Derivation Assertion establishes contribution.

## 6. Validation, normalization, enrichment, and rewrite

### 6.1 Validation

Validation can inspect ToolProposal fields without changing the effective invocation representation.

Validation is use/control provenance unless it creates or rewrites ToolInvocation content.

A validation success assertion does not establish tool safety, semantic correctness, authorization, or future execution.

### 6.2 Normalization

Normalization that changes representation creates ToolInvocation content through the ToolPreparation Transform.

Examples include:

- canonicalizing enum values;
- converting string numbers to numeric values;
- path normalization;
- adding provider/tool-specific wrappers.

Exact or partial Derivation identifies preserved ancestry.

### 6.3 Application enrichment

Application enrichment adds content not present in the ToolProposal.

Examples include:

- repository identifier;
- tenant identifier;
- authenticated user context;
- default arguments;
- runtime-selected environment.

The enriched scopes are not model_supplied unless positive proposal ancestry actually contributes to them.

### 6.4 Policy rewrite

A policy can rewrite proposed values.

The effective ToolInvocation records the rewritten representation.

The policy Artifact can be control-only, a representation contributor, or both depending on what was actually emitted.

A rewritten value does not remain exact representation-equal to the proposal merely because it occupies the same logical argument path.

### 6.5 Dropped proposed arguments

A proposed argument omitted from the ToolInvocation does not become part of effective invocation content.

It can remain in transformation/control provenance without becoming a positive argument Derivation target.

## 7. ToolDecision

### 7.1 Purpose

Part E promotes ToolDecision to a core Assertion because allow/deny provenance cannot be represented correctly as ToolExecution.

A ToolDecision records an application/policy decision about exactly one subject:

~~~text
ToolProposal
or
ToolInvocation
~~~

### 7.2 Decision values

Core Part E conceptual decision values are:

~~~text
allow
deny
unknown
~~~

The exact wire vocabulary remains unfrozen.

### 7.3 Decision basis

A ToolDecision can reference policy/configuration/evidence Artifacts or leave its basis unknown.

A decision is a Producer/policy assertion and does not establish objective safety or authorization correctness.

### 7.4 Denied proposal before invocation

If a ToolProposal is denied before an effective ToolInvocation is prepared, the denial can be recorded directly against the ToolProposal.

No ToolInvocation is required solely to represent the denial.

No ToolExecution is created solely because the denial occurred.

### 7.5 Denied invocation before execution

If a ToolInvocation is prepared and then denied before execution begins, the ToolDecision can target the ToolInvocation.

The ToolInvocation remains in provenance.

No ToolExecution is created solely to represent denial.

### 7.6 Allow does not imply execution

An allow decision records permission/selection state only.

Execution can still fail to start, be abandoned, be superseded, or remain unknown.

### 7.7 Deny does not rewrite later history

A deny decision does not make later execution structurally impossible.

A later override, bug, different decision, or unrelated application path can still lead to a ToolExecution.

If both denial and execution are recorded, the provenance preserves both facts rather than deleting or rewriting the denial.

C2ATrace is policy-neutral and does not automatically judge whether that execution was authorized.

## 8. ToolExecution lifecycle

### 8.1 Execution occurrence

A ToolExecution is an Activity representing one actual attempt to execute exactly one ToolInvocation.

ToolExecution exists only once execution has actually begun at the instrumented tool-runtime boundary.

### 8.2 Multiple executions of one invocation

One ToolInvocation can have zero or more ToolExecutions.

This supports:

- retries;
- replay;
- duplicate execution;
- uncertain prior completion;
- application-level recovery.

Every ToolExecution has its own occurrence identity.

### 8.3 Execution lifecycle

Part E conceptually distinguishes:

~~~text
in_progress
terminal
unknown
~~~

A terminal ToolExecution can have one disposition:

~~~text
completed
failed
timeout
cancelled
interrupted
unknown
~~~

This is application/runtime-observed execution lifecycle state.

### 8.4 completed

completed means the instrumented tool runtime observed the execution return through its normal completion boundary.

It does not establish:

- tool semantic success;
- external effect truth;
- outcome success;
- exactly-once behavior.

### 8.5 failed

failed means the tool runtime observed an error termination other than the separately recorded timeout, cancellation, or interruption categories.

### 8.6 timeout

timeout means the application/runtime classified the execution as reaching its timeout condition.

The external operation may have partially or fully occurred before the timeout.

### 8.7 cancelled

cancelled means the application/runtime records an intentional cancellation of an in-progress execution.

Cancellation does not prove that a remote system stopped processing.

### 8.8 interrupted

interrupted means execution/result delivery began but the application/runtime observed abnormal termination before normal completion.

## 9. ToolResult semantics

### 9.1 ToolResult role

A ToolResult is an immutable Artifact representing the terminal assembled application-visible result representation returned or exposed by one ToolExecution.

It can contain:

- normal return values;
- structured response data;
- error representations;
- remote identifiers;
- status fields;
- tool/runtime metadata.

### 9.2 Result ownership

Every ToolResult belongs to exactly one ToolExecution.

Core v0.1 records zero or one terminal ToolResult for one ToolExecution.

A ToolExecution can therefore complete, fail, timeout, cancel, or interrupt with or without a ToolResult.

### 9.3 ToolResult occurrence identity

ToolResult identity is occurrence-based.

Equal result representations or commitments do not merge ToolResults from distinct ToolExecutions.

### 9.4 Result capture extent

Part E conceptually permits ToolResult capture extent:

~~~text
complete
partial
unknown
~~~

Complete means complete relative to the declared application-visible tool-result capture scope.

It does not establish remote-system completeness or external truth.

### 9.5 Tool-reported status

A ToolResult can contain or carry tool-reported status such as success/error codes.

Such status is result metadata.

It does not independently establish external effect truth or desired outcome success.

## 10. EffectObservation semantics

### 10.1 EffectObservation role

An EffectObservation is an immutable Artifact recording a bounded observation/evidence claim about possible external state associated with tool activity.

It is not the external Effect itself.

It is not OutcomeVerification.

### 10.2 Effect observation claim

An EffectObservation records what external-state proposition was observed or reported, at a scope the Producer can actually support.

Examples:

- a follow-up API read reports issue 123 exists;
- a filesystem observation reports path X exists;
- a database read reports row R is present;
- a tool result reports object ID 123 was created.

The exact general-purpose effect-claim vocabulary remains unfrozen.

### 10.3 Evidence basis

Every EffectObservation carries one evidence basis or explicitly records the basis as unknown.

Part E defines the conceptual basis kinds:

~~~text
execution_result
separate_observation
external_attestation
unknown
~~~

### 10.4 execution_result basis

execution_result means the observation is supported by the ToolResult of the execution whose effect is being discussed.

This is often only the tool/runtime reporting its own claimed effect.

It is not independent verification.

### 10.5 separate_observation basis

separate_observation means the effect claim is supported by a distinct later observation Artifact, such as a follow-up read/query.

It is stronger provenance separation than merely repeating the execution result, but it still remains bounded by the truth/evidence properties of the observing source.

### 10.6 external_attestation basis

external_attestation means the observation is supported by a separately identified attestation/evidence Artifact under a future or applicable evidence profile.

The presence of the label alone does not create cryptographic or factual validity.

### 10.7 unknown basis

unknown preserves inability to establish how the effect claim was observed.

### 10.8 Multiple evidence Artifacts

An EffectObservation can reference one or more evidence Artifacts supporting the same bounded effect claim.

The number of supporting artifacts does not by itself upgrade the claim to objective truth.

## 11. Execution, result, effect, and outcome boundaries

The following implications are invalid in core v0.1:

~~~text
ToolExecution completed
⇒ ToolResult says success

ToolResult says success
⇒ external Effect occurred

EffectObservation exists
⇒ Effect is objectively true

Effect observed
⇒ desired Outcome achieved

same external identifier
⇒ same execution

same idempotency key
⇒ exactly-once Effect
~~~

A verifier preserves each claim at its own evidence level.

## 12. Retry, duplicate execution, and idempotency

### 12.1 Execution relationships

When known, ToolExecutions can carry Producer-recorded orchestration relationships such as:

~~~text
retry_of
replay_of
duplicate_of
unknown
~~~

These relationships describe execution history, not effect cardinality.

### 12.2 Same invocation, multiple executions

If execution-relevant ToolInvocation representation is unchanged, multiple execution attempts can reference the same ToolInvocation.

If execution-relevant representation changes, including argument or idempotency metadata changes, a new ToolInvocation identity is required.

### 12.3 Retry relation

retry_of means the later ToolExecution was initiated as an attempt to repeat/recover the same effective ToolInvocation after an earlier attempt.

It does not establish that the earlier execution had no effect.

### 12.4 duplicate_of relation

duplicate_of is a Producer assertion that one execution is considered a duplicate/replay of another for orchestration purposes.

It does not prove duplicate external effect.

### 12.5 Idempotency key

An idempotency key or equivalent token is execution-relevant ToolInvocation metadata.

Its presence, reuse, or equality does not establish:

- remote support for idempotency;
- correct remote enforcement;
- no duplicate execution;
- no duplicate effect;
- exactly-once semantics.

### 12.6 Unknown prior completion

If an execution times out and the application cannot determine whether the external operation completed, later retries preserve that uncertainty.

The retry is not evidence that the prior execution had no effect.

## 13. Argument provenance claim matrix

| Claim | Evidence basis | Core v0.1 interpretation |
|---|---|---|
| ToolProposal P belongs to ModelOutput O | STRUCTURAL + Part D occurrence premise | Recorded model-output proposal occurrence |
| ToolInvocation I exists | STRUCTURAL + PRODUCER_ASSERTED occurrence premise | Effective application-side invocation Artifact |
| I derives from P through preparation Transform | STRUCTURAL + PRODUCER_ASSERTED Derivation; optionally REPRESENTATION-verifiable | Positive proposal ancestry |
| Argument /title is model_supplied | Derived from explicit argument lineage | Proposal-side representation ancestry only |
| Argument /repo is application_supplied | Derived from explicit argument lineage | Non-proposal application-side ancestry |
| Argument /labels is mixed | Derived from explicit argument lineage | Proposal + non-proposal contributors |
| Argument provenance is unknown | Knowledge state | No stronger contributor classification justified |
| ToolDecision says allow | PRODUCER_ASSERTED/policy assertion | Does not imply execution |
| ToolDecision says deny | PRODUCER_ASSERTED/policy assertion | Denial record; not an execution |
| ToolExecution E uses I | STRUCTURAL + PRODUCER_ASSERTED occurrence premise | Recorded execution attempt |
| ToolResult R belongs to E | STRUCTURAL + PRODUCER_ASSERTED occurrence premise | Returned/captured result representation |
| ToolResult reports success | PRODUCER_ASSERTED/tool-reported | Does not establish external effect |
| EffectObservation basis=execution_result | STRUCTURAL + PRODUCER_ASSERTED | Effect claim supported by execution result only |
| EffectObservation basis=separate_observation | STRUCTURAL + PRODUCER_ASSERTED | Distinct observation supports bounded effect claim |
| External Effect objectively occurred | unsupported by core in general | Requires stronger evidence profile |
| Desired Outcome achieved | unsupported by core | Outcome verification outside core v0.1 |

## 14. Normative requirements

### TOOL-001 — Proposal ownership

Every ToolProposal MUST reference exactly one ModelOutput.

Planned test: tool-proposal-owner-001.

### TOOL-002 — Proposal identity is occurrence-based

A verifier MUST NOT merge distinct ToolProposal identities solely because provider call IDs, tool names, arguments, representations, or commitments match.

Planned test: tool-proposal-no-content-merge-001.

### TOOL-003 — Proposal is not invocation

A verifier MUST NOT infer ToolInvocation existence solely from ToolProposal presence.

Planned test: tool-proposal-no-invocation-001.

### TOOL-004 — Proposal is not authorization

A verifier MUST NOT report a ToolProposal as application authorization, approval, or execution permission solely because the proposal exists.

Planned test: tool-proposal-no-authorization-001.

### TOOL-005 — Invocation identity is occurrence-bound

A verifier MUST NOT merge distinct ToolInvocation identities solely because effective tool identifiers, arguments, idempotency keys, or commitments match.

Planned test: tool-invocation-no-content-merge-001.

### TOOL-006 — Invocation without proposal is valid

A conforming representation MUST permit a ToolInvocation with no ToolProposal ancestry.

Planned test: tool-invocation-without-proposal-001.

### TOOL-007 — No implicit proposal linkage

A verifier MUST NOT infer proposal-to-invocation lineage solely from matching tool identifiers, arguments, timestamps, provider proposal IDs, or content similarity.

Planned test: tool-proposal-invocation-no-inference-001.

### TOOL-008 — Proposal-derived invocation uses explicit lineage

When a ToolInvocation is claimed to derive from a ToolProposal, the record MUST identify explicit Transform / Derivation provenance connecting the proposal and invocation scopes.

Planned test: tool-proposal-invocation-lineage-001.

### TOOL-009 — Proposal and invocation identities remain distinct

A ToolProposal and ToolInvocation MUST retain distinct Artifact identities even when their tool identifier and argument representations are equal.

Planned test: tool-proposal-invocation-identity-separation-001.

### TOOL-010 — Effective invocation mutation creates new identity

If execution-relevant ToolInvocation representation changes, the changed representation MUST NOT reuse the prior ToolInvocation identity.

Planned test: tool-invocation-mutation-new-identity-001.

### TOOL-011 — Argument path scheme

For ToolInvocation arguments declared to use the JSON data model, a core interoperable argument path MUST use json_pointer semantics.

Planned test: tool-argument-json-pointer-001.

### TOOL-012 — Argument provenance requires positive derivation

A verifier MUST NOT classify an argument scope as model_supplied, application_supplied, or mixed solely from transform use/control relations without positive representation Derivation evidence or explicit transform-generated application content.

Planned test: tool-argument-provenance-positive-001.

### TOOL-013 — model_supplied is proposal-boundary provenance

A verifier MUST NOT interpret model_supplied as proof of hidden model-internal origin or causal responsibility; it only summarizes recorded ToolProposal-side representation ancestry.

Planned test: tool-argument-model-supplied-bounded-001.

### TOOL-014 — application_supplied excludes proposal contributors

A verifier MUST NOT classify an argument scope as application_supplied when positive ToolProposal representation ancestry contributes to that scope.

Planned test: tool-argument-application-supplied-001.

### TOOL-015 — mixed requires both contributor domains

A verifier MUST NOT classify an argument scope as mixed unless positive provenance identifies both ToolProposal-side and non-ToolProposal application/runtime/policy representation contributors.

Planned test: tool-argument-mixed-001.

### TOOL-016 — Unknown provenance remains unknown

When contributor provenance for an argument scope cannot be established, a conforming record MUST preserve unknown rather than defaulting to model_supplied or application_supplied.

Planned test: tool-argument-unknown-001.

### TOOL-017 — Control input is not argument content ancestry

A verifier MUST NOT treat a validator, policy, schema, feature flag, budget, or other control-only input as an argument representation contributor without a positive Derivation Assertion.

Planned test: tool-argument-control-no-content-001.

### TOOL-018 — Dropped proposal argument is not effective argument

A verifier MUST NOT report a proposed argument scope as present in the ToolInvocation when the preparation lineage shows that scope was omitted and no effective argument occurrence exists.

Planned test: tool-argument-dropped-001.

### TOOL-019 — Rewrite preserves effective value

When policy/application preparation rewrites an argument, the ToolInvocation MUST preserve the rewritten effective representation rather than the superseded proposed value as its effective argument.

Planned test: tool-argument-rewrite-effective-001.

### TOOL-020 — Validation success is bounded

A verifier MUST NOT report validation success as proof of semantic correctness, safety, authorization, external effect success, or future execution.

Planned test: tool-validation-bounded-001.

### TOOL-021 — ToolDecision subject cardinality

Every ToolDecision MUST identify exactly one subject: either one ToolProposal or one ToolInvocation.

Planned test: tool-decision-subject-001.

### TOOL-022 — ToolDecision value

A core Part E ToolDecision MUST identify exactly one conceptual decision value from allow, deny, or unknown.

Planned test: tool-decision-value-001.

### TOOL-023 — Denial before invocation needs no invocation

A conforming representation MUST permit a deny ToolDecision on a ToolProposal without creating a ToolInvocation.

Planned test: tool-deny-proposal-no-invocation-001.

### TOOL-024 — Denial is not execution

A Producer MUST NOT create a ToolExecution solely to represent a deny ToolDecision.

Planned test: tool-deny-no-execution-001.

### TOOL-025 — Allow is not execution

A verifier MUST NOT infer ToolExecution existence solely from an allow ToolDecision.

Planned test: tool-allow-no-execution-001.

### TOOL-026 — Decision does not erase contradictory later history

A verifier MUST NOT treat a deny ToolDecision as proof that no later ToolExecution occurred when an execution is separately recorded.

Planned test: tool-deny-later-execution-001.

### TOOL-027 — Decision basis unknown is valid

A conforming ToolDecision MUST permit its evidence/policy basis to be unknown.

Planned test: tool-decision-basis-unknown-001.

### TOOL-028 — Execution ownership

Every ToolExecution MUST reference exactly one ToolInvocation.

Planned test: tool-execution-owner-001.

### TOOL-029 — Execution starts before it exists

A Producer MUST NOT create a ToolExecution for an invocation that never began execution at the instrumented tool-runtime boundary.

Planned test: tool-no-phantom-execution-001.

### TOOL-030 — Multiple executions per invocation

A conforming representation MUST permit one ToolInvocation to have multiple ToolExecutions.

Planned test: tool-multiple-executions-001.

### TOOL-031 — Execution identity is occurrence-based

A verifier MUST NOT merge distinct ToolExecution identities solely because they reference the same ToolInvocation or have equal result representations, timestamps, or idempotency metadata.

Planned test: tool-execution-no-merge-001.

### TOOL-032 — Execution terminal disposition is single-valued

A terminal ToolExecution MUST have at most one terminal disposition in the core Part E vocabulary.

Planned test: tool-execution-disposition-001.

### TOOL-033 — Completed execution is not effect proof

A verifier MUST NOT infer tool semantic success, external Effect truth, or Outcome success solely from ToolExecution disposition=completed.

Planned test: tool-execution-completed-no-effect-001.

### TOOL-034 — Timeout preserves uncertain effect

A verifier MUST NOT report ToolExecution disposition=timeout as proof that no external Effect occurred.

Planned test: tool-timeout-effect-unknown-001.

### TOOL-035 — Cancellation is not remote-stop proof

A verifier MUST NOT report ToolExecution cancellation as proof that a remote tool/service stopped processing.

Planned test: tool-cancel-no-remote-stop-001.

### TOOL-036 — ToolResult ownership

Every ToolResult MUST reference exactly one ToolExecution.

Planned test: tool-result-owner-001.

### TOOL-037 — ToolResult cardinality

A ToolExecution MUST NOT own more than one core terminal ToolResult.

Planned test: tool-result-cardinality-001.

### TOOL-038 — Result absence is not no-result proof

Absence of ToolResult for a ToolExecution in the supplied Receipt MUST NOT be reported as proof that no application-visible tool result existed.

Planned test: tool-result-absence-not-negation-001.

### TOOL-039 — ToolResult identity is occurrence-based

A verifier MUST NOT merge distinct ToolResult identities solely because their representations, remote identifiers, status values, or commitments match.

Planned test: tool-result-no-content-merge-001.

### TOOL-040 — Result capture extent is bounded

A verifier MUST NOT report ToolResult capture_extent=complete as proof of complete remote-system state or objective external truth.

Planned test: tool-result-capture-bounded-001.

### TOOL-041 — Tool-reported success is not effect truth

A verifier MUST NOT report a ToolResult success/status field as independent proof that the claimed external Effect occurred.

Planned test: tool-result-success-no-effect-001.

### TOOL-042 — EffectObservation basis required

Every EffectObservation MUST identify one conceptual evidence basis or explicitly record basis=unknown.

Planned test: tool-effect-basis-001.

### TOOL-043 — execution_result basis is not independent verification

A verifier MUST NOT report an EffectObservation with basis=execution_result as independently verified external state solely because the ToolResult supports it.

Planned test: tool-effect-result-basis-bounded-001.

### TOOL-044 — Separate observation remains evidence-bounded

A verifier MUST NOT upgrade basis=separate_observation to objective external truth solely because the observation was made in a distinct later operation.

Planned test: tool-effect-separate-observation-bounded-001.

### TOOL-045 — External attestation label is not self-validating

A verifier MUST NOT treat basis=external_attestation as cryptographically or factually valid unless the applicable attestation/evidence profile is independently satisfied.

Planned test: tool-effect-attestation-profile-001.

### TOOL-046 — Unknown effect basis remains unknown

A verifier MUST NOT replace EffectObservation basis=unknown with execution_result, separate_observation, or external_attestation based solely on timing or graph proximity.

Planned test: tool-effect-basis-unknown-001.

### TOOL-047 — Evidence multiplicity is not truth

A verifier MUST NOT infer objective Effect truth solely from the number of evidence Artifacts supporting an EffectObservation.

Planned test: tool-effect-multiple-evidence-no-truth-001.

### TOOL-048 — EffectObservation is not OutcomeVerification

A verifier MUST NOT report EffectObservation existence as proof that the application's desired Outcome was achieved.

Planned test: tool-effect-not-outcome-001.

### TOOL-049 — Execution relationship is explicit

A verifier MUST NOT infer retry_of, replay_of, duplicate_of, or equivalent ToolExecution relationships solely from timestamps, identical invocations, equal results, or idempotency keys.

Planned test: tool-execution-relation-no-inference-001.

### TOOL-050 — Execution relationship does not imply invocation equality

A verifier MUST NOT infer that ToolExecutions related by retry_of, replay_of, or duplicate_of reference the same or representation-equal ToolInvocation.

Planned test: tool-execution-relation-no-invocation-equality-001.

### TOOL-051 — Execution predecessor is not self-referential

A ToolExecution MUST NOT identify itself as its own retry_of or replay_of predecessor.

Planned test: tool-execution-relation-no-self-loop-001.

### TOOL-052 — Retry/replay predecessor graph is acyclic

Within one C2ATrace resolution scope, the directed predecessor graph formed by retry_of and replay_of ToolExecution relationships MUST be acyclic, including when related executions reference different ToolInvocations.

Planned test: tool-execution-predecessor-cycle-001.

### TOOL-053 — Retry does not negate prior effect

A verifier MUST NOT treat retry_of as evidence that the prior ToolExecution produced no external Effect.

Planned test: tool-retry-prior-effect-unknown-001.

### TOOL-054 — Idempotency key is not exactly-once proof

A verifier MUST NOT infer remote idempotency support, duplicate suppression, exactly-once execution, or exactly-once Effect solely from the presence or equality of an idempotency key.

Planned test: tool-idempotency-no-exactly-once-001.

### TOOL-055 — Idempotency equality does not merge identity

A verifier MUST NOT merge ToolInvocation or ToolExecution identities solely because idempotency keys are equal.

Planned test: tool-idempotency-no-merge-001.

### TOOL-056 — Invocation change across retry requires new invocation identity

If execution-relevant ToolInvocation representation changes between execution attempts, the changed invocation MUST have a new ToolInvocation identity rather than being represented as another execution of the old invocation.

Planned test: tool-retry-invocation-mutation-001.

### TOOL-057 — ToolResult is not future context automatically

A verifier MUST NOT infer that a ToolResult became model context solely because the ToolResult exists; later context use requires explicit Transform / Derivation / RequestBinding provenance.

Planned test: tool-result-no-context-inference-001.

### TOOL-058 — Effect timing is not causality

A verifier MUST NOT infer that a ToolExecution caused an EffectObservation solely because the observation timestamp follows the execution.

Planned test: tool-effect-time-no-causality-001.

### TOOL-059 — Missing EffectObservation is not no-effect proof

Absence of EffectObservation in the supplied Receipt MUST NOT be reported as proof that no external Effect occurred.

Planned test: tool-effect-absence-not-negation-001.

### TOOL-060 — Missing execution is not no-execution proof

Absence of ToolExecution in the supplied Receipt MUST NOT be reported as proof that no execution occurred, except for the narrower statement that no ToolExecution is present in the supplied Receipt.

Planned test: tool-execution-absence-scope-001.

### TOOL-061 — ToolDecision identity is occurrence-based

A verifier MUST NOT merge distinct ToolDecision identities solely because their subjects, decision values, policy labels, or evidence bases match.

Planned test: tool-decision-no-content-merge-001.

### TOOL-062 — Missing ToolDecision is not no-decision proof

Absence of ToolDecision in the supplied Receipt MUST NOT be reported as proof that no application/policy decision occurred.

Planned test: tool-decision-absence-not-negation-001.

## 15. Adversarial architecture review

### Review A — Proposal arguments copied unchanged

~~~text
ToolProposal:
  title = "Bug"

ToolInvocation:
  title = "Bug"
~~~

The proposal and invocation remain distinct Artifacts. Exact argument lineage can classify /title as model_supplied.

Result: RESOLVED by TOOL-008, TOOL-009, and TOOL-013.

### Review B — Application adds repository

~~~text
ToolProposal:
  title = "Bug"

Application Artifact:
  repo = "org/repo"

ToolInvocation:
  title = "Bug"
  repo = "org/repo"
~~~

/title can be model_supplied while /repo is application_supplied.

Result: RESOLVED by TOOL-012 through TOOL-016.

### Review C — Mixed argument

~~~text
proposal:
  path = "src/"

application:
  filename = "a.py"

effective:
  path = "src/a.py"
~~~

The effective /path can be mixed when both representations contribute.

Result: RESOLVED by TOOL-015 and Part B many-to-one Derivation.

### Review D — Runtime supplies auth secret

The secret can be application/runtime provenance, privacy-protected, or unknown.

It is not model_supplied merely because the model selected the tool.

Result: RESOLVED by TOOL-012 through TOOL-016.

### Review E — Policy rewrites labels

~~~text
proposal labels = ["urgent"]
policy rewrite
effective labels = ["review-required"]
~~~

The effective value is preserved in ToolInvocation. The proposed value is not treated as the effective value.

Result: RESOLVED by TOOL-019.

### Review F — Validator rejects proposal before invocation

~~~text
ToolProposal P
ToolDecision(P) = deny
~~~

No fake ToolInvocation or ToolExecution is required.

Result: RESOLVED by TOOL-023 and TOOL-024.

### Review G — Invocation prepared, then denied

~~~text
ToolProposal P
  ↓
ToolInvocation I
ToolDecision(I) = deny
~~~

I remains provenance evidence. No ToolExecution is created solely for denial.

Result: RESOLVED by TOOL-024.

### Review H — Deny recorded, execution later occurs

A bug, override, or later decision can still produce ToolExecution E.

C2ATrace preserves both the deny decision and E. It does not rewrite history or automatically judge authorization correctness.

Result: RESOLVED by TOOL-026.

### Review I — Allow but application crashes before execution

allow does not create ToolExecution.

Result: RESOLVED by TOOL-025.

### Review J — Execution completes and result says success, but remote write never happened

~~~text
ToolExecution disposition = completed
ToolResult status = success
EffectObservation basis = execution_result
~~~

The receipt can report all three without claiming objective external effect truth.

Result: RESOLVED by TOOL-033, TOOL-041, and TOOL-043.

### Review K — Timeout after remote write succeeds

The application times out before seeing success.

A later retry does not prove the first attempt had no effect and can risk duplicate effects.

Result: RESOLVED by TOOL-034 and TOOL-053.

### Review L — Follow-up read confirms object

A distinct later observation reports the object exists.

EffectObservation can use basis=separate_observation.

This is stronger provenance separation than execution_result but remains evidence-bounded.

Result: RESOLVED by TOOL-044.

### Review M — Tool lies about object ID

A ToolResult can report object_id=123 even when no such object exists.

C2ATrace preserves the returned representation and does not upgrade it into objective Effect truth.

Result: RESOLVED by TOOL-041.

### Review N — Same invocation retried twice

~~~text
ToolInvocation I
  ├→ Execution E1 timeout
  └→ Execution E2 completed
~~~

Both executions remain distinct. E2 retry_of E1 is optional explicit orchestration provenance.

Result: RESOLVED by TOOL-030, TOOL-031, and TOOL-049.

### Review O — Retry changes idempotency key

The execution-relevant invocation representation changed, so a new ToolInvocation identity is required.

The later execution can still be explicitly recorded as retry_of the earlier execution. That orchestration relation does not claim ToolInvocation equality.

Result: RESOLVED by TOOL-010, TOOL-050, and TOOL-056.

### Review P — Same idempotency key used twice

The key does not merge execution identities and does not establish exactly-once external effects.

Result: RESOLVED by TOOL-054 and TOOL-055.

### Review Q — Same result returned from duplicate executions

Equal ToolResult representations do not merge ToolExecutions or ToolResults.

Result: RESOLVED by TOOL-031 and TOOL-039.

### Review R — ToolResult becomes next-turn model context

The ToolResult alone does not prove it entered the next model request.

The later chain remains:

~~~text
ToolResult
→ Transform / Derivation
→ ContextFragment / ModelInputComponent
→ RequestBinding
→ RequestSnapshot
~~~

Result: RESOLVED by TOOL-057 and Parts B/C.

### Review S — EffectObservation appears after unrelated execution

Timestamp order alone does not bind the observation causally to that execution.

Result: RESOLVED by TOOL-058.

### Review T — Receipt contains no EffectObservation

No observation in the supplied receipt does not prove no side effect occurred.

Result: RESOLVED by TOOL-059.

### Review U — Receipt contains proposal but later receipt has execution

A partial receipt can omit ToolInvocation/ToolExecution that exists elsewhere.

Absence is scoped to supplied provenance.

Result: RESOLVED by TOOL-060 and Phase 0 completeness rules.

### Review V — Proposed tool alias resolves to different effective tool

~~~text
proposal tool = "search"
application routing
effective tool = "internal_search_v2"
~~~

The effective ToolInvocation stores the selected executable-facing identifier. Positive lineage can preserve the proposal identifier as control/content ancestry without pretending the identifiers are equal.

Result: RESOLVED by proposal-to-invocation transformation semantics.

### Review W — Policy text influences decision but is not emitted into arguments

The policy is control provenance for ToolPreparation/ToolDecision, not automatically argument representation ancestry.

Result: RESOLVED by TOOL-017.

### Review X — Tool returns an error object after completed runtime call

ToolExecution can be completed at the runtime-call level while ToolResult contains a semantic/tool-level error status.

This does not contradict the lifecycle model because completed does not mean semantic success.

Result: RESOLVED by TOOL-033 and TOOL-041.

## 16. Architecture revisions caused by Part E

### 16.1 ToolDecision becomes a core Assertion

Part E promotes ToolDecision into the normative core object model:

~~~text
ToolDecision = Assertion
~~~

Its subject is one ToolProposal or ToolInvocation.

This preserves allow/deny provenance without inventing ToolExecution.

### 16.2 ToolInvocation argument provenance reuses Derivation

Part E does not create a second argument-provenance graph.

Argument-level provenance uses Part B qualified Derivation over ToolInvocation argument Regions.

The model_supplied / application_supplied / mixed / unknown vocabulary is a coarse summary over that lineage, not a replacement for it.

### 16.3 One ToolInvocation can have many ToolExecutions

ToolInvocation is the immutable effective call representation.

ToolExecution is an attempt occurrence.

This distinction supports retry/replay without duplicating unchanged invocation representations.

### 16.4 One ToolExecution has zero or one core ToolResult

ToolResult is the terminal assembled application-visible result Artifact for one execution attempt.

Streaming/chunk-level tool result evidence remains future profile work.

### 16.5 EffectObservation remains evidence, not Effect truth

Part E formalizes evidence basis while keeping objective Effect and Outcome outside the automatically established core claim set.

## 17. Part E resolved decisions

Part E locks the following decisions:

1. ToolProposal is an occurrence-identified ModelOutput item and does not imply authorization or execution.
2. ToolInvocation is the immutable effective application-selected call representation immediately before execution.
3. ToolProposal and ToolInvocation remain distinct identities even when their representations are equal.
4. Proposal-to-invocation linkage uses explicit Transform / Derivation provenance.
5. ToolInvocation can exist without ToolProposal ancestry.
6. Argument-level provenance uses ToolInvocation argument Regions and qualified Derivation.
7. model_supplied / application_supplied / mixed / unknown are bounded coarse summaries over recorded representation ancestry.
8. Control-only policy/validation inputs are not argument content contributors.
9. Effective rewrites/enrichment are preserved in ToolInvocation rather than overwritten by proposal values.
10. ToolDecision is a core Assertion with allow / deny / unknown semantics.
11. Denial does not create ToolExecution; allow does not prove ToolExecution.
12. ToolExecution represents an actual execution attempt and one ToolInvocation can have multiple executions.
13. Execution completed does not imply semantic success, external Effect, or Outcome success.
14. Core ToolExecution has zero or one terminal ToolResult.
15. ToolResult success/status remains tool-reported evidence and not Effect truth.
16. EffectObservation records a bounded effect claim plus execution_result / separate_observation / external_attestation / unknown evidence basis.
17. EffectObservation is not objective Effect truth or OutcomeVerification.
18. Retry/replay/duplicate execution relationships are explicit, can span changed ToolInvocations, and do not establish invocation equality or effect cardinality.
19. Idempotency metadata does not prove exactly-once semantics.
20. ToolResult does not become future model context without explicit later provenance.
21. ToolDecision identities are occurrence-based, and missing decisions do not prove no decision occurred.

## 18. Open items handed to later phases

Part E intentionally does not freeze:

- JSON field names or enum serialization;
- exact executable/tool registry identity model;
- secret representation and privacy handling;
- final ToolDecision policy vocabulary beyond allow/deny/unknown;
- structured tool-argument canonicalization profile;
- rich non-JSON argument path schemes;
- detailed tool-runtime error taxonomy;
- streaming/chunk-level ToolResult profile;
- general Effect claim schema;
- external attestation/evidence profiles;
- OutcomeVerification;
- distributed exactly-once proofs;
- remote transaction semantics;
- authorization-policy correctness.

These remain constrained by Part E semantics.

## 19. Gate decision

Phase 1 Part E: PASS AFTER ADVERSARIAL REVIEW.

The next semantic work remains pre-Schema and should cover:

~~~text
Trust / Taint semantics
Privacy semantics
Integrity / Receipt semantics
Provider adapter contract
Tool adapter contract
Verifier contract
~~~

JSON Schema and implementation remain BLOCKED.
