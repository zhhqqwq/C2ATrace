# C2ATrace v0.1 — Schema / Semantic Check Boundary

Status: SCHEMA FREEZE IN PROGRESS.

JSON Schema is a wire-format validator. It is not the complete C2ATrace verifier.

## Directly Schema-enforced

The v0.1 schemas directly constrain, among other things:

- required discriminators and local fields;
- explicit local versus external Reference form;
- explicit Region/RequestLocation tagged unions;
- Unicode-scalar and byte interval local shape;
- SourceObservation source_ref cardinality at the object level;
- Derivation positive precision vocabulary exact/partial and non-empty contributor set;
- RequestSnapshot exactly-one owner field;
- capture-level, lifecycle, ToolDecision, Trust, Taint, Privacy, and CaptureDiagnostic vocabularies;
- Receipt protocol version/reference mode and baseline integrity identifiers;
- zero-or-more IntegrityEnvelopes;
- VerificationFinding result domain/status compatibility.

## Verifier semantic checks

The following cannot be established merely by JSON Schema and remain required semantic verification:

- object-ID uniqueness and immutable identity across a Resolution Set;
- local/external reference existence, type compatibility, unique/pinned resolution;
- Derivation and ReceiptLink acyclicity;
- Transform input/generated/selected reference correctness;
- exact Derivation complete origin accounting;
- Region interval end bounds against actual representation length;
- coordinate/path profile support and path existence;
- RequestSnapshot owner target kind and attempt-scoped reuse restrictions;
- at-most-one effective snapshot per ProviderAttempt/capture level;
- RequestBinding source/target representation equality and hidden-sublocation limits;
- one ModelOutput per ProviderAttempt across record collection;
- OutputItem ownership/ordering consistency and accepted_output ownership;
- ToolProposal→ToolInvocation positive lineage;
- ToolDecision applicability/governance of a ToolExecution;
- argument provenance classification from Derivation;
- one ToolResult per ToolExecution across record collection;
- EffectObservation separate_observation distinctness and bounded claim support;
- Trust/Taint conflict, policy compatibility, propagation, lattice, and sanitization rules;
- privacy descriptor versus disclosed representation consistency;
- digest/HMAC candidate recomputation and redaction lineage;
- ARP inventory equality with record membership;
- Receipt identity immutability and cross-Receipt object consistency;
- RFC 8785 canonicalization and SHA-256 recomputation;
- SigningStatement construction, key resolution, and Ed25519 verification;
- signed-envelope to supplied-ARP binding;
- adapter capability versus observed occurrence/capture evidence;
- structural invalidity versus factual uncertainty;
- completeness, conflict preservation, prohibited inference, and claim-strength wording;
- mandatory-check accounting and process-outcome aggregation.

Schema-valid does not mean semantically valid, factually true, trusted, causally responsible, or complete.
