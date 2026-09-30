# C2ATrace v0.1 Claim Matrix

Status: Phase 0 baseline.

## 1. Claim strength classes

### C1 — Structurally Verifiable

The verifier can establish the claim from supplied graph structure and protocol rules alone.

Examples: reference resolves, object type is compatible, graph invariant holds.

### C2 — Representation Verifiable

The verifier can establish the claim when the necessary representation is supplied.

Examples: digest matches bytes; a fragment matches a recorded request range.

If privacy mode withholds the representation, the verifier MUST NOT report the representation-level claim as verified.

### C3 — Cryptographically Verifiable

The verifier can validate a cryptographic commitment or signature. Cryptographic validity does not establish external truth or completeness.

### C4 — Producer Asserted

The Producer records that an external or runtime event occurred. The verifier can validate the assertion's representation, references, and integrity, but not necessarily the external fact.

Examples: a URL was fetched, a provider request was transmitted, a tool execution occurred, a remote system returned a result.

### C5 — Prohibited Automatic Inference

Claims that C2ATrace v0.1 MUST NOT derive automatically.

Examples:

- Source X caused Action Y.
- The Producer captured everything.
- trusted means objectively trustworthy.
- a valid signature means the events are true.
- tool success means the intended outcome succeeded.
- a valid supplied chain means the full history is complete.

## 2. Claim matrix

| Claim | Class | Offline verifier | Meaning |
|---|---|---:|---|
| Receipt structure is valid | C1 | Yes | Structural only |
| Object reference resolves | C1 | Yes | Structural |
| Graph invariants hold | C1 | Yes | Internal consistency |
| Digest matches supplied representation | C2 | Yes | Representation equality |
| Fragment matches recorded request range | C2 | Conditional | Requires both representations |
| Signature is mathematically valid | C3 | Yes | Cryptographic integrity only |
| Public key belongs to organization X | External | No | Key trust is outside v0.1 |
| URL X was really fetched | C4 | No | Producer assertion |
| SourceObservation digest matches supplied bytes | C2 | Yes | Does not prove source origin |
| observed_at is accurate wall-clock time | C4 | No | No trusted timestamp |
| Provider received request R | C4 | No | Producer-side observation unless provider evidence exists |
| Provider internally supplied exactly R to the model | C5 | No | Prohibited without separate evidence |
| ModelOutput is linked to ProviderAttempt | C1+C4 | Partial | Link is structural; factual capture is asserted |
| ToolProposal belongs to ModelOutput | C1/C2 | Conditional | Depends on output representation availability |
| ToolInvocation differs from ToolProposal | C2 | Conditional | Requires representations |
| ToolExecution occurred | C4 | No | Producer assertion |
| ToolResult was recorded | C1+C4 | Partial | Artifact exists; external origin is asserted |
| External effect exists | C4 | No | EffectObservation is evidence, not ground truth |
| Untrusted source exists in recorded provenance envelope | Derived | Yes | Graph path plus TrustAssertion |
| Untrusted source caused downstream action | C5 | No | Prohibited causal inference |
| Receipt unchanged since signing | C3 | Yes | Subject to signature model |
| Supplied receipt chain links correctly | C1 | Yes | Supplied scope only |
| Full run history is complete | C5 | No | Not established in v0.1 |

## 3. Verifier language

A verifier SHOULD prefer precise status language such as:

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

A verifier SHOULD avoid stronger terms such as TRUE, PROVEN, SAFE, TRUSTWORTHY, CAUSED, COMPLETE, or FULLY VERIFIED unless the exact stronger property has actually been established.

In particular:

~~~text
not present in supplied receipt
≠
did not happen
~~~