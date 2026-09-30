# C2ATrace v0.1 Claim Matrix

Status: Phase 0 baseline, second-review revision.

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
PRODUCER_ASSERTED TrustAssertion(label="untrusted")
=
verified statement:
  "a source carrying an 'untrusted' TrustAssertion is on the recorded path"

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

When trust status comes from TrustAssertion, verifier output MUST preserve that it is an asserted label and MUST NOT restate it as objective source truth.

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
| ModelOutput references ProviderAttempt | E1 + E4 premise | Partial | Link is structural; capture occurrence is asserted |
| ToolProposal is structurally contained in ModelOutput | E1; E2 if bytes supplied | Yes/conditional | Structure versus representation verification |
| ToolInvocation differs from ToolProposal | E2 | Conditional | Requires comparable representations |
| Producer states ToolExecution occurred | E4 | Yes, as an assertion | Runtime occurrence not independently proven |
| ToolResult artifact exists | E1 | Yes | Origin/return occurrence may still be E4 |
| EffectObservation exists with evidence basis | E1 + E4 premise | Partial | Observation record is not external truth |
| A source carrying TrustAssertion(label="untrusted") is on recorded path | E1 + E4 premise | Yes, with asserted-label wording | Does not establish objective untrustworthiness |
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
