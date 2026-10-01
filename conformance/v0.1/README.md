# C2ATrace v0.1 Conformance Suite

Status: IN PROGRESS.

This directory defines the language-neutral conformance harness for the frozen C2ATrace v0.1 protocol.

The suite separates four responsibilities:

- direct_schema — local wire-shape rules checked only by JSON Schema;
- mixed_schema_semantic — Schema constrains local shape and semantic verifier checks complete the requirement;
- semantic_verifier — cross-object, graph, evidence, conflict, completeness, causality, or reporting rule;
- deterministic_vector — canonicalization, digest, signature, keyed commitment, or other algorithmic rule with reproducible vectors.

Every numbered requirement receives a unique case ID derived from both requirement ID and planned-test ID. Duplicate planned-test names therefore never merge requirements.

Cases use deterministic input documents plus optional add/remove/replace JSON-Pointer patches. Expected results are language-neutral normative matchers; free-text messages and implementation-generated finding IDs are not golden data.

A case is not counted as accepted until its input, execution phases, expected result, and requirement mapping are all executable and independently checked.
