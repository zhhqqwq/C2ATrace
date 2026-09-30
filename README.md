# C2ATrace

Context-to-Action provenance for AI agents.

> Know what your application sent to the model, where it came from, and what the agent did next.

C2ATrace is a provider-neutral, framework-neutral, policy-neutral provenance protocol for preserving source and transformation provenance into an application-visible provider request, then linking that request to downstream model outputs, effective tool invocations, executions, results, and effect observations.

## Core boundary

~~~text
SourceRef
  ↓
SourceObservation
  ↓
Transform / Derivation
  ↓
ModelInputComponent / ContextFragment
  ↓
RequestBinding
  ↓
RequestSnapshot
  ↓
ProviderAttempt
  ↓
ModelOutput
  ↓
ToolProposal
  ↓
ToolInvocation
  ↓
ToolExecution
  ↓
ToolResult
  ↓
EffectObservation
~~~

C2ATrace records provenance and execution linkage. It does not claim model-internal causality, producer completeness, provider-internal visibility, or external truth beyond available evidence.

## Current status

Specification-first. Phase 0 foundations are accepted with revisions. JSON Schema and implementation are intentionally not frozen yet.

See:

- [Phase 0 Foundations](spec/PHASE-0-FOUNDATIONS.md)
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
- Every normative claim must map to a future conformance test.

## What v0.1 is not

C2ATrace v0.1 is not an agent runtime, dashboard, security gateway, prompt-injection detector, authorization engine, causal-attribution system, or outcome-verification system.

## Next specification gate

The next phase defines SourceRef / SourceObservation, Transform / Derivation, and RequestSnapshot / RequestBinding semantics before any JSON Schema freeze.