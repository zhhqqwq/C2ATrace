# C2ATrace v0.1 Claim Matrix

Status: Phase 1 Part H aligned.

## 1. Claim evidence model

The previous draft described C1-C5 as "claim strength classes." That was too rigid because one claim can depend on multiple kinds of evidence.

Phase 0 now uses **evidence basis tags**, which may be combined:

### E1 — STRUCTURAL

Established from supplied graph structure and protocol invariants.

Examples: reference resolves, object type is compatible, graph invariant holds.

### E2 — REPRESENTATION

Established by comparing supplied representations, ranges, or digests under defined representation rules.

Examples: digest matches bytes; a fragment matches a supplied request range.

### E3 — CRYPTOGRAPHIC

Established by validating a cryptographic commitment or signature under the relevant cryptographic profile.

Cryptographic validity does not establish external truth or completeness.

### E4 — PRODUCER_ASSERTED

The Producer states that a runtime or external fact occurred.

Examples: a URL was fetched, a request was transmitted, a tool execution occurred, a remote service returned a result.

The verifier may validate the assertion's syntax, references, and integrity without establishing the external fact.

### P1 — PROHIBITED_INFERENCE

P1 is not an evidence basis. It marks conclusions that core C2ATrace v0.1 does not automatically derive from weaker premises.

Examples:

- Source X caused downstream action Y.
- The Producer captured everything.
- a source labeled trusted is objectively trustworthy.
- a valid signature means the recorded events are true.
- tool success means the intended outcome succeeded.
- valid supplied receipt linkage means the full history is complete.

## 2. Normative claim-reporting requirements

### CLAIM-000 — Evidence composition

A claim MAY depend on multiple evidence tags. A verifier MUST preserve the weakest unresolved premise when reporting the composed claim.

Planned test: `claim-composition-001`.

For example:

~~~text
STRUCTURAL graph path
+
PRODUCER_ASSERTED TrustAssertion(
  dimension="source_authority",
  state="untrusted",
  policy="P"
)
=
verified statement:
  "a source carrying an asserted 'untrusted' state for
   dimension 'source_authority' under policy P is on the recorded path"

not:
  "an objectively untrusted source is on the path"
~~~

### CLAIM-001 — No evidence-basis upgrade

A verifier MUST NOT report a PRODUCER_ASSERTED premise as independently established external truth solely because STRUCTURAL, REPRESENTATION, or CRYPTOGRAPHIC checks succeed.

Planned test: `claim-no-upgrade-001`.

### CLAIM-002 — Binding verification levels

A verifier MUST preserve distinct RequestBinding evidence states when they differ, including:

- recorded;
- structurally valid;
- location-resolved;
- commitment-matched;
- representation-verified.

If the target representation or a recognized location/inclusion proof is unavailable, it MUST NOT report a subpath or subrange binding as location-resolved or representation-verified solely from recorded digests.

Planned test: `binding-verification-level-001`.

### CLAIM-003 — Trust-label wording

When trust status comes from TrustAssertion, verifier output MUST preserve its asserted state, trust dimension, issuer/policy context when available, and MUST NOT restate it as objective source truth.

Planned test: `trust-label-wording-001`.

### CLAIM-004 — Absence wording

A verifier MUST distinguish "not present in the supplied Receipt" from "did not happen."

Planned test: `absence-wording-001`.

### CLAIM-005 — Prohibited causal strengthening

A verifier MUST NOT transform inclusion, derivation, taint ancestry, or graph reachability into model-internal causal responsibility.

Planned test: `claim-causality-001`.

## 3. Claim matrix

| Claim | Evidence basis | Offline verifier | Meaning |
|---|---|---:|---|
| Receipt structure is valid | E1 | Yes | Structural only |
| Object reference resolves | E1 | Yes | Structural |
| Graph invariants hold | E1 | Yes | Internal consistency |
| Digest matches supplied representation | E2 | Yes | Representation equality |
| RequestBinding is structurally valid | E1 | Yes | Does not prove target path exists in hidden content |
| RequestBinding target location resolves | E2 or recognized proof | Conditional | Requires target representation/proof |
| Component matches recorded request location | E2 | Conditional | Requires source and target representations or recognized proof |
| Compatible commitments match | E2 | Conditional | Commitment equality is distinct from target-location membership |
| Signature is mathematically valid | E3 | Yes | Cryptographic validity only |
| Public key belongs to organization X | External | No | Key identity outside core v0.1 |
| Producer states URL X was fetched | E4 | Yes, as an assertion | Does not prove remote origin |
| SourceObservation digest matches supplied bytes | E2 | Yes | Does not prove source origin |
| Producer states observed_at = T | E4 | Yes, as an assertion | No trusted timestamp |
| Producer states request R was transmitted | E4 | Yes, as an assertion | Does not prove Provider receipt |
| Provider received request R | External / unsupported by core | No | Requires external/provider evidence |
| Provider internally supplied exactly R to the model | P1 unless future evidence profile exists | No | Core v0.1 does not establish |
| ProviderAttempt belongs to ModelInvocation | E1 + E4 premise | Partial | Grouping is structural/Producer-recorded, not inferred from equality |
| ProviderAttempt terminal disposition is recorded | E4 | Yes, as an assertion | Application-observed lifecycle classification |
| ModelOutput references ProviderAttempt | E1 + E4 premise | Partial | Ownership is structural; capture occurrence is asserted |
| ModelInvocation accepts ModelOutput | E4 + E1 ownership check | Partial | Application selection; does not establish completeness |
| ModelOutput capture_extent=complete | E4 | No external proof | Complete only relative to declared application-visible capture scope |
| ModelOutput response_termination=complete | E4 | No external proof | Normal completion observed at application boundary |
| Provider-reported model identifier | E4 | No | Does not establish provider-internal model identity |
| OutputItem representation matches supplied content | E2 | Conditional | Representation equality only |
| ToolProposal is structurally contained in ModelOutput | E1; E2 if representation supplied | Yes/conditional | Proposal is output occurrence, not authorization/execution |
| ToolInvocation derives from ToolProposal | E1 + E4; E2 where mappings are independently checked | Conditional | Positive preparation lineage; not implicit from matching args |
| ToolInvocation argument is model_supplied/application_supplied/mixed | Derived from explicit lineage | Conditional | Bounded provenance summary, not hidden model causality |
| ToolDecision allow/deny exists | E1 + E4 | Yes, as assertion | Does not establish execution or policy correctness |
| Producer states ToolExecution occurred | E4 | Yes, as an assertion | Runtime occurrence not independently proven |
| ToolExecution disposition=completed | E4 | Yes, as assertion | Does not establish semantic success/effect |
| ToolResult artifact exists | E1 + E4 premise | Partial | Returned representation; external truth not established |
| ToolResult reports success | E4/tool-reported | No external proof | Does not establish external effect |
| EffectObservation basis=execution_result | E1 + E4 premise | Partial | Same execution/result supports bounded claim |
| EffectObservation basis=separate_observation | E1 + E4 premise | Partial | Distinct observation supports bounded claim, still not objective truth |
| TrustAssertion state=trusted/untrusted/unknown | E4 | Yes, as assertion | Local issuer/policy assessment, not objective trustworthiness |
| Conflicting TrustAssertions exist | E1 + E4 premises | Yes | Preserve conflict; no timestamp winner without policy precedence |
| TaintAssertion state=present/absent/unknown | E4 | Yes, as assertion | Policy-scoped taint state, not maliciousness/cleanliness |
| Propagated taint follows exact verified lineage | E1/E2 + E4 policy rule | Conditional | Evidence strength cannot exceed weakest propagation premise |
| Sanitization records downstream taint absent | E4; stronger only with sanitizer evidence profile | Conditional | Does not erase upstream tainted ancestry or create trust |
| Original representation is disclosed in this Receipt | Direct package inspection | Yes | Package-relative disclosure fact only |
| Original representation is withheld in this Receipt | Package structure/profile | Yes | Does not prove non-observation, deletion, or absence elsewhere |
| Unkeyed commitment candidate matches | E2 + candidate | Conditional | Candidate/commitment match only; low-entropy enumeration remains possible |
| HMAC candidate matches | E2 + candidate + secret capability | Conditional | Authorized keyed verification, not public verification |
| Redacted derivative commitment matches | E2 | Conditional | Redacted representation only |
| Redacted derivative proves original plaintext | P1 | No | Prohibited evidence-scope upgrade |
| Whole commitment proves hidden RequestBinding sublocation | P1 | No | Needs target representation or recognized inclusion proof |
| hash_only/hmac proves global confidentiality | P1 | No | Privacy is package-relative and metadata/linkability can leak |
| Receipt package inventory is complete for supplied ARP | E1/E2 | Conditional | Package membership only, not runtime/history completeness |
| ExternalReference uniquely resolves | E1 plus supplied Resolution Set | Conditional | Resolution only; exact target payload binding requires pin |
| ExternalReference payload pin matches | E2 | Conditional | Binds target ARP commitment, not signer/truth/completeness |
| ReceiptLink target digest matches | E2 | Conditional | Supplied linkage only, not adjacency/global history |
| ARP SHA-256 digest matches | E2 | Yes under selected profile | Computational commitment match, not factual truth |
| Ed25519 signature verifies | E3 | Yes under key/profile | Key-relative cryptographic validity only |
| Verification key belongs to named organization/person | E4 or external trust profile | No by core signature alone | Key label/reference is not real-world identity proof |
| Signed Receipt is complete history | P1 | No | Signature/linkage cannot prove omitted records/Receipts do not exist |
| Signed hash-only/redacted Receipt signs hidden plaintext directly | P1 | No | Signature authenticates disclosed ARP commitment/redacted evidence only |
| Tainted request automatically taints ModelOutput | P1 / prohibited core inference | No | Would overclaim model causality |
| Missing TaintAssertion means taint absent | P1 / prohibited inference | No | Absence of record is not a negative state |
| Desired Outcome achieved | P1 / unsupported by core | No | OutcomeVerification outside core v0.1 |
| A source carrying TrustAssertion(state="untrusted") is on recorded path | E1 + E4 premise | Yes, with asserted-state wording | Does not establish objective untrustworthiness |
| Untrusted source caused downstream action | P1 | No | Prohibited causal inference |
| Receipt signature validates under supplied trusted key | E3 | Yes | Does not prove signer honesty |
| Supplied receipt linkage is internally valid | E1/E3 depending profile | Conditional | Supplied scope only |
| Full run history is complete | P1 | No | Not established in core v0.1 |

## 4. Verifier language

Preferred status vocabulary includes:

~~~text
VALID
INVALID
MATCHED
CONSISTENT
ASSERTED
UNVERIFIED
UNKNOWN
NOT PRESENT IN SUPPLIED RECEIPT
~~~

Stronger words such as TRUE, PROVEN, SAFE, TRUSTWORTHY, CAUSED, COMPLETE, or FULLY VERIFIED should only appear if a future profile defines and establishes that exact stronger property.
