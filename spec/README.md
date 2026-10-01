# C2ATrace Specification

Status: pre-schema specification work.

## Current documents

- PHASE-0-FOUNDATIONS.md — reviewed Phase 0 baseline, object taxonomy, relation semantics, graph invariants, and open design gates.
- PHASE-1-PART-A-SOURCE-SEMANTICS.md — accepted SourceRef / SourceObservation semantics after adversarial review.
- PHASE-1-PART-B-TRANSFORM-DERIVATION.md — accepted Transform / Derivation semantics, Region lineage, and control-vs-content separation after adversarial review.
- PHASE-1-PART-C-REQUEST-SEMANTICS.md — accepted RequestSnapshot / RequestBinding semantics, capture levels, request locations, digest semantics, and hash-only verification boundaries after adversarial review.
- PHASE-1-PART-D-MODEL-OUTPUT-SEMANTICS.md — accepted ModelInvocation / ProviderAttempt / ModelOutput semantics, retry/failover, output identity, streaming boundaries, and completion/capture distinctions after adversarial review.
- PHASE-1-PART-E-TOOL-EFFECT-SEMANTICS.md — accepted ToolProposal / ToolInvocation / ToolDecision / ToolExecution / ToolResult / EffectObservation semantics, argument provenance, denial, retry/idempotency, and effect-evidence boundaries after adversarial review.
- PHASE-1-PART-F-TRUST-TAINT-SEMANTICS.md — accepted TrustAssertion / TaintAssertion semantics, policy scoping, conservative taint lattice, content/control separation, sanitization, and anti-laundering boundaries after adversarial review.
- PHASE-1-PART-G-PRIVACY-SEMANTICS.md — accepted package-relative privacy semantics, full/hash-only/HMAC/redacted profiles, metadata leakage, redacted identity, verifier capability, and verification downgrade boundaries after adversarial review.
- PHASE-1-PART-H-INTEGRITY-RECEIPT-SEMANTICS.md — accepted Receipt identity/scope/subset, ExternalReference/multi-Receipt resolution, ReceiptLink, RFC 8785 + SHA-256 + Ed25519 integrity, privacy composition, and multidimensional verifier-result semantics after adversarial review.
- PROVIDER-ADAPTER-CONTRACT.md — accepted application-visible Provider Adapter capture contract, capability declaration, CaptureDiagnostic, request/output/streaming/retry capture, privacy-aware degradation, and evidence-boundary rules after adversarial review.
- TOOL-ADAPTER-CONTRACT.md — accepted application/runtime-visible Tool Adapter capture contract, effective invocation/argument provenance, decision/execution/result boundaries, retry/idempotency, streaming results, effect-evidence acquisition, privacy, and CaptureDiagnostic semantics after adversarial review.
- THREAT-MODEL.md — trust boundaries, adversary assumptions, and numbered normative threat requirements.
- CLAIMS.md — composable evidence-basis model and numbered verifier-reporting requirements.
- TERMINOLOGY.md — shared definitional vocabulary, now aligned through Tool Adapter Contract.

## Project gate

JSON Schema remains unfrozen. Phase 1 Parts A through H are complete.

Provider Adapter Contract and Tool Adapter Contract are complete. The final pre-Schema specification gate is Verifier Contract.

## Normative language discipline

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are protocol-normative only inside numbered normative requirements or definitions that explicitly cite those requirements.

Every numbered MUST / MUST NOT requirement is paired with a planned conformance test identifier before Schema freeze.
