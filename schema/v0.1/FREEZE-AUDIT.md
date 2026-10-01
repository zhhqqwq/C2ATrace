# C2ATrace v0.1 — JSON Schema Freeze Audit

Status: PASS. v0.1 JSON Schema is accepted and frozen.

## Scope

This audit covers the v0.1 Schema bundle, first normative/invalid fixtures, deterministic integrity/privacy vectors, and the Schema-to-requirement traceability baseline.

It does not declare the complete 907-case conformance suite finished, and it does not unlock implementation by itself.

## Schema bundle

- JSON Schema dialect: Draft 2020-12.
- Schema files: 16.
- Unique schema identifiers: 16.
- Cross-file references checked: 259.
- Broken references: 0.
- Manifest omissions: 0.
- Runtime Record union branches: 24, with no duplicate branch references.
- Top-level document union branches: 5, with no duplicate branch references.
- Expected semantic/package/verifier wire objects checked: 34.
- Missing expected wire homes: 0.
- Package/meta objects incorrectly present in runtime Record union: 0.

## Freeze defect found and fixed

The audit found a Draft 2020-12 composition defect in concrete record schemas that combined a BaseRecord through allOf while placing unevaluatedProperties=false inside a sibling allOf branch.

That placement could cause inherited BaseRecord fields such as id/kind/run_id to be treated as unevaluated.

The fix moved unevaluatedProperties=false to the concrete schema object containing the allOf composition. No protocol field, enum, ownership rule, or accepted semantic meaning changed.

All affected concrete schemas were regenerated and the fixtures were revalidated after the fix.

## Fixture layer audit

Valid Receipt fixtures:

- 9 checked.
- 9 Schema-valid.
- 9 have matching recomputed ARP SHA-256 digests.
- 0 dangling local references in the valid set.
- 0 inventory mismatches in the valid set.
- 0 Derivation cycles in the valid set.

Schema-invalid fixtures:

- RequestSnapshot with both invocation_owner and attempt_owner fails the owner XOR.
- ProviderAttempt using terminal_disposition=succeeded fails the frozen disposition vocabulary.

Semantic-invalid fixtures are intentionally Schema-valid:

- dangling local reference: Schema-valid, unresolved local target detected;
- Derivation cycle: Schema-valid, cycle detected;
- ARP inventory mismatch: Schema-valid, inventory mismatch detected.

Crypto-invalid fixture:

- payload-digest-mismatch is Schema-valid, but recomputed ARP SHA-256 differs from the stored digest.

Multi-Receipt fixture:

- object-level ExternalReference payload pins match the target Receipt A ARP digest;
- ReceiptLink payload digest matches the same target ARP digest;
- object-level resolution and package-level linkage remain distinct semantics.

## Deterministic vectors

The stored baseline integrity vector was independently recomputed:

- ARP canonical form matches the stored RFC 8785 JCS test string;
- SHA-256 hex/base64url matches;
- Ed25519 public key derived from the fixed test seed matches;
- Signing Statement canonical form matches;
- Ed25519 signature matches.

The privacy vectors were independently recomputed:

- HMAC-SHA256 tag matches;
- HMAC negative candidate does not match;
- hash-only SHA-256 digest matches.

The vectors remain public deterministic test material only.

## Requirement traceability

All accepted numbered requirements are represented in traceability/v0.1/.

Total: 907.

Family counts:

- TM 12
- CLAIM 6
- GRAPH 16
- SRC 22
- DRV 32
- REQ 52
- OUT 53
- TOOL 62
- TRUST 25
- TAINT 59
- PRIV 80
- RCPT 51
- INTG 70
- PAD 95
- TAD 118
- VFY 154

Traceability integrity:

- duplicate requirement IDs: 0;
- missing planned tests: 0;
- requirements without enforcement layers: 0.

Primary enforcement classification:

- direct_schema: 6
- mixed_schema_semantic: 87
- semantic_verifier: 771
- deterministic_vector: 43

The classification is an implementation responsibility map, not a verification-strength ranking.

Post-freeze conformance executability audit corrected six responsibility classifications (REQ-005, REQ-006, REQ-013, REQ-014, RCPT-012, RCPT-013). This changed no protocol semantics and no frozen Schema shape.

## Schema / verifier boundary

Schema validation freezes local wire shape.

It does not replace semantic verification for reference resolution, immutable identity, DAG checks, representation membership, commitment recomputation, signature verification, conflict preservation, completeness, causal boundaries, or external truth.

## Gate decision

JSON Schema Freeze: PASS.

C2ATrace v0.1 Schema is FROZEN.

Next gate:

complete normative fixtures + invalid fixtures + cross-language conformance vectors.

Independent Verifier implementation: BLOCKED until the conformance suite gate passes.

SDK implementation: BLOCKED until the conformance suite gate passes.
