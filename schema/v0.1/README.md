# C2ATrace v0.1 JSON Schema Freeze

Status: ACCEPTED AND FROZEN AFTER AUDIT.

Dialect: JSON Schema Draft 2020-12.

Schema IDs use `urn:c2atrace:schema:v0.1:`. Profile IDs use `urn:c2atrace:profile:v0.1:`.

## Wire rules

- IDs are opaque strings; digests never define identity.
- References are explicitly tagged `local` or `external`; externality is never inferred from a missing local target.
- Record discriminators use the accepted CamelCase protocol object names.
- Core text intervals are Unicode-scalar half-open ranges; byte intervals are byte half-open ranges.
- Structured paths carry an explicit scheme; core JSON paths use `json_pointer`.
- Unknown core top-level fields are rejected. Future extensions enter through explicit extension/profile points.
- JSON Schema validates wire shape. Cross-object provenance, graph, commitment, signature, completeness, conflict, and claim-strength requirements remain verifier semantic checks.

The package manifest maps the protocol namespace. `semantic-checks.md` records the Schema/verifier boundary; `FREEZE-AUDIT.md` records the acceptance audit; and `traceability/v0.1/` maps all 907 numbered requirements to their enforcement layer and planned conformance test.

The frozen Schema does not unlock implementation by itself. The complete normative fixture and cross-language conformance-vector suite remains the next gate.
