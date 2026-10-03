# C2ATrace v0.1 Conformance Runner Contract

Status: IN PROGRESS WITH THE v0.1 CONFORMANCE SUITE.

This document defines language-neutral execution semantics for files under `conformance/v0.1/`. It is test-infrastructure semantics, not a new C2ATrace runtime protocol object.

## 1. Case loading

A runner loads the suite manifest, the referenced case-index shard, one case document, and its expected-result document.

Case IDs are globally unique. Requirement IDs and planned-test IDs remain separate traceability fields.

A runner must not infer that two requirements are the same case merely because they share a planned-test name.

## 2. Input materialization

Each case document entry is materialized independently.

For a path source:

1. load the referenced JSON document;
2. if `extract_pointer` is present, evaluate that JSON Pointer and deep-copy the selected value;
3. apply the document's patch operations, in listed order, to that copied value.

For an inline source, deep-copy the inline value and then apply patches.

The v0.1 patch subset is deterministic RFC-6902-compatible `add`, `remove`, and `replace`.

Patch failures are harness errors, not protocol findings.

The special final array token `-` means append for `add`.

## 3. Schema resolution

Protocol Schema targets are resolved using `schema/v0.1/manifest.json` and the frozen URN identifiers.

Conformance Schema targets are resolved using `conformance/v0.1/manifest.json`.

A missing Schema resource is a harness/configuration error. It must not be rewritten as a protocol-invalid result for the tested document.

## 4. Execution phases

Cases list the phases they require. Runners execute only applicable phases, preserving this conceptual order:

1. `schema_validate`
2. `resolve_references`
3. `graph_checks`
4. `representation_checks`
5. `privacy_checks`
6. `integrity_checks`
7. `claim_checks`
8. `aggregate_report`

A case may omit phases that are irrelevant to its requirement.

A later phase must not silently repair or reinterpret an earlier invalid input.

Independent checks that remain safe on partially invalid material may still run when required by the Verifier Contract.

## 5. Semantic-verifier harness input

The optional `harness` object is validated by `harness-input.schema.json`.

Document IDs named in `primary_documents`, `resolution_set`, and `external_evidence` refer to materialized case documents.

Verification keys and HMAC capabilities are test-only verifier inputs. They are never inserted into the historical Receipt being verified.

Private HMAC material is harness input and must not appear in ordinary VerificationFinding output.

## 6. Golden result normalization

Expected-result files are comparison specifications, not literal full verifier reports.

### 6.1 Normalized finding comparison view

A runner compares finding matchers against a conformance-normalized finding view. This view is runner infrastructure; it does not add fields to the protocol `VerificationFinding`.

The normalized view carries the case's unique `requirement_id` as conformance attribution. `check_id`, `domain`, `status`, `reason_code`, `evidence_bases`, and `prohibited_inferences` come from the applicable machine check result and must not be inferred from human-readable text.

`subject_selector` is a recursive subset match against a normalized `subject_scope` object. Protocol subject coordinates are copied without semantic change from `VerificationFinding.subject` when applicable. Check-local conformance coordinates may additionally use only these keys:

```text
report_id
vector_id
linked_receipt_id
path
dropped_path
slot
compared_object_id
metadata_name
event_semantics
capture_extent
origin
```

These extension coordinates identify deterministic case-local evaluation scope. They are comparison metadata, not protocol fields. A runner must obtain them from the machine check that produced the normalized finding; it must not derive them from free-text messages. Extension coordinates must not overwrite or reinterpret protocol subject coordinates.

`schema_results` are keyed by `document_id`.

For `required_findings`, every matcher must match at least one actual VerificationFinding.

For `forbidden_findings`, no matcher may match any actual VerificationFinding.

A finding matcher compares only fields it explicitly contains. `subject_selector` is a recursive subset match against the actual finding subject/scope.

When `evidence_bases` or `prohibited_inferences` are present in a matcher, the listed values are required subsets unless the case explicitly uses `exact_normative`.

Free-text messages, diagnostic prose, object-key ordering, array ordering of independent findings, and implementation-generated `finding_id` values are not golden data.

## 7. Comparison modes

`contains_normative` permits additional non-contradictory findings while requiring every listed normative matcher.

`exact_normative` requires the complete normalized normative result set represented by the golden file and is intended mainly for bounded schema-only and deterministic-vector cases.

Neither mode compares human-readable rendering.

## 8. Process outcome

When present, `process_outcome` is compared to the VerificationReport process outcome defined by the Verifier Contract.

It is operational aggregation only. It must not be interpreted as an overall factual-truth or fully-verified boolean.

## 9. Cross-language determinism

Two conforming runners given the same case, frozen Schema bundle, supported profiles, capabilities, and deterministic vector material must produce equivalent normalized golden comparison results.

They may differ in:

- internal data structures;
- finding IDs;
- error-stack formatting;
- human-readable wording;
- ordering of independent findings.

They must not differ in the normative statuses required or forbidden by the case.

## 10. Acceptance states

`mapped` means the requirement has a unique case ID.

`planned` means design work exists but executable material is incomplete.

`executable` means inputs, phases, and golden expectations are fully materialized and harness-self-checked.

`accepted` means the executable case has additionally passed the applicable independent conformance execution gate.

The suite gate requires all 907 requirement cases to be accepted.
