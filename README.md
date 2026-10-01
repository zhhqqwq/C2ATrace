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

Specification-first. Phase 0 is complete after second review. Phase 1 Parts A (SourceRef / SourceObservation), B (Transform / Derivation), C (RequestSnapshot / RequestBinding), D (ModelInvocation / ProviderAttempt / ModelOutput), and E (Tool / Effect semantics) are complete after adversarial review. JSON Schema remains unfrozen and implementation has not started.

See:

- [Phase 0 Foundations](spec/PHASE-0-FOUNDATIONS.md)
- [Phase 1 Part A — Source Semantics](spec/PHASE-1-PART-A-SOURCE-SEMANTICS.md)
- [Phase 1 Part B — Transform / Derivation](spec/PHASE-1-PART-B-TRANSFORM-DERIVATION.md)
- [Phase 1 Part C — Request Semantics](spec/PHASE-1-PART-C-REQUEST-SEMANTICS.md)
- [Phase 1 Part D — Model Invocation / Output](spec/PHASE-1-PART-D-MODEL-OUTPUT-SEMANTICS.md)
- [Phase 1 Part E — Tool / Effect Semantics](spec/PHASE-1-PART-E-TOOL-EFFECT-SEMANTICS.md)
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
- Recorded inclusion is not causal responsibility.
- Every numbered normative requirement maps to a planned conformance test.

## What v0.1 is not

C2ATrace v0.1 is not an agent runtime, dashboard, security gateway, prompt-injection detector, authorization engine, causal-attribution system, or outcome-verification system.

## Next specification gate

The next semantic phase defines Trust / Taint semantics. JSON Schema freeze remains blocked until trust/taint, privacy, integrity/receipt, adapter, and verifier semantics pass their specification gates.
