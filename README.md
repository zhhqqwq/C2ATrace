# C2ATrace

Context-to-Action provenance for AI agents.

> Know what your application sent to the model, where it came from, and what the agent did next.

C2ATrace is a provider-neutral, framework-neutral, policy-neutral provenance protocol for preserving source and transformation provenance into an application-visible provider request, then linking that request to downstream model outputs, effective tool invocations, executions, results, and effect observations.

## Core boundary

~~~text
SourceRef
  ↓ observed_from
SourceObservation
  ↓ used by
Transform
  ↓ generates
ModelInputComponent / ContextFragment
  ↓ RequestBinding
RequestSnapshot
  ↓ used by
ProviderAttempt
  ↓ produces
ModelOutput
  ↓ contains
ToolProposal
  ↓ optional application preparation Transform
ToolInvocation
  ↓ used by
ToolExecution
  ↓ returns
ToolResult
  ↓ supports
EffectObservation
~~~

Derivation is an explicit assertion between Artifacts; it is not the same thing as Transform. A recorded transformation path does not automatically establish exact derivation.

C2ATrace records provenance and execution linkage. It does not claim model-internal causality, producer completeness, provider-internal visibility, or external truth beyond available evidence.

## Current status

Specification-first. Phase 0, Phase 1 Parts A-H, Provider Adapter Contract, Tool Adapter Contract, Verifier Contract, and the v0.1 JSON Schema freeze are complete. The Conformance Suite is now active: 907/907 requirements have mapped case IDs, 136 cases are executable, all 43 deterministic-vector and all 87 mixed schema-semantic requirements are materialized, and 6 direct-schema cases are accepted. Product Independent Verifier and SDK implementation remain blocked until the complete conformance gate passes.

See:

- [Phase 0 Foundations](spec/PHASE-0-FOUNDATIONS.md)
- [Phase 1 Part A — Source Semantics](spec/PHASE-1-PART-A-SOURCE-SEMANTICS.md)
- [Phase 1 Part B — Transform / Derivation](spec/PHASE-1-PART-B-TRANSFORM-DERIVATION.md)
- [Phase 1 Part C — Request Semantics](spec/PHASE-1-PART-C-REQUEST-SEMANTICS.md)
- [Phase 1 Part D — Model Invocation / Output](spec/PHASE-1-PART-D-MODEL-OUTPUT-SEMANTICS.md)
- [Phase 1 Part E — Tool / Effect Semantics](spec/PHASE-1-PART-E-TOOL-EFFECT-SEMANTICS.md)
- [Phase 1 Part F — Trust / Taint Semantics](spec/PHASE-1-PART-F-TRUST-TAINT-SEMANTICS.md)
- [Phase 1 Part G — Privacy Semantics](spec/PHASE-1-PART-G-PRIVACY-SEMANTICS.md)
- [Phase 1 Part H — Integrity / Receipt Semantics](spec/PHASE-1-PART-H-INTEGRITY-RECEIPT-SEMANTICS.md)
- [Provider Adapter Contract](spec/PROVIDER-ADAPTER-CONTRACT.md)
- [Tool Adapter Contract](spec/TOOL-ADAPTER-CONTRACT.md)
- [Verifier Contract](spec/VERIFIER-CONTRACT.md)
- [v0.1 JSON Schema](schema/v0.1/README.md)
- [Schema Freeze Audit](schema/v0.1/FREEZE-AUDIT.md)
- [Conformance Suite](conformance/v0.1/README.md)
- [Project Delivery Package](delivery/v0.1/README.md)
- [Threat Model](spec/THREAT-MODEL.md)
- [Claim Matrix](spec/CLAIMS.md)
- [Terminology](spec/TERMINOLOGY.md)

## Design principles

- Specification before integrations.
- Provider-neutral and framework-neutral.
- Policy-neutral provenance infrastructure.
- Unknown over guessing.
- Conservative over false precision.
- Integrity is not truth.
- Execution is not outcome.
- Transform use/generation is not Derivation.
- Control influence is not representation derivation.
- Selection/forwarding is not generation.
- Locator equality is not source identity.
- Content equality is not source identity.
- RequestBinding is capture-level-local.
- Prepared HTTP body capture is not Provider receipt.
- Hash-only commitment equality is not hidden sublocation proof.
- Attempt completion is not output capture completeness.
- Accepted output is not complete output.
- Requested/reported model identity is not provider-internal model identity.
- ToolProposal is not ToolInvocation or ToolExecution.
- Allow/deny decisions are not execution events.
- Tool completion or reported success is not external effect truth.
- Effect observation is not outcome verification.
- Idempotency metadata is not exactly-once proof.
- Trusted is not objectively true.
- Tainted is not malicious.
- Trust does not automatically inherit.
- Content taint and control taint are distinct.
- Tainted request does not automatically taint model output.
- Sanitized is not trusted.
- Sanitization does not erase provenance history.
- Privacy is package-relative, not global non-disclosure.
- Hash-only is not a confidentiality guarantee.
- HMAC verification can be independent without being public.
- Redacted representation is not the original representation.
- Withheld is not absent, null, or empty.
- Privacy omission never strengthens provenance.
- Receipt inventory completeness is not runtime-history completeness.
- ExternalReference resolution is not causality or truth.
- ReceiptLink integrity is not complete-history proof.
- Signature validity is not record truth.
- Signature validity is not capture completeness.
- Verification-key labels are not real-world signer identity.
- Signed hash-only/redacted evidence is not direct signature over unavailable plaintext.
- Provider Adapter visibility is application-side.
- Adapter capability is not runtime capture proof.
- Hidden provider/SDK retries are not invented.
- Streaming capture requires application-visible stream-consumption visibility.
- Capture failure is not ProviderAttempt failure.
- CaptureDiagnostic is not instrumentation completeness proof.
- Provider-reported metadata is not provider-internal attestation.
- Tool Adapter visibility is application/runtime-side.
- Proposal ancestry and allow decisions are not inferred from execution.
- Effective ToolInvocation is the final visible pre-execution representation.
- ToolExecution failure/timeout/cancellation does not prove no Effect.
- Idempotency metadata is not exactly-once proof.
- Tool-reported success/transaction/job status is not external Effect truth.
- separate_observation requires a distinct observation occurrence.
- EffectObservation is not OutcomeVerification.
- Tool Adapter diagnostics are not tool-path completeness proof.
- Verifier authority is evidence-bounded and invocation-relative.
- Valid/matched/asserted/unknown/unverified/unsupported/conflict are typed results, not one strength scale.
- Signature validity and binding to the supplied ARP are separate verifier dimensions.
- A fully resolved Resolution Set is not complete global history.
- Human output and CLI exit status cannot strengthen machine findings.
- There is no unqualified overall fully_verified boolean.
- Recorded inclusion is not causal responsibility.
- Every numbered normative requirement maps to a planned conformance test.

## What v0.1 is not

C2ATrace v0.1 is not an agent runtime, dashboard, security gateway, prompt-injection detector, authorization engine, causal-attribution system, or outcome-verification system.

## Next specification gate

All pre-Schema semantic/contract gates and the v0.1 JSON Schema freeze are complete. The active gate is the complete language-neutral Conformance Suite: all 907 requirements are mapped, with direct-schema acceptance complete and mixed/deterministic/semantic layers still being materialized. Independent verifier implementation and SDK implementation remain blocked until the suite reaches 907/907 accepted cases with cross-language normalized equivalence.
