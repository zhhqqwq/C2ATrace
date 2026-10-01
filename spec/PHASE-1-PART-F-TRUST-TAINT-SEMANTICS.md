# C2ATrace v0.1 — Phase 1 Part F: Trust / Taint Semantics

Status: DRAFT FOR ADVERSARIAL REVIEW.

Scope: TrustAssertion subjects, trust dimensions and labels, issuer/policy identity, unknown/conflict semantics, inheritance prohibitions; TaintAssertion subjects, taint kind/state/channel/precision, conservative lattice, content/control propagation, mixed ancestry, sanitization, anti-laundering, and model/tool/effect boundary rules.

JSON Schema: NOT FROZEN.

Implementation: NOT STARTED.

## 1. Design objective

Part F defines policy-scoped trust and taint metadata without turning C2ATrace into a policy engine, causal-attribution system, or truth oracle.

The central separations are:

~~~text
trusted
≠
true

untrusted
≠
false

taint present
≠
malicious

taint absent
≠
objectively clean

sanitized
≠
trusted

TrustAssertion
≠
authorization

TaintAssertion
≠
causal attribution
~~~

Trust and Taint are Assertions layered on the provenance graph. They do not replace SourceRef, Derivation, RequestBinding, ToolDecision, or other provenance relations.

## 2. Common assertion scope

### 2.1 Subject

A TrustAssertion or TaintAssertion targets exactly one identified C2ATrace subject.

The conceptual subject can be:

- a Reference such as SourceRef;
- an Artifact;
- an Artifact Region;
- an Activity;
- another Assertion;
- a Package or other identified protocol object when a later profile makes that use meaningful.

A TrustAssertion or TaintAssertion does not use its own identity as its subject.

### 2.2 Assertion occurrence identity

TrustAssertion and TaintAssertion identities are occurrence-based.

Two assertions with the same subject, state, issuer, and policy can still remain separate assertion occurrences.

### 2.3 Issuer

Every trust/taint assertion records one asserted_by identity reference or explicitly records the issuer as unknown.

The issuer can represent, for example:

- the Producer;
- an application subsystem;
- a policy engine;
- a user/administrator identity;
- an external evaluator.

The exact principal-identity wire model remains unfrozen.

### 2.4 Policy context

Every trust/taint assertion records one policy/context identifier or explicitly records the policy context as unknown.

Policy identity scopes the meaning of labels, dimensions, propagation rules, sanitizer rules, and precedence.

Equal labels under different policy identities are not automatically semantically equivalent.

### 2.5 Basis

An assertion can reference zero or more evidence/policy Artifacts and can explicitly record basis unknown.

Basis references are evidence lineage. They do not independently establish the truth of the assertion.

## 3. TrustAssertion semantics

### 3.1 Trust dimension

A TrustAssertion identifies one trust dimension.

Core v0.1 does not define one universal concept of "trusted."

Illustrative dimensions can include:

~~~text
source_authority
content_reliability
runtime_integrity
policy_approval
identity_confidence
application_defined
~~~

The interoperable vocabulary for trust dimensions remains profile-defined.

### 3.2 Trust state

Core Part F trust states are:

~~~text
trusted
untrusted
unknown
~~~

These are issuer/policy assessments.

They are not objective properties of the subject.

### 3.3 Local assertion semantics

TrustAssertion applies only to its explicit subject and trust dimension under its explicit issuer/policy context.

It is not an inheritable property of provenance descendants, ancestors, containers, members, or related activities.

### 3.4 Explicit unknown

unknown means the issuer/policy cannot justify trusted or untrusted for the subject/dimension.

No TrustAssertion being present is different from an explicit TrustAssertion(state=unknown).

### 3.5 Conflicting assertions

Multiple TrustAssertions can disagree.

For example:

~~~text
Policy A: source_authority = trusted
Policy B: source_authority = untrusted
~~~

or even:

~~~text
same policy identity:
  assertion 1 = trusted
  assertion 2 = untrusted
~~~

Core v0.1 preserves the assertions and does not choose a winner from timestamps or insertion order.

A future policy profile can define precedence or supersession semantics.

## 4. Trust does not inherit

Core v0.1 does not automatically propagate trust across:

- SourceRef → SourceObservation;
- Artifact → derived Artifact;
- ModelInputComponent → RequestSnapshot;
- RequestSnapshot → ProviderAttempt;
- ProviderAttempt → ModelOutput;
- ModelOutput → ToolProposal;
- ToolProposal → ToolInvocation;
- ToolInvocation → ToolExecution;
- ToolExecution → ToolResult;
- ToolResult → EffectObservation;
- containment or selection relations.

A policy engine can issue additional TrustAssertions on related subjects when justified.

Those remain separate assertion occurrences.

## 5. Trust, integrity, taint, and decision boundaries

### 5.1 Trust versus integrity

A signed or digest-valid TrustAssertion can have verified representation integrity while the trust judgement itself remains Producer/policy asserted.

Signature validity does not make the trust label objectively correct.

### 5.2 Trust versus taint

Trust state and taint state are independent dimensions.

Examples:

- a trusted source can contain sensitive content;
- an untrusted source can contain non-sensitive content;
- a sanitized output can still have an untrusted-source ancestry;
- a tainted Artifact can still carry a TrustAssertion under another dimension.

Core v0.1 does not automatically convert TrustAssertion into TaintAssertion or vice versa.

### 5.3 Trust versus ToolDecision

TrustAssertion does not directly authorize or deny tool execution.

A policy can use trust evidence when issuing ToolDecision, but the decision remains a distinct Assertion.

## 6. TaintAssertion semantic dimensions

### 6.1 Taint kind

A TaintAssertion identifies one taint_kind.

Core v0.1 intentionally does not standardize a universal catalogue of taint kinds.

Illustrative application/policy-defined kinds include:

~~~text
untrusted_source
user_controlled
sensitive
secret
pii
unverified_tool_data
policy_defined
~~~

The meaning and propagation behavior of a taint kind are scoped by policy identity.

### 6.2 Taint state

Core Part F taint states are:

~~~text
present
absent
unknown
~~~

present means the policy asserts that the active taint kind applies somewhere in the declared subject scope.

absent means the policy asserts that the active taint kind is not present in the declared subject scope under the assertion's evidence and policy.

unknown means the available evidence does not justify present or absent.

None of these states is objective ground truth.

### 6.3 Taint channel

Core Part F channels are:

~~~text
content
control
mixed
unknown
~~~

content tracks representation ancestry.

control tracks policy-defined influence through explicit control-use/activity relationships without claiming representation contribution.

mixed records both content and control involvement.

unknown preserves inability to distinguish the channel.

### 6.4 Taint precision

Core Part F precision values are:

~~~text
exact
conservative
unknown
~~~

exact means the asserted taint scope is not intentionally broader than the provenance/mapping evidence used by the assertion.

conservative means the asserted taint scope can over-approximate the evidence because precise mapping or policy refinement is unavailable.

unknown means precision cannot be established.

Precision does not upgrade the factual truth of the taint judgement.

### 6.5 Taint basis

Part F conceptually distinguishes basis kinds:

~~~text
direct
propagated
sanitization
unknown
~~~

direct is a policy/issuer assertion not claimed to result from C2ATrace propagation.

propagated derives the active state from upstream TaintAssertions plus provenance/policy rules.

sanitization records policy-scoped discharge/reclassification through an identified Transform.

unknown preserves inability to classify the basis.

## 7. Conservative taint lattice

For one compatible tuple:

~~~text
(policy identity,
 taint_kind,
 channel,
 subject scope)
~~~

Part F defines the conservative state ordering:

~~~text
absent < unknown < present
~~~

with join:

| A | B | conservative join |
|---|---|---|
| absent | absent | absent |
| absent | unknown | unknown |
| unknown | unknown | unknown |
| present | absent | present |
| present | unknown | present |
| present | present | present |

This is a conservative propagation ordering, not a truth lattice.

Assertions from different policy contexts, taint kinds, channels, or incompatible scopes are not automatically joined.

## 8. Content-taint propagation

### 8.1 Policy-scoped propagation

A taint kind propagates only according to an identified policy/profile rule.

Core Part F supplies mechanics and safety boundaries, not a universal security policy.

### 8.2 Derivation-based propagation

Positive representation Derivation is the primary content-taint propagation relation.

When a policy marks a taint kind as content-propagating, a tainted contributor Region can support taint on the derived output Region.

Transform use without positive Derivation is insufficient for content-taint propagation.

### 8.3 RequestBinding propagation

A RequestBinding can carry content taint from a ModelInputComponent scope to its bound RequestSnapshot location under an applicable taint policy.

The propagated assertion preserves the binding evidence strength.

A structurally recorded or commitment-only binding does not become representation-verified merely because taint was propagated across it.

### 8.4 Precision inheritance

Exact content-taint propagation requires exact, coordinate-compatible provenance mapping for the asserted scope.

Partial derivation, broader region summaries, or incomplete mappings can support conservative taint but do not support exact taint scope.

### 8.5 Unknown contribution

If representation contribution itself is unknown, content-taint propagation does not manufacture a positive derivation claim.

The resulting taint state can remain unknown or be conservatively classified under an explicit policy rule, but its basis cannot be reported as exact representation ancestry.

## 9. Control-taint propagation

### 9.1 Explicit control relation

Control-taint propagation uses explicit control-use/activity evidence such as Part B usage role=control or mixed, together with an applicable taint policy.

Control-taint does not mean that input bytes/text appear in the output representation.

### 9.2 Activity and output control taint

A policy can propagate control taint to the Activity whose behavior was influenced and can conservatively propagate a control-channel assertion to generated/selected outputs when that policy explicitly defines the rule.

That propagation remains a policy assertion about influence envelope, not representation Derivation or model-internal causality.

### 9.3 Content/control separation

Control-only taint does not automatically become content taint.

Content taint does not automatically prove control influence.

mixed is used only when both channels are positively supported under the policy.

## 10. Model boundary anti-causality rule

Request inclusion and ProviderAttempt execution do not establish that a model-visible tainted input caused or contributed representation content to ModelOutput.

Therefore core v0.1 has no automatic content- or control-taint propagation rule from:

~~~text
RequestSnapshot
→ ProviderAttempt
→ ModelOutput
~~~

A policy can issue a separate assertion such as exposure-risk metadata, but it cannot be reported as representation ancestry or model-internal causality unless separate evidence exists.

The same restriction applies from arbitrary ModelInputComponent ancestry directly to ToolProposal merely because the proposal appeared in a later ModelOutput.

## 11. Tool, result, and effect taint boundaries

### 11.1 ToolProposal to ToolInvocation

ToolProposal → ToolInvocation argument taint can propagate through the explicit Part E ToolPreparation Transform / Derivation graph.

This is ordinary content-taint propagation at the argument Region level.

### 11.2 ToolInvocation to ToolExecution

A policy can classify ToolExecution with control/input taint based on the ToolInvocation it attempts to execute.

This does not imply that external effects actually inherit or contain invocation representation.

### 11.3 ToolExecution to ToolResult

ToolResult does not automatically inherit content taint from ToolInvocation or ToolExecution.

Tool-result content is a new application-visible representation and requires its own direct assertion or justified policy/evidence rule.

### 11.4 ToolResult to EffectObservation

The supported_by relation does not automatically propagate content taint from ToolResult to EffectObservation.

A policy can separately classify the evidentiary quality or provenance risk of an EffectObservation, but that remains an explicit TaintAssertion.

### 11.5 ToolResult to later model context

If ToolResult representation becomes later model context, taint propagation follows the explicit Transform / Derivation / RequestBinding lineage from Parts B/C.

ToolResult existence alone does not create later-context taint.

## 12. Mixed ancestry

An output can combine:

- taint-present contributors;
- taint-absent contributors;
- taint-unknown contributors;
- transform-generated content.

For a compatible content-propagating taint kind, the conservative lattice applies over relevant contributors.

A whole-Artifact summary can therefore be conservative-present even when only one exact Region is taint-present.

Region-level assertions preserve finer precision when available.

## 13. Sanitization semantics

### 13.1 Sanitizer is still a Transform

A transform name such as sanitize, escape, validate, normalize, redact, clean, or filter has no built-in taint-clearing power.

Sanitization is expressed through an explicit output TaintAssertion with basis=sanitization under an identified policy rule.

### 13.2 Sanitization discharge

A sanitization assertion identifies:

- the output subject/Region;
- the taint_kind and channel being discharged/reclassified;
- the sanitizer Transform;
- the relevant upstream TaintAssertion(s) or taint evidence;
- the policy/rule identity;
- the resulting state/precision.

The exact wire structure remains unfrozen.

### 13.3 Sanitization is kind- and scope-specific

Discharging one taint kind does not discharge other taint kinds.

Discharging one Region does not discharge sibling or ancestor scopes without policy support.

Discharging content taint does not automatically discharge control taint.

### 13.4 Sanitization effectiveness evidence

A Producer/policy can assert sanitization effectiveness.

Independent verifier confirmation requires a recognized sanitizer verification profile or other evidence sufficient for that exact claim.

Without such evidence, integrity of the assertion does not make the sanitizer objectively effective.

### 13.5 Ancestry remains immutable

Sanitization changes active taint state under a policy; it does not delete SourceRef, Derivation, prior TaintAssertion, or other provenance history.

A verifier can simultaneously report:

~~~text
upstream taint-present ancestry recorded
+
downstream taint absent under sanitizer rule P
~~~

without contradiction.

## 14. Anti-laundering rules

The following do not by themselves clear taint:

- copying into a new Artifact;
- renaming fields;
- reserializing;
- normalization;
- validation;
- changing tool/model boundaries;
- successful ToolExecution;
- successful ToolResult status;
- signing a Receipt;
- applying TrustAssertion(state=trusted);
- omitting upstream taint records from a partial Receipt.

Taint discharge is explicit, policy-scoped, evidence-bounded, and history-preserving.

## 15. Trust/Taint claim matrix

| Claim | Evidence basis | Core v0.1 interpretation |
|---|---|---|
| TrustAssertion says trusted | PRODUCER_ASSERTED/policy | Local trust assessment, not objective truth |
| TrustAssertion says untrusted | PRODUCER_ASSERTED/policy | Local trust assessment, not objective falsehood |
| TrustAssertion is signed | CRYPTOGRAPHIC + assertion | Integrity/authenticity under key; judgement still asserted |
| SourceRef trusted → SourceObservation trusted | unsupported automatically | Requires separate TrustAssertion/policy result |
| TaintAssertion state=present | PRODUCER_ASSERTED/policy | Active taint asserted in scope |
| TaintAssertion state=absent | PRODUCER_ASSERTED/policy | Absence asserted under scope/policy, not objective cleanliness |
| TaintAssertion state=unknown | PRODUCER_ASSERTED knowledge state | No stronger taint state justified |
| Content taint propagated across exact Derivation | STRUCTURAL/REPRESENTATION + policy | Can preserve exact scope when evidence permits |
| Content taint propagated across partial mapping | STRUCTURAL + policy | Conservative scope; not exact |
| Control-taint propagated from control input | STRUCTURAL usage + policy | Influence-envelope assertion, not content ancestry |
| Request taint automatically becomes model-output taint | prohibited core inference | Would overclaim model causality |
| Sanitizer outputs state=absent | policy assertion; optionally stronger evidence | Does not erase tainted ancestry |
| Sanitized means trusted | prohibited inference | Trust and taint are independent |
| Tainted means malicious | prohibited inference | Taint is policy metadata, not moral/security verdict |
| ToolResult success clears taint | prohibited inference | Execution/result status is unrelated |
| Missing TaintAssertion means absent | prohibited inference | Absence of record is not negative proof |

## 16. Normative Trust requirements

### TRUST-001 — Trust subject cardinality

Every TrustAssertion MUST identify exactly one subject.

Planned test: trust-subject-cardinality-001.

### TRUST-002 — No self-subject assertion

A TrustAssertion MUST NOT identify itself as its own subject.

Planned test: trust-no-self-subject-001.

### TRUST-003 — Trust assertion identity is occurrence-based

A verifier MUST NOT merge distinct TrustAssertion identities solely because their subjects, dimensions, states, issuers, policy identities, bases, or timestamps match.

Planned test: trust-assertion-no-merge-001.

### TRUST-004 — Trust dimension is explicit

Every TrustAssertion MUST identify exactly one trust dimension.

Planned test: trust-dimension-001.

### TRUST-005 — Core trust state

Every core Part F TrustAssertion MUST identify exactly one state from trusted, untrusted, or unknown.

Planned test: trust-state-vocabulary-001.

### TRUST-006 — Issuer is explicit or unknown

Every TrustAssertion MUST identify exactly one asserted_by issuer reference or explicitly record asserted_by=unknown.

Planned test: trust-issuer-001.

### TRUST-007 — Policy context is explicit or unknown

Every TrustAssertion MUST identify one policy/context identity or explicitly record policy=unknown.

Planned test: trust-policy-context-001.

### TRUST-008 — Cross-policy labels are not automatically equivalent

A verifier MUST NOT merge, compare as interchangeable, or resolve TrustAssertions solely because their dimensions and trust-state labels match when their policy contexts differ.

Planned test: trust-cross-policy-no-equivalence-001.

### TRUST-009 — Unknown trust is first-class

A verifier MUST NOT replace TrustAssertion(state=unknown) with trusted or untrusted without separate evidence/policy assertion.

Planned test: trust-unknown-preserved-001.

### TRUST-010 — Missing assertion is not explicit unknown

Absence of TrustAssertion in the supplied Receipt MUST NOT be reported as an explicit trust state of unknown, trusted, or untrusted.

Planned test: trust-absence-not-state-001.

### TRUST-011 — Trust is not objective truth

A verifier MUST NOT restate TrustAssertion(state=trusted) as objective truthworthiness or TrustAssertion(state=untrusted) as objective falsehood/maliciousness.

Planned test: trust-wording-bounded-001.

### TRUST-012 — No SourceRef inheritance

A verifier MUST NOT infer SourceObservation trust from SourceRef trust or SourceRef trust from SourceObservation trust without a separate applicable assertion/policy rule.

Planned test: trust-source-no-inheritance-001.

### TRUST-013 — No derivation inheritance

A verifier MUST NOT infer trust state for a derived Artifact solely from trust state of its contributor Artifacts.

Planned test: trust-derivation-no-inheritance-001.

### TRUST-014 — No containment inheritance

A verifier MUST NOT infer trust between a container and contained member solely from containment, including ModelOutput/OutputItem relationships.

Planned test: trust-containment-no-inheritance-001.

### TRUST-015 — No request/output inheritance

A verifier MUST NOT propagate trust automatically across RequestBinding, ProviderAttempt, or ProviderAttempt→ModelOutput relationships.

Planned test: trust-request-output-no-inheritance-001.

### TRUST-016 — No tool-chain inheritance

A verifier MUST NOT propagate trust automatically from ToolProposal to ToolInvocation, ToolExecution, ToolResult, or EffectObservation.

Planned test: trust-tool-chain-no-inheritance-001.

### TRUST-017 — Signature does not upgrade trust judgement

A verifier MUST NOT report a cryptographically valid TrustAssertion as objectively correct solely because its signature or integrity envelope validates.

Planned test: trust-signature-no-truth-upgrade-001.

### TRUST-018 — Trust does not create taint

A verifier MUST NOT synthesize a TaintAssertion solely from a TrustAssertion without an explicit applicable policy rule/assertion.

Planned test: trust-no-implicit-taint-001.

### TRUST-019 — Taint does not create trust

A verifier MUST NOT synthesize a TrustAssertion solely from a TaintAssertion.

Planned test: trust-no-taint-conversion-001.

### TRUST-020 — Trust does not authorize tools

A verifier MUST NOT infer ToolDecision allow/deny or ToolExecution authorization solely from TrustAssertion state.

Planned test: trust-no-tool-authorization-001.

### TRUST-021 — Conflicting assertions are preserved

When incompatible TrustAssertions are present and no applicable precedence/supersession profile resolves them, a verifier MUST preserve/report the conflict rather than select one value.

Planned test: trust-conflict-preserved-001.

### TRUST-022 — Timestamp is not trust precedence

A verifier MUST NOT resolve conflicting TrustAssertions solely by choosing the assertion with the latest timestamp.

Planned test: trust-no-last-write-wins-001.

### TRUST-023 — Unknown issuer/policy limits wording

A verifier MUST NOT describe a TrustAssertion with asserted_by=unknown or policy=unknown as an identified policy authority judgement.

Planned test: trust-unknown-authority-wording-001.

### TRUST-024 — Region trust does not imply whole-artifact trust

A verifier MUST NOT expand a TrustAssertion on one Artifact Region to the entire Artifact without an explicit policy/assertion supporting that scope.

Planned test: trust-region-no-whole-upgrade-001.

## 17. Normative Taint requirements

### TAINT-001 — Taint subject cardinality

Every TaintAssertion MUST identify exactly one subject.

Planned test: taint-subject-cardinality-001.

### TAINT-002 — No self-subject assertion

A TaintAssertion MUST NOT identify itself as its own subject.

Planned test: taint-no-self-subject-001.

### TAINT-003 — Taint assertion identity is occurrence-based

A verifier MUST NOT merge distinct TaintAssertion identities solely because their subjects, taint kinds, states, channels, precisions, issuers, policies, bases, or timestamps match.

Planned test: taint-assertion-no-merge-001.

### TAINT-004 — Taint kind is explicit

Every TaintAssertion MUST identify exactly one taint_kind.

Planned test: taint-kind-001.

### TAINT-005 — Core taint state

Every core Part F TaintAssertion MUST identify exactly one state from present, absent, or unknown.

Planned test: taint-state-vocabulary-001.

### TAINT-006 — Core taint channel

Every core Part F TaintAssertion MUST identify exactly one channel from content, control, mixed, or unknown.

Planned test: taint-channel-vocabulary-001.

### TAINT-007 — Core taint precision

Every core Part F TaintAssertion MUST identify exactly one precision from exact, conservative, or unknown.

Planned test: taint-precision-vocabulary-001.

### TAINT-008 — Taint issuer is explicit or unknown

Every TaintAssertion MUST identify exactly one asserted_by issuer reference or explicitly record asserted_by=unknown.

Planned test: taint-issuer-001.

### TAINT-009 — Taint policy is explicit or unknown

Every TaintAssertion MUST identify one policy/context identity or explicitly record policy=unknown.

Planned test: taint-policy-context-001.

### TAINT-010 — Missing assertion is not absent

Absence of TaintAssertion in the supplied Receipt MUST NOT be reported as taint state=absent.

Planned test: taint-absence-not-absent-001.

### TAINT-011 — Missing assertion is not explicit unknown

Absence of TaintAssertion in the supplied Receipt MUST NOT be reported as an explicit taint state=unknown.

Planned test: taint-absence-not-unknown-001.

### TAINT-012 — Taint present is not maliciousness

A verifier MUST NOT restate TaintAssertion(state=present) as proof that the subject is malicious, unsafe, false, or compromised.

Planned test: taint-present-no-maliciousness-001.

### TAINT-013 — Taint absent is not objective cleanliness

A verifier MUST NOT restate TaintAssertion(state=absent) as proof that the subject is objectively clean, safe, trustworthy, or free of omitted tainted ancestry.

Planned test: taint-absent-bounded-001.

### TAINT-014 — Conservative lattice compatibility

A verifier MUST NOT apply the Part F taint-state join across assertions with incompatible policy identities, taint kinds, channels, or incomparable subject scopes.

Planned test: taint-lattice-compatibility-001.

### TAINT-015 — Present dominates conservative join

For compatible assertions combined under the Part F conservative lattice, state=present MUST dominate unknown and absent.

Planned test: taint-lattice-present-001.

### TAINT-016 — Unknown dominates absent

For compatible assertions combined under the Part F conservative lattice when no present state applies, state=unknown MUST dominate absent.

Planned test: taint-lattice-unknown-001.

### TAINT-017 — Absent requires bounded complete support

A verifier MUST NOT derive state=absent from upstream contributor assertions unless the applicable policy rule has complete relevant contributor accounting for the claimed scope and no unresolved applicable contributor remains.

Planned test: taint-absent-complete-support-001.

### TAINT-018 — Propagation requires policy context

A verifier MUST NOT automatically propagate a taint kind across provenance relations without an applicable policy/profile rule defining that taint kind's propagation behavior.

Planned test: taint-propagation-policy-required-001.

### TAINT-019 — Content propagation requires positive representation relation

A verifier MUST NOT propagate content-channel taint solely from Transform use, temporal order, containment, or graph proximity without positive representation Derivation, RequestBinding inclusion, or another profile-defined representation relation.

Planned test: taint-content-positive-relation-001.

### TAINT-020 — Control-only use is not content taint

A verifier MUST NOT convert control-only usage into content-channel taint without separate positive representation ancestry.

Planned test: taint-control-not-content-001.

### TAINT-021 — Data use without derivation is insufficient

A verifier MUST NOT infer content-taint propagation solely because an Artifact has usage role=data when representation contribution remains unestablished.

Planned test: taint-data-use-no-derivation-001.

### TAINT-022 — Control propagation requires explicit control evidence

A verifier MUST NOT report propagated control-channel taint unless explicit control/mixed usage evidence and an applicable policy rule support that propagation.

Planned test: taint-control-propagation-evidence-001.

### TAINT-023 — Mixed channel requires both channels

A verifier MUST NOT classify propagated taint channel=mixed unless both content and control channels are positively supported under the applicable policy.

Planned test: taint-mixed-channel-001.

### TAINT-024 — Propagation cannot strengthen evidence

A propagated TaintAssertion MUST NOT be reported with stronger provenance/evidence verification than the weakest premise required for its propagation.

Planned test: taint-propagation-no-evidence-upgrade-001.

### TAINT-025 — Exact precision requires exact scope mapping

A verifier MUST NOT report propagated precision=exact unless the provenance/mapping evidence is exact and coordinate-compatible for the asserted scope.

Planned test: taint-exact-requires-exact-mapping-001.

### TAINT-026 — Partial mapping degrades precision

If a required content-provenance mapping is partial or the assertion intentionally over-approximates scope, a verifier MUST NOT report propagated taint precision=exact.

Planned test: taint-partial-conservative-001.

### TAINT-027 — Unknown contribution is not exact propagation

When representation contribution is unknown, a verifier MUST NOT report exact content-taint propagation through that unknown contribution.

Planned test: taint-unknown-contribution-001.

### TAINT-028 — RequestBinding verification bounds taint propagation

A verifier MUST NOT upgrade taint propagated through a RequestBinding beyond the binding's established location/representation verification level.

Planned test: taint-binding-evidence-bound-001.

### TAINT-029 — No automatic model-boundary taint propagation

A verifier MUST NOT automatically propagate taint from ModelInputComponent or RequestSnapshot to ModelOutput or ToolProposal solely because the model invocation used that request.

Planned test: taint-no-model-causality-001.

### TAINT-030 — Model exposure assertion is not content ancestry

If a policy issues taint/risk metadata because a model was exposed to tainted input, a verifier MUST NOT report that metadata as representation Derivation from the input to ModelOutput.

Planned test: taint-model-exposure-wording-001.

### TAINT-031 — ToolProposal to ToolInvocation follows derivation

Content taint from ToolProposal arguments to ToolInvocation arguments MUST NOT be propagated without the explicit ToolPreparation Derivation lineage required by Part E.

Planned test: taint-tool-argument-lineage-001.

### TAINT-032 — Invocation taint does not imply ToolResult content taint

A verifier MUST NOT automatically propagate content taint from ToolInvocation or ToolExecution to ToolResult solely because the execution used that invocation.

Planned test: taint-invocation-no-result-content-001.

### TAINT-033 — Result support does not imply EffectObservation content taint

A verifier MUST NOT automatically propagate ToolResult content taint through supported_by into EffectObservation as representation ancestry.

Planned test: taint-result-effect-no-content-propagation-001.

### TAINT-034 — ToolResult later-context taint needs explicit lineage

A verifier MUST NOT report ToolResult taint as present in later model context without explicit Transform / Derivation / RequestBinding provenance to that later request.

Planned test: taint-result-context-lineage-001.

### TAINT-035 — Sanitizer name does not clear taint

A verifier MUST NOT infer taint discharge solely from Transform names, types, metadata, or labels such as sanitize, escape, validate, normalize, redact, clean, or filter.

Planned test: taint-sanitizer-name-no-clear-001.

### TAINT-036 — Sanitization discharge basis is explicit

A TaintAssertion with basis=sanitization and state=absent MUST identify the sanitizer Transform, the applicable taint_kind/channel/scope, policy/rule identity, and relevant upstream taint evidence.

Planned test: taint-sanitization-basis-001.

### TAINT-037 — Sanitization does not erase ancestry

A verifier MUST NOT remove, hide, or reinterpret upstream Derivation or prior TaintAssertions solely because a downstream sanitization assertion records state=absent.

Planned test: taint-sanitization-history-preserved-001.

### TAINT-038 — Sanitization is scope-specific

A verifier MUST NOT expand a sanitization discharge beyond the taint_kind, channel, and subject scope explicitly supported by the sanitization assertion/policy rule.

Planned test: taint-sanitization-scope-001.

### TAINT-039 — Sanitization effectiveness is not self-proving

A verifier MUST NOT report sanitization as independently effective solely because a Producer/policy asserts basis=sanitization or because the sanitizer Transform completed.

Planned test: taint-sanitization-no-self-proof-001.

### TAINT-040 — Unknown sanitizer effectiveness does not become absent

When sanitizer effectiveness for the applicable taint_kind/scope cannot be established under the policy, a verifier MUST NOT upgrade the downstream state to absent solely from sanitizer execution.

Planned test: taint-sanitization-unknown-no-clear-001.

### TAINT-041 — Sanitization does not create trust

A verifier MUST NOT synthesize TrustAssertion(state=trusted) solely from successful or asserted sanitization.

Planned test: taint-sanitized-not-trusted-001.

### TAINT-042 — Trust does not discharge taint

A verifier MUST NOT change taint state from present/unknown to absent solely because the subject also carries TrustAssertion(state=trusted).

Planned test: taint-trust-no-discharge-001.

### TAINT-043 — Copy/rename/serialization does not discharge taint

A verifier MUST NOT infer taint discharge solely from copying, renaming, restructuring, normalization, serialization, encoding, or movement across protocol object boundaries.

Planned test: taint-transform-no-laundering-001.

### TAINT-044 — Successful execution/result does not discharge taint

A verifier MUST NOT infer taint discharge solely from ToolExecution completion or ToolResult success/status.

Planned test: taint-tool-success-no-clear-001.

### TAINT-045 — Signature/integrity does not discharge taint

A verifier MUST NOT infer taint discharge solely because the relevant Artifact, Assertion, Receipt, or IntegrityEnvelope passes cryptographic integrity verification.

Planned test: taint-integrity-no-clear-001.

### TAINT-046 — Partial Receipt cannot prove taint absence

A verifier MUST NOT report state=absent solely because no taint-present ancestry is visible in a supplied Receipt whose completeness is not independently established.

Planned test: taint-partial-receipt-no-absence-001.

### TAINT-047 — Region taint can support conservative whole scope

When a Region within an Artifact has state=present under a compatible policy/taint kind, a verifier MAY report a whole-Artifact summary as conservative-present under that same policy/kind, while preserving that the exact tainted Region can be narrower.

Planned test: taint-region-to-whole-conservative-001.

### TAINT-048 — Whole-scope present does not mean every subregion is tainted

A verifier MUST NOT infer that every subregion of an Artifact is taint-present solely from a whole-Artifact state=present assertion unless the assertion/policy explicitly establishes full-scope applicability.

Planned test: taint-whole-not-every-region-001.

### TAINT-049 — Conflicting taint assertions are preserved

When incompatible TaintAssertions are present and no applicable precedence/supersession profile resolves them, a verifier MUST preserve/report the conflict rather than silently select one state.

Planned test: taint-conflict-preserved-001.

### TAINT-050 — Timestamp is not taint precedence

A verifier MUST NOT resolve conflicting TaintAssertions solely by choosing the assertion with the latest timestamp.

Planned test: taint-no-last-write-wins-001.

### TAINT-051 — Cross-policy taint is not automatically comparable

A verifier MUST NOT combine or compare TaintAssertions as one lattice state solely because their taint_kind strings match when their policy contexts differ.

Planned test: taint-cross-policy-no-join-001.

### TAINT-052 — Taint is not causal attribution

A verifier MUST NOT report TaintAssertion propagation or ancestry as proof that the tainted subject caused a model decision, ToolDecision, ToolExecution, external Effect, or Outcome.

Planned test: taint-no-causal-upgrade-001.

### TAINT-053 — Taint state does not create ToolDecision

A verifier MUST NOT infer ToolDecision allow/deny solely from TaintAssertion state.

Planned test: taint-no-tool-decision-001.

### TAINT-054 — Unknown channel remains unknown

A verifier MUST NOT replace channel=unknown with content, control, or mixed solely from temporal order or object adjacency.

Planned test: taint-unknown-channel-001.

### TAINT-055 — Unknown precision remains unknown

A verifier MUST NOT replace precision=unknown with exact or conservative without additional mapping/policy evidence.

Planned test: taint-unknown-precision-001.

### TAINT-056 — Unknown taint state remains unknown

A verifier MUST NOT replace state=unknown with present or absent without separate applicable evidence/policy.

Planned test: taint-unknown-state-001.

## 18. Adversarial architecture review

### Review A — Trusted SourceRef, modified SourceObservation

A SourceRef is marked trusted under one policy, then a SourceObservation is captured later.

The observation does not automatically inherit trust.

Result: RESOLVED by TRUST-012.

### Review B — Trusted input plus untrusted input concatenated

Trust does not compose automatically through concat.

Taint can conservatively propagate under a policy using explicit Derivation.

Result: RESOLVED by TRUST-013 and TAINT-018 through TAINT-026.

### Review C — Untrusted source influences rerank only

The source changes ranking but its representation is not emitted.

A policy can propagate control taint without content taint.

Result: RESOLVED by TAINT-020 through TAINT-023.

### Review D — Untrusted context enters model request, model emits tool proposal

The request contains tainted input.

Core v0.1 does not automatically mark the ModelOutput or ToolProposal as content-derived or tainted from that input because model-internal causality is not observed.

A separate policy can issue exposure-risk taint, but the verifier preserves its policy-asserted nature.

Result: RESOLVED by TAINT-029 and TAINT-030.

### Review E — ToolProposal argument copied into ToolInvocation

Explicit ToolPreparation Derivation maps the proposal argument to the effective invocation argument.

Content taint can propagate along that mapping.

Result: RESOLVED by TAINT-031.

### Review F — Runtime injects secret argument

The secret has direct taint_kind=secret.

Only the secret argument Region needs exact content taint; the whole invocation can receive a conservative-present summary.

Result: RESOLVED by TAINT-047 and TAINT-048.

### Review G — Redaction replaces secret with [REDACTED]

The redaction output retains Derivation ancestry to the secret input.

A policy can assert taint_kind=contains_secret_content as absent after a verified/claimed sanitizer while the upstream secret taint and ancestry remain recorded.

Result: RESOLVED by TAINT-035 through TAINT-041.

### Review H — Sanitizer merely renames a field

No sanitizer name or transform metadata clears taint.

Result: RESOLVED by TAINT-035 and TAINT-043.

### Review I — Sanitized output is marked trusted

Sanitization and trust remain independent.

A separate TrustAssertion is required.

Result: RESOLVED by TAINT-041.

### Review J — Signed receipt says source is trusted

Signature validation authenticates the recorded assertion representation under a key; it does not make the trust judgement objectively true.

Result: RESOLVED by TRUST-017.

### Review K — Two trust policies disagree

Both assertions remain available.

No timestamp or generic label precedence picks a winner.

Result: RESOLVED by TRUST-008, TRUST-021, and TRUST-022.

### Review L — Taint policy A and policy B use same kind string

The assertions are not joined solely because both say sensitive.

Result: RESOLVED by TAINT-014 and TAINT-051.

### Review M — Partial lineage includes known tainted contributor

Positive contribution is known but exact mapping is partial.

The policy can produce conservative-present taint, not exact scope.

Result: RESOLVED by TAINT-025 and TAINT-026.

### Review N — Unknown contributor with no positive derivation

Content taint is not fabricated as exact ancestry.

State can remain unknown or be conservatively classified only under an explicit policy rule.

Result: RESOLVED by TAINT-027.

### Review O — Whole artifact has one tainted Region

The exact Region remains available.

A whole-artifact conservative-present summary is allowed without claiming every byte/field is tainted.

Result: RESOLVED by TAINT-047 and TAINT-048.

### Review P — ToolInvocation is tainted; ToolResult returns fixed "OK"

The result does not automatically inherit content taint.

If a policy wants an evidentiary/control classification, it issues a separate assertion.

Result: RESOLVED by TAINT-032.

### Review Q — ToolResult is tainted and supports EffectObservation

supported_by does not mean representation derivation.

The EffectObservation does not automatically inherit ToolResult content taint.

Result: RESOLVED by TAINT-033.

### Review R — ToolResult later becomes context

Only explicit Transform / Derivation / RequestBinding lineage carries content taint into the later request.

Result: RESOLVED by TAINT-034.

### Review S — Successful tool call used as sanitizer proof

Execution completion and success status do not establish sanitization effectiveness or taint discharge.

Result: RESOLVED by TAINT-039, TAINT-040, and TAINT-044.

### Review T — Partial Receipt omits tainted ancestor

No visible taint-present path is insufficient to prove absence because receipt completeness is not established.

Result: RESOLVED by TAINT-046.

### Review U — TrustAssertion used directly to allow a tool

Core does not turn trust state into ToolDecision.

The application/policy can separately issue ToolDecision with TrustAssertion as basis.

Result: RESOLVED by TRUST-020.

### Review V — TaintAssertion used directly to deny a tool

Core does not turn taint state into ToolDecision.

A separate policy decision remains necessary.

Result: RESOLVED by TAINT-053.

### Review W — Control-tainted policy changes template, then static output is emitted

The output can receive control-channel taint under a policy, but not content-channel taint from the policy text without positive Derivation.

Result: RESOLVED by TAINT-020 through TAINT-023.

### Review X — Provider request has taint; output text happens to copy it exactly

String equality alone does not justify model-boundary taint propagation or Derivation.

A future provider evidence profile could establish a stronger relation, but core does not infer it.

Result: RESOLVED by TAINT-029 and existing derivation rules.

## 19. Architecture revisions caused by Part F

### 19.1 Trust becomes dimensioned and policy-scoped

TrustAssertion is no longer a generic trusted/untrusted bit.

Its meaning is:

~~~text
subject
+
trust dimension
+
trust state
+
asserted_by
+
policy context
+
basis
~~~

Trust remains local and non-inheriting.

### 19.2 Taint becomes state + channel + precision

TaintAssertion semantics are:

~~~text
subject scope
+
taint_kind
+
state: present | absent | unknown
+
channel: content | control | mixed | unknown
+
precision: exact | conservative | unknown
+
asserted_by
+
policy context
+
basis
~~~

### 19.3 Taint propagation is policy-scoped

Core defines a conservative lattice and safe relation boundaries.

Each taint kind's actual propagation behavior is defined by an identified policy/profile.

This keeps C2ATrace policy-neutral.

### 19.4 Sanitization discharges active taint, not provenance history

Sanitization can change downstream active taint state under a policy.

It never rewrites historical Source/Derivation/Taint provenance.

### 19.5 Model boundary remains non-causal

Part F explicitly refuses automatic taint propagation from request/input to ModelOutput.

This prevents taint from becoming disguised model causal attribution.

## 20. Part F resolved decisions

Part F locks the following decisions:

1. TrustAssertion and TaintAssertion are occurrence-identified policy assertions.
2. Assertions target one explicit subject and record issuer plus policy context or explicit unknown.
3. Trust is dimensioned; trusted/untrusted/unknown are local assessments, not objective properties.
4. Trust does not automatically inherit along any provenance relation.
5. Trust does not automatically create taint or ToolDecision.
6. Taint kinds are policy-defined; core standardizes state/channel/precision mechanics.
7. Taint state lattice is absent < unknown < present for compatible conservative joins.
8. Taint channels distinguish content from control influence.
9. Exact/conservative/unknown precision prevents false range precision.
10. Content taint propagates only through positive representation relations under an applicable policy.
11. Control taint requires explicit control evidence plus policy.
12. Taint propagation cannot have stronger verification than its weakest premise.
13. RequestBinding evidence level bounds propagated taint evidence.
14. No automatic taint propagation crosses the model request→output boundary.
15. ToolProposal→ToolInvocation taint follows explicit argument Derivation.
16. ToolInvocation/Execution taint does not automatically become ToolResult content taint.
17. ToolResult supported_by EffectObservation does not create representation ancestry.
18. Sanitizer metadata alone never clears taint.
19. Sanitization discharge is kind/channel/scope-specific and keeps upstream taint history.
20. Sanitization does not create trust.
21. Trusted state does not discharge taint.
22. Tool success, signature validity, serialization, renaming, and partial-receipt omission do not launder taint.
23. Missing assertions are not negative states.
24. Conflicting trust/taint assertions remain conflicts absent explicit precedence semantics.
25. Trust/taint never directly establish model causality, tool authorization, external Effect, or Outcome.

## 21. Open items handed to later phases

Part F intentionally does not freeze:

- JSON field names or enum serialization;
- principal/issuer identity wire format;
- policy object wire format;
- standard trust-dimension registry;
- standard taint-kind registry;
- application-specific policy precedence;
- assertion supersession model;
- executable sanitizer-verification profiles;
- policy engine implementation;
- authorization rules;
- provider-internal exposure proofs;
- cross-receipt trust/taint resolution.

These remain constrained by Part F semantics.

## 22. Gate decision

Phase 1 Part F is ready for adversarial/mechanical review.

JSON Schema and implementation remain BLOCKED.
